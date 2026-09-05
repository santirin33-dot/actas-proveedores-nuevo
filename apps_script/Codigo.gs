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

  // 'tipo' y 'ans_id' van AL FINAL a propósito: las filas que ya existen se
  // siguen leyendo bien por índice y llegan con esos campos vacíos, que se
  // interpretan como tarea normal. No hay que migrar ninguna fila.
  'Tareas':      ['id', 'reunion_id', 'fecha', 'proveedor_id', 'proveedor', 'tipo_servicio',
                  'tema', 'tarea', 'responsable', 'estado', 'prioridad', 'fecha_limite',
                  'fecha_completada', 'tarea_origen_id', 'actualizado_por',
                  'tipo', 'ans_id'],

  'Seguimiento': ['id', 'tarea_id', 'fecha', 'reunion_id', 'avance',
                  'estado_anterior', 'estado_nuevo', 'autor'],

  // Los ANS son PRINCIPIOS del contrato: no llevan fecha, ni caducidad, ni
  // estado de cumplimiento. Al ser un principio se entiende cumplido. Lo único
  // que tienen es 'activo', para retirar un acuerdo que ya no está vigente —
  // eso es ciclo de vida, no incumplimiento.
  'ANS':         ['id', 'proveedor_id', 'proveedor', 'titulo', 'descripcion',
                  'periodicidad', 'activo', 'creado_por', 'fecha_creacion']
};


/**
 * Pone la fila de encabezados al día con COLUMNAS.
 *
 * Hace falta porque _hoja() solo escribe los encabezados cuando CREA la pestaña.
 * Al añadir una columna nueva, las hojas que ya existían se quedaban con el
 * encabezado viejo y los datos nuevos caían en columnas sin título: quien abre
 * la Hoja a mano veía valores sueltos sin saber qué eran.
 *
 * Es idempotente: corre en cada llamada y no escribe nada si ya coinciden.
 */
function _asegurarColumnas(h, nombre) {
  var cols = COLUMNAS[nombre];
  var ancho = h.getLastColumn();
  var cabecera = ancho ? h.getRange(1, 1, 1, ancho).getValues()[0] : [];
  var igual = cabecera.length >= cols.length;
  if (igual) {
    for (var i = 0; i < cols.length; i++) {
      if (String(cabecera[i] || '') !== cols[i]) { igual = false; break; }
    }
  }
  if (igual) return;
  h.getRange(1, 1, 1, cols.length).setValues([cols]);
}


function _hoja(nombre) {
  if (!COLUMNAS[nombre]) throw new Error('Pestaña desconocida: ' + nombre);
  var libro = SpreadsheetApp.getActiveSpreadsheet();
  var h = libro.getSheetByName(nombre);
  if (!h) {
    h = libro.insertSheet(nombre);
    h.appendRow(COLUMNAS[nombre]);
    h.setFrozenRows(1);
  } else {
    _asegurarColumnas(h, nombre);
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
      seguimiento: _leerPestana('Seguimiento'),
      ans:         _leerPestana('ANS')
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

    var creado = carpeta.createFile(blob);

    /* Al reeditar un acta, la copia anterior se manda a la papelera. Si no, cada
       corrección dejaría "Acta X (2).docx", "(3)"... y el enlace guardado solo
       apunta a la última: las demás serían basura indistinguible. Se borra
       DESPUÉS de crear la nueva, para no quedarse sin ninguna si algo falla. */
    if (archivo.reemplazar) {
      try { DriveApp.getFileById(archivo.reemplazar).setTrashed(true); }
      catch (err2) { console.warn('No se pudo retirar el acta anterior: ' + err2); }
    }

    return creado.getUrl();
  } catch (err) {
    console.error('No se pudo archivar el acta en Drive: ' + err);
    return '';
  }
}


/**
 * Borra filas por id. Devuelve cuántas quitó.
 *
 * Se recorre de ABAJO hacia arriba: borrando de arriba abajo, cada fila
 * eliminada corre hacia arriba las que quedan y el resto de índices deja de
 * apuntar a donde creíamos.
 */
function _borrar(nombre, ids) {
  var h = _hoja(nombre);
  var quiero = {};
  (ids || []).forEach(function (x) { quiero[String(x)] = true; });
  if (!Object.keys(quiero).length) return 0;

  var datos = h.getDataRange().getValues();
  var quitadas = 0;
  for (var i = datos.length - 1; i >= 1; i--) {
    if (quiero[String(datos[i][0])]) { h.deleteRow(i + 1); quitadas++; }
  }
  return quitadas;
}


