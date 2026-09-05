# Actas de Proveedores — Abelardo Yepes S.A.S.
**Para:** Gerencia de Proveedores · **Administra:** Santiago Rincón

## Qué es
App web (Flask) que convierte la transcripción de una reunión con un proveedor en un
**acta ejecutiva** —temas, conclusiones y compromisos— usando **Google Gemini**, la guarda,
y desde ahí arma un **tablero de seguimiento** y una **línea de tiempo por proveedor**.

**No tiene nada que ver en ejecución con el generador de actas F08.** Otro repo, otro
hosting, otra Hoja de Google. Solo se copiaron patrones de código ya probados (el motor de
Gemini, el manejo de fechas, el bloque de OAuth). Tocar esta app **no puede romper**
`generador-actas-gtqs.onrender.com`.

Se desplegó en **Vercel** y no en Render como el F08. La razón es concreta: el plan gratis
de Render duerme la app por inactividad y la primera visita del día se demora ~50 segundos,
y esta la abre el gerente todos los días, a veces delante del proveedor.

## La idea central: continuidad entre reuniones
Antes de llamar a Gemini, el backend busca los compromisos **abiertos** de reuniones
anteriores con ese mismo proveedor y **se los inyecta al prompt**. La IA reporta cuáles se
mencionaron y qué avance hubo; eso se guarda en la pestaña `Seguimiento` y es lo que dibuja
la línea de tiempo. Sin esa inyección, cada reunión sería una isla.

Regla estricta del prompt: **si un pendiente no se mencionó en la reunión, no se reporta**.
No se marca nada por omisión — sigue pendiente y así queda.

## Estructura
```
ActasProveedores/
├── app/
│   ├── app.py           ← Flask: rutas, OAuth, roles
│   ├── hoja.py          ← ÚNICA capa de datos (Hoja de Google) + caché de 60 s
│   ├── motor_ia.py      ← motor de Gemini resistente (copiado del F08)
│   ├── prompts.py       ← el prompt del acta de proveedores
│   ├── build_acta.py    ← el .docx, armado desde cero (sin plantilla)
│   ├── templates/       ← base, generador, dashboard, timeline, tareas, proveedores…
│   └── static/estilo.css
├── api/index.py         ← punto de entrada de Vercel (solo expone la app de Flask)
├── vercel.json          ← solo maxDuration e includeFiles (el enrutado lo hace el preset)
├── requirements.txt     ← dependencias (en la raíz: ahí las busca Vercel)
├── docs/GUIA_DISENO_DASHBOARD.md ← guía visual de la casa; manda sobre el front
├── apps_script/Codigo.gs ← copia de referencia del Web App (el real vive en Apps Script)
├── dev/                 ← simulador de la Hoja, sembrador de datos, arranque local
└── iniciar.sh           ← arranque local (gitignored)
```

## Modelo de datos — Hoja "Actas Proveedores"
Cuatro pestañas; las columnas exactas están en `COLUMNAS` de `apps_script/Codigo.gs`.
Si se reordenan en la hoja, **hay que reordenarlas ahí también**.

| Pestaña | Para qué |
|---|---|
| `Proveedores` | catálogo: nombre, tipo de servicio, contacto, estado |
| `Reuniones` | una fila por reunión; el acta completa va serializada en `temas_json`, y `enlace_docx` apunta al archivo en Drive |
| `Tareas` | los compromisos; `tarea_origen_id` encadena una tarea con la que la originó |
| `Seguimiento` | bitácora de avances: alimenta la línea de tiempo y el historial |

Las fechas se guardan **siempre** en `AAAA-MM-DD`. Es lo mismo que ya se corrigió en el
generador F08: en texto largo, "10 de junio" ordenaría antes que "5 de mayo", y si la celda
queda como fecha, la Hoja devuelve `2026-08-20T05:00:00.000Z` y el navegador la lee como
inválida — la tarea nunca aparecería vencida. `fecha_iso()` en `hoja.py` normaliza a la
entrada y `Utilities.formatDate` a la salida.

