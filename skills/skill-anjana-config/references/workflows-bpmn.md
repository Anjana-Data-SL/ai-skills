# Anjana Data Platform — Workflows (BPMN 2.0)

Referencia para crear workflows de validación de Anjana. Se basa en dos workflows reales incluidos en `references/examples/`:

| Ejemplo | Qué muestra |
|---------|-------------|
| `GENERIC_TEMPLATE_2_VALIDATION_STEPS.bpmn20.xml` | Dos pasos de validación en secuencia (`role_name_1` → `role_name_2`, notificación 7 a cada validador). Aprobado → notificación 5; rechazado en cualquier paso → notificación 9 (ids de notificación de ese entorno). |
| `DSA_SENSIBILIDAD.bpmn20.xml` | Bifurcación inicial por el valor del atributo `nivelSensibilidadDsa`: "Público"/"Interno" → validación automática; "Confidencial"/"Restringido" → validación de `DATA_OWNER` (notificación 20). Aprobado → notificación 5; rechazado → notificación 5. |

---

## 1. Cómo encaja un workflow en Anjana

- Un workflow es un **proceso BPMN 2.0** que ejecuta el motor Activiti de Anjana (servicio *hermes*). Las tareas de servicio usan clases `com.anjana.hermes.functionalities.*`.
- El **`id` del `<process>`** es el identificador del workflow. Es el valor que se pone en los campos `createWorkflow`, `modifyWorkflow`, `activateWorkflow`, `deactivateWorkflow`, `transferWorkflow` y `deprecateWorkflow` del `objectSubType`. `AUTO` significa "sin workflow".
- El fichero se llama `<id>.bpmn20.xml`.
- **Despliegue**: este skill genera y valida el fichero, pero no conoce un endpoint de API para desplegarlo. El usuario lo carga en Anjana con el procedimiento de su entorno (administración de workflows o equipo de plataforma). **No inventar endpoints.** Si el usuario facilita el endpoint, usarlo e indicarle que no está documentado en este skill.
- Orden: primero se despliega el workflow; después se crea el `objectSubType` que lo referencia. Si el objectSubType ya existe, cambiar su workflow es una **modificación** y este skill no modifica configuración existente: hay que avisar al usuario.

## 2. Piezas del proceso

### 2.1 Inicio

```xml
<startEvent id="Event_Start" name="Start">
  <outgoing>FLOW_ID</outgoing>
  <outputSet />
</startEvent>
```

### 2.2 Paso de validación humana (`userTask`)

```xml
<userTask id="id_validation_step_1" name="Validation Step1">
  <extensionElements>
    <activiti:field name="validatorRole">
      <activiti:string>ROLE_NAME</activiti:string>        <!-- `name` del rol en Anjana, p. ej. DATA_OWNER -->
    </activiti:field>
    <activiti:field name="notificationCode">
      <activiti:string>NNN</activiti:string>              <!-- id de la notificación que recibe el validador -->
    </activiti:field>
  </extensionElements>
  <incoming>…</incoming>
  <outgoing>FLOW_OK</outgoing>
  <outgoing>FLOW_KO</outgoing>
  <multiInstanceLoopCharacteristics activiti:collection="MODULE_ORGANIZATIONAL_UNIT">
    <completionCondition xsi:type="tFormalExpression">${ACCEPTED != 'true'}</completionCondition>
  </multiInstanceLoopCharacteristics>
</userTask>
```

- Salidas obligatorias: **OK** con `${ACCEPTED == 'true'}` (al paso siguiente o a `FINAL_EXEC`) y **KO** con `${ACCEPTED == 'false'}` (a `FINAL_REJECT_EXEC`). `ACCEPTED` es la decisión del interviniente al terminar el paso (`'true'` o `'false'`, como texto); solo se evalúa en estas dos salidas, no en las bifurcaciones.
- El bloque `multiInstanceLoopCharacteristics` se copia **literalmente** en todos los pasos (también en los automáticos). No cambiar la colección ni la condición.
- `validatorRole` es el `name` técnico del rol (`GET /gateway/api/portuno/api/filter/roles`), no su descripción. Comprobar que existe antes de generar.

