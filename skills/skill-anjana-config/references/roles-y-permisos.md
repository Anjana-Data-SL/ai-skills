## Entidad: Roles

**Endpoint**: `POST /gateway/api/portuno/roles`

Recopila del usuario:
- **Nombre del rol**: El nombre deseado
- **¿Es un rol cross?**: Pregúntalo explícitamente; por defecto `false`
- **Descripción** (opcional): Si no se proporciona, usa el nombre original del rol
- **¿Es el rol por defecto?**: Pregúntalo explícitamente; por defecto `false`

Construye el body:
- `module`: Siempre `"ALL"`
- `name`: Sanea el nombre proporcionado por el usuario:
  - Sustituye espacios por `_`
  - Elimina acentos/tildes (á→a, é→e, í→i, ó→o, ú→u, ñ→n)
  - Elimina caracteres especiales (`*`, `/`, y otros no alfanuméricos ni `_`)
- `isCross`: `true` si el usuario confirma que es un rol cross, en caso contrario `false`
- `description`: Nombre original tal como lo dio el usuario (sin restricciones de caracteres)
- `isDefault`: **incluye SIEMPRE este campo como booleano explícito en TODAS las versiones, incluida la 25.1**: `true` solo si el usuario confirma que es el rol por defecto, en caso contrario `false`. **No lo omitas nunca.** Si se omite `isDefault`, la plataforma almacena `null`, un estado inválido: el campo solo admite `true`/`false`, deja el rol inconsistente con el resto de roles (todos los roles de la plataforma llevan un booleano explícito) y, de forma crítica, **no se puede corregir después** (ver la gestión de errores más abajo). Algunos entornos etiquetados como 25.1 exponen el modelo de rol de 25.2/26.1 (la columna `isDefault` existe), por lo que el campo debe enviarse siempre.

**Importante**: Guarda el href del rol: se necesita para asignar permisos a este rol. En 26.1 la respuesta no incluye `_links` (verificado): constrúyelo como `<PORTUNO_HREF>/roles/<id>` con el `id` de la respuesta; en 25.x usa `_links.self.href` si está presente.

**CRÍTICO: `isDefault` es inmutable una vez que el rol tiene usuarios asignados.** Un `PATCH /roles/<id>` para cambiar `isDefault` (por ejemplo, para corregir un `null` a `false`) falla con `4006 "The change is not possible while there are users with the role assigned."` en cuanto cualquier entrada de `userOURoles` referencia el rol. Por tanto, `isDefault` **debe ser correcto en el momento de la creación, antes de cualquier asignación de usuarios**: no hay recuperación vía API después (el usuario se ve obligado a corregirlo manualmente en la BD/UI). Esta es la razón por la que el campo es obligatorio en el POST y no opcional. Crear un rol con `isDefault: true` requiere la confirmación reforzada (ver "Creaciones sensibles").

**Gestión de errores en las versiones 25.2 y 26.1**: Si la API devuelve un error `409` cuando `isDefault` es `true`, significa que ya existe un rol por defecto configurado. Informa al usuario: "Ya existe un rol por defecto configurado. Solo puede haber un rol por defecto. Si deseas que este rol sea el rol por defecto, primero hay que modificar el rol actual para que deje de serlo." A continuación, comprueba con `GET <BASE_URL>/gateway/api/portuno/api/filter/roles?nameEquals=<name>` si el rol se creó de todos modos, e informa al usuario del resultado real: no lo des por supuesto. NO reintentes automáticamente.

## Entidad: Permisos

**Endpoint**: `POST /gateway/api/portuno/permissions`

Recopila del usuario:
- **Qué permiso** asignar (del catálogo de 25 tipos de permiso de la versión 26.1 en `references/permissions-catalog.md`, que también lista los equivalentes de 25.x)
- **A qué rol** asignarlo (usa el href de un rol recién creado, o pídeselo al usuario)
- **Object subtype** (solo para los permisos que lo requieren, en mayúsculas y sin espacios)

**Verifica el rol antes de crear el permiso (obligatorio)**: toma el id numérico del final del href del rol y ejecuta:

```bash
curl -s "<BASE_URL>/gateway/api/portuno/roles/<ROLE_ID>" \
  -H @"<AUTH_HEADER_FILE>" \
  -H "Content-Type: application/json"
```

- Si la respuesta devuelve el rol, muestra su `name` y `description` al usuario para que confirme que es el rol previsto. Si la respuesta incluye `_links.self.href`, usa ese valor como `role` en el body del permiso; en caso contrario (26.1) usa `<PORTUNO_HREF>/roles/<ROLE_ID>`. La forma de gateway `<BASE_URL>/gateway/portuno/roles/<ROLE_ID>` también se acepta (verificado).
- Si el rol no existe (404 o respuesta vacía), **no** crees el permiso: díselo al usuario y pide el rol correcto. Si el usuario solo conoce el nombre del rol, búscalo en `GET <BASE_URL>/gateway/api/portuno/api/filter/roles`.
- No rechaces el href de un rol solo porque su host difiera de `<BASE_URL>`: lo que cuenta es que el rol exista en este entorno.
- Dentro de una sesión, un rol ya verificado (o recién creado) no necesita comprobarse de nuevo para cada uno de sus permisos.

