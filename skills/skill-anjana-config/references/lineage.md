## Entidad: Capas de Lineage

Las capas de lineage definen las vistas disponibles en el panel de lineage. Cada capa contiene un conjunto de entidades y/o relaciones (creadas por el usuario o tipos nativos internos).

### Paso 1: Comprobar las capas existentes (obligatorio)

Antes de crear una capa, lista **todas** las capas existentes (paginando hasta que `last` sea `true`):

```bash
curl -s "<BASE_URL>/gateway/api/portuno/api/filter/layers?page=0&size=200" \
  -H @"<AUTH_HEADER_FILE>"
```

**a) Nombre igual o parecido.** Compara el nombre solicitado con cada `name` existente tras normalizar ambos (minúsculas, sin tildes, y con espacios, `_` y `-` tratados como iguales):
- **Mismo nombre normalizado** (p. ej. "Vista técnica" vs "vista tecnica"): **no** crees la capa. Indica al usuario que ya existe (id y nombre exacto) y pregúntale si quiere usar esa capa en su lugar; añadirle entidades, relaciones o agregaciones es una creación y sigue los pasos normales de más abajo.
- **Nombre parecido**: uno contiene al otro, difieren solo en singular/plural, o difieren en uno o dos caracteres (p. ej. "Vista técnica" vs "Vista técnica BI", "Capa BI" vs "Capas BI"): muestra al usuario las capas parecidas (id y nombre exacto) y **pídele que confirme** si se crea la capa nueva o se usa una de las existentes. No la crees hasta que responda.
- Dos capas con el mismo nombre también romperían el Paso 2, donde la capa nueva se localiza por su nombre.

**b) Capa por defecto.** Busca una capa con `isDefault: true` entre los resultados (o `GET …/api/filter/layers?isDefaultEquals=true`). Si existe alguna, avisa al usuario de que poner `isDefault: true` en la nueva capa entrará en conflicto (solo puede haber una capa por defecto a la vez).

### Paso 2: Crear la capa

**Endpoint**: `POST <BASE_URL>/gateway/api/portuno/api/resource/layers`

**Body de la petición**:
```json
{
    "name": "Vista de negocio",
    "isDefault": false
}
```

| Campo | Reglas |
|-------|-------|
| `name` | Nombre de la capa tal como lo proporciona el usuario |
| `isDefault` | `true` solo si el usuario lo pide explícitamente como capa por defecto Y no existe ninguna otra capa por defecto |

**Obtener el href de la capa**: necesario para el siguiente paso. **En 26.1 la respuesta está vacía** (verificado: HTTP 200 sin cuerpo, pero la capa *sí* se crea). **No** reintentes el POST, crearía una capa duplicada: busca la capa con `GET <BASE_URL>/gateway/api/portuno/api/filter/layers?nameEquals=<name>` y construye su href como `<PORTUNO_HREF>/layers/<id>`. Si la respuesta sí incluye `_links.self.href`, úsalo.

### Paso 3: Añadir entidades y relaciones a la capa

**Endpoint**: `POST <BASE_URL>/gateway/api/portuno/layerObjectSubtypes`

**Body de la petición**:
```json
{
    "layer": "<LAYER_HREF>",
    "objectSubType": "INFORME"
}
```

**Comprueba qué contiene ya la capa (obligatorio, para evitar duplicados).** Antes de añadir nada, lee el contenido actual de la capa (verificado en 26.1; pagina hasta que `last` sea `true`):

```bash
curl -s "<BASE_URL>/gateway/api/portuno/api/filter/layerObjectSubtypes?layerEquals=<LAYER_ID>&page=0&size=200" \
  -H @"<AUTH_HEADER_FILE>"
```

Cada elemento tiene el nombre del `objectSubType`. Quita de la lista a añadir: los subtipos que ya están en la capa y cualquier nombre que el usuario haya repetido en la petición. Indica al usuario cuáles se omitieron y por qué ("ya estaba en la capa" / "repetido en la petición"). En una capa recién creada en esta sesión el contenido está vacío, pero la comprobación es barata y protege frente a una ejecución parcial anterior.

