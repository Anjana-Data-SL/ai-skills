# Anjana Data Platform - API Endpoints Reference

## Base Configuration

- **Base URL**: `<BASE_URL>` — the environment URL the user provides at session start (e.g. `https://<environment>.anjanadata.org`). Every endpoint below is relative to it.
- **Backend href prefix**: `<PORTUNO_HREF>` — the prefix of the hrefs returned in `_links.self.href` (everything before the resource name). How to obtain it, and when to build hrefs from the `id` (e.g. every `api/filter` response and `POST /roles` in 26.1 have no `_links`), is explained in `SKILL.md`, section "Environment".
- **Authentication**: `Authorization: Bearer <JWT_TOKEN>`
- **Content-Type**: `application/json`

---

## 1. Organizational Units (OUs)

### Endpoint

```
POST <BASE_URL>/gateway/api/portuno/organizationalUnits
```

### Request Body

```json
{
    "module": "ALL",
    "alias": "Seguros",
    "parent": null,
    "description": "Dominio sector seguros",
    "organizationalUnitType": "1"
}
```

### Field Rules

| Field | Value | Rules |
|-------|-------|-------|
| `module` | `"ALL"` | Always fixed to `"ALL"` |
| `alias` | String | Name of the OU. For multi-level hierarchies, concatenate levels with `/` (e.g., `"nivel1/nivel2/nivel3"`) |
| `parent` | `null` or href | `null` for level-1 OUs. For child OUs, use the href of the parent OU |
| `description` | String | Brief description in a few words |
| `organizationalUnitType` | String number | `"1"` for level 1, `"2"` for level 2, etc. Represents the hierarchy depth |

### Level 1 (top-level) OU

- `parent`: `null`
- `organizationalUnitType`: `"1"`
- `alias`: The OU name (e.g., `"Pharma"`)

**Example response**:
```json
{
    "id": 34,
    "description": "Dominio sector Pharma",
    "module": "ALL",
    "alias": "Pharma",
    "parent": null,
    "organizationalUnitType": "1",
    "identifierKey": "34-Pharma"
}
```

### Level 2 (child) OU

- `parent`: `<BASE_URL>/gateway/portuno/organizationalUnits/<PARENT_ID>` — ID from parent's `identifierKey`
- `organizationalUnitType`: `"2"`
- `alias`: Parent alias + `/` + child name (e.g., `"Pharma/compliances"`)
- `description`: Can be `null`

**Example body**:
```json
{
    "module": "ALL",
    "alias": "Pharma/compliances",
    "parent": "<BASE_URL>/gateway/portuno/organizationalUnits/34",
    "description": null,
    "organizationalUnitType": "2"
}
```

**Note**: The parent URL uses `/gateway/portuno/` (without `api/`), same pattern as userOURoles references.

---

## 2. Roles

### Endpoint

```
POST <BASE_URL>/gateway/api/portuno/roles
```

### Request Body

```json
{
    "module": "ALL",
    "name": "Custodio_de_datos",
    "isCross": false,
    "description": "Custodio de datos",
    "isDefault": false
}
```

### Field Rules

| Field | Value | Rules |
|-------|-------|-------|
| `module` | `"ALL"` | Always fixed to `"ALL"` |
| `name` | String | Sanitized version of the role name (see sanitization rules below) |
| `isCross` | Boolean | `true` only if the user explicitly says the role is "cross"; otherwise `false` |
| `description` | String | Original name as given by the user, with no character restrictions |
| `isDefault` | Boolean | **Always send it explicitly** (`true` only if the user confirms it is the default role). If omitted it is stored as `null`, which cannot be corrected through the API once users have the role — see SKILL.md, "Entity: Roles" |

### Name Sanitization Rules

Transform the user-provided name:
1. Replace spaces with `_`
2. Remove accents: á→a, é→e, í→i, ó→o, ú→u, Á→A, É→E, Í→I, Ó→O, Ú→U
3. Replace ñ→n, Ñ→N
4. Remove prohibited characters: `*`, `/`, and any non-alphanumeric character except `_`

**Examples:**
- "Custodio de datos" → `Custodio_de_datos`
- "Administrador/Gestor" → `AdministradorGestor`
- "Técnico señor" → `Tecnico_senor`

### Response (Important)

The response contains the role href needed for permission assignment:

```json
{
    "id": 16,
    "module": "ALL",
    "name": "Custodio_de_datos",
    "description": "Custodio de datos",
    "isCross": false,
    "identifierKey": "16-Custodio_de_datos-Custodio de datos",
    "_links": {
        "self": {
            "href": "<PORTUNO_HREF>/roles/16"
        },
        "role": {
            "href": "<PORTUNO_HREF>/roles/16"
        }
    }
}
```

