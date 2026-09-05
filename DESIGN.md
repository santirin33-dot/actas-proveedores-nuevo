# Diseño

El sistema visual de esta app **no es propio**: sigue la *Guía de diseño de
dashboard* de Abelardo Yepes, la misma que rige los demás tableros
administrativos de la casa. El objetivo declarado es que se sienta parte de la
misma familia de productos, no que tenga personalidad propia.

Este archivo recoge solo lo que la guía deja abierto y las decisiones que hubo
que tomar al aplicarla aquí. Para cualquier duda que no esté abajo, manda la
guía.

## Concepto

Dashboard ejecutivo sobrio, limpio y preciso. Herramienta de trabajo, no página
promocional: el gerente empieza a analizar desde el primer pantallazo, sin
héroes ni decoración.

El orden de lectura de cada página es fijo: encabezado, filtros globales,
indicadores, tabla. Los filtros mandan sobre todo lo que hay debajo.

## Color

Paleta de la guía, implementada como variables en `estilo.css`. Los nombres
`--color-*` son los de la guía; los nombres semánticos (`--ink`, `--marca`,
`--vencido`…) se conservan del sistema anterior **a propósito**: las plantillas
los usan en estilos en línea y renombrarlos obligaría a tocar los nueve archivos
a la vez.

| Rol | Token | Valor |
|---|---|---|
| Fondo general | `--ground` | gris 50 `#F7F9FC` |
| Superficies | `--surface` | blanco |
| Encabezado y navegación | — | azul oscuro `#102A43` |
| Interacción | `--marca` | azul medio `#2563A6` |
| Resultado favorable | `--hecho` | verde `#287A57` |

**Las cifras de los indicadores van siempre en azul oscuro**, como manda el
punto 9 de la guía. El rojo aparece solo cuando hay algo vencido, que es lo
único que exige una decisión inmediata. El verde se retiró de ahí: un "0
vencidos" pintado de verde es un semáforo gigante —la anti-referencia declarada
del producto— y premiaba visualmente un dato que ya se entiende leyendo la
cifra.

El verde **dejó de ser el color de marca** y pasó a significar "cumplido", como
manda la guía. El azul medio ocupa su lugar en enlaces, botones primarios y foco.

### Una desviación deliberada

El ámbar de la guía (`--color-warning: #B7791F`) sobre su propio fondo
(`#FFF7E6`) da **3,42:1**, por debajo del 4,5:1 que la propia guía exige en su
punto 19. Para texto se usa `#976217`, que llega a 4,83:1. El token original se
conserva intacto para usos que no sean texto.

Los pares de color del sistema están medidos y todos superan 4,5:1.

**Corrección:** una versión anterior de este archivo afirmaba lo mismo y era
falso. El enlace "Salir" daba **2,94:1** porque un estilo en línea en
`base.html` anulaba la regla correcta de `.usuario a` (9,49:1). La medición se
había hecho sobre los tokens, no sobre lo que el navegador terminaba aplicando.
Un par medido en la hoja de estilos no está medido si algo lo pisa después.

## Tipografía

`Inter, Manrope` primero, como pide la guía, con el tipo del sistema como
respaldo. **No se carga desde ningún CDN**: el proyecto no usa ninguno, así que
en equipos sin Inter instalado cae al tipo del sistema. Si algún día se quiere
la fuente exacta en todas partes, habría que alojar los archivos en `static/`.

Escala aplicada: página 28px, sección 20px, cuerpo 16px, tabla 15px,
encabezado de tabla 13px, metadatos 13px. **Nada funcional por debajo de 12px.**

## Tablas

Componente principal de análisis, no la letra pequeña del final.

- Cuerpo 15px, encabezado 13px semibold sobre gris 100.
- Fila de una línea ≈48px, dentro del rango 46-54 de la guía.
- Las filas que llevan una **segunda línea de dato real** (la fecha de la última
  reunión bajo el nombre del proveedor, el "en 3 días" bajo el plazo) miden más.
  Eso es contenido, no relleno, y no se comprime.
- Columnas de cifras fijadas a 92px con `.num`. Sin eso se llevaban casi 100px
  cada una y el nombre del proveedor se partía en dos líneas.
- `.pill-servicio` ajusta a dos renglones en vez de forzar una sola línea: con
  `nowrap` reclamaba ancho y estrangulaba la columna del proveedor.

## Gráficos

Dibujados a mano en SVG y CSS. El proyecto no usa CDN, y una barra horizontal es
una fila con un ancho en porcentaje: cargar 90 KB de librería para eso sería
pagar mucho por muy poco.

