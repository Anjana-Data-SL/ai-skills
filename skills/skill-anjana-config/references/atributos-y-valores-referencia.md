## Entidad: Definiciones de Atributos de Metadatos

**Endpoint**: `POST /gateway/api/portuno/attributeDefinitions`

Recopila del usuario:
- **Nombre del atributo** (label)
- **Tipo de atributo** (texto, número, fecha, booleano, selector, etc.)
- **Descripción**: Pide al usuario una descripción breve

Construye el body:
- `name`: Convierte el label a camelCase (ej: "Fecha de creación" → `fechaDeCreacion`)
- `type`: Mapea la descripción del usuario a la KEY correspondiente (ej: "texto simple" → `INPUT_TEXT`, "booleano" → `INPUT_CHECKBOX`)
- `label`: El nombre original tal como lo proporcionó el usuario
- `placeHolder`: Siempre `null`
- `shortDescription`: Siempre `null`
- `startDate`: Siempre `null`
- `lastModifiedDate`: Siempre `null`
- `description`: Descripción proporcionada por el usuario. Manténla por debajo de ~250 caracteres: las descripciones más largas se han rechazado con HTTP 500 (lo mismo aplica a las descripciones de menús y secciones)

### Traducciones de un atributo nuevo (obligatorio)

Tras crear un atributo (o un nuevo `label` / `description` para uno existente), escribe sus traducciones de modo que **ningún idioma registrado quede vacío** (ver "Cómo se muestran las traducciones que faltan: nunca dejes una clave vacía" en `references/internacionalizacion.md`, y el paso 8 "Cobertura de traducciones" del "Flujo conversacional"):
- **Label**: la clave de traducción es el texto del **`label` exactamente como está almacenado** (ej: `"Fecha de revisión"`), **no** el `name` técnico (`fechaDeRevision`). Valor en cada idioma: el label en ese idioma; para `es-ES` (o el idioma en el que se escribió el label) es el propio label.
- **Descripción**: la clave es el texto de la **`description`** exactamente como está almacenado; valor en cada idioma: la descripción en ese idioma.
- **Valores de referencia** de un selector: la clave es el texto de cada `value`; valor en cada idioma: su traducción (los nombres comerciales y los términos técnicos universales mantienen el mismo texto; ver las reglas de traducción en `references/internacionalizacion.md`).
- Antes de escribir, comprueba con `search` si la clave ya existe con un valor en algún idioma (otro atributo puede compartir el mismo label): si es así, ese idioma es una sobrescritura y requiere el protocolo de confirmación explícita; en caso contrario es una creación simple.
- Escribe todos los idiomas en un único `submit` (26.1) o en un `POST /translations` por clave e idioma (25.1/25.2, más publicación), vuelve a leerlos para confirmar que ninguno está vacío y limpia la caché.
- Los atributos nativos cuyo `label` es en sí mismo una clave (`ATTRIBUTE_NOMBRE.<name>`) ya están traducidos por la plataforma: no crees traducciones para ellos.

### Nombres reservados (prohibidos como valor de `name`)

La plataforma Anjana reserva ciertos identificadores para uso interno. Estas cadenas **no se pueden** usar como `name` de una `attributeDefinition` en ninguna versión. Intentar crear un atributo con uno de estos nombres reservados fallará o colisionará en silencio con campos internos de la plataforma:

| `name` reservado | Motivo | Usar en su lugar |
|---|---|---|
| `version` | Reservado para el versionado interno de objetos de la plataforma. | `versionDelDocumento`, `versionDelInforme`, `versionDelPlan`, `versionPublicada`, etc.: desambigua siempre con la entidad o el tipo de versión. |
| `status`, `estado`, y cualquier `name` **o label** que empiece por "estado"/"status" o sea solo eso (ej: `estadoDelProyecto`, `statusDelInforme`, label "Estado") | Todo objeto ya tiene un **estado nativo** (el estado del workflow: borrador, pendiente, publicado, obsoleto…). **No es editable** por los usuarios y se muestra como "Estado" en la UI. Un atributo personalizado con esa palabra colisiona con él en la UI, en los filtros y en las exportaciones, y los usuarios confunden uno con otro. | Nombra la situación de negocio por lo que es: `fase…` (fase del proyecto), `situacion…` (situación operativa, de la incidencia), `avance…` (avance de la acción), `vigencia…` (vigencia del acuerdo), `etapa…`, `cumplimiento…`. |
| `name`, `description` (y copias de dominio como `nombreDelSistema`, `nombreDelInforme`, `descripcionDelSistema`, `descripcionDelIndicador`) | Atributos globales nativos. Toda entidad y relación usa **el `name` nativo como su nombre lógico y la `description` nativa como su descripción** (ver "Atributos base obligatorios"). Crear atributos de nombre/descripción por entidad duplica datos, rompe la búsqueda, las plantillas masivas y los filtros, e impide la reutilización. | Reutiliza el `name` / `description` nativos. Pon cualquier validación específica de la entidad (ej: `MIN_LENGTH`) en el templateAttribute `description` nativo de esa entidad. |

