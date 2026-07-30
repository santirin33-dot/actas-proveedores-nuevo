/**
 * Web App de Apps Script — Hoja "Actas Proveedores".
 * Al implementarlo como aplicación web, la URL que devuelve es la que va en la
 * variable de entorno LOG_URL del proyecto de Vercel.
 *
 * Maneja CUATRO pestañas de la misma hoja:
 *   · "Proveedores"  → catálogo de proveedores y su tipo de servicio
 *   · "Reuniones"    → cada reunión registrada (el acta completa va en temas_json)
 *   · "Tareas"       → los compromisos que salieron de cada reunión
 *   · "Seguimiento"  → bitácora de avances (alimenta la línea de tiempo)
 *
 * Después de pegar cambios aquí hay que volver a desplegar:
 *   Implementar → Administrar implementaciones → editar → Versión: Nueva → Implementar
 *
 * IMPORTANTE al desplegar: "Ejecutar como: Yo" y "Quién tiene acceso: Cualquier persona".
 */

var TZ = 'America/Bogota';

// Carpeta de Drive donde se archivan las actas. Dentro se crea una subcarpeta
// por proveedor. Se busca por nombre y se crea si no existe, así que no hay que
// pegar ningún id a mano: basta con no renombrarla después.
var CARPETA_ACTAS = 'Actas de Proveedores';

// Orden EXACTO de las columnas de cada pestaña. Si se reordenan en la hoja,
// hay que reordenarlas aquí también.
var COLUMNAS = {
  'Proveedores': ['id', 'nombre', 'tipo_servicio', 'contacto', 'email', 'telefono',
                  'estado', 'creado_por', 'fecha_creacion'],

  'Reuniones':   ['id', 'fecha', 'proveedor_id', 'proveedor', 'tipo_servicio', 'titulo',
                  'participantes', 'resumen', 'temas_json', 'generado_por', 'fecha_registro',
                  'enlace_docx'],

  'Tareas':      ['id', 'reunion_id', 'fecha', 'proveedor_id', 'proveedor', 'tipo_servicio',
                  'tema', 'tarea', 'responsable', 'estado', 'prioridad', 'fecha_limite',
                  'fecha_completada', 'tarea_origen_id', 'actualizado_por'],

  'Seguimiento': ['id', 'tarea_id', 'fecha', 'reunion_id', 'avance',
                  'estado_anterior', 'estado_nuevo', 'autor']
};


function _hoja(nombre) {
  if (!COLUMNAS[nombre]) throw new Error('Pestaña desconocida: ' + nombre);
  var libro = SpreadsheetApp.getActiveSpreadsheet();
  var h = libro.getSheetByName(nombre);
  if (!h) {
    h = libro.insertSheet(nombre);
    h.appendRow(COLUMNAS[nombre]);
    h.setFrozenRows(1);
  }
  return h;
}


function _json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}


/**
 * Las celdas de fecha vuelven como objeto Date y, serializadas a JSON, salen como
 * "2026-08-20T05:00:00.000Z". El dashboard compara y ordena con AAAA-MM-DD, así que
 * aquí se normaliza todo a texto antes de responder.
 */
function _texto(v) {
  if (v instanceof Date) return Utilities.formatDate(v, TZ, 'yyyy-MM-dd');
  return String(v === null || v === undefined ? '' : v);
}


function _leerPestana(nombre) {
  var h = _hoja(nombre);
  var cols = COLUMNAS[nombre];
  var datos = h.getDataRange().getValues();
  if (datos.length < 2) return [];
  return datos.slice(1).map(function (r) {
    var o = {};
    for (var i = 0; i < cols.length; i++) o[cols[i]] = _texto(r[i]);
    return o;
  }).filter(function (o) { return o.id; });
}


function doGet(e) {
  var p = (e && e.parameter) || {};
  var nombre = p.sheet || '';

  if (nombre === 'todo') {
    return _json({
      proveedores: _leerPestana('Proveedores'),
      reuniones:   _leerPestana('Reuniones'),
      tareas:      _leerPestana('Tareas'),
      seguimiento: _leerPestana('Seguimiento')
    });
  }

  if (!COLUMNAS[nombre]) return _json({ error: 'Pestaña no válida' });

  var filas = _leerPestana(nombre);

  // Filtros opcionales (el filtrado fino lo hace igual el backend; esto solo
  // ahorra transferencia cuando se pide una sola cosa).
  if (p.proveedor_id) {
    filas = filas.filter(function (f) { return f.proveedor_id === p.proveedor_id; });
  }
  if (p.estado) {
    filas = filas.filter(function (f) { return f.estado === p.estado; });
  }
  if (p.desde) {
    filas = filas.filter(function (f) { return f.fecha >= p.desde; });
  }
  if (p.hasta) {
    filas = filas.filter(function (f) { return f.fecha <= p.hasta; });
  }
  return _json(filas);
}


