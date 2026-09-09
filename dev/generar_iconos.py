#!/usr/bin/env python3
"""Genera los iconos de la app desde su definición vectorial.

Los PNG del repositorio NO se editan a mano: salen de aquí. Así el día que
cambie el color de marca se regeneran todos en un comando y no quedan tamaños
sueltos con la paleta vieja.

    python3 dev/generar_iconos.py

UN SOLO DIBUJO. La versión anterior necesitaba dos —la composición completa de
portapapeles, persona y caja para tamaños grandes, y un portapapeles suelto para
16px— porque la completa se empastaba al reducirla. Este dibujo son cuatro
trazos: tres renglones y un visado. Aguanta 16px sin simplificar nada, así que
la marca del teléfono, la del favicon y la de la cabecera son el MISMO archivo y
no se pueden desincronizar.

Es también el glifo de la maqueta que se aprobó: un acta con sus puntos y el
visado de que se cumplieron, que es literalmente lo que hace la aplicación.

DOS TINTAS, SEGÚN EL FONDO:

    · Sobre el cuadro navy (icono de app, favicon): trazos blancos, visado
      Jordy.
    · Plana, sin cuadro (cabecera): todo en navy, porque allí el cuadro ya es
      Jordy y el blanco encima daría 1,9:1.
"""
import os
import fitz

AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(AQUI, "..", "app", "static")

# Los mismos tokens que `app/static/estilo.css`. Si cambia la paleta de la app,
# se cambian aquí y se vuelve a ejecutar este archivo: los PNG se regeneran
# todos a la vez y no queda ningún tamaño con el color viejo.
#
# Paleta del Sistema de Diseño Transferible, la misma que `app/static/estilo.css`.
NAVY   = "#1F3554"   # --color-navy-900
JORDY  = "#8DB9E4"   # --color-jordy, el acento de interacción
BLANCO = "#FFFFFF"


# Grosor de los renglones y del visado, en unidades del dibujo (0..320).
GROSOR_RENGLON = 26
GROSOR_VISADO  = 30


def dibujo(tinta, acento):
    """Tres renglones y un visado, en coordenadas 0..320.

    Centrado a mano: contando el grosor, el conjunto va de x=27 a x=293 y de
    y=73 a y=247, así que su centro cae en (160, 160). Sin ese ajuste la masa se
    iba arriba-izquierda y quedaba descuadrado dentro del cuadro redondeado.

    Los renglones terminan en x=134 y el visado arranca en x=180: esos 46 de
    aire impiden que se toquen y se lean como una sola mancha.

    LOS RENGLONES SON RECTÁNGULOS CON `rx`, NO TRAZOS CON `stroke-linecap`. El
    conversor de PyMuPDF que rasteriza los PNG ignora el `linecap` en tramos
    horizontales —da igual escribirlos con `H` o con `L`—, así que el SVG salía
    con puntas redondas y el PNG con puntas cuadradas: la marca del navegador
    distinta de la del teléfono. Un rectángulo redondeado no depende de que el
    rasterizador entienda el atributo. El visado sí va como trazo, porque ahí
    los `linecap` y `linejoin` sí se respetan al no ser horizontal.
    """
    p = []
    g = GROSOR_RENGLON
    for y, x2 in ((86, 134), (160, 134), (234, 102)):
        p.append(f'<rect x="{40 - g/2:.0f}" y="{y - g/2:.0f}" '
                 f'width="{x2 - 40 + g:.0f}" height="{g}" rx="{g/2:.0f}" fill="{tinta}"/>')
    p.append(f'<path d="M180 161 l34 36 l64 -74" fill="none" stroke="{acento}" '
             f'stroke-width="{GROSOR_VISADO}" stroke-linecap="round" '
             f'stroke-linejoin="round"/>')
    return "\n  ".join(p)


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

    sobre_navy = dibujo(BLANCO, JORDY)
    # Plana: todo navy. La cabecera la pone dentro de un cuadro Jordy, donde el
    # blanco daría 1,9:1 y el navy da 5,6:1.
    plana = dibujo(NAVY, NAVY)

    # Fuentes vectoriales
    with open(ruta("icono.svg"), "w") as f:
        f.write(svg(sobre_navy, 512, 0.76, 0.225))
    with open(ruta("marca.svg"), "w") as f:
        f.write(svg(sobre_navy, 512, 0.80, 0.225))
    # Sin cuadro, para la cabecera: el cuadro Jordy ya lo pone el CSS.
    with open(ruta("marca-plana.svg"), "w") as f:
        f.write(svg(plana, 512, 0.90, 0, fondo=False))
    # Enmascarable: más pequeño, porque Android recorta hasta el 80% central.
    with open(ruta("icono-maskable.svg"), "w") as f:
        f.write(svg(sobre_navy, 512, 0.60, 0.5))

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
