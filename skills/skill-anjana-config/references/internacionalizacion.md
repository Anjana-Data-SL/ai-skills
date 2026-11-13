## Entidad: Internacionalización (Idiomas)

Anjana soporta múltiples idiomas. Antes de habilitar contenido multi-idioma, los idiomas deseados deben registrarse en la plataforma.

> **División por versión: léelo primero.** La versión **26.1 sustituyó toda la API de i18n**. Los idiomas y las traducciones ya no son recursos separados: ambos se escriben mediante un único endpoint `submit` y no existe paso de publicación. Comprueba `<ANJANA_VERSION>` antes de hacer nada en esta sección:
>
> | | 25.1 / 25.2 | 26.1 |
> |---|---|---|
> | Listar idiomas y traducciones | `GET /api/portuno/api/filter/languages`, `GET /api/portuno/api/filter/translations` | `POST /portuno/translations/v1/search` |
> | Crear un idioma | `POST /portuno/languages` | `POST /portuno/i18n/v1/submit` con `"action": "CREATE"` |
> | Actualizar un idioma | - | `POST /portuno/i18n/v1/submit` con `"action": "UPDATE"` |
> | Escribir claves de traducción | `POST /portuno/translations` (una llamada por clave) | mapa `values` dentro de la misma llamada `submit` |
> | Campos `internal` / `usedFor` | Sí, en lectura y escritura | `search` los sigue **devolviendo**, pero **no se aceptan** en escritura: `submit` solo admite clave → valor |
> | Paso de publicación | `PUT /public/v4/translations/upload`: **obligatorio** | **Ninguno**: `submit` publica directamente |
> | Traducción del nombre del idioma (clave = el propio código) | Obligatoria en todos los idiomas | **No necesaria** |
>
> **Los pasos 1, 2, 3c y 4 de más abajo son específicos de cada versión.** El catálogo de claves de traducción del paso 3, las APIs de traducción automática y todas las reglas de traducción (conservación de mayúsculas, tokens `#PLACEHOLDER#`, nombres comerciales) se aplican igual a **todas las versiones**: solo cambia el transporte.

### Paso 1: Comprobar los idiomas existentes

**Versiones 25.1 y 25.2**:
```bash
GET <BASE_URL>/gateway/api/portuno/api/filter/languages?page=0&size=20&sequenceOrder=id
```

**Versión 26.1**: los idiomas y sus claves de traducción se leen desde el mismo endpoint de búsqueda:
```bash
POST <BASE_URL>/gateway/api/portuno/translations/v1/search
```

**Body de la petición**:
```json
{"pageable":{"page":0,"size":30,"sort":["configKey,asc"]}}
```

**Estructura de la respuesta**: una fila por clave de traducción, con un mapa `values` que contiene **todos los idiomas registrados**. Un idioma que no tiene traducción para esa clave devuelve `null`:
```json
{
  "code": "0000",
  "description": "Successful operation.",
  "data": {
    "results": [
      {
        "configKey": "ACCOUNTING",
        "usedFor": null,
        "internal": false,
        "values": {"en-US": "Accounting", "es-ES": "Contabilidad", "es-CL": null}
      }
    ],
    "page": 0,
    "size": 30,
    "totalElements": 1500,
    "totalPages": 50
  }
}
```

Notas sobre la respuesta:
- **Los idiomas registrados son las claves del mapa `values` de cualquier fila**: así se comprueba si un idioma ya existe. En 26.1 no hay un endpoint separado para listar idiomas.
- **`internal` y `usedFor` se siguen devolviendo aquí** aunque `submit` no los acepte en escritura. Usa `internal` para distinguir las claves propias de la plataforma de las claves de configuración de usuario al decidir qué traducir.
- **Pagina**: usa `data.totalPages` e itera `page` desde 0 en adelante. Una sola llamada solo devuelve `size` claves. `size: 500` funciona bien y reduce un catálogo de varios miles de claves a un puñado de llamadas.
- **`configKey` no está garantizada como única.** La misma clave puede aparecer dos veces con distinto `internal` / `usedFor`. Como el `values` de `submit` es un mapa plano, no se puede apuntar a una de las dos filas: avisa de esas claves al usuario en lugar de adivinar.

Revisa la respuesta para ver qué idiomas ya están registrados. Si el idioma requerido ya está presente, omite el paso 2 y ve directamente al paso 3.

#### Cómo se muestran las traducciones que faltan: nunca dejes una clave vacía (obligatorio)