En el navegador las fechas se comparan **como texto**, nunca con `new Date()`: eso las
interpreta en UTC y en Colombia (UTC-5) corre el día hacia atrás.

## Dónde quedan las actas
Dos copias, con papeles distintos:

1. **Los datos, en la Hoja.** Texto, temas, conclusiones y compromisos. Es lo que alimenta
   el tablero y la línea de tiempo, y desde ahí el `.docx` se puede reconstruir siempre.
2. **El archivo, en Google Drive.** Al guardar la reunión, la app arma el `.docx` y lo manda
   en base64 dentro de la misma llamada `add_reunion`; el Web App lo deja en
   `Actas de Proveedores / <Nombre del proveedor> /` y devuelve el enlace, que se guarda en
   la columna `enlace_docx`. Ese enlace es el que el gerente le puede pegar al proveedor en
   un correo.

La carpeta se busca por nombre y se crea si no existe, así que no hay ningún id que pegar a
mano. **Si la renombras en Drive, la próxima acta creará una carpeta nueva** con el nombre
original y las anteriores quedarán en la vieja.

Si Drive falla, `_archivarActa()` devuelve `''` y la fila se guarda igual con el enlace
vacío: perder el archivo es molesto, perder el registro de la reunión sería grave. En la
interfaz, esas reuniones muestran «Descargar Word» en vez de «Abrir acta» y el documento se
reconstruye al vuelo — que es también lo que pasa con las reuniones guardadas antes de que
existiera la carpeta.

El `.docx` se arma **en memoria** (`_docx_bytes` en `app.py`). No hay archivos temporales:
la primera versión usaba `NamedTemporaryFile(delete=False)` y cada descarga dejaba un
documento abandonado en el disco del servidor.

### Formato del acta (`build_acta.py`)
Ficha gerencial: banda de datos, resumen a todo el ancho, los temas como bloques numerados
**en dos columnas** —título, lo que se habló, y la conclusión etiquetada— y la matriz de
compromisos. Un solo color, el verde de la marca, sobre tintes muy claros: el documento se
lee con el proveedor al lado.

Tres cosas que hay que saber antes de tocarlo:

- **Las dos columnas son una sola fila de tabla con dos celdas**, cada una con su pila de
  bloques, repartidos por longitud de texto (`_repartir`). La versión anterior usaba una fila
  por par de temas y cada fila esperaba a que cupiera el bloque más alto: dejaba media hoja
  en blanco.
- **Cada bloque es una tabla anidada** con `cantSplit`, para que no se parta entre páginas
  mientras la columna sigue fluyendo. Como consecuencia, si un bloque no cabe en lo que queda
  de página, salta entero: **es normal ver espacio libre al final de una página**. Es el costo
  de las dos columnas con párrafos de verdad; con una sola columna no pasaría.
- **Los anchos se fijan con `tabla.columns[i].width`**, no con el ancho de cada celda. Word
  manda por la rejilla de columnas (`tblGrid`); fijando solo las celdas, la columna del número
  salía enorme y la del compromiso estrangulada.

`python-docx` no expone sombreado, bordes ni márgenes de celda: van como XML a mano en los
ayudantes `_sombrear`, `_bordes_celda` y `_margenes_celda`.

## Variables de entorno (se configuran en Vercel, nunca en el repo)
| Variable | Para qué |
|---|---|
| `GEMINI_API_KEY`, `_2..7` | Llaves de Gemini. La app **rota** entre ellas para no topar la cuota gratis. |
| `LOG_URL` | Web App de Apps Script que lee y escribe la Hoja. **Sin esto no se guarda nada** (la app avisa en pantalla). |
| `SECRET_KEY` | Firma de sesiones. **Obligatoria en Vercel**: cada instancia es distinta, así que sin una clave fija las sesiones se cierran solas. Si falta, la app lo avisa en un banner rojo. |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Login con Google. |
| `DOMINIO_PERMITIDO` | `abelardoyepes.com` → todo ese dominio puede entrar y escribir. |
| `SUPERADMIN` | Santiago. Siempre tiene acceso total. |
| `GERENTE` | Correos con permiso de escritura (el gerente de proveedores). Separados por coma. |
| `LECTORES` | Correos de **solo consulta**: ven el tablero pero no pueden cambiar nada. |
| `DEV_LOCAL` | Solo local: salta el login. **Nunca ponerla en Vercel.** |

