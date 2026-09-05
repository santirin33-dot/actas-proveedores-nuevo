#!/usr/bin/env python3
"""
Siembra datos de prueba en el simulador de la Hoja.

Sirve para ver el tablero y la línea de tiempo con volumen realista —vencidos,
varios proveedores, una segunda reunión que reporta avances— sin gastar cuota de
Gemini ni tocar datos reales.

    python3 dev/sembrar.py          # agrega a lo que ya haya
    python3 dev/sembrar.py --limpio # borra todo y siembra de cero

NO forma parte de la app desplegada.
"""
import os, sys, json, uuid
from datetime import date, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(HERE, "datos_prueba.json")
HOY = date.today()


def d(dias):
    return (HOY + timedelta(days=dias)).isoformat()


def ident(pre):
    return f"{pre}-{HOY.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"


PROVEEDORES = [
    ("Ascensores Andinos S.A.S.", "Ascensores", "Mario Ramírez", "3105551122"),
    ("Aseo Total Ltda.", "Aseo y limpieza", "Claudia Restrepo", "3145559988"),
    ("Vigilancia Centinela", "Seguridad y vigilancia", "Édgar Molina", "3025557766"),
    ("Jardines del Sur", "Jardinería", "Luz Marina Ospina", "3185554433"),
]

# (tema, tarea, responsable, estado, prioridad, dias_acordado, dias_plazo)
# dias_plazo None = sin plazo, que es un caso que la interfaz debe manejar sin
# inventarle urgencia.
COMPROMISOS = {
    0: [
        ("Mantenimiento", "Reemplazar la botonera del ascensor 2 de la torre A", "Mario Ramírez – Ascensores Andinos", "pendiente", "alta", -45, -12),
        ("Facturación", "Enviar la nota crédito de la factura FE-4471", "Mario Ramírez – Ascensores Andinos", "pendiente", "media", -45, -4),
        ("Mantenimiento", "Entregar el cronograma de mantenimiento preventivo del semestre", "Mario Ramírez – Ascensores Andinos", "en_proceso", "media", -20, 6),
        ("Contrato", "Revisar la cláusula de tiempos de respuesta con jurídica", "Gerencia de Proveedores", "pendiente", "baja", -20, None),
    ],
    1: [
        ("Personal", "Reponer la operaria de la torre B en turno de la tarde", "Claudia Restrepo – Aseo Total", "completada", "alta", -30, -18),
        ("Insumos", "Cambiar el proveedor de bolsas por uno biodegradable", "Claudia Restrepo – Aseo Total", "en_proceso", "media", -30, 12),
        ("Calidad", "Presentar el plan de choque para los sótanos", "Claudia Restrepo – Aseo Total", "pendiente", "media", -8, 3),
    ],
    2: [
        ("Seguridad", "Instalar el punto de cámara en el acceso peatonal", "Édgar Molina – Centinela", "pendiente", "alta", -60, -25),
        ("Documentación", "Entregar hojas de vida y antecedentes del personal nuevo", "Édgar Molina – Centinela", "completada", "alta", -60, -40),
        ("Capacitación", "Programar la capacitación de manejo de emergencias", "Édgar Molina – Centinela", "pendiente", "media", -14, 20),
    ],
    3: [
        ("Poda", "Podar los árboles del costado occidental antes de la temporada de lluvias", "Luz Marina Ospina – Jardines del Sur", "completada", "media", -25, -10),
        ("Riego", "Cotizar el sistema de riego automático para la zona común", "Luz Marina Ospina – Jardines del Sur", "pendiente", "baja", -25, None),
    ],
}

