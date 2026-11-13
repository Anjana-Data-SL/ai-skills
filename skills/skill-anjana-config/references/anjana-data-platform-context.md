# Anjana Data Platform - Contexto de configuracion

Este documento describe las capacidades de configuracion de Anjana Data Platform. Su objetivo es servir como fuente de conocimiento para cualquier skill o agente que necesite entender que se puede gobernar y configurar en la plataforma.

> **Es una vision general de conceptos.** Para endpoints, campos, reglas y procedimientos, prevalecen `SKILL.md` y el resto de ficheros de `references/`: si algo de este documento no coincide con ellos, seguir siempre `SKILL.md`.

---

## 1. Tipos de objetos gobernables

Anjana Data Platform permite gobernar dos grandes familias de objetos:

### 1.1 Entidades (`ENTITY`)

Representan activos o recursos de datos. Cada entidad tiene un subtipo que define su naturaleza. Existen subtipos nativos (fijos) y subtipos personalizados creados por el usuario.

#### Subtipos nativos de entidad

| Subtipo | Descripcion | Modulo |
|---------|-------------|--------|
| `DATASET` | Conjunto de datos. Es el activo principal del catalogo de datos | DC |
| `DATASET_FIELD` | Campo individual dentro de un dataset. Representa una columna o atributo de un dataset | DC |
| `DSA` | Data Service Agreement. Contrato de servicio de datos que regula el acceso y uso de datasets | DC |
| `PROCESS` | Proceso de tratamiento de datos. Representa una operacion o transformacion sobre datos | DC |
| `INSTANCE` | Instancia de ejecucion de un proceso. Cada vez que un proceso se ejecuta genera una instancia | DC |
| `SOLUTION` | Solucion. Agrupa instancias relacionadas que forman parte de un mismo flujo o proyecto | DC |
| `ORGANIZATIONAL_UNIT` | Unidad organizativa. Representa areas, departamentos o equipos de la organizacion | Interno |
| `USER` | Usuario de la plataforma | Interno |

> **Nota sobre modulos**: Los subtipos del catalogo de datos pertenecen al modulo `DC` (Data Catalog). Los subtipos personalizados creados por el usuario pueden pertenecer a `DC` si son del catalogo o a `BG` (Business Glossary) en caso contrario.

#### Subtipos personalizados de entidad

El usuario puede crear subtipos de entidad adicionales para gobernar otros tipos de activos (por ejemplo: `SISTEMA_ORIGEN`, `APLICACION`, `INFORME`). Se crean con `typeObject: "ENTITY"` y se les asigna un modulo (`DC` o `BG`), workflows y configuracion de linaje.

### 1.2 Relaciones (`RELATIONSHIP`)

Representan conexiones o vinculos entre entidades. Al igual que las entidades, tienen subtipos nativos y personalizados.

#### Subtipos nativos de relacion

| Subtipo | Descripcion | Conecta |
|---------|-------------|---------|
| `STRUCTURE` | Estructura de un dataset. Relaciona un dataset con sus campos | DATASET -> DATASET_FIELD |
| `ADHERENCE` | Adhesion a un DSA por parte de un usuario | DSA -> USER |
| `DSA_CONTENT` | Contenido de un DSA. Asocia un DSA con las entidades que regula | DSA -> cualquier entidad |
| `INSTANCE_DATASET_IN` | Dataset de entrada de una instancia | DATASET -> INSTANCE |
| `INSTANCE_DATASET_OUT` | Dataset de salida de una instancia | INSTANCE -> DATASET |
| `INSTANCE_PROCESS` | Proceso que genera una instancia | PROCESS -> INSTANCE |
| `SOLUTION_OWNED_INSTANCE` | Instancias que pertenecen a una solucion | SOLUTION -> INSTANCE |
| `SOLUTION_RELATED_INSTANCE` | Instancias relacionadas con una solucion | SOLUTION -> INSTANCE |

#### Subtipos personalizados de relacion

