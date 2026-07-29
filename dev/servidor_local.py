#!/usr/bin/env python3
"""
Arranque local todo-en-uno para desarrollo y pruebas.

Levanta el simulador de la Hoja (en un hilo, puerto 5099) y la app (puerto 5052)
con las variables ya puestas, sin necesidad de dos terminales ni de exportar nada
a mano. Es el equivalente de `iniciar.sh` pero en Python, para poder usarlo desde
la vista previa del editor.

    python3 dev/servidor_local.py

Toma la llave de Gemini de la del generador de actas si existe; si no, de la
variable GEMINI_API_KEY del entorno. Sin llave la app arranca igual: todo
funciona menos la generación con IA.
"""
import os, re, sys, threading, logging

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(RAIZ, "app"))
sys.path.insert(0, HERE)

PUERTO_HOJA = 5099
PUERTO_APP = int(os.environ.get("PORT", 5052))

# ── Llave de Gemini: se reutiliza la del generador de actas para que siga
# existiendo en un solo archivo del computador, en vez de copiarla aquí.
if not os.environ.get("GEMINI_API_KEY"):
    ruta = "/Users/santiagorincon/Desktop/Claude/Actas /iniciar.sh"
    try:
        with open(ruta) as f:
            m = re.search(r'^export GEMINI_API_KEY=["\']?([^"\'\n]+)', f.read(), re.M)
        if m:
            os.environ["GEMINI_API_KEY"] = m.group(1).strip()
            print("✓ Llave de Gemini tomada del generador de actas")
    except Exception:
        print("⚠️  Sin GEMINI_API_KEY: la app arranca, pero no podrá generar actas")

os.environ["LOG_URL"] = f"http://127.0.0.1:{PUERTO_HOJA}"
os.environ["DEV_LOCAL"] = "1"
os.environ.setdefault("SECRET_KEY", "desarrollo-local-no-usar-en-produccion")

logging.getLogger("werkzeug").setLevel(logging.WARNING)

import mock_hoja
import app as aplicacion


def _hoja():
    mock_hoja.app.run(host="127.0.0.1", port=PUERTO_HOJA, use_reloader=False)


threading.Thread(target=_hoja, daemon=True).start()

print(f"▶  Simulador de la Hoja  → http://127.0.0.1:{PUERTO_HOJA}")
print(f"▶  Actas de Proveedores  → http://localhost:{PUERTO_APP}")
print(f"   Datos de prueba en {os.path.join(HERE, 'datos_prueba.json')}")

aplicacion.app.run(host="0.0.0.0", port=PUERTO_APP, use_reloader=False)