REUNIONES = {
    0: [
        (-45, "Seguimiento de mantenimiento y facturación pendiente",
         "Se revisó el estado de los dos ascensores de la torre A tras las fallas reportadas en junio. "
         "El proveedor reconoció el retraso en la botonera y quedó de enviar la nota crédito de una factura mal liquidada. "
         "Se discutió el cronograma de mantenimiento preventivo del semestre."),
        (-20, "Revisión de avances y cronograma preventivo",
         "Se retomaron los pendientes de la reunión anterior. El proveedor presentó avances parciales en el cronograma "
         "y reconoció que la botonera sigue sin reemplazarse por demora del importador. Se acordó revisar la cláusula "
         "de tiempos de respuesta del contrato."),
    ],
    1: [(-30, "Refuerzo de personal e insumos",
         "Se trató la ausencia de la operaria de la torre B en el turno de la tarde y su impacto en la percepción de los residentes. "
         "También se evaluó el cambio a insumos biodegradables."),
        (-8, "Calidad del servicio en sótanos",
         "Los residentes reportaron acumulación de polvo en los sótanos. El proveedor quedó de presentar un plan de choque.")],
    2: [(-60, "Inicio de contrato y documentación de personal",
         "Primera reunión del contrato vigente. Se revisó la documentación del personal asignado y se identificó un punto ciego "
         "en el acceso peatonal que requiere cámara."),
        (-14, "Seguimiento de seguridad física",
         "Se verificó el estado de los compromisos iniciales. La documentación quedó al día; la cámara del acceso peatonal "
         "sigue sin instalarse.")],
    3: [(-25, "Programación de poda y riego",
         "Se programó la poda del costado occidental antes de la temporada de lluvias y se pidió cotización "
         "de un sistema de riego automático.")],
}

TEMAS = [
    ("Estado del servicio", "Se revisó el desempeño del proveedor en el periodo, con los reportes recibidos de la administración.",
     "Se acordó mantener el seguimiento mensual y documentar cada incidencia."),
    ("Pendientes de la reunión anterior", "Se repasaron uno a uno los compromisos que quedaron abiertos.",
     "Se ratificaron los plazos y se ajustaron los que estaban vencidos."),
    ("Costos y facturación", "Se revisaron los valores facturados en el último trimestre frente a lo contratado.",
     "Se solicitó la corrección de las inconsistencias identificadas."),
]


# Acuerdos de servicio: PRINCIPIOS del contrato. Sin fecha, sin caducidad y sin
# estado de cumplimiento. Jardines del Sur va sin ninguno a propósito, para que
# el estado vacío de esa sección también se vea al probar.
ANS = [
    [("Revisión anual de cables de tracción con empresa certificada", "Anual",
      "Incluye informe firmado por ingeniero y copia para la administración."),
     ("Atención de emergencias en menos de 2 horas", "Permanente",
      "Aplica 24/7, incluidos fines de semana y festivos.")],
    [("Refuerzo de aseo con maquinaria especializada", "Anual",
      "Pulido de pisos de zonas comunes y lavado de fachada interna.")],
    [("Reemplazo del personal de puesto en menos de 4 horas", "Permanente",
      "Ante ausencia no programada del guarda asignado.")],
    [],
]

# Responsabilidades continuas: sin plazo y fuera del cumplimiento.
PERMANENTES = [
    [("Supervisión permanente del estado de los ascensores", "Mario Ramírez – Ascensores Andinos"),
     ("Control mensual del consumo eléctrico de los equipos", "Gerencia de Proveedores")],
    [("Control diario de insumos y dotación del personal", "Claudia Restrepo – Aseo Total")],
    [],
    [("Seguimiento mensual del sistema de riego automatizado", "Jardines del Sur")],
]