### 2.3 Paso de validación automática

```xml
<userTask id="Activity_auto" name="Validación automática">
  <extensionElements>
    <activiti:field name="automatic"><activiti:string>true</activiti:string></activiti:field>
    <activiti:field name="validatorRole"><activiti:string>automatic</activiti:string></activiti:field>
  </extensionElements>
  … (misma multiInstanceLoopCharacteristics)
</userTask>
```

- Sin `notificationCode`, pero **con las mismas dos salidas que un paso humano**: OK (`${ACCEPTED == 'true'}`) y KO (`${ACCEPTED == 'false'}` → `FINAL_REJECT_EXEC`). Tras cualquier `userTask`, aunque `validatorRole` sea `automatic`, hay que definir siempre las dos salidas para estar preparados para cualquier decisión. Por eso todo workflow con algún paso de validación necesita notificación de rechazo. (El ejemplo `DSA_SENSIBILIDAD` de `references/examples/` solo tiene la salida OK en su paso automático; el generador añade la KO.)
- Un workflow en el que todos los pasos son automáticos equivale a `AUTO`: proponer `AUTO` en su lugar.

### 2.4 Bifurcación por el valor de un atributo (`exclusiveGateway`)

```xml
<exclusiveGateway id="Gateway_01khb6y" name="¿SENSIBILIDAD?">
  <incoming>…</incoming>
  <outgoing>FLOW_RAMA_1</outgoing>
  <outgoing>FLOW_RAMA_2</outgoing>
</exclusiveGateway>
<sequenceFlow id="FLOW_RAMA_1" name="Publica o Interna" sourceRef="Gateway_01khb6y" targetRef="PASO_RAMA_1">
  <conditionExpression xsi:type="tFormalExpression">${nivelSensibilidadDsa == 'Público' || nivelSensibilidadDsa == 'Interno'}</conditionExpression>
</sequenceFlow>
```

**Expresiones admitidas** en las condiciones (las variables son los atributos del objeto):

| Forma | Ejemplo |
|---|---|
| Igualdad con un valor de un `SELECT`, varias opciones con `\|\|` | `${nivelSensibilidadDsa == 'Público' \|\| nivelSensibilidadDsa == 'Interno'}` |
| Booleano (`INPUT_CHECKBOX`), **sin comillas** | `${contieneDatosPersonales == true}` |
| Distinto (`!=`) | `${tipo != 'X'}`, `${contieneDatosPersonales != true}` |
| Combinación de atributos con `&&` | `${tipo == 'X' && nivel == 'Alto'}` |

Las comparaciones de orden (`>`, `<`, `>=`, `<=`) solo están confirmadas con la variable `OBJECT_EXPIRATION_DATE` (ver tabla siguiente). No hay patrón confirmado para comparar así atributos numéricos o de fecha de la plantilla, ni para `MULTI_SELECT`: no usarlos sin probarlos antes en el entorno (el generador no los admite).

**Comillas**: los textos van siempre entre comillas simples rectas `'…'` (y el alias de `ORGANIZATIONAL_UNIT`, entre comillas dobles rectas `"…"`). Las comillas tipográficas (`‘ ’ “ ”`), habituales al copiar y pegar desde un documento, no delimitan el texto y rompen la condición: sustituirlas siempre.

**Variables de contexto** que también se pueden evaluar en las salidas de una bifurcación (se combinan con atributos y entre sí con `&&`, y admiten `==` y `!=` salvo `ORGANIZATIONAL_UNIT`):

