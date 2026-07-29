#!/usr/bin/env python3
"""
Motor de Google Gemini, resistente a propósito.

Es el mismo motor que lleva tiempo funcionando en el generador de actas F08
(`Actas /_engine/generar_acta.py`): se copió tal cual —sin los prompts ni nada
del formato F08— en vez de reescribirlo, porque ya sobrevivió en producción a
que Google jubilara modelos y a que los Gemini 3 rechazaran `thinking_budget=0`.

Qué hace cuando algo sale mal:
  · Modelo retirado (404)          → salta al siguiente de MODELOS.
  · Configuración rechazada (400)  → reintenta ESE modelo sin `thinking` y lo recuerda.
  · Cuota o saturación (429/503)   → prueba otras llaves y modelos.
  · Lista completa obsoleta        → le pregunta a Google qué modelos hay.

Variable de entorno: GEMINI_API_KEY (acepta varias separadas por coma) y
GEMINI_API_KEY_2..7. Cada cuenta de Google trae su propia cuota gratis, así que
con varias llaves se multiplica la capacidad diaria.
"""
import os, json, time, re, logging
from google import genai
from google.genai import types


# Modelos a usar, en orden de preferencia. Se incluyen alias "-latest" (Google los
# mantiene apuntando al modelo vigente) y varias versiones de respaldo. Si Google
# retira uno, el código pasa AUTOMÁTICAMENTE al siguiente; y si se acaban todos,
# le pregunta a Google qué modelos hay disponibles (ver _descubrir_modelos).
MODELOS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-2.0-flash-lite",
]

# ─── "Pensamiento" del modelo (razonar antes de redactar) ───
# 0 = apagado: el modelo responde de una (lo más rápido).
# Un número (p. ej. 4096) = razona antes de redactar, pero CON TOPE, para no
# demorarse de más ni acercarse al límite de tiempo de Render.
# Se controla con la variable GEMINI_THINKING: cambiarlo NO exige tocar el código.
try:
    PENSAMIENTO = max(0, int(os.environ.get("GEMINI_THINKING", "0")))
except ValueError:
    PENSAMIENTO = 0


# ─── Medición de consumo (tokens y costo en USD) ───
PRECIOS = {
    "2.5-flash-lite": (0.10, 0.40),
    "2.0-flash-lite": (0.075, 0.30),
    "2.5-flash":      (0.15, 0.60),
    "2.0-flash":      (0.10, 0.40),
    "3.5-flash":      (1.50, 9.00),
    "3.6-flash":      (1.50, 7.50),
    "pro":            (2.00, 12.00),
}

# Precio de respaldo cuando el nombre no dice la versión (p. ej.
# "gemini-flash-latest"). Google resuelve esos alias al Flash MÁS NUEVO, que es
# el más caro. Ante la duda, el más caro: equivocarse por encima se nota y se
# corrige; por debajo pasa inadvertido.
PRECIO_DESCONOCIDO = PRECIOS["3.6-flash"]


def _precio_modelo(modelo):
    m = (modelo or "").lower()
    for clave in sorted(PRECIOS, key=len, reverse=True):
        if clave in m:
            return PRECIOS[clave]
    if "pro" in m:
        return PRECIOS["pro"]
    if "lite" in m:                      # alias de lite: el lite más caro
        return PRECIOS["2.5-flash-lite"]
    return PRECIO_DESCONOCIDO


# Acumulador por acta: se reinicia antes de generar y se lee al terminar. Suma
# TODAS las llamadas, no solo la última.
_consumo = {"entrada": 0, "salida": 0, "costo": 0.0, "modelo": "",
            "precio_in": 0.0, "precio_out": 0.0}


def reiniciar_consumo():
    _consumo.update(entrada=0, salida=0, costo=0.0, modelo="",
                    precio_in=0.0, precio_out=0.0)


def consumo_actual():
    return dict(_consumo)


def _sumar_consumo(resp, modelo):
    """Suma los tokens de una respuesta al acumulador. A prueba de fallos: si no
    viene el dato, no rompe la generación."""
    try:
        um = getattr(resp, "usage_metadata", None)
        if not um:
            return
        ent = getattr(um, "prompt_token_count", 0) or 0
        sal = getattr(um, "candidates_token_count", 0) or 0
        # El nombre PEDIDO puede ser un alias; la respuesta trae el que de verdad
        # se ejecutó. Se cobra por ese, que es lo que factura Google.
        real = getattr(resp, "model_version", None) or modelo
        p_in, p_out = _precio_modelo(real)
        _consumo["entrada"] += ent
        _consumo["salida"] += sal
        _consumo["costo"] += ent / 1_000_000 * p_in + sal / 1_000_000 * p_out
        _consumo["modelo"] = real
        _consumo["precio_in"] = p_in
        _consumo["precio_out"] = p_out
    except Exception:
        pass


def _es_temporal(e):
    """Error pasajero (saturación/cuota): conviene esperar y reintentar."""
    msg = str(e).lower()
    return any(s in msg for s in ("503", "unavailable", "429", "high demand",
                                  "overloaded", "resource_exhausted", "timeout", "quota"))


