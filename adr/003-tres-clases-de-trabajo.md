# ADR-003: Tres clases de trabajo en `Tareas`, y la regla vive en un solo sitio

## Contexto
No todo lo que se registra como "tarea" pesa igual para el cumplimiento: un
compromiso puntual de una reunión no es lo mismo que la ejecución de un acuerdo de
servicio (ANS) ni que una responsabilidad permanente sin plazo. Tratarlas igual
inflaría o desinflaría el indicador de cumplimiento sin sentido.

Ya ocurrió un bug de esto: la regla de qué cuenta para el cumplimiento se copió en
más de una pantalla, y en un momento el indicador de arriba sumaba las tareas
canceladas mientras la fila del proveedor no las sumaba — daban el mismo número
solo por casualidad, porque todavía no había ninguna cancelada.

## Decisión
La columna `tipo` de `Tareas` distingue tres clases:

| tipo | Qué es | Cuenta para cumplimiento |
|---|---|---|
| `normal` | compromiso adquirido en una reunión | **sí** — es lo único que lo mide |
| `ans` | ejecución de un acuerdo de servicio | no, se mide aparte |
| `permanente` | responsabilidad continua, sin plazo | no, y tampoco vence |

Las filas guardadas antes de que existiera la columna llegan con `tipo` vacío y se
leen como `normal` — no hubo que migrar ninguna fila existente.

La regla de qué cuenta y cómo se calcula vive en **un solo sitio**, `base.html`:
`tipoTarea()`, `cuentaParaCumplimiento()`, `cuentaComoAbierta()` y
`tasaCumplimiento()`.

## Consecuencias
Cualquier pantalla que necesite calcular cumplimiento debe llamar a esas cuatro
funciones de `base.html`, nunca reimplementar la condición localmente — es
exactamente lo que causó el bug del indicador descuadrado.
