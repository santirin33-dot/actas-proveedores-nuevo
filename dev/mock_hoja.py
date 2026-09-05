#!/usr/bin/env python3
"""
Simulador de la Hoja de Google para pruebas locales.

Imita el Web App de Apps Script (mismo doGet/doPost, mismas acciones) pero
guardando en un JSON en disco. Sirve para probar la app completa sin tocar la
Hoja de verdad ni gastar cuota, y para reproducir un problema con datos falsos.

    python3 dev/mock_hoja.py                 # queda escuchando en :5099
    LOG_URL=http://localhost:5099 bash iniciar.sh

Los datos quedan en dev/datos_prueba.json. Bórralo para empezar de cero.
"""
import os, json
from flask import Flask, request, jsonify

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(HERE, "datos_prueba.json")

PESTANAS = ("Proveedores", "Reuniones", "Tareas", "Seguimiento", "ANS")

app = Flask(__name__)


def cargar():
    if os.path.exists(ARCHIVO):
        with open(ARCHIVO, encoding="utf-8") as f:
            d = json.load(f)
        # Un archivo de pruebas anterior no tiene las pestañas nuevas.
        for p in PESTANAS:
            d.setdefault(p, [])
        return d
    return {p: [] for p in PESTANAS}


def guardar(datos):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


@app.route("/", methods=["GET"])
def do_get():
    datos = cargar()
    pestana = request.args.get("sheet", "")
    if pestana == "todo":
        return jsonify({
            "proveedores": datos["Proveedores"], "reuniones": datos["Reuniones"],
            "tareas": datos["Tareas"], "seguimiento": datos["Seguimiento"],
            "ans": datos["ANS"],
        })
    if pestana not in PESTANAS:
        return jsonify({"error": "Pestaña no válida"})
    return jsonify(datos[pestana])


def _archivar(archivo):
    """Equivalente local de la carpeta de Drive. Devuelve "" si falla, igual que
    el Web App: un problema al archivar nunca puede tumbar el guardado."""
    if not archivo or not archivo.get("contenido_b64"):
        return ""
    try:
        import base64
        carpeta = os.path.join(HERE, "actas", archivo.get("carpeta") or "Sin proveedor")
        os.makedirs(carpeta, exist_ok=True)
        ruta = os.path.join(carpeta, archivo.get("nombre") or "Acta.docx")
        n = 2
        while os.path.exists(ruta):
            base, ext = os.path.splitext(archivo.get("nombre") or "Acta.docx")
            ruta = os.path.join(carpeta, f"{base} ({n}){ext}")
            n += 1
        with open(ruta, "wb") as f:
            f.write(base64.b64decode(archivo["contenido_b64"]))
        return "file://" + ruta
    except Exception as e:
        print("No se pudo archivar el acta:", e)
        return ""


def _actualizar(filas, id_, cambios):
    for f in filas:
        if str(f.get("id")) == str(id_):
            f.update({k: str(v) for k, v in (cambios or {}).items()})
            return True
    return False


@app.route("/", methods=["POST"])
def do_post():
    datos = cargar()
    body = request.get_json(silent=True) or {}
    accion = body.get("action", "")

    if accion == "add_proveedor":
        datos["Proveedores"].append(body["proveedor"])

    elif accion == "update_proveedor":
        if not _actualizar(datos["Proveedores"], body.get("id"), body.get("cambios")):
            return jsonify({"ok": False, "msg": "Proveedor no encontrado"})

    elif accion == "add_reunion":
        reunion = body["reunion"]
        # Imita lo que hace Apps Script con Drive: guarda el .docx en
        # dev/actas/<Proveedor>/ y deja la ruta como "enlace".
        reunion["enlace_docx"] = _archivar(body.get("archivo"))
        datos["Reuniones"].append(reunion)
        datos["Tareas"].extend(body.get("tareas") or [])
        datos["Seguimiento"].extend(body.get("seguimiento") or [])
        for c in (body.get("cambios_tareas") or []):
            _actualizar(datos["Tareas"], c["id"], c.get("cambios"))

    elif accion == "add_tareas":
        datos["Tareas"].extend(body.get("tareas") or [])

    elif accion == "update_tarea":
        if not _actualizar(datos["Tareas"], body.get("id"), body.get("cambios")):
            return jsonify({"ok": False, "msg": "Tarea no encontrada"})
        if body.get("seguimiento"):
            datos["Seguimiento"].append(body["seguimiento"])

    elif accion == "add_seguimiento":
        datos["Seguimiento"].append(body["seguimiento"])

    elif accion == "add_ans":
        datos["ANS"].append(body["ans"])

    elif accion == "update_ans":
        if not _actualizar(datos["ANS"], body.get("id"), body.get("cambios")):
            return jsonify({"ok": False, "msg": "ANS no encontrado"})

    elif accion == "update_reunion":
        cambios_r = dict(body.get("cambios") or {})
        enlace = _archivar(body.get("archivo"))
        if enlace:
            cambios_r["enlace_docx"] = enlace
        if not _actualizar(datos["Reuniones"], body.get("id"), cambios_r):
            return jsonify({"ok": False, "msg": "Reunión no encontrada"})
        for c in body.get("actualizar_tareas") or []:
            _actualizar(datos["Tareas"], c.get("id"), c.get("cambios"))
        datos["Tareas"].extend(body.get("tareas_nuevas") or [])
        fuera = {str(x) for x in (body.get("tareas_fuera") or [])}
        if fuera:
            datos["Seguimiento"] = [g for g in datos["Seguimiento"]
                                    if str(g.get("tarea_id")) not in fuera]
            datos["Tareas"] = [t for t in datos["Tareas"] if str(t.get("id")) not in fuera]

    elif accion == "update_fila":
        hoja = body.get("sheet")
        if hoja not in PESTANAS:
            return jsonify({"ok": False, "msg": f"Pestaña desconocida: {hoja}"})
        if not _actualizar(datos[hoja], body.get("id"), body.get("cambios")):
            return jsonify({"ok": False, "msg": "No se encontró la fila"})

    elif accion == "delete_filas":
        hoja = body.get("sheet")
        if hoja not in PESTANAS:
            return jsonify({"ok": False, "msg": f"Pestaña desconocida: {hoja}"})
        fuera = {str(x) for x in (body.get("ids") or [])}
        datos[hoja] = [f for f in datos[hoja] if str(f.get("id")) not in fuera]

    elif accion == "delete_reunion":
        rid = str(body.get("id"))
        ids_t = {str(t["id"]) for t in datos["Tareas"] if str(t.get("reunion_id")) == rid}
        antes = len(datos["Reuniones"])
        datos["Seguimiento"] = [g for g in datos["Seguimiento"]
                                if str(g.get("tarea_id")) not in ids_t
                                and str(g.get("reunion_id")) != rid]
        datos["Tareas"] = [t for t in datos["Tareas"] if str(t.get("reunion_id")) != rid]
        datos["Reuniones"] = [r for r in datos["Reuniones"] if str(r.get("id")) != rid]
        if len(datos["Reuniones"]) == antes:
            return jsonify({"ok": False, "msg": "Reunión no encontrada"})

    else:
        return jsonify({"ok": False, "msg": f"Acción desconocida: {accion}"})

    guardar(datos)
    return jsonify({"ok": True})


if __name__ == "__main__":
    print(f"▶  Simulador de la Hoja en http://localhost:5099  (datos: {ARCHIVO})")
    app.run(host="127.0.0.1", port=5099)
