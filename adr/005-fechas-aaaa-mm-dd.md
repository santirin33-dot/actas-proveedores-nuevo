# ADR-005: Fechas siempre en AAAA-MM-DD, comparadas como texto

## Contexto
Mismo problema ya resuelto en el generador F08 (ver su ADR-016): en texto largo
("10 de junio"), una comparación alfabética ordenaría antes que "5 de mayo". Además,
si la celda de la Hoja de Google queda con formato de fecha nativo, la API la
devuelve como `2026-08-20T05:00:00.000Z`, que el navegador puede leer como fecha
inválida — con ese bug, una tarea vencida nunca aparecería como vencida.

Un segundo problema, propio de JavaScript: comparar fechas con `new Date()` las
interpreta en UTC, y en Colombia (UTC-5) eso corre el día hacia atrás — una tarea
con vencimiento "hoy" podía leerse como vencida desde ayer.

## Decisión
Las fechas se guardan siempre como texto en formato `AAAA-MM-DD`. `fecha_iso()` en
`hoja.py` normaliza al guardar y `Utilities.formatDate` (en Apps Script) al mostrar.
En el navegador, las fechas se comparan **como texto** (comparación de cadenas
ISO ordena igual que el calendario), nunca con `new Date()`.

## Consecuencias
Cualquier código nuevo que compare o filtre fechas en el frontend debe comparar los
strings `AAAA-MM-DD` directamente, no construir objetos `Date` para comparar.