def sembrar(datos):
    for i, (nombre, tipo, contacto, tel) in enumerate(PROVEEDORES):
        pid = ident("PRV")
        datos["Proveedores"].append({
            "id": pid, "nombre": nombre, "tipo_servicio": tipo, "contacto": contacto,
            "email": "", "telefono": tel, "estado": "activo",
            "creado_por": "prueba@abelardoyepes.com", "fecha_creacion": d(-90),
        })

        reuniones_ids = []
        for j, (dias, titulo, resumen) in enumerate(REUNIONES[i]):
            rid = ident("REU")
            reuniones_ids.append(rid)
            datos["Reuniones"].append({
                "id": rid, "fecha": d(dias), "proveedor_id": pid, "proveedor": nombre,
                "tipo_servicio": tipo, "titulo": titulo,
                "participantes": f"{contacto} – {nombre}; David – Gerencia de Proveedores",
                "resumen": resumen,
                "temas_json": json.dumps({
                    "temas": [{"titulo": t, "discusion": di, "conclusion": c}
                              for t, di, c in (TEMAS if j else TEMAS[:2])],
                    "proxima_reunion": "",
                }, ensure_ascii=False),
                "generado_por": "prueba@abelardoyepes.com",
                "fecha_registro": d(dias) + " 10:30",
            })

        tareas_ids = []
        for tema, tarea, resp, estado, prio, dacord, dplazo in COMPROMISOS[i]:
            # Cada compromiso se cuelga de la reunión cuya fecha coincide.
            rid = reuniones_ids[0]
            for k, (dias, _, _) in enumerate(REUNIONES[i]):
                if dias == dacord:
                    rid = reuniones_ids[k]
            tid = ident("TAR")
            tareas_ids.append((tid, estado, dacord))
            datos["Tareas"].append({
                "id": tid, "reunion_id": rid, "fecha": d(dacord), "proveedor_id": pid,
                "proveedor": nombre, "tipo_servicio": tipo, "tema": tema, "tarea": tarea,
                "responsable": resp, "estado": estado, "prioridad": prio,
                "fecha_limite": d(dplazo) if dplazo is not None else "",
                "fecha_completada": d(dplazo) if estado == "completada" and dplazo is not None else "",
                "tarea_origen_id": "", "actualizado_por": "prueba@abelardoyepes.com",
                "tipo": "normal", "ans_id": "",
            })

        # La segunda reunión reporta avance sobre los compromisos de la primera:
        # es lo que dibuja la cadena de seguimiento en la línea de tiempo.
        if len(reuniones_ids) > 1:
            segunda_fecha = REUNIONES[i][1][0]
            for tid, estado, dacord in tareas_ids:
                if dacord >= segunda_fecha:
                    continue
                nuevo = "completada" if estado == "completada" else "en_proceso"
                datos["Seguimiento"].append({
                    "id": ident("SEG"), "tarea_id": tid, "fecha": d(segunda_fecha),
                    "reunion_id": reuniones_ids[1],
                    "avance": ("El proveedor confirmó que quedó ejecutado y entregó el soporte."
                               if nuevo == "completada"
                               else "El proveedor reportó avance parcial y pidió ampliación del plazo."),
                    "estado_anterior": "pendiente", "estado_nuevo": nuevo,
                    "autor": "prueba@abelardoyepes.com",
                })

        # ── Acuerdos de servicio ──
        for k, (titulo, periodicidad, descripcion) in enumerate(ANS[i]):
            aid = ident("ANS")
            datos["ANS"].append({
                "id": aid, "proveedor_id": pid, "proveedor": nombre,
                "titulo": titulo, "descripcion": descripcion,
                "periodicidad": periodicidad, "activo": "si",
                "creado_por": "prueba@abelardoyepes.com", "fecha_creacion": d(-80),
            })
            # Del primer acuerdo de cada proveedor cuelga una ejecución, para que
            # la relación ANS → tarea se vea sin tener que crearla a mano. No
            # cuenta en el cumplimiento: se mide aparte.
            if k == 0:
                datos["Tareas"].append({
                    "id": ident("TAR"), "reunion_id": "", "fecha": d(-40),
                    "proveedor_id": pid, "proveedor": nombre, "tipo_servicio": tipo,
                    "tema": "ANS", "tarea": f"Ejecutar: {titulo}",
                    "responsable": contacto, "estado": "pendiente", "prioridad": "media",
                    "fecha_limite": d(30), "fecha_completada": "",
                    "tarea_origen_id": "", "actualizado_por": "prueba@abelardoyepes.com",
                    "tipo": "ans", "ans_id": aid,
                })

        # ── Responsabilidades permanentes ──
        for tarea, resp in PERMANENTES[i]:
            datos["Tareas"].append({
                "id": ident("TAR"), "reunion_id": "", "fecha": d(-70),
                "proveedor_id": pid, "proveedor": nombre, "tipo_servicio": tipo,
                "tema": "", "tarea": tarea, "responsable": resp,
                "estado": "pendiente", "prioridad": "media",
                # Sin plazo a propósito: es continua, no puede vencer.
                "fecha_limite": "", "fecha_completada": "",
                "tarea_origen_id": "", "actualizado_por": "prueba@abelardoyepes.com",
                "tipo": "permanente", "ans_id": "",
            })


def main():
    if "--limpio" in sys.argv or not os.path.exists(ARCHIVO):
        datos = {"Proveedores": [], "Reuniones": [], "Tareas": [],
                 "Seguimiento": [], "ANS": []}
    else:
        with open(ARCHIVO, encoding="utf-8") as f:
            datos = json.load(f)

    sembrar(datos)

    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    print(f"Sembrado en {ARCHIVO}")
    for k, v in datos.items():
        print(f"  {k}: {len(v)}")
    print("\nReinicia el servidor o pulsa «Actualizar datos» en el tablero.")


if __name__ == "__main__":
    main()
