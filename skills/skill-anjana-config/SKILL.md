---
name: skill-anjana-config
description: "Esta skill debe usarse cuando el usuario pida crear o dar de alta configuración en Anjana Data Platform por API REST: usuarios y su autorización, unidades organizativas (OU), roles, permisos, atributos de metadatos, valores de referencia, taxonomías, relaciones entre atributos, entidades u objectSubType (nuevos tipos de activo), menús, secciones, atributos de plantilla y sus validaciones, capas y agrupaciones de lineage, idiomas y traducciones, notificaciones, filtros de búsqueda y workflows de validación (BPMN 2.0). Dispara con frases como crear/nuevo/añadir + {unidad organizativa, OU, rol, permiso, atributo, usuario, valor de referencia, taxonomía, árbol de valores, entidad, tipo de activo, menú, sección, validación, capa de lineage, idioma, notificación, filtro, workflow, BPMN}, además de dar de alta en Anjana, configurar Anjana Data Platform, jerarquía de metadatos, filtro de búsqueda, o cualquier mención a añadir configuración a Anjana Data Platform. Solo crea configuración; modificar o borrar exige confirmación explícita."
version: 2.0.0
team: functional
trigger: "[skill-anjana-config]"
autonomy: alto-impacto
effort_recomendado: high
author: Arquitectura
created: 2026-09-21
updated: 2026-11-13
---

# Anjana Data Platform - Skill de Configuración

Esta skill añade configuración a Anjana Data Platform vía API REST. Permite crear: Usuarios, Unidades Organizativas (OUs), Roles, Permisos, Definiciones de Atributos de Metadatos, Valores de Referencia para atributos de tipo selector, Jerarquías de Taxonomía, Relaciones entre Atributos, Object SubTypes (Entidades/Assets), Menús, Secciones, Template Attributes y sus Validaciones, Capas y Agrupaciones de Lineage, Idiomas y Traducciones, Notificaciones, Filtros de Búsqueda y Workflows de validación (ficheros BPMN 2.0 generados en local para su despliegue).

**REGLA CRÍTICA: Esta skill crea configuración nueva. Modificar, sobrescribir o eliminar configuración existente queda fuera de su alcance y debe rechazarse, salvo estas operaciones documentadas:**
- **Correctivas**: borrar valores de referencia duplicados (paso «Limpieza si ya se crearon duplicados» de `references/atributos-y-valores-referencia.md`), borrar validaciones aplicadas a un tipo de atributo incompatible (limpiezas de MIN/MAX, MIN_LENGTH/MAX_LENGTH, DEPENDS_ON) y poner `parental: true` en una relación (`references/lineage.md`).
- **Internacionalización**: activar o desactivar un idioma, cambiar el idioma por defecto y sobrescribir claves de traducción que ya tienen valor (incluidas las claves internas de la plataforma) — ver `references/internacionalizacion.md`.

**Cada una de ellas exige el protocolo de confirmación explícita de abajo; nunca se ejecuta como parte del flujo normal de creación.**

### Operaciones que modifican o borran — confirmación explícita (obligatorio)

**Lo que activa este protocolo es el efecto de la llamada, no su verbo HTTP.** Aplícalo antes de cualquier llamada que cambie, sobrescriba o elimine algo que ya existe:
- Cualquier `DELETE`.
- Cualquier `PATCH` o `PUT` que cambie configuración existente.
- **Llamadas `POST` con ese efecto**, en particular `POST /i18n/v1/submit` (26.1) cuando sobrescribe claves que ya tienen valor en el idioma destino, escribe claves internas de la plataforma, cambia el flag `active` de un idioma o pone `defaultLang: true` (también dentro de un `CREATE`). Antes de enviar un `submit`, comprueba con `POST /portuno/translations/v1/search` cuáles de las claves ya tienen valor en cada idioma destino: si ninguna lo tiene y no cambia ningún flag de idioma, es una creación simple y el protocolo no aplica.

No cubiertas por el protocolo (forman parte del flujo normal): la limpieza de caché `PUT /gateway/api/v1/cache/clear-all` y la publicación obligatoria de traducciones `PUT /gateway/public/v4/translations/upload` de 25.1/25.2 — antes de llamar a esta última, basta con avisar al usuario de que hace visibles las traducciones a todos los usuarios del entorno.

