# Registro de decisiones de arquitectura (ADR)

Cada archivo documenta una decisión ya tomada: qué problema la forzó, qué se
decidió y qué no hay que deshacer sin repetir el análisis. El `CLAUDE.md` del
proyecto asume estas decisiones como vigentes; consultar el ADR correspondiente
antes de tocar el código que menciona.

| ADR | Decisión |
|---|---|
| [001](001-por-que-vercel-no-render.md) | Por qué Vercel y no Render (como el generador F08) |
| [002](002-continuidad-entre-reuniones.md) | Continuidad entre reuniones — inyectar los pendientes abiertos al prompt |
| [003](003-tres-clases-de-trabajo.md) | Tres clases de trabajo en `Tareas`, y la regla vive en un solo sitio |
| [004](004-ans-son-principios-no-tareas.md) | Los ANS son principios, no tareas |
| [005](005-fechas-aaaa-mm-dd.md) | Fechas siempre en AAAA-MM-DD, comparadas como texto |
| [006](006-dos-copias-actas-hoja-y-drive.md) | Las actas viven en dos lugares, con papeles distintos |
| [007](007-formato-acta-dos-columnas.md) | Formato del acta — dos columnas con bloques que no se parten |
| [008](008-roles-diferencia-con-f08.md) | Modelo de roles, y por qué es más estricto que el del F08 |
| [009](009-perfil-proveedor.md) | Diseño del perfil del proveedor |
| [010](010-correccion-de-lo-guardado.md) | Corregir lo ya guardado — mismos caminos que crear |
| [011](011-gotchas-primer-despliegue-vercel.md) | Dos fallas que bloquearon el primer despliegue en Vercel |
| [012](012-limites-plataforma-serverless-vercel.md) | Límites de la plataforma sin servidor (Vercel Hobby) |
| [013](013-decisiones-operativas-no-deshacer.md) | Decisiones operativas que conviene no deshacer sin pensarlo |
| [014](014-hoja-google-no-es-base-de-datos.md) | La Hoja de Google no es una base de datos, y el aislamiento vive en `hoja.py` |