| Variable | Qué evalúa | Valores | Ejemplo |
|---|---|---|---|
| `WORKFLOW_TYPE` | Operación que lanzó el workflow | `CREATE`, `MODIFY`, `ACTIVATE`, `DEACTIVATE`, `TRANSFER`, `DEPRECATE`, `ADHERENCE`, `DISADHERENCE` | `${WORKFLOW_TYPE == 'CREATE'}` |
| `OBJECT_TYPE` | Tipo de objeto | `ENTITY`, `RELATIONSHIP` | `${OBJECT_TYPE == 'ENTITY'}` |
| `OBJECT_SUB_TYPE` | Subtipo del objeto | El `name` de un objectSubType del entorno (`GET /gateway/api/portuno/api/filter/objectSubTypes`) | `${OBJECT_SUB_TYPE == 'DATASET'}`, `${OBJECT_SUB_TYPE != 'DATASET'}` |
| `ROLE_NAME` | Rol del usuario que lanza la acción | El `name` de un rol del entorno (`GET /gateway/api/portuno/api/filter/roles`) | `${ROLE_NAME == 'DataSteward'}` |
| `SENDER_USER` | Usuario que desencadena el workflow | El `userName` de un usuario del entorno (`GET` de usuarios) | `${SENDER_USER == 'jperez'}` |
| `ORGANIZATIONAL_UNIT` | Unidades organizativas de los objetos que se validan | El `alias` de una OU **hoja** (`GET /gateway/api/portuno/api/ousNotParent`) | `${execution.getVariable("ORGANIZATIONAL_UNIT").contains("HQ/Legal")}` |
| `OBJECT_EXPIRATION_DATE` | Valor del atributo nativo `expirationDate` del objeto | Una fecha **siempre** con formato `aaaa-mm-ddThh:mm:ss.000Z`. Admite también `>`, `<`, `>=`, `<=` | `${OBJECT_EXPIRATION_DATE > '2022-03-30T11:23:27.000Z'}` |

- Un mismo workflow asignado a varias operaciones del objectSubType puede distinguirlas con `WORKFLOW_TYPE` (p. ej., validación humana al crear y automática al modificar). `ADHERENCE` y `DISADHERENCE` corresponden a la adhesión y la baja de un DSA.
- Resolver siempre los valores de `OBJECT_SUB_TYPE`, `ROLE_NAME`, `SENDER_USER` y `ORGANIZATIONAL_UNIT` con un `GET` al entorno y copiarlos exactos. El generador comprueba los valores de `WORKFLOW_TYPE` y `OBJECT_TYPE`, pero no puede comprobar los que dependen del entorno.
- **`SENDER_USER`, con prudencia**: hace depender el workflow de una persona concreta (si cambia de puesto o deja la organización, la rama deja de tener sentido) y deja su `userName`, un dato personal, escrito en el fichero del workflow. Proponer `ROLE_NAME` en su lugar, salvo que el usuario lo pida expresamente.
- **`OBJECT_EXPIRATION_DATE`**: la fecha va entre comillas simples y **siempre** en el formato `aaaa-mm-ddThh:mm:ss.000Z` (año de 4 cifras, mes, día, `T`, hora en 24 h, `.000Z`). Con ese formato fijo, el orden de los textos coincide con el de las fechas; con otro (`30/03/2022`, sin hora, sin `.000Z`) la comparación da resultados erróneos sin avisar. El generador rechaza cualquier otro formato. Para no dejar objetos bloqueados, emparejar cada comparación con su contraria (`>` con `<=`, `<` con `>=`) y preguntar al usuario qué debe pasar con los objetos **sin** fecha de expiración: su comportamiento en la comparación no está confirmado, así que conviene probarlo en el entorno.
- **`ORGANIZATIONAL_UNIT`**: solo se evalúa con `contains`, y un objeto puede pertenecer a varias OUs, así que varias ramas pueden cumplirse a la vez (gana la primera). No hay forma confirmada de negarlo: si no hay una rama por cada OU posible, el objeto de una OU sin rama se queda bloqueado. Antes de usarlo, revisar con el usuario el orden de las ramas y la cobertura de todas las OUs hoja.

