## Jerarquía de Taxonomía (attributeRelationShips para TREE_SELECT / TREE_MULTISELECT)

**Endpoint**: `POST /gateway/api/portuno/attributeRelationShips`

Para atributos de tipo `TREE_SELECT` o `TREE_MULTISELECT`, los valores de referencia se pueden organizar en una jerarquía de árbol (taxonomía). Cada nivel del árbol se define creando una relación entre un valor hijo y su valor padre.

**Importante**: Si el href de un valor de referencia no está disponible en la sesión actual, pide al usuario el ID numérico y recupera el href real vía:
```bash
curl -s "<BASE_URL>/gateway/api/portuno/attributeDefinitionValues/<ID>" \
  -H @"<AUTH_HEADER_FILE>" \
  -H "Content-Type: application/json"
```
Extrae el href de `_links.self.href` en la respuesta.

### Paso 1: Crear los valores de referencia

Primero, crea todos los valores de referencia para el atributo usando el endpoint `attributeDefinitionValues` (ver sección anterior). Guarda el `_links.self.href` de cada valor creado.

### Paso 2: Declarar los valores de nivel 1 (raíz)

Por cada valor raíz (parte superior del árbol), envía un POST con `sourceValue: null`:

```json
{
    "destinationValue": "<HREF_OF_ROOT_VALUE>",
    "sourceValue": null,
    "objectSubType": null
}
```

### Paso 3: Declarar los valores de nivel 2+ (hijos)

Por cada valor hijo, envía un POST con `sourceValue` apuntando a su padre:

```json
{
    "destinationValue": "<HREF_OF_CHILD_VALUE>",
    "sourceValue": "<HREF_OF_PARENT_VALUE>",
    "objectSubType": null
}
```

Repite para niveles más profundos: el `sourceValue` de un valor de nivel 3 es el href de su padre de nivel 2, y así sucesivamente.

**Nota**: `objectSubType` es siempre `null` para relaciones TREE_SELECT / TREE_MULTISELECT.

### Ejemplo: construir una taxonomía de 3 niveles

Dado un atributo TREE_SELECT "Dominio" con valores: "Finanzas" (N1), "Banca" (N2 bajo Finanzas), "Hipotecas" (N3 bajo Banca):

1. Crea los 3 valores de referencia → obtén los hrefs: `href_finanzas`, `href_banca`, `href_hipotecas`
2. Raíz: `{"destinationValue": "href_finanzas", "sourceValue": null, "objectSubType": null}`
3. N2: `{"destinationValue": "href_banca", "sourceValue": "href_finanzas", "objectSubType": null}`
4. N3: `{"destinationValue": "href_hipotecas", "sourceValue": "href_banca", "objectSubType": null}`

## Relaciones entre Atributos (attributeRelationShips entre atributos distintos)

**Endpoint**: `POST /gateway/api/portuno/attributeRelationShips`

Estas relaciones enlazan valores de referencia entre dos atributos **distintos** SELECT o MULTI_SELECT. Se usan para pre-filtrar qué valores están disponibles en un atributo destino en función del valor seleccionado en un atributo origen. Para que este filtrado funcione en la UI, también debe configurarse una validación DEPENDS_ON (ver la sección "Validaciones de Template Attribute" en `references/menus-secciones-atributos.md`).

### Conceptos

- **Atributo origen**: El atributo que dirige el filtrado (el que el usuario selecciona primero)
- **Atributo destino**: El atributo cuyos valores disponibles se filtran en función de la selección del origen
- **sourceValue**: href de un valor de referencia en el atributo origen
- **destinationValue**: href de un valor de referencia en el atributo destino

### Recopilar del usuario

- **Valor del atributo origen**: Qué valor del atributo origen dispara el filtrado. Si el href no está disponible en la sesión actual, pide al usuario el ID numérico del valor de referencia.
- **Valor del atributo destino**: Qué valor del atributo destino debe aparecer cuando se selecciona el valor origen. Misma regla para href/ID.
- **Alcance**: Pregunta al usuario si la relación aplica a todas las entidades/relaciones (`null`) o solo a una específica (proporcionando el nombre de la entidad/relación).

### Construir el body

```json
{
    "destinationValue": "<HREF_OF_DESTINATION_VALUE>",
    "sourceValue": "<HREF_OF_SOURCE_VALUE>",
    "objectSubType": null
}
```

- `destinationValue`: href del valor de referencia destino (del `_links.self.href` del objeto valor)
- `sourceValue`: href del valor de referencia origen (del `_links.self.href` del objeto valor)
- `objectSubType`: `null` si la relación aplica a todas las entidades/relaciones. Si aplica solo a una entidad/relación específica, usa su `name` (ej: `"SISTEMA_ORIGEN"`). Para consultar el nombre: GET `<BASE_URL>/gateway/api/portuno/api/filter/objectSubTypes`. Si tienes dudas, pregunta al usuario.

**Nota**: Si el usuario proporciona un ID numérico en lugar de un href completo, recupera el href real vía GET `<BASE_URL>/gateway/api/portuno/attributeDefinitionValues/<ID>` y extrae `_links.self.href`.

### Ejemplo

Dado el atributo "Infraestructura" (origen) con valor "AWS" (ID 55) y el atributo "Tecnología" (destino) con valor "S3" (ID 58):

```json
{
    "destinationValue": "<HREF_OF_VALUE_58>",
    "sourceValue": "<HREF_OF_VALUE_55>",
    "objectSubType": null
}
```

Esto significa: cuando el usuario selecciona "AWS" en Infraestructura, "S3" estará disponible en Tecnología.

Crea una relación por cada par valor origen-destino. Por ejemplo, si "AWS" debe mostrar tanto "S3" como "Redshift" en Tecnología, envía dos peticiones POST.
