#!/usr/bin/env python3
"""Genera los iconos de la app desde su definición vectorial.

Los PNG del repositorio NO se editan a mano: salen de aquí. Así el día que
cambie el color de marca se regeneran todos en un comando y no quedan tamaños
sueltos con la paleta vieja.

    python3 dev/generar_iconos.py

DOS DIBUJOS, NO UNO. La composición completa —portapapeles, persona y caja— se
empasta por debajo de 48px: los tres elementos se pisan y el icono deja de
leerse. Medido rasterizando a 64, 32 y 16px.

    · Icono de aplicación (192px en adelante): composición completa.
    · Marca (favicon y barra superior, 16-32px): solo el portapapeles con un
      visado grande, que es la única variante que sobrevive a 16px.

Comparten fondo navy, portapapeles blanco y visado azul, así que se leen como
la misma familia aunque no sean el mismo dibujo.
"""
import os
import fitz

AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(AQUI, "..", "app", "static")

# Los mismos tokens que `app/static/estilo.css`. Si cambia la paleta de la app,
# se cambian aquí y se vuelve a ejecutar este archivo: los PNG se regeneran
# todos a la vez y no queda ningún tamaño con el color viejo.
#
# OJO: existe una rama `estilo/sistema-transferible`, sin fusionar, que mueve la
# app a navy #1F3554 con azul Jordy. Si esa rama entra, hay que cambiar estas
# cinco constantes y volver a ejecutar. El icono usa el navy que está EN
# PRODUCCIÓN hoy, no el de una rama que quizá no llegue.
NAVY        = "#102A43"   # --color-navy-900
ACENTO      = "#2F73B9"   # --color-blue-600, el azul de interacción
CLARO       = "#8FB4DC"   # figura sobre navy: legible sin competir con el acento
MUY_CLARO   = "#B9D2EA"   # renglones del portapapeles
BLANCO      = "#FFFFFF"


def _visto(cx, cy, r):
    a = r * 0.46
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{ACENTO}"/>'
            f'<path d="M{cx-a} {cy+a*0.06} l{a*0.72} {a*0.72} l{a*1.28} {-a*1.42}" '
            f'fill="none" stroke="{BLANCO}" stroke-width="{r*0.30:.1f}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def dibujo_completo():
    """Portapapeles, persona y caja, en coordenadas 0..320."""
    p = []
    # Persona, detrás. Los hombros arrancan por encima de la base de la cabeza:
    # si empiezan justo debajo queda una muesca de cuello y a tamaño pequeño se
    # ven dos manchas sueltas en vez de una persona.
    p.append(f'<circle cx="238" cy="78" r="34" fill="{CLARO}"/>')
    p.append(f'<path d="M186 196 C186 146 209 106 238 106 C267 106 290 146 290 196 '
             f'L290 210 L186 210 Z" fill="{CLARO}"/>')

    # Portapapeles, delante a la izquierda.
    p.append(f'<rect x="28" y="44" width="172" height="228" rx="19" fill="{BLANCO}"/>')
    p.append(f'<rect x="86" y="26" width="56" height="36" rx="14" fill="{BLANCO}"/>')
    p.append(f'<circle cx="114" cy="43" r="8" fill="{NAVY}"/>')
    for y, w in ((110, 80), (162, 80), (214, 54)):
        p.append(_visto(70, y, 19))
        p.append(f'<rect x="102" y="{y-7}" width="{w}" height="14" rx="7" fill="{MUY_CLARO}"/>')

    # Caja en tres cuartos. Las tres caras llevan blancos distintos para que el
    # volumen se lea sin contorno; la cinta sigue la inclinación de las aristas,
    # porque vertical se vería pegada encima en vez de envolviendo.
    p.append(f'<path d="M208 212 L266 184 L324 212 L266 240 Z" fill="{BLANCO}"/>')
    p.append(f'<path d="M208 212 L266 240 L266 300 L208 272 Z" fill="#E4F0FC"/>')
    p.append(f'<path d="M324 212 L266 240 L266 300 L324 272 Z" fill="#C6D8EE"/>')
    p.append(f'<path d="M237 198 L266 184 L295 198 L266 212 Z" fill="{ACENTO}"/>')
    p.append(f'<path d="M295 198 L266 212 L266 272 L295 258 Z" fill="{ACENTO}"/>')
    return "\n  ".join(p)