**Regla**: antes de enviar el POST, normaliza el `name` **y el label** propuestos y compruébalos contra esta lista de reservados:
- `version` o `estado`/`status` → pide al usuario un nombre más específico (ej: `version` → "¿versión de qué? (documento, modelo, plan…)"; `estado` → "¿fase, situación, avance, vigencia…?"). NO lo renombres automáticamente en silencio.
- Un nombre/descripción del propio objeto (`nombre…`, `name…`, `descripcion…`, `description…` referidos a la entidad) → NO lo crees; indica al usuario que se usarán el `name`/`description` nativos. Si el texto describe otra cosa (ej: `descripcionDeLosDatos` = los datos utilizados), propón un nombre que no empiece por `descripcion`/`nombre` (ej: `datosUtilizados`) para que no se confunda con la descripción nativa.

### Reutilizar antes de crear (verificación previa obligatoria, todas las versiones)

Las `attributeDefinitions` son **globales**: la misma definición se puede asignar a plantillas de muchas entidades. **Siempre que más de una entidad necesite un atributo con el mismo significado, debe haber una única attributeDefinition reutilizada en todas ellas**, nunca una por entidad (`responsableDelInforme`, `responsableDelIndicador`… para el mismo concepto). Ventajas: un único filtro de búsqueda cubre todas las entidades, los usuarios ven el mismo campo con la misma etiqueta, y las traducciones y los valores de referencia se mantienen una sola vez.

Antes de cada `POST /attributeDefinitions`:
1. Busca una definición existente con el mismo significado o uno similar: `GET /gateway/api/portuno/api/filter/attributeDefinitions?nameContains=<root>&page=0&size=50` (prueba con el nombre en camelCase y con 1-2 palabras clave del label, ej: `responsable`, `fechaDe`, `calidad`).
2. Si existe una con el mismo significado y un tipo compatible, **reutilízala** (crea solo el `templateAttribute` en la nueva sección). Las validaciones como `REQUIRED` son por templateAttribute, de modo que un atributo compartido puede ser obligatorio en una entidad y opcional en otra.
3. Si el significado es el mismo pero el tipo difiere, detente y pregunta al usuario cuál conservar: no crees un casi-duplicado.
4. Cuando trabajes a partir de un documento de diseño, construye primero la lista de atributos que aparecen en más de una entidad y crea cada uno una sola vez.
5. Nombra los atributos compartidos de forma genérica (`dominio`, `fechaDeRevision`, `responsableTecnico`), no según una entidad (`fechaRevisionInforme`).

### Tipos de texto multiidioma

Elige el tipo de texto pensando en entornos multiidioma:
- Texto escrito por usuarios que debe ser traducible (descripciones, justificaciones, conclusiones, nombres de áreas o de puestos) → `INPUT_TEXT_INTERNATIONAL`, `TEXT_AREA_INTERNATIONAL` o `ENRICHED_TEXT_AREA_INTERNATIONAL`.
- Valores idénticos en todos los idiomas (códigos, NIF, números de registro, versiones, referencias de contrato, nombres de personas, umbrales, URLs, nombres técnicos de fuentes) → `INPUT_TEXT` / `TEXT_AREA`.
En caso de duda, pregunta al usuario; por defecto usa el tipo `_INTERNATIONAL` para texto libre.

### Documentos: URL, no fichero

Anjana **no tiene permisos de visualización**: todo lo publicado, incluidos los ficheros subidos con `UPLOAD_FILE` / `ARRAY_UPLOAD_FILE`, puede ser visto y descargado por cualquiera con acceso al catálogo. Usa por defecto `UPLOAD_URL` / `ARRAY_UPLOAD_URL` apuntando a un repositorio con control de acceso (SharePoint o similar). Usa `UPLOAD_FILE` solo si el usuario confirma explícitamente que el documento no es sensible.

### `NOT_EDITABLE` lo bloquea todo

Un atributo con `NOT_EDITABLE` no se puede editar de ninguna forma: ni en la UI, ni por script, ni por API. Úsalo solo para valores que nunca deben cambiar tras la creación (el `name` nativo, y `source`/`destination` de las relaciones). **Nunca** lo pongas en campos que se espera que un script o una integración actualicen (puntuaciones calculadas, estados sincronizados, valores de métricas).

