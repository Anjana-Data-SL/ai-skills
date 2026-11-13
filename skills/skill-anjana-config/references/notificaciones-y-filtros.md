## Notificaciones

Configurar una notificación siempre requiere dos pasos: crear las claves de la notificación y, después, crear las traducciones.

### Paso 1: Crear la notificación

**Endpoint**: `POST <BASE_URL>/gateway/api/portuno/notifications`

**Body**:
```json
{
  "moduleType": "ALL",
  "notificationCode": null,
  "notificationReceiverType": "<RECEIVER_TYPE>",
  "notificationType": "<NOTIFICATION_TYPE>",
  "receiverRole": "<ROLE_NAME_OR_NULL>",
  "severity": "<SEVERITY>",
  "subject": "<SUBJECT_KEY>",
  "translationKey": "<BODY_KEY>"
}
```

**Reglas de campos**:

| Campo | Valores | Notas |
|---|---|---|
| `moduleType` | `"ALL"` | Siempre `"ALL"` |
| `notificationCode` | `null` | Siempre `null` para notificaciones de usuario (solo se usa para notificaciones internas de la plataforma). **No lo confundas con el número que usan los workflows**: los workflows BPMN referencian el `id` autogenerado de la notificación (ver más abajo). |
| `notificationReceiverType` | `"ROLE"` o `"USER"` | `"ROLE"` → la recibe un rol: **dentro de un paso de validación de un workflow** (`userTask`) es el `validatorRole` del paso; **en cualquier otro lugar** (p. ej. las tareas finales `SEND_CREATOR` / `SEND_USER`) es el rol indicado en `receiverRole`. `"USER"` → la recibe el **usuario que lanzó el workflow** (habitual en los avisos de aprobado/rechazado). Ver "Quién recibe una notificación" más abajo. |
| `notificationType` | `"ALERT"` o `"NOTICE"` | `"ALERT"` = alerta sobre la participación en un workflow; `"NOTICE"` = aviso informativo sobre algo que ha ocurrido |
| `receiverRole` | `name` del rol o `null` | `null` cuando `notificationReceiverType` es `"USER"`. Con `"ROLE"`: el `name` de `GET /gateway/api/portuno/api/filter/roles` cuando la notificación se envía fuera de un paso de validación; si la notificación se usa solo dentro de pasos de validación, el `validatorRole` del paso lo sobrescribe (pregunta al usuario qué valor espera su entorno en ese caso). |
| `severity` | `"HIGH"`, `"MEDIUM"`, `"LOW"` | Por defecto: `"MEDIUM"` si el usuario no especifica |
| `subject` | string clave de traducción | Propón una clave a partir del texto de asunto que quiere el usuario, p. ej. `NOTIFICATION.SUBJECT.ACTION.MUST-BE-VALIDATED`. Debe ser única entre las notificaciones. |
| `translationKey` | string clave de traducción | Propón una clave a partir del texto del cuerpo que quiere el usuario, p. ej. `NOTIFICATION.1.ROLE`. Debe ser única entre las notificaciones. |

**Para proponer claves**: derívalas del texto deseado por el usuario, en mayúsculas, separadas por puntos, con el prefijo `NOTIFICATION.SUBJECT.` para el asunto y `NOTIFICATION.` para el cuerpo. Comprueba primero las notificaciones existentes mediante `GET /gateway/api/portuno/api/filter/notifications` para evitar duplicados.

### Quién recibe una notificación

| Dónde la envía el workflow | `notificationReceiverType` | Quién la recibe |
|---|---|---|
| Dentro de un paso de validación (`notificationCode` de un `userTask`) | `ROLE` | El `validatorRole` del paso |
| Fuera de un paso de validación (p. ej. `SEND_CREATOR`, `SEND_USER`) | `ROLE` | El rol indicado en `receiverRole` |
| En cualquier lugar | `USER` | El usuario que lanzó el workflow |

Consecuencias al diseñar:
- Una notificación de "validación pendiente" (`ROLE`) se envía al rol que valida el paso, de modo que la misma notificación puede reutilizarse en pasos de distintos roles si el texto es genérico.
- Los avisos de aprobado/rechazado para el solicitante son `USER`.
- Para avisar a un rol concreto cuando termina un workflow (p. ej. la oficina de gobierno del dato cuando se aprueba un objeto), usa una notificación `ROLE` con ese `receiverRole` en la tarea final.
- Las tareas finales envían una notificación cada una; para avisar a más roles, añade nodos de notificación intermedios (`notify`) antes del final.