1. **Muestra exactamente qué va a cambiar**: la operación, el entorno (`<BASE_URL>` y si es producción — ver «Configuración de sesión») y la lista de objetos afectados con sus ids y nombres (o el recuento y una muestra si son muchos). En traducciones, indica cuántos valores existentes se sobrescribirán, en qué idiomas, y muestra algunos ejemplos con el valor actual y el nuevo.
2. **Explica los riesgos** en lenguaje llano:
   - El cambio se aplica de inmediato y lo ven todos los usuarios del entorno.
   - **No hay deshacer por API**: una fila borrada no se puede restaurar y recrearla produce un id nuevo.
   - Otra configuración puede referenciar los objetos afectados (taxonomías, relaciones `DEPENDS_ON`, plantillas, filtros, workflows) y dejar de funcionar o quedar inconsistente.
   - Si el entorno es de producción, el impacto llega a los usuarios y datos reales del cliente.
3. **Recomienda precauciones**: ejecutarlo antes en un entorno no productivo y guardar el estado actual antes de cambiarlo (la salida del `GET` correspondiente, escrita en un fichero local). Esa copia contiene la configuración de la organización: guárdala **fuera del directorio de trabajo y fuera de cualquier carpeta sincronizada** (por defecto en `<SECRETS_DIR>`, o en una ubicación no sincronizada que elija el usuario), dile su ruta y recuérdale que se borra con `<SECRETS_DIR>` al terminar la sesión salvo que la mueva.
4. **Pide confirmación explícita de esa operación concreta** (p. ej. «Confirmo el borrado de estos 12 valores en <BASE_URL>») y espérala. No valen una aprobación general anterior, la confirmación del resumen de una creación ni el silencio. Una confirmación cubre un lote (muestra su recuento y una muestra; no pidas confirmación llamada a llamada); un lote distinto necesita la suya.

Si el usuario no confirma, no ejecutes la operación e informa de lo que ha quedado sin cambios.

### Creaciones sensibles — confirmación reforzada (obligatorio)

Algunas creaciones no sobrescriben nada, pero otorgan mucho poder o afectan a muchos objetos a la vez. Para ellas, el resumen de creación del flujo normal no basta: en el mismo mensaje, indica el riesgo concreto en una frase y pide confirmación explícita antes de ejecutar.

| Creación | Riesgo a indicar |
|---|---|
| Permiso `ADMIN_ACCESS` (25.x: `ADMIN` / `ANJANA`) | Da acceso al panel de administración: los usuarios del rol pueden cambiar la configuración del entorno. |
| Permiso `API_ADMIN` | Da uso de la API de la plataforma: los usuarios del rol pueden operar sobre el entorno por API, fuera de la UI. |
| Permiso `DELETE_ALL` | Los usuarios del rol pueden borrar objetos de ese subtipo creados por cualquiera. |
| Permiso `CHANGE_OU` | Los usuarios del rol pueden mover objetos de ese subtipo a otra unidad organizativa, lo que puede cambiar quién es su responsable. |
| Asignar un rol **transversal** (cross) a un usuario | El rol aplica en todas las unidades organizativas (en 25.1 se crea una asignación por cada OU existente). |
| Rol con `isDefault: true` | Todo usuario nuevo lo recibe y no se puede corregir por API una vez que hay usuarios que lo tienen. |
| **Operaciones masivas** — más de 20 elementos del mismo tipo, sea cual sea el número de llamadas (permisos sobre muchos subtipos, valores de referencia cargados desde un documento, claves de traducción…) | Un error se repite en cada llamada. Confirma una vez por lote, mostrando el recuento y una muestra; en producción, propón ejecutar primero un lote pequeño (unos 5) y comprobarlo antes del resto. |

Mantén esta lista cerrada: cualquier otra creación sigue el flujo normal (resumen + ejecución). Pedir confirmación para todo hace que el usuario apruebe sin leer y la confirmación deja de proteger nada.

## Configuración de sesión

**Antes de hacer cualquier otra cosa**, pide al usuario estos tres datos:

1. **Versión de Anjana**: qué versión de Anjana Data Platform está usando. Opciones disponibles: `25.1`, `25.2` o `26.1`. Guárdala como `<ANJANA_VERSION>` — determina qué comportamiento específico de versión aplicar durante toda la sesión.
2. **URL base del entorno**: la URL base de su entorno Anjana (p. ej. `https://<entorno>.anjanadata.org`). Guárdala como `<BASE_URL>` — se usará en todas las llamadas a la API y en la construcción de hrefs.
3. **¿Es un entorno de producción?** (usuarios y datos reales). Guarda la respuesta como `<IS_PRODUCTION>`. **Si el usuario no lo sabe, trátalo como producción.** Cuando lo sea:
   - Di una vez, al principio, que cada cambio afectará a usuarios reales y recomienda probar antes la configuración en un entorno no productivo.
   - Menciónalo explícitamente en cada confirmación explícita o reforzada («…en el entorno de **producción** <BASE_URL>»).
   - En operaciones masivas, propón un primer lote pequeño antes del resto (ver «Creaciones sensibles»).

   Es lo que declara el usuario, no una comprobación técnica: nunca lo uses para saltarte una confirmación que de otro modo aplicaría.

No continúes hasta tener los tres valores.

## Entorno

- **URL base**: `<BASE_URL>` (proporcionada por el usuario al inicio de la sesión)
- **Prefijo del gateway**: `/gateway/api/portuno/`
- **Prefijo de href del backend**: `<PORTUNO_HREF>` — el prefijo de los hrefs que devuelve la API en `_links.self.href` (todo lo anterior al nombre del recurso, p. ej. antes de `/roles/16`); apunta al host del backend, no a `<BASE_URL>`. Obtenlo una vez por sesión de una respuesta que tenga `_links` — p. ej. `GET <BASE_URL>/gateway/api/portuno/api/ousNotParent`: toma cualquier `_links.self.href` y conserva la parte anterior a `/organizationalUnits/`. Nunca adivines su host ni su puerto.
- **Hrefs (verificado en 26.1)**:
  - Los endpoints `GET …/api/filter/…` devuelven paginación de Spring (`content`, `totalElements`, `totalPages`, `last`…) **sin `_links`**: construye el href de un elemento como `<PORTUNO_HREF>/<recurso>/<id>` (p. ej. `<PORTUNO_HREF>/attributeDefinitions/57`). Están paginados: itera `page` hasta que `last` sea `true`. Excepciones que devuelven `_embedded` con `_links`: `GET …/api/ousNotParent` y los endpoints de colección fuera de `api/filter` (p. ej. `GET …/templateAttributes`).
  - Las respuestas de creación (`POST`) incluyen `_links.self.href`, **salvo `POST /roles`**, que devuelve solo el `id` (`GET /roles/<id>` tampoco tiene `_links`): usa `<PORTUNO_HREF>/roles/<id>`; y **`POST /api/resource/layers`**, que devuelve cuerpo vacío aunque la capa se crea (ver `references/lineage.md`). Una respuesta de creación vacía o inesperada no es un fallo por sí misma: comprueba con un `GET` si el objeto existe antes de hacer nada más y nunca reintentes a ciegas.
  - Una referencia dentro de un cuerpo se acepta en la forma del backend (`<PORTUNO_HREF>/<recurso>/<id>`) y, donde esta skill lo documenta, en la forma del gateway (`<BASE_URL>/gateway/portuno/<recurso>/<id>`): ambas resuelven al mismo objeto por su id (verificado para el `role` de un permiso). Cuando la respuesta tenga `_links.self.href`, prefiérelo.
  - En 25.1 / 25.2 las formas de respuesta pueden diferir: si una respuesta tiene `_embedded` / `_links`, úsalos; si no, construye el href desde el id como arriba.
- **Rutas**: todo endpoint cuelga de `<BASE_URL>/gateway`. Las formas cortas usadas en tablas y notas son relativas a él: `/api/portuno/…`, `/api/filter/…` y `/portuno/…` (i18n, translations, languages, users, roles…) significan `<BASE_URL>/gateway/api/portuno/…` (`/api/filter/x` → `<BASE_URL>/gateway/api/portuno/api/filter/x`), y `/public/…` significa `<BASE_URL>/gateway/public/…`.
- **Autenticación**: Bearer Token (JWT) en la cabecera `Authorization: Bearer <token>`