def dibujo_marca():
    """Portapapeles con un visado grande: la variante que aguanta 16px."""
    return "\n  ".join([
        f'<rect x="62" y="62" width="196" height="230" rx="26" fill="{BLANCO}"/>',
        f'<rect x="126" y="38" width="68" height="42" rx="17" fill="{BLANCO}"/>',
        f'<circle cx="160" cy="58" r="10" fill="{NAVY}"/>',
        f'<path d="M104 182 l38 40 l76 -84" fill="none" stroke="{ACENTO}" '
        f'stroke-width="30" stroke-linecap="round" stroke-linejoin="round"/>',
    ])


def svg(dibujo, lado=512, escala=0.74, radio=0.225, fondo=True):
    """`escala` es la fracción del lado que ocupa el dibujo.

    El icono enmascarable la baja a 0.56 y usa esquinas de círculo completo:
    Android recorta el icono en círculo, en gota o en cuadrado según el
    lanzador, y todo lo que quede fuera del 80% central se pierde.
    """
    tam = lado * escala
    off = (lado - tam) / 2
    k = tam / 320
    cuadro = (f'<rect width="{lado}" height="{lado}" rx="{lado*radio:.0f}" '
              f'fill="{NAVY}"/>') if fondo else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {lado} {lado}" '
            f'width="{lado}" height="{lado}">\n  {cuadro}\n'
            f'  <g transform="translate({off:.1f} {off:.1f}) scale({k:.4f})">\n'
            f'  {dibujo}\n  </g>\n</svg>')


def _png(ruta_svg, ruta_png, lado):
    doc = fitz.open(ruta_svg)
    pdf = fitz.open("pdf", doc.convert_to_pdf())
    pg = pdf[0]
    m = fitz.Matrix(lado / pg.rect.width, lado / pg.rect.height)
    pg.get_pixmap(matrix=m, alpha=False).save(ruta_png)


def main():
    def ruta(n):
        return os.path.normpath(os.path.join(DESTINO, n))

    # Fuentes vectoriales
    with open(ruta("icono.svg"), "w") as f:
        f.write(svg(dibujo_completo(), 512, 0.74, 0.225))
    with open(ruta("marca.svg"), "w") as f:
        f.write(svg(dibujo_marca(), 512, 0.78, 0.225))
    # La marca sin cuadro, para la barra superior: allí el fondo ya es navy y un
    # segundo cuadro navy sobre navy solo añadiría un borde raro.
    with open(ruta("marca-plana.svg"), "w") as f:
        f.write(svg(dibujo_marca(), 512, 0.94, 0, fondo=False))
    # Enmascarable: mismo dibujo, más pequeño y sin depender del radio.
    with open(ruta("icono-maskable.svg"), "w") as f:
        f.write(svg(dibujo_completo(), 512, 0.56, 0.5))

    for nombre, origen, lado in (
        ("icono-192.png",          "icono.svg",          192),
        ("icono-512.png",          "icono.svg",          512),
        ("icono-maskable-512.png", "icono-maskable.svg", 512),
        ("apple-touch-icon.png",   "icono.svg",          180),
        # Respaldo para navegadores que no aceptan favicon en SVG.
        ("favicon-32.png",         "marca.svg",           32),
        ("favicon-180.png",        "marca.svg",          180),
    ):
        _png(ruta(origen), ruta(nombre), lado)
        print(f"  {nombre}")

    print("\nSVG: icono.svg · marca.svg · marca-plana.svg · icono-maskable.svg")


if __name__ == "__main__":
    main()