**Extract `_links.self.href`** and retain it for permission creation. **In 26.1 the response has no `_links`** (verified): build the href as `<PORTUNO_HREF>/roles/<id>` with the `id` of the response.

---

## 3. Permissions

### Endpoint

```
POST <BASE_URL>/gateway/api/portuno/permissions
```

### Request Body

```json
{
    "action": "CREATION_MODIF",
    "subType": "DATASET",
    "role": "<PORTUNO_HREF>/roles/15"
}
```

### Field Rules

| Field | Value | Rules |
|-------|-------|-------|
| `action` | String KEY | Determined by the permission type. See `permissions-catalog.md` |
| `subType` | String KEY | `"ALL"` for general permissions, or the specific object subtype in uppercase |
| `role` | URL String | The full `_links.self.href` URL of the role to assign the permission to |

### Getting the Role href

- If the role was just created in this session, use the href from the creation response
- If the role already exists, ask the user to provide the role href URL
- Before creating the permission, verify the role with `GET <BASE_URL>/gateway/api/portuno/roles/<ROLE_ID>` (id = number at the end of the href). If it does not exist, do not create the permission. See "Entity: Permissions" in `SKILL.md`

For the complete catalog of permission types, see `references/permissions-catalog.md`.

---

## 4. Metadata Attribute Definitions

### Endpoint

```
POST <BASE_URL>/gateway/api/portuno/attributeDefinitions
```

### Request Body

```json
{
    "name": "encriptar",
    "type": "INPUT_CHECKBOX",
    "label": "Encriptar",
    "placeHolder": null,
    "shortDescription": null,
    "startDate": null,
    "lastModifiedDate": null,
    "description": "Indica si el campo debe estar encriptado por seguridad"
}
```

### Field Rules

| Field | Value | Rules |
|-------|-------|-------|
| `name` | String | Auto-generated from the label in camelCase format |
| `type` | String KEY | One of the 34 attribute type KEYs (see table below) |
| `label` | String | The attribute name as provided by the user |
| `placeHolder` | `null` | Always `null` |
| `shortDescription` | `null` | Always `null` |
| `startDate` | `null` | Always `null` |
| `lastModifiedDate` | `null` | Always `null` |
| `description` | String | Description provided by the user |

### camelCase Conversion Rules

Convert the user-provided label to camelCase for the `name` field:
1. Remove accents (á→a, é→e, etc.)
2. Split by spaces and special characters
3. First word lowercase, subsequent words capitalized
4. Remove non-alphanumeric characters

**Examples:**
- "Encriptar" → `encriptar`
- "Fecha de creación" → `fechaDeCreacion`
- "Nivel de confidencialidad" → `nivelDeConfidencialidad`
- "URL del recurso" → `urlDelRecurso`

### Reserved `name` values (forbidden)

Some identifiers are reserved by the Anjana platform for internal use and **must not** be used as the `name` of an `attributeDefinition` (any version):

| Reserved `name` | Reason | Replace with |
|---|---|---|
| `version` | Reserved for the platform's internal object versioning. Creating an attribute named `version` collides with the internal field. | `versionDelDocumento`, `versionDelInforme`, `versionDelPlan`, `versionPublicada`, etc. — disambiguate with the entity or the kind of version. |
| `status`, `estado` (and names or labels starting with them, e.g. `estadoDelProyecto`) | Collides with the native, non-editable status of every object. | `fase…`, `situacion…`, `avance…`, `vigencia…`, `etapa…`, `cumplimiento…`. |
| `name`, `description` and per-entity copies (`nombreDelSistema`, `descripcionDelIndicador`…) | Native global attributes: every entity uses the native `name` and `description`. | Reuse the native attributes (see SKILL.md, "MANDATORY baseline attributes"). |

When the camelCase conversion of the user's label produces one of these reserved names, do NOT auto-rename — ask the user for a more specific label first.

### Attribute Type Catalog

