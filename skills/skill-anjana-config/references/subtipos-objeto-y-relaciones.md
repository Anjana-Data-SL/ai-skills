## Entidad: Object SubTypes (Entidades / Assets)

**Endpoint**: `POST /gateway/api/portuno/objectSubTypes`

Los Object SubTypes definen los tipos de assets (entidades) que se pueden gestionar en la plataforma (ej: "SISTEMA_ORIGEN", "APLICACION", etc.).

### Recopilar del usuario

- **Nombre de la entidad**: El nombre para el tipo de entidad. Se convertirá a mayúsculas, sin espacios ni caracteres especiales (`:`, `,`, `#`, `(`, `)` están prohibidos).
- **Módulo**: Pregúntalo al usuario. Usa `"DC"` para las entidades estándar del catálogo de datos (DATASET, DSA, PROCESS, INSTANCE, SOLUTION). Para el resto, usa `"BG"` por defecto salvo que el usuario indique lo contrario.
- **Identificador(es) de workflow**: Pide al usuario el ID de workflow. Si proporciona uno, úsalo para los 6 campos de workflow. Si quiere IDs distintos por workflow, recopílalos todos. El ID es `AUTO` (sin validación) o el `id` de un workflow BPMN ya desplegado en el entorno (ver workflows-bpmn.md); si el workflow todavía no existe, genéralo primero.
- **wfRoleDependent**: Por defecto `false`. Ponlo a `true` solo si el usuario lo pide explícitamente.

### Construir el body

- `name`: Nombre proporcionado por el usuario, convertido a MAYÚSCULAS. Sustituye espacios por `_`. Elimina caracteres prohibidos (`:`, `,`, `#`, `(`, `)`).
- `module`: `"DC"` o `"BG"` (ver reglas arriba)
- `typeObject`: Siempre `"ENTITY"`
- `activateWorkflow`: Identificador de workflow proporcionado por el usuario
- `createWorkflow`: Mismo identificador de workflow (u otro distinto si se especificó)
- `deactivateWorkflow`: Mismo identificador de workflow (u otro distinto si se especificó)
- `modifyWorkflow`: Mismo identificador de workflow (u otro distinto si se especificó)
- `transferWorkflow`: Mismo identificador de workflow (u otro distinto si se especificó)
- `deprecateWorkflow`: Mismo identificador de workflow (u otro distinto si se especificó)

**Qué va en los seis campos de workflow**: el identificador del workflow es **el `id` del elemento `<process>` del fichero BPMN desplegado** (por ejemplo, para `<process id="GENERIC_TEMPLATE_2_VALIDATION_STEPS" …>` el valor es `"GENERIC_TEMPLATE_2_VALIDATION_STEPS"`) o `"AUTO"` si no hay validación. Cada campo controla qué workflow se ejecuta en una operación sobre objetos de este subtipo:

| Campo | Operación |
|---|---|
| `createWorkflow` | Creación |
| `modifyWorkflow` | Modificación |
| `activateWorkflow` | Activación |
| `deactivateWorkflow` | Desactivación |
| `transferWorkflow` | Transferencia |
| `deprecateWorkflow` | Deprecación |

Reglas: copia el id del proceso exactamente (distingue mayúsculas y minúsculas, sin el sufijo `.bpmn20.xml`); el workflow debe estar desplegado en el entorno antes de crear el objectSubType; operaciones distintas pueden usar workflows distintos (típico: validación en crear/modificar/deprecar y `AUTO` en el resto): pregunta al usuario por operación cuando quiera más de uno; si no se conoce el id del proceso, abre el `.bpmn20.xml` y lee `<process id="…">`.
- `wfRoleDependent`: `false` por defecto
- `parental`: Siempre `false`

### Reglas de saneamiento del nombre

Transforma el nombre proporcionado por el usuario:
1. Conviértelo a MAYÚSCULAS
2. Sustituye los espacios por `_`
3. Elimina los caracteres prohibidos: `:`, `,`, `#`, `(`, `)`

**Ejemplos:**
- "Sistema origen" → `SISTEMA_ORIGEN`
- "Aplicación (v2)" → `APLICACION_V2`
- "Data: Source" → `DATA_SOURCE`

