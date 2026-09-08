# ADR-012: Límites de la plataforma sin servidor (Vercel Hobby)

## Contexto
Vercel impone límites propios de un entorno serverless que no existían en el
Render del F08 (un proceso persistente).

## Decisión
- **`maxDuration` en 300 s** en `vercel.json` — el máximo del plan Hobby con fluid
  compute. Generar un acta toma entre 20 y 60 s, así que sobra margen. Si Vercel
  llegara a rechazar ese valor, bajarlo y verificar que la generación siga cabiendo
  dentro del nuevo límite.
- **Tope de subida de 4,5 MB por petición**, impuesto por la plataforma, no por la
  app. `TOPE_SUBIDA` en `app.py` refleja ese mismo número para poder mostrar un
  mensaje entendible al usuario en vez de un error crudo de la plataforma. Un
  `.docx` o `.txt` nunca se acerca a ese tamaño; un PDF escaneado largo sí puede.
- **El caché de `hoja.py` es por instancia** de función serverless, no compartido
  entre instancias — ver el comentario del propio módulo para el detalle de
  invalidación.

## Consecuencias
Cualquier funcionalidad que suba archivos grandes (por ejemplo, adjuntar
documentos extensos a una reunión) debe validar contra `TOPE_SUBIDA` antes de
enviar la petición, no depender de que Vercel devuelva un error claro por su
cuenta.