**En 26.1**, cuando una clave no tiene valor para el idioma del usuario, la UI muestra, por este orden:
1. el valor en el idioma configurado como **predeterminado**;
2. si no hay, el valor en **`en-US`**;
3. si tampoco hay, **la propia clave**.

Consecuencias: un `es-ES` vacío junto a un `en-US` relleno hace que los usuarios vean el texto en inglés (p. ej., una capa creada como "Vista de negocio" con solo `en-US = "Business view"` se muestra como "Business view" cuando el español es el idioma predeterminado y falta su valor); y una clave vacía en todos los idiomas muestra la clave en bruto (`FILTERS.DOMINIO`, `ROLE.DATA_STEWARD`). En 25.1 / 25.2 la UI recurre al texto almacenado en español, pero la regla siguiente se aplica a todas las versiones.

**Regla: nunca dejes una clave de traducción sin valor en ningún idioma registrado.**
- Siempre que esta skill escriba una clave, escríbela **en todos los idiomas registrados** (las claves de cualquier mapa `values` devuelto por `search`), en el mismo `submit` cuando sea posible, incluidos el idioma predeterminado y `es-ES`.
- Tras escribir, vuelve a leer la clave con `search` y confirma que ningún idioma registrado está a `null`. Comunica cualquier hueco al usuario.
- Si el usuario no puede o no quiere proporcionar un valor para algún idioma, indícale exactamente qué verán los usuarios de ese idioma (según el orden anterior) y pide confirmación explícita antes de dejarlo vacío.

**Dónde está el texto fuente en español.** Muchas claves tienen `es-ES` = `null` porque la propia `configKey` *es* el texto en español. Al traducir desde el español, usa `values["es-ES"]` cuando exista; cuando sea `null` y la clave se lea como lenguaje natural, usa la `configKey` como texto en español **y escríbela también como valor de `es-ES`** (para que los usuarios en español no caigan a `en-US`). Para claves técnicas (`FILTERS.*`, `RESPONSE.CODE.*`, `ROLE.*`, identificadores con puntos en mayúsculas) con valor español `null`, nunca escribas el identificador como texto visible: pide al usuario el texto real en cada idioma.

### Paso 2: Crear un idioma nuevo (si no está ya registrado)

#### Versiones 25.1 y 25.2

**Endpoint**: `POST <BASE_URL>/gateway/api/portuno/languages`

**Body de la petición**:
```json
{
    "i18nCode": "en-US",
    "description": "Inglés"
}
```

| Campo | Reglas |
|-------|-------|
| `i18nCode` | Debe ser uno de los códigos válidos listados abajo (no distingue mayúsculas/minúsculas) |
| `description` | Nombre legible para el idioma, tal como lo proporciona el usuario |

#### Versión 26.1

**Endpoint**: `POST <BASE_URL>/gateway/api/portuno/i18n/v1/submit`

**Body de la petición**: una entrada por idioma bajo `languages`, con el código del idioma como clave:
```json
{
    "languages": {
        "es-CL": {
            "active": false,
            "defaultLang": false,
            "action": "CREATE",
            "values": {}
        }
    }
}
```

| Campo | Reglas |
|-------|-------|
| *(clave del mapa)* | El código del idioma a crear, p. ej. `"es-CL"`. Ver códigos válidos más abajo |
| `active` | `true` / `false`: si el idioma se puede seleccionar en la UI. Créalo con `false` mientras las traducciones estén incompletas y luego cámbialo a `true` con un `UPDATE` |
| `defaultLang` | `true` / `false`: si es el idioma predeterminado de la plataforma |
| `action` | `"CREATE"` para un idioma nuevo |
| `values` | Mapa clave de traducción → valor. Puede dejarse vacío (`{}`) y rellenarse después, o rellenarse en la misma llamada (ver paso 3) |

Se pueden crear varios idiomas en una sola llamada añadiendo más entradas al mapa `languages`.

#### Versión 26.1: actualizar un idioma existente

Mismo endpoint, con `action` a `"UPDATE"`:

```json
{
    "languages": {
        "es-CL": {
            "active": true,
            "defaultLang": false,
            "action": "UPDATE",
            "values": {}
        }
    }
}
```

Usa `UPDATE` para activar/desactivar un idioma, cambiar el idioma predeterminado o añadir claves de traducción a un idioma que ya existe. **Activar o desactivar un idioma y cambiar el idioma predeterminado modifican el entorno para todos los usuarios: aplica el protocolo de confirmación explícita ("Operaciones que modifican o borran") antes de enviarlos.** Lo mismo se aplica a un `CREATE` con `defaultLang: true`.