### Ejemplo de body

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

> **OBLIGATORIO tras crear una entidad**: toda entidad debe incluir el atributo global nativo cuyo `name` es `"name"` (`INPUT_TEXT`, label `"Nombre"`) con sort=0 en la primera sección, con las validaciones `REQUIRED` + `NOT_EDITABLE`. El id de este atributo es **específico de cada entorno**: búscalo siempre con `nameEquals=name` en la plataforma de destino; NO escribas el id a mano. Consulta la sección "OBLIGATORIO: atributos base de toda entidad Y relación" más abajo (dentro de Entidad: Relaciones) para la regla completa.

## Entidad: Relaciones (objectSubTypes con typeObject RELATIONSHIP)

**Endpoint**: `POST /gateway/api/portuno/objectSubTypes`

Las relaciones definen los tipos de conexiones entre entidades, lo que permite un modelo entidad-relación en la plataforma.

### Recopilar del usuario

- **Nombre de la relación**: El nombre para el tipo de relación. Se convertirá a MAYÚSCULAS, sin espacios ni caracteres especiales (`:`, `,`, `#`, `(`, `)` están prohibidos).
- **Identificador(es) de workflow**: Pide al usuario el ID de workflow. Si proporciona uno, úsalo para los 6 campos de workflow. Si quiere IDs distintos por workflow, recopílalos todos. El ID es `AUTO` (sin validación) o el `id` de un workflow BPMN ya desplegado en el entorno (ver workflows-bpmn.md); si el workflow todavía no existe, genéralo primero.
- **wfRoleDependent**: Por defecto `false`. Ponlo a `true` solo si el usuario lo pide explícitamente.
- **parental**: Por defecto `false`. Ponlo a `true` solo si el usuario quiere que esta relación actúe como relación de agregación en las capas de lineage.

### Construir el body

- `name`: Nombre proporcionado por el usuario, convertido a MAYÚSCULAS. Sustituye espacios por `_`. Elimina caracteres prohibidos (`:`, `,`, `#`, `(`, `)`).
- `module`: sigue a las entidades que conecta la relación: `"DC"` cuando conecta entidades del catálogo de datos (`DC`), `"BG"` en cualquier otro caso (por defecto). Si las entidades conectadas pertenecen a módulos distintos, pregunta al usuario
- `typeObject`: Siempre `"RELATIONSHIP"`
- `activateWorkflow`: Identificador de workflow proporcionado por el usuario
- `createWorkflow`: Mismo identificador de workflow (u otro distinto si se especificó)
- `deactivateWorkflow`: Mismo identificador de workflow (u otro distinto si se especificó)
- `modifyWorkflow`: Mismo identificador de workflow (u otro distinto si se especificó)
- `transferWorkflow`: Mismo identificador de workflow (u otro distinto si se especificó)
- `deprecateWorkflow`: Mismo identificador de workflow (u otro distinto si se especificó)

**Qué va en los seis campos de workflow**: el identificador del workflow es **el `id` del elemento `<process>` del fichero BPMN desplegado** (por ejemplo, para `<process id="GENERIC_TEMPLATE_2_VALIDATION_STEPS" …>` el valor es `"GENERIC_TEMPLATE_2_VALIDATION_STEPS"`) o `"AUTO"` si no hay validación. Cada campo controla qué workflow se ejecuta en una operación sobre objetos de este subtipo:

| Campo | Operación |
|---|---|
| `createWorkflow` | Creación |
| `modifyWorkflow` | Modificación |
| `activateWorkflow` | Activación |
| `deactivateWorkflow` | Desactivación |
| `transferWorkflow` | Transferencia |
| `deprecateWorkflow` | Deprecación |

Reglas: copia el id del proceso exactamente (distingue mayúsculas y minúsculas, sin el sufijo `.bpmn20.xml`); el workflow debe estar desplegado en el entorno antes de crear el objectSubType; operaciones distintas pueden usar workflows distintos (típico: validación en crear/modificar/deprecar y `AUTO` en el resto): pregunta al usuario por operación cuando quiera más de uno; si no se conoce el id del proceso, abre el `.bpmn20.xml` y lee `<process id="…">`.
- `wfRoleDependent`: `false` por defecto
- `parental`: `false` por defecto. `true` si el usuario quiere agregación en las capas de lineage.