/** Añade una o varias filas (objetos) a una pestaña, en el orden de sus columnas. */
function _agregar(nombre, registros) {
  var h = _hoja(nombre);
  var cols = COLUMNAS[nombre];
  var filas = (registros || []).map(function (o) {
    return cols.map(function (c) {
      var v = o[c];
      return (v === null || v === undefined) ? '' : String(v);
    });
  });
  if (!filas.length) return 0;
  // Se escribe todo de un golpe: appendRow fila por fila es mucho más lento y
  // con varios compromisos por reunión se notaba la espera.
  h.getRange(h.getLastRow() + 1, 1, filas.length, cols.length).setValues(filas);
  return filas.length;
}


/** Devuelve la subcarpeta del proveedor, creando lo que falte. */
function _carpetaProveedor(nombreProveedor) {
  var raices = DriveApp.getFoldersByName(CARPETA_ACTAS);
  var raiz = raices.hasNext() ? raices.next() : DriveApp.createFolder(CARPETA_ACTAS);

  var limpio = String(nombreProveedor || 'Sin proveedor').trim() || 'Sin proveedor';
  var subs = raiz.getFoldersByName(limpio);
  return subs.hasNext() ? subs.next() : raiz.createFolder(limpio);
}


/**
 * Archiva el .docx que mandó la app y devuelve su enlace.
 *
 * Devuelve '' si algo falla: perder el archivo es molesto, pero perder el
 * registro de la reunión sería grave, así que un fallo aquí NUNCA aborta el
 * guardado de la fila.
 */
function _archivarActa(archivo) {
  if (!archivo || !archivo.contenido_b64) return '';
  try {
    var bytes = Utilities.base64Decode(archivo.contenido_b64);
    var blob = Utilities.newBlob(
      bytes,
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      archivo.nombre || 'Acta.docx');

    var carpeta = _carpetaProveedor(archivo.carpeta);

    // Si ya existe un acta con ese nombre (misma fecha y proveedor), se le pone
    // sufijo en vez de sobrescribir: dos reuniones el mismo día son posibles y
    // ninguna debe pisar a la otra.
    var nombre = blob.getName();
    var n = 2;
    while (carpeta.getFilesByName(nombre).hasNext()) {
      nombre = blob.getName().replace(/\.docx$/, '') + ' (' + n + ').docx';
      n++;
    }
    blob.setName(nombre);

    return carpeta.createFile(blob).getUrl();
  } catch (err) {
    console.error('No se pudo archivar el acta en Drive: ' + err);
    return '';
  }
}


/** Actualiza campos sueltos de una fila buscada por su id. */
function _actualizar(nombre, id, cambios) {
  var h = _hoja(nombre);
  var cols = COLUMNAS[nombre];
  var ultima = Math.max(h.getLastRow(), 1);
  var ids = h.getRange(1, 1, ultima, 1).getValues();
  for (var i = 1; i < ids.length; i++) {
    if (String(ids[i][0]) !== String(id)) continue;
    var fila = i + 1;                          // la hoja es 1-indexada
    for (var campo in cambios) {
      var col = cols.indexOf(campo);
      if (col === -1) continue;                // campo desconocido: se ignora
      h.getRange(fila, col + 1).setValue(String(cambios[campo]));
    }
    return true;
  }
  return false;
}


function doPost(e) {
  var body = {};
  try { body = JSON.parse(e.postData.contents); } catch (err) { body = {}; }
  var accion = body.action || '';

  try {
    if (accion === 'add_proveedor') {
      return _json({ ok: true, count: _agregar('Proveedores', [body.proveedor]) });
    }

    if (accion === 'update_proveedor') {
      var okP = _actualizar('Proveedores', body.id, body.cambios || {});
      return _json({ ok: okP, msg: okP ? '' : 'Proveedor no encontrado' });
    }

    // Guarda la reunión, sus compromisos y los avances reportados, todo junto:
    // si se hiciera en tres llamadas y fallara la segunda, quedaría una reunión
    // sin tareas y el seguimiento se rompería.
    if (accion === 'add_reunion') {
      var reunion = body.reunion || {};
      reunion.enlace_docx = _archivarActa(body.archivo);
      _agregar('Reuniones', [reunion]);
      var nT = _agregar('Tareas', body.tareas || []);
      var nS = _agregar('Seguimiento', body.seguimiento || []);
      // Los avances reportados en la reunión cambian el estado de la tarea anterior.
      (body.cambios_tareas || []).forEach(function (c) {
        _actualizar('Tareas', c.id, c.cambios || {});
      });
      return _json({ ok: true, tareas: nT, seguimiento: nS,
                     enlace_docx: reunion.enlace_docx });
    }

    if (accion === 'add_tareas') {
      return _json({ ok: true, count: _agregar('Tareas', body.tareas || []) });
    }

    if (accion === 'update_tarea') {
      var okT = _actualizar('Tareas', body.id, body.cambios || {});
      if (okT && body.seguimiento) _agregar('Seguimiento', [body.seguimiento]);
      return _json({ ok: okT, msg: okT ? '' : 'Tarea no encontrada' });
    }

    if (accion === 'add_seguimiento') {
      return _json({ ok: true, count: _agregar('Seguimiento', [body.seguimiento]) });
    }

    return _json({ ok: false, msg: 'Acción desconocida: ' + accion });
  } catch (err) {
    return _json({ ok: false, msg: String(err) });
  }
}