Envía un POST por cada entidad o relación a añadir. El `objectSubType` puede ser cualquiera de los siguientes:

**Tipos creados por el usuario**: cualquier nombre de `objectSubType` creado mediante el endpoint `/objectSubTypes` (p. ej., `INFORME`, `ALIMENTA_INFORME`).

**Relaciones internas nativas**:

| `objectSubType` | Descripción | Origen → Destino |
|-----------------|-------------|----------------------|
| `STRUCTURE` | Campos de un dataset | DATASET → DATASET_FIELD |
| `ADHERENCE` | Aceptación de un DSA por un usuario | DSA → USER |
| `DSA_CONTENT` | Contenido de un DSA | DSA → cualquier entidad |
| `INSTANCE_DATASET_IN` | Dataset de entrada de una instancia | DATASET → INSTANCE |
| `INSTANCE_DATASET_OUT` | Dataset de salida de una instancia | INSTANCE → DATASET |
| `INSTANCE_PROCESS` | Proceso que genera una instancia | PROCESS → INSTANCE |
| `SOLUTION_OWNED_INSTANCE` | Instancias que pertenecen a una solución | SOLUTION → INSTANCE |
| `SOLUTION_RELATED_INSTANCE` | Instancias relacionadas con una solución | SOLUTION → INSTANCE |

**Entidades internas nativas**:

| `objectSubType` | Descripción |
|-----------------|-------------|
| `ORGANIZATIONAL_UNIT` | UO creadas por el usuario |
| `USER` | Usuarios de la plataforma |

### Paso 4: Consultar las capas existentes

Para listar todas las capas configuradas:

```bash
curl -s "<BASE_URL>/gateway/api/portuno/api/filter/layers" \
  -H @"<AUTH_HEADER_FILE>"
```

### Paso 5: Traducir el nombre de la capa (obligatorio)

El `name` de la capa es una clave de traducción (ver el catálogo de claves de traducción en internacionalizacion.md), y **ninguna clave puede quedarse sin valor en ningún idioma registrado** (ver "Cómo se muestran las traducciones que faltan: nunca dejes una clave vacía" en internacionalizacion.md). Tras crear una capa:
1. Lee los idiomas registrados (26.1: las claves de cualquier mapa `values` devuelto por `POST …/translations/v1/search`; 25.1/25.2: `GET …/api/filter/languages`) y los valores actuales de la clave.
2. Indica al usuario qué idiomas necesitan un valor: **todos, incluidos el idioma por defecto y `es-ES`** (para `es-ES` el propio nombre de la capa suele ser el valor correcto), y pregúntale por los textos o cómo obtenerlos. La traducción automática está sujeta al aviso sobre servicios de terceros (MyMemory/Itzuli son servicios externos: elige el usuario), como en el resto de la skill.
3. Escríbelos como se describe en internacionalizacion.md (26.1: un único `submit` con todos los idiomas y `action: "UPDATE"`; 25.1/25.2: `POST /translations` + publicación). Si la clave ya tiene un valor en algún idioma, se trata de una sobrescritura: aplica el protocolo de confirmación explícita.
4. Vuelve a leer la clave y confirma que ningún idioma registrado está vacío; después limpia la caché.

Si el usuario no quiere traducir, indícale qué verán los usuarios de cada idioma vacío (idioma por defecto → `en-US` → clave) y déjalo vacío solo con su confirmación explícita.

---

## Entidad: Relaciones de agregación en las capas de Lineage

Dentro de una capa de lineage, ciertas relaciones se pueden configurar para actuar como **relaciones de agregación** (agrupaciones). Esto controla cómo se agrupa o colapsa visualmente el lineage según el tipo de relación.

### Elegibilidad

Una relación se puede configurar como relación de agregación si:
- Es una **relación nativa de Anjana** (p. ej., `STRUCTURE`, `INSTANCE_DATASET_IN`, etc.), O
- Es una **relación creada por el usuario** recuperada mediante la API con `parental: true`

