#!/usr/bin/env python3
"""
Genera el .docx del acta de reunión con un proveedor.

Maqueta de acta ejecutiva, en el formato que pidió la Gerencia de Proveedores:

    ACTA EJECUTIVA          ← titular serif a todo lo ancho
    banda de datos          ← fecha · participantes · servicio
    OBJETIVO                ← recuadro teñido
    DECISIONES CLAVE        ← tarjetas numeradas a dos columnas,
                              cada una con su conclusión destacada
    COMPROMISOS             ← agrupados por plazo, con cabecera navy
    PRÓXIMO HITO
    pie

No hay plantilla: el documento se arma desde cero con python-docx, escribiendo
a mano el XML de sombreados, bordes y márgenes de celda que la librería no
expone. Es lo que sostiene el aspecto de ficha.

Dos tipografías con papeles distintos: una serif para los titulares —es lo que
le da el aire de documento ejecutivo y no de informe de sistema— y la sans del
cuerpo para todo lo que se lee seguido. Ambas están en Windows y en Mac sin
instalar nada: el acta se abre en el computador del proveedor.

El acta se lee CON EL PROVEEDOR AL LADO. De ahí que el color sea el mismo azul
oscuro de la aplicación, que el verde solo aparezca en las conclusiones —lo que
se acordó, no lo que se reclama— y que ningún dato incómodo lleve adorno.
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── Paleta ──
# El mismo azul oscuro del tablero: el acta y la aplicación son el mismo
# producto y el proveedor las ve las dos.
NAVY   = RGBColor(0x10, 0x2A, 0x43)
VERDE  = RGBColor(0x28, 0x7A, 0x57)   # solo para lo acordado
GRIS   = RGBColor(0x66, 0x70, 0x85)   # texto secundario
NEGRO  = RGBColor(0x1F, 0x28, 0x33)   # cuerpo
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)

TINTA_SUAVE  = "EFF4F1"   # recuadros de objetivo y conclusión
TINTA_BANDA  = "F4F7F9"   # banda de datos
NAVY_HEX     = "102A43"   # cabeceras de tabla
LINEA        = "DCE3E8"
LINEA_SUAVE  = "E8EDF0"

SERIF = "Georgia"         # titulares
SANS  = "Calibri"         # cuerpo

MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_larga(iso):
    """2026-07-29 → 29 de julio de 2026. Si no se puede, devuelve lo que llegó."""
    try:
        a, m, d = str(iso).split("-")
        return f"{int(d)} de {MESES[int(m)]} de {a}"
    except Exception:
        return str(iso or "")


def fecha_corta(iso):
    """2026-09-04 → 4 SEP 2026, para la columna de plazos."""
    try:
        a, m, d = str(iso).split("-")
        return f"{int(d)} {MESES[int(m)][:3].upper()} {a}"
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


def _ancho_fijo(tabla, anchos=None):
    """Obliga a Word a respetar los anchos que se le dan.

    Sin `tblLayout=fixed`, Word reparte las columnas a su criterio según el
    contenido. Y aun con eso, el ancho que manda es el de la REJILLA de columnas
    (tblGrid), no el de cada celda: por eso hay que escribir
    `tabla.columns[i].width`, que es lo que python-docx traduce a la rejilla.
    Fijando solo el ancho de las celdas, la columna del número salía enorme y la
    del compromiso estrangulada."""
    tabla.autofit = False
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tabla._tbl.tblPr.append(layout)
    if anchos:
        for columna, ancho in zip(tabla.columns, anchos):
            columna.width = ancho
        for fila in tabla.rows:
            for celda, ancho in zip(fila.cells, anchos):
                celda.width = ancho


def _fila_no_se_parte(fila):
    """Un bloque cortado a mitad entre dos páginas es ilegible."""
    trPr = fila._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))


def _regla(parrafo, color=LINEA, grosor=6, espacio=4):
    """Filete bajo un párrafo. `grosor` va en octavos de punto: 6 es un filete
    fino de separación y 12 el trazo firme que cierra la cabecera."""
    pPr = parrafo._p.get_or_add_pPr()
    bordes = OxmlElement("w:pBdr")
    el = OxmlElement("w:bottom")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(grosor))
    el.set(qn("w:space"), str(espacio))
    el.set(qn("w:color"), color)
    bordes.append(el)
    pPr.append(bordes)



def _espaciado(run, twips=30):
    """Espaciado entre letras. Es lo que convierte un rótulo en mayúsculas en un
    rótulo compuesto; sin él, las versalitas se ven apelmazadas."""
    rPr = run._element.get_or_add_rPr()
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:val"), str(twips))
    rPr.append(sp)
    return run


def _p(contenedor, texto="", tam=9.5, negrita=False, color=NEGRO, fuente=None,
       antes=0, despues=3, alineacion=None, interlineado=None, primero=False,
       mayusculas=False, espaciado=None):
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
        r = p.add_run(texto.upper() if mayusculas else texto)
        r.font.size = Pt(tam)
        r.font.bold = negrita
        r.font.color.rgb = color
        if fuente:
            r.font.name = fuente
        if espaciado:
            _espaciado(r, espaciado)
    return p


def _rotulo(contenedor, texto, primero=False, color=None, tam=7.5,
            alineacion=None, despues=2):
    """Versalitas espaciadas: los rótulos de campo y las notas de sección."""
    p = _p(contenedor, "", despues=despues, primero=primero, alineacion=alineacion)
    r = p.add_run(texto.upper())
    r.font.size = Pt(tam)
    r.font.bold = True
    r.font.color.rgb = color or GRIS
    _espaciado(r, 30)
    return p


# ─────────────── Cabecera ───────────────
def _cabecera(doc, acta, proveedor, tipo_servicio):
    """Titular a la izquierda y emisor a la derecha.

    El bloque de la derecha lo ocupa QUIÉN emite el documento, no un lema: el
    acta se le entrega al proveedor y lo que importa ahí es de quién viene.
    """
    t = doc.add_table(rows=1, cols=2)
    _sin_bordes_tabla(t)
    _ancho_fijo(t, [Cm(12.6), Cm(5.3)])
    izq, der = t.rows[0].cells

    p = _p(izq, "", despues=0, primero=True)
    r = p.add_run("ACTA EJECUTIVA")
    r.font.size = Pt(27)
    r.font.bold = True
    r.font.name = SERIF
    r.font.color.rgb = NAVY
    _espaciado(r, 4)

    # El título que redacta la IA casi siempre termina en el nombre del proveedor
    # ("Seguimiento y Estrategia Comercial – Alwaysmart"). Añadirlo otra vez daba
    # "… – Alwaysmart · Alwaysmart" y partía el subtítulo en dos líneas.
    titulo = (acta.get("titulo") or f"Reunión con {proveedor}").strip()
    prov = (proveedor or "").strip()
    subtitulo = titulo if prov and prov.lower() in titulo.lower() else f"{titulo} · {prov}"

    p2 = _p(izq, "", despues=1, antes=2)
    r2 = p2.add_run(subtitulo)
    r2.font.size = Pt(11)
    r2.font.bold = True
    r2.font.name = SERIF
    r2.font.color.rgb = NAVY

    _p(izq, f"Servicio: {tipo_servicio}", tam=9, color=GRIS, despues=0)

    # Emisor, alineado a la derecha y en versalitas: acompaña al titular sin
    # competir con él.
    _rotulo(der, "Abelardo Yepes S.A.S.", primero=True, color=NAVY, tam=8,
            alineacion=WD_ALIGN_PARAGRAPH.RIGHT, despues=1)
    _rotulo(der, "Gerencia de Proveedores", color=GRIS, tam=7.5,
            alineacion=WD_ALIGN_PARAGRAPH.RIGHT, despues=0)

    # Filete grueso bajo la cabecera: separa el titular del contenido.
    p3 = _p(doc, "", despues=0, antes=6)
    _regla(p3, color=NAVY_HEX, grosor=12)
    return t


def _banda_datos(doc, acta, tipo_servicio):
    """Fecha, participantes y servicio en tres columnas separadas por filete."""
    participantes = [p for p in (acta.get("participantes") or []) if str(p).strip()]
    campos = [
        ("Fecha", fecha_larga(acta.get("fecha", ""))),
        ("Participantes", "; ".join(participantes) if participantes else "No registrados"),
        ("Servicio", tipo_servicio or "Sin clasificar"),
    ]

    t = doc.add_table(rows=1, cols=3)
    _sin_bordes_tabla(t)
    anchos = [Cm(4.6), Cm(8.7), Cm(4.6)]
    _ancho_fijo(t, anchos)

    for i, (celda, (etiqueta, valor)) in enumerate(zip(t.rows[0].cells, campos)):
        celda.width = anchos[i]
        _sombrear(celda, TINTA_BANDA)
        # Solo filete a la izquierda entre columnas: separa sin encajonar.
        _bordes_celda(celda, color=LINEA, grosor=6,
                      lados=("top", "bottom") + (("left",) if i else ()) +
                            (("right",) if i == 2 else ()))
        _margenes_celda(celda, 120, 150, 120, 150)
        _rotulo(celda, etiqueta, primero=True, despues=2)
        _p(celda, str(valor), tam=9, despues=0, interlineado=1.12)
    return t


def _objetivo(doc, texto):
    """El resumen de la reunión, destacado como objetivo del acta."""
    t = doc.add_table(rows=1, cols=1)
    _sin_bordes_tabla(t)
    _ancho_fijo(t, [Cm(17.9)])
    _fila_no_se_parte(t.rows[0])
    celda = t.rows[0].cells[0]
    _sombrear(celda, TINTA_SUAVE)
    _bordes_celda(celda, color="C9DCD2")
    _margenes_celda(celda, 150, 180, 150, 180)

    p = _p(celda, "", despues=3, primero=True)
    r = p.add_run("OBJETIVO")
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.name = SERIF
    r.font.color.rgb = NAVY
    _espaciado(r, 20)

    _p(celda, texto, tam=9.5, despues=0, interlineado=1.2,
       alineacion=WD_ALIGN_PARAGRAPH.JUSTIFY)
    return t


def _titulo_seccion(doc, texto, nota="", antes=14):
    """Titular de sección: serif en mayúsculas, filete y, a la derecha, un dato
    real de la sección.

    En la maqueta de referencia ese hueco de la derecha lleva un lema comercial.
    Aquí lleva el conteo de lo que viene debajo: ocupa el mismo sitio y equilibra
    igual el filete, pero informa en vez de rellenar — que es lo que pide la voz
    del producto.
    """
    t = doc.add_table(rows=1, cols=2)
    _sin_bordes_tabla(t)
    _ancho_fijo(t, [Cm(11.0), Cm(6.9)])
    izq, der = t.rows[0].cells

    p = _p(izq, "", despues=0, primero=True, antes=antes)
    r = p.add_run(texto.upper())
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.name = SERIF
    r.font.color.rgb = NAVY
    _espaciado(r, 14)

    if nota:
        _rotulo(der, nota, primero=True, color=GRIS, tam=7.5,
                alineacion=WD_ALIGN_PARAGRAPH.RIGHT, despues=0)
        der.paragraphs[0].paragraph_format.space_before = Pt(antes + 6)

    p2 = _p(doc, "", despues=4, antes=1)
    _regla(p2, color=LINEA, grosor=8)
    return t

# ─────────────── Decisiones clave ───────────────
CIRCULOS = "❶❷❸❹❺❻❼❽❾❿"


def _numero(parrafo, n):
    """El número dentro de un círculo relleno.

    Se usa el carácter Unicode y no una forma dibujada: Word no sabe hacer un
    círculo en una celda de tabla sin meterse en XML de autoformas, y estos
    glifos existen en las fuentes de símbolos de Windows y de Mac. Pasado el 10
    se cae a "11." sin círculo, que es feo pero legible — y un acta con once
    temas ya tiene otro problema.
    """
    r = parrafo.add_run(CIRCULOS[n - 1] if 1 <= n <= 10 else f"{n}.")
    r.font.size = Pt(12.5)
    r.font.color.rgb = NAVY
    r2 = parrafo.add_run(" ")
    r2.font.size = Pt(12.5)
    return r


def _tarjeta_decision(celda, numero, tema, ancho):
    """Una decisión: número y título, lo que se habló, y la conclusión en su
    propio recuadro teñido."""
    _sombrear(celda, "FFFFFF")
    _bordes_celda(celda, color=LINEA)
    _margenes_celda(celda, 140, 150, 130, 150)

    # Sangría francesa: si el título se parte, la segunda línea alinea con el
    # texto y no debajo del círculo, que dejaba el número flotando solo.
    p = _p(celda, "", despues=4, primero=True, interlineado=1.0)
    p.paragraph_format.left_indent = Cm(0.62)
    p.paragraph_format.first_line_indent = Cm(-0.62)
    _numero(p, numero)
    rt = p.add_run((tema.get("titulo") or "").strip())
    rt.font.size = Pt(10.5)
    rt.font.bold = True
    rt.font.name = SERIF
    rt.font.color.rgb = NAVY

    discusion = (tema.get("discusion") or "").strip()
    if discusion:
        _p(celda, discusion, tam=8.5, despues=5, color=NEGRO,
           alineacion=WD_ALIGN_PARAGRAPH.JUSTIFY, interlineado=1.16)

    conclusion = (tema.get("conclusion") or "").strip()
    if conclusion:
        # La conclusión va en su propio recuadro: es lo que el gerente busca
        # cuando relee el acta, y como párrafo suelto se perdía dentro del
        # cuerpo del tema.
        interna = celda.add_table(rows=1, cols=1)
        _sin_bordes_tabla(interna)
        _ancho_fijo(interna, [ancho - Cm(0.55)])
        c2 = interna.rows[0].cells[0]
        _sombrear(c2, TINTA_SUAVE)
        _bordes_celda(c2, color="D5E4DC")
        _margenes_celda(c2, 100, 120, 100, 120)

        p2 = _p(c2, "", despues=0, primero=True, interlineado=1.14)
        r1 = p2.add_run("Conclusión:  ")
        r1.font.size = Pt(8.5)
        r1.font.bold = True
        r1.font.color.rgb = VERDE
        r2 = p2.add_run(conclusion)
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = NEGRO



def _rejilla_decisiones(doc, temas):
    """Las decisiones en una rejilla de FILAS emparejadas.

    Cada fila lleva dos tarjetas y, como las celdas de una fila de tabla miden
    todas lo mismo, las dos empiezan y terminan a la misma altura. Es lo que da
    la simetría de la maqueta.

    La versión anterior usaba dos columnas continuas, cada una fluyendo por su
    cuenta como una columna de periódico. Ganaba unos milímetros de papel —una
    columna corta se rellenaba con la tarjeta siguiente en vez de esperar— pero
    ninguna tarjeta alineaba con la de al lado y el bloque entero se veía
    desordenado. Entre aprovechar el hueco y que se lea ordenado, manda lo
    segundo: el acta se le entrega al proveedor.

    Si el número de temas es impar, el último ocupa las dos columnas, igual que
    en la referencia. Así ninguna fila queda con media tarjeta y un vacío.
    """
    ancho_col = Cm(8.6)
    ancho_lleno = Cm(17.9)

    # Parejas, y el impar final a lo ancho.
    parejas = [temas[i:i + 2] for i in range(0, len(temas), 2)]

    t = doc.add_table(rows=0, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    _sin_bordes_tabla(t)
    _ancho_fijo(t, [ancho_col, ancho_col])
    _separacion_celdas(t, 90)     # gotera entre tarjetas, horizontal y vertical

    numero = 1
    for pareja in parejas:
        fila = t.add_row()
        # La fila no se parte: una tarjeta cortada por la mitad entre dos páginas
        # es peor que un poco de blanco al pie.
        _fila_no_se_parte(fila)

        if len(pareja) == 1:
            celda = fila.cells[0].merge(fila.cells[1])
            celda.width = ancho_lleno
            _tarjeta_decision(celda, numero, pareja[0], ancho_lleno)
            numero += 1
            continue

        for celda, tema in zip(fila.cells, pareja):
            celda.width = ancho_col
            _tarjeta_decision(celda, numero, tema, ancho_col)
            numero += 1
    return t


# ─────────────── Compromisos ───────────────
ORDEN_PRIORIDAD = {"alta": 0, "media": 1, "baja": 2}
ROTULO_PRIORIDAD = {"alta": "Alta prioridad", "media": "Prioridad media",
                    "baja": "Prioridad baja"}


def _cabecera_prioridad(doc, prioridad, responsables):
    """Barra navy que abre cada grupo de compromisos."""
    t = doc.add_table(rows=1, cols=1)
    _sin_bordes_tabla(t)
    _ancho_fijo(t, [Cm(17.9)])
    celda = t.rows[0].cells[0]
    _sombrear(celda, NAVY_HEX)
    _margenes_celda(celda, 90, 150, 90, 150)

    # La barra se queda con su primera fila: sola al pie de una página anuncia
    # un grupo que empieza en la siguiente.
    _fila_no_se_parte(t.rows[0])
    p = _p(celda, "", despues=0, primero=True)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(ROTULO_PRIORIDAD.get(prioridad, "Compromisos").upper())
    r.font.size = Pt(9)
    r.font.bold = True
    r.font.color.rgb = BLANCO
    _espaciado(r, 30)

    # Un solo responsable para todo el grupo se dice una vez en la barra; si son
    # varios, cada compromiso lleva el suyo y la barra no promete nada.
    if len(responsables) == 1:
        r2 = p.add_run(f"   ·   RESPONSABLE: {list(responsables)[0].upper()}")
        r2.font.size = Pt(9)
        r2.font.bold = True
        r2.font.color.rgb = RGBColor(0xC3, 0xD2, 0xE0)
        _espaciado(r2, 30)
    return t


def _grupo_compromisos(doc, compromisos, uno_solo):
    """Compromisos agrupados por plazo: la fecha a la izquierda y sus tareas
    como viñetas a la derecha."""
    por_fecha = {}
    for c in compromisos:
        por_fecha.setdefault(c.get("fecha_limite") or "", []).append(c)
    # Los que tienen plazo primero y en orden; los que no, al final.
    claves = sorted([k for k in por_fecha if k]) + ([""] if "" in por_fecha else [])

    anchos = [Cm(4.4), Cm(13.5)]
    t = doc.add_table(rows=0, cols=2)
    _sin_bordes_tabla(t)
    _ancho_fijo(t, anchos)

    for clave in claves:
        fila = t.add_row()
        _fila_no_se_parte(fila)
        cf, ct = fila.cells
        cf.width, ct.width = anchos

        for celda in (cf, ct):
            _bordes_celda(celda, color=LINEA_SUAVE, grosor=6, lados=("bottom",))
            _margenes_celda(celda, 110, 150, 110, 150)

        p = _p(cf, "", despues=0, primero=True)
        r = p.add_run(fecha_corta(clave) if clave else "SIN PLAZO DEFINIDO")
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.color.rgb = NAVY if clave else GRIS
        _espaciado(r, 20)

        for i, c in enumerate(por_fecha[clave]):
            p2 = _p(ct, "", despues=0 if i == len(por_fecha[clave]) - 1 else 3,
                    primero=(i == 0), interlineado=1.12)
            rb = p2.add_run("•   ")
            rb.font.size = Pt(9)
            rb.font.color.rgb = VERDE
            rt = p2.add_run(c.get("tarea", "").strip())
            rt.font.size = Pt(9)
            rt.font.color.rgb = NEGRO
            # El responsable solo se repite aquí cuando la barra no lo dijo.
            resp = (c.get("responsable") or "").strip()
            if resp and not uno_solo:
                rr = p2.add_run(f"   — {resp}")
                rr.font.size = Pt(8.5)
                rr.font.color.rgb = GRIS
    return t


def _compromisos(doc, compromisos):
    """Un bloque por prioridad, de la más alta a la más baja."""
    grupos = {}
    for c in compromisos:
        pr = (c.get("prioridad") or "media").lower()
        grupos.setdefault(pr if pr in ORDEN_PRIORIDAD else "media", []).append(c)

    for prioridad in sorted(grupos, key=lambda k: ORDEN_PRIORIDAD[k]):
        lote = grupos[prioridad]
        responsables = {(c.get("responsable") or "").strip()
                        for c in lote if (c.get("responsable") or "").strip()}
        _cabecera_prioridad(doc, prioridad, responsables)
        _grupo_compromisos(doc, lote, uno_solo=(len(responsables) == 1))
        _p(doc, "", tam=5, despues=0)


def _proximo_hito(doc, texto):
    t = doc.add_table(rows=1, cols=1)
    _sin_bordes_tabla(t)
    _ancho_fijo(t, [Cm(17.9)])
    _fila_no_se_parte(t.rows[0])
    celda = t.rows[0].cells[0]
    _sombrear(celda, TINTA_SUAVE)
    _bordes_celda(celda, color="C9DCD2")
    _margenes_celda(celda, 140, 180, 140, 180)

    p = _p(celda, "", despues=2, primero=True)
    r = p.add_run("PRÓXIMO HITO")
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.name = SERIF
    r.font.color.rgb = NAVY
    _espaciado(r, 20)

    _p(celda, texto, tam=10, despues=0, color=NEGRO)
    return t

def _apretar_cola(doc):
    """Encoge los párrafos vacíos del final.

    Word exige que el cuerpo termine en un párrafo cuando lo anterior es una
    tabla, así que no se puede borrar. Pero a tamaño normal ese párrafo mide lo
    suficiente para desbordar por unos puntos y llevarse una hoja entera: el
    acta salía en tres páginas y la tercera venía en blanco. A 1pt y sin
    interlineado ocupa lo justo para ser válida y no empujar nada.
    """
    for p in reversed(doc.paragraphs):
        if p.text.strip():
            break
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1
        for r in p.runs:
            r.font.size = Pt(1)
        if not p.runs:
            r = p.add_run("")
            r.font.size = Pt(1)


def _pie_de_pagina(doc):
    """La firma del documento va en el PIE de la página, no al final del cuerpo.

    Como párrafo suelto se llevaba una hoja entera para sí sola cuando el
    contenido terminaba cerca del borde: el acta de siete temas salía en tres
    páginas y la tercera tenía 127 caracteres. En el pie aparece en todas las
    páginas y no empuja nada.
    """
    for s in doc.sections:
        pie = s.footer
        p = pie.paragraphs[0] if pie.paragraphs else pie.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        _regla(p, color=LINEA, grosor=6, espacio=6)
        r = p.add_run("Documento generado a partir de la transcripción de la reunión "
                      "y revisado por la Gerencia de Proveedores — Abelardo Yepes S.A.S.")
        r.font.size = Pt(7.5)
        r.font.color.rgb = GRIS
        r.font.name = SANS


# ─────────────── Documento ───────────────
def build(acta, proveedor, tipo_servicio, destino):
    """Escribe el .docx. `acta` es el JSON ya revisado por el gerente.

    `destino` puede ser una ruta o un objeto en memoria (BytesIO)."""
    doc = Document()

    for s in doc.sections:
        s.top_margin = s.bottom_margin = Cm(1.5)
        s.left_margin = s.right_margin = Cm(1.5)

    estilo = doc.styles["Normal"]
    estilo.font.name = SANS
    estilo.font.size = Pt(9.5)
    estilo.font.color.rgb = NEGRO

    _pie_de_pagina(doc)

    _cabecera(doc, acta, proveedor, tipo_servicio)
    _p(doc, "", tam=5, despues=0)
    _banda_datos(doc, acta, tipo_servicio)

    resumen = (acta.get("resumen") or "").strip()
    if resumen:
        _p(doc, "", tam=6, despues=0)
        _objetivo(doc, resumen)

    temas = [t for t in (acta.get("temas") or []) if (t.get("titulo") or "").strip()]
    if temas:
        _titulo_seccion(doc, "Decisiones clave",
                        f"{len(temas)} {'tema tratado' if len(temas) == 1 else 'temas tratados'}")
        _rejilla_decisiones(doc, temas)

    compromisos = [c for c in (acta.get("compromisos") or [])
                   if (c.get("tarea") or "").strip()]
    con_plazo = sum(1 for c in compromisos if c.get("fecha_limite"))
    _titulo_seccion(
        doc, "Compromisos",
        f"{con_plazo} de {len(compromisos)} con plazo" if compromisos else "ninguno")
    if compromisos:
        _compromisos(doc, compromisos)
    else:
        _p(doc, "La reunión no dejó compromisos pendientes.", tam=9, color=GRIS)

    proxima = (acta.get("proxima_reunion") or "").strip()
    if proxima:
        _p(doc, "", tam=6, despues=0)
        _proximo_hito(doc, proxima)

    _apretar_cola(doc)
    doc.save(destino)
    return destino