**Conserva el `id` de la notificación.** Anjana lo genera automáticamente al almacenar la notificación. Es el número que los workflows ponen en su campo `notificationCode` (ver `references/workflows.md`). Léelo de la respuesta del POST; si la respuesta no lo incluye, búscalo con `GET /gateway/api/portuno/api/filter/notifications` filtrando por la clave `subject` recién creada. Comunícaselo al usuario junto con el asunto.

### Paso 2: Crear las traducciones

Se necesitan dos traducciones en **todos los idiomas registrados** (no se puede dejar ninguna clave vacía: ver el paso 8 "Cobertura de traducciones" del "Flujo conversacional" y `internacionalizacion.md`):

1. **Traducción del asunto**: clave = valor usado en `subject`, valor = texto de asunto proporcionado por el usuario
2. **Traducción del cuerpo**: clave = valor usado en `translationKey`, valor = texto de cuerpo proporcionado por el usuario

**Versiones 25.1 y 25.2**: créalas con `POST <BASE_URL>/gateway/api/portuno/translations`. Ambas deben llevar `"internal": true` y `"language"` con el código del idioma destino. Después llama al endpoint de publicación (`PUT /gateway/public/v4/translations/upload`) para activarlas.

**Versión 26.1**: envía ambas claves en el mapa `values` de `POST <BASE_URL>/gateway/api/portuno/i18n/v1/submit` con `"action": "UPDATE"`, una entrada por idioma destino. No hay flag `internal` ni paso de publicación. Si la clave del asunto o del cuerpo ya tiene valor en un idioma destino, enviarla lo sobrescribe: aplica el protocolo de confirmación explícita.

```json
{
    "languages": {
        "es-ES": {
            "action": "UPDATE",
            "values": {
                "NOTIFICATION.SUBJECT.ACTION.MUST-BE-VALIDATED": "Acción pendiente de validación",
                "NOTIFICATION.1.ROLE": "Tiene una acción pendiente de validación"
            }
        }
    }
}
```

**Regla de sentence case** (todas las versiones): El valor de toda traducción de notificación debe estar en sentence case (primera letra en mayúscula, el resto en minúscula), salvo los tokens `#PLACEHOLDER#`, los nombres comerciales y las siglas, que conservan exactamente su capitalización. Aplica esto después de traducir (p. ej. `"AN ACTION IS PENDING YOUR VALIDATION"` → `"An action is pending your validation"`).

---

## Filtros de búsqueda (filterConfs)

Los filtros de búsqueda configuran qué atributos de metadatos aparecen como filtros en el Buscador (portal de búsqueda).

### Paso 1: Determinar la posición

Si el usuario no especifica una posición, busca la posición más alta existente entre los filterConfs con los mismos valores de `collection` y `main`, y súmale 1:

```bash
GET <BASE_URL>/gateway/api/portuno/api/filter/filterConfs
```

Filtra los resultados por `collection == "kerno"` y `main == <desired_main_value>`, extrae el valor de `position` más alto y usa `highest + 1`.

### Paso 2: Obtener el attributeDefinition

Recupera la definición del atributo para el que se configurará el filtro:

```bash
GET <BASE_URL>/gateway/api/portuno/api/filter/attributeDefinitions?nameContains=<name>
```

Extrae:
- `name`: se usa como `name` del filtro y para construir el `label`
- `type`: se usa para determinar el `type` del filtro (ver la tabla de mapeo más abajo)

### Paso 3: Crear el filtro

**Endpoint**: `POST <BASE_URL>/gateway/api/portuno/filterConfs`

**Body**:
```json
{
  "name": "<ATTRIBUTE_NAME_UPPERCASE>",
  "label": "FILTERS.<ATTRIBUTE_NAME_UPPERCASE>",
  "type": "<FILTER_TYPE>",
  "collection": "kerno",
  "pageName": null,
  "position": "<POSITION>",
  "main": true,
  "sortable": false
}
```

**Reglas de campos**:

| Campo | Reglas |
|---|---|
| `name` | El campo `name` del attributeDefinition convertido a **MAYÚSCULAS** (p. ej. `"DOMINIO"`) |
| `label` | `"FILTERS."` + `name` en MAYÚSCULAS (p. ej. `"FILTERS.DOMINIO"`) |
| `type` | Ver la tabla de mapeo más abajo |
| `collection` | Siempre `"kerno"` para filtros de búsqueda |
| `pageName` | Siempre `null` |
| `position` | La indicada por el usuario, o autocalculada (ver Paso 1), como string |
| `main` | `true` = se muestra por defecto en el portal de búsqueda; `false` = el usuario lo añade bajo demanda |
| `sortable` | Siempre `false` |

