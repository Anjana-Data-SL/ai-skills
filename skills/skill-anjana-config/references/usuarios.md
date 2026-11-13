## Entidad: Usuarios

**Endpoint**: `POST /gateway/api/portuno/users`

**Cabecera adicional obligatoria**:
```
-H "x-language: es-ES"
```

Recopila del usuario:
- **ID de usuario** (userName): El identificador de login del usuario
- **Nombre completo**: Nombre y apellido(s): divídelo en `firstName` y `lastName`
- **Email**: La dirección de correo del usuario
- **Contraseña**: La contraseña deseada por el usuario (se hasheará antes de enviarla)

> **Aviso de seguridad: díselo al usuario antes de pedirle la contraseña.** La contraseña indicada aquí queda en la transcripción de esta conversación (el comando que calcula su hash la lee de un fichero temporal, nunca de la línea de comandos). Recomienda dar una **contraseña temporal** y pedir al nuevo usuario que la **cambie tras el primer login**. No la repitas nunca en tus mensajes ni en tus resúmenes.

Construye el body:
- `userName`: El ID de usuario proporcionado por el usuario
- `firstName`: Extraído del nombre completo (primera palabra)
- `lastName`: Extraído del nombre completo (resto de palabras tras la primera)
- `email`: Email proporcionado por el usuario
- `phone`: Siempre `null`
- `title`: Siempre `null`
- `password`: La contraseña proporcionada por el usuario, **hasheada con BCrypt** antes de enviarla. La contraseña nunca va en la línea de comandos:
  1. Con la herramienta de escritura de ficheros, escribe `<SECRETS_DIR>/pw.txt` con únicamente la contraseña. Si termina en espacio o tabulador, pide otra (los espacios finales pueden perderse al escribir el fichero); si ocupa más de 72 bytes, bcrypt la rechaza: pide una más corta.
  2. Genera el hash leyendo el fichero por entrada estándar, y borra el fichero. **El prefijo `$2a$` es forzado**: la librería `bcrypt` de Python emite `$2b$` por defecto, y algunas instalaciones 26.1 devuelven un 500 en `POST /portuno/users` con un hash `$2b$` y aceptan el mismo hash con el prefijo `$2a$`. El algoritmo es idéntico entre `$2a$` y `$2b$`, por lo que la reescritura es segura:
     ```bash
     python -c 'import sys,bcrypt; p=sys.stdin.buffer.read().decode("utf-8").rstrip("\r\n").encode("utf-8"); print(bcrypt.hashpw(p, bcrypt.gensalt(rounds=10)).decode().replace("$2b$", "$2a$", 1))' < "<SECRETS_DIR>/pw.txt"
     rm -f "<SECRETS_DIR>/pw.txt"
     ```
     Si la librería `bcrypt` de Python no está disponible, `htpasswd` (utilidades de Apache) también lee la contraseña por entrada estándar con `-i`:
     ```bash
     htpasswd -niBC 10 "" < "<SECRETS_DIR>/pw.txt" | tr -d ':\n' | sed 's/$2y/$2a/'
     rm -f "<SECRETS_DIR>/pw.txt"
     ```
  3. Pon el hash resultante en `<SECRETS_DIR>/body.json` junto con el resto de campos (con la herramienta de escritura de ficheros), envíalo como se describe en "Construcción segura de comandos" con la cabecera adicional `-H "x-language: es-ES"`, y borra `body.json` después.
- `isServiceUser`: Siempre `false`

**Ejemplo de body**:
```json
{
    "userName": "jperez",
    "firstName": "Juan",
    "lastName": "Pérez García",
    "email": "jperez@example.com",
    "phone": null,
    "title": null,
    "password": "<BCRYPT_HASH: the 60-character value generated in step 2, with the 2a prefix and cost 10>",
    "isServiceUser": false
}
```

**Importante**: Guarda el `_links.self.href` de la respuesta: se necesita más adelante para configurar la autorización del usuario (ver la sección Autorización de usuario).

## Autorización de usuario (userOURoles)

**Endpoint**: `POST /gateway/api/portuno/userOURoles`

Esta operación asigna un rol y una unidad organizativa a un usuario. Normalmente se realiza después de crear un usuario (y opcionalmente después de crear un rol y/u OU).

El comportamiento difiere según si el rol que se asigna es un **rol cross** y según la **versión de Anjana**:

| Escenario | 25.1 | 25.2 / 26.1 |
|---|---|---|
| El rol NO es cross | Pregunta al usuario qué OU asignar | Pregunta al usuario qué OU asignar |
| El rol SÍ es cross | Crea una entrada `userOURoles` **por cada OU existente** | Crea una **única** entrada `userOURoles` usando la OU con alias `"Cross"` |

### Paso 1: Determinar qué OUs usar

**Si el rol NO es un rol cross (ambas versiones):**

Recupera la lista de OUs hoja disponibles (las que no tienen hijos):

```bash
curl -s "<BASE_URL>/gateway/api/portuno/api/ousNotParent" \
  -H @"<AUTH_HEADER_FILE>" \
  -H "Content-Type: application/json"
```

La respuesta contiene `_embedded.organizationalUnits`, un array de OUs. Cada OU tiene:
- `alias`: El nombre visible (ej: "España", "Banca/Hipotecas", "Pharma/compliances")
- `_links.self.href`: La URL a usar en el campo `ou`

Muestra la lista al usuario por su `alias` para que pueda elegir una.

---

**Si el rol SÍ es un rol cross y la versión es 25.1:**

Recupera todas las OUs existentes:

```bash
curl -s "<BASE_URL>/gateway/api/portuno/api/filter/organizationalUnits" \
  -H @"<AUTH_HEADER_FILE>" \
  -H "Content-Type: application/json"
```

Crea una entrada `userOURoles` por cada OU de la respuesta (ver Paso 3). Asignar un rol cross requiere la confirmación reforzada ("Creaciones sensibles"): indica al usuario a cuántas OUs se aplicará la asignación antes de crearlas.

---

**Si el rol SÍ es un rol cross y la versión es 25.2 o 26.1:**

Recupera la OU "Cross" directamente:

```bash
curl -s "<BASE_URL>/gateway/api/portuno/api/filter/organizationalUnits?aliasEquals=Cross" \
  -H @"<AUTH_HEADER_FILE>" \
  -H "Content-Type: application/json"
```

La respuesta del filtro no tiene `_links`: usa `<PORTUNO_HREF>/organizationalUnits/<id>` del único resultado. Crea solo una entrada `userOURoles` usando esta OU.

### Paso 2: Recopilar datos del usuario

- **Qué usuario** autorizar (usa el href de un usuario recién creado, o pídeselo)
- **Qué rol** asignar (usa el href de un rol recién creado, o pídeselo)
- **Qué OU** asignar: solo necesario si el rol no es cross (ver Paso 1)

**IMPORTANTE: Valida que la OU sea una hoja antes de continuar:**

Cuando el usuario indique una OU por nombre, DEBES llamar a `ousNotParent` y verificar que la OU aparece en la respuesta antes de crear la entrada `userOURoles`. Las OUs padre (las que tienen hijos) NO son destinos válidos de asignación.

```bash
curl -s "<BASE_URL>/gateway/api/portuno/api/ousNotParent" \
  -H @"<AUTH_HEADER_FILE>" \
  -H "Content-Type: application/json"
```

- Si la OU solicitada SÍ está en la lista → continúa con la asignación.
- Si la OU solicitada NO está en la lista → es una OU padre. Informa al usuario, muéstrale las OUs hoja disponibles bajo esa rama (filtrando por prefijo de alias), y pídele que elija una.

### Paso 3: Construir el body

Por cada OU a asignar, envía un POST con:

- `user`: `<BASE_URL>/gateway/portuno/users/<USER_ID>` donde `<USER_ID>` es el ID numérico extraído del final del `_links.self.href` del usuario
- `ou`: Usa directamente el `_links.self.href` de la OU elegida de `ousNotParent` (o `<PORTUNO_HREF>/organizationalUnits/<id>` para una OU obtenida de un endpoint de filtro)
- `role`: `<BASE_URL>/gateway/portuno/roles/<ROLE_ID>` donde `<ROLE_ID>` es el ID numérico extraído del final del `_links.self.href` del rol

**Importante**: Ten en cuenta que las URLs en el body usan `/gateway/portuno/` (sin `api/`), mientras que el propio endpoint usa `/gateway/api/portuno/`. Para `ou`, usa tal cual el href devuelto por `ousNotParent` (forma del backend `<PORTUNO_HREF>/organizationalUnits/<id>`), o constrúyelo de esa forma para una OU obtenida de un endpoint de filtro.

**Ejemplo de body**:
```json
{
    "user": "<BASE_URL>/gateway/portuno/users/20",
    "ou": "<OU_HREF_FROM_API_RESPONSE>",
    "role": "<BASE_URL>/gateway/portuno/roles/17"
}
```