### Códigos de idioma válidos

Los códigos se aceptan en **minúsculas o mayúsculas** (`es-cl` y `es-CL` funcionan ambos). Solo funcionan los códigos i18n oficiales: códigos inventados como `es-ES1` no funcionarán.

Códigos de uso común:

| Código | Idioma |
|------|----------|
| `es-es` | Español |
| `es-ct` | Catalán |
| `es-ga` | Gallego |
| `es-pv` | Euskera |
| `en-uk` | Inglés (Reino Unido) |
| `en-us` | Inglés (USA) |
| `de-de` | Alemán |
| `fr-fr` | Francés |
| `it-it` | Italiano |
| `pt-pt` | Portugués |
| `br-br` | Portugués (Brasil) |
| `mx-mx` | Español (México) |
| `ar-ar` | Español (Argentina) |

El catálogo completo (más de 250 combinaciones país/idioma, p. ej. `es-CL` para Chile) está publicado en:
`https://wiki.anjanadata.com/es/configuracion/26.1/customizar-iconografia-y-css`

Si el usuario pide un idioma que no está en la tabla anterior, consulta esa página en lugar de adivinar el código.

### Paso 3: Configurar las traducciones

Las traducciones asocian una clave a un valor mostrado para un idioma determinado.

#### Versiones 25.1 y 25.2: una llamada por clave

**Endpoint**: `POST <BASE_URL>/gateway/api/portuno/translations`

**Body de la petición**:
```json
{
    "key": "Sistemas dependientes",
    "language": "en-US",
    "usedFor": null,
    "internal": false,
    "value": "Dependent systems"
}
```

| Campo | Reglas |
|-------|-------|
| `key` | La clave de traducción (ver catálogo más abajo) |
| `language` | Un `i18nCode` válido que ya esté registrado como idioma en la plataforma. Verifícalo con `GET /api/portuno/api/filter/translations` |
| `usedFor` | Siempre `null` salvo que el usuario proporcione explícitamente un valor |
| `internal` | `false` para traducciones de configuración de usuario. `true` para traducciones nativas de la plataforma |
| `value` | El texto traducido que verá el usuario para este idioma |

#### Versión 26.1: las claves van en el mapa `values` de `submit`

No existe un endpoint por clave. Las claves de traducción se escriben mediante la misma llamada `submit` que se usa para crear o actualizar el idioma, en el objeto `values`: **cada propiedad es una clave de traducción, cada valor es el texto traducido para ese idioma**.

**Endpoint**: `POST <BASE_URL>/gateway/api/portuno/i18n/v1/submit`

**Body de la petición**:
```json
{
    "languages": {
        "es-CL": {
            "action": "UPDATE",
            "values": {
                "Ordenador personal": "Computador personal",
                "Sistemas dependientes": "Sistemas dependientes"
            }
        }
    }
}
```

Reglas específicas de 26.1:
- **`values` funciona tanto en la creación como en cualquier momento posterior**: incluye claves en la llamada `CREATE` o envíalas más tarde con `action: "UPDATE"`.
- **Una clave ya existente se sobrescribe** con el nuevo valor; una clave que no existe se añade. Antes de cada lote, comprueba con `search` qué claves ya tienen valor en el idioma de destino: si alguna lo tiene, el lote sobrescribe configuración existente y requiere el protocolo de confirmación explícita ("Operaciones que modifican o borran"), indicando cuántos valores se sobrescribirán. Las claves nuevas para ese idioma son una creación normal.
- **`internal` y `usedFor` no se aceptan en escritura.** Cualquier clave traducible va en el mismo mapa plano: nombres de menús, nombres de secciones, etiquetas y descripciones de atributos, placeholders, valores de selectores, etiquetas de filtros, nombres de roles, asuntos y cuerpos de notificaciones. (Ambos campos se siguen *devolviendo* en `search`; ver paso 1.)
- **Las traducciones internas (nativas de la plataforma) no se pueden crear en 26.1**: son propiedad de la plataforma. Lo que `submit` permite es *sobrescribir el valor* de una clave interna que ya existe, incluyendo esa clave en `values`. Lee las claves existentes con `POST /portuno/translations/v1/search` (paso 1) antes de sobrescribir, y aplica el protocolo de confirmación explícita siempre que una clave interna ya tenga valor en el idioma de destino: esos textos son la propia interfaz de la plataforma.
- **Agrupa en lotes grandes.** Envía muchas claves por llamada en lugar de una llamada por clave, y varios idiomas en el mismo mapa `languages` cuando traduzcas a más de uno. **Los lotes de 500 claves por `submit` funcionan.** Si un lote falla, comunícaselo al usuario; con su acuerdo, reintenta el lote partido por la mitad para aislar la clave problemática, en lugar de recurrir a una llamada por clave.
- **`values` es un mapa plano clave → valor**, por lo que una `configKey` que aparece más de una vez en `search` no se puede apuntar individualmente; ver la nota sobre claves duplicadas en el paso 1.
- **Sin paso de publicación**: ver paso 4.

