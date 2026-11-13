## Entidad: Menús

**Endpoint**: `POST /gateway/api/portuno/menus`

Cada entidad o relación debe tener al menos un menú. Un menú pertenece exclusivamente a una entidad o relación y no se comparte.

### Recopilar del usuario

- **Nombre del menú**
- **Orden**: posición en la que se muestra el menú en el detalle de la entidad/relación (empieza en `"1"`)
- **Entidad/Relación**: a qué entidad o relación pertenece este menú
- **Descripción** (opcional): si no se proporciona, pregunta al usuario si quiere rellenarla o dejarla como `null`

### Construir el body

- `name`: nombre del menú tal como se proporcionó
- `order`: `"1"` o la posición proporcionada por el usuario (string)
- `subType`: href a la entidad o relación. Lógica:
  1. Si la entidad/relación se acaba de crear en esta sesión, usa el href de su respuesta POST
  2. Si no: GET `<BASE_URL>/gateway/api/portuno/api/filter/objectSubTypes?nameContains=<name>` y construye su href como `<PORTUNO_HREF>/objectSubTypes/<id>` (la respuesta del filtro no tiene `_links`)
  3. Si el GET devuelve más de un resultado, pide al usuario que aclare
- `description`: descripción proporcionada por el usuario, o `null` (mantenla por debajo de unos ~250 caracteres: los textos más largos han sido rechazados con HTTP 500)

**Ejemplo de body**:
```json
{
    "name": "General",
    "order": "1",
    "subType": "<SUBTYPE_HREF>",
    "description": "Datos generales del sistema"
}
```

**Importante**: Conserva el `_links.self.href` de la respuesta: es necesario para crear secciones dentro de este menú.

## Entidad: Secciones

**Endpoint**: `POST /gateway/api/portuno/sections`

Cada menú debe tener al menos una sección. Las secciones pertenecen a un menú concreto de una entidad o relación.

### Recopilar del usuario

- **Nombre de la sección**
- **Orden**: posición dentro del menú (empieza en `"1"`)
- **Menú**: a qué menú pertenece esta sección
- **Descripción** (opcional): si no se proporciona, pregunta al usuario si quiere rellenarla o dejarla como `null`

### Construir el body

- `name`: nombre de la sección tal como se proporcionó
- `order`: `"1"` o la posición proporcionada por el usuario (string)
- `menu`: href al menú. Lógica:
  1. Si el menú se acaba de crear en esta sesión, usa el href de su respuesta POST
  2. Si no:
     - GET del ID de la entidad/relación: `GET <BASE_URL>/gateway/api/portuno/api/filter/objectSubTypes?nameContains=<name>`
     - GET de los menús de esa entidad: `GET <BASE_URL>/gateway/api/portuno/api/filter/menus?subTypeEquals=<ID>`, y construye el href del menú como `<PORTUNO_HREF>/menus/<id>`
     - Si algún GET devuelve más de un resultado, pide al usuario que aclare cuál
- `description`: descripción proporcionada por el usuario, o `null` (mantenla por debajo de unos ~250 caracteres: los textos más largos han sido rechazados con HTTP 500)

**Ejemplo de body**:
```json
{
    "name": "Calidad del dato",
    "order": "1",
    "menu": "<MENU_HREF>",
    "description": "Reglas de calidad aplicables"
}
```

**Importante**: Conserva el `_links.self.href` de la respuesta: es necesario para asignar atributos de metadatos a esta sección.

## Entidad: Template Attributes (asignar metadatos a las secciones)

**Endpoint**: `POST /gateway/api/portuno/templateAttributes`

Los template attributes asignan una definición de atributo de metadatos a una sección de un menú de una entidad o relación.

### Recopilar del usuario

