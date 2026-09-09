# Diseño

> **ACTUALIZACIÓN — septiembre de 2026.** El front ya no sigue esta guía en
> paleta ni en estados. Lo sustituye el **Sistema de Diseño Transferible**
> (navy `#1F3554`, azul Jordy `#8DB9E4`, superficies de vidrio sobre fondo
> ambiental), cuya implementación completa y comentada vive en
> `app/static/estilo.css`.
>
> Lo que cambió respecto a lo que dice este documento más abajo:
>
> - **No hay rojo, ámbar ni verde.** Una sola tonalidad. Lo que exige atención
>   no cambia de matiz sino de PESO: un compromiso vencido lleva relleno navy y
>   uno cerrado se aclara hasta retroceder.
> - **Cuatro tratamientos de estado, no cinco tintes.** «Cumplida» y
>   «Cancelada» comparten estilo a propósito: operativamente ninguna pide nada.
> - **El color no comunica solo.** Esto se refuerza, no se relaja: como el matiz
>   ya no distingue estados, el texto de la etiqueta es obligatorio siempre.
>
> Lo demás de esta guía sigue vigente: densidad, tamaños de tabla, mínimos de
> contraste, objetivos táctiles de 40 px y comportamiento de navegación.

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

### El tablero es un centro de control

No es una página de cifras: es donde el gerente comprueba si tiene el control.
La cabecera son **tres paneles del mismo ancho**, y cada uno responde una
pregunta distinta con su propio gráfico:

| Panel | Pregunta | Gráfico |
|---|---|---|
| Cumplimiento | ¿Cómo va la operación? | proporción de toda la cartera |
| Riesgo por servicio | ¿Dónde está el problema? | barras de lo vencido por servicio |
| Ritmo de seguimiento | ¿Se está haciendo seguimiento? | evolución mensual de reuniones |

Sustituyen a una tira de cuatro cifras que decía lo mismo cuatro veces: un
número grande sin nada que lo situara. Además usaba `flex: 1 1 160px`, así que
cada caja medía distinto según su texto — la asimetría estaba construida.

**El riesgo se agrupa por SERVICIO, no por proveedor.** Un servicio con varios
proveedores fallando es un problema estructural; uno solo fallando es un
problema de ese contrato. La diferencia cambia lo que el gerente hace después.

### Listas: cinco o seis filas y el resto se desliza

Las tablas del tablero llevan `.tabla-alta` (336px). Con 17 proveedores, una
tabla completa empuja todo lo demás fuera de la pantalla y el centro de control
deja de leerse de un vistazo.

**La página de Compromisos NO lleva ese tope**: allí la lista es el contenido de
la página, se entra a trabajarla entera, y un scroll dentro de otro scroll sería
peor que el scroll de página.

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
- **Se retiró el reparto por estado.** Era la misma información que la barra de
  proporción del panel de cumplimiento, en una sección aparte al final. Y el
  reparto por categoría se sustituyó por *Concentración por servicio*, que lleva
  el riesgo dentro de la misma barra: un servicio ancho y limpio es
  concentración sana, uno ancho y rojo es un problema estructural.

### La animación entra desde arriba, no desde abajo

`translateY(6px)` hacía nacer la fila 6px por debajo de su sitio, y un
contenedor con `overflow` cuenta ese desbordamiento inferior como área
desplazable **de forma permanente**, aunque la transformación ya haya terminado.
Una tabla de tres filas que cabía entera mostraba barra de scroll para 6px de
nada. El desbordamiento hacia arriba no crea scroll, así que la misma animación
desde `-6px` no deja rastro.

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

## El acta en Word

Maqueta de **acta ejecutiva**, pedida por la Gerencia de Proveedores:

```
ACTA EJECUTIVA        ← titular serif a todo lo ancho
banda de datos        ← fecha · participantes · servicio
OBJETIVO              ← recuadro teñido
DECISIONES CLAVE      ← tarjetas numeradas a dos columnas,
                        cada una con su conclusión destacada
COMPROMISOS           ← agrupados por prioridad y plazo, cabecera navy
PRÓXIMO HITO
```

**Dos tipografías con papeles distintos**: Georgia para los titulares —es lo que
le da aire de documento ejecutivo y no de informe de sistema— y Calibri para el
cuerpo. Ambas están en Windows y en Mac sin instalar nada: el acta se abre en el
computador del proveedor.

**El mismo azul oscuro del tablero.** El acta y la aplicación son el mismo
producto y el proveedor ve las dos. El verde solo aparece en las conclusiones:
lo que se acordó, no lo que se reclama.

Decisiones que hubo que tomar contra los límites de Word:

- **Los números van en círculo con el carácter Unicode `❶`**, no con una forma
  dibujada: Word no hace un círculo dentro de una celda de tabla sin XML de
  autoformas, y esos glifos existen en las fuentes de símbolos de Windows y Mac.
  Pasado el diez se cae a "11." sin círculo.
