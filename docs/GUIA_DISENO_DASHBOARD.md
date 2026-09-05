# Guía de diseño reutilizable

## 1. Propósito

Esta guía define la identidad visual y las reglas de interfaz aprobadas para construir dashboards administrativos y analíticos en otros proyectos. El objetivo es conservar una apariencia sobria, clara, moderna y corporativa, con alta densidad de información sin sacrificar legibilidad.

No se debe copiar el contenido, los datos ni la lógica específica del proyecto original. Se debe trasladar su lenguaje visual, su jerarquía y su comportamiento de navegación.

## 2. Concepto rector

**Dashboard ejecutivo sobrio, limpio y preciso.**

La interfaz debe sentirse como una herramienta profesional de análisis y toma de decisiones, no como una página promocional. La información útil y los controles principales deben aparecer desde el primer pantallazo.

Principios:

- Claridad antes que decoración.
- Información densa, pero bien jerarquizada.
- Fondos claros y superficies blancas.
- Contraste elegante mediante azul oscuro, grises y acentos verdes o azules.
- Bordes suaves, sombras discretas y esquinas moderadamente redondeadas.
- Datos importantes visibles sin exigir desplazamientos innecesarios.
- Consistencia absoluta entre páginas, tablas, tarjetas, gráficos y filtros.

## 3. Personalidad visual

La experiencia debe transmitir:

- Confianza.
- Orden.
- Precisión.
- Modernidad sin extravagancia.
- Control operativo.
- Facilidad de lectura.

Evitar:

- Diseños recargados.
- Colores muy saturados.
- Fondos beige, amarillos o excesivamente cálidos.
- Sombras fuertes.
- Gradientes decorativos sin función.
- Íconos grandes o ilustraciones que compitan con los datos.
- Textos diminutos.
- Exceso de insignias, etiquetas o indicadores de estado.

## 4. Paleta de color

La paleta debe implementarse mediante variables globales para que pueda adaptarse sin alterar cada componente.

```css
:root {
  --color-navy-950: #0B1F33;
  --color-navy-900: #102A43;
  --color-blue-700: #2563A6;
  --color-blue-600: #2F73B9;
  --color-blue-100: #EAF2F8;

  --color-green-700: #2F6B57;
  --color-green-600: #3E8068;
  --color-green-100: #E9F3EF;

  --color-gray-950: #17202A;
  --color-gray-800: #344054;
  --color-gray-600: #667085;
  --color-gray-400: #98A2B3;
  --color-gray-300: #D0D5DD;
  --color-gray-200: #E4E7EC;
  --color-gray-100: #F2F4F7;
  --color-gray-50: #F7F9FC;
  --color-white: #FFFFFF;

  --color-warning: #B7791F;
  --color-warning-bg: #FFF7E6;
  --color-error: #B42318;
  --color-error-bg: #FEECEB;
  --color-success: #287A57;
  --color-success-bg: #EAF6F0;
}
```

Reglas de aplicación:

- Fondo general: gris muy claro, preferiblemente `--color-gray-50`.
- Encabezados principales y navegación: azul oscuro.
- Tarjetas y tablas: blanco.
- Color primario de interacción: azul medio.
- Verde: para variables energéticas, resultados favorables o confirmaciones.
- Amarillo y rojo: únicamente para alertas reales; nunca como decoración dominante.
- El color no debe ser el único medio para comunicar un estado.

## 5. Tipografía

Usar una fuente sans serif moderna y altamente legible. Orden recomendado:

```css
font-family: Inter, Manrope, "Segoe UI", Roboto, Arial, sans-serif;
```

Escala sugerida:

| Uso | Tamaño | Peso | Interlineado |
|---|---:|---:|---:|
| Título de página | 28–32 px | 700 | 1,15 |
| Título de sección | 20–24 px | 650–700 | 1,25 |
| Título de tarjeta | 15–17 px | 600–650 | 1,3 |
| Indicador principal | 24–32 px | 700 | 1,1 |
| Texto general | 16 px | 400–500 | 1,45 |
| Tabla y controles | 14–15 px | 450–600 | 1,35 |
| Metadatos secundarios | 12–13 px | 450–500 | 1,35 |

Reglas obligatorias:

- La tipografía de tablas no debe sentirse pequeña.
- Proveedor, calidad, copropiedad y demás campos relevantes deben leerse con comodidad.
- Usar cifras tabulares cuando la fuente lo permita: `font-variant-numeric: tabular-nums`.
- Mantener contraste alto entre texto y fondo.
- Evitar pesos `300` en información funcional.

## 6. Estructura general

Orden recomendado de cada página:

1. Encabezado compacto con nombre del módulo y contexto.
2. Barra global de filtros.
3. Indicadores principales.
4. Gráficos o visualizaciones.
5. Tabla detallada.
6. Paneles expandibles o información secundaria.

La barra de filtros debe permanecer en una posición visual consistente en todas las páginas. Los filtros globales deben afectar simultáneamente indicadores, gráficos, tablas, totales y cualquier detalle visible.

## 7. Navegación

- Navegación lateral o superior compacta, según el número de módulos.
- Estado activo inequívoco mediante fondo suave, texto más oscuro y un acento del color primario.
- Íconos lineales, sencillos y del mismo sistema visual.
- Etiquetas siempre visibles en escritorio; no depender únicamente del ícono.
- Evitar menús con demasiados niveles.
- Conservar la misma ubicación y tamaño de navegación en todo el producto.

## 8. Filtros globales

Los filtros constituyen una parte central del diseño, no un elemento accesorio.

Filtros base recomendados:

- Copropiedad.
- Proveedor.
- Periodo o mes, cuando aplique.

Comportamiento:

- Deben actualizar toda la página de manera coordinada.
- Deben conservarse al cambiar entre páginas cuando el contexto lo permita.
- Debe existir una opción clara de “Todas” o “Todos”.
- Mostrar los filtros activos sin saturar la pantalla.
- Incluir una acción visible para limpiar filtros cuando haya selecciones.
- Los selectores deben tener mínimo 40–44 px de altura para facilitar interacción.
- En móvil, se apilan verticalmente o se agrupan en un panel, sin perder accesibilidad.

## 9. Tarjetas de indicadores

- Fondo blanco.
- Borde gris muy claro de 1 px.
- Radio entre 12 y 16 px.
- Sombra mínima o inexistente.
- Espaciado interior entre 16 y 22 px.
- Etiqueta corta en gris medio.
- Valor principal destacado en azul oscuro.
- Unidad y periodo claramente diferenciados.
- Variaciones o comparaciones solo cuando aporten una decisión.

No convertir todos los datos en tarjetas. Los indicadores deben reservarse para cifras realmente prioritarias.

## 10. Gráficos

Principios:

- Pocos colores y alta legibilidad.
- Mantener el mismo color para una misma entidad o métrica entre páginas.
- Fondo blanco, ejes discretos y rejillas muy suaves.
- Leyendas cercanas al gráfico y nombres completos cuando el espacio lo permita.
- Formato local de cifras: separador de miles con punto y decimales con coma.
- Valores monetarios con `COP` o `$`, de forma consistente.
- Energía en `kWh`; potencia en `kW` o `kWp`, según corresponda.
- Tooltips con nombre, periodo, valor y unidad.
- No usar gráficos 3D.
- No usar más series de las que puedan distinguirse con claridad.

Elección de visualización:

| Necesidad | Visual recomendado |
|---|---|
| Evolución mensual | Línea o área muy sutil |
| Comparar entidades | Barras horizontales |
| Comparar dos métricas relacionadas | Barras agrupadas o paneles separados |
| Participación de pocas categorías | Dona, solo si son 2–5 categorías |
| Estado frente a una meta | Barra de progreso o bullet chart |
| Detalle exacto | Tabla, no gráfico |

## 11. Tablas

La tabla debe ser un componente principal de análisis, no una letra pequeña al final de la página.

Reglas visuales:

- Tamaño de letra general: 14–15 px.
- Encabezados: 13–14 px, semibold, fondo gris muy claro.
- Altura de fila: 46–54 px.
- Separadores horizontales suaves.
- Poco uso de líneas verticales.
- Encabezado fijo cuando la tabla sea larga.
- Hover de fila sutil.
- Números alineados a la derecha.
- Texto alineado a la izquierda.
- Estados centrados solo cuando tenga sentido.