El usuario puede crear relaciones adicionales (por ejemplo: `CONSUME`, `ALIMENTA_INFORME`). Se crean con `typeObject: "RELATIONSHIP"`, modulo `BG` (o `DC` si conectan entidades del catalogo de datos: el modulo sigue al de las entidades que conectan), y pueden marcarse como `parental: true` si representan relaciones de agregacion (jerarquicas) en el linaje.

---

## 2. Organizacion de metadatos: menus y secciones

Los metadatos de cada tipo de objeto se organizan en una estructura jerarquica de **menus** y **secciones** que da contexto sobre la naturaleza de la informacion que contienen.

```
Tipo de objeto (Entidad o Relacion)
  +-- Menu (pestana en la vista de detalle)
  |     +-- Seccion (agrupacion logica de atributos)
  |     |     +-- Atributo de metadato 1
  |     |     +-- Atributo de metadato 2
  |     +-- Seccion
  |           +-- Atributo de metadato 3
  +-- Menu
        +-- Seccion
              +-- Atributo de metadato 4
```

### Reglas de menus

- Cada tipo de objeto debe tener al menos un menu.
- Un menu pertenece exclusivamente a un tipo de objeto (no se comparte entre tipos).
- Cada menu tiene un `name`, un `order` (posicion de visualizacion, empezando en 1) y opcionalmente una `description`.

### Reglas de secciones

- Cada menu debe tener al menos una seccion.
- Una seccion pertenece a un menu concreto.
- Cada seccion tiene un `name`, un `order` (posicion dentro del menu) y opcionalmente una `description`.
- Las secciones agrupan atributos de metadato relacionados tematicamente.

### Ejemplo

```
Entidad: SISTEMA_ORIGEN
  +-- Menu: "General" (order: 1)
  |     +-- Seccion: "Calidad del dato" (order: 1)
  |     |     +-- encriptar (order: 1)
  |     |     +-- nivelDeConfidencialidad (order: 2)
  |     +-- Seccion: "Gobernanza" (order: 2)
  |           +-- sistemasDependientes (order: 1)
  +-- Menu: "Linaje" (order: 2)
        +-- Seccion: "Relaciones" (order: 1)
              +-- consumidores (order: 1)
```

---

## 3. Tipos de atributos de metadatos

Cada atributo de metadato tiene un tipo (`type`) que determina su comportamiento en la interfaz y las validaciones aplicables. A continuacion se listan todos los tipos disponibles con su codigo interno.

### Textos

| Codigo interno | Descripcion |
|----------------|-------------|
| `INPUT_TEXT` | Texto simple (una linea, sin soporte multiidioma) |
| `INPUT_TEXT_INTERNATIONAL` | Texto simple con soporte multiidioma |
| `TEXT_AREA` | Area de texto (varias lineas, sin soporte multiidioma) |
| `TEXT_AREA_INTERNATIONAL` | Area de texto con soporte multiidioma |
| `ENRICHED_TEXT_AREA` | Texto enriquecido (rich text con formato) |
| `ENRICHED_TEXT_AREA_INTERNATIONAL` | Texto enriquecido con soporte multiidioma |

### Numericos

| Codigo interno | Descripcion |
|----------------|-------------|
| `INPUT_NUMBER` | Numero entero |
| `INPUT_DECIMAL` | Numero decimal |
| `INPUT_RANGE` | Rango numerico (valor entre un minimo y maximo definidos en validaciones) |

### Fecha y booleano

| Codigo interno | Descripcion |
|----------------|-------------|
| `INPUT_DATE` | Selector de fecha |
| `INPUT_CHECKBOX` | Booleano (casilla de verificacion) |

### Selectores simples y multiples

