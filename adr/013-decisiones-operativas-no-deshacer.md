# ADR-013: Decisiones operativas que conviene no deshacer sin pensarlo

## Contexto
Cinco decisiones puntuales, tomadas por razones concretas de integridad de datos y
experiencia de uso, agrupadas aquí porque ninguna necesita su propio ADR extenso
pero todas son fáciles de revertir "por prolijidad" sin notar por qué existen.

## Decisiones

**Paso de revisión antes de guardar.**
`/api/generar` no escribe nada en la Hoja: el gerente corrige el borrador en
pantalla y solo al confirmar se llama a `/api/reuniones`. Esto impide que la IA
meta compromisos inventados directo en el histórico, que después contaminarían el
tablero y la línea de tiempo sin que nadie lo notara a tiempo.

**Solo se acepta seguimiento de ids que existen de verdad.**
Si Gemini devuelve, en el reporte de continuidad (ver
[ADR-002](002-continuidad-entre-reuniones.md)), un id de tarea inventado o de otro
proveedor, se descarta en el servidor antes de guardarlo.

**El semáforo solo aparece si hay fecha límite puesta a mano.**
Sin plazo explícito no se inventa urgencia — misma regla que el panel de tareas del
generador F08.

**Escrituras síncronas.**
A diferencia del F08, que registra en segundo plano (fire-and-forget), aquí se
espera la respuesta de la Hoja y se revisa `ok:false` antes de confirmar al
usuario. Sin eso, la pantalla podría decir "guardado" y al recargar el cambio no
estaría ahí.

**Caché de 60 s en `hoja.py`.**
Toda escritura invalida la pestaña que tocó, así que el usuario nunca ve su propio
cambio desactualizado. Si la Hoja falla al leer, se devuelve lo último que quedó en
caché antes que mostrar un tablero en ceros que parezca pérdida de datos.

## Consecuencias
Ninguna de estas cinco reglas es incidental — revertir cualquiera reabre un
problema concreto de integridad de datos o de confianza del usuario en lo que ve
en pantalla.