| KEY | Type Description |
|-----|-----------------|
| `INPUT_TEXT` | Simple text (no multi-language) |
| `INPUT_DATE` | Date picker |
| `INPUT_RANGE` | Numeric range (value between a range defined in metadata validations) |
| `INPUT_NUMBER` | Integer number |
| `SELECT` | Single-value selector from reference metadata |
| `TEXT_AREA` | Text area (no language selection) |
| `INPUT_CHECKBOX` | Boolean (checkbox) |
| `INPUT_DECIMAL` | Decimal number |
| `SELECT_USERS` | User selector |
| `MULTI_USERS` | Multi-user selector |
| `SELECT_ORGANIZATIONAL_UNIT` | Organizational unit selector |
| `MULTI_ORGANIZATIONAL_UNIT` | Multi organizational unit selector |
| `UPLOAD_FILE` | File upload |
| `UPLOAD_URL` | URL link |
| `ARRAY_NUMBER` | Array of integers |
| `ARRAY_DATE` | Array of dates |
| `ARRAY_DECIMAL` | Array of decimals |
| `ARRAY_BOOLEAN` | Array of booleans |
| `ARRAY_ALPHANUMERICAL` | Array of alphanumeric texts |
| `ARRAY_UPLOAD_FILE` | Array of files |
| `ARRAY_UPLOAD_URL` | Array of URLs |
| `MULTI_SELECT` | Multi-selector of reference metadata |
| `ARRAY_ENTITY` | Multi-selector of entities |
| `ENTITY_SEARCH` | Entity selector |
| `ENRICHED_TEXT_AREA` | Rich text |
| `ENRICHED_TEXT_AREA_INTERNATIONAL` | Rich text multi-language |
| `INPUT_TEXT_INTERNATIONAL` | Simple text multi-language |
| `TEXT_AREA_INTERNATIONAL` | Text area multi-language |
| `TREE_SELECT` | Taxonomy selector |
| `TREE_MULTISELECT` | Multi taxonomy selector |
| `SELECT_IMG_TXT` | Image with text selector |
| `MULTI_SELECT_IMG_TXT` | Multi image with text selector |
| `SELECT_IMG` | Image selector |
| `MULTI_SELECT_IMG` | Multi image selector |

---

## 5. Reference Values (attributeDefinitionValues)

### Endpoint

```
POST <BASE_URL>/gateway/api/portuno/attributeDefinitionValues
```

### Request Body

```json
{
    "value": "Platino",
    "attributeDefinition": "<PORTUNO_HREF>/attributeDefinitions/10222"
}
```

### Field Rules

| Field | Value | Rules |
|-------|-------|-------|
| `value` | String | The reference value text to add as a selectable option |
| `attributeDefinition` | URL String | The `_links.self.href` URL of an existing attribute definition of a selector type |

### Applicable Attribute Types

Reference values can only be created for attributes of these types:

| Type KEY | Description |
|----------|-------------|
| `SELECT` | Single-value selector |
| `MULTI_SELECT` | Multi-value selector |
| `SELECT_IMG_TXT` | Image with text selector |
| `MULTI_SELECT_IMG_TXT` | Multi image with text selector |
| `SELECT_IMG` | Image selector |
| `MULTI_SELECT_IMG` | Multi image selector |
| `TREE_SELECT` | Taxonomy selector |
| `TREE_MULTISELECT` | Multi taxonomy selector |

### Fetching Existing Selector Attributes

To find existing attributes by type, use:

```
GET <BASE_URL>/gateway/api/portuno/api/filter/attributeDefinitions?typeEquals=<TYPE>
```

Replace `<TYPE>` with one of the applicable types above (e.g., `SELECT`, `MULTI_SELECT`, etc.).

The response (26.1) is paginated in `content` (iterate `page` until `last` is `true`); each attribute has:
- `label`: The display name of the attribute
- `type`: The attribute type KEY
- `id`: build the URL for the `attributeDefinition` field as `<PORTUNO_HREF>/attributeDefinitions/<id>` (filter responses have no `_links`)

---

## 6. Taxonomy Hierarchy (attributeRelationShips)

### Endpoint

```
POST <BASE_URL>/gateway/api/portuno/attributeRelationShips
```

### Purpose

Defines parent-child relationships between reference values of a `TREE_SELECT` or `TREE_MULTISELECT` attribute, creating a navigable tree taxonomy.

### Request Body — Level 1 (root)

```json
{
    "destinationValue": "<PORTUNO_HREF>/attributeDefinitionValues/2035",
    "sourceValue": null,
    "objectSubType": null
}
```

### Request Body — Level 2+ (child)

```json
{
    "destinationValue": "<PORTUNO_HREF>/attributeDefinitionValues/2036",
    "sourceValue": "<PORTUNO_HREF>/attributeDefinitionValues/2035",
    "objectSubType": null
}
```

### Field Rules

| Field | Value | Rules |
|-------|-------|-------|
| `destinationValue` | URL String | The `_links.self.href` of the reference value being placed in the tree |
| `sourceValue` | URL String or `null` | `null` for root (level-1) values. For child values, the `_links.self.href` of the parent value |
| `objectSubType` | `null` | Always `null` for TREE_SELECT / TREE_MULTISELECT relationships |

---

## 7. Cross-Attribute Relationships (attributeRelationShips between different attributes)