- **Atributo**: qué definición de atributo asignar
- **Sección**: a qué sección asignarlo
- **Orden** (`sort`): posición dentro de la sección (los atributos base nativos ocupan las primeras posiciones, empezando en `"0"`: ver "OBLIGATORIO: atributos base de toda entidad Y relación" en subtipos-objeto-y-relaciones.md; los atributos de dominio van después)
- **Activo**: siempre `true` salvo que el usuario pida explícitamente que esté inactivo
- **Visible** (`isVisible`): solo `true` si se cumplen ambas condiciones: (1) la entidad es `DATASET_FIELD`, y (2) el usuario pide explícitamente visibilidad en la pestaña "Estructura". En caso contrario, `false`.

### Construir el body

- `sort`: `"1"` o la posición proporcionada por el usuario (string)
- `attributeDefinition`: href a la definición de atributo. Lógica:
  1. Si el atributo se acaba de crear en esta sesión, usa el href de su respuesta POST
  2. Si no, busca por label: `GET <BASE_URL>/gateway/api/portuno/api/filter/attributeDefinitions?labelContains=<label>`
  3. O por nombre: `GET <BASE_URL>/gateway/api/portuno/api/filter/attributeDefinitions?nameContains=<name>`
  4. Si hay más de un resultado, pide al usuario que confirme
- `section`: href a la sección. Lógica:
  1. Si la sección se acaba de crear en esta sesión, usa el href de su respuesta POST
  2. Si no: `GET <BASE_URL>/gateway/api/portuno/api/filter/sections?page=0&size=20&sequenceOrder=id&idOrder=desc&menuEquals=<MENU_ID>&nameContains=<section_name>`
- `active`: `true` por defecto
- `isVisible`: `false` por defecto; `true` solo en las condiciones indicadas arriba

**Ejemplo de body**:
```json
{
    "sort": "1",
    "attributeDefinition": "<ATTRIBUTE_DEFINITION_HREF>",
    "section": "<SECTION_HREF>",
    "active": true,
    "isVisible": false
}
```

**Importante**: Conserva el `_links.self.href` de la respuesta: es necesario para configurar validaciones sobre este template attribute.

## Entidad: Template Attribute Validations

**Endpoint**: `POST /gateway/api/portuno/templateAttributeValidations`

Las validaciones se aplican a un template attribute (un atributo ya asignado a una sección). El href de `templateAttribute` debe provenir de la respuesta POST de la creación del template attribute, o recuperarse mediante GET si no está disponible.

### Obtener el href del templateAttribute (si no está disponible en la sesión)

```bash
curl -s "<BASE_URL>/gateway/api/portuno/templateAttributes" \
  -H @"<AUTH_HEADER_FILE>" \
  -H "Content-Type: application/json"
```

Extrae el href de `_links.self.href` del template attribute que coincida.

### Tipos de validación

| key | params | Aplicable a |
|---|---|---|
| `REQUIRED` | `"true"` | Cualquier tipo de atributo **EXCEPTO `INPUT_CHECKBOX`**: ver la regla más abajo |
| `MAX` | valor entero (string) | Entero, decimal |
| `MIN` | valor entero (string) | Entero, decimal |
| `MAX_DECIMAL_PRECISION` | valor entero (string) | Decimal |
| `MIN_DECIMAL_PRECISION` | valor entero (string) | Decimal |
| `MAX_LENGTH` | valor entero (string) | Tipos de texto |
| `MIN_LENGTH` | valor entero (string) | Tipos de texto |
| `MAX_LENGTH_ARRAY` | valor entero (string) | Tipos array |
| `MIN_LENGTH_ARRAY` | valor entero (string) | Tipos array |
| `NOT_EDITABLE` | `"true"` | Cualquier tipo de atributo |
| `HERITABLE` | `name` de la definición de atributo origen | Solo booleano |
| `DEPENDS_ON` | `name` de la definición de atributo origen | **Solo tipos SELECT / MULTI_SELECT**: ver la regla estricta más abajo |
| `SUBTYPE_FILTER` | Uno o varios nombres de `objectSubType` separados por `_-` | Solo `ENTITY_SEARCH` / `ARRAY_ENTITY`: restringe qué subtipos de entidad se pueden seleccionar. **Obligatoria en TODO atributo de estos dos tipos** (en entidades Y en relaciones). El diseño debe declarar los subtipos de destino válidos. |

