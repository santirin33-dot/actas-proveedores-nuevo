# ADR-001: Por qué Vercel y no Render (como el generador F08)

## Contexto
El generador de actas F08 corre en Render, plan gratuito. Esa app la abre un
director de vez en cuando; que la primera visita del día tarde ~50 segundos en
despertar es tolerable. Actas de Proveedores la abre el gerente **todos los días**,
a veces con el proveedor delante — esa demora ahí sí es un problema real, no
cosmético.

## Decisión
Actas de Proveedores se despliega en **Vercel**, no en Render. Es otro repo, otro
hosting y otra Hoja de Google — solo se reutilizaron patrones de código ya probados
en el F08 (el motor de Gemini, el manejo de fechas, el bloque de OAuth). Tocar esta
app **no puede romper** `generador-actas-gtqs.onrender.com`.

## Consecuencias
Vercel trae su propio conjunto de restricciones distintas a Render (funciones sin
servidor, `maxDuration`, tope de subida por petición) — ver
[ADR-012](012-limites-plataforma-serverless-vercel.md) — y su propio proceso de
despliegue, distinto en el orden al del F08.
