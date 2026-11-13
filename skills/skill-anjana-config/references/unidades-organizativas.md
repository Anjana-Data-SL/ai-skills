## Entidad: Unidades Organizativas (OUs)

**Endpoint**: `POST /gateway/api/portuno/organizationalUnits`

Las OUs pueden ser de nivel 1 (raíz) o nivel 2 (hijas de una OU de nivel 1). Pregunta al usuario qué nivel quiere crear.

### OU de Nivel 1 (raíz)

Recopila del usuario:
- **Alias**: Nombre de la OU
- **Descripción**: Descripción breve

Construye el body:
- `module`: Siempre `"ALL"`
- `alias`: El nombre proporcionado por el usuario
- `parent`: `null`
- `description`: Descripción proporcionada por el usuario
- `organizationalUnitType`: `"1"`

**Importante**: Guarda el `identifierKey` de la respuesta: el número al principio (antes del `-`) es el ID de la OU, necesario para OUs hijas, autorización de usuarios y otras referencias.

**Ejemplo de respuesta**:
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

### OU de Nivel 2 (hija)

Recopila del usuario:
- **OU padre**: Qué OU de nivel 1 es la padre (usa el ID del `identifierKey` de una OU recién creada, o pregúntaselo al usuario)
- **Nombre de la hija**: Nombre de la OU hija
- **Descripción** (opcional): Si no se proporciona, usa `null`

Construye el body:
- `module`: Siempre `"ALL"`
- `alias`: Concatena alias del padre + `/` + nombre de la hija (ej: `"Banca/Hipotecas"`)
- `parent`: `<BASE_URL>/gateway/portuno/organizationalUnits/<PARENT_ID>` donde `<PARENT_ID>` es el número del `identifierKey` del padre
- `description`: Descripción proporcionada por el usuario, o `null`
- `organizationalUnitType`: `"2"`

**Ejemplo de body** (hija de "Pharma" con ID 34):
```json
{
    "module": "ALL",
    "alias": "Pharma/compliances",
    "parent": "<BASE_URL>/gateway/portuno/organizationalUnits/34",
    "description": null,
    "organizationalUnitType": "2"
}
```

### OU de Nivel 3 (nieta): solo versión 26.1

En la versión 26.1, las OUs admiten un tercer nivel jerárquico. Una OU de nivel 3 es hija de una OU de nivel 2.

Recopila del usuario:
- **OU padre**: Qué OU de nivel 2 es la padre (usa el ID del `identifierKey` de una OU recién creada, o pregúntaselo al usuario)
- **Nombre de la hija**: Nombre de la OU de nivel 3
- **Descripción** (opcional): Si no se proporciona, usa `null`

Construye el body:
- `module`: Siempre `"ALL"`
- `alias`: Concatena alias del abuelo + `/` + nombre del padre + `/` + nombre de la hija (ej: `"Banca/Particulares/Hipotecas"`). Forma más sencilla: toma el alias de la OU padre de nivel 2 y añade `/` + nombre de la hija.
- `parent`: `<BASE_URL>/gateway/portuno/organizationalUnits/<PARENT_L2_ID>` donde `<PARENT_L2_ID>` es el número del `identifierKey` del padre de nivel 2
- `description`: Descripción proporcionada por el usuario, o `null`
- `organizationalUnitType`: `"3"`

**Ejemplo de body** (hija de "Banca/Particulares" con ID 885):
```json
{
    "module": "ALL",
    "alias": "Banca/Particulares/Hipotecas",
    "parent": "<BASE_URL>/gateway/portuno/organizationalUnits/885",
    "description": "Hipotecas para clientes particulares",
    "organizationalUnitType": "3"
}
```

**Nota**: Las OUs de nivel 3 **no están disponibles en las versiones 25.1 ni 25.2**. Si `<ANJANA_VERSION>` es inferior a 26.1 y el usuario solicita una OU de nivel 3, infórmale de que la funcionalidad solo está soportada a partir de la 26.1.

### Nota sobre UTF-8 en las descripciones de las OUs

Las descripciones de las OUs contienen con frecuencia caracteres acentuados del español (á, é, í, ó, ú, ñ). Al enviarlos con `curl -d '<json>'` desde un shell, pueden corromperse y provocar que la API responda `400 "Failed to read request"`. Para evitarlo, escribe el body JSON en un fichero UTF-8 y envíalo con `--data-binary @file.json` y la cabecera `Content-Type: application/json; charset=utf-8`, que ya es obligatoria para todo body (ver "Construcción segura de comandos").

Para las reglas de campos detalladas, consulta `references/api-endpoints.md`.
