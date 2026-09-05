---
target: el tablero
total_score: 20
max_score: 40
na_heuristics: 
p0_count: 1
p1_count: 1
timestamp: 2026-09-05T18-48-02Z
slug: app-templates-dashboard-html
---
Method: dual-agent (A: a995c2fb7c040293e · B: af7cf6d26f4a0bd71)

## Puntuación de salud del diseño

| # | Heurística | Nota | Hallazgo clave |
|---|---|---|---|
| 1 | Visibilidad del estado | 2 | Un filtro activo es invisible; `th` es `position: static`, así que con 17 filas las cinco columnas de cifras se quedan sin rótulo |
| 2 | Sistema ↔ mundo real | 3 | Voz excelente ("26 días de atraso"), pero "Cumplimiento" nombra algo que la fórmula no calcula |
| 3 | Control y libertad | 2 | Los filtros no viven en la URL: no se puede marcar ni compartir una vista, y el *atrás* la pierde |
| 4 | Consistencia y estándares | 2 | El medidor no se dibuja; una sección miente en su vacío; otra ignora 2 de 5 filtros |
| 5 | Prevención de errores | 3 | "Sin plazo no hay urgencia" implementado hasta el fondo; elegir proveedor limpia el servicio |
| 6 | Reconocer antes que recordar | 2 | Nada dice que los 3 vencidos ya están dentro de los 13 abiertos |
| 7 | Flexibilidad y eficiencia | 1 | Sin ordenamiento, sin paginación, sin estado en URL; 17 tabulaciones hasta la primera fila |
| 8 | Estética y minimalismo | 2 | 7,17 pantallas a escala real, de las cuales 22% son gráficos que repiten la tabla de arriba |
| 9 | Recuperación de errores | 1 | El fallo de carga borra el cuerpo y deja una frase sin `role="alert"` y **sin botón de reintentar** |
| 10 | Ayuda y documentación | 2 | Nada en pantalla explica "Cumplimiento", "ANS" ni "Permanente" — justo lo que el proveedor pregunta |
| **Total** | | **20/40** | Banda baja, con fundamentos buenos |

## Veredicto de especificidad

**Parcialmente anclado, y la mitad genérica ocupa más pantalla que la específica.**

Cuatro de siete secciones son de este producto. Tres son mobiliario intercambiable.

El hallazgo grave: PRODUCT.md declara como principio 5 *"Continuidad sobre eventos... el diseño debe hacer visible esa cadena"*. En `dashboard.html` hay **cero apariciones** de `seguimiento`, `anterior`, `avance` u `origen`. El arreglo `D.seguimiento` llega en cada carga y esta pantalla no lo lee nunca. La tesis del producto no está en su pantalla de entrada.

## Detector determinista

`dashboard.html` y `base.html`: **exit 0, cero hallazgos**. El destino sale limpio.

Dos hallazgos en otras plantillas: `flat-type-hierarchy` en `login.html:14` y `sin_acceso.html:12`.

Detector en navegador: 6 hallazgos a 1440px, 12 a 375px. **Tres familias son falsos positivos** verificados: `cramped-padding` sobre `.tabla-marco` (mide el contenedor sin mirar el padding de las celdas), `text-overflow` sobre `.barra-nombre` (`scrollWidth === clientWidth`, la elipsis funciona) y el detalle numérico de `flat-type-hierarchy` (imprime el rango total, no el paso más estrecho).

Los overlays se construyeron en el DOM pero **no hay superposición visible**: el panel del navegador está oculto.

## Verificación cruzada

B confirmó con medida exacta 7 de las 8 afirmaciones de A:

