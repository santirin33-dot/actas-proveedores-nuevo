# ADR-014: La Hoja de Google no es una base de datos, y el aislamiento vive en `hoja.py`

## Contexto
Se eligió Google Sheets como almacenamiento porque el volumen real (un gerente,
decenas de reuniones al año) no lo justifica una base de datos propia, y porque el
equipo ya opera con Hojas de Google para todo lo demás. Pero Sheets no ofrece
transacciones y cada lectura trae la pestaña completa — eso no escala
indefinidamente.

## Decisión
Se acepta la limitación mientras el volumen de uso sea el actual. Para que el día
que se necesite cambiar a otra cosa (Firestore, por ejemplo) el costo sea bajo,
**`hoja.py` es el único archivo del proyecto que sabe que los datos viven en una
Hoja de Google** — el resto de la app (rutas, plantillas, motor de IA) no conoce el
mecanismo de almacenamiento, solo llama a las funciones de `hoja.py`.

## Consecuencias
Cualquier acceso a datos nuevo debe pasar por `hoja.py`, nunca leer o escribir la
Hoja de Google directamente desde otro módulo — hacerlo rompería el único punto de
reemplazo que esta decisión protege.