**Mapeo de tipo de filtro** (según el `type` del attributeDefinition):

| tipo(s) de attributeDefinition | `type` de filterConf |
|---|---|
| `INPUT_DATE`, `DATE_RANGE` | `INPUT_DATE_RANGE` |
| `INPUT_NUMBER`, `INPUT_DECIMAL`, `INPUT_INTEGER`, `NUMBER_RANGE` | `INPUT_NUMBER_RANGE` |
| `ENTITY_SEARCH`, `ARRAY_ENTITY`, `ENTITY`, `ENTITY_CONTAINER` | `ENTITY` |
| `SELECT_USERS`, `MULTI_USERS`, `INPUT_USER` | `SELECT_USERS` |
| `TREE_SELECT`, `TREE_MULTISELECT` | `MULTI_SELECT_TREE` |
| `SELECT_ORGANIZATIONAL_UNIT`, `MULTI_ORGANIZATIONAL_UNIT` | `MULTI_SELECT_TREE_OU` |
| `INPUT_CHECKBOX` | `BOOLEAN` |
| `SELECT`, `MULTI_SELECT`, `SELECT_IMG`, `MULTI_SELECT_IMG`, `SELECT_IMG_TXT`, `MULTI_SELECT_IMG_TXT` | `MULTI_SELECT` |

Si el tipo del atributo no figura en esta tabla (textos, arrays, ficheros, URL, `INPUT_RANGE`), no se conoce ningún tipo de filtro para él: díselo al usuario en lugar de adivinar uno.

### Paso 4: Crear las traducciones del label del filtro

El label del filtro necesita la clave `FILTERS.<ATTRIBUTE_NAME_UPPERCASE>` traducida en **cada idioma configurado**, con el mismo valor ya usado para el label del atributo.

**Versiones 25.1 y 25.2** (una llamada por idioma):

```bash
POST <BASE_URL>/gateway/api/portuno/translations
{
  "key": "FILTERS.<ATTRIBUTE_NAME_UPPERCASE>",
  "language": "<LANG_CODE>",
  "usedFor": null,
  "internal": true,
  "value": "<SAME_VALUE_AS_ATTRIBUTE_LABEL_TRANSLATION>"
}
```

Para obtener el `value` correcto de cada idioma: consulta las traducciones existentes del texto del **`label`** del attributeDefinition (la clave usada para las traducciones del label del atributo, no su `name`) mediante:

```bash
GET <BASE_URL>/gateway/api/portuno/api/filter/translations?keyEquals=<ATTRIBUTE_LABEL_URL_ENCODED>&internalEquals=false
```

**Versión 26.1** (una sola llamada `submit` que cubre todos los idiomas a la vez; si la clave `FILTERS.<NAME>` ya tiene valor en un idioma, esto lo sobrescribe: aplica el protocolo de confirmación explícita):

```bash
POST <BASE_URL>/gateway/api/portuno/i18n/v1/submit
{
  "languages": {
    "es-ES": {"action": "UPDATE", "values": {"FILTERS.DOMINIO": "Dominio"}},
    "en-US": {"action": "UPDATE", "values": {"FILTERS.DOMINIO": "Domain"}}
  }
}
```

Para obtener el valor correcto por idioma, lee las traducciones existentes del texto del **`label`** del attributeDefinition (la clave de las traducciones del label, no su `name`) con `POST <BASE_URL>/gateway/api/portuno/translations/v1/search` (paginando los resultados como se describe en `internacionalizacion.md`).

Usa el `value` de cada idioma como valor de traducción del label del filtro.

### Paso 5: Publicar las traducciones y limpiar la caché

**Publicar las traducciones** (**solo versiones 25.1 y 25.2**):
```bash
PUT <BASE_URL>/gateway/public/v4/translations/upload
Body: {"headers":{"normalizedNames":{},"lazyUpdate":null}}
```
En 26.1 `submit` ya las publicó: omite esta llamada.

**Limpiar la caché** (obligatorio tras configurar un filtro, **todas las versiones**):
```bash
PUT <BASE_URL>/gateway/api/v1/cache/clear-all
```

La publicación (donde aplique) y la limpieza de caché deben tener éxito ambas para que el filtro aparezca correctamente en la UI.

---
