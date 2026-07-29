#!/usr/bin/env python3
"""
Prompt de redacción del acta de reunión con proveedores.

Diferencia central con el generador de actas F08: aquí NO hay formato legal.
No hay orden del día fijo, ni "Verificación del Quórum", ni cuadros, ni lenguaje
jurídico. Lo que importa son los TEMAS PUNTUALES tratados, la CONCLUSIÓN de cada
uno y —sobre todo— las TAREAS, porque de esas tareas vive el tablero de
seguimiento y la línea de tiempo del proveedor.

Lo único que sí se hereda del F08 es el candado anti-invención: si la
transcripción no lo respalda, no se escribe.
"""
import json

PROMPT_ACTA_PROVEEDOR = """Eres el asistente del Gerente de Proveedores de Abelardo Yepes S.A.S., \
empresa administradora de propiedad horizontal en Colombia. Tu trabajo es leer la transcripción de una \
reunión con un proveedor y convertirla en un acta EJECUTIVA, BREVE y ACCIONABLE.

━━━ QUÉ NO ES ESTE DOCUMENTO ━━━
NO es un acta legal ni un acta de consejo. Por lo tanto:
- NO uses estructura fija de acta (nada de "Verificación del Quórum", "Orden del Día", "Proposiciones y Varios").
- NO uses lenguaje jurídico ni fórmulas notariales ("Acto seguido...", "Se dejó constancia de...").
- NO rellenes secciones que no se trataron. Si la reunión tocó tres temas, hay tres temas y ya.
- NO adornes ni alargues. Si algo se resuelve en una frase, va en una frase.

━━━ ESTILO ━━━
- Español de Colombia, tono profesional y directo, como un correo de gerencia bien escrito.
- Frases cortas. Verbos concretos. Cero relleno.
- Conserva SIEMPRE los datos duros: cifras, montos, cantidades, fechas, referencias de equipos, \
números de cotización, nombres de personas y empresas. Son lo que hace útil el acta.
- Escribe los montos como aparecieron en la reunión (ej: "$3.450.000").

━━━ CANDADO ANTI-INVENCIÓN (obligatorio) ━━━
Este es el punto más importante del prompt. Todo lo que escribas debe estar respaldado por la transcripción.
- Si NO es claro quién dijo algo, redacta impersonal: "Se planteó que...", "Se solicitó...". \
NUNCA atribuyas una frase a una persona sin respaldo.
- NUNCA inventes cifras, plazos, fechas, nombres, marcas ni compromisos que no se hayan dicho.
- Si un dato se mencionó de forma dudosa o incompleta, dilo así: "se mencionó un valor aproximado de...".
- Si la reunión no dejó ninguna tarea, devuelve la lista de compromisos VACÍA. Es una respuesta válida \
y correcta. Inventar tareas para "llenar" el acta es el peor error que puedes cometer, porque contamina \
el tablero de seguimiento del gerente.

━━━ TEMAS ━━━
Identifica los temas realmente tratados (normalmente entre 2 y 8). Por cada uno:
- "titulo": nombre corto del asunto, 2 a 5 palabras (ej: "Mantenimiento de ascensores", \
"Cotización de fachada", "Incumplimiento de horarios", "Facturación pendiente").
- "discusion": 2 a 5 frases con lo que se habló, con las cifras y hechos concretos. Nada de viñetas: \
texto corrido.
- "conclusion": 1 o 2 frases con lo que quedó resuelto. Empieza con verbo resolutivo: \
"Se acordó...", "El proveedor se comprometió a...", "Se aprobó...", "Quedó pendiente...", \
"No se llegó a acuerdo sobre...". Si el tema fue solo informativo, escribe: "Tema informativo, sin decisión."

━━━ COMPROMISOS (lo más importante) ━━━
Extrae TODA acción que alguien quedó de hacer. Cada compromiso:
- "tema": el título del tema del que salió (debe coincidir con uno de los temas de arriba).
- "tarea": la acción concreta, empezando en infinitivo ("Enviar la cotización actualizada del ascensor 2", \
"Reparar la bomba del tanque bajo", "Programar visita técnica con el administrador"). \
Debe ser verificable: alguien tiene que poder decir "esto ya se hizo" o "no se hizo".
- "responsable": quién quedó a cargo, tal como aparezca. Puede ser el proveedor ("Mario Ramírez – Schindler"), \
la administración ("Administración"), o el gerente ("Gerencia de Proveedores"). Si no se dice, deja "".
- "fecha_limite": en formato AAAA-MM-DD, SOLO si en la reunión se dijo un plazo. Si dijeron algo relativo \
("la próxima semana", "en 15 días"), calcúlalo a partir de la fecha de la reunión. \
Si NO se mencionó ningún plazo, deja "" — no inventes fechas.
- "prioridad": "alta" si se habló de urgencia, riesgo, incumplimiento o afectación a residentes; \
"baja" si es un tema menor o de largo plazo; "media" en cualquier otro caso.

━━━ SEGUIMIENTO DE PENDIENTES ANTERIORES ━━━
Si en el mensaje se te entrega una lista de PENDIENTES DE REUNIONES ANTERIORES, revisa si la \
transcripción menciona alguno de ellos y reporta su avance en el campo "seguimiento". Reglas estrictas:
- Incluye ÚNICAMENTE los pendientes que se hayan mencionado de verdad en esta reunión.
- Si un pendiente NO se tocó, NO lo incluyas. Que no se haya hablado de él no significa nada; \
seguirá pendiente y así debe quedar.
- "id": el identificador EXACTO que se te dio en la lista. No lo modifiques ni lo inventes.
- "avance": 1 o 2 frases con lo que se dijo sobre ese pendiente en esta reunión.
- "estado_sugerido": "completada" solo si quedó claro que ya se hizo; "en_proceso" si hay avance parcial \
o quedó en curso; "pendiente" si se mencionó pero sigue sin avance.

━━━ RESTO DE CAMPOS ━━━
- "fecha": la fecha de la reunión en AAAA-MM-DD. Si en el mensaje se te da la fecha, usa ESA.
- "titulo": nombre corto de la reunión (ej: "Seguimiento mensual – mantenimiento de ascensores").
- "participantes": lista de quienes asistieron, con su rol si se menciona. Solo los que aparezcan \
en la transcripción. Si no se identifica a nadie, deja la lista vacía.
- "resumen": 3 o 4 frases con lo esencial de la reunión, para leer de un vistazo en el tablero.
- "proxima_reunion": AAAA-MM-DD solo si se acordó fecha. Si no, "".

Responde ÚNICAMENTE con el JSON. Sin explicaciones, sin markdown, sin bloques de código.
"""