## Autenticación

Al inicio de cada sesión, ofrece al usuario dos opciones de autenticación.

> **Aviso de seguridad — muéstraselo al usuario antes de que elija.** Cualquier credencial escrita en esta conversación queda en la transcripción. Los comandos de esta skill nunca la ponen en la línea de comandos (la leen de ficheros temporales privados — ver «Construcción segura de comandos»), pero la transcripción no se puede evitar. Base64 es una codificación, no un cifrado. Por tanto:
> - **Recomienda la Opción A** (un token JWT tomado de una sesión activa): caduca, lo que limita la exposición.
> - Si el usuario elige la **Opción B**, recomiéndale **cambiar esa contraseña después de la sesión** y sugiere usar, cuando sea posible, un usuario con solo los permisos que necesita la tarea en lugar de una cuenta de administrador personal.
> - Nunca repitas la contraseña ni el token en tus mensajes, resúmenes o ficheros.

### Opción A: proporcionar directamente un token JWT
Preferiblemente, **deja que sea el usuario quien escriba el token en el fichero** en vez de pegarlo en la conversación: crea `<AUTH_HEADER_FILE>` con la única línea `Authorization: Bearer ` (con la herramienta de escritura de ficheros), dale su ruta y pídele que pegue el token después del espacio y guarde. Si pega solo el token, o el prefijo dos veces, normaliza el fichero a una línea `Authorization: Bearer <token>` sin imprimirlo. Si el usuario pega el token en la conversación, escríbelo tú en `<AUTH_HEADER_FILE>`. Después comprueba su caducidad (abajo) y usa ese fichero en cada llamada.

**Comprobación de caducidad del token (obligatoria tras obtener un token y antes de operaciones largas o masivas).** La fecha de caducidad viaja dentro del JWT; este comando la lee **sin imprimir el token ni el nombre de usuario**:

```bash
python -c 'import sys,json,base64,datetime as d; s=open(sys.argv[1],encoding="utf-8").read().split(); t=s[-1] if s else ""; p=(t.split(".")+["",""])[1]
try: e=json.loads(base64.urlsafe_b64decode(p+"="*(-len(p)%4))).get("exp")
except Exception: e=None
print("token: formato no válido o sin caducidad" if not e else "token caduca: "+d.datetime.fromtimestamp(e).strftime("%Y-%m-%d %H:%M")+" | quedan "+str(round((e-d.datetime.now().timestamp())/3600,1))+" h")' "<AUTH_HEADER_FILE>"
```

Dile al usuario cuándo caduca el token. Si queda poco tiempo antes de una operación larga, sugiere renovarlo antes en lugar de fallar a mitad. Lo que limita la sesión es la propia caducidad del token (normalmente 24 h): no pidas un token nuevo mientras el actual sea válido.

### Opción B: login con usuario y contraseña
El usuario proporciona su usuario y contraseña en texto plano (ver el aviso de seguridad de arriba). La API espera ambos valores codificados en base64.

**Endpoint de login**: `POST <BASE_URL>/gateway/public/v4/auth/login/local`

**Pasos**:
1. Con la herramienta de escritura de ficheros, escribe `<SECRETS_DIR>/login.txt` con exactamente dos líneas: el usuario en la primera y la contraseña en la segunda. Si la contraseña termina en espacio o tabulador, pide al usuario otra: el espacio final puede perderse al escribir el fichero.
2. Ejecuta el comando de abajo. Lee el fichero por entrada estándar, codifica ambos valores en base64, los envía y escribe el token directamente en `<AUTH_HEADER_FILE>`: ni la contraseña ni el token aparecen en la línea de comandos ni en la salida. Después borra `login.txt` sea cual sea el resultado.

