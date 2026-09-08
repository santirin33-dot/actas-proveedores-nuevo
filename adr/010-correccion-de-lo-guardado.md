# ADR-010: Corregir lo ya guardado — mismos caminos que crear, nunca un editor aparte

## Contexto
Con 18 reuniones y 121 compromisos ya en producción, poder arreglar un error pesa
tanto como poder crear un registro nuevo. Un editor separado del flujo de creación
tiende a acumular sus propios defectos con el tiempo.

## Decisión
- **Editar un acta** reutiliza `/reunion/<id>/editar`, la **misma pantalla de
  revisión** donde se aprueba el acta antes de guardarla la primera vez — es donde
  el acta se lee entera, y un segundo editor sería una segunda forma de hacer lo
  mismo con sus propios defectos. Al guardar, los compromisos que ya existían se
  **actualizan**, no se borran y se recrean: recrearlos les cambiaría el id y sus
  avances de seguimiento quedarían huérfanos.
- **Borrar un acta** se lleva en cascada sus compromisos y los avances de esos
  compromisos — a propósito: de lo contrario esas tareas seguirían contando en los
  indicadores sin que nadie pudiera abrirlas para revisarlas.
- **Un avance** se corrige o se borra desde el historial de la tarea, no desde el
  acta que lo originó.

## Consecuencias
No crear una pantalla de edición nueva para actas o compromisos — extender la
pantalla de revisión existente en vez de duplicarla.