Reglas de las condiciones:
- La variable es el **`name` técnico del atributo** de la plantilla (camelCase), p. ej. `nivelSensibilidadDsa`.
- El valor comparado de un selector es el **valor almacenado** del valor de referencia, entre comillas simples. En entornos multi-idioma es su **clave de traducción**, que puede no coincidir con la etiqueta que se ve en otro idioma. Resolverlo con `GET /gateway/api/portuno/api/filter/attributeDefinitionValues` (en muchos entornos la clave es el propio texto en castellano) y copiarlo exacto, con tildes y mayúsculas. Un booleano se compara con `true` / `false` sin comillas.
- **Casillas (`INPUT_CHECKBOX`)**: una casilla que nunca se ha tocado puede no tener valor. Para la rama "no marcada" usar `!= true` en lugar de `== false`, que no cubriría ese caso y dejaría el objeto bloqueado.
- Las ramas deben **cubrir todas las situaciones posibles**, sin solaparse. Si ninguna condición se cumple, el objeto se queda bloqueado en el workflow; si se cumplen varias, se toma la primera, y el orden pasa a decidir el resultado. Con un único `SELECT`: una rama por grupo de valores, sin repetir valores, y el atributo debería ser `REQUIRED` en la plantilla. Con `&&` o `!=`: revisar a mano todas las combinaciones (lo habitual es emparejar cada `==` con su `!=` sobre el mismo atributo).
- Cada rama termina en uno o varios pasos (2.2 o 2.3).

### 2.5 Final aprobado (ids fijos)

```xml
<serviceTask id="FINAL_EXEC" name="End" implementation="##WebService" activiti:class="com.anjana.hermes.functionalities.LastExecutionJavaDelegate">…</serviceTask>
<serviceTask id="SEND_CREATOR" name="Creator notification" implementation="##WebService" activiti:class="com.anjana.hermes.functionalities.SentNotificationJavaDelegate">
  <extensionElements><activiti:field name="notificationCode" stringValue="NNN" /></extensionElements>   <!-- id de la notificación de aprobación -->
</serviceTask>
<endEvent id="Event_End"><inputSet /></endEvent>
<!-- FINAL_EXEC → SEND_CREATOR → Event_End -->
```

### 2.6 Final rechazado (ids fijos)

```xml
<serviceTask id="FINAL_REJECT_EXEC" name="Reject" implementation="##WebService" activiti:class="com.anjana.hermes.functionalities.LastExecutionJavaDelegate">…</serviceTask>
<serviceTask id="CANCEL_EXEC" name="Cancel" implementation="##WebService" activiti:class="com.anjana.hermes.functionalities.CancelTaskWorkflowDelegate">…</serviceTask>
<serviceTask id="SEND_USER" name="Notification for the Responsible" implementation="##WebService" activiti:class="com.anjana.hermes.functionalities.SentNotificationJavaDelegate">
  <extensionElements><activiti:field name="notificationCode"><activiti:string>NNN</activiti:string></activiti:field></extensionElements>   <!-- id de la notificación de rechazo -->
</serviceTask>
<endEvent id="Event_reject_End"><inputSet /></endEvent>
<!-- FINAL_REJECT_EXEC → CANCEL_EXEC → SEND_USER → Event_reject_End -->
```

Todas las salidas KO de todos los pasos (humanos y automáticos) convergen en `FINAL_REJECT_EXEC`; todas las salidas OK finales, en `FINAL_EXEC`. Solo un workflow sin ningún paso de validación (únicamente avisos, o una rama vacía) carece de camino de rechazo.

### 2.7 Notificaciones

