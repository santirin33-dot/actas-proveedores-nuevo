/* Service worker de Actas de Proveedores.

   Existe por DOS razones y ninguna es velocidad: que la app se pueda instalar en
   el teléfono, y que al abrirla sin señal aparezca algo escrito en vez del error
   del navegador.

   REGLA DURA: NUNCA se guarda en caché una página ni una respuesta de /api/.

   Dos motivos, y el segundo es el que manda:

   1. Los datos vienen de una Hoja de Google y cambian todo el día. Una tabla
      servida desde caché mostraría compromisos que ya se cerraron.
   2. La app va detrás de un inicio de sesión y hay perfiles con permisos
      distintos. Guardar el HTML de una sesión en el disco del dispositivo
      significa que la siguiente persona que abra la app en ese mismo equipo
      podría ver los datos de la anterior. Eso no se arregla con un caché bien
      configurado: se evita no guardando nada.

   Lo único que se guarda son los archivos estáticos —hoja de estilos e
   iconos—, que no llevan datos de nadie. */

const CACHE = "actas-estaticos-v1";

/* Solo lo que hace falta para que la pantalla sin conexión se vea como la app y
   no como una página rota. */
const ESTATICOS = [
  "/static/estilo.css",
  "/static/marca.svg",
  "/static/icono-192.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => c.addAll(ESTATICOS))
      // Si un archivo no está, la instalación NO debe fallar: sin service
      // worker la app funciona igual, y romper la instalación por un icono
      // sería cambiar una molestia por un fallo.
      .catch(() => {})
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((claves) => Promise.all(
        claves.filter((k) => k !== CACHE).map((k) => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Páginas: siempre de la red. Sin señal, una nota escrita.
  if (req.mode === "navigate") {
    e.respondWith(
      fetch(req).catch(() => new Response(SIN_CONEXION, {
        status: 503,
        headers: { "Content-Type": "text/html; charset=utf-8" },
      }))
    );
    return;
  }

  // Datos: red o nada. Un compromiso vencido servido de caché es peor que un
  // error honesto.
  if (url.pathname.startsWith("/api/")) return;

  // Estáticos: la red manda, y el caché solo entra si no hay señal. Al revés
  // —caché primero— una hoja de estilos vieja sobreviviría a los despliegues.
  if (url.pathname.startsWith("/static/")) {
    e.respondWith(
      fetch(req)
        .then((res) => {
          if (res && res.ok) {
            const copia = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copia)).catch(() => {});
          }
          return res;
        })
        .catch(() => caches.match(req))
    );
  }
});

const SIN_CONEXION = `<!doctype html>
<html lang="es-CO"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sin conexión · Actas de Proveedores</title>
<style>
  body { margin:0; min-height:100vh; display:grid; place-items:center;
         background:#EDF1F7; color:#17202A; text-align:center; padding:24px;
         font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  .caja { max-width:34ch; }
  img { width:72px; height:72px; margin-bottom:20px; }
  h1 { margin:0 0 8px; font-size:20px; color:#1F3554; }
  p  { margin:0; font-size:15px; color:#344054; line-height:1.5; }
</style></head>
<body><div class="caja">
  <img src="/static/icono-192.png" alt="">
  <h1>Sin conexión</h1>
  <p>Los datos vienen de la Hoja de Google, así que hace falta señal para
     verlos. Vuelve a intentarlo cuando tengas red.</p>
</div></body></html>`;
