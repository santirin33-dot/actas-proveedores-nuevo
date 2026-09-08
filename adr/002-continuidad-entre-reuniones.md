# ADR-002: Continuidad entre reuniones — inyectar los pendientes abiertos al prompt

## Contexto
Sin memoria entre reuniones, cada reunión con un proveedor sería una isla: no
habría forma de saber si un compromiso de la reunión pasada se cumplió, ni de armar
una línea de tiempo de seguimiento real.

## Decisión
Antes de llamar a Gemini, el backend busca los compromisos **abiertos** de
reuniones anteriores con ese mismo proveedor y se los inyecta al prompt. La IA
reporta cuáles se mencionaron en la reunión actual y qué avance hubo; eso se guarda
en la pestaña `Seguimiento` y es lo que dibuja la línea de tiempo.

Regla estricta del prompt: **si un pendiente no se mencionó en la reunión, no se
reporta.** No se marca nada por omisión — sigue pendiente y así queda.

## Consecuencias
Cualquier cambio al prompt de `prompts.py` debe mantener esta regla explícita; sin
ella el modelo puede inferir avance donde no se habló de un tema, lo que
contaminaría el historial de seguimiento con progreso que nunca ocurrió.