def _modelo_no_disponible(e):
    """El modelo ya no existe: hay que pasar al SIGUIENTE (no insistir con el mismo)."""
    msg = str(e).lower()
    return any(s in msg for s in ("not_found", "not found", "no longer available",
                                  "is not supported", "does not exist", "404"))


def _claves():
    """Lista de API keys. Acepta GEMINI_API_KEY con una o varias separadas por
    coma, y/o GEMINI_API_KEY_2, _3, ... (adicionales)."""
    crudas = []
    crudas += (os.environ.get("GEMINI_API_KEY", "") or "").split(",")
    for i in range(2, 8):
        crudas.append(os.environ.get(f"GEMINI_API_KEY_{i}", "") or "")
    vistas, claves = set(), []
    for k in (x.strip() for x in crudas):
        if k and k not in vistas:
            vistas.add(k); claves.append(k)
    return claves


_CLIENTES = {}


def _cliente(clave):
    if clave not in _CLIENTES:
        _CLIENTES[clave] = genai.Client(api_key=clave)
    return _CLIENTES[clave]


_MODELO_OK = None             # último modelo que funcionó (para no re-descubrir cada vez)
_MODELOS_DESCUBIERTOS = None  # caché de la lista que devolvió Google


def _descubrir_modelos(claves):
    """Último recurso: le pregunta a Google qué modelos hay para esta llave (por
    si TODA la lista MODELOS quedó obsoleta). Prioriza los 'flash' estables."""
    global _MODELOS_DESCUBIERTOS
    if _MODELOS_DESCUBIERTOS is not None:
        return _MODELOS_DESCUBIERTOS

    def malo(n):
        return any(k in n for k in ("vision", "tts", "image", "audio", "embedding", "aqa", "learnlm"))

    def pref(n):
        s = 0
        if any(k in n for k in ("preview", "exp", "thinking")): s += 5   # evitar experimentales
        if "lite" in n: s += 1
        if "latest" in n: s -= 1                                         # preferir alias estables
        return s

    for clave in claves:
        try:
            nombres = []
            for m in _cliente(clave).models.list():
                acciones = getattr(m, "supported_actions", None) or []
                if "generateContent" in acciones:
                    nombres.append(m.name.replace("models/", ""))
            flash = [n for n in nombres if "flash" in n and not malo(n)]
            otros = [n for n in nombres if not malo(n)]
            elegidos = sorted(dict.fromkeys(flash or otros), key=pref)
            _MODELOS_DESCUBIERTOS = elegidos
            return elegidos
        except Exception:
            continue
    _MODELOS_DESCUBIERTOS = []
    return []


_SIN_THINKING = set()   # modelos que NO aceptan thinking_budget=0 (p. ej. los Gemini 3)


def _config_invalida(e):
    """El modelo rechazó la configuración (típico: los Gemini 3 no aceptan
    thinking_budget=0). Hay que reintentar sin esa opción, no rendirse."""
    msg = str(e).lower()
    return "invalid_argument" in msg or "invalid argument" in msg or "400" in msg


def _fatal(e):
    """Errores que fallarán con CUALQUIER modelo y llave: no vale la pena seguir."""
    msg = str(e).lower()
    return any(s in msg for s in ("api key not valid", "api_key_invalid",
                                  "unauthenticated", "permission_denied", "403"))


def _sin_thinking(cfg):
    """Copia de la config sin thinking_config (o None si no se puede)."""
    if cfg is None or getattr(cfg, "thinking_config", None) is None:
        return None
    try:
        return cfg.model_copy(update={"thinking_config": None})
    except Exception:
        try:
            d = cfg.model_dump(exclude_none=True)
            d.pop("thinking_config", None)
            return types.GenerateContentConfig(**d)
        except Exception:
            return None


def _intentar(modelos, claves, **kwargs):
    """Prueba cada modelo con cada llave. Si un modelo rechaza la configuración,
    reintenta ESE modelo sin esa opción. Nunca aborta por culpa de un solo
    modelo: pasa al siguiente y guarda el error."""
    global _MODELO_OK
    ultimo = None
    for modelo in modelos:
        for clave in claves:
            kw = dict(kwargs)
            if modelo in _SIN_THINKING:                 # ya sabemos que no acepta thinking
                alt = _sin_thinking(kw.get("config"))
                if alt is not None:
                    kw["config"] = alt
            try:
                r = _cliente(clave).models.generate_content(model=modelo, **kw)
                _MODELO_OK = modelo        # recuerda el que sirvió para la próxima vez
                _sumar_consumo(r, modelo)
                return r, None
            except Exception as e:
                ultimo = e
                if _fatal(e):
                    raise                  # llave inválida o sin permisos: fallará con todo
                if _config_invalida(e):
                    # Se anota de UNA que este modelo no acepta la opción, aunque el
                    # reintento de abajo falle por otra causa (p. ej. saturación). Si no,
                    # se desperdiciaría una llamada rechazada en cada petición siguiente.
                    _SIN_THINKING.add(modelo)
                    alt = _sin_thinking(kw.get("config"))
                    if alt is not None:
                        try:               # reintento del MISMO modelo sin thinking
                            r = _cliente(clave).models.generate_content(
                                model=modelo, config=alt,
                                **{k: v for k, v in kw.items() if k != "config"})
                            _MODELO_OK = modelo
                            _sumar_consumo(r, modelo)
                            return r, None
                        except Exception as e2:
                            ultimo = e2
                    break                  # este modelo no sirve → siguiente modelo
                if _modelo_no_disponible(e):
                    break                  # este modelo ya no existe → siguiente modelo
                if not _es_temporal(e):
                    break                  # error raro con este modelo → siguiente modelo
                # temporal (cuota/saturación) → probar con la siguiente llave
    return None, ultimo


