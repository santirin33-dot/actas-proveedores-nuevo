# ADR-009: Diseño del perfil del proveedor

## Contexto
`/proveedor/<id>` reúne todo lo relacionado a un proveedor en una sola pantalla:
indicadores, información, ANS, compromisos abiertos, tareas permanentes e historia.
Antes de este diseño, `api_crear_tarea` ya existía en el backend pero ninguna
plantilla la llamaba — no había forma de registrar una responsabilidad permanente
sin pasar directo por la API.

## Decisión
- El perfil del proveedor es el **único sitio desde donde se crean tareas sueltas**
  (no ligadas a una reunión).
- **Un solo formulario de alta** para los dos tipos que ahí se crean
  (`formularioTarea(tipo)`): un compromiso y una tarea permanente comparten los
  mismos campos salvo el plazo, que la permanente no lleva. Duplicar el formulario
  por esa única diferencia habría dejado dos sitios donde arreglar el mismo fallo.
- **Editar la información del proveedor recarga la página entera**, en vez de
  repintar solo el cuerpo: el nombre y el tipo de servicio del encabezado los
  pinta el servidor al cargar, y un repintado parcial del cuerpo los dejaría
  desactualizados justo encima del dato que se acaba de corregir.

## Consecuencias
Cualquier tarea nueva que no venga de una reunión debe crearse desde este perfil,
no agregando un formulario propio en otra pantalla.