| Afirmación | Veredicto | Medida |
|---|---|---|
| El medidor de cumplimiento no se dibuja | **CONFIRMADA** | 4 de 4 `.medidor-relleno` miden **0×0 px**, `display: inline` |
| "Salir" falla contraste | **CONFIRMADA** | **2,94:1** — un estilo en línea anula la regla correcta, que daría 9,49:1 |
| Fechas a 42px en móvil | **CONFIRMADA** | 42,00px contra los 44 de selects y botones |
| Texto SVG bajo 12px | **CONFIRMADA, peor** | Eje a **5,02px** reales; valores a 5,43px |
| "Reuniones por mes" miente con filtro | **CONFIRMADA** | Dice "Todavía no hay reuniones" habiendo 7 |
| "Categorías" ignora filtros | **PARCIALMENTE REFUTADA** | Ignora fecha y tipo; **sí** respeta proveedor y servicio |
| Encabezados no fijos | **CONFIRMADA** | `position: static` en las 3 tablas |
| Enlaces duplicados | **CONFIRMADA con matiz** | Solo "Descargar Word" ×7 es fallo real: 7 nombres iguales, 7 destinos distintos |

## Impresión general

La disciplina de sistema es genuinamente buena —tokens coherentes, color medido, voz sin relleno— y encima de ella hay **un componente que no ha renderizado nunca** y **una fórmula que acusa a proveedores que no han incumplido**. La mayor oportunidad no es añadir: es que la pantalla de entrada responda la pregunta del producto en vez de hacer inventario.

## Lo que funciona

**La banda de vencidos.** Días de atraso como cifra tabular fija, luego el compromiso, luego el proveedor como enlace: es el orden exacto de la frase que David dice en voz alta al reclamar. Tope de 6 con enlace al resto, para que 26 vencidos no se conviertan en un muro.

**"Sin plazo no hay urgencia", implementado hasta el fondo.** `estaVencida()` exige fecha límite; las permanentes salen de vencidos, de abiertos y del cumplimiento; y "sin plazo" solo cuenta compromisos a los que *falta* fecha. Ninguna alarma roja de esta pantalla es inventada — que es la diferencia entre un tablero defendible frente al proveedor y uno que no.

**El color nunca comunica solo, y está medido.** Todas las etiquetas llevan palabra; la leyenda solo aparece cuando una barra tiene dos colores.

## Problemas prioritarios

**[P0] La barra de cumplimiento no se ha dibujado nunca, y el número que queda acusa en falso**

`.medidor-relleno` es un `<span>` sin `display:block`. Al ser `inline`, el ancho no aplica: **0×0 px en las cuatro filas**, con `width:33%` puesto. Todas las filas muestran una pista gris vacía.

Y `tasaCumplimiento()` divide entre *todos* los compromisos normales, incluidos los que aún no vencen. Ascensores: 5 compromisos, 0 completados, **3 todavía sin vencer** → la pantalla dice **"Cumplimiento 0%"**.

Es la columna que David señalaría, y dice algo que no puede sostener si el proveedor pregunta cuáles incumplió. Contradice el principio 2 y el 3 en la misma celda.

*Arreglo:* `display:block` en `.medidor-relleno`; denominador = compromisos cuyo plazo ya pasó o que están cerrados; `null` cuando no hay nada medible, para que la celda diga `—` y `3 aún sin vencer`.

**[P1] El tablero se degrada justo en la escena para la que existe: un solo proveedor**

Filtrando por un proveedor: tabla de 7 columnas con una fila; una barra sola con leyenda de dos colores; "1 proveedor en 1 categoría · 100%"; 380px de gráfico para dos puntos; y "Vencen en 15 días" desaparece sin nota. ~676px de gráfico que no dice nada, y la lista que David vino a buscar no está.

Es el minuto anterior a la reunión, el caso de uso número uno, y su camino real termina abandonando el tablero.

*Arreglo:* dar a "Categorías" y "Carga" el mismo guardián que "Reparto" ya tiene; subir el umbral de evolución a 4 reuniones; y con un proveedor filtrado, cambiar la tabla por sus compromisos abiertos con días de atraso.

**[P2] La cadena de compromisos no está en la pantalla de entrada**

El tablero mide *stock* cuando el producto existe para mostrar *flujo*. "Compromisos abiertos: 13" no responde "qué reclamo"; "este compromiso lleva tres reuniones abierto" sí.