- El campo del BPMN se llama `notificationCode`, pero su valor es el **`id` de la notificación en Anjana**: el identificador numérico que se genera automáticamente al registrar la notificación en base de datos. **No** es el campo `notificationCode` de la notificación (que va a `null` en las notificaciones de usuario).
- Las notificaciones son **configurables**: cada cliente crea las suyas y decide cuál envía cada paso del workflow. No hay ids por defecto ni "estándar", y el id de una notificación equivalente cambia de un entorno a otro.
- Hay que obtener siempre el id de: la notificación de cada paso de validación humana (aviso al validador), la de aprobación (aviso al creador) y la de rechazo (aviso al responsable). Los pasos automáticos no llevan notificación.
- Cómo obtenerlo: `GET /gateway/api/portuno/api/filter/notifications`, localizar la notificación por su `subject` o `translationKey` y leer su `id`. Si la notificación no existe, crearla primero (sección *Notifications* del skill) y tomar el id de la respuesta.
- **Quién la recibe** depende de dónde se envía y de su `notificationReceiverType`:
  - `ROLE` dentro de un paso de validación (`userTask`) → el rol del `validatorRole` de ese paso (p. ej. la 7 del ejemplo genérico la recibe `role_name_1`).
  - `ROLE` fuera de un paso de validación (tareas finales `SEND_CREATOR` / `SEND_USER`) → el rol configurado en `receiverRole` de la notificación.
  - `USER` → el usuario que lanzó el workflow (p. ej. la 9 del ejemplo genérico, al rechazar).
  - Por tanto, un aviso "pendiente de validar" de tipo `ROLE` con texto genérico sirve para todos los pasos, sea cual sea el rol validador; y para avisar a un rol concreto al terminar (no al solicitante), la tarea final debe enviar una notificación `ROLE` con ese `receiverRole`.
- Los ids de los ejemplos (7, 20, 5, 9) son los de ese entorno concreto y solo ilustran dónde va cada uno. El mismo id puede usarse en varios puntos del workflow (el ejemplo DSA envía la misma notificación al aprobar y al rechazar).

### 2.8 Diagrama (`bpmndi`)

El bloque `bpmndi:BPMNDiagram` solo sirve para dibujar el proceso en un editor (los ejemplos se exportaron con Yaoqiang). El generador crea uno con una rejilla simple para que el fichero se pueda abrir y revisar visualmente.

---

## 3. Recogida de datos (conversación)

1. **Identificador** del workflow (`UPPER_SNAKE_CASE`, sin espacios; p. ej. `WF_VALIDACION_DOMINIO`) y nombre (por defecto, el mismo).
2. **Estructura**: pasos en secuencia, o bifurcación por condiciones sobre atributos: por los valores de un `SELECT` (nombre técnico del atributo y valores de cada rama), o por comparaciones `==` / `!=` combinadas con `&&`, incluidas casillas booleanas (nombre técnico de cada atributo, operador y valor), y por variables de contexto (`WORKFLOW_TYPE`, `OBJECT_TYPE`, `OBJECT_SUB_TYPE`, `ROLE_NAME`, `SENDER_USER`, `ORGANIZATIONAL_UNIT`, `OBJECT_EXPIRATION_DATE`; ver §2.4). Comprobar con el usuario que las ramas cubren todas las situaciones.
3. Para cada **paso**: nombre visible, id (`id_validation_step_N` o descriptivo, único), y rol validador + código de notificación, o "automático".
4. **Notificaciones** de aprobación (al creador) y de rechazo (al responsable), identificadas por su `id` en Anjana. No hay valores por defecto: se preguntan siempre.
5. **A qué `objectSubType` y operaciones** se aplicará (crear, modificar, activar, desactivar, transferir, deprecar).

Mostrar un resumen (diagrama en texto) y pedir confirmación antes de generar.

## 4. Generación con el script

```bash
python scripts/generate_bpmn.py spec.json <carpeta_salida>
```