#### Catálogo de claves de traducción (traducciones de configuración de usuario, `internal: false`)

Realiza **10 llamadas a la API** para reunir todos los datos necesarios. Cada llamada produce un tipo de traducción:

| Llamada a la API | Traducciones extraídas |
|----------|------------------------|
| `GET /api/portuno/api/filter/attributeDefinitions` | **Etiquetas de atributos**: clave = el texto de **`label`** (p. ej. `"Fecha de revisión"`), **nunca el `name` técnico** (`fechaDeRevision`); valor = la etiqueta en cada idioma (verificado en 26.1: prácticamente todos los atributos usan el texto de la etiqueta como clave, casi ninguno el `name`) |
| `GET /api/portuno/api/filter/attributeDefinitions` | **Descripciones de atributos**: clave = el texto de **`description`**; valor = la descripción en cada idioma |
| `GET /api/portuno/api/filter/attributeDefinitionValues` | **Valores de selector**: clave=`value`, valor=traducción de `value` |
| `GET /api/portuno/api/filter/layers` | **Nombres de capas**: clave=`name`, valor=traducción de `name` |
| `GET /api/portuno/api/filter/menus` | **Nombres de menús**: clave=`name`, valor=traducción de `name` |
| `GET /api/portuno/api/filter/menus` | **Descripciones de menús**: clave=`description`, valor=traducción de `description` |
| `GET /api/portuno/api/filter/sections` | **Nombres de secciones**: clave=`name`, valor=traducción de `name` |
| `GET /api/portuno/api/filter/sections` | **Descripciones de secciones**: clave=`description`, valor=traducción de `description` |
| `GET /api/portuno/api/filter/organizationalUnits` | **Nombres de UO**: clave=`alias`, valor=traducción de `alias` |
| `GET /api/portuno/api/filter/roles` | **Nombres de roles**: clave=`"ROLE." + name`, valor=traducción de `description` |

**Regla especial para valores de selector**: si el valor es un nombre comercial (p. ej., AWS, Denodo, Azure) o un término del sector de datos de uso habitual sin traducir (p. ej., Raw data, Datawarehouse, Datalake), usa el **mismo valor en todos los idiomas**: no lo traduzcas.

#### Lógica para generar todas las traducciones de un idioma

Cuando se pida generar todas las traducciones de un idioma, sigue este orden:

**Paso 3a: traducciones internas / de plataforma**:
- Para **es-ES** o **en-US**: las traducciones internas vienen preconfiguradas, omite este paso por completo.
- Para **cualquier otro idioma**, el texto fuente a traducir es el texto de plataforma en español. Cómo se lee y se escribe depende de la versión:

**Versiones 25.1 y 25.2**: obtén como referencia las traducciones internas en español:
```bash
GET <BASE_URL>/gateway/api/portuno/api/filter/translations?languageEquals=es-ES&internalEquals=true
```
Después crea una traducción por cada entrada con `POST /portuno/translations`, traduciendo el `value` del español al idioma de destino. Reglas:
- **`internal: true`**: establece siempre `internal` a `true` en estas traducciones, nunca `false`.
- **Conserva `usedFor`**: copia el campo `usedFor` de la entrada original en español (no lo fijes a `null`).

**Versión 26.1**: recorre página a página `POST /portuno/translations/v1/search` (paso 1) para reunir las claves existentes y sus valores en español, traduce cada valor y envíalos de vuelta en el mapa `values` de una llamada `submit` para el idioma de destino. Filtra por el indicador `internal: true` que devuelve la búsqueda para seleccionar las claves propias de la plataforma. No reenvías `internal` ni `usedFor`: las filas ya existen, así que `submit` está *sobrescribiendo su valor para el nuevo idioma*, que es la única operación que 26.1 permite sobre las traducciones internas. Cuando `es-ES` sea `null`, toma el texto fuente en español como se describe en "Cómo se muestran las traducciones que faltan: nunca dejes una clave vacía" (paso 1), y escribe también `es-ES`: ningún idioma registrado puede quedar vacío.