### IMPORTANTE: reglas de validación que NUNCA se deben incumplir (todas las versiones)

- **`REQUIRED` + `INPUT_CHECKBOX` está prohibido.** Un checkbox siempre lleva un valor (`true` o `false`), así que una comprobación "obligatorio" nunca puede fallar. Anjana almacena la validación pero la interfaz la ignora, lo que genera confusión. **Si necesitas forzar que el usuario confirme algo de forma activa, modélalo como un `SELECT` con valores como `Sí` / `No` y aplica `REQUIRED` a ese SELECT.** Esta regla se aplica a las versiones 25.1, 25.2 y 26.1.
- **`MAX` / `MIN` / `MAX_DECIMAL_PRECISION` / `MIN_DECIMAL_PRECISION` son SOLO para tipos numéricos: regla estricta, todas las versiones**. Tipos válidos: `INPUT_NUMBER`, `INPUT_DECIMAL`, `INPUT_RANGE`. La plataforma acepta el POST en silencio sobre cualquier otro tipo (TEXT_AREA, INPUT_TEXT, INPUT_CHECKBOX, ENTITY_SEARCH, SELECT…) y almacena la validación, pero **la interfaz la ignora**: no se ejecuta ninguna comprobación real de mín/máx. Resultado: una validación huérfana que induce a error a los auditores.

  **Comprobación previa (obligatoria) antes de hacer POST de cualquier MIN/MAX/MIN_DECIMAL_PRECISION/MAX_DECIMAL_PRECISION**: resuelve `templateAttribute → attributeDefinition.type` a partir del registro (o mediante GET si no está en caché). Si el tipo no es uno de `{INPUT_NUMBER, INPUT_DECIMAL, INPUT_RANGE}`, **NO hagas el POST**. Avisa al usuario y sugiere una de estas opciones:
  - Cambiar el tipo del atributo a `INPUT_NUMBER`/`INPUT_DECIMAL` si el campo realmente representa un número (error típico: un "número de registros" o "edad" modelado como TEXT_AREA; remodelarlo como INPUT_NUMBER con MIN=0).
  - Eliminar la declaración MIN/MAX del diseño y hacer cumplir la restricción de forma operativa (a nivel de proceso), no a nivel de plataforma.

  Al revisar una plataforma existente con validaciones MIN/MAX incorrectas, lístalas con `GET /api/filter/templateAttributeValidations?keyEquals=MIN&page=0&size=500` (y lo mismo para `MAX`, `MIN_DECIMAL_PRECISION`, `MAX_DECIMAL_PRECISION`), inspecciona el `templateAttribute.attributeDefinition.type` de cada una y **borra las que no sean de tipo numérico** con `DELETE /templateAttributeValidations/<templateAttribute_id>-<KEY>` (patrón de URL de clave compuesta, igual que en la limpieza de DEPENDS_ON). **Solo después del protocolo de confirmación explícita** ("Operaciones que modifican o borran"): muestra la lista de validaciones a borrar y espera la confirmación explícita del usuario.

- **`MAX_LENGTH` / `MIN_LENGTH` son SOLO para tipos de texto: regla estricta, todas las versiones**. Tipos válidos: `INPUT_TEXT`, `TEXT_AREA`, `INPUT_TEXT_INTERNATIONAL`, `TEXT_AREA_INTERNATIONAL`, `ENRICHED_TEXT_AREA`, `ENRICHED_TEXT_AREA_INTERNATIONAL`, `ARRAY_ALPHANUMERICAL`. Aplica la misma comprobación previa de tipo que para MIN/MAX antes de hacer POST: aborta si el tipo no está en este conjunto. El procedimiento de limpieza es idéntico, incluido el protocolo de confirmación explícita: `DELETE /templateAttributeValidations/<templateAttribute_id>-MAX_LENGTH` (o `-MIN_LENGTH`).