### Roles
`puede_leer()` y `puede_escribir()` en `app.py`. Un correo que esté en `LECTORES` y no en
`GERENTE` no escribe, aunque sea del dominio. La comprobación está **en el servidor**, no
solo escondiendo botones: un lector podría llamar la API directamente.

Diferencia deliberada con el generador F08: allá, sin OAuth configurado, `es_gerencia()`
devuelve `True` y cualquiera con la contraseña ve todo. Aquí, sin Google y sin `DEV_LOCAL`,
**no entra nadie**.

## Uso local
```bash
cd ~/Desktop/Claude/ActasProveedores
python3 -m pip install -r requirements.txt
python3 dev/servidor_local.py       # app + simulador de la Hoja, todo en uno → :5052
```
`iniciar.sh` toma la llave de Gemini de la del generador de actas, para que siga existiendo
en un solo archivo del computador. Los datos de prueba quedan en `dev/datos_prueba.json` y
las actas archivadas en `dev/actas/<Proveedor>/`, que es el equivalente local de la carpeta
de Drive. Ambos están en `.gitignore`.

```bash
python3 dev/sembrar.py --limpio    # datos de ejemplo con vencidos y seguimiento
```

## Despliegue

Hay que hacerlo **en este orden**: la Hoja produce la `LOG_URL` que necesita Vercel, y
Vercel produce el dominio que necesita Google Cloud para el login.

### 1. La Hoja de Google y el Apps Script
Todo en la **cuenta de la empresa** (`@abelardoyepes.com`), nunca en una personal: de esa
cuenta dependen la Hoja, el Web App y el Drive donde caen las actas.

1. Crear una hoja de cálculo llamada **Actas Proveedores**. No hay que crear pestañas ni
   encabezados: el script los crea solo la primera vez.
2. Extensiones → Apps Script. Borrar el contenido y pegar `apps_script/Codigo.gs`.
3. Implementar → Nueva implementación → **Aplicación web**, con
   **"Ejecutar como: Yo"** y **"Quién tiene acceso: Cualquier persona"**.
4. Aceptar los permisos. Pedirá acceso a **Drive** (el script crea las carpetas y los
   archivos de las actas) y a la **hoja**. Sin el permiso de Drive las reuniones se guardan
   pero ningún acta queda archivada.
5. Copiar la URL que queda: esa es `LOG_URL`.

Comprobación antes de seguir: abrir `LOG_URL?sheet=Proveedores` en el navegador. Debe
responder `[]`. Si devuelve HTML, la implementación quedó mal publicada (casi siempre por
"Quién tiene acceso"); la app también lo dice en pantalla si pasa.

### 2. Credenciales de Google para el login
En Google Cloud, sobre el proyecto que ya existe para el generador F08:

1. APIs y servicios → Credenciales → Crear credenciales → **ID de cliente de OAuth**,
   tipo *Aplicación web*.
2. Dejarlo abierto: la URI de redirección se agrega en el paso 4, cuando ya exista el
   dominio de Vercel.

### 3. Repo y Vercel
1. Repo **privado** nuevo en GitHub (`actas-proveedores`). Push a `main` = despliegue.
2. Vercel → Add New Project → importar el repo. **No hay que configurar build**: el
   `vercel.json` y `requirements.txt` de la raíz ya lo dicen todo.
3. Cargar las variables de entorno de la tabla de arriba. `SECRET_KEY` puede ser cualquier
   cadena larga al azar (`python3 -c "import secrets; print(secrets.token_hex(32))"`).
