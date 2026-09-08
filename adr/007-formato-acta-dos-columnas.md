# ADR-007: Formato del acta — dos columnas con bloques que no se parten

## Contexto
El acta ejecutiva se diseñó como una ficha gerencial: banda de datos, resumen a
todo el ancho, los temas en bloques numerados a dos columnas (título, lo hablado,
conclusión etiquetada) y la matriz de compromisos. Un solo color, el verde de la
marca, sobre tintes muy claros, pensado para leerse con el proveedor al lado.

La primera versión de las dos columnas usaba una fila de tabla por par de temas, y
cada fila esperaba a que cupiera el bloque más alto de los dos — dejaba media hoja
en blanco cuando un tema era mucho más largo que su par.

## Decisión
- **Las dos columnas son una sola fila de tabla con dos celdas**, cada una con su
  propia pila de bloques repartidos por longitud de texto (`_repartir`), no
  emparejados uno a uno.
- **Cada bloque es una tabla anidada** con `cantSplit`, para que no se parta entre
  páginas mientras la columna sigue fluyendo. Consecuencia aceptada: si un bloque no
  cabe en lo que queda de página, salta entero a la siguiente — **es normal ver
  espacio libre al final de una página**; es el costo de tener dos columnas con
  párrafos reales en vez de una sola columna.
- **Los anchos se fijan con `tabla.columns[i].width`**, no con el ancho de cada
  celda: Word gobierna el ancho por la rejilla de columnas (`tblGrid`), y fijar solo
  las celdas dejaba la columna del número enorme y la del compromiso estrangulada.
- `python-docx` no expone sombreado, bordes ni márgenes de celda — van como XML a
  mano en `_sombrear`, `_bordes_celda` y `_margenes_celda`.

## Consecuencias
No revertir a "una fila por par de temas" sin resolver primero el problema de
espacio en blanco que originó el cambio.
