#!/usr/bin/env python3
"""
Única capa de acceso a los datos: la Hoja de Google, a través del Web App de
Apps Script publicado en la variable de entorno LOG_URL.

Todo el resto de la app llama solo a `leer()` y `escribir()`. Si algún día la
Hoja se queda corta y hay que pasar a una base de datos de verdad (Firestore,
Postgres), este es el ÚNICO archivo que cambia.

Detalle importante: la Hoja no es una base de datos y cada lectura trae la
pestaña completa por HTTP (~1-2 s). Por eso hay un caché en memoria de 60 s por
pestaña; cualquier escritura invalida la pestaña que tocó, así que el usuario
nunca ve su propio cambio desactualizado.

En Vercel el caché rinde menos de lo que parece: la app corre como función sin
servidor y cada instancia tiene su propia memoria, así que un usuario puede caer
en una instancia con el caché frío y esperar la lectura completa. No es un error
—los datos siempre son correctos— pero explica por qué algunas cargas del tablero
tardan un par de segundos más que otras.
"""
import os, re, json, time, logging, threading

LOG_URL = os.environ.get("LOG_URL", "").strip()

PESTANAS = ("Proveedores", "Reuniones", "Tareas", "Seguimiento", "ANS")

# Segundos que se considera fresco lo leído. Con un solo usuario, 60 s es
# invisible al usar la app y evita cientos de llamadas a Apps Script.
TTL = 60

_cache = {}                 # pestaña -> (momento, filas)
_lock = threading.Lock()


def configurada():
    """False si falta LOG_URL: la app funciona pero avisa que no está guardando."""
    return bool(LOG_URL)


# ─────────────────────────── Fechas ───────────────────────────
_MESES_ES = {"enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
             "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
             "septiembre": "09", "setiembre": "09", "octubre": "10",
             "noviembre": "11", "diciembre": "12"}


def fecha_iso(texto, respaldo=""):
    """Normaliza una fecha a AAAA-MM-DD.

    Todo el tablero ordena, agrupa y calcula vencimientos con este formato. En
    texto no serviría: "10 de junio" ordenaría antes que "5 de mayo". Además la
    Hoja puede devolver la celda como fecha completa ("2026-08-20T05:00:00.000Z")
    según cómo haya quedado formateada, y sin normalizar eso el navegador la lee
    como inválida y la tarea nunca aparece vencida.
    """
    t = str(texto or "").strip().lower()
    m = re.match(r"(\d{4}-\d{2}-\d{2})(?:[t ]|$)", t)
    if m:
        return m.group(1)
    m = re.search(r"(\d{1,2})\s*de\s*([a-záéíóú]+)\s*de\s*(\d{4})", t)
    if m and m.group(2) in _MESES_ES:
        return f"{m.group(3)}-{_MESES_ES[m.group(2)]}-{int(m.group(1)):02d}"
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", t)          # 15/07/2026
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return respaldo


def hoy():
    from datetime import datetime, timezone, timedelta
    return datetime.now(timezone(timedelta(hours=-5))).strftime("%Y-%m-%d")   # Colombia


def ahora():
    from datetime import datetime, timezone, timedelta
    return datetime.now(timezone(timedelta(hours=-5))).strftime("%Y-%m-%d %H:%M")


def nuevo_id(prefijo):
    """Id legible y ordenable en el tiempo: PRE-20260729103012-a1b2c3."""
    import uuid
    from datetime import datetime, timezone, timedelta
    sello = datetime.now(timezone(timedelta(hours=-5))).strftime("%Y%m%d%H%M%S")
    return f"{prefijo}-{sello}-{uuid.uuid4().hex[:6]}"


# ─────────────────────────── Lectura ───────────────────────────
_CAMPOS_FECHA = ("fecha", "fecha_limite", "fecha_creacion")


def _normalizar(filas):
    for f in filas:
        for campo in _CAMPOS_FECHA:
            if campo in f:
                f[campo] = fecha_iso(f[campo], "")
    return filas


