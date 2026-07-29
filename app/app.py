#!/usr/bin/env python3
"""
Actas de Proveedores — Abelardo Yepes S.A.S.

App independiente para la Gerencia de Proveedores: convierte la transcripción de
una reunión con un proveedor en un acta ejecutiva (temas, conclusiones y tareas),
la guarda, y desde ahí arma el tablero de seguimiento y la línea de tiempo de
cada proveedor.

No comparte NADA en ejecución con el generador de actas F08: otro repo, otro
servicio y otra Hoja. Solo se copiaron patrones de código ya probados.

Variables de entorno: ver CLAUDE.md.
"""
import os, sys, io, json, tempfile, logging, secrets, threading

from flask import (Flask, request, session, jsonify, redirect, url_for,
                   render_template, send_file)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import hoja
import motor_ia
import prompts
from build_acta import build as build_docx

logging.basicConfig(level=logging.INFO)


# ─────────────────────────── Entorno ───────────────────────────
# En Vercel la app corre como función sin servidor: no hay un proceso único ni
# disco compartido entre peticiones, y eso cambia tres cosas (clave de sesión,
# tamaño máximo de subida y utilidad del caché).
EN_VERCEL = bool(os.environ.get("VERCEL"))
DEV_LOCAL = os.environ.get("DEV_LOCAL", "").strip() == "1"

# Tope de subida. En Vercel lo impone la plataforma (4,5 MB por petición) y no se
# puede subir; aceptar más aquí solo produciría un error crudo de la plataforma
# en vez de un mensaje entendible.
TOPE_SUBIDA = (4 * 1024 * 1024 + 512 * 1024) if EN_VERCEL else 40 * 1024 * 1024


# ─────────────────────────── App ───────────────────────────
# Se marca cuando la clave de sesión no es estable, para poder avisarlo en
# pantalla en vez de dejar que la gente se desloguee sola sin explicación.
CLAVE_INESTABLE = False


def _clave_estable():
    """SECRET_KEY estable para firmar las sesiones.

    Sin una clave fija, cada instancia firma con una distinta y las sesiones se
    invalidan al azar: el usuario aparece deslogueado a mitad de trabajo. En un
    servidor normal basta con guardarla en disco, pero en Vercel cada petición
    puede caer en una instancia nueva con su propio disco temporal, así que ahí
    la variable de entorno es obligatoria."""
    global CLAVE_INESTABLE
    k = os.environ.get("SECRET_KEY")
    if k:
        return k

    if EN_VERCEL:
        CLAVE_INESTABLE = True
        logging.critical(
            "Falta SECRET_KEY. En Vercel es obligatoria: sin ella las sesiones "
            "se cierran solas de forma aleatoria. Configúrala en las variables "
            "de entorno del proyecto.")
        return secrets.token_hex(32)

    ruta = os.path.join(tempfile.gettempdir(), "actas_proveedores_secret.key")
    try:
        if os.path.exists(ruta):
            guardada = open(ruta).read().strip()
            if guardada:
                return guardada
        nueva = secrets.token_hex(32)
        with open(ruta, "w") as f:
            f.write(nueva)
        return nueva
    except Exception:
        return secrets.token_hex(32)


app = Flask(__name__, template_folder=os.path.join(HERE, "templates"),
            static_folder=os.path.join(HERE, "static"))
app.secret_key = _clave_estable()
app.config["MAX_CONTENT_LENGTH"] = TOPE_SUBIDA
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 7  # sesión de 7 días

# En local, releer las plantillas en cada petición: sin esto hay que reiniciar el
# servidor para ver cualquier cambio de HTML. En producción no aplica (cuesta E/S).
if DEV_LOCAL:
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.jinja_env.auto_reload = True

# Detrás del proxy de Vercel: respeta https para armar bien las URLs de OAuth.
# Sin esto, la URL de retorno de Google saldría en http y el login fallaría.
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
except Exception:
    pass


@app.errorhandler(413)
def _archivo_muy_grande(_e):
    """Sin este manejador, pasarse del tope devuelve una página de error cruda."""
    mb = TOPE_SUBIDA / 1024 / 1024
    msg = (f"El archivo pasa de {mb:.1f} MB, que es el máximo que acepta el servidor. "
           "Si es un PDF escaneado, pega el texto en el cuadro de abajo o súbelo "
           "como .docx o .txt, que pesan mucho menos.")
    if request.path.startswith("/api/"):
        return jsonify({"error": msg}), 413
    return msg, 413


