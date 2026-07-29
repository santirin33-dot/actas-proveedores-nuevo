#!/usr/bin/env python3
"""
Punto de entrada para Vercel.

Vercel busca los archivos dentro de `api/` y, en el runtime de Python, toma la
variable `app` si es una aplicación WSGI. Toda la lógica vive en `app/app.py`;
este archivo solo la expone.

El `vercel.json` de la raíz reenvía todas las rutas aquí, así que Flask sigue
resolviendo su propio enrutamiento como en local.
"""
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "app"))

from app import app  # noqa: E402  (la ruta hay que ajustarla antes de importar)