| Codigo interno | Descripcion |
|----------------|-------------|
| `SELECT` | Selector de valor unico (desde valores de referencia definidos por el usuario) |
| `MULTI_SELECT` | Selector multiple de valores de referencia |
| `SELECT_IMG_TXT` | Selector de imagen con texto |
| `MULTI_SELECT_IMG_TXT` | Selector multiple de imagen con texto |
| `SELECT_IMG` | Selector de imagen |
| `MULTI_SELECT_IMG` | Selector multiple de imagen |

### Selectores de taxonomia (jerarquicos)

| Codigo interno | Descripcion |
|----------------|-------------|
| `TREE_SELECT` | Selector de taxonomia (estructura en arbol, valor unico) |
| `TREE_MULTISELECT` | Selector multiple de taxonomia (estructura en arbol) |

### Selectores de usuarios y unidades organizativas

| Codigo interno | Descripcion |
|----------------|-------------|
| `SELECT_USERS` | Selector de usuario |
| `MULTI_USERS` | Selector multiple de usuarios |
| `SELECT_ORGANIZATIONAL_UNIT` | Selector de unidad organizativa |
| `MULTI_ORGANIZATIONAL_UNIT` | Selector multiple de unidades organizativas |

### Entidades

| Codigo interno | Descripcion |
|----------------|-------------|
| `ENTITY_SEARCH` | Selector de entidad (busqueda de una entidad existente) |
| `ARRAY_ENTITY` | Selector multiple de entidades |

### Arrays

| Codigo interno | Descripcion |
|----------------|-------------|
| `ARRAY_NUMBER` | Array de numeros enteros |
| `ARRAY_DECIMAL` | Array de numeros decimales |
| `ARRAY_DATE` | Array de fechas |
| `ARRAY_BOOLEAN` | Array de booleanos |
| `ARRAY_ALPHANUMERICAL` | Array de textos alfanumericos |

### Archivos y URLs

| Codigo interno | Descripcion |
|----------------|-------------|
| `UPLOAD_FILE` | Subida de archivo |
| `UPLOAD_URL` | Enlace URL |
| `ARRAY_UPLOAD_FILE` | Array de archivos |
| `ARRAY_UPLOAD_URL` | Array de URLs |

---

## 4. Definicion de atributos: name y label

Cada atributo de metadato se define con dos identificadores:

- **`label`**: Nombre visible para el usuario (por ejemplo: "Fecha de creacion", "Nivel de confidencialidad"). Es el texto que se muestra en la interfaz. Admite espacios, tildes y caracteres especiales.
- **`name`**: Nombre tecnico interno, generado automaticamente a partir del label en formato **camelCase**. Se utiliza como identificador en la API, en validaciones y como clave de traduccion.

### Reglas de generacion del name (camelCase)

1. Eliminar tildes y diacriticos (a->a, e->e, i->i, o->o, u->u).
2. Separar por espacios y caracteres especiales.
3. Primera palabra en minusculas, palabras siguientes con inicial mayuscula.
4. Eliminar caracteres no alfanumericos.

### Ejemplos

| Label (visible) | Name (interno) |
|------------------|----------------|
| Encriptar | `encriptar` |
| Fecha de creacion | `fechaDeCreacion` |
| Nivel de confidencialidad | `nivelDeConfidencialidad` |
| URL del recurso | `urlDelRecurso` |
| Dominio | `dominio` |

---

## 5. Atributos de tipo selector y sus valores de referencia

Los atributos de tipo selector permiten al usuario elegir entre un conjunto de valores predefinidos. Estos valores se denominan **valores de referencia** y son configurados por el administrador.

### Tipos que admiten valores de referencia

| Codigo interno | Descripcion |
|----------------|-------------|
| `SELECT` | Selector de valor unico |
| `MULTI_SELECT` | Selector multiple |
| `SELECT_IMG_TXT` | Selector de imagen con texto |
| `MULTI_SELECT_IMG_TXT` | Selector multiple de imagen con texto |
| `SELECT_IMG` | Selector de imagen |
| `MULTI_SELECT_IMG` | Selector multiple de imagen |
| `TREE_SELECT` | Selector de taxonomia |
| `TREE_MULTISELECT` | Selector multiple de taxonomia |

