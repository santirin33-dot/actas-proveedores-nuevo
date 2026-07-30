#!/usr/bin/env python3
"""
Genera el .docx del acta de reunión con un proveedor.

Formato de ficha gerencial: una banda de datos arriba, el resumen a todo el
ancho, y los temas como bloques numerados en dos columnas —cada uno con su
título, lo que se habló y la conclusión etiquetada—, cerrando con la matriz de
compromisos.

No hay plantilla: el documento se arma desde cero con python-docx. Es a
propósito, porque el gerente pidió un acta sin formato institucional.

Paleta deliberadamente apagada: el verde de Abelardo Yepes como único color, y
grises para todo lo demás. El documento se lee con el proveedor al lado, así que
no lleva los colores de cartilla de una infografía.
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

VERDE  = RGBColor(0x2F, 0x5D, 0x19)   # acento de marca
GRIS   = RGBColor(0x5C, 0x66, 0x54)   # texto secundario
NEGRO  = RGBColor(0x1E, 0x24, 0x1A)   # texto principal

TINTA_BLOQUE = "F3F7F0"   # fondo de cada bloque de tema
TINTA_BANDA  = "EDF2E8"   # fondo de la banda de datos y del encabezado de tabla
LINEA        = "D5DED1"   # filete

MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_larga(iso):
    """2026-07-29 → 29 de julio de 2026. Si no se puede, devuelve lo que llegó."""
    try:
        a, m, d = str(iso).split("-")
        return f"{int(d)} de {MESES[int(m)]} de {a}"
    except Exception:
        return str(iso or "")


# ─────────────── Utilidades de XML ───────────────
# python-docx no expone sombreado, bordes ni márgenes de celda, así que hay que
# escribir el XML a mano. Son las tres piezas que sostienen el aspecto de ficha.

def _sombrear(celda, hex_color):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    celda._tc.get_or_add_tcPr().append(shd)


def _bordes_celda(celda, color=LINEA, grosor=6, lados=("top", "left", "bottom", "right")):
    """grosor va en octavos de punto: 6 = 0,75 pt."""
    tcPr = celda._tc.get_or_add_tcPr()
    bordes = OxmlElement("w:tcBorders")
    for lado in lados:
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), str(grosor))
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        bordes.append(el)
    tcPr.append(bordes)


def _margenes_celda(celda, arriba=110, izq=140, abajo=110, der=140):
    """Márgenes internos en vigésimos de punto (dxa). 140 ≈ 0,25 cm."""
    tcPr = celda._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for lado, valor in (("top", arriba), ("left", izq), ("bottom", abajo), ("right", der)):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:w"), str(valor))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tcPr.append(mar)


def _sin_bordes_tabla(tabla):
    """La tabla que hace de rejilla no debe verse: los bordes los ponen las celdas."""
    borders = OxmlElement("w:tblBorders")
    for lado in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{lado}")
        el.set(qn("w:val"), "none")
        el.set(qn("w:sz"), "0")
        borders.append(el)
    tabla._tbl.tblPr.append(borders)


def _separacion_celdas(tabla, dxa=90):
    """Aire entre bloques. Es lo que los hace leer como fichas y no como tabla."""
    esp = OxmlElement("w:tblCellSpacing")
    esp.set(qn("w:w"), str(dxa))
    esp.set(qn("w:type"), "dxa")
    tabla._tbl.tblPr.append(esp)


def _ancho_fijo(tabla):
    """Obliga a Word a respetar los anchos que se le dan.

    Sin esto, Word reparte las columnas a su criterio según el contenido: la
    columna del número quedaba enorme y la del compromiso estrangulada."""
    tabla.autofit = False
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tabla._tbl.tblPr.append(layout)


def _fila_no_se_parte(fila):
    """Un bloque cortado a mitad entre dos páginas es ilegible."""
    trPr = fila._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))


def _regla(parrafo, color=LINEA):
    """Filete fino bajo un párrafo, para separar la conclusión de la discusión."""
    pPr = parrafo._p.get_or_add_pPr()
    bordes = OxmlElement("w:pBdr")
    el = OxmlElement("w:bottom") if False else OxmlElement("w:bottom")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), "6")
    el.set(qn("w:space"), "4")
    el.set(qn("w:color"), color)
    bordes.append(el)
    pPr.append(bordes)


# ─────────────── Bloques de texto ───────────────
def _p(contenedor, texto="", tam=9.5, negrita=False, color=NEGRO,
       antes=0, despues=3, alineacion=None, interlineado=None, primero=False):
    """Añade un párrafo. `primero` reutiliza el párrafo vacío que traen las celdas
    recién creadas, para que no quede un renglón en blanco arriba."""
    if primero and getattr(contenedor, "paragraphs", None):
        p = contenedor.paragraphs[0]
    else:
        p = contenedor.add_paragraph()
    p.paragraph_format.space_before = Pt(antes)
    p.paragraph_format.space_after = Pt(despues)
    if interlineado:
        p.paragraph_format.line_spacing = interlineado
    if alineacion is not None:
        p.alignment = alineacion
    if texto:
        r = p.add_run(texto)
        r.font.size = Pt(tam)
        r.font.bold = negrita
        r.font.color.rgb = color
    return p


def _rotulo(contenedor, texto, primero=False):
    p = _p(contenedor, "", despues=2, primero=primero)
    r = p.add_run(texto.upper())
    r.font.size = Pt(7)
    r.font.bold = True
    r.font.color.rgb = GRIS
    r.font.all_caps = True
    return p


def _banda_datos(doc, acta, proveedor, tipo_servicio):
    """Los metadatos de la reunión, en una banda de una sola celda."""
    t = doc.add_table(rows=1, cols=1)
    _sin_bordes_tabla(t)
    celda = t.rows[0].cells[0]
    _sombrear(celda, TINTA_BANDA)
    _bordes_celda(celda)
    _margenes_celda(celda, 140, 170, 140, 170)

    filas = [("Proveedor", proveedor), ("Tipo de servicio", tipo_servicio),
             ("Fecha", fecha_larga(acta.get("fecha", "")))]
    participantes = [p for p in (acta.get("participantes") or []) if str(p).strip()]
    if participantes:
        filas.append(("Participantes", "; ".join(participantes)))

    for i, (etiqueta, valor) in enumerate(filas):
        p = _p(celda, "", despues=2 if i < len(filas) - 1 else 0, primero=(i == 0))
        r = p.add_run(f"{etiqueta}   ")
        r.font.size = Pt(8)
        r.font.bold = True
        r.font.color.rgb = GRIS
        r2 = p.add_run(str(valor))
        r2.font.size = Pt(9.5)
        r2.font.color.rgb = NEGRO


def _bloque_tema(celda, numero, tema):
    """Un tema: número y título, lo que se habló, y la conclusión etiquetada."""
    _sombrear(celda, TINTA_BLOQUE)
    _bordes_celda(celda)
    _margenes_celda(celda)

    # Número y título en el mismo renglón: el número es la marca del bloque.
    p = _p(celda, "", despues=4, primero=True)
    rn = p.add_run(f"{numero}   ")
    rn.font.size = Pt(13)
    rn.font.bold = True
    rn.font.color.rgb = VERDE
    rt = p.add_run((tema.get("titulo") or "").strip())
    rt.font.size = Pt(10.5)
    rt.font.bold = True
    rt.font.color.rgb = NEGRO

    discusion = (tema.get("discusion") or "").strip()
    if discusion:
        _p(celda, discusion, tam=9, despues=6,
           alineacion=WD_ALIGN_PARAGRAPH.JUSTIFY, interlineado=1.18)

    conclusion = (tema.get("conclusion") or "").strip()
    if conclusion:
        # El filete va sobre el rótulo, que es lo que separa la narración del
        # acuerdo. Es lo que el gerente busca cuando relee el acta.
        sep = _p(celda, "", despues=0, antes=2)
        _regla(sep)
        _rotulo(celda, "Conclusión")
        _p(celda, conclusion, tam=9, negrita=True, color=VERDE, despues=0,
           interlineado=1.15)


def _repartir(temas):
    """Parte los temas en dos columnas de altura parecida.

    Se reparte por longitud de texto y no por mitades: con un tema muy largo y
    tres cortos, cortar por la mitad dejaría una columna al doble de la otra.
    """
    largo = [len((t.get("discusion") or "")) + len((t.get("conclusion") or "")) + 90
             for t in temas]
    total = sum(largo)
    corte, acumulado = len(temas), 0
    for i, n in enumerate(largo):
        # El corte cae en cuanto pasar el siguiente tema desequilibraría más de
        # lo que ya está desequilibrado.
        if acumulado + n > total / 2 and i > 0:
            corte = i if abs(acumulado - total / 2) < abs(acumulado + n - total / 2) else i + 1
            break
        acumulado += n
    corte = max(1, min(corte, len(temas)))
    return temas[:corte], temas[corte:]


def _rejilla_temas(doc, temas):
    """Los temas en dos columnas continuas.

    Una sola fila con dos celdas, cada una con su pila de bloques, en vez de una
    fila por par de temas. Con filas por pares, cada fila espera a que quepa el
    bloque más alto y, si no cabe, salta de página entera: dejaba media hoja en
    blanco. Así cada columna se llena de corrido, como una columna de periódico.
    """
    izquierda, derecha = _repartir(temas)

    t = doc.add_table(rows=1, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    _sin_bordes_tabla(t)
    _separacion_celdas(t)

    ancho = Cm(8.4)
    for celda, grupo, desde in ((t.rows[0].cells[0], izquierda, 1),
                                (t.rows[0].cells[1], derecha, len(izquierda) + 1)):
        celda.width = ancho
        _p(celda, "", despues=0, primero=True)     # ancla del contenido de la celda
        for k, tema in enumerate(grupo):
            # Cada bloque es su propia tabla dentro de la columna: así conserva su
            # recuadro y, con cantSplit, no se parte entre dos páginas, mientras la
            # columna sigue fluyendo.
            interna = celda.add_table(rows=1, cols=1)
            interna.autofit = False
            _sin_bordes_tabla(interna)
            _fila_no_se_parte(interna.rows[0])
            interna.rows[0].cells[0].width = ancho
            _bloque_tema(interna.rows[0].cells[0], desde + k, tema)
            if k < len(grupo) - 1:
                _p(celda, "", tam=5, despues=0)     # aire entre bloques
    return t


def _matriz_compromisos(doc, compromisos):
    encabezados = ["", "COMPROMISO", "RESPONSABLE", "FECHA LÍMITE", "PRIOR."]
    anchos = [Cm(0.9), Cm(7.4), Cm(4.1), Cm(3.0), Cm(1.9)]

    t = doc.add_table(rows=1, cols=len(encabezados))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    _sin_bordes_tabla(t)

    for celda, titulo, ancho in zip(t.rows[0].cells, encabezados, anchos):
        celda.width = ancho
        _sombrear(celda, TINTA_BANDA)
        _bordes_celda(celda)
        _margenes_celda(celda, 70, 110, 70, 110)
        p = _p(celda, "", despues=0, primero=True)
        r = p.add_run(titulo)
        r.font.size = Pt(7)
        r.font.bold = True
        r.font.color.rgb = GRIS

    for i, c in enumerate(compromisos, 1):
        fila = t.add_row()
        _fila_no_se_parte(fila)
        valores = [
            str(i),
            c.get("tarea", "").strip(),
            c.get("responsable", "").strip() or "Sin asignar",
            fecha_larga(c["fecha_limite"]) if c.get("fecha_limite") else "Sin plazo",
            (c.get("prioridad") or "media").capitalize(),
        ]
        for j, (celda, valor, ancho) in enumerate(zip(fila.cells, valores, anchos)):
            celda.width = ancho
            _bordes_celda(celda)
            _margenes_celda(celda, 80, 110, 80, 110)
            p = _p(celda, "", despues=0, primero=True)
            r = p.add_run(valor)
            r.font.size = Pt(9)
            # El número y la prioridad alta son las dos cosas que se buscan de un
            # vistazo en la matriz.
            r.font.bold = (j == 0) or (j == 4 and valor == "Alta")
            r.font.color.rgb = VERDE if j == 0 else (
                NEGRO if j in (1,) else GRIS)
    return t


# ─────────────── Documento ───────────────
def build(acta, proveedor, tipo_servicio, destino):
    """Escribe el .docx. `acta` es el JSON ya revisado por el gerente.

    `destino` puede ser una ruta o un objeto en memoria (BytesIO)."""
    doc = Document()

    # Márgenes ajustados: con dos columnas de bloques hace falta el ancho.
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Cm(1.7)
        s.left_margin = s.right_margin = Cm(1.5)

    estilo = doc.styles["Normal"]
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(9.5)
    estilo.font.color.rgb = NEGRO

    # ── Encabezado ──
    _rotulo(doc, "Acta ejecutiva de reunión con proveedor")
    titulo = _p(doc, (acta.get("titulo") or f"Reunión con {proveedor}").strip(),
                tam=17, negrita=True, color=VERDE, despues=10)
    titulo.paragraph_format.space_before = Pt(0)

    _banda_datos(doc, acta, proveedor, tipo_servicio)

    # ── Resumen ──
    resumen = (acta.get("resumen") or "").strip()
    if resumen:
        _p(doc, "", despues=0, antes=10)
        _rotulo(doc, "Resumen de la reunión")
        _p(doc, resumen, tam=9.5, despues=4,
           alineacion=WD_ALIGN_PARAGRAPH.JUSTIFY, interlineado=1.2)

    # ── Temas en dos columnas ──
    temas = [t for t in (acta.get("temas") or []) if (t.get("titulo") or "").strip()]
    if temas:
        _p(doc, "", despues=0, antes=12)
        _rotulo(doc, "Temas tratados y conclusiones")
        _p(doc, "", despues=2)
        _rejilla_temas(doc, temas)

    # ── Compromisos ──
    compromisos = [c for c in (acta.get("compromisos") or []) if (c.get("tarea") or "").strip()]
    _p(doc, "", despues=0, antes=16)
    _rotulo(doc, "Matriz de compromisos")
    _p(doc, "", despues=2)
    if compromisos:
        _matriz_compromisos(doc, compromisos)
    else:
        _p(doc, "La reunión no dejó compromisos pendientes.", tam=9, color=GRIS)

    # ── Cierre ──
    if (acta.get("proxima_reunion") or "").strip():
        _p(doc, "", despues=0, antes=12)
        p = doc.paragraphs[-1]
        r = p.add_run("Próxima reunión   ")
        r.font.size = Pt(8)
        r.font.bold = True
        r.font.color.rgb = GRIS
        r2 = p.add_run(fecha_larga(acta["proxima_reunion"]))
        r2.font.size = Pt(9.5)
        r2.font.bold = True
        r2.font.color.rgb = NEGRO

    _p(doc, "Documento generado a partir de la transcripción de la reunión y revisado "
            "por la Gerencia de Proveedores — Abelardo Yepes S.A.S.",
       tam=7.5, color=GRIS, antes=16)

    doc.save(destino)
    return destino