- **Sangría francesa en el título de cada tarjeta.** Sin ella, un título que se
  parte dejaba la segunda línea debajo del círculo y el número flotando solo.
- **Las decisiones van en filas emparejadas, no en columnas continuas.** Las
  celdas de una fila de tabla miden todas lo mismo, así que las dos tarjetas de
  una fila empiezan y terminan a la misma altura: eso es lo que da la simetría.
  La versión anterior fluía cada columna por su cuenta, como una columna de
  periódico: ganaba unos milímetros de papel —una columna corta se rellenaba con
  la tarjeta siguiente en vez de esperar— pero ninguna tarjeta alineaba con la
  de al lado y el bloque se veía desordenado. Entre aprovechar el hueco y que se
  lea ordenado manda lo segundo: el acta se le entrega al proveedor.
- **Si los temas son impares, el último ocupa las dos columnas**, igual que en la
  referencia. Así ninguna fila queda con media tarjeta y un vacío al lado.
- **El pie va en el PIE de página, no al final del cuerpo.** Como párrafo suelto
  se llevaba una hoja entera para sí solo cuando el contenido terminaba cerca del
  borde: el acta de siete temas salía en tres páginas y la tercera tenía 127
  caracteres.
- **La cola del documento se aprieta a 1pt.** Word exige que el cuerpo termine en
  un párrafo cuando lo anterior es una tabla, así que no se puede borrar; a
  tamaño normal desbordaba por unos puntos y se llevaba otra página.
- **Objetivo, hito y barra de prioridad llevan `cantSplit`**: sin eso, la caja
  del próximo hito se partía y dejaba el título en una página y la fecha en la
  siguiente.

En la maqueta de referencia, el hueco a la derecha de cada titular de sección
lleva un lema comercial. Aquí lleva **el conteo de lo que viene debajo** —"7
temas tratados", "3 de 7 con plazo"—: ocupa el mismo sitio y equilibra igual el
filete, pero informa en vez de rellenar, que es lo que pide la voz del producto.

## Logo e iconos

Los PNG **no se editan a mano**: salen de `dev/generar_iconos.py`, que los
dibuja en SVG y los rasteriza. El día que cambie la paleta se cambian cinco
constantes y se vuelve a ejecutar; así no queda ningún tamaño con el color
viejo.

### Dos dibujos, no uno

| Dónde | Dibujo | Por qué |
|---|---|---|
| Icono de app (192px+) | portapapeles + persona + caja | hay sitio para los tres |
| Favicon y barra (16-32px) | portapapeles con un visado | es lo único que sobrevive a 16px |

Medido rasterizando las variantes a 64, 32 y 16px: la composición completa se
empasta por debajo de 48 —los tres elementos se pisan y el icono deja de
leerse— y una lista de tres renglones tampoco aguanta. El visado solo, sí.

Comparten fondo navy, portapapeles blanco y visado azul, así que se leen como la
misma familia aunque no sean el mismo dibujo.

Los renglones del portapapeles van a 1,56:1 **a propósito**: representan líneas
de texto en un papel y deben verse tenues. Lo que porta el significado son los
visados, que están en 4,91:1 sobre el blanco.

### El icono enmascarable

Android recorta el icono en círculo, en gota o en cuadrado según el lanzador, y
se pierde todo lo que quede fuera del 80% central. Por eso
`icono-maskable-512.png` lleva el mismo dibujo al 56% del lienzo en vez del 74%.

### Lo que hace y no hace el service worker

Está para dos cosas: que la app se pueda instalar en el teléfono, y que sin
señal aparezca una nota escrita en vez del error del navegador.

**Nunca guarda en caché una página ni una respuesta de `/api/`.** El segundo
motivo es el que manda: la app va detrás de un inicio de sesión y hay perfiles
con permisos distintos; guardar el HTML de una sesión en el disco del
dispositivo significaría que la siguiente persona que abra la app en ese mismo
equipo podría ver los datos de la anterior. Eso no se arregla configurando bien
el caché, se evita no guardando nada.

Se sirve desde `/sw.js` y no desde `/static/`: un service worker solo controla
las rutas que cuelgan de su propia dirección.

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

- **Paginación y ordenamiento de tablas.** La guía los pide (punto 11). Con el
  volumen actual —decenas de reuniones al año— todavía no hacen falta.

Cerradas el 9 de septiembre de 2026: los skeletons de carga (el tablero dibuja
su forma —tres paneles y una lista— antes de tener los datos), el estado de los
filtros en la URL (se puede marcar y compartir una vista filtrada, y «atrás»
deshace el último filtro en vez de sacar del tablero) y el botón de reintentar
tras un fallo de carga.

Esta lista se revisa en cada crítica. La versión anterior omitía el encabezado
fijo de tabla, que la guía exige y que ya dolía con 17 filas.