### Caracteristicas de los valores de referencia

- Se definen por cada atributo de tipo selector.
- Cada valor tiene un texto (`value`) que se muestra al usuario.
- Los valores de referencia son traducibles a los idiomas configurados.
- **Excepcion de traduccion**: Nombres comerciales (AWS, Denodo, Azure) o terminos tecnicos de uso universal (Raw data, Datawarehouse, Datalake) se mantienen iguales en todos los idiomas.

---

## 6. Reutilizacion de atributos en multiples plantillas

Un mismo atributo de metadato (definicion de atributo) puede asociarse a las plantillas de **mas de un tipo de objeto**. La asociacion se realiza mediante un registro de **TemplateAttribute** que vincula la definicion del atributo con una seccion concreta de un menu de un tipo de objeto.

### Como funciona

1. La **definicion de atributo** (`attributeDefinition`) se crea una sola vez. Define el tipo, label, name y descripcion.
2. Para cada tipo de objeto donde se quiera usar, se crea un **TemplateAttribute** que vincula la definicion con una seccion especifica.
3. Cada TemplateAttribute es independiente y puede tener:
   - Su propia posicion (`sort`) dentro de la seccion.
   - Su propio estado de activacion (`active`).
   - Su propia visibilidad (`isVisible`).
   - Su propio conjunto de validaciones.

### Ejemplo

El atributo "Dominio" (tipo `SELECT`) se define una vez y se asocia a tres entidades distintas:

| Tipo de objeto | Menu | Seccion | Posicion |
|----------------|------|---------|----------|
| DATASET | General | Clasificacion | 1 |
| SISTEMA_ORIGEN | General | Gobernanza | 3 |
| APLICACION | Configuracion | Metadatos | 1 |

En cada caso, el atributo puede tener validaciones diferentes (por ejemplo, obligatorio en DATASET pero opcional en APLICACION).

---

## 7. Validaciones de atributos

Se pueden configurar validaciones sobre los atributos asignados a las plantillas de un tipo de objeto. Las validaciones disponibles varian segun el tipo del atributo.

### Catalogo de validaciones

| Clave | Parametro | Tipos aplicables | Descripcion |
|-------|-----------|------------------|-------------|
| `REQUIRED` | `"true"` | Todos **salvo `INPUT_CHECKBOX`** (una casilla siempre tiene valor; para exigir una confirmacion, usar un `SELECT` Si/No obligatorio) | Marca el campo como obligatorio |
| `MAX` | valor numerico | `INPUT_NUMBER`, `INPUT_DECIMAL`, `INPUT_RANGE` | Valor maximo permitido |
| `MIN` | valor numerico | `INPUT_NUMBER`, `INPUT_DECIMAL`, `INPUT_RANGE` | Valor minimo permitido |
| `MAX_DECIMAL_PRECISION` | valor numerico | `INPUT_DECIMAL` | Numero maximo de decimales |
| `MIN_DECIMAL_PRECISION` | valor numerico | `INPUT_DECIMAL` | Numero minimo de decimales |
| `MAX_LENGTH` | valor numerico | Tipos de texto (`INPUT_TEXT`, `TEXT_AREA`, variantes internacionales y enriquecidas) y `ARRAY_ALPHANUMERICAL` | Longitud maxima de caracteres |
| `MIN_LENGTH` | valor numerico | Los mismos que `MAX_LENGTH` | Longitud minima de caracteres |
| `MAX_LENGTH_ARRAY` | valor numerico | Tipos con varios valores (`ARRAY_*`, `ARRAY_ENTITY`, `MULTI_SELECT`, `MULTI_SELECT_IMG_TXT`, `MULTI_SELECT_IMG`, `MULTI_USERS`, `MULTI_ORGANIZATIONAL_UNIT`, `TREE_MULTISELECT`) | Numero maximo de elementos |
| `MIN_LENGTH_ARRAY` | valor numerico | Los mismos que `MAX_LENGTH_ARRAY` | Numero minimo de elementos |
| `NOT_EDITABLE` | `"true"` | Todos | El campo no se puede modificar de ninguna forma tras la creacion (ni en la interfaz, ni por API) |
| `HERITABLE` | `name` del atributo origen | Solo `INPUT_CHECKBOX` (booleano) | El valor se hereda del objeto padre en la jerarquia |
| `DEPENDS_ON` | `name` del atributo origen | Solo `SELECT` y `MULTI_SELECT` | Filtra los valores disponibles del selector en funcion del valor de otro atributo |
| `SUBTYPE_FILTER` | `name` de uno o varios subtipos separados por `_-` | Solo `ENTITY_SEARCH` y `ARRAY_ENTITY` (**obligatoria** en todos ellos) | Restringe que subtipos de entidad se pueden seleccionar |