def leer(pestana, forzar=False):
    """Devuelve la pestaña completa como lista de diccionarios.

    Si la Hoja no responde, devuelve lo último que haya en caché (aunque esté
    vencido) antes que una lista vacía: es preferible mostrar datos de hace unos
    minutos que un tablero en ceros que parezca que se perdió la información.
    """
    if pestana not in PESTANAS:
        raise ValueError(f"Pestaña desconocida: {pestana}")
    if not LOG_URL:
        return []

    with _lock:
        guardado = _cache.get(pestana)
    if guardado and not forzar and (time.time() - guardado[0]) < TTL:
        return guardado[1]

    try:
        import requests
        data = requests.get(LOG_URL, params={"sheet": pestana}, timeout=20).json()
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(data["error"])
        filas = _normalizar([dict(f) for f in (data or [])])
        with _lock:
            _cache[pestana] = (time.time(), filas)
        return filas
    except Exception:
        logging.exception("No se pudo leer la pestaña %s de la Hoja", pestana)
        return guardado[1] if guardado else []


def leer_todo(forzar=False):
    """Las cuatro pestañas de una sola llamada HTTP (lo que usa el tablero)."""
    if not LOG_URL:
        return {"proveedores": [], "reuniones": [], "tareas": [],
                "seguimiento": [], "ans": []}

    frescas = all(
        (g := _cache.get(p)) and (time.time() - g[0]) < TTL for p in PESTANAS
    ) if not forzar else False
    if frescas:
        return {
            "proveedores": _cache["Proveedores"][1],
            "reuniones":   _cache["Reuniones"][1],
            "tareas":      _cache["Tareas"][1],
            "seguimiento": _cache["Seguimiento"][1],
            "ans":         _cache["ANS"][1],
        }

    try:
        import requests
        data = requests.get(LOG_URL, params={"sheet": "todo"}, timeout=25).json() or {}
        salida = {}
        for clave, pestana in (("proveedores", "Proveedores"), ("reuniones", "Reuniones"),
                               ("tareas", "Tareas"), ("seguimiento", "Seguimiento"),
                               ("ans", "ANS")):
            filas = _normalizar([dict(f) for f in (data.get(clave) or [])])
            with _lock:
                _cache[pestana] = (time.time(), filas)
            salida[clave] = filas
        return salida
    except Exception:
        logging.exception("No se pudo leer la Hoja completa")
        return {
            "proveedores": leer("Proveedores"),
            "reuniones":   leer("Reuniones"),
            "tareas":      leer("Tareas"),
            "seguimiento": leer("Seguimiento"),
            "ans":         leer("ANS"),
        }


def invalidar(*pestanas):
    with _lock:
        for p in (pestanas or PESTANAS):
            _cache.pop(p, None)


# ─────────────────────────── Escritura ───────────────────────────
def escribir(accion, payload, invalida=()):
    """Envía una acción al Web App y ESPERA la respuesta.

    Se hace síncrono a propósito: son acciones que el usuario acaba de pedir
    ("guardar reunión", "marcar completada") y necesita saber si de verdad
    quedaron. La Hoja puede responder {ok:false} —por ejemplo, id no encontrado—
    y sin revisarlo la pantalla diría "guardado" y al recargar el cambio no
    estaría. Devuelve (ok, mensaje_de_error).
    """
    if not LOG_URL:
        return False, "La Hoja no está configurada (falta LOG_URL)."
    cuerpo = dict(payload or {})
    cuerpo["action"] = accion
    try:
        import requests
        resp = requests.post(LOG_URL, json=cuerpo, timeout=30)
    except Exception:
        logging.exception("Fallo al escribir en la Hoja (acción %s)", accion)
        return False, "No se pudo contactar la Hoja de Google. Intenta de nuevo."

    try:
        r = resp.json()
    except Exception:
        # Apps Script responde HTML cuando el despliegue quedó mal publicado
        # (típico: "Quién tiene acceso" distinto de "Cualquier persona").
        logging.warning("La Hoja respondió algo que no es JSON: %.200s", resp.text)
        return False, "La Hoja respondió de forma inesperada. Revisa el despliegue del Web App."

    if isinstance(r, dict) and r.get("ok") is False:
        return False, r.get("msg") or "La Hoja rechazó el cambio."

    invalidar(*(invalida or PESTANAS))
    return True, ""
