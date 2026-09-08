# Actas de Proveedores — Abelardo Yepes S.A.S.
**Para:** Gerencia de Proveedores · **Administra:** Santiago Rincón

## Qué es
App web (Flask) que convierte la transcripción de una reunión con un proveedor en un
**acta ejecutiva** —temas, conclusiones y compromisos— usando **Google Gemini**, la guarda,
y desde ahí arma un **tablero de seguimiento** y una **línea de tiempo por proveedor**.

**No tiene nada que ver en ejecución con el generador de actas F08.** Otro repo, otro
hosting (Vercel, no Render — ver [ADR-001](adr/001-por-que-vercel-no-render.md)), otra Hoja
de Google. Solo se copiaron patrones de código ya probados (motor de Gemini, manejo de
fechas, bloque de OAuth). Tocar esta app **no puede romper**
`generador-actas-gtqs.onrender.com`.

## La idea central: continuidad entre reuniones
Antes de llamar a Gemini, el backend inyecta al prompt los compromisos **abiertos** de
reuniones anteriores con ese proveedor; la IA reporta avance solo de lo que sí se
mencionó — nunca por omisión. Detalle y razón en
[ADR-002](adr/002-continuidad-entre-reuniones.md).

## Estructura
```
ActasProveedores/
├── adr/                 ← decisiones de arquitectura, ver índice en adr/README.md
├── app/
│   ├── app.py           ← Flask: rutas, OAuth, roles
│   ├── hoja.py          ← ÚNICA capa de datos (Hoja de Google) + caché de 60 s
│   ├── motor_ia.py      ← motor de Gemini resistente (copiado del F08)
│   ├── prompts.py       ← el prompt del acta de proveedores
│   ├── build_acta.py    ← el .docx, armado desde cero (sin plantilla)
│   ├── templates/       ← base, generador, dashboard, timeline, tareas, proveedores…
│   └── static/estilo.css
├── api/index.py         ← punto de entrada de Vercel (solo expone la app de Flask)
├── vercel.json          ← solo maxDuration e includeFiles (el enrutado lo hace el preset)
├── requirements.txt     ← dependencias (en la raíz: ahí las busca Vercel)
├── docs/GUIA_DISENO_DASHBOARD.md ← guía visual de la casa; manda sobre el front
├── apps_script/Codigo.gs ← copia de referencia del Web App (el real vive en Apps Script)
├── dev/                 ← simulador de la Hoja, sembrador de datos, arranque local
└── iniciar.sh           ← arranque local (gitignored)
```

## Modelo de datos — Hoja "Actas Proveedores"
Cuatro pestañas; las columnas exactas están en `COLUMNAS` de `apps_script/Codigo.gs`.
Si se reordenan en la hoja, **hay que reordenarlas ahí también**.

| Pestaña | Para qué |
|---|---|
| `Proveedores` | catálogo: nombre, tipo de servicio, contacto, estado |
| `Reuniones` | una fila por reunión; el acta completa va serializada en `temas_json`, y `enlace_docx` apunta al archivo en Drive |
| `Tareas` | los compromisos; `tarea_origen_id` encadena una tarea con la que la originó |
| `Seguimiento` | bitácora de avances: alimenta la línea de tiempo y el historial |
| `ANS` | acuerdos de servicio de cada proveedor |

La columna `tipo` de `Tareas` distingue tres clases que no pesan igual para el cumplimiento
(por qué, y el bug que causó, en [ADR-003](adr/003-tres-clases-de-trabajo.md)):

| tipo | Qué es | Cuenta para cumplimiento |
|---|---|---|
| `normal` | compromiso adquirido en una reunión | **sí** |
| `ans` | ejecución de un acuerdo de servicio | no |
| `permanente` | responsabilidad continua, sin plazo | no |

## Decisiones de arquitectura — leer el ADR antes de tocar esto
Índice completo en [`adr/README.md`](adr/README.md).

| Si vas a tocar… | Regla activa | Detalle |
|---|---|---|
| Hosting / despliegue | Vercel, no Render — el porqué es específico de esta app | [ADR-001](adr/001-por-que-vercel-no-render.md) |
| `prompts.py` (continuidad) | No reportar avance de lo que no se mencionó en la reunión | [ADR-002](adr/002-continuidad-entre-reuniones.md) |
| Columna `tipo` de Tareas | normal/ans/permanente; cálculo de cumplimiento en un solo sitio (`base.html`) | [ADR-003](adr/003-tres-clases-de-trabajo.md) |
| Modelo de ANS | Sin fecha ni estado — es un principio, no una tarea | [ADR-004](adr/004-ans-son-principios-no-tareas.md) |
| Cualquier fecha | Siempre `AAAA-MM-DD`, comparar como texto, nunca `new Date()` | [ADR-005](adr/005-fechas-aaaa-mm-dd.md) |
| Guardado del acta | Hoja = fuente de verdad; Drive es adjunto, puede fallar sin perder el registro | [ADR-006](adr/006-dos-copias-actas-hoja-y-drive.md) |
| `build_acta.py` | Dos columnas por reparto de longitud, no por pares; anchos con `columns[i].width` | [ADR-007](adr/007-formato-acta-dos-columnas.md) |
| `puede_leer()` / `puede_escribir()` | Sin login, no entra nadie — a propósito distinto del F08 | [ADR-008](adr/008-roles-diferencia-con-f08.md) |
| Crear tareas nuevas | Un solo formulario, un solo sitio (`/proveedor/<id>`) | [ADR-009](adr/009-perfil-proveedor.md) |
| Editar/borrar actas o tareas | Reusar la pantalla de revisión; actualizar, no recrear; borrado en cascada | [ADR-010](adr/010-correccion-de-lo-guardado.md) |
| `vercel.json` | Nunca agregar `rewrites` — el preset de Flask ya enruta todo | [ADR-011](adr/011-gotchas-primer-despliegue-vercel.md) |
| Límites de Vercel Hobby | `maxDuration=300s`, tope de subida 4,5 MB, caché por instancia | [ADR-012](adr/012-limites-plataforma-serverless-vercel.md) |
| Revisión antes de guardar, ids de seguimiento, semáforo, escrituras síncronas, caché | Cinco reglas operativas que no se deben deshacer sueltas | [ADR-013](adr/013-decisiones-operativas-no-deshacer.md) |
| Acceso a datos nuevo | Siempre por `hoja.py` — es el único punto de reemplazo si algún día se cambia de Hoja a base de datos | [ADR-014](adr/014-hoja-google-no-es-base-de-datos.md) |