La plataforma acepta validaciones aplicadas a un tipo incompatible, pero la interfaz las ignora: comprobar siempre el tipo antes de crearlas.

### Nota sobre DEPENDS_ON

La validacion `DEPENDS_ON` requiere dos pasos:
1. Crear la validacion indicando el `name` del atributo del que depende.
2. Crear relaciones entre valores (`attributeRelationShips`) que definen que valores del atributo origen habilitan que valores del atributo destino.

---

## 8. Capas de linaje y agrupaciones

El linaje en Anjana Data permite visualizar las relaciones y flujos entre entidades en un panel grafico. La configuracion del linaje se basa en **capas** y **agrupaciones**.

### Capas de linaje (layers)

- Una capa define una vista del linaje que muestra un subconjunto de entidades y relaciones.
- Se pueden crear multiples capas para ofrecer diferentes perspectivas del linaje.
- Cada capa puede contener:
  - Subtipos de entidad (nativos o personalizados).
  - Subtipos de relacion (nativos o personalizados).
- Una capa puede marcarse como **default** (capa por defecto que se muestra inicialmente).

### Agrupaciones (groupings)

Las agrupaciones permiten definir relaciones de agregacion (jerarquicas) dentro de una capa de linaje. Por ejemplo, que los campos de un dataset se agrupen visualmente bajo su dataset padre.

#### Requisitos para la agrupacion

La relacion utilizada como agrupacion debe ser:
- Una relacion nativa de Anjana (como `STRUCTURE`, `INSTANCE_DATASET_IN`, etc.), **o**
- Una relacion personalizada creada con `parental: true`.

#### Definicion de una agrupacion

Cada agrupacion se define con tres elementos:
- **`sourceSubtype`**: Tipo de entidad origen (padre en la jerarquia).
- **`destinationSubtype`**: Tipo de entidad destino (hijo en la jerarquia).
- **`relationshipSubtype`**: Tipo de relacion que conecta origen y destino.

Una vez creada la agrupacion, se asigna a una o mas capas de linaje para que sea visible en ellas.

### Ejemplo

```
Capa: "Vista completa"
  Entidades: DATASET, DATASET_FIELD, PROCESS, INSTANCE
  Relaciones: STRUCTURE, INSTANCE_DATASET_IN, INSTANCE_DATASET_OUT
  Agrupaciones:
    - DATASET agrupa DATASET_FIELD via STRUCTURE
    - PROCESS agrupa INSTANCE via INSTANCE_PROCESS
```

---

## 9. Filtros

La plataforma permite configurar **filtros** que aparecen en el buscador (portal de busqueda) para facilitar la localizacion de activos. Cada filtro se asocia a un atributo de metadato existente.

### Caracteristicas de los filtros

- Un filtro presenta un control en la interfaz del buscador que permite refinar los resultados segun el valor de un atributo.
- El tipo de control del filtro se determina automaticamente a partir del tipo del atributo subyacente.
- Los filtros pueden ser **principales** (`main: true`, visibles por defecto) o **secundarios** (`main: false`, el usuario los anade bajo demanda).
- Cada filtro tiene una posicion (`position`) que determina su orden en el panel de filtros.