4. Desplegar. Verificar `https://<dominio>/health`: debe responder
   `{"status":"ok","hoja":true}`. Si `hoja` sale `false`, falta `LOG_URL`.

### 4. Cerrar el login
1. Copiar el dominio de Vercel y agregar a la credencial de OAuth la URI de redirección
   `https://<dominio>/auth/callback`.
2. Entrar con la cuenta de David y confirmar que pasa del login al tablero.

### 5. Compartirle a David
- La **Hoja**, con permiso de edición.
- La carpeta de Drive **Actas de Proveedores**, con permiso de edición.
- La URL de la app.

### Al actualizar
- **Código de la app:** push a `main` y Vercel redespliega solo.
- **`Codigo.gs`:** hay que **volver a implementar con versión nueva** (Implementar →
  Administrar implementaciones → editar → Versión: Nueva). Si solo se guarda, sigue
  corriendo la versión anterior y los cambios no tienen efecto.

### Dos cosas que bloquearon el primer despliegue
- **Nada de `rewrites` en `vercel.json`.** Vercel detecta el proyecto como Flask
  (`Application Preset: Flask`) y ya enruta todas las rutas a la app. Un rewrite catch-all
  propio se suma a ese enrutado y la app recibe siempre la misma ruta interna: el guardia de
  acceso responde **401 a todo**, incluidas `/login` y `/health`, y parece un problema de
  permisos cuando es de enrutado. El build lo avisa con
  `WARNING! Internal rewrites in backend framework projects`.
- **El correo del autor del commit tiene que ser uno real de la cuenta de GitHub.** Si git no
  tiene `user.email` configurado, macOS inventa `usuario@NombreDelMac.local` y Vercel
  **bloquea el despliegue** antes de compilar. Está puesto en la configuración global como
  `287859181+santirin33-dot@users.noreply.github.com`.

### Notas del entorno sin servidor
- `maxDuration` está en **300 s** en `vercel.json`, que es el máximo del plan Hobby con
  fluid compute. Generar un acta toma 20-60 s, así que sobra. Si algún día Vercel rechaza
  ese valor, bajarlo y verificar que la generación siga cabiendo.
- **Tope de subida de 4,5 MB por petición**, impuesto por la plataforma. `TOPE_SUBIDA` en
  `app.py` lo refleja para poder dar un mensaje entendible en vez de un error crudo. Un
  `.docx` o `.txt` nunca se acerca; un PDF escaneado largo sí puede.
- El caché de `hoja.py` es por instancia (ver el comentario del módulo).

## Decisiones que conviene no deshacer sin pensarlo
- **Paso de revisión antes de guardar.** `/api/generar` no escribe nada: el gerente corrige
  el borrador y solo al confirmar se llama a `/api/reuniones`. Es lo que impide que la IA
  meta compromisos inventados en el histórico, que después contaminarían el tablero.
- **Solo se acepta seguimiento de ids que existen de verdad.** Si Gemini devuelve un id
  inventado o de otro proveedor, se descarta en el servidor.
- **El semáforo solo aparece si hay fecha límite puesta a mano.** Sin plazo no se inventa
  urgencia — misma regla que el panel de tareas del F08.
- **Escrituras síncronas.** A diferencia del F08, que registra en segundo plano, aquí se
  espera la respuesta de la Hoja y se revisa `ok:false`. Si no, la pantalla diría "guardado"
  y al recargar el cambio no estaría.
- **Caché de 60 s en `hoja.py`.** Toda escritura invalida la pestaña que tocó, así que el
  usuario nunca ve su propio cambio desactualizado. Si la Hoja falla, se devuelve lo último
  en caché antes que un tablero en ceros que parezca pérdida de datos.

## Limitación conocida
La Hoja de Google **no es una base de datos**: cada lectura trae la pestaña completa y no
hay transacciones. Con un gerente y decenas de reuniones al año rinde de sobra. Si algún día
se queda corta, `hoja.py` es el **único** archivo a reemplazar (por Firestore, por ejemplo):
el resto de la app no sabe de dónde salen los datos.
