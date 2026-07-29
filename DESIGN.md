# Design

## Direction contract

**THESIS** — Un instrumento de gestión que se lee como un informe, no un tablero de SaaS.
Rechaza la rejilla de tarjetas iguales y el fondo oscuro con acento neón que heredó de
Control de Lecturas: la información se ordena con filetes y bandas, como un documento que
puede girarse hacia el proveedor sin que parezca una acusación.

**OWN-WORLD** — Papel casi blanco con un tinte verde imperceptible; verde profundo de
Abelardo Yepes como único color de marca, en menos del 10% de la superficie. Filetes
finos en vez de bordes de tarjeta. Cifras en tabulares. El color solo aparece donde
significa algo: el estado de un compromiso.

**STORY** — David abre y ve, en la primera línea, qué se está incumpliendo y con quién.
Baja a la tabla de proveedores ordenada por quién peor va. Entra a uno y lee su historia
reunión por reunión.

**FIRST VIEWPORT** — Barra superior con navegación. Debajo, la banda de estado a ancho
completo: si hay vencidos, los nombra y los lista ahí mismo; si no, una sola línea de
calma. Luego la tira de cifras separadas por filetes verticales, y de inmediato la tabla
de proveedores. Sin héroe, sin bienvenida.

**FORM** — Informe de gestión impreso, traducido a pantalla. Dirección fijada por el
usuario (claro y sobrio, acento verde de la marca, lo vencido primero), no por sorteo.

## Theme

Claro. La escena manda: David lo usa sentado en su computador de oficina, con luz natural
de ventana, y a veces gira la pantalla hacia el proveedor que tiene enfrente. Un fondo
oscuro con acento lima se lava con esa luz y se lee como producto de startup, no como
instrumento de una administradora.

## Color

Estrategia: **Restrained** — neutros tintados más un acento. Es el default correcto cuando
el usuario vino a operar, no a ser persuadido.

Todos los tokens en OKLCH. El tinte de los neutros va hacia el verde de la marca (hue 145),
nunca hacia el cálido por defecto: el fondo crema es el reflejo saturado de IA y este
proyecto lo evita explícitamente.

| Token | Valor | Uso |
|---|---|---|
| `--ground` | `oklch(.988 .003 145)` | fondo de página |
| `--surface` | `oklch(1 0 0)` | superficies elevadas, filas |
| `--sunken` | `oklch(.962 .006 145)` | campos, insets, encabezados de tabla |
| `--line` | `oklch(.905 .008 145)` | filete estándar |
| `--line-firm` | `oklch(.83 .012 145)` | filete de separación de sección |
| `--ink` | `oklch(.22 .02 150)` | texto principal (≈15:1) |
| `--ink-2` | `oklch(.42 .02 150)` | secundario (≈5.8:1) |
| `--ink-3` | `oklch(.46 .015 150)` | rótulos (≈4.7:1 también sobre `--sunken`) |
| `--marca` | `oklch(.42 .10 143)` | acento Abelardo Yepes (≈5.8:1) |
| `--marca-fuerte` | `oklch(.34 .09 143)` | hover del acento |
| `--marca-lavado` | `oklch(.955 .022 143)` | fondo teñido del acento |

Estados. El texto de estado se usa **sobre su propio fondo teñido**, no sobre blanco,
así que los valores están calculados contra ese fondo, que es el caso exigente: todos
quedan ≥4.6:1 ahí y muy por encima sobre blanco.

| Estado | Texto | Fondo |
|---|---|---|
| Vencido | `oklch(.45 .16 27)` | `oklch(.955 .028 27)` |
| En proceso | `oklch(.46 .12 72)` | `oklch(.958 .04 82)` |
| Pendiente | `oklch(.45 .12 255)` | `oklch(.955 .025 255)` |
| Completado | `oklch(.44 .11 152)` | `oklch(.955 .028 152)` |
| Cancelado | `oklch(.46 .01 145)` | `oklch(.955 .004 145)` |

Sobre una banda teñida (la de vencidos), los enlaces se tiñen de ese mismo tono. Un
verde de marca dentro de un bloque rojo compite y rompe la unidad del bloque.

**El color nunca comunica estado por sí solo.** Toda píldora lleva su texto. La pantalla
puede proyectarse en sala y el daltonismo y el proyector fallan igual.

## Typography

Stack de sistema, sin webfonts. Es una herramienta de operación, no una pieza de marca, y
la carga cero importa más que una voz tipográfica propia. La sensación de documento la dan
la estructura, los filetes y las cifras tabulares, no una serif editorial.

Escala (razón ≈1.25): 11 · 12 · 13.5 · 15 · 19 · 24 · 30.
Rótulos: 11px, `600`, `letter-spacing .04em`, mayúscula inicial. **No** versalitas rastreadas
sobre cada sección.

Cifras: `font-variant-numeric: tabular-nums` siempre. Alinean en columna y no bailan al
actualizarse.

Medida de lectura de prosa: máx. 68ch.

## Layout

- Ancho de contenido 1180px.
- **Bandas y filetes, no tarjetas.** La tarjeta se reserva para lo que de verdad es una
  unidad separable: un hito de la línea de tiempo, un bloque de edición del acta. Nunca
  tarjeta dentro de tarjeta.
- Secciones separadas por `--line-firm` con el título encima, no encajonadas.
- Las cifras van en una tira horizontal dividida por filetes verticales, no en una rejilla
  de tarjetas de métrica.
- Tablas con encabezado en `--sunken` y filas separadas por `--line`.

## Motion

Un momento de movimiento por pantalla, no efectos sueltos. Entrada escalonada de las filas
al cargar (24ms por fila, tope 12), con `cubic-bezier(.16,1,.3,1)`. El contenido está
visible por defecto: la animación lo acompaña, no lo condiciona.

`prefers-reduced-motion` colapsa todo a 0.

## Components

- **Banda de estado**: primera cosa de la página. Fondo teñido del estado que reporta,
  filete completo (nunca barra lateral de color), y la lista de lo vencido dentro.
- **Tira de cifras**: `display:flex`, divisores con `border-left`, cifra en 30px tabular
  sobre rótulo de 11px.
- **Píldora de estado**: texto + fondo teñido, `border-radius` 4px. Nunca solo color.
- **Medidor en línea**: barra de 6px dentro de la celda de tabla, con el porcentaje en
  cifra al lado. Sustituye al gráfico de barras suelto.
- **Hito de línea de tiempo**: única tarjeta real del sistema, con marcador circular sobre
  el carril vertical.

## Accessibility

WCAG 2.1 AA. Anillo de foco `2px` en `--marca` con `2px` de separación, visible sobre todo
fondo. Objetivos de clic ≥40px. Estado siempre con texto.