### Correspondencia entre tipo de atributo y tipo de filtro

| Tipos de atributo | Tipo de filtro resultante |
|--------------------|--------------------------|
| `INPUT_DATE` | `INPUT_DATE_RANGE` (rango de fechas) |
| `INPUT_DECIMAL`, `INPUT_NUMBER` | `INPUT_NUMBER_RANGE` (rango numerico) |
| `ENTITY_SEARCH`, `ARRAY_ENTITY` | `ENTITY` (busqueda de entidad) |
| `SELECT_USERS`, `MULTI_USERS` | `SELECT_USERS` (selector de usuarios) |
| `TREE_SELECT`, `TREE_MULTISELECT` | `MULTI_SELECT_TREE` (arbol de taxonomia) |
| `SELECT_ORGANIZATIONAL_UNIT`, `MULTI_ORGANIZATIONAL_UNIT` | `MULTI_SELECT_TREE_OU` (arbol de unidades organizativas) |
| `INPUT_CHECKBOX` | `BOOLEAN` (si/no) |
| `SELECT`, `MULTI_SELECT`, `SELECT_IMG`, `MULTI_SELECT_IMG`, `SELECT_IMG_TXT`, `MULTI_SELECT_IMG_TXT` | `MULTI_SELECT` (selector multiple) |

### Requisitos adicionales

- Cada filtro requiere traducciones de su etiqueta en todos los idiomas configurados.
- Tras crear un filtro y sus traducciones, es necesario publicar las traducciones y limpiar la cache para que el filtro sea visible en la interfaz.

---

## 10. Idiomas

Anjana Data Platform soporta multiples idiomas. La plataforma incluye por defecto espanol (`es-ES`) e ingles (`en-US`), y se pueden anadir idiomas adicionales.

### Idiomas soportados

Los codigos se aceptan en minusculas o mayusculas. Solo son validos los codigos i18n oficiales: codigos inventados como `es-ES1` no funcionan. El catalogo completo (mas de 250 combinaciones pais/idioma) esta publicado en `https://wiki.anjanadata.com/es/configuracion/26.1/customizar-iconografia-y-css`.

Los mas habituales:

| Codigo i18n | Idioma |
|-------------|--------|
| `es-ES` | Espanol (incluido por defecto) |
| `en-US` | Ingles USA (incluido por defecto) |
| `en-UK` | Ingles Reino Unido |
| `es-CT` | Catalan |
| `es-GA` | Gallego |
| `es-PV` | Euskera |
| `de-DE` | Aleman |
| `fr-FR` | Frances |
| `it-IT` | Italiano |
| `pt-PT` | Portugues |
| `br-BR` | Portugues (Brasil) |
| `mx-MX` | Espanol (Mexico) |
| `es-CL` | Espanol (Chile) |

### Impacto de anadir un idioma

**Versiones 25.1 y 25.2**:
1. Registrar el idioma en la plataforma.
2. Crear traducciones internas (textos de la interfaz y notificaciones del sistema).
3. Crear traducciones de configuracion de usuario (labels de atributos, descripciones, valores de selectores, nombres de menus, secciones, capas, unidades organizativas, roles, etc.).
4. Crear traducciones del nombre del idioma en todos los idiomas existentes.
5. Publicar las traducciones para que sean visibles.

**Version 26.1** (API de i18n rehecha):
1. Crear el idioma con `action: "CREATE"` en el endpoint `submit`, indicando si queda activo y si es el idioma por defecto.
2. Enviar las claves de traduccion en el mapa `values` de ese mismo `submit`, o en llamadas posteriores con `action: "UPDATE"`. Un unico `values` cubre tanto las claves internas (cuyo valor se sobreescribe) como las de configuracion de usuario: la distincion `internal` desaparece.
3. **No** hay que traducir el nombre del idioma: la plataforma lo resuelve sola.
4. **No** hay paso de publicacion: `submit` publica directamente.