**Se aplica a todas las versiones**:
- **Conserva los tokens `#PLACEHOLDER#`**: si el valor original contiene texto envuelto en `#` (p. ej., `#OBJECT_NAME#`, `#USER_NAME#`), mantén esos tokens exactamente como están y traduce solo el texto que los rodea. Ejemplo: `"Workflow finalizado para #OBJECT_NAME#"` → `"Lan-fluxua osatuta #OBJECT_NAME#"`.

**APIs de traducción**: se proponen por defecto dos APIs, según el idioma de destino: MyMemory para todos los idiomas excepto el euskera, e Itzuli para el euskera (`es-pv`).

> **Aviso sobre servicios de terceros: obligatorio antes de cualquier traducción automática.** MyMemory (Translated) e Itzuli (Vicomtech) son **servicios externos no operados por Anjana**. Usarlos implica enviarles los textos a traducir (etiquetas y descripciones de atributos, valores de referencia, nombres de UO y de roles, textos de notificaciones), es decir, el contenido de configuración del entorno, que puede incluir información sobre la organización o sus clientes y, en el caso de MyMemory, la dirección de correo del usuario. Antes de enviar ningún texto, explícaselo al usuario y pídele que elija:
> 1. **Usar MyMemory / Itzuli**, tras comprobar que la política de datos de su organización (o de su cliente) permite enviar este contenido a esos servicios.
> 2. **Usar otro servicio de traducción** de su elección: pide su endpoint, autenticación y códigos de idioma, y adapta las llamadas siguientes (mantén el enmascarado de placeholders, la conservación de mayúsculas y las reglas de cuota).
> 3. **Ningún servicio de traducción externo**: traduce los textos directamente en esta conversación, o usa las traducciones que proporcione el usuario.
>
> No envíes ningún texto a un servicio externo hasta que el usuario haya elegido de forma explícita. La elección se aplica a toda la tarea de traducción; vuelve a preguntar si la tarea cambia de entorno.

**Solo si el usuario eligió MyMemory**: antes de empezar, pide al usuario su dirección de correo electrónico. Guárdala como `<USER_EMAIL>`. Se usa como identificador en MyMemory para elevar la cuota diaria de 5.000 a **50.000 palabras/día por usuario**. Como esta skill la comparten varios usuarios, cada uno debe proporcionar su propio correo para beneficiarse de su propia cuota independiente.

---

#### API 1: MyMemory (todos los idiomas excepto el euskera)

**Endpoint**:
```
GET https://api.mymemory.translated.net/get?q=<url-encoded-text>&langpair=<pair>&de=<USER_EMAIL>
```

- No requiere API key: el parámetro `de` (correo del usuario) es el identificador de la cuota de 50.000 palabras/día.
- Haz las llamadas desde un script que lea los textos de un fichero y los codifique como URL (ver "Construcción segura de comandos", regla 7): nunca pongas el texto a traducir dentro de un comando de shell.
- **Respuesta**: extrae `responseData.translatedText`
- **Comprobación de cuota**: si `quotaFinished` es `true` en la respuesta, detente e informa al usuario.

**`langpair` según el i18nCode de Anjana**:

| i18nCode de Anjana | Idioma   | `langpair` de MyMemory |
|-----------------|------------|---------------------|
| `es-ct`         | Catalán    | `es\|ca`            |
| `es-ga`         | Gallego    | `es\|gl`            |
| `en-uk`         | Inglés (Reino Unido) | `es\|en`            |
| `en-us`         | Inglés (EE. UU.)    | `es\|en`            |
| `de-de`         | Alemán     | `es\|de`            |

---

#### API 2: Itzuli / Vicomtech (solo euskera: `es-pv`)

Traductor oficial del Gobierno Vasco (Eusko Jaurlaritza). La API key debe solicitarse en: `https://itzuli.vicomtech.org/en/api/`