- **`MAX_LENGTH_ARRAY` / `MIN_LENGTH_ARRAY` son SOLO para tipos array** (`ARRAY_NUMBER`, `ARRAY_DATE`, `ARRAY_DECIMAL`, `ARRAY_BOOLEAN`, `ARRAY_ALPHANUMERICAL`, `ARRAY_UPLOAD_FILE`, `ARRAY_UPLOAD_URL`, `ARRAY_ENTITY`, `MULTI_SELECT`, `MULTI_SELECT_IMG_TXT`, `MULTI_SELECT_IMG`, `MULTI_USERS`, `MULTI_ORGANIZATIONAL_UNIT`, `TREE_MULTISELECT`). Aplica la misma comprobación previa de tipo; aborta si no es de cardinalidad array.

- **`HERITABLE` es SOLO para tipos `INPUT_CHECKBOX`: regla estricta.** Hereda un valor booleano de un atributo de la entidad padre. La plataforma acepta el POST en tipos no booleanos, pero la herencia no se ejecuta. Comprobación previa: aborta si `attributeDefinition.type != INPUT_CHECKBOX`.

#### Patrón genérico de comprobación previa para validaciones restringidas por tipo

Antes de hacer POST de **cualquier** validación cuya key esté en `{MIN, MAX, MIN_DECIMAL_PRECISION, MAX_DECIMAL_PRECISION, MIN_LENGTH, MAX_LENGTH, MIN_LENGTH_ARRAY, MAX_LENGTH_ARRAY, HERITABLE, DEPENDS_ON, SUBTYPE_FILTER}`:

1. Resuelve el `attributeDefinition.type` del template attribute de destino (búscalo en el registro o con `GET /templateAttributes/<id>`).
2. Comprueba que el tipo está en la lista de tipos permitidos de la validación (ver la tabla de arriba).
3. Si NO lo está, **aborta el POST** y emite un aviso claro al usuario que identifique: la entidad, la sección, el atributo, la key de validación declarada, el tipo real y los tipos permitidos. Sugiere una corrección (cambiar el tipo o descartar la validación).
4. No envíes nunca el POST en silencio esperando que la plataforma lo haga cumplir: la API de Anjana acepta sin error la mayoría de las validaciones con tipo incompatible, pero la interfaz las ignora.

Esta comprobación previa es obligatoria en **todo** bucle de creación de validaciones (atributo individual, script por lotes, parser de documento de diseño). En caso de duda, vuelca e inspecciona antes de enviar.
- **`DEPENDS_ON` es SOLO para tipos `SELECT` y `MULTI_SELECT`: regla estricta, todas las versiones**. La plataforma almacena la validación si haces POST sobre `INPUT_CHECKBOX`, `INPUT_TEXT`, `TEXT_AREA`, `ENTITY_SEARCH`, `UPLOAD_FILE` o cualquier otro tipo que no sea selector, pero **la interfaz la ignora**: en realidad no oculta ni muestra de forma condicional el atributo dependiente. Resultado: una validación huérfana que confunde a los auditores y no produce ningún comportamiento.

  **Si un diseño de origen (p. ej., un documento de metamodelo) declara `DEPENDS_ON` sobre un atributo que no es selector** (error típico: hacer que un TEXT_AREA dependa de un flag INPUT_CHECKBOX como "Contiene datos personales"), aplica en su lugar esta solución alternativa:
  - Sustituye el atributo padre por un `SELECT` (p. ej., `tipoDeDatos` con valores `Personales`/`Sensibles`/`Anónimos`...) y aplica DEPENDS_ON en los hijos apuntando a ese SELECT.
  - O, más simple si la marca binaria es la única señal relevante, acepta que la lógica condicional debe hacerse cumplir de forma operativa (en el proceso, no a nivel de plataforma): descarta la declaración DEPENDS_ON y avisa al usuario de que se ha omitido.

  Al revisar una plataforma existente con validaciones DEPENDS_ON incorrectas, lístalas con `GET /api/filter/templateAttributeValidations?keyEquals=DEPENDS_ON&page=0&size=500`, inspecciona el `templateAttribute.attributeDefinition.type` de cada una y **borra las que no tengan un tipo en `{SELECT, MULTI_SELECT}`** con `DELETE /templateAttributeValidations/<templateAttribute_id>-DEPENDS_ON` (patrón de URL de clave compuesta). **Solo después del protocolo de confirmación explícita** ("Operaciones que modifican o borran").