# ─────────────────────────── Acceso y roles ───────────────────────────
GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
OAUTH_ACTIVO = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)

# DEV_LOCAL (definida arriba) entra como gerente sin login. Solo la pone el
# arranque local: en producción NO existe. A diferencia del generador F08 —donde
# sin OAuth todos quedaban como gerencia—, aquí si no hay Google y no hay
# DEV_LOCAL, no entra nadie.


def _lista(nombre):
    return {e.strip().lower() for e in os.environ.get(nombre, "").split(",") if e.strip()}


SUPERADMIN        = os.environ.get("SUPERADMIN", "santirin33@gmail.com").strip().lower()
GERENTES          = _lista("GERENTE")            # escriben: generan actas y mueven tareas
LECTORES          = _lista("LECTORES")           # solo consultan el tablero
DOMINIO_PERMITIDO = os.environ.get("DOMINIO_PERMITIDO", "").strip().lower().lstrip("@")

USUARIO_LOCAL = "local@abelardoyepes.com"


def usuario_actual():
    if DEV_LOCAL and not OAUTH_ACTIVO:
        return USUARIO_LOCAL
    return (session.get("usuario") or "").strip().lower()


def puede_leer(email=None):
    email = (email if email is not None else usuario_actual()).strip().lower()
    if DEV_LOCAL and not OAUTH_ACTIVO:
        return True
    if not email:
        return False
    if email == SUPERADMIN or email in GERENTES or email in LECTORES:
        return True
    # El dominio de la empresa da acceso de lectura: el tablero es información
    # de gestión interna, no confidencial.
    return bool(DOMINIO_PERMITIDO and email.endswith("@" + DOMINIO_PERMITIDO))


def puede_escribir(email=None):
    """Generar actas, crear proveedores y mover tareas. Un LECTOR nunca escribe."""
    email = (email if email is not None else usuario_actual()).strip().lower()
    if DEV_LOCAL and not OAUTH_ACTIVO:
        return True
    if not email:
        return False
    if email in LECTORES and email not in GERENTES and email != SUPERADMIN:
        return False
    if email == SUPERADMIN or email in GERENTES:
        return True
    return bool(DOMINIO_PERMITIDO and email.endswith("@" + DOMINIO_PERMITIDO))


oauth = None
if OAUTH_ACTIVO:
    from authlib.integrations.flask_client import OAuth
    oauth = OAuth(app)
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


RUTAS_LIBRES = {"login", "auth_google", "auth_callback", "sin_acceso", "logout",
                "health", "static"}


@app.before_request
def _control_acceso():
    if request.endpoint in RUTAS_LIBRES:
        return
    if puede_leer():
        return
    if usuario_actual():
        return redirect(url_for("sin_acceso"))
    # Las llamadas de la interfaz reciben 401 en JSON; los enlaces, el login.
    if request.path.startswith("/api/"):
        return jsonify({"error": "No autorizado"}), 401
    return redirect(url_for("login"))


def _exige_escritura():
    """Devuelve una respuesta de error si el usuario no puede escribir, o None.

    Se comprueba en el servidor y no solo escondiendo botones: un lector podría
    llamar la API directamente."""
    if puede_escribir():
        return None
    return jsonify({"error": "Tu cuenta es de solo consulta. No puedes hacer cambios."}), 403


@app.route("/login")
def login():
    if puede_leer():
        return redirect(url_for("index"))
    return render_template("login.html", oauth_activo=OAUTH_ACTIVO)


@app.route("/auth/google")
def auth_google():
    if not OAUTH_ACTIVO:
        return redirect(url_for("login"))
    redirect_uri = url_for("auth_callback", _external=True, _scheme="https")
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/auth/callback")
def auth_callback():
    if not OAUTH_ACTIVO:
        return redirect(url_for("login"))
    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo") or {}
    except Exception:
        logging.exception("Error en el callback de Google")
        return redirect(url_for("login"))
    email = (userinfo.get("email") or "").strip().lower()
    if not email or not userinfo.get("email_verified", False):
        return redirect(url_for("login"))
    session.permanent = True
    session["usuario"] = email
    session["nombre"] = userinfo.get("name") or email.split("@")[0]
    return redirect(url_for("index") if puede_leer(email) else url_for("sin_acceso"))