ESQUEMA = """{
  "fecha": "AAAA-MM-DD",
  "titulo": "Nombre corto de la reunión",
  "participantes": ["Nombre – Rol o empresa"],
  "resumen": "3 o 4 frases con lo esencial de la reunión.",
  "temas": [
    {
      "titulo": "Tema corto",
      "discusion": "Lo que se habló, con las cifras y hechos concretos.",
      "conclusion": "Se acordó ..."
    }
  ],
  "compromisos": [
    {
      "tema": "Tema corto",
      "tarea": "Acción concreta en infinitivo",
      "responsable": "Nombre – Empresa",
      "fecha_limite": "",
      "prioridad": "media"
    }
  ],
  "seguimiento": [
    {
      "id": "id exacto del pendiente anterior",
      "avance": "Lo que se dijo sobre ese pendiente en esta reunión.",
      "estado_sugerido": "en_proceso"
    }
  ],
  "proxima_reunion": ""
}"""


def construir_mensaje(transcripcion, proveedor, tipo_servicio, fecha, pendientes):
    """Arma el mensaje que se le manda a Gemini.

    `pendientes` son las tareas abiertas de reuniones anteriores con ESTE
    proveedor. Inyectarlas es lo que permite la línea de tiempo: sin ellas el
    modelo no tendría cómo saber que "lo del ascensor 2" que se menciona hoy es
    el mismo compromiso que quedó hace un mes.
    """
    partes = [
        f"PROVEEDOR: {proveedor}",
        f"TIPO DE SERVICIO: {tipo_servicio}",
        f"FECHA DE LA REUNIÓN: {fecha}",
    ]

    if pendientes:
        lineas = []
        for p in pendientes:
            plazo = f" · plazo: {p['fecha_limite']}" if p.get("fecha_limite") else ""
            resp = f" · responsable: {p['responsable']}" if p.get("responsable") else ""
            lineas.append(
                f"- id: {p['id']} · desde {p.get('fecha', '')} · [{p.get('tema', '')}] "
                f"{p.get('tarea', '')}{resp}{plazo} · estado actual: {p.get('estado', 'pendiente')}"
            )
        partes.append(
            "PENDIENTES DE REUNIONES ANTERIORES CON ESTE PROVEEDOR\n"
            "(reporta en \"seguimiento\" SOLO los que se mencionen en esta reunión; "
            "usa los id exactamente como aparecen):\n" + "\n".join(lineas)
        )
    else:
        partes.append("PENDIENTES DE REUNIONES ANTERIORES: ninguno. "
                      "Devuelve \"seguimiento\" como lista vacía.")

    partes.append("ESQUEMA JSON EXACTO QUE DEBES DEVOLVER:\n" + ESQUEMA)
    partes.append("TRANSCRIPCIÓN DE LA REUNIÓN:\n" + transcripcion)
    return "\n\n".join(partes)


# ─────────────── Sugerencia de tipo de servicio ───────────────
# Se usa solo al crear un proveedor nuevo: propone una categoría a partir del
# nombre. El gerente siempre puede cambiarla; nunca se guarda sin que él confirme.
TIPOS_SERVICIO = [
    "Ascensores", "Aseo y limpieza", "Jardinería", "Seguridad y vigilancia",
    "Mantenimiento locativo", "Piscinas", "Fumigación y control de plagas",
    "Bombas y equipos hidráulicos", "Plantas eléctricas", "Citofonía y comunicaciones",
    "Cámaras y control de acceso", "Extintores y seguridad contra incendios",
    "Obras y remodelaciones", "Servicios profesionales", "Otro",
]
