# ADR-006: Las actas viven en dos lugares, con papeles distintos

## Contexto
El acta necesita ser consultable como datos (para alimentar el tablero y la línea
de tiempo) y también entregable como documento (para que el gerente se lo pueda
compartir al proveedor). Un solo lugar de almacenamiento no cubre los dos usos
bien.

## Decisión
- **Los datos, en la Hoja de Google.** Texto, temas, conclusiones y compromisos.
  Es la fuente de verdad: desde ahí el `.docx` se puede reconstruir siempre.
- **El archivo, en Google Drive.** Al guardar la reunión, la app arma el `.docx` y
  lo manda en base64 dentro de la misma llamada `add_reunion`; el Web App lo deja en
  `Actas de Proveedores / <Nombre del proveedor> /` y devuelve el enlace, guardado en
  la columna `enlace_docx`. La carpeta se busca por nombre y se crea si no existe —
  no hay ningún id que pegar a mano, pero **si se renombra la carpeta en Drive, la
  próxima acta crea una carpeta nueva** con el nombre original y las anteriores
  quedan en la vieja.
- **Si Drive falla**, `_archivarActa()` devuelve `''` y la fila se guarda igual con
  el enlace vacío: perder el archivo es molesto, perder el registro de la reunión
  sería grave. Esas reuniones muestran "Descargar Word" en vez de "Abrir acta" y el
  documento se reconstruye al vuelo desde los datos de la Hoja — lo mismo que pasa
  con reuniones guardadas antes de que existiera la carpeta.
- **El `.docx` se arma en memoria** (`_docx_bytes` en `app.py`). La primera versión
  usaba `NamedTemporaryFile(delete=False)` y cada descarga dejaba un documento
  abandonado en el disco del servidor.

## Consecuencias
El guardado de una reunión nunca debe depender de que Drive responda — la Hoja es
la fuente de verdad y Drive es un adjunto conveniente, no al revés.