## Variables de entorno (se configuran en Vercel, nunca en el repo)
| Variable | Para qué |
|---|---|
| `GEMINI_API_KEY`, `_2..7` | Llaves de Gemini. La app **rota** entre ellas para no topar la cuota gratis. |
| `LOG_URL` | Web App de Apps Script que lee y escribe la Hoja. **Sin esto no se guarda nada** (la app avisa en pantalla). |
| `SECRET_KEY` | Firma de sesiones. **Obligatoria en Vercel**: cada instancia es distinta, así que sin una clave fija las sesiones se cierran solas. Si falta, la app lo avisa en un banner rojo. |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Login con Google. |
| `DOMINIO_PERMITIDO` | `abelardoyepes.com` → todo ese dominio puede entrar y escribir. |
| `SUPERADMIN` | Santiago. Siempre tiene acceso total. |
| `GERENTE` | Correos con permiso de escritura (el gerente de proveedores). Separados por coma. |
| `LECTORES` | Correos de **solo consulta**: ven el tablero pero no pueden cambiar nada. |
| `DEV_LOCAL` | Solo local: salta el login. **Nunca ponerla en Vercel.** |

## Uso local
```bash
cd ~/Desktop/Claude/ActasProveedores
python3 -m pip install -r requirements.txt
python3 dev/servidor_local.py       # app + simulador de la Hoja, todo en uno → :5052
```
`iniciar.sh` toma la llave de Gemini de la del generador de actas, para que siga existiendo
en un solo archivo del computador. Los datos de prueba quedan en `dev/datos_prueba.json` y
las actas archivadas en `dev/actas/<Proveedor>/`, equivalente local de la carpeta de Drive.
Ambos están en `.gitignore`.

```bash
python3 dev/sembrar.py --limpio    # datos de ejemplo con vencidos y seguimiento
```

## Despliegue
Hay que hacerlo **en este orden**: la Hoja produce la `LOG_URL` que necesita Vercel, y
Vercel produce el dominio que necesita Google Cloud para el login.

### 1. La Hoja de Google y el Apps Script
Todo en la **cuenta de la empresa** (`@abelardoyepes.com`), nunca en una personal.

1. Crear una hoja de cálculo llamada **Actas Proveedores**. El script crea pestañas y
   encabezados solo la primera vez.
2. Extensiones → Apps Script. Borrar el contenido y pegar `apps_script/Codigo.gs`.
3. Implementar → Nueva implementación → **Aplicación web**, con
   **"Ejecutar como: Yo"** y **"Quién tiene acceso: Cualquier persona"**.
4. Aceptar los permisos (Drive y Hoja). Sin el permiso de Drive las reuniones se guardan
   pero ningún acta queda archivada.
5. Copiar la URL que queda: esa es `LOG_URL`.

Comprobación antes de seguir: abrir `LOG_URL?sheet=Proveedores` en el navegador. Debe
responder `[]`. Si devuelve HTML, la implementación quedó mal publicada (casi siempre por
"Quién tiene acceso"); la app también lo avisa en pantalla si pasa.

### 2. Credenciales de Google para el login
Sobre el proyecto de Google Cloud que ya existe para el generador F08: APIs y servicios →
Credenciales → Crear credenciales → **ID de cliente de OAuth**, tipo *Aplicación web*.
Dejar la URI de redirección para el paso 4, cuando ya exista el dominio de Vercel.

### 3. Repo y Vercel
1. Repo **privado** nuevo en GitHub (`actas-proveedores`). Push a `main` = despliegue.
2. Vercel → Add New Project → importar el repo. No hay que configurar build: el
   `vercel.json` y `requirements.txt` de la raíz ya lo dicen todo.
3. Cargar las variables de entorno de la tabla de arriba. `SECRET_KEY`:
   `python3 -c "import secrets; print(secrets.token_hex(32))"`.
4. Desplegar. Verificar `https://<dominio>/health`: debe responder
   `{"status":"ok","hoja":true}`. Si `hoja` sale `false`, falta `LOG_URL`.

### 4. Cerrar el login
Copiar el dominio de Vercel y agregar a la credencial de OAuth la URI de redirección
`https://<dominio>/auth/callback`. Entrar con la cuenta de David y confirmar que pasa
del login al tablero.

### 5. Compartirle a David
La **Hoja** (edición), la carpeta de Drive **Actas de Proveedores** (edición), y la URL
de la app.

### Al actualizar
- **Código de la app:** push a `main` y Vercel redespliega solo.
- **`Codigo.gs`:** hay que **volver a implementar con versión nueva** (Implementar →
  Administrar implementaciones → editar → Versión: Nueva). Si solo se guarda, sigue
  corriendo la versión anterior.

Fallas conocidas del primer despliegue (rewrites en `vercel.json`, correo de commit
inválido): ver [ADR-011](adr/011-gotchas-primer-despliegue-vercel.md).