@app.route("/sin-acceso")
def sin_acceso():
    return render_template("sin_acceso.html", usuario=session.get("usuario", ""),
                           superadmin=SUPERADMIN)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/health")
def health():
    return jsonify({"status": "ok", "hoja": hoja.configurada()})


# ─────────────────────────── Lectura de archivos ───────────────────────────
def leer_texto(file_bytes, filename):
    """Extrae el texto de un .docx, .pdf o .txt."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "docx":
        from docx import Document as DocxReader
        doc = DocxReader(io.BytesIO(file_bytes))
        partes = [p.text for p in doc.paragraphs if p.text.strip()]
        for t in doc.tables:
            for row in t.rows:
                celdas = [c.text.strip() for c in row.cells if c.text.strip()]
                if celdas:
                    partes.append(" | ".join(celdas))
        return "\n".join(partes)
    if ext == "pdf":
        import fitz
        pdf = fitz.open(stream=file_bytes, filetype="pdf")
        texto = "\n".join(page.get_text() for page in pdf)
        pdf.close()
        return texto
    return file_bytes.decode("utf-8", errors="ignore")


# ─────────────────────────── Contexto común ───────────────────────────
def _contexto():
    return {
        "usuario": usuario_actual(),
        "nombre": session.get("nombre") or usuario_actual().split("@")[0],
        "puede_escribir": puede_escribir(),
        "hoja_ok": hoja.configurada(),
        "clave_inestable": CLAVE_INESTABLE,
    }


# La entrada es el tablero, no el generador: lo primero que el gerente necesita
# saber al abrir es qué se está incumpliendo. Generar el acta es una tarea que
# él viene a hacer sabiendo que la va a hacer; los vencidos hay que recordárselos.
@app.route("/")
def index():
    return render_template("dashboard.html", **_contexto())


@app.route("/generar")
def generador():
    return render_template("generador.html", **_contexto())


# /dashboard siguió siendo la dirección del tablero durante el desarrollo; se
# mantiene como redirección para que ningún enlace guardado quede roto.
@app.route("/dashboard")
def dashboard():
    return redirect(url_for("index"))


@app.route("/tareas")
def tareas():
    return render_template("tareas.html", **_contexto())


@app.route("/proveedores")
def proveedores():
    return render_template("proveedores.html", **_contexto())


@app.route("/proveedor/<pid>")
def proveedor(pid):
    prov = next((p for p in hoja.leer("Proveedores") if p["id"] == pid), None)
    if not prov:
        return render_template("no_encontrado.html", que="proveedor", **_contexto()), 404
    return render_template("timeline.html", proveedor=prov, **_contexto())


# ─────────────────────────── API de datos ───────────────────────────
@app.route("/api/datos")
def api_datos():
    """Todo lo que necesitan el tablero, la línea de tiempo y la bandeja de
    tareas, en una sola llamada. El filtrado se hace en el navegador: son
    volúmenes pequeños y así los filtros responden al instante."""
    datos = hoja.leer_todo(forzar=request.args.get("forzar") == "1")
    datos["hoy"] = hoja.hoy()
    datos["puede_escribir"] = puede_escribir()
    return jsonify(datos)


@app.route("/api/proveedores", methods=["POST"])
def api_crear_proveedor():
    if (err := _exige_escritura()):
        return err
    body = request.get_json(silent=True) or {}
    nombre = (body.get("nombre") or "").strip()
    tipo = (body.get("tipo_servicio") or "").strip()
    if not nombre or not tipo:
        return jsonify({"error": "El nombre y el tipo de servicio son obligatorios."}), 400

    existentes = hoja.leer("Proveedores")
    if any(p["nombre"].strip().lower() == nombre.lower() for p in existentes):
        return jsonify({"error": f"Ya existe un proveedor llamado «{nombre}»."}), 409

    registro = {
        "id": hoja.nuevo_id("PRV"),
        "nombre": nombre,
        "tipo_servicio": tipo,
        "contacto": (body.get("contacto") or "").strip(),
        "email": (body.get("email") or "").strip(),
        "telefono": (body.get("telefono") or "").strip(),
        "estado": "activo",
        "creado_por": usuario_actual(),
        "fecha_creacion": hoja.hoy(),
    }
    ok, msg = hoja.escribir("add_proveedor", {"proveedor": registro}, invalida=("Proveedores",))
    if not ok:
        return jsonify({"error": msg}), 502
    return jsonify({"ok": True, "proveedor": registro})


@app.route("/api/proveedores/<pid>", methods=["POST"])
def api_actualizar_proveedor(pid):
    if (err := _exige_escritura()):
        return err
    body = request.get_json(silent=True) or {}
    permitidos = {"nombre", "tipo_servicio", "contacto", "email", "telefono", "estado"}
    cambios = {k: str(v).strip() for k, v in body.items() if k in permitidos}
    if not cambios:
        return jsonify({"error": "No hay nada que cambiar."}), 400
    ok, msg = hoja.escribir("update_proveedor", {"id": pid, "cambios": cambios},
                            invalida=("Proveedores",))
    if not ok:
        return jsonify({"error": msg}), 502
    return jsonify({"ok": True})


# ─────────────────────────── Generación del acta ───────────────────────────
def _pendientes_de(proveedor_id):
    """Tareas abiertas de reuniones anteriores con este proveedor.

    Son las que se le inyectan al prompt para que la IA reporte qué avance hubo.
    Es lo que convierte reuniones sueltas en una línea de tiempo."""
    abiertas = [t for t in hoja.leer("Tareas")
                if t.get("proveedor_id") == proveedor_id
                and t.get("estado") in ("pendiente", "en_proceso")]
    abiertas.sort(key=lambda t: t.get("fecha", ""))
    return abiertas


@app.route("/api/generar", methods=["POST"])
def api_generar():
    """Genera el borrador del acta. NO guarda nada: el gerente lo revisa primero."""
    if (err := _exige_escritura()):
        return err

    proveedor_id = (request.form.get("proveedor_id") or "").strip()
    fecha = hoja.fecha_iso(request.form.get("fecha") or "", hoja.hoy())

    prov = next((p for p in hoja.leer("Proveedores") if p["id"] == proveedor_id), None)
    if not prov:
        return jsonify({"error": "Selecciona un proveedor de la lista."}), 400

    # La transcripción puede llegar como archivo o pegada en el cuadro de texto.
    transcripcion = (request.form.get("transcripcion") or "").strip()
    archivo = request.files.get("archivo")
    if archivo and archivo.filename:
        try:
            transcripcion = leer_texto(archivo.read(), archivo.filename).strip()
        except Exception:
            logging.exception("No se pudo leer el archivo de transcripción")
            return jsonify({"error": "No se pudo leer el archivo. Súbelo en .docx, .pdf o .txt."}), 400

    if len(transcripcion) < 200:
        return jsonify({"error": "La transcripción está vacía o es demasiado corta "
                                 "para generar un acta."}), 400

    pendientes = _pendientes_de(proveedor_id)
    mensaje = prompts.construir_mensaje(
        transcripcion, prov["nombre"], prov["tipo_servicio"], fecha, pendientes)
    logging.info("Generando acta de %s con %d pendientes previos inyectados",
                 prov["nombre"], len(pendientes))

    motor_ia.reiniciar_consumo()
    try:
        acta = motor_ia.json_de_ia(prompts.PROMPT_ACTA_PROVEEDOR, mensaje)
    except Exception as e:
        logging.exception("Fallo al generar el acta")
        return jsonify({"error": motor_ia.mensaje_amable(e)}), 502

    acta["fecha"] = hoja.fecha_iso(acta.get("fecha"), fecha)
    acta.setdefault("titulo", f"Reunión con {prov['nombre']}")
    for lista in ("participantes", "temas", "compromisos", "seguimiento"):
        if not isinstance(acta.get(lista), list):
            acta[lista] = []

    # La IA solo puede reportar avance de pendientes que existen de verdad: si
    # devuelve un id inventado o de otro proveedor, se descarta aquí.
    validos = {p["id"]: p for p in pendientes}
    seguimiento = []
    for s in acta["seguimiento"]:
        origen = validos.get(str(s.get("id", "")).strip())
        if not origen:
            continue
        seguimiento.append({
            "id": origen["id"],
            "tarea": origen.get("tarea", ""),
            "tema": origen.get("tema", ""),
            "fecha_origen": origen.get("fecha", ""),
            "estado_anterior": origen.get("estado", "pendiente"),
            "avance": str(s.get("avance", "")).strip(),
            "estado_sugerido": s.get("estado_sugerido")
                if s.get("estado_sugerido") in ("pendiente", "en_proceso", "completada")
                else "en_proceso",
        })
    acta["seguimiento"] = seguimiento

    for c in acta["compromisos"]:
        c["fecha_limite"] = hoja.fecha_iso(c.get("fecha_limite"), "")
        if c.get("prioridad") not in ("alta", "media", "baja"):
            c["prioridad"] = "media"
    acta["proxima_reunion"] = hoja.fecha_iso(acta.get("proxima_reunion"), "")

    return jsonify({
        "ok": True,
        "acta": acta,
        "proveedor": prov,
        "pendientes_previos": len(pendientes),
        "consumo": motor_ia.consumo_actual(),
    })


@app.route("/api/reuniones", methods=["POST"])
def api_guardar_reunion():
    """Guarda la reunión ya revisada, sus compromisos y los avances reportados."""
    if (err := _exige_escritura()):
        return err
    body = request.get_json(silent=True) or {}
    acta = body.get("acta") or {}
    proveedor_id = (body.get("proveedor_id") or "").strip()

    prov = next((p for p in hoja.leer("Proveedores") if p["id"] == proveedor_id), None)
    if not prov:
        return jsonify({"error": "Proveedor no encontrado."}), 400

    fecha = hoja.fecha_iso(acta.get("fecha"), hoja.hoy())
    usuario = usuario_actual()
    reunion_id = hoja.nuevo_id("REU")

    reunion = {
        "id": reunion_id,
        "fecha": fecha,
        "proveedor_id": prov["id"],
        "proveedor": prov["nombre"],
        "tipo_servicio": prov["tipo_servicio"],
        "titulo": (acta.get("titulo") or "").strip(),
        "participantes": "; ".join(acta.get("participantes") or []),
        "resumen": (acta.get("resumen") or "").strip(),
        # El acta completa se guarda serializada para poder volver a mostrarla y
        # descargarla sin gastar otra llamada a Gemini.
        "temas_json": json.dumps({"temas": acta.get("temas") or [],
                                  "proxima_reunion": acta.get("proxima_reunion", "")},
                                 ensure_ascii=False),
        "generado_por": usuario,
        "fecha_registro": hoja.ahora(),
        # Lo rellena el Web App con el enlace del archivo que deja en Drive.
        "enlace_docx": "",
    }

    tareas_nuevas = []
    for c in (acta.get("compromisos") or []):
        texto = (c.get("tarea") or "").strip()
        if not texto:
            continue
        tareas_nuevas.append({
            "id": hoja.nuevo_id("TAR"),
            "reunion_id": reunion_id,
            "fecha": fecha,
            "proveedor_id": prov["id"],
            "proveedor": prov["nombre"],
            "tipo_servicio": prov["tipo_servicio"],
            "tema": (c.get("tema") or "").strip(),
            "tarea": texto,
            "responsable": (c.get("responsable") or "").strip(),
            "estado": "pendiente",
            "prioridad": c.get("prioridad") if c.get("prioridad") in ("alta", "media", "baja") else "media",
            "fecha_limite": hoja.fecha_iso(c.get("fecha_limite"), ""),
            "fecha_completada": "",
            # Si el compromiso viene de retomar un pendiente anterior, queda encadenado.
            "tarea_origen_id": (c.get("tarea_origen_id") or "").strip(),
            "actualizado_por": usuario,
        })

    # Los avances reportados sobre pendientes anteriores: una fila de bitácora y,
    # si cambió el estado, la actualización de la tarea original.
    seguimiento, cambios = [], []
    abiertas = {t["id"]: t for t in _pendientes_de(prov["id"])}
    for s in (acta.get("seguimiento") or []):
        origen = abiertas.get(str(s.get("id", "")).strip())
        if not origen:
            continue
        nuevo = s.get("estado_sugerido")
        if nuevo not in ("pendiente", "en_proceso", "completada"):
            nuevo = "en_proceso"
        anterior = origen.get("estado", "pendiente")
        seguimiento.append({
            "id": hoja.nuevo_id("SEG"),
            "tarea_id": origen["id"],
            "fecha": fecha,
            "reunion_id": reunion_id,
            "avance": (s.get("avance") or "").strip(),
            "estado_anterior": anterior,
            "estado_nuevo": nuevo,
            "autor": usuario,
        })
        if nuevo != anterior:
            cambios.append({"id": origen["id"], "cambios": {
                "estado": nuevo,
                "fecha_completada": fecha if nuevo == "completada" else "",
                "actualizado_por": usuario,
            }})

    # El .docx viaja junto con la fila para que el Web App lo archive en Drive.
    # Si Drive falla, la reunión se guarda igual y el enlace queda vacío: perder
    # el archivo es molesto, perder el registro sería grave.
    acta_docx = dict(acta)
    acta_docx["compromisos"] = [{
        "tarea": t["tarea"], "responsable": t["responsable"],
        "fecha_limite": t["fecha_limite"], "prioridad": t["prioridad"],
    } for t in tareas_nuevas]

    archivo = None
    try:
        import base64
        archivo = {
            "nombre": _nombre_archivo(prov["nombre"], fecha),
            "carpeta": prov["nombre"],
            "contenido_b64": base64.b64encode(
                _docx_bytes(acta_docx, prov["nombre"], prov["tipo_servicio"])).decode(),
        }
    except Exception:
        logging.exception("No se pudo construir el .docx para archivar en Drive")

    ok, msg = hoja.escribir("add_reunion", {
        "reunion": reunion,
        "tareas": tareas_nuevas,
        "seguimiento": seguimiento,
        "cambios_tareas": cambios,
        "archivo": archivo,
    })
    if not ok:
        return jsonify({"error": msg}), 502

    # El enlace lo asigna el Web App al crear el archivo; se relee para
    # devolvérselo a la pantalla de "reunión guardada".
    enlace = ""
    try:
        fila = next((r for r in hoja.leer("Reuniones", forzar=True) if r["id"] == reunion_id), None)
        enlace = (fila or {}).get("enlace_docx", "")
    except Exception:
        pass

    return jsonify({"ok": True, "reunion_id": reunion_id, "enlace_docx": enlace,
                    "tareas": len(tareas_nuevas), "seguimiento": len(seguimiento)})


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _docx_bytes(acta, proveedor, tipo_servicio):
    """El .docx en memoria.

    Se trabaja con bytes y no con un archivo temporal a propósito: la versión
    anterior escribía en disco con delete=False y nadie borraba nada, así que
    cada descarga dejaba un .docx abandonado en el servidor."""
    buf = io.BytesIO()
    build_docx(acta, proveedor, tipo_servicio, buf)
    return buf.getvalue()


def _nombre_archivo(proveedor, fecha):
    limpio = "".join(ch if ch.isalnum() or ch in " ._-" else "" for ch in proveedor).strip()
    return f"Acta {limpio} {fecha}.docx"


def _acta_de_reunion(reunion):
    """Rearma el acta desde lo guardado en la Hoja, sin volver a llamar a la IA."""
    try:
        extra = json.loads(reunion.get("temas_json") or "{}")
    except Exception:
        extra = {}
    return {
        "titulo": reunion.get("titulo", ""),
        "fecha": reunion.get("fecha", ""),
        "participantes": [p.strip() for p in (reunion.get("participantes") or "").split(";") if p.strip()],
        "resumen": reunion.get("resumen", ""),
        "temas": extra.get("temas", []),
        "compromisos": [{
            "tarea": t.get("tarea", ""), "responsable": t.get("responsable", ""),
            "fecha_limite": t.get("fecha_limite", ""), "prioridad": t.get("prioridad", "media"),
        } for t in hoja.leer("Tareas") if t.get("reunion_id") == reunion["id"]],
        "proxima_reunion": extra.get("proxima_reunion", ""),
    }


@app.route("/reunion/<rid>/docx")
def descargar_docx(rid):
    """Descarga el acta. El archivo de Drive es la copia archivada; esta ruta
    la reconstruye desde los datos, así que sirve también para las reuniones
    guardadas antes de que existiera la carpeta de Drive."""
    reunion = next((r for r in hoja.leer("Reuniones") if r["id"] == rid), None)
    if not reunion:
        return render_template("no_encontrado.html", que="reunión", **_contexto()), 404

    datos = _docx_bytes(_acta_de_reunion(reunion),
                        reunion.get("proveedor", ""), reunion.get("tipo_servicio", ""))
    return send_file(io.BytesIO(datos), as_attachment=True, mimetype=DOCX_MIME,
                     download_name=_nombre_archivo(reunion.get("proveedor", "proveedor"),
                                                   reunion.get("fecha", "")))


# ─────────────────────────── Seguimiento de tareas ───────────────────────────
@app.route("/api/tareas/actualizar", methods=["POST"])
def api_actualizar_tarea():
    """Cambia el estado, el plazo o la prioridad de una tarea, y registra el avance."""
    if (err := _exige_escritura()):
        return err
    body = request.get_json(silent=True) or {}
    tarea_id = str(body.get("id", "")).strip()
    if not tarea_id:
        return jsonify({"error": "Falta el identificador de la tarea."}), 400

    tarea = next((t for t in hoja.leer("Tareas") if t["id"] == tarea_id), None)
    if not tarea:
        return jsonify({"error": "Tarea no encontrada."}), 404

    usuario = usuario_actual()
    cambios = {"actualizado_por": usuario}
    nota = (body.get("avance") or "").strip()
    anterior = tarea.get("estado", "pendiente")
    nuevo = anterior

    if "estado" in body:
        nuevo = str(body["estado"]).strip()
        if nuevo not in ("pendiente", "en_proceso", "completada", "cancelada"):
            return jsonify({"error": "Estado inválido."}), 400
        cambios["estado"] = nuevo
        cambios["fecha_completada"] = hoja.hoy() if nuevo == "completada" else ""

    if "fecha_limite" in body:
        plazo = hoja.fecha_iso(body["fecha_limite"], "")
        if body["fecha_limite"] and not plazo:
            return jsonify({"error": "La fecha debe tener el formato AAAA-MM-DD."}), 400
        cambios["fecha_limite"] = plazo

    if "prioridad" in body:
        if body["prioridad"] not in ("alta", "media", "baja"):
            return jsonify({"error": "Prioridad inválida."}), 400
        cambios["prioridad"] = body["prioridad"]

    payload = {"id": tarea_id, "cambios": cambios}
    # Toda nota o cambio de estado deja rastro en la bitácora: es lo que después
    # se ve como historial en la línea de tiempo.
    if nota or nuevo != anterior:
        payload["seguimiento"] = {
            "id": hoja.nuevo_id("SEG"),
            "tarea_id": tarea_id,
            "fecha": hoja.hoy(),
            "reunion_id": "",                 # cambio hecho a mano, no en una reunión
            "avance": nota,
            "estado_anterior": anterior,
            "estado_nuevo": nuevo,
            "autor": usuario,
        }

    ok, msg = hoja.escribir("update_tarea", payload, invalida=("Tareas", "Seguimiento"))
    if not ok:
        return jsonify({"error": msg}), 502
    return jsonify({"ok": True})


@app.route("/api/tareas", methods=["POST"])
def api_crear_tarea():
    """Tarea suelta, creada a mano fuera de una reunión."""
    if (err := _exige_escritura()):
        return err
    body = request.get_json(silent=True) or {}
    texto = (body.get("tarea") or "").strip()
    proveedor_id = (body.get("proveedor_id") or "").strip()
    prov = next((p for p in hoja.leer("Proveedores") if p["id"] == proveedor_id), None)
    if not texto or not prov:
        return jsonify({"error": "Faltan el proveedor o la descripción de la tarea."}), 400

    registro = {
        "id": hoja.nuevo_id("TAR"),
        "reunion_id": "",
        "fecha": hoja.hoy(),
        "proveedor_id": prov["id"],
        "proveedor": prov["nombre"],
        "tipo_servicio": prov["tipo_servicio"],
        "tema": (body.get("tema") or "").strip(),
        "tarea": texto,
        "responsable": (body.get("responsable") or "").strip(),
        "estado": "pendiente",
        "prioridad": body.get("prioridad") if body.get("prioridad") in ("alta", "media", "baja") else "media",
        "fecha_limite": hoja.fecha_iso(body.get("fecha_limite"), ""),
        "fecha_completada": "",
        "tarea_origen_id": (body.get("tarea_origen_id") or "").strip(),
        "actualizado_por": usuario_actual(),
    }
    ok, msg = hoja.escribir("add_tareas", {"tareas": [registro]}, invalida=("Tareas",))
    if not ok:
        return jsonify({"error": msg}), 502
    return jsonify({"ok": True, "tarea": registro})


@app.route("/api/tipos-servicio")
def api_tipos_servicio():
    """Los tipos sugeridos más los que ya se hayan usado (el gerente puede crear
    los suyos y quedan disponibles para el siguiente proveedor)."""
    usados = {p["tipo_servicio"].strip() for p in hoja.leer("Proveedores") if p.get("tipo_servicio")}
    return jsonify(sorted(usados | set(prompts.TIPOS_SERVICIO)))


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5052))
    app.run(host="0.0.0.0", port=puerto, debug=DEV_LOCAL)
