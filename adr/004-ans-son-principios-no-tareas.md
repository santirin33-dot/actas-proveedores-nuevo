# ADR-004: Los ANS son principios, no tareas

## Contexto
Un Acuerdo de Nivel de Servicio (ANS) es una condición del contrato con el
proveedor ("tiempo de respuesta menor a 24h", por ejemplo), no un compromiso puntual
con fecha de entrega. Modelarlo como una tarea más habría exigido inventarle una
fecha límite y un estado de cumplimiento que no le corresponden.

## Decisión
Decisión de Santiago, y es lo que simplifica todo el módulo: **un ANS no tiene
fecha, ni caducidad, ni estado de cumplimiento.** Al ser un principio del contrato,
se entiende cumplido por defecto. Lo único que tiene es `activo`, para retirar un
acuerdo que dejó de estar vigente — eso es ciclo de vida del acuerdo, no
incumplimiento de una tarea.

Cuando toca ejecutar un ANS concreto (por ejemplo, una revisión trimestral
pactada), **Convertir en tarea** crea una tarea `tipo=ans` con `ans_id` apuntando al
acuerdo. El ANS en sí no cambia; la tarea es solo una de sus ejecuciones.

## Consecuencias
No agregar campos de fecha o estado directamente al ANS — cualquier necesidad de
seguimiento de una ejecución concreta pasa por crear una tarea `tipo=ans`, nunca por
extender el modelo del ANS mismo.