**Si `parental` es `false`**: se trata de una modificación de configuración existente. Aplica el protocolo de confirmación explícita ("Operaciones que modifican o borran") y, solo si el usuario confirma:
1. Haz PATCH del objectSubType para poner `parental: true`:

```bash
PATCH <BASE_URL>/gateway/api/portuno/objectSubTypes/<ID>
Body: {"parental": true}
```

Después continúa con la comprobación previa y las dos acciones de más abajo.

### Comprobación previa: la capa debe contener la relación, su origen y su destino (obligatorio)

Antes de configurar una agregación en una capa, lee el contenido de la capa (`GET …/api/filter/layerObjectSubtypes?layerEquals=<LAYER_ID>`, ver "Entidad: Capas de Lineage", Paso 3) y comprueba que contiene **los tres**:
- la relación (`relationshipSubtype`),
- su entidad de origen (`sourceSubtype`),
- su entidad de destino (`destinationSubtype`).

Si falta alguno, **avisa al usuario antes de hacer nada más**: lista los tipos que faltan, explica que una agregación sobre tipos que no están en la capa no tiene efecto visible y pregunta si se añaden. Si el usuario está de acuerdo, añádelos primero (Paso 3 de "Entidad: Capas de Lineage", con su comprobación de duplicados) y solo entonces configura la agregación (Acciones 1 y 2). Si el usuario no quiere añadirlos, no configures la agregación salvo que lo pida explícitamente de todos modos.

Comprueba también que la agregación no está ya asignada a la capa (`GET …/api/filter/layerGroupings?layerEquals=<LAYER_ID>`, verificado en 26.1): si el mismo grouping ya está, díselo al usuario y omítelo.

### Acción 1: Crear el método de agrupación (o reutilizar el existente)

Define qué relación actúa como agregación entre un tipo de entidad de origen y uno de destino.

**Antes de crear, comprueba siempre si la agrupación ya existe:**

```bash
GET <BASE_URL>/gateway/api/portuno/api/filter/groupings
```

Inspecciona la respuesta y busca un grouping con los mismos `sourceSubtype`, `destinationSubtype` y `relationshipSubtype`. Si existe, construye su href como `<PORTUNO_HREF>/groupings/<id>` (las respuestas de filtro no tienen `_links`) y salta directamente a la Acción 2.

Solo si no existe ningún grouping coincidente, crea uno nuevo:

**Endpoint**: `POST <BASE_URL>/gateway/api/portuno/groupings`

**Body de la petición**:
```json
{
    "sourceSubtype": "SISTEMA_ORIGEN",
    "destinationSubtype": "INFORME",
    "relationshipSubtype": "ALIMENTA_INFORME"
}
```

| Campo | Reglas |
|-------|-------|
| `sourceSubtype` | Tipo de entidad de origen: creada por el usuario o entidad nativa de Anjana |
| `destinationSubtype` | Tipo de entidad de destino: creada por el usuario o entidad nativa de Anjana |
| `relationshipSubtype` | El tipo de relación que se usará como agregación: creada por el usuario o relación nativa de Anjana |

**Extrae el `_links.self.href` del grouping** de la respuesta: es necesario para la Acción 2.

Para listar los métodos de agrupación existentes:
```bash
GET <BASE_URL>/gateway/api/portuno/api/filter/groupings
```

### Acción 2: Aplicar la agrupación a una capa concreta

No todos los métodos de agrupación se aplican a todas las capas. Este paso asigna un grouping a una capa concreta.

**Endpoint**: `POST <BASE_URL>/gateway/api/portuno/layerGroupings`

**Body de la petición**:
```json
{
    "layer": "<PORTUNO_HREF>/layers/4",
    "grouping": "<PORTUNO_HREF>/groupings/6"
}
```

| Campo | Reglas |
|-------|-------|
| `layer` | `_links.self.href` de la capa de destino |
| `grouping` | `_links.self.href` del método de agrupación creado en la Acción 1 |

Para recuperar las asignaciones capa-grouping existentes:
```bash
GET <BASE_URL>/gateway/api/portuno/api/filter/layerGroupings
```
