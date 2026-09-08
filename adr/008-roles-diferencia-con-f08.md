# ADR-008: Modelo de roles, y por qué es más estricto que el del F08

## Contexto
Esta app expone datos de proveedores y compromisos a distintos niveles de acceso:
el gerente necesita poder escribir, otros correos del dominio solo necesitan
consultar, y sin configuración de login el acceso por defecto debía decidirse.

## Decisión
`puede_leer()` y `puede_escribir()` en `app.py` deciden el acceso, y la
comprobación está **en el servidor**, no solo escondiendo botones en la interfaz —
un lector podría llamar la API directamente sin pasar por la pantalla. Un correo en
`LECTORES` que no esté también en `GERENTE` no puede escribir, aunque sea del
dominio autorizado.

**Diferencia deliberada con el generador F08**: allá, si no hay OAuth configurado,
`es_gerencia()` devuelve `True` por defecto y cualquiera con la contraseña de
respaldo ve todo. Aquí, sin Google configurado y sin `DEV_LOCAL`, **no entra
nadie** — no hay modo de respaldo abierto.

## Consecuencias
Al portar código de autenticación entre los dos proyectos, no asumir que el
comportamiento por defecto es el mismo — copiar el patrón del F08 tal cual
reabriría el acceso sin login en esta app.
