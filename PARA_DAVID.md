# Actas de Proveedores — cómo se usa

Herramienta de la Gerencia de Proveedores. Convierte la transcripción de una reunión en un
acta con los compromisos claros, y guarda el histórico para que en la siguiente reunión
sepas exactamente qué quedó pendiente.

No hay que instalar nada. Se entra desde el navegador con el correo de la empresa.

---

## Lo que vas a ver al entrar

**El tablero.** Lo primero que aparece es qué está vencido: los compromisos con fecha límite
pasada que siguen sin cerrar, con los días de atraso y el proveedor. Si no hay nada vencido,
te dice qué vence en los próximos 15 días.

Debajo, la tabla de proveedores ordenada por quién peor va: reuniones, compromisos abiertos,
vencidos y porcentaje de cumplimiento.

Los cuatro filtros de arriba (proveedor, tipo de servicio y rango de fechas) mandan sobre
todo lo que hay abajo.

---

## Los cuatro pasos del trabajo

### 1. Crear el proveedor (solo la primera vez)
En **Proveedores** → nombre y tipo de servicio. El tipo de servicio es lo que después te
permite filtrar el tablero por categoría (ascensores, aseo, seguridad…). Si el que necesitas
no está en la lista, eliges «Crear uno nuevo» y queda disponible para los siguientes.

### 2. Generar el acta después de la reunión
En **Generar acta** → eliges el proveedor, la fecha, y subes la transcripción (`.docx`,
`.pdf` o `.txt`) o la pegas en el cuadro.

Si ese proveedor tiene compromisos abiertos de reuniones anteriores, te avisa cuántos. Esos
se le entregan a la inteligencia artificial para que revise si se mencionaron en esta reunión
y reporte qué avance hubo.

Tarda entre 20 y 60 segundos.

### 3. Revisar antes de guardar
**Esto es importante.** Lo que sale es un borrador y todo es editable: los temas, las
conclusiones, los compromisos, los responsables y los plazos. Puedes borrar lo que no
corresponda y agregar lo que falte.

Lo que guardes aquí es lo que alimenta el tablero. Si dejas pasar un compromiso mal
redactado o que no se acordó, te va a aparecer como pendiente durante meses.

Al guardar, el acta en Word queda archivada en Drive, en la carpeta de ese proveedor, y
tienes el enlace para pegárselo al proveedor en un correo.

### 4. Hacer seguimiento entre reuniones
En **Compromisos** ves todo lo que está sin cerrar, con los vencidos primero. Ahí puedes:

- cambiar el estado (pendiente, en proceso, cumplido, cancelado)
- ponerle o cambiarle la fecha límite
- **anotar un avance**: una nota de qué pasó, con quién hablaste, qué falta

Cada cambio y cada nota quedan registrados con la fecha. Ese historial es lo que después
puedes mostrarle al proveedor como evidencia.

---

## La historia de cada proveedor

Haz clic en el nombre de cualquier proveedor. Vas a ver:

- **Para la próxima reunión**: los compromisos que siguen abiertos. Esto es lo que conviene
  revisar antes de sentarte con él.
- **La historia**: cada reunión, de la más reciente a la más antigua, con sus temas,
  conclusiones y compromisos. Y cuando una reunión reportó avances sobre pendientes
  anteriores, aparece el bloque «Avance de lo que quedó pendiente antes» con el cambio de
  estado: pendiente → en proceso → cumplido.

Esa es la parte que convierte reuniones sueltas en un seguimiento de verdad.

---

## Cosas que conviene saber

**Un compromiso sin fecha límite no está vencido ni está bien: está sin plazo**, y la
herramienta lo dice así. No inventa urgencias. Si quieres que algo tenga semáforo, ponle
fecha límite a mano en la pantalla de Compromisos.

**La inteligencia artificial no marca nada por omisión.** Si un pendiente no se mencionó en
la reunión, no lo toca: sigue pendiente. Solo reporta lo que de verdad se habló.

**No inventa datos.** Si en la transcripción no está claro quién dijo algo, lo escribe de
forma impersonal en vez de atribuirlo. Y si la reunión no dejó compromisos, deja la lista
vacía en vez de rellenarla.

**Puedes girar la pantalla hacia el proveedor.** La herramienta está hecha para eso: muestra
los datos sin dramatismo y sin lenguaje acusatorio.

**Los datos están en una Hoja de Google** a la que también tienes acceso, y las actas en una
carpeta de Drive compartida. Si algún día necesitas corregir algo a mano o sacar los datos a
Excel, están ahí.

---

## Si algo sale mal

| Qué ves | Qué pasa |
|---|---|
| «Gemini está saturado o se agotó la cuota del día» | Espera uno o dos minutos y vuelve a intentar. La transcripción no se pierde. |
| «La IA no devolvió un acta utilizable» | Normalmente la transcripción es muy larga. Intenta de nuevo, o divide la reunión en dos partes. |
| «El archivo pasa de 4,5 MB» | Suele ser un PDF escaneado. Pega el texto en el cuadro, o súbelo como `.docx` o `.txt`. |
| Un banner amarillo o rojo arriba | Falta algo de configuración en el servidor. Avísale a Santiago. |
| Tu cuenta no tiene acceso | Estás entrando con un correo que no es el de la empresa. |

Cualquier otra cosa, Santiago.