- Tampoco apliques DEPENDS_ON a `TREE_SELECT`/`TREE_MULTISELECT`: esos usan el mecanismo de jerarquía de taxonomías (`attributeRelationShips` padre-hijo) en lugar de DEPENDS_ON.
- `SUBTYPE_FILTER` es solo para `ENTITY_SEARCH` / `ARRAY_ENTITY`: restringe qué subtipos de entidad se pueden referenciar. **Siempre obligatoria en TODO atributo de estos dos tipos**, tanto si el atributo está en una entidad como en una relación. Sin ella el usuario podría seleccionar cualquier tipo de entidad, lo que corrompe el modelo de datos. `params` es uno o varios nombres de `objectSubType` separados por `_-`. Ejemplo: `params="INFORME_-INDICADOR"` permite dos tipos de origen.

**Al diseñar un atributo de tipo `ENTITY_SEARCH` o `ARRAY_ENTITY`** (ya sea en una entidad o en una relación), el diseño DEBE declarar qué `objectSubType(s)` son válidos como referencia. Mapea esa declaración directamente al `SUBTYPE_FILTER.params` del templateAttribute. Ejemplos:
- APLICACION `datasetsUtilizados` (ARRAY_ENTITY) → `SUBTYPE_FILTER=DATASET`
- INFORME `indicadorPrincipal` (ENTITY_SEARCH) → `SUBTYPE_FILTER=INDICADOR`
- INDICADOR `terminoDeNegocio` (ENTITY_SEARCH) → `SUBTYPE_FILTER=TERMINO_NEGOCIO`
- APLICACION `sistemasOrigen` (ARRAY_ENTITY) → `SUBTYPE_FILTER=SISTEMA_ORIGEN`
- `source` de una relación (ENTITY_SEARCH) → el SUBTYPE_FILTER es el tipo de entidad de origen de esa relación
- `destination` de una relación (ENTITY_SEARCH) → el SUBTYPE_FILTER es el tipo de entidad de destino

Si un diseño de origen (p. ej., un documento de metamodelo) declara `REQUIRED` sobre un `INPUT_CHECKBOX`, **descarta esa validación** (no la envíes) y avisa al usuario de que se ha omitido porque los checkbox no pueden ser obligatorios.

### Obtener el `name` de la definición de atributo (necesario para HERITABLE y DEPENDS_ON)

```bash
curl -s "<BASE_URL>/gateway/api/portuno/templateAttributes" \
  -H @"<AUTH_HEADER_FILE>" \
  -H "Content-Type: application/json"
```

Localiza el template attribute y extrae el campo `name` de su objeto `attributeDefinition`.

### Construir el body

```json
{
    "templateAttribute": "<TEMPLATE_ATTRIBUTE_HREF>",
    "key": "<VALIDATION_KEY>",
    "params": "<VALUE>"
}
```

### DEPENDS_ON: paso adicional obligatorio

Al configurar una validación `DEPENDS_ON`, también debes crear `attributeRelationShips` entre los valores de los dos atributos (ver taxonomias-y-relaciones.md, sección de relaciones entre atributos). La validación `DEPENDS_ON` activa el filtrado en la interfaz; los `attributeRelationShips` definen qué pares de valores concretos quedan vinculados.

- `templateAttribute`: href del atributo **destino** (aquel cuyos valores se van a filtrar)
- `params`: `name` de la definición de atributo **origen** (el que dirige el filtrado)