`spec.json` (pasos en secuencia):
```json
{"id": "GENERIC_TEMPLATE_2_VALIDATION_STEPS", "approveNotificationCode": "5", "rejectNotificationCode": "9",
 "steps": [
   {"id": "id_validation_step_1", "name": "Validation Step1", "validatorRole": "role_name_1", "notificationCode": "7"},
   {"id": "id_validation_step_2", "name": "Validation Step2", "validatorRole": "role_name_2", "notificationCode": "7"}]}
```

`spec.json` (bifurcación):
```json
{"id": "DSA_SENSIBILIDAD", "approveNotificationCode": "5", "rejectNotificationCode": "5",
 "gateway": {"id": "Gateway_01khb6y", "name": "¿SENSIBILIDAD?", "attribute": "nivelSensibilidadDsa",
   "branches": [
     {"name": "Publica o Interna", "values": ["Público", "Interno"],
      "steps": [{"id": "Activity_1w4r5i4", "name": "Sensibilidad \"Publica\" o \"Interna\": Validación automática", "automatic": true}]},
     {"name": "Confidencial o Restringido", "values": ["Confidencial", "Restringido"],
      "steps": [{"id": "Activity_16zd687", "name": "Sensibilidad \"Confidencial\" o \"Restringida\": Validación  del Propietario", "validatorRole": "DATA_OWNER", "notificationCode": "20"}]}]}}
```

Ambas especificaciones reproducen los ejemplos de `references/examples/` con los mismos nodos, campos y condiciones (cambian los ids de los flujos y el diagrama, y el paso automático de `DSA_SENSIBILIDAD` recibe además la salida KO, ver §2.3).

`spec.json` (bifurcación con comparaciones, `"when"`): cada comparación es `{"attribute", "op", "value"}`, con `op` `"=="` (por defecto) o `"!="`, y `value` texto o booleano `true`/`false`. Las comparaciones de una rama se unen con `&&`; para un "o" entre combinaciones, usar varias ramas. El `attribute` de la bifurcación solo hace falta en las ramas con `"values"`, y ambas formas se pueden mezclar en una misma bifurcación.
```json
{"id": "WF_DATOS_PERSONALES", "approveNotificationCode": "5", "rejectNotificationCode": "9",
 "gateway": {"id": "gw_datos", "name": "¿Datos personales?", "branches": [
   {"name": "Personales y nivel alto",
    "when": [{"attribute": "contieneDatosPersonales", "value": true}, {"attribute": "nivel", "value": "Alto"}],
    "steps": [{"id": "val_dpo", "name": "Validación del DPO", "validatorRole": "DPO", "notificationCode": "8"}]},
   {"name": "Personales, otro nivel",
    "when": [{"attribute": "contieneDatosPersonales", "value": true}, {"attribute": "nivel", "op": "!=", "value": "Alto"}],
    "steps": [{"id": "val_owner", "name": "Validación del propietario", "validatorRole": "DATA_OWNER", "notificationCode": "7"}]},
   {"name": "Sin datos personales",
    "when": [{"attribute": "contieneDatosPersonales", "op": "!=", "value": true}],
    "steps": [{"id": "auto_1", "name": "Validación automática", "automatic": true}]}]}}
```
Genera `${contieneDatosPersonales == true && nivel == 'Alto'}`, `${contieneDatosPersonales == true && nivel != 'Alto'}` y `${contieneDatosPersonales != true}`: las tres ramas cubren todas las situaciones sin solaparse. Con ramas `"when"` el script **no puede comprobar la cobertura**: lo indica con un `AVISO` y hay que revisarla con el usuario (`allValues` no se admite en esas bifurcaciones).

**Notificaciones que aún no existen**: si el cliente todavía no ha creado sus notificaciones, escribir cada id como marcador `"@CLAVE"` (p. ej. `"@N_VALIDAR_DOMINIO"`) y generar con `--draft`: el fichero sale marcado como BORRADOR y **no se debe desplegar**. Cuando existan las notificaciones, anotar sus ids en un JSON `{"N_VALIDAR_DOMINIO": 123, …}` y regenerar con `--ids ids.json`. Sin `--ids` ni `--draft`, un marcador es un error.