/** Devuelve los ids de una pestaña que cumplen `campo === valor`. */
function _idsDonde(nombre, campo, valor) {
  return _leerPestana(nombre)
    .filter(function (f) { return String(f[campo] || '') === String(valor); })
    .map(function (f) { return f.id; });
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

    // ── ANS ──
    if (accion === 'add_ans') {
      return _json({ ok: true, count: _agregar('ANS', [body.ans]) });
    }

    if (accion === 'update_ans') {
      var okA = _actualizar('ANS', body.id, body.cambios || {});
      return _json({ ok: okA, msg: okA ? '' : 'ANS no encontrado' });
    }

    /* Editar un acta ya guardada, en UNA sola llamada.
       Se hace junto por lo mismo que add_reunion: si fueran seis llamadas y
       fallara la tercera, quedaría una reunión con la mitad de sus compromisos
       y nadie sabría cuál mitad.

       Los compromisos que ya existían se ACTUALIZAN, no se borran y recrean:
       recrearlos les cambiaría el id y sus avances quedarían huérfanos. */
    if (accion === 'update_reunion') {
      var cambiosR = body.cambios || {};
      // El Word se rehace con el texto corregido. Si el archivado falla, el
      // enlace NO se toca: es preferible que apunte a la versión anterior a que
      // se quede en blanco y parezca que nunca hubo acta.
      var enlaceNuevo = _archivarActa(body.archivo);
      if (enlaceNuevo) cambiosR.enlace_docx = enlaceNuevo;

      var okR = _actualizar('Reuniones', body.id, cambiosR);
      if (!okR) return _json({ ok: false, msg: 'Reunión no encontrada' });

      (body.actualizar_tareas || []).forEach(function (c) {
        _actualizar('Tareas', c.id, c.cambios || {});
      });
      var nNuevas = _agregar('Tareas', body.tareas_nuevas || []);

      // Un compromiso que el gerente quitó del acta se lleva sus avances: son
      // notas sobre algo que ya no existe.
      var fuera = body.tareas_fuera || [];
      var idsS = [];
      if (fuera.length) {
        _leerPestana('Seguimiento').forEach(function (g) {
          if (fuera.indexOf(g.tarea_id) !== -1) idsS.push(g.id);
        });
      }
      var nAv = _borrar('Seguimiento', idsS);
      var nQu = _borrar('Tareas', fuera);

      return _json({ ok: true, nuevas: nNuevas, quitadas: nQu,
                     avances_quitados: nAv, enlace_docx: enlaceNuevo });
    }

    // ── Corrección de datos ya guardados ──
    // Genéricas a propósito: editar un avance, un compromiso o el título de una
    // reunión son la misma operación sobre pestañas distintas, y tener una
    // acción por pestaña multiplicaría el mismo código cuatro veces. La pestaña
    // se valida contra COLUMNAS dentro de _hoja().
    if (accion === 'update_fila') {
      var okF = _actualizar(body.sheet, body.id, body.cambios || {});
      return _json({ ok: okF, msg: okF ? '' : 'No se encontró la fila' });
    }

    if (accion === 'delete_filas') {
      return _json({ ok: true, count: _borrar(body.sheet, body.ids || []) });
    }

    /* Borrar una reunión se lleva por delante sus compromisos y los avances de
       esos compromisos. Si se borrara solo la reunión, las tareas quedarían
       apuntando a un acta que ya no existe y seguirían contando en los
       indicadores del proveedor sin que nadie pudiera abrirlas. */
    if (accion === 'delete_reunion') {
      var idsT = _idsDonde('Tareas', 'reunion_id', body.id);
      // El seguimiento cuelga de la TAREA, no de la reunión: hay que recogerlo
      // por cada tarea que se va, o quedarían avances huérfanos.
      var idsS = [];
      _leerPestana('Seguimiento').forEach(function (g) {
        if (idsT.indexOf(g.tarea_id) !== -1 || String(g.reunion_id) === String(body.id)) {
          idsS.push(g.id);
        }
      });
      var nS = _borrar('Seguimiento', idsS);
      var nT = _borrar('Tareas', idsT);
      var nR = _borrar('Reuniones', [body.id]);
      return _json({ ok: nR > 0, reuniones: nR, tareas: nT, seguimiento: nS,
                     msg: nR ? '' : 'Reunión no encontrada' });
    }

    return _json({ ok: false, msg: 'Acción desconocida: ' + accion });
  } catch (err) {
    return _json({ ok: false, msg: String(err) });
  }
}