Construye el body:
- `action`: Determinado por el tipo de permiso (ver catálogo)
- `subType`: Determinado por el tipo de permiso; puede ser `"ALL"`, `"ANJANA"` o un object subtype proporcionado por el usuario
- `role`: La URL href completa del rol

**CRÍTICO: los códigos exactos de action/subType dependen de la versión. NO te fíes de la memoria.** Antes de lanzar el primer POST de permiso de una sesión, abre `references/permissions-catalog.md` y busca el par exacto `action` / `subType`. La plataforma acepta en silencio combinaciones desconocidas (por ejemplo, `ANJANA_PLATFORM_ACCESS / ALL`) y las almacena como filas huérfanas que no producen ningún efecto en la UI: el usuario parece tener acceso, pero en realidad no puede iniciar sesión ni usar el módulo. Errores habituales en 26.1:

| Petición en lenguaje natural | ❌ Incorrecto (NO funciona) | ✅ Correcto en 26.1 |
|---|---|---|
| Acceso a la plataforma / al portal | `ANJANA_PLATFORM_ACCESS / ALL` | `PLATFORM_ACCESS / ANJANA` |
| Acceso al panel de administración | `ANJANA_ADMIN_ACCESS / ALL` | `ADMIN_ACCESS / ANJANA` |
| Acceso al Marketplace / solicitar acceso a datos | `MARKETPLACE_ACCESS / ALL` | `ADHERENCE_ACCESS / ALL` |
| Permiso de uso de la API | `ALL_API_ADMIN / ALL` | `API_ADMIN / ALL` |

Las cadenas de rol del JWT (por ejemplo, `ROLE_ANJANA_PLATFORM_ACCESS`) **no** son los códigos de action: son la serialización interna de la plataforma de `action+subType` y no deben reutilizarse como entrada del endpoint de permisos.

**Reglas de validación para permisos específicos:**
- `ORGANIZATIONAL_UNIT_OWNER` y `CHANGE_OU`: Solo aplican a entidades (no a relaciones). Pide confirmación al usuario.
- `CHANGE_STATUS`: No se puede aplicar a los subtipos DATASET, DSA, PROCESS, INSTANCE o SOLUTION. Valida antes de enviar. `DEPRECATION` no tiene esa restricción: es válido sobre esos subtipos nativos del catálogo de datos en 25.1, 25.2 y 26.1.
- **Subtipos nativos (`createWorkflow == "WF_NATIVO"`)**: NO les asignes permisos de acción de usuario (`CREATION_MODIF`, `DELETE_MY_OBJ`, `DELETE_ALL`, `ORGANIZATIONAL_UNIT_OWNER`, `CHANGE_OU`, `CHANGE_STATUS`, `DEPRECATION`, `AUTOMATIC_METADATA`). Las instancias de los subtipos nativos (por ejemplo, `ADHERENCE`, `STRUCTURE`) las genera automáticamente la plataforma: estos permisos crean entradas huérfanas sin efecto en la UI. **Especialmente relevante en asignaciones masivas**: al iterar `GET /api/filter/objectSubTypes` para conceder a un rol permisos sobre muchos subtipos, filtra siempre primero los `createWorkflow == "WF_NATIVO"`.
- **`DATASET_FIELD`**: NUNCA asignes permisos de acción de usuario (`CREATION_MODIF`, `DELETE_MY_OBJ`, `DELETE_ALL`, `ORGANIZATIONAL_UNIT_OWNER`, `CHANGE_OU`, `CHANGE_STATUS`, `DEPRECATION`, `AUTOMATIC_METADATA`) a `DATASET_FIELD`. Los campos son entidades hijas que se gestionan en línea dentro del DATASET padre (mediante la pestaña "Estructura"), no de forma independiente mediante el asistente. Para permitir que un rol gestione campos, dale `CREATION_MODIF/DATASET`: eso autoriza automáticamente la gestión de campos dentro de los datasets propios.

**Versión 25.2: los conjuntos grandes de permisos pueden romper el login**: cada permiso de los roles del usuario se añade al JWT como una entrada `ROLE_*`, por lo que conceder a un rol permisos sobre muchos subtipos puede hacer que el token supere el límite de tamaño de cabecera del servidor (~8 KB) y que el login falle. Concede solo los permisos que el rol necesita y avisa al usuario antes de concesiones masivas en 25.2.

**Permiso base obligatorio para las versiones 25.1 / 25.2: `WIZARD/ALL`**:

Las versiones 25.1 y 25.2 de Anjana requieren el permiso `WIZARD/ALL` para que el asistente de creación ("+") aparezca en la UI. El asistente es invisible sin él, aunque el rol tenga `CREATION_MODIF` para subtipos concretos. **Cuando `<ANJANA_VERSION>` sea `25.1` o `25.2`, todo rol que reciba al menos un `CREATION_MODIF` debe recibir también `WIZARD/ALL`** como parte de la misma configuración.

```json
{"action": "WIZARD", "subType": "ALL", "role": "<ROLE_HREF>"}
```

**En la versión 26.1 la action `WIZARD` se eliminó**: NO la crees; el asistente se infiere automáticamente a partir de cualquier `CREATION_MODIF`. Enviar `WIZARD/ALL` en 26.1 devuelve un error.

Para el catálogo completo de permisos con todas las combinaciones action/subType, los permisos base por versión y la lista de validación, consulta `references/permissions-catalog.md`.