Pide al usuario su API key de Itzuli cuando el idioma de destino sea `es-pv`. **Seguridad**: igual que el token, deja que el usuario la escriba él mismo en un fichero de `<SECRETS_DIR>` (créalo con la herramienta de escritura de ficheros y facilítale la ruta) en lugar de pegarla en la conversación: lo que se pega queda en la transcripción. A diferencia del token, esta clave **no caduca**: nunca la imprimas, borra su fichero en cuanto termine la tarea de traducción (no la conserves durante el resto de la sesión) y, si se pegó en la conversación, recomienda al usuario que la rote después. El script de traducción la lee de ese fichero; más abajo se denomina `<ITZULI_API_KEY>`.

**Endpoint**: `POST https://api.itzuli.vicomtech.org/translation/get`

**Cabeceras**:
```
Authorization: Bearer <ITZULI_API_KEY>
Content-Type: application/json
```

**Body de la petición**:
```json
{"sourcelanguage": "es", "targetlanguage": "eu", "text": "<source_text>"}
```

**Respuesta**: extrae `translated_text`

Comprueba la cuota restante: `GET https://api.itzuli.vicomtech.org/quota/get` con la misma cabecera Bearer.

---

**Reglas aplicables a todas las APIs**:
- Usa un retardo de 0,35 s entre peticiones para evitar el rate limiting.
- Antes de enviar, enmascara los tokens `#PLACEHOLDER#` con marcadores neutros (p. ej., `XPLACEHOLDER0X`), envía el texto enmascarado y después restaura los tokens originales en el resultado traducido. Tras restaurarlos, comprueba que todos los tokens originales están presentes en la traducción; enumera cualquier texto al que le falte alguno y no lo cargues sin revisión del usuario.
- Detente e informa al usuario si se supera la cuota.

**Regla de conservación de mayúsculas**: si el texto fuente original está completamente en mayúsculas (p. ej. `"INFORME"`, `"ALTO"`), el valor traducido también debe estar completamente en mayúsculas. Aplica `.upper()` al resultado traducido cuando la fuente esté toda en mayúsculas.

**Paso 3b: traducciones de configuración de usuario**:
Para cada idioma, obtén cada tipo de entidad del catálogo anterior y crea una traducción por clave, traduciendo el valor al idioma de destino. En 25.1/25.2 llevan `internal: false`; en 26.1 van en el mapa `values` como cualquier otra clave.

### Paso 3c: Añadir traducciones del nombre del idioma (solo versiones 25.1 y 25.2)

> **No aplicable en 26.1.** La plataforma resuelve por sí misma el nombre del idioma: **no** añadas una traducción cuya clave sea el código del idioma.

Cada vez que se añada un idioma nuevo, crea una traducción con su `i18nCode` como clave en **todos los idiomas existentes** (incluido el propio idioma nuevo), para que el nombre del idioma aparezca correctamente en la UI para todos los usuarios.

Para cada idioma existente (incluido el nuevo), haz POST de:

```json
{"key": "<NEW_LANG_CODE>", "language": "<EXISTING_LANG_CODE>", "usedFor": null, "internal": true, "value": "<LANG_NAME_IN_THAT_LANGUAGE>"}
```

**Ejemplo**: añadir euskera (`es-pv`) a un entorno con es-ES y en-US:

| `key` | `language` | `value` |
|-------|------------|---------|
| `es-pv` | `en-US` | `Basque` |
| `es-pv` | `es-ES` | `Euskera` |
| `es-pv` | `es-pv` | `Euskara` |

Llama siempre a la **subida del paso 4** tras crear estas traducciones.

### Paso 4: Publicar las traducciones (solo versiones 25.1 y 25.2)

Tras crear todas las traducciones, lanza la subida para que sean visibles en la UI de la plataforma:

**Endpoint**: `PUT <BASE_URL>/gateway/public/v4/translations/upload`

**Body de la petición**:
```json
{"headers":{"normalizedNames":{},"lazyUpdate":null}}
```

Una respuesta `{"code":"0000","description":"Successful operation."}` confirma que las traducciones ya están activas. Este paso es **obligatorio**: las traducciones creadas por API no son visibles hasta que se llama a este endpoint.

> **Versión 26.1: omite este paso.** `POST /portuno/i18n/v1/submit` publica las traducciones por sí mismo: no hay un endpoint de subida aparte al que llamar. No invoques `PUT /public/v4/translations/upload` en 26.1.

**Todas las versiones**: ejecuta igualmente la limpieza de caché (`PUT <BASE_URL>/gateway/api/v1/cache/clear-all`) tras cualquier cambio de configuración (paso 7 del "Flujo conversacional").
