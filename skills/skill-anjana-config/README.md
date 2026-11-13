# skill-anjana-config

Añade configuración a Anjana Data Platform vía su API REST (`/gateway/api/portuno/`): usuarios y su autorización, unidades organizativas, roles, permisos, atributos de metadatos, valores de referencia, taxonomías, relaciones entre atributos, subtipos de objeto (entidades/activos), menús, secciones, validaciones de atributo de plantilla, capas de lineage, internacionalización, notificaciones y filtros de búsqueda. Además genera y valida en local workflows de validación BPMN 2.0 (sin desplegarlos).

**Regla crítica de la propia skill: solo crea configuración nueva.** Modificar, sobrescribir o borrar configuración existente queda fuera de su alcance, salvo un conjunto cerrado de operaciones correctivas y de internacionalización, que exigen confirmación explícita (ver «Operaciones que modifican o borran» en `SKILL.md`). Las creaciones que otorgan mucho poder (permisos de administración, roles por defecto, operaciones masivas…) piden confirmación reforzada.

## Trigger

`[skill-anjana-config]`, o cuando el usuario pida crear una unidad organizativa, rol, permiso, atributo, usuario, valor de referencia, taxonomía, relación entre atributos, entidad, menú, sección, notificación, filtro o workflow en Anjana Data Platform.

## Versiones soportadas

Anjana `25.1`, `25.2` y `26.1`. La versión se pregunta al inicio de la sesión y determina el comportamiento específico.

## Estructura

- `SKILL.md`: hub. Reglas de modificación/borrado, setup de sesión, autenticación, flujo conversacional, construcción segura de comandos y plantilla curl.
- `references/`: un fichero por tipo de entidad con los pasos de recolección de datos y el body de la petición, más el catálogo de permisos (`permissions-catalog.md`), el catálogo de endpoints (`api-endpoints.md`), la visión conceptual de la plataforma (`anjana-data-platform-context.md`), el flujo de workflows (`workflows.md`, `workflows-bpmn.md`) y dos workflows reales de ejemplo en `references/examples/`.
- `scripts/generate_bpmn.py`: genera y valida un `.bpmn20.xml` a partir de una especificación JSON (solo biblioteca estándar de Python).

## Seguridad

Los secretos (token, contraseñas, claves de servicios externos) nunca van en la línea de comandos: se leen de ficheros en un directorio temporal privado fuera del repo y de carpetas sincronizadas, que se borra al terminar la sesión.