Para la tabla completa de las 34 KEYs de tipo de atributo, consulta `references/api-endpoints.md`.

## Entidad: Valores de Referencia (attributeDefinitionValues)

**Endpoint**: `POST /gateway/api/portuno/attributeDefinitionValues`

Los valores de referencia son las opciones seleccionables de los atributos de metadatos de tipo selector. Solo se pueden asignar a atributos de estos tipos: `SELECT`, `MULTI_SELECT`, `SELECT_IMG_TXT`, `MULTI_SELECT_IMG_TXT`, `SELECT_IMG`, `MULTI_SELECT_IMG`, `TREE_SELECT`, `TREE_MULTISELECT`.

### Paso 1: Recuperar los atributos de tipo selector existentes

Si el usuario no especifica a qué atributo añadir valores, o si el atributo no se creó en la sesión actual, recupera los atributos existentes de tipos selector:

```bash
curl -s "<BASE_URL>/gateway/api/portuno/api/filter/attributeDefinitions?typeEquals=<TYPE>" \
  -H @"<AUTH_HEADER_FILE>" \
  -H "Content-Type: application/json"
```

Sustituye `<TYPE>` por uno de: `SELECT`, `MULTI_SELECT`, `SELECT_IMG_TXT`, `MULTI_SELECT_IMG_TXT`, `SELECT_IMG`, `MULTI_SELECT_IMG`, `TREE_SELECT`, `TREE_MULTISELECT`.

Muestra al usuario la lista de atributos coincidentes por su `label` para que elija uno. Su href es `<PORTUNO_HREF>/attributeDefinitions/<id>` (la respuesta del filtro no incluye `_links`).

### Paso 2: Recopilar datos del usuario

- **A qué atributo** añadir valores (del Paso 1 o de un atributo recién creado)
- **Qué valor(es)** añadir: el usuario puede proporcionar uno o varios valores a la vez

### Paso 3: Comprobar SIEMPRE si existen duplicados antes de crear

**CRÍTICO**: Anjana NO impone una restricción de unicidad sobre `(attributeDefinition_id, value)`. Hacer POST del mismo par `(atributo, valor)` dos veces crea dos filas distintas con ids diferentes, y ambas aparecen en la UI como opciones duplicadas en el desplegable. Es un bug silencioso de integridad de datos.

**Antes de cada POST, consulta los valores existentes de ese atributo:**

```bash
curl -s "<BASE_URL>/gateway/api/portuno/api/filter/attributeDefinitionValues?attributeDefinitionEquals=<ATTR_ID>&page=0&size=200" \
  -H @"<AUTH_HEADER_FILE>"
```

Recorre todas las páginas de resultados (`page` 0, 1, … hasta que `last` sea `true`) y construye un conjunto con las cadenas `value` existentes: un atributo puede tener más valores que los de una página. **Omite el POST de cualquier valor que ya esté en ese conjunto.**

Esta regla es especialmente importante al ejecutar scripts de carga por lotes que agregan valores de múltiples fuentes (ej: un parser + un mapeo manual). Cada lote debe deduplicar contra el estado de la plataforma, no solo internamente.

### Paso 4: Construir y enviar el body

Por cada valor que no exista todavía, envía una petición POST separada:

```json
{
    "value": "<VALUE>",
    "attributeDefinition": "<ATTRIBUTE_HREF>"
}
```

- `value`: El texto del valor de referencia proporcionado por el usuario
- `attributeDefinition`: La URL `_links.self.href` de la definición de atributo destino

Si el usuario proporciona varios valores, ejecuta un POST por valor secuencialmente, aplicando a cada uno la comprobación de duplicados del Paso 3.

### Paso 5: Limpieza si ya se crearon duplicados

Si la plataforma ya tiene pares (atributo, valor) duplicados (un script se ejecutó sin la comprobación de duplicados), el patrón de limpieza es:
1. Lista todos los valores, recorriendo `GET /api/filter/attributeDefinitionValues?page=<n>&size=500` hasta que `last` sea `true`
2. Agrupa por `(attributeDefinition.id, value)`. Los pares con `len(ids) > 1` son duplicados.
3. Para cada par duplicado, **conserva el id más bajo** (el primero creado, probablemente ya referenciado por taxonomías y relaciones DEPENDS_ON) y haz `DELETE` del resto.

**Esta operación DELETE es una de las excepciones documentadas a la regla de "no modificar" de la skill**: es una acción correctiva para filas huérfanas creadas por un script de carga defectuoso. No la ejecutes nunca sin aplicar el protocolo de confirmación explícita ("Operaciones que modifican o borran"): lista los ids a borrar, explica los riesgos y espera la confirmación explícita del usuario.