**Comando**:
```bash
python -c 'import sys,json,base64; u,p=sys.stdin.buffer.read().decode("utf-8").splitlines()[:2]; b=lambda s: base64.b64encode(s.encode("utf-8")).decode(); sys.stdout.write(json.dumps({"u": b(u), "p": b(p)}))' < "<SECRETS_DIR>/login.txt" \
  | curl -s -X POST "<BASE_URL>/gateway/public/v4/auth/login/local" -H "Content-Type: application/json" --data-binary @- \
  | python -c 'import sys,json; r=json.load(sys.stdin); t=(r.get("data") or {}).get("token"); ok=r.get("code")=="0000" and t; ok and open(sys.argv[1],"w",encoding="utf-8").write("Authorization: Bearer "+t); print(r.get("code"), r.get("description"), "- token guardado" if ok else "- sin token")' "<AUTH_HEADER_FILE>"
rm -f "<SECRETS_DIR>/login.txt"
```

**Parseo de la respuesta**:
- El comando imprime solo el `code` y la `description` de la respuesta, y si el token se guardó.
- `0000` significa login correcto: el token está en `<AUTH_HEADER_FILE>`, listo para las siguientes llamadas.
- Si el login falla, muestra el código y la descripción al usuario y NO reintentes automáticamente.
- Tras un login correcto, ejecuta la comprobación de caducidad de la Opción A.

## Flujo conversacional

1. **Configuración de sesión**: pide la versión de Anjana, la URL base del entorno y si es producción (ver la sección «Configuración de sesión»).
2. **Autenticación**: pregunta al usuario si quiere proporcionar un token JWT directamente o hacer login con usuario y contraseña (ver la sección «Autenticación»). Guarda el token solo en `<AUTH_HEADER_FILE>` (ver «Construcción segura de comandos»).
3. **Pregunta qué entidad** crear: Usuario, OU, Rol, Permiso, Atributo de Metadatos, Valor de Referencia, Taxonomía, Relación entre Atributos, Object SubType (Entidad/Relación), Menú, Sección, Template Attribute, Validación o Workflow (ver `references/workflows.md`: no usa la API REST y sigue su propio flujo).
4. **Recopila los datos necesarios** para la entidad elegida — carga el fichero de referencia correspondiente de la lista de abajo.
5. **Muestra un resumen** de la acción a realizar (tipo de entidad, valores de los campos) para que el usuario confirme que los datos son correctos.
6. **Ejecuta el comando curl inmediatamente** — NO pidas una segunda confirmación para ejecutar la llamada a la API. Una vez el usuario confirme los datos, ejecútala. Esto aplica **solo a creaciones simples**: cualquier llamada que cambie, sobrescriba o elimine configuración existente — sea cual sea su verbo HTTP — sigue el protocolo de confirmación explícita de «Operaciones que modifican o borran», y las creaciones listadas en «Creaciones sensibles» necesitan la confirmación reforzada.
7. **Parsea la respuesta** e informa al usuario del resultado. Si se creó un rol, conserva su href por si hay que asignarle permisos (`<PORTUNO_HREF>/roles/<id>` en 26.1, cuya respuesta no tiene `_links`). Tras cada cambio de configuración, ejecuta la limpieza de caché `PUT <BASE_URL>/gateway/api/v1/cache/clear-all` para que el cambio sea visible en la UI.
8. **Cobertura de traducciones (obligatorio, antes de terminar)**: toda clave traducible de la configuración creada en la sesión debe tener valor en **todos los idiomas registrados** (ver «Cómo se muestran las traducciones que faltan: nunca dejes una clave vacía» en `references/internacionalizacion.md`). Construye la lista de claves a partir de lo creado — etiquetas y descripciones de atributos, valores de selector, nombres y descripciones de menús y secciones, alias de OU, nombres de rol (`ROLE.<name>`), nombres de capa, etiquetas de filtro (`FILTERS.<NAME>`), asuntos y cuerpos de notificación; ver el catálogo de claves de traducción —, lee sus valores actuales con `search`, muestra al usuario qué claves/idiomas están vacíos y rellénalos (textos del usuario, traducidos en la conversación, o un servicio externo solo tras el aviso de servicios de terceros). Léelos de vuelta para confirmar y limpia la caché. Deja una clave vacía solo con confirmación explícita del usuario, tras decirle qué se mostrará en su lugar.
9. **Fin de sesión**: borra `<SECRETS_DIR>` con todo su contenido (`rm -rf "<SECRETS_DIR>"`) y dile al usuario que se ha borrado. **Una sesión es toda la conversación de trabajo con un entorno, no cada tarea individual**: conserva `<SECRETS_DIR>` y el token entre tareas para que el usuario no tenga que proporcionarlo de nuevo, y bórralo solo cuando (a) el usuario diga que ha terminado, (b) el token haya caducado (ya no funciona; un `401` lo confirma) o (c) el usuario cambie a otro entorno (un token pertenece a un entorno: nunca lo reutilices contra otro `<BASE_URL>`). No lo dejes nunca atrás indefinidamente: si la conversación termina sin un cierre explícito, recuerda al usuario que la carpeta sigue conteniendo el token y dónde está.

