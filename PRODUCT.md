# Product

## Register

product

## Platform

web

## Users

**David, Gerente de Proveedores de Abelardo Yepes S.A.S.** (administradora de propiedad
horizontal, Colombia). Trabaja sentado en su computador de oficina, antes y después de las
reuniones con proveedores de servicios: ascensores, aseo, jardinería, seguridad, obras.

Su trabajo tiene dos momentos y la herramienta sirve a los dos:

1. **Después de la reunión** — tiene una transcripción y necesita convertirla en un acta con
   los compromisos claros, sin perder media hora redactando.
2. **Antes de la siguiente reunión** — necesita llegar sabiendo qué quedó pendiente la vez
   pasada y qué se incumplió, para poder reclamarlo con evidencia.

A veces abre la herramienta **delante del proveedor**, en la reunión misma.

Un segundo perfil, de solo consulta: gerencia que quiere ver cómo van los proveedores sin
poder modificar nada.

## Product Purpose

Convertir reuniones sueltas con proveedores en un **seguimiento continuo**. Hoy cada reunión
es una isla: se acuerdan cosas, nadie las registra de forma consultable, y en la reunión
siguiente nadie se acuerda de qué quedó pendiente.

La herramienta cierra ese ciclo: la IA extrae los compromisos del acta, y en la reunión
siguiente le devuelve al gerente los pendientes anteriores para que la IA misma reporte qué
avance hubo. El resultado es una línea de tiempo por proveedor donde se ve, reunión a
reunión, qué se prometió y qué se cumplió.

Éxito = David llega a una reunión sabiendo exactamente qué reclamar, y el proveedor sabe que
queda registrado.

## Brand Personality

**Orden, claridad, evidencia.**

Debe sentirse como un informe de gestión bien hecho: se entiende de un vistazo, sin que se
sienta una auditoría hostil. La herramienta no acusa, muestra. El dato incómodo (un
compromiso vencido) se presenta con precisión y sin dramatismo, porque va a leerse con el
proveedor al lado.

Voz: español de Colombia, profesional y directo. Frases cortas. Cero relleno y cero
lenguaje de software ("optimiza", "potencia", "gestiona tu flujo").

## Anti-references

- **El tablero SaaS oscuro con acento neón.** Es de donde viene esta app (heredó el look de
  Control de Lecturas) y es justo lo que no debe ser: se ve mal en una oficina iluminada y
  parece un producto de startup, no un instrumento de gestión de una administradora.
- **La estética de auditoría punitiva:** rojo por todas partes, semáforos gigantes,
  porcentajes de castigo. El proveedor está mirando la pantalla.
- **El adorno de dashboard:** anillos de progreso decorativos, tarjetas iguales repetidas,
  gráficos que no responden a ninguna pregunta que David se haga.
- No debe parecerse a Control de Lecturas, aunque sea de la misma casa.

## Design Principles

1. **Lo vencido se ve primero.** La pantalla de entrada responde "¿qué se está incumpliendo?"
   antes que cualquier otra cosa. Todo lo demás está a un clic.
2. **Sin plazo no hay urgencia.** Nunca se inventa una alarma. Un compromiso sin fecha límite
   no es tarde ni está bien: está sin plazo, y se dice así.
3. **Presentable delante del proveedor.** Cualquier pantalla puede terminar proyectada o
   girada hacia la otra persona. Nada que avergüence ni que suene a acusación.
4. **La IA propone, el gerente firma.** Nada entra al histórico sin revisión humana. El paso
   de revisión no es fricción: es lo que hace confiable el tablero.
5. **Continuidad sobre eventos.** El objeto de valor no es el acta, es la cadena de
   compromisos entre reuniones. El diseño debe hacer visible esa cadena.

## Accessibility & Inclusion

WCAG 2.1 AA. Uso en oficina con luz natural, en pantalla de escritorio, por un usuario adulto
que no es técnico.

- Contraste de texto ≥4.5:1; nada de gris claro "elegante" sobre fondo claro.
- El estado (vencido / en proceso / cumplido) **nunca** se comunica solo por color: siempre
  lleva texto. La proyección en sala y el daltonismo lo exigen por igual.
- `prefers-reduced-motion` respetado en toda animación.
- Todo objetivo táctil y de clic ≥40px de alto.