def _quedo_cortada(resp):
    """True si el modelo se quedó sin espacio a mitad de la respuesta."""
    try:
        fr = str(getattr(resp.candidates[0], "finish_reason", "")).upper()
        return "MAX_TOKEN" in fr or "LENGTH" in fr
    except Exception:
        return False


def _generar_con_reintentos(modelos=None, **kwargs):
    """Genera contenido de forma resistente a que Google jubile modelos:
    1) prueba la lista conocida (empezando por el último que funcionó);
    2) si toda la lista quedó obsoleta, le PREGUNTA a Google qué hay;
    3) si el fallo fue por saturación, espera un poco y reintenta una vez."""
    base = list(modelos) if modelos is not None else list(MODELOS)
    if _MODELO_OK and _MODELO_OK not in base:
        base = [_MODELO_OK] + base
    claves = _claves()
    if not claves:
        raise RuntimeError("GEMINI_API_KEY no configurada. Obtén tu key gratis en aistudio.google.com")

    r, ultimo = _intentar(base, claves, **kwargs)
    if r is not None:
        return r

    descubiertos = [m for m in _descubrir_modelos(claves) if m not in base]
    if descubiertos:
        r, ultimo = _intentar(descubiertos, claves, **kwargs)
        if r is not None:
            return r

    # Solo si fue saturación temporal: UN reintento corto. No hacemos esperas
    # largas dentro de la petición web: con 1 solo worker eso bloquea a todos y
    # puede pasarse del timeout de gunicorn (que sale como error 500).
    if ultimo is not None and _es_temporal(ultimo):
        time.sleep(8)
        r, ultimo = _intentar(base + descubiertos, claves, **kwargs)
        if r is not None:
            return r
    raise ultimo if ultimo is not None else RuntimeError("No se pudo generar con ningún modelo de Gemini.")


def json_de_ia(sistema, prompt, tokens=32768, temperatura=0.2):
    """Pide un JSON a la IA y lo interpreta. Si la respuesta viene CORTADA o el
    JSON queda incompleto (típico en reuniones largas), reintenta con más espacio
    antes de rendirse: así el usuario no ve el error 'no devolvió JSON válido'."""
    intentos = [tokens, min(tokens * 2, 65536)]
    ultimo = None
    for i, tk in enumerate(intentos):
        cfg_kw = dict(system_instruction=sistema, temperature=temperatura, max_output_tokens=tk)
        if PENSAMIENTO > 0:
            cfg_kw["thinking_config"] = types.ThinkingConfig(thinking_budget=PENSAMIENTO)
        cfg = types.GenerateContentConfig(**cfg_kw)
        resp = _generar_con_reintentos(config=cfg, contents=prompt)
        raw = (resp.text or "").strip()
        raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE).strip()
        raw = re.sub(r'```\s*$', '', raw, flags=re.MULTILINE).strip()
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            raw = m.group()
        try:
            if raw and not _quedo_cortada(resp):
                return json.loads(raw, strict=False)
            ultimo = json.JSONDecodeError("respuesta cortada por límite de longitud", raw or "", 0)
        except json.JSONDecodeError as e:
            ultimo = e
        if i == 0:
            logging.warning("La IA devolvió un JSON incompleto; reintentando con más espacio…")
    raise ultimo or json.JSONDecodeError("sin respuesta utilizable de la IA", "", 0)


def mensaje_amable(e):
    """Traduce el error técnico a algo que el gerente pueda entender y accionar."""
    msg = str(e).lower()
    if _fatal(e):
        return "La llave de Gemini no es válida o no tiene permisos. Avísale a Santiago."
    if _es_temporal(e):
        return "Gemini está saturado o se agotó la cuota del día. Espera 1-2 minutos y vuelve a intentar."
    if isinstance(e, json.JSONDecodeError) or "json" in msg:
        return ("La IA no devolvió un acta utilizable, normalmente porque la transcripción "
                "es muy larga o llegó incompleta. Intenta de nuevo o divide la reunión.")
    return "No se pudo generar el acta. Intenta de nuevo en un momento."