## Cabeceras comunes

Todas las llamadas a la API requieren:

```
-H @"<AUTH_HEADER_FILE>"
-H "Content-Type: application/json"
```

`-H @"<AUTH_HEADER_FILE>"` envía la cabecera `Authorization: Bearer …` guardada en ese fichero (ver abajo). Las llamadas que envían cuerpo usan `-H "Content-Type: application/json; charset=utf-8"`.

## Construcción segura de comandos (obligatorio)

**Nunca pongas datos ni secretos literalmente dentro de un comando de shell.** Un valor con una comilla simple (`O'Brien`), un `$` o un acento grave rompe el comando, lo cambia en silencio (entre comillas dobles, la contraseña `Pa$word1` se codificaría como `Pa`) o inyecta otro comando que se ejecuta con los permisos del usuario. Además, los argumentos de un programa en ejecución son visibles para otros usuarios de la máquina en la lista de procesos. Esto aplica a todo valor que venga del usuario, de un documento o de la API: nombres, descripciones, valores de referencia, contraseñas, tokens y textos a traducir.

1. **Directorio temporal privado.** Al empezar la sesión, crea uno con `mktemp -d`, **fuera del directorio de trabajo y fuera de cualquier carpeta sincronizada** (Google Drive, OneDrive, Dropbox…) para que los secretos no se suban a ningún sitio. Guarda su ruta como `<SECRETS_DIR>`. Las variables de shell no persisten entre comandos: escribe siempre la ruta literal. En Windows (Git Bash), `cygpath -w <ruta>` da la forma que espera la herramienta de escritura de ficheros; ambas formas funcionan en los comandos.
2. **Escribe los ficheros con la herramienta de escritura de ficheros**, nunca con `echo`, `printf` ni un heredoc: devolvería el contenido a un comando.
3. **Token**: `<AUTH_HEADER_FILE>` es `<SECRETS_DIR>/auth.hdr`, un fichero con una sola línea `Authorization: Bearer <token>`. Cada llamada lo envía con `-H @"<AUTH_HEADER_FILE>"` (curl 7.55 o posterior).
4. **Cuerpos JSON**: escribe el cuerpo en `<SECRETS_DIR>/body.json` (UTF-8) y envíalo con `--data-binary @"<SECRETS_DIR>/body.json"` y `-H "Content-Type: application/json; charset=utf-8"`. Sobrescribe el fichero en cada llamada. Esto además mantiene intactos los caracteres acentuados.
5. **Contraseñas**: los comandos las leen de un fichero por entrada estándar (ver «Opción B» y `references/usuarios.md`); borra el fichero justo después de usarlo.
6. **Parámetros de consulta con texto del usuario** (`?nameContains=…`, `?aliasEquals=…`): codifica el valor en URL; si contiene `'`, `"`, `` ` ``, `$` o `\`, construye la petición en un script que lea el valor de un fichero en lugar de escribirlo en el comando.
7. **Operaciones masivas y traducciones**: usa un script (p. ej. Python) que lea los valores o textos de un fichero y haga él mismo las llamadas HTTP, nunca un comando de shell por valor con el valor dentro. Las API keys de servicios externos (p. ej. Itzuli) siguen la misma regla que el token: léelas de un fichero en `<SECRETS_DIR>`.
8. **Limpieza**: borra `login.txt` y los ficheros de contraseñas inmediatamente después de usarlos. Conserva `auth.hdr` mientras dure la sesión (se reutiliza entre tareas) y borra todo `<SECRETS_DIR>` cuando termine la sesión — ver el paso 9 del flujo para saber cuándo.

## Plantilla del comando curl

Genera los comandos curl con este formato:

```bash
curl -s -X POST "<BASE_URL>/gateway/api/portuno/<endpoint>" \
  -H @"<AUTH_HEADER_FILE>" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @"<SECRETS_DIR>/body.json"