*Arreglo:* reemplazar "Proveedores por categoría" (490px, la anti-referencia declarada) por "Compromisos arrastrados de reuniones anteriores", ordenados por cuántas reuniones llevan encima.

**[P3] A escala real son 7,17 pantallas y la tabla pierde sus encabezados**

6.452px con 17 proveedores. `th` es `static`, y la guía exige encabezado fijo en tablas largas — desviación que ni siquiera está en la lista de pendientes de DESIGN.md. "Vencen en 15 días" queda en la pantalla 4,6; "Carga de pendientes" duplica dos columnas de la tabla que está 1.700px más arriba.

*Arreglo:* `position: sticky; top: 60px` en `th`; eliminar "Carga de pendientes"; subir "Vencen en 15 días" junto a la banda.

**[P4] Un filtro activo es invisible, y el mensaje más tranquilizador es alcanzable por accidente**

Sin chips ni resumen; "Quitar filtros" se ve igual con y sin filtros. Con un rango de fechas vacío, la banda dice **"Todo al día en este filtro"** en verde de ancho completo — la misma frase que cuando de verdad no hay nada vencido.

*Arreglo:* chips de filtros activos con X; `.btn-primario` en "Quitar filtros" cuando hay alguno; rama `hayFiltro()` en evolución; aplicar fecha y tipo en categorías.

## Banderas rojas por persona

**David, 9:50 a.m., reunión a las 10:00.** La banda funciona en 3 segundos. Pero el filtro está *debajo* de la banda, así que al filtrar tiene que volver a subir para leer su propio resultado. La vista filtrada se degrada, y termina yéndose al perfil del proveedor: el tablero fue un desvío de 20 segundos.

**El proveedor, pantalla girada hacia él.** Lee un "13" y un "3" de 30px, luego un panel rojo con su empresa dos veces, luego una fila que termina en **"0%"** — cuando tres de esos cinco compromisos ni siquiera han vencido. David acaba defendiendo su herramienta en vez de sostener el reclamo.

**La gerente de solo consulta.** En teléfono, `.usuario { display:none }` borra su nombre, su rol **y el enlace de salir**. La navegación le ofrece "Generar acta", entra, y encuentra el botón deshabilitado sin ninguna frase que explique por qué. El perfil está anunciado pero no diseñado.

## Observaciones menores

- **Único fallo de contraste del sistema**, y DESIGN.md afirma que los 21 pares pasan: "Salir" da **2,94:1** por un estilo en línea que anula la regla correcta.
- Los campos de fecha se quedan en 42px en táctil porque `input` (0-0-1) pierde contra `input[type="date"]` (0-1-1): las media queries no suman especificidad.
- Texto de gráfico a **5px** en teléfono por la escala del `viewBox`.
- Cero `aria-live` o `role="alert"`: el cuerpo se reemplaza entero en cada filtro sin anunciar nada.
- Sin *skip link*: 42 paradas de foco, 85 elementos interactivos a escala real.
- La animación de entrada es una carrera con la red: se apaga a los 1.200 ms desde el parseo, y los datos vienen de una Hoja de Google.
- **Anomalía de arranque:** en la primera carga apareció "No se pudieron cargar los datos" pese a que `/api/datos` responde 200. Transitorio, pero real.

## Preguntas provocadoras

1. Si el éxito es "llegar sabiendo qué reclamar", ¿por qué esta pantalla no tiene **ninguna** acción principal y el camino real de David termina saliendo de ella?
2. "Cumplimiento" divide por compromisos que aún no vencen. ¿Le mostrarías ese número al proveedor? Si no, ¿por qué es una columna de la pantalla que giras hacia él?
3. Se quitó el verde del "0 vencidos" por ser un semáforo gigante. La banda de calma es el mismo verde con cinco veces el área. ¿Qué argumento sobrevive a esa diferencia?
4. Nombra la decisión que David toma distinto después de leer "Proveedores por categoría".
5. Si el número real de vencidos es 26 y la banda tope en 6 con enlace a `/tareas`, ¿esto es el tablero, o el tablero es `/tareas`?
