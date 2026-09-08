# ADR-011: Dos fallas que bloquearon el primer despliegue en Vercel

## Contexto
El primer despliegue en Vercel falló dos veces por razones que no eran evidentes
desde el mensaje de error.

## Decisión / hallazgo

**Nada de `rewrites` en `vercel.json`.**
Vercel detecta el proyecto como Flask (`Application Preset: Flask`) y ya enruta
todas las rutas a la app. Agregar un rewrite catch-all propio se suma a ese
enrutado, y la app termina recibiendo siempre la misma ruta interna: el guardia de
acceso responde **401 a todo**, incluidas `/login` y `/health`, y parece un
problema de permisos cuando en realidad es de enrutado duplicado. El build lo avisa
con `WARNING! Internal rewrites in backend framework projects` — no ignorar ese
warning.

**El correo del autor del commit tiene que ser uno real de la cuenta de GitHub.**
Si git no tiene `user.email` configurado, macOS inventa
`usuario@NombreDelMac.local`, y Vercel **bloquea el despliegue** antes de siquiera
compilar. Quedó puesto en la configuración global de git como
`287859181+santirin33-dot@users.noreply.github.com`.

## Consecuencias
Antes de tocar `vercel.json`, no agregar `rewrites` sin entender que el preset de
Flask ya enruta todo. Si un despliegue nuevo falla con 401 generalizado o se
rechaza antes de compilar, revisar primero estas dos causas.