En ambos casos, limpiar la cache del sistema al terminar.

---

## 11. Traducciones

El sistema de traducciones de Anjana gestiona todos los textos visibles en la plataforma. Hay dos categorias:

> **Cambio en 26.1**: al **escribir**, una traduccion es simplemente un par clave-valor dentro del mapa `values` del endpoint `submit`: los campos `internal` y `usedFor` no se envian. Al **leer** con `translations/v1/search` ambos campos siguen viniendo en la respuesta, asi que la distincion entre las dos categorias sigue siendo consultable. Ademas, en 26.1 **no se pueden crear** traducciones internas nuevas: solo actualizar el valor de las que la plataforma ya trae.
>
> **Traducciones ausentes en 26.1**: si una clave no tiene valor en el idioma del usuario, la interfaz muestra el valor del idioma por defecto; si tampoco existe, el de `en-US`; y si tampoco, la propia clave. Por eso **ninguna clave debe quedar sin valor en ningun idioma registrado**: un `es-ES` vacio con `en-US` relleno muestra el texto en ingles a los usuarios en espanol. Muchas claves tienen `es-ES` a `null` porque la propia `configKey` es el texto en castellano: al traducir desde espanol se usa `values["es-ES"]` si existe o la `configKey` si es `null`, y se escribe tambien como valor de `es-ES`. En claves tecnicas (`FILTERS.*`, `RESPONSE.CODE.*`, `ROLE.*`) nunca se escribe el identificador como texto: se pide el texto real.

### Traducciones internas (`internal: true` hasta 25.2)

- Textos de la interfaz de usuario, notificaciones y mensajes del sistema.
- Vienen preconfiguradas para `es-ES` y `en-US`.
- Para idiomas adicionales, se traducen a partir de los textos en espanol.
- Pueden contener **tokens de sustitucion** (por ejemplo `#OBJECT_NAME#`, `#USER_NAME#`) que no deben traducirse.

### Traducciones de configuracion (`internal: false` hasta 25.2)

Son las traducciones de todos los elementos configurados por el usuario. Las fuentes de claves de traduccion son:

| Elemento | Clave de traduccion | Valor a traducir |
|----------|---------------------|------------------|
| Label de atributo | El texto del `label` (no el `name` tecnico) | El `label` en cada idioma |
| Descripcion de atributo | El texto de la `description` | La `description` en cada idioma |
| Valor de selector | Texto del `value` | El propio texto del valor |
| Nombre de capa de linaje | `name` de la capa | El `name` de la capa |
| Nombre de menu | `name` del menu | El `name` del menu |
| Descripcion de menu | `description` del menu | La `description` del menu |
| Nombre de seccion | `name` de la seccion | El `name` de la seccion |
| Descripcion de seccion | `description` de la seccion | La `description` de la seccion |
| Nombre de unidad organizativa | `alias` de la OU | El `alias` de la OU |
| Nombre de rol | `"ROLE." + name` del rol | La `description` del rol |

### Reglas de traduccion

- **Conservacion de mayusculas**: Si el texto original esta en mayusculas (por ejemplo `INFORME`), la traduccion debe mantenerse tambien en mayusculas.
- **Conservacion de tokens**: Los tokens como `#OBJECT_NAME#` deben preservarse intactos en la traduccion.
- **Nombres comerciales y terminos tecnicos**: Valores como AWS, Denodo, Azure, Raw data, Datawarehouse o Datalake se mantienen iguales en todos los idiomas, sin traducir.
- **Publicacion obligatoria (solo 25.1 y 25.2)**: Las traducciones no publicadas no son visibles en la interfaz. Tras crear o modificar traducciones hay que publicarlas y limpiar la cache del sistema. En **26.1** el endpoint `submit` publica por si mismo y no existe paso de publicacion: solo hay que limpiar la cache.