- **Un color por significado, no por serie.** Azul para el volumen, rojo solo
  para lo vencido. Si cada barra tuviera su color, el color dejaría de decir
  algo y sería adorno.
- **La leyenda solo aparece cuando una barra lleva más de un color**, que es
  cuando el color dice algo que el texto no dice.
- **La tercera columna de `.barra-fila` va fija, no `auto`.** Cada fila es su
  propia rejilla: con `auto`, la columna de la cifra se dimensionaba según el
  texto de esa fila y movía el arranque de la barra unos píxeles en cada una.
  Comparar longitudes deja de funcionar si no todas empiezan en la misma
  vertical.
- **Reuniones por mes rellena los meses vacíos.** Dibujando solo los meses con
  actividad, dos reuniones separadas por medio año saldrían pegadas y la línea
  mentiría sobre el ritmo.
- **Categorías en barras y no en dona**: la guía admite la dona con 2-5
  categorías y aquí pueden ser muchas más.
- **Barra de 6px, no de 10.** Con dieciséis proveedores en pantalla, una barra
  gruesa y saturada por fila es un muro de azul: el gráfico pesa más que el dato
  que transporta. Fina, sobre una pista casi imperceptible y con más aire entre
  filas, la comparación de longitudes se lee igual y la página respira.
- **Sin separadores entre filas.** Con las barras ya alineadas en la misma
  vertical, la línea solo añadía ruido horizontal.

## Acciones e iconos

Tres pesos, y el peso dice de qué tipo de acción se trata:

- **Principal** (`.btn-primario`): azul relleno. Una por pantalla.
- **Secundaria** (`.btn`): borde y texto, sin relleno.
- **Terciaria** (`.btn-icono`): solo el icono lineal, sin superficie hasta el
  hover. Corregir y borrar viven aquí.

Editar y borrar **no llevan palabra**. Con el texto al lado competían con
"Anotar avance", que sí es la acción principal de la tarjeta, y la fila
terminaba siendo cinco controles del mismo peso. El nombre accesible va en
`aria-label`, que es donde lo busca un lector de pantalla.

El área de pulsación sigue siendo de **40×40 px** aunque el icono mida 18: lo
que baja es el peso visual, nunca el objetivo de clic.

Los iconos se dibujan a mano en `base.html` (`ICONOS` + `icono()`): son dos
trazados, y una librería serían cientos de kB. Usan `currentColor` para heredar
el color del botón en cada estado sin declararlo dos veces.

## Qué mide "Cumplimiento"

**Solo los compromisos a los que ya les llegó la hora**: los cerrados, y los
abiertos cuyo plazo ya pasó. Uno abierto con plazo en noviembre no es un
incumplimiento en septiembre.

La primera versión dividía entre *todos* los compromisos normales. Un proveedor
con tres tareas en plazo y ninguna vencida aparecía con **0%**. Ese número se
lee delante del proveedor y no se podía sostener: contradecía a la vez el
principio 2 ("nunca se inventa una alarma") y el 3 ("presentable delante del
proveedor"). Al corregirlo, Aseo Total pasó de 33% a 100% — había cumplido todo
lo exigible.

La celda muestra además cuántos quedan **aún en plazo**, para que un 100% o un
guion no se lean como "no queda nada pendiente".

## Estados

Etiquetas sobrias, **siempre con texto**: el color nunca comunica solo. Vencido,
pendiente, en proceso, cumplido y cancelado, cada uno sobre su propio fondo
teñido.

El semáforo solo aparece si hay fecha límite puesta a mano. Sin plazo no se
inventa urgencia.

## Movimiento

Un solo momento: las filas entran escalonadas al cargar, 24ms de desfase y como
mucho doce filas. Después de 1200ms la animación se desactiva, para que no se
repita en cada cambio de filtro. `prefers-reduced-motion` la anula por completo.

## Desviaciones pendientes de la guía

- **Skeletons de carga.** La guía los pide (punto 17); la app todavía usa un
  spinner. La clase `.skeleton` ya existe en `estilo.css`, falta aplicarla en las
  plantillas.
- **Paginación y ordenamiento de tablas.** La guía los pide (punto 11). Con el
  volumen actual —decenas de reuniones al año— todavía no hacen falta.
- **Estado de los filtros en la URL.** No se puede marcar ni compartir una vista
  filtrada, y el botón *atrás* del navegador la pierde.
- **Reintentar tras un fallo de carga.** Hoy el error borra el cuerpo y deja una
  frase sin ningún control para volver a intentarlo.

Esta lista se revisa en cada crítica. La versión anterior omitía el encabezado
fijo de tabla, que la guía exige y que ya dolía con 17 filas.
