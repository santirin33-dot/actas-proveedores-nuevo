#!/usr/bin/env python3
"""
Genera el .docx del acta de reunión con un proveedor.

A diferencia del generador F08, aquí NO hay plantilla: el documento se arma
desde cero con python-docx. Es a propósito — el gerente pidió un acta sin
formato institucional, así que no hay cuadros que rellenar ni XML que manipular.
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

VERDE = RGBColor(0x2F, 0x5D, 0x0E)
GRIS = RGBColor(0x5C, 0x66, 0x54)
NEGRO = RGBColor(0x1E, 0x24, 0x1A)

MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_larga(iso):
    """2026-07-29 → 29 de julio de 2026. Si no se puede, devuelve lo que llegó."""
    try:
        a, m, d = str(iso).split("-")
        return f"{int(d)} de {MESES[int(m)]} de {a}"
    except Exception:
        return str(iso or "")


def _texto(doc, contenido, tam=10.5, negrita=False, color=NEGRO,
           espacio_antes=0, espacio_despues=4, alineacion=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(espacio_antes)
    p.paragraph_format.space_after = Pt(espacio_despues)
    if alineacion is not None:
        p.alignment = alineacion
    r = p.add_run(contenido)
    r.font.size = Pt(tam)
    r.font.bold = negrita
    r.font.color.rgb = color
    return p


def build(acta, proveedor, tipo_servicio, destino):
    """Escribe el .docx. `acta` es el JSON ya revisado por el gerente.

    `destino` puede ser una ruta o cualquier objeto tipo archivo (un BytesIO),
    que es como lo usa la app: el documento no toca el disco."""
    doc = Document()

    # Márgenes cómodos: es un documento para leer, no un formato oficial.
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Cm(2)
        s.left_margin = s.right_margin = Cm(2.2)

    estilo = doc.styles["Normal"]
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(10.5)

    # ── Encabezado ──
    _texto(doc, "ACTA DE REUNIÓN CON PROVEEDOR", tam=9, negrita=True, color=GRIS,
           espacio_despues=2)
    _texto(doc, acta.get("titulo") or f"Reunión con {proveedor}", tam=17, negrita=True,
           color=VERDE, espacio_despues=10)

    ficha = [
        ("Proveedor", proveedor),
        ("Tipo de servicio", tipo_servicio),
        ("Fecha", fecha_larga(acta.get("fecha", ""))),
    ]
    participantes = [p for p in (acta.get("participantes") or []) if str(p).strip()]
    if participantes:
        ficha.append(("Participantes", "; ".join(participantes)))

    for etiqueta, valor in ficha:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(f"{etiqueta}:  ")
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = GRIS
        r2 = p.add_run(str(valor))
        r2.font.size = Pt(10)

    # ── Resumen ──
    if (acta.get("resumen") or "").strip():
        _texto(doc, "RESUMEN", tam=9, negrita=True, color=GRIS, espacio_antes=14, espacio_despues=3)
        _texto(doc, acta["resumen"].strip(), alineacion=WD_ALIGN_PARAGRAPH.JUSTIFY, espacio_despues=6)

    # ── Temas tratados ──
    temas = [t for t in (acta.get("temas") or []) if (t.get("titulo") or "").strip()]
    if temas:
        _texto(doc, "TEMAS TRATADOS", tam=9, negrita=True, color=GRIS,
               espacio_antes=14, espacio_despues=6)
        for i, t in enumerate(temas, 1):
            _texto(doc, f"{i}. {t.get('titulo', '').strip()}", tam=11.5, negrita=True,
                   color=VERDE, espacio_antes=8, espacio_despues=3)
            if (t.get("discusion") or "").strip():
                _texto(doc, t["discusion"].strip(), alineacion=WD_ALIGN_PARAGRAPH.JUSTIFY,
                       espacio_despues=3)
            if (t.get("conclusion") or "").strip():
                # La conclusión va marcada porque es lo que el gerente busca al releer.
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.left_indent = Cm(0.4)
                r = p.add_run("Conclusión:  ")
                r.font.size = Pt(10.5)
                r.font.bold = True
                r.font.color.rgb = VERDE
                r2 = p.add_run(t["conclusion"].strip())
                r2.font.size = Pt(10.5)
                r2.font.bold = True

    # ── Compromisos ──
    compromisos = [c for c in (acta.get("compromisos") or []) if (c.get("tarea") or "").strip()]
    _texto(doc, "COMPROMISOS", tam=9, negrita=True, color=GRIS,
           espacio_antes=16, espacio_despues=6)

    if not compromisos:
        _texto(doc, "La reunión no dejó compromisos pendientes.", color=GRIS)
    else:
        tabla = doc.add_table(rows=1, cols=4)
        tabla.style = "Table Grid"
        tabla.alignment = WD_TABLE_ALIGNMENT.CENTER
        anchos = [Cm(6.4), Cm(4.2), Cm(3.2), Cm(2.6)]
        for celda, titulo, ancho in zip(tabla.rows[0].cells,
                                        ["TAREA", "RESPONSABLE", "FECHA LÍMITE", "PRIORIDAD"],
                                        anchos):
            celda.width = ancho
            r = celda.paragraphs[0].add_run(titulo)
            r.font.size = Pt(8.5)
            r.font.bold = True
            r.font.color.rgb = GRIS

        for c in compromisos:
            fila = tabla.add_row().cells
            valores = [
                c.get("tarea", "").strip(),
                c.get("responsable", "").strip() or "—",
                fecha_larga(c["fecha_limite"]) if c.get("fecha_limite") else "Sin plazo",
                (c.get("prioridad") or "media").capitalize(),
            ]
            for celda, valor, ancho in zip(fila, valores, anchos):
                celda.width = ancho
                r = celda.paragraphs[0].add_run(valor)
                r.font.size = Pt(9.5)

    # ── Próxima reunión ──
    if (acta.get("proxima_reunion") or "").strip():
        _texto(doc, f"Próxima reunión: {fecha_larga(acta['proxima_reunion'])}",
               negrita=True, espacio_antes=14)

    _texto(doc,
           "Documento generado automáticamente a partir de la transcripción de la reunión "
           "y revisado por la Gerencia de Proveedores — Abelardo Yepes S.A.S.",
           tam=8, color=GRIS, espacio_antes=18)

    doc.save(destino)
    return destino