### Endpoint

```
POST <BASE_URL>/gateway/api/portuno/attributeRelationShips
```

### Purpose

Links reference values between two different SELECT or MULTI_SELECT attributes. Used for pre-filtering: when a value is selected in the source attribute, only related values are shown in the destination attribute. Requires a DEPENDS_ON validation to be active in the UI.

### Request Body

```json
{
    "destinationValue": "<PORTUNO_HREF>/attributeDefinitionValues/58",
    "sourceValue": "<PORTUNO_HREF>/attributeDefinitionValues/8",
    "objectSubType": null
}
```

### Field Rules

| Field | Value | Rules |
|-------|-------|-------|
| `destinationValue` | URL String | The `_links.self.href` of a reference value in the destination (dependent) attribute |
| `sourceValue` | URL String | The `_links.self.href` of a reference value in the source (driving) attribute |
| `objectSubType` | `null` or subtype `name` | `null` if the relationship applies to all entities/relations; the `name` of an objectSubType to limit it to that one (see SKILL.md, "Cross-Attribute Relationships") |

### Building hrefs from IDs

If only the numeric ID is known, build the href as:
`<PORTUNO_HREF>/attributeDefinitionValues/<ID>`

---

## 8. Object SubTypes (Entities / Assets)

### Endpoint

```
POST <BASE_URL>/gateway/api/portuno/objectSubTypes
```

### Request Body

```json
{
    "name": "SISTEMA_ORIGEN",
    "module": "BG",
    "typeObject": "ENTITY",
    "activateWorkflow": "AUTO",
    "createWorkflow": "AUTO",
    "deactivateWorkflow": "AUTO",
    "modifyWorkflow": "AUTO",
    "transferWorkflow": "AUTO",
    "deprecateWorkflow": "AUTO",
    "wfRoleDependent": false,
    "parental": false
}
```

### Field Rules

| Field | Value | Rules |
|-------|-------|-------|
| `name` | String (UPPERCASE) | Entity name in UPPERCASE. No spaces (use `_`), no `:`, `,`, `#`, `(`, `)` |
| `module` | `"DC"` or `"BG"` | `"DC"` for DATASET, DSA, PROCESS, INSTANCE, SOLUTION. `"BG"` for others (default) |
| `typeObject` | `"ENTITY"` | Always `"ENTITY"` |
| `activateWorkflow` | String | Workflow identifier (e.g., `"AUTO"`) |
| `createWorkflow` | String | Workflow identifier |
| `deactivateWorkflow` | String | Workflow identifier |
| `modifyWorkflow` | String | Workflow identifier |
| `transferWorkflow` | String | Workflow identifier |
| `deprecateWorkflow` | String | Workflow identifier |
| `wfRoleDependent` | Boolean | `false` by default. `true` only if user requests it |
| `parental` | Boolean | Always `false` for entities |

---

## 9. Relationships (objectSubTypes with typeObject RELATIONSHIP)

### Endpoint

```
POST <BASE_URL>/gateway/api/portuno/objectSubTypes
```

### Purpose

Defines relationship types between entities, enabling entity-relationship modeling in the platform.

### Request Body

```json
{
    "name": "CONSUME",
    "module": "BG",
    "typeObject": "RELATIONSHIP",
    "activateWorkflow": "AUTO",
    "createWorkflow": "AUTO",
    "deactivateWorkflow": "AUTO",
    "modifyWorkflow": "AUTO",
    "transferWorkflow": "AUTO",
    "deprecateWorkflow": "AUTO",
    "wfRoleDependent": false,
    "parental": false
}
```

### Field Rules

| Field | Value | Rules |
|-------|-------|-------|
| `name` | String (UPPERCASE) | Relationship name in UPPERCASE. No spaces (use `_`), no `:`, `,`, `#`, `(`, `)` |
| `module` | `"BG"` or `"DC"` | Follows the entities it connects: `"DC"` for data-catalog entities, `"BG"` otherwise (default) |
| `typeObject` | `"RELATIONSHIP"` | Always `"RELATIONSHIP"` |
| `activateWorkflow` | String | Workflow identifier (e.g., `"AUTO"`) |
| `createWorkflow` | String | Workflow identifier |
| `deactivateWorkflow` | String | Workflow identifier |
| `modifyWorkflow` | String | Workflow identifier |
| `transferWorkflow` | String | Workflow identifier |
| `deprecateWorkflow` | String | Workflow identifier |
| `wfRoleDependent` | Boolean | `false` by default. `true` only if user requests it |
| `parental` | Boolean | `false` by default. `true` if the relationship acts as aggregation in lineage layers |