```

## Entidades — carga la referencia según lo que pida el usuario

- **`references/usuarios.md`** — Usuarios, autorización de usuario (userOURoles)
- **`references/unidades-organizativas.md`** — Unidades Organizativas (niveles 1 y 2)
- **`references/roles-y-permisos.md`** — Roles, Permisos
- **`references/atributos-y-valores-referencia.md`** — Definiciones de Atributos de Metadatos, Valores de Referencia
- **`references/taxonomias-y-relaciones.md`** — Jerarquía de Taxonomía, Relaciones entre Atributos
- **`references/subtipos-objeto-y-relaciones.md`** — Object SubTypes (Entidades/Assets), Relaciones
- **`references/menus-secciones-atributos.md`** — Menús, Secciones, Template Attributes, Validaciones de Template Attribute
- **`references/lineage.md`** — Capas de Lineage, Relaciones de Agregación
- **`references/internacionalizacion.md`** — Idiomas, traducciones
- **`references/notificaciones-y-filtros.md`** — Notificaciones, Filtros de Búsqueda (filterConfs)
- **`references/workflows.md`** — Workflows de validación (BPMN 2.0): flujo propio, sin API REST

## Encadenar operaciones

Al crear un rol y luego asignarle permisos en la misma sesión:
1. Crea primero el rol
2. Toma su href: `<PORTUNO_HREF>/roles/<id>` en 26.1 (la respuesta no tiene `_links`); en otro caso, `_links.self.href`
3. Usa ese href como campo `role` en la petición de permiso

## Gestión de errores

- Si la API devuelve un error, muestra el cuerpo de la respuesta al usuario (code, description, message) — nunca las cabeceras de la petición, el token ni el contenido de `<SECRETS_DIR>`
- NO reintentes automáticamente — deja que el usuario decida
- Errores comunes: 401 (token caducado), 409 (duplicado), 400 (error de validación)
- Ante un `401`: el token ha caducado o no es válido. Detente, díselo al usuario, vacía `<AUTH_HEADER_FILE>` dejándolo en `Authorization: Bearer ` y pídele que pegue un token nuevo ahí (Opción A); después ejecuta de nuevo la comprobación de caducidad. No reenvíes la operación fallida hasta que el usuario lo confirme: antes comprueba con un `GET` si llegó a aplicarse

## Recursos adicionales

### Ficheros de referencia

Para especificaciones detalladas de endpoints y catálogos de campos:
- **`references/anjana-data-platform-context.md`** — Visión conceptual, en español, de lo que se puede gobernar y configurar (tipos de objeto, menús y secciones, tipos de atributo y validaciones, lineage, filtros, idiomas y traducciones). Léelo para entender la plataforma o explicársela al usuario; para endpoints, campos y reglas prevalecen este `SKILL.md` y el resto de referencias
- **`references/api-endpoints.md`** — Documentación de endpoints de los recursos principales (OUs, roles, permisos, definiciones de atributo, valores de referencia, taxonomías, objectSubTypes), reglas de campos, ejemplos de cuerpo y el catálogo de tipos de atributo
- **`references/permissions-catalog.md`** — Catálogo completo de los 25 tipos de permiso de la versión 26.1 (y sus equivalentes 25.x) con las correspondencias action/subType y sus restricciones
- **`references/workflows-bpmn.md`** — Bloques de construcción de workflows (BPMN 2.0), reglas, formato de especificación del generador y checklist de validación
- **`references/examples/`** — Dos workflows reales de Anjana: `GENERIC_TEMPLATE_2_VALIDATION_STEPS.bpmn20.xml` (dos pasos de validación secuenciales) y `DSA_SENSIBILIDAD.bpmn20.xml` (bifurcación por valor de atributo + paso automático; su paso automático solo tiene la salida OK, el generador añade la KO)

### Scripts
- **`scripts/generate_bpmn.py`** — Genera y valida un `.bpmn20.xml` de workflow a partir de una especificación JSON