### Forma general: `flow`

Para workflows con avisos intermedios y bifurcaciones anidadas, la especificación usa `"flow"`: una secuencia de nodos.

| Nodo | Forma | Genera |
|------|-------|--------|
| Validación humana | `{"id", "name", "validatorRole", "notificationCode"}` | `userTask` con salidas OK/KO (§2.2) |
| Validación automática | `{"id", "name", "automatic": true}` | `userTask` automático con salidas OK/KO (§2.3) |
| Aviso sin validación | `{"id", "name", "notify": "<id notificación>"}` | `serviceTask` con `SentNotificationJavaDelegate` en mitad del flujo. Úsese con notificaciones `ROLE` + `receiverRole` (el rol que debe enterarse) |
| Bifurcación | `{"gateway": {"id", "name", "attribute", "allValues": [...], "branches": [{"name", "values" \| "when", "flow": [...]}]}}` | `exclusiveGateway`; siempre es el último nodo de su secuencia y cada rama sigue hasta el final aprobado. Una rama con `flow` vacío va directa al final. Cada rama lleva `values` o `when` (ver arriba) |

- `allValues` (recomendado cuando todas las ramas usan `values`): lista completa de valores del atributo. El script falla si algún valor no tiene rama (el objeto se quedaría bloqueado) o si una rama usa un valor inexistente.
- **Patrón "máquina de estados"**: cuando un objeto recorre varias fases con relevos entre roles, el workflow de modificación bifurca por un atributo `SELECT` de fase. Como durante la validación no se puede editar, cada relevo es: el rol edita y cambia la fase → el workflow valida (aprobar/devolver) según la fase → avisa al siguiente rol. El workflow no conoce la fase anterior: guardar sin cambiar de fase repite la rama.
- Los avisos intermedios usan la misma clase que las tareas finales, pero **no aparecen en los ejemplos de Anjana**: probarlos en el entorno antes de depender de ellos.


## 5. Comprobaciones antes de entregar (el script las hace)

- Ids del workflow, de los pasos y de las bifurcaciones con solo letras, números, `_` y `-` (empezando por letra); el id del workflow es también el nombre del fichero. El atributo de una bifurcación es un `name` técnico (letras, números y `_`).
- Los valores de las ramas no contienen comillas simples, barras invertidas ni caracteres de control, que alterarían la condición (por ejemplo, convirtiéndola en siempre cierta y saltando un paso de validación). Si un valor real lleva apóstrofo, el script se niega a generar: renombrar el valor o editar esa condición a mano.
- XML bien formado; ids únicos; todo `sourceRef`/`targetRef` existe.
- Cada paso humano tiene `validatorRole`, `notificationCode` (id numérico de la notificación) y salidas OK y KO.
- Cada paso automático tiene también las salidas OK y KO.
- En las ramas `when`, los valores de `WORKFLOW_TYPE` y `OBJECT_TYPE` son de su lista; `ORGANIZATIONAL_UNIT` solo con `contains` (y `contains` solo con esa variable); `>`, `<`, `>=`, `<=` solo con `OBJECT_EXPIRATION_DATE`, cuya fecha debe ser válida y tener el formato `aaaa-mm-ddThh:mm:ss.000Z`; `ACCEPTED` no se usa en bifurcaciones.
- En las ramas `when`: atributos con `name` técnico, operador `==` o `!=`, y valor de texto o booleano.
- Todas las salidas del gateway tienen condición; ningún valor se repite entre ramas `values`.

Además, a mano:
- Los roles de `validatorRole` existen en el entorno.
- Los códigos de notificación existen en el entorno.
- Los valores de las condiciones coinciden exactamente con los valores almacenados del atributo y cubren todos sus valores.
- Con ramas `when` (el script avisa): ninguna situación se queda sin rama y no hay dos ramas que se cumplan a la vez.