Reglas de ancho:

- La primera columna numérica o consecutivo debe ser muy estrecha: aproximadamente 48–64 px.
- La columna de proveedor no debe dominar desproporcionadamente la tabla.
- Copropiedad y proveedor pueden truncarse con elipsis, pero deben mostrar el nombre completo mediante tooltip.
- Las columnas de cifras deben tener ancho suficiente para evitar saltos de línea.
- Calidad, proveedor y demás campos clave deben usar el mismo tamaño legible del cuerpo de tabla.
- Permitir desplazamiento horizontal controlado en móvil, sin comprimir los datos hasta hacerlos ilegibles.

Reglas funcionales:

- Ordenamiento en columnas relevantes.
- Paginación clara y compacta.
- Conteo de resultados.
- Estado vacío explicativo.
- Exportación solo si forma parte del alcance funcional.
- Filas o grupos expandibles cuando una entidad contenga subproyectos, cuentas o instalaciones.

## 12. Jerarquías y agrupaciones

Cuando una copropiedad contenga varios proyectos internos, se debe representar como una sola entidad principal expandible.

Ejemplo conceptual:

- Copropiedad
  - Proyecto interno 1
  - Proyecto interno 2
  - Proyecto interno 3

Reglas:

- No duplicar la copropiedad como si cada proyecto interno fuera una copropiedad diferente.
- El nivel principal muestra totales consolidados.
- Al expandir, aparecen los proyectos internos y sus valores.
- Los gráficos mensuales deben consolidar primero a nivel de copropiedad, salvo que el usuario elija explícitamente un proyecto interno.
- La interacción de expandir debe ser visible, consistente y accesible mediante teclado.

## 13. Estados y calidad de datos

Los estados deben describir la condición real del dato, sin generar alertas innecesarias.

Ejemplos:

- Validado.
- Revisar.
- Incompleto.
- Sin información.

Reglas:

- Antes de marcar un dato como “Revisar”, contrastar la información disponible con el valor total o la evidencia asociada.
- Usar etiquetas pequeñas y sobrias.
- Reservar el rojo para errores o inconsistencias reales.
- Incluir texto o ícono además del color.
- Cuando una tarifa tenga varios valores, mostrar el promedio calculado y aclarar la unidad; no reemplazar el dato por una etiqueta genérica como “Confirmada”.

## 14. Espaciado y geometría

Usar una escala consistente basada en múltiplos de 4 px:

```text
4, 8, 12, 16, 20, 24, 32, 40 y 48 px
```

Valores recomendados:

- Separación entre secciones: 24–32 px.
- Separación entre tarjetas: 16–20 px.
- Padding del contenedor principal: 24–32 px en escritorio; 16 px en móvil.
- Radio de tarjetas: 12–16 px.
- Radio de campos y botones: 8–10 px.
- Bordes: 1 px, gris claro.

La interfaz puede ser compacta, pero nunca apretada. Debe respirar sin desperdiciar pantalla.

## 15. Botones y controles

- Botón primario: fondo azul medio, texto blanco y contraste suficiente.
- Botón secundario: fondo blanco, borde gris y texto azul oscuro.
- Botón terciario: texto o ícono sin superficie dominante.
- Acciones destructivas: rojo, únicamente cuando corresponda.
- Altura mínima recomendada: 40 px en escritorio y 44 px para uso táctil.
- Foco visible en todos los controles.
- Deshabilitados claramente diferenciados, sin desaparecer visualmente.

## 16. Iconografía

- Íconos lineales y simples.
- Grosor visual consistente.
- Tamaño habitual: 16–20 px.
- Usarlos como apoyo, no como sustituto de etiquetas importantes.
- Evitar emojis como elementos de interfaz.

## 17. Movimiento e interacción

- Transiciones cortas: 150–220 ms.
- Usar movimiento para cambios de estado, expansión y retroalimentación.
- Evitar animaciones decorativas permanentes.
- Mostrar carga mediante skeletons en la estructura final del contenido.
- Respetar `prefers-reduced-motion`.

## 18. Diseño responsivo

### Escritorio

- Aprovechar el ancho para comparar indicadores, gráficos y tabla.
- Mantener una cuadrícula estable.
- Evitar columnas excesivamente anchas.