### Ejemplo de body

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

### OBLIGATORIO: atributos base de toda entidad Y relación (todas las versiones)

Todo `objectSubType` (tanto `ENTITY` como `RELATIONSHIP`) **debe incluir el atributo global nativo cuyo `name` es `"name"`** (`INPUT_TEXT`, label `"Nombre"`) con sort=0 y las validaciones `REQUIRED` + `NOT_EDITABLE`. Sin él, las plantillas Excel de carga masiva de la plataforma carecen de la columna "Nombre" y la interfaz no puede mostrar las instancias de entidad/relación con un nombre canónico.

**Regla crítica sobre los IDs**: los atributos globales nativos de la plataforma (`name`, `source`, `destination`, `description`) tienen **IDs numéricos específicos de cada entorno**: varían entre instalaciones de Anjana. No escribas nunca un id a mano. Resuelve siempre el id en tiempo de ejecución consultando `GET /api/portuno/api/filter/attributeDefinitions?nameEquals=<attr_name>&page=0&size=20` y leyendo `content[0].id`. Construye el href manualmente como `<PORTUNO_HREF>/attributeDefinitions/<id>`.

Además, las **relaciones** deben incluir 3 atributos base más: `source`, `destination`, `description`.

#### Para ENTIDADES (`typeObject = "ENTITY"`)

| Nombre del atributo | Label | Tipo | Sort | Validaciones | Origen |
|----------------|-------|------|------|-------------|--------|
| `name` | Nombre | `INPUT_TEXT` | `"0"` | `REQUIRED` + `NOT_EDITABLE` | **Global nativo**: búscalo con `nameEquals=name` para resolver su id (varía según el entorno). Reutilízalo siempre; nunca lo recrees. |
| `description` | Descripción | `TEXT_AREA` o `ENRICHED_TEXT_AREA_INTERNATIONAL` (el que tenga la plataforma) | `"1"` | Según lo requiera el diseño (ej. `REQUIRED`, `MIN_LENGTH`) | **Global nativo**: búscalo con `nameEquals=description`. Reutilízalo siempre; nunca lo recrees. |

**El `name` y el `description` nativos son el único nombre y la única descripción de toda entidad.** NO crees atributos de nombre o descripción específicos del dominio (`nombreDelSistema`, `nombreDelInforme`, `descripcionDelSistema`, `descripcionDelIndicador`…) para entidades nuevas: duplica datos y rompe la reutilización (la búsqueda, las plantillas de carga masiva, los filtros y las exportaciones dependen de los nativos). Si un documento de diseño declara un atributo así, mapéalo al nativo (manteniendo la intención de su label y sus validaciones en el templateAttribute nativo) y avisa al usuario. Como `name` es `NOT_EDITABLE`, acuerda con el usuario una convención de nombres antes de crear instancias. Las entidades heredadas que ya tienen un atributo de nombre específico del dominio lo conservan (esta skill nunca borra configuración), pero las plantillas nuevas no deben añadir uno.

#### Para RELACIONES (`typeObject = "RELATIONSHIP"`)

Un objectSubType de relación **NUNCA debe quedarse sin atributos**. Tras crear el `objectSubType`, configura estos 4 atributos base:

| Nombre del atributo | Label | Tipo | Sort | Validaciones | Origen |
|----------------|-------|------|------|-------------|--------|
| `name` | Nombre | `INPUT_TEXT` | `"0"` | `REQUIRED` + `NOT_EDITABLE` | **Global nativo**: búscalo con `nameEquals=name`. |
| `source` | Source | `ENTITY_SEARCH` | `"1"` | `REQUIRED` + `NOT_EDITABLE` + `SUBTYPE_FILTER` (ver abajo) | **Global nativo**: búscalo con `nameEquals=source`. |
| `destination` | Destination | `ENTITY_SEARCH` | `"2"` | `REQUIRED` + `NOT_EDITABLE` + `SUBTYPE_FILTER` (ver abajo) | **Global nativo**: búscalo con `nameEquals=destination`. |
| `description` | Description | `TEXT_AREA` o `ENRICHED_TEXT_AREA_INTERNATIONAL` (el que tenga la plataforma) | `"3"` | (ninguna obligatoria) | **Global nativo**: búscalo con `nameEquals=description`. |