### Tableta

- Reducir el número de tarjetas por fila.
- Mantener filtros visibles y reorganizarlos en dos filas cuando sea necesario.

### Móvil

- Apilar módulos.
- Priorizar indicadores y filtros.
- Permitir scroll horizontal solo dentro de tablas.
- No reducir la tipografía para “hacer que todo quepa”.
- Mantener controles táctiles de al menos 44 px.

## 19. Accesibilidad

- Contraste mínimo recomendado: 4,5:1 para texto normal.
- Navegación completa mediante teclado.
- Foco visible.
- Etiquetas accesibles en filtros, botones e íconos interactivos.
- Encabezados semánticos y tabla con estructura correcta.
- Estados que no dependan exclusivamente del color.
- Compatibilidad con ampliación de texto al 200 %.
- Tooltips no deben contener información indispensable que no exista en otro lugar.

## 20. Componentes reutilizables mínimos

Crear y reutilizar, como mínimo:

- `AppShell`
- `PageHeader`
- `GlobalFilters`
- `MetricCard`
- `ChartCard`
- `DataTable`
- `StatusBadge`
- `ExpandableGroup`
- `EmptyState`
- `LoadingSkeleton`
- `Pagination`
- `Tooltip`

Cada componente debe alimentarse con propiedades y datos; no duplicar estilos por página.

## 21. Variables de diseño sugeridas

```css
:root {
  --font-sans: Inter, Manrope, "Segoe UI", Roboto, Arial, sans-serif;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;

  --radius-control: 9px;
  --radius-card: 14px;

  --border-subtle: 1px solid #E4E7EC;
  --shadow-card: 0 2px 10px rgba(16, 42, 67, 0.05);

  --transition-fast: 160ms ease;
  --transition-normal: 220ms ease;
}
```

## 22. Reglas innegociables al migrar el estilo

1. Mantener el diseño claro, sobrio y corporativo.
2. No reconstruir la identidad visual con otro lenguaje gráfico sin autorización.
3. No reducir la tipografía de tablas para acomodar más columnas.
4. Mantener estrecha la columna de consecutivo.
5. Evitar que la columna de proveedor ocupe un ancho desproporcionado.
6. Aplicar los filtros globales a gráficos, tablas, indicadores y totales.
7. Conservar agrupaciones jerárquicas y elementos expandibles.
8. Mostrar cifras con formatos y unidades consistentes.
9. Usar estados solo cuando representen una condición real del dato.
10. Priorizar la herramienta de trabajo desde el primer pantallazo; no agregar un hero promocional.

## 23. Lista de validación final

Antes de aprobar una nueva implementación, verificar:

- [ ] ¿El primer pantallazo permite empezar a analizar o trabajar inmediatamente?
- [ ] ¿La interfaz se percibe sobria, clara y profesional?
- [ ] ¿Los filtros modifican toda la página de manera coherente?
- [ ] ¿La tipografía de tablas y controles es cómoda de leer?
- [ ] ¿La primera columna de la tabla es compacta?
- [ ] ¿Proveedor y copropiedad tienen anchos equilibrados?
- [ ] ¿Los gráficos usan pocas series y colores consistentes?
- [ ] ¿Las unidades y formatos numéricos son correctos?
- [ ] ¿Las jerarquías se consolidan y expanden correctamente?
- [ ] ¿Los estados de calidad corresponden a una validación real?
- [ ] ¿La experiencia funciona en escritorio, tableta y móvil?
- [ ] ¿Se puede navegar con teclado y el foco es visible?
- [ ] ¿No hay texto funcional por debajo de 12 px?
- [ ] ¿La estética se mantiene igual en todas las páginas?

## 24. Instrucción breve para otro proyecto

> Usa esta guía como sistema visual obligatorio. Adapta únicamente los nombres, datos, módulos y funciones del nuevo proyecto. Conserva la paleta, jerarquía, densidad, tipografía, tablas legibles, filtros globales, tarjetas sobrias, gráficos limpios, agrupaciones expandibles y comportamiento responsivo. La nueva interfaz debe sentirse parte de la misma familia de productos, sin copiar información específica del dashboard original.