**El `SUBTYPE_FILTER` en `source` y `destination` es obligatorio** en toda relación. Esta validación restringe qué subtipos de entidad se pueden seleccionar como origen/destino de las instancias de la relación. Sin ella, el usuario podría elegir cualquier tipo de entidad y las hojas auxiliares (`Origen` / `Destino`) de la plantilla de carga masiva no filtrarían correctamente.

`params` es un string con los nombres de los subtipos de entidad permitidos separados por `_-` (el mismo separador que usa la plataforma para `ARRAY_ALPHANUMERICAL`). Un único valor si solo hay un tipo válido:

```json
// Single source type - params has just one subtype
{"templateAttribute": "<source_tmpl_href>", "key": "SUBTYPE_FILTER", "params": "SISTEMA_ORIGEN"}
{"templateAttribute": "<destination_tmpl_href>", "key": "SUBTYPE_FILTER", "params": "APLICACION"}

// Multiple source types - separated by _-
{"templateAttribute": "<source_tmpl_href>", "key": "SUBTYPE_FILTER", "params": "INFORME_-INDICADOR"}
```

Al definir una relación nueva, el diseño debe declarar los subtipos de origen y los subtipos de destino permitidos. Mapéalos directamente al `SUBTYPE_FILTER.params` del atributo base correspondiente.

**Nota**: Anjana permite que varios `templateAttributes` compartan el mismo valor de `sort` dentro de una sección (el primer atributo no entrará en conflicto con otro sort=0). Así, si una relación heredada ya tiene un `nombre` personalizado en sort=0, aun así puedes añadir el `name` nativo en sort=0 a su lado sin conflicto.

**Pasos de implementación para cada entidad O relación nueva**:
1. Crea el `objectSubType`.
2. Crea al menos un menú, p. ej. `{"name": "General", "order": "1", "subType": <subtype_href>}`.
3. Crea al menos una sección en el primer menú, p. ej. `{"name": "Identificación", "order": "1", "menu": <menu_href>}`.
4. **Añade siempre** el atributo nativo `name` (resuelto con la búsqueda `nameEquals=name`) con sort=0 en la primera sección, con `REQUIRED` + `NOT_EDITABLE`. **Para entidades**, añade también el `description` nativo (resuelto con `nameEquals=description`) con sort=1 en la misma sección.
5. **Solo para relaciones**: añade también `source`, `destination`, `description` (sorts 1, 2, 3) en la misma sección. **Tanto en `source` como en `destination`, además de `REQUIRED` + `NOT_EDITABLE`, añade una validación `SUBTYPE_FILTER` con `params` = el nombre del subtipo de entidad permitido (o los nombres separados por `_-` si son varios)**. El diseño de la relación DEBE declararlos explícitamente: p. ej. `ALIMENTA` tiene `source.SUBTYPE_FILTER=SISTEMA_ORIGEN` y `destination.SUBTYPE_FILTER=APLICACION`.
6. Continúa añadiendo atributos específicos del dominio a partir de sort=2 en las entidades (sort=4 en adelante en las relaciones), reutilizando las attributeDefinitions existentes siempre que el significado sea el mismo (ver "Reutilizar antes de crear" en atributos-y-valores-referencia.md).

**Para los atributos globales nativos** (`name`, `source`, `destination`, `description`):
- Busca la definición existente con `nameEquals=<attr_name>` usando **paginación de Spring (`content`)**, NO `_embedded` de HATEOAS.
- La respuesta del filtro NO incluye `_links`: construye el href manualmente como `<PORTUNO_HREF>/attributeDefinitions/<id>`.
- Reutilízalos siempre; nunca los recrees. Intentar hacer POST de un duplicado por nombre falla con una violación de restricción de unicidad.
