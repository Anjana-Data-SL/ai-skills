#!/usr/bin/env python3
"""Genera un workflow BPMN 2.0 (motor Activiti de Anjana) a partir de una especificación JSON.

Uso:
    python generate_bpmn.py spec.json [carpeta_salida] [--ids ids.json] [--draft]

Escribe <id>.bpmn20.xml en la carpeta de salida (por defecto, la actual) y valida el resultado.

Ids de notificación con marcador: en la especificación, un id de notificación puede escribirse como
"@CLAVE" (p. ej. "@N_VALIDAR_DOMINIO") cuando la notificación aún no existe en el entorno.
  --ids ids.json  sustituye cada marcador por su id real: {"N_VALIDAR_DOMINIO": 123, ...}
  --draft         permite generar con marcadores sin resolver (fichero NO desplegable; se avisa)
Sin --ids ni --draft, un marcador es un error.

Especificación (ver references/workflows-bpmn.md):
{
  "id": "WF_X",                              # id del proceso = identificador del workflow en el objectSubType
  "name": "WF_X",                            # opcional (por defecto = id)
  "approveNotificationCode": "<id>",         # OBLIGATORIO: notificación al final aprobado
  "rejectNotificationCode": "<id>",          # OBLIGATORIO si hay algún paso de validación (humano o automático)
  # "notificationCode" = id numérico de la notificación en Anjana (autogenerado al registrarla),
  # NO el campo notificationCode de la notificación. Cada cliente tiene las suyas: no hay valores por defecto.

  "flow": [ <nodo>, <nodo>, ... ]            # secuencia de nodos (forma general)
  # Formas abreviadas (compatibles): "steps": [pasos]  o  "gateway": {... "branches": [{"steps": [...]}]}
}

Nodos de "flow":
  {"id": "val_x", "name": "…", "validatorRole": "ROL", "notificationCode": "<id>"}   paso de validación (OK / KO)
  {"id": "auto_x", "name": "…", "automatic": true}                                   paso automático (OK / KO)
  {"id": "not_x", "name": "…", "notify": "<id>"}                                     tarea de notificación (sin validación)
  {"gateway": {"id": "gw_x", "name": "…", "attribute": "nombreAtributo",
               "allValues": ["…"],                                                   # opcional: comprueba cobertura
               "branches": [{"name": "…", "values": ["…"], "flow": [ … ]}, …]}}    # bifurcación (siempre al final)

Condición de una rama: "values" (valores del "attribute" de la bifurcación, unidos con ||) o "when" (comparaciones
unidas con &&; el "attribute" de la bifurcación no es necesario si todas las ramas usan "when"):
  {"name": "…", "when": [{"attribute": "tipo", "op": "==", "value": "X"},
                         {"attribute": "contieneDatosPersonales", "op": "!=", "value": true}], "flow": [ … ]}
  "op": "==" (por defecto) o "!=". "value": texto (va entre comillas) o booleano true/false (sin comillas).
  Con "when" el script no puede comprobar la cobertura: avisa y hay que revisarla a mano.
  Además de atributos, "attribute" admite variables de contexto del workflow: WORKFLOW_TYPE (CREATE, MODIFY, ACTIVATE,
  DEACTIVATE, TRANSFER, DEPRECATE, ADHERENCE, DISADHERENCE), OBJECT_TYPE (ENTITY, RELATIONSHIP), OBJECT_SUB_TYPE,
  ROLE_NAME, SENDER_USER (valores del entorno) y ORGANIZATIONAL_UNIT, solo con "op": "contains" y el alias de una OU hoja:
  {"attribute": "ORGANIZATIONAL_UNIT", "op": "contains", "value": "HQ/Legal"}.
  OBJECT_EXPIRATION_DATE (atributo nativo expirationDate) admite además '>', '<', '>=', '<=' con una fecha en formato
  aaaa-mm-ddThh:mm:ss.000Z: {"attribute": "OBJECT_EXPIRATION_DATE", "op": ">", "value": "2022-03-30T11:23:27.000Z"}.

Ids (workflow, pasos, bifurcaciones): solo letras, números, '_' y '-', empezando por letra; el id del workflow es
también el nombre del fichero. "attribute": name técnico (letras, números y '_'). Los valores de las ramas no pueden
contener comillas simples, barras invertidas ni caracteres de control (alterarían la condición).

Una bifurcación es siempre el último nodo de su secuencia: cada rama continúa hasta el final aprobado.
Una rama con "flow" vacío va directamente al final aprobado.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.sax.saxutils import escape

HEADER = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:activiti="http://activiti.org/bpmn" '
          'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
          'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
          'xmlns:tns="DC" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:yaoqiang="http://bpmn.sourceforge.net" '
          'id="_1613044313489" name="" targetNamespace="DC" exporter="Yaoqiang BPMN Editor" exporterVersion="5.3" '
          'xsi:schemaLocation="http://www.omg.org/spec/BPMN/20100524/MODEL http://bpmn.sourceforge.net/schemas/BPMN20.xsd">\n')

DELEGATE = "com.anjana.hermes.functionalities."
FIXED_IDS = {"Event_Start", "Event_End", "Event_reject_End", "FINAL_EXEC", "SEND_CREATOR",
             "FINAL_REJECT_EXEC", "CANCEL_EXEC", "SEND_USER"}
OK = "${ACCEPTED == 'true'}"
KO = "${ACCEPTED == 'false'}"
ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")    # ids del workflow, pasos y bifurcaciones (el del workflow es también el nombre del fichero)
ATTR_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")   # name técnico (camelCase) del atributo de una bifurcación
# Variables de contexto del workflow con valores fijos (los de OBJECT_SUB_TYPE, ROLE_NAME y SENDER_USER salen del entorno)
FIXED_VALUES = {
    "WORKFLOW_TYPE": {"CREATE", "MODIFY", "ACTIVATE", "DEACTIVATE", "TRANSFER", "DEPRECATE", "ADHERENCE", "DISADHERENCE"},
    "OBJECT_TYPE": {"ENTITY", "RELATIONSHIP"},
}
OU_VAR = "ORGANIZATIONAL_UNIT"   # solo con "contains": ${execution.getVariable("ORGANIZATIONAL_UNIT").contains("<OU>")}
DATE_VAR = "OBJECT_EXPIRATION_DATE"   # atributo nativo expirationDate; única variable con comparaciones de orden
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.000Z")   # formato obligatorio aaaa-mm-ddThh:mm:ss.000Z
ORDER_OPS = (">", "<", ">=", "<=")


def attr(v):
    """Escapa un valor de atributo XML (comillas dobles como &#34;, igual que los ejemplos de Anjana)."""
    return escape(str(v), {'"': "&#34;"})


def condition_for(attribute, values):
    return "${" + " || ".join(f"{attribute} == '{v}'" for v in values) + "}"


def when_condition(clauses):
    """Condición de una rama "when": comparaciones (== / !=) unidas con &&. Un booleano va sin comillas."""
    parts = []
    for c in clauses:
        v = c["value"]
        if c.get("op") == "contains":
            parts.append(f'execution.getVariable("{c["attribute"]}").contains("{v}")')
            continue
        lit = ("true" if v else "false") if isinstance(v, bool) else f"'{v}'"
        parts.append(f"{c['attribute']} {c.get('op', '==')} {lit}")
    return "${" + " && ".join(parts) + "}"


def normalize(spec):
    """Convierte las formas abreviadas ("steps" / "gateway") a "flow"."""
    forms = [k for k in ("flow", "steps", "gateway") if k in spec]
    if len(forms) != 1:
        raise ValueError("use exactamente una de 'flow', 'steps' o 'gateway'")
    if "steps" in spec:
        return spec["steps"]
    if "gateway" in spec:
        g = spec["gateway"]
        for b in g["branches"]:
            b.setdefault("flow", b.pop("steps", []))
        return [{"gateway": g}]
    return spec["flow"]


def check_safe(spec, flow):
    """Rechaza ids, atributos y valores que podrían alterar las condiciones o la ruta del fichero de salida."""
    def check_id(v, where):
        if not ID_RE.fullmatch(str(v if v is not None else "")):
            raise ValueError(f"{where}: id '{v}' no válido (solo letras, números, '_' y '-', empezando por letra)")

    def check_value(v, where):
        s = str(v)
        if "'" in s or "\\" in s or any(ord(c) < 32 or ord(c) == 127 for c in s):
            raise ValueError(f"{where}: el valor {s!r} contiene comillas simples, barras invertidas o caracteres de control, "
                             "que alterarían la condición del workflow; renombre el valor o edite esa condición a mano")

    check_id(spec.get("id"), "id del workflow")
    for n in walk(flow):
        if "gateway" in n:
            g = n["gateway"]
            check_id(g.get("id"), "bifurcación")
            if not isinstance(g.get("branches"), list) or not g["branches"]:
                raise ValueError(f"{g['id']}: la bifurcación necesita al menos una rama en 'branches'")
            for b in g["branches"]:
                if ("values" in b) == ("when" in b):
                    raise ValueError(f"{g['id']} (rama {b.get('name')}): use exactamente uno de 'values' o 'when'")
                if "values" in b and (not isinstance(b["values"], list) or not b["values"]):
                    raise ValueError(f"{g['id']} (rama {b.get('name')}): 'values' debe ser una lista de valores no vacía")
            if any("values" in b for b in g["branches"]) and not ATTR_RE.fullmatch(str(g.get("attribute") or "")):
                raise ValueError(f"{g.get('id')}: atributo '{g.get('attribute')}' no válido (debe ser el name técnico, p. ej. nivelSensibilidadDsa)")
            for v in g.get("allValues", []):
                check_value(v, f"{g['id']} (allValues)")
            for b in g["branches"]:
                where = f"{g['id']} (rama {b.get('name')})"
                for v in b.get("values", []):
                    check_value(v, where)
                if "when" in b:
                    if not isinstance(b["when"], list) or not b["when"]:
                        raise ValueError(f"{where}: 'when' debe ser una lista de comparaciones no vacía")
                    for c in b["when"]:
                        if not isinstance(c, dict) or not ATTR_RE.fullmatch(str(c.get("attribute") or "")):
                            raise ValueError(f"{where}: atributo '{c.get('attribute') if isinstance(c, dict) else c}' no válido (debe ser el name técnico)")
                        a, op = c["attribute"], c.get("op", "==")
                        if a == "ACCEPTED":
                            raise ValueError(f"{where}: ACCEPTED no se usa en bifurcaciones; el script ya genera las salidas OK/KO de cada paso")
                        if op not in ("==", "!=", "contains") + ORDER_OPS:
                            raise ValueError(f"{where}: operador '{op}' no admitido (solo '==', '!=', 'contains' o, con {DATE_VAR}, '>', '<', '>=', '<=')")
                        if (op == "contains") != (a == OU_VAR):
                            raise ValueError(f"{where}: 'contains' solo se usa con {OU_VAR}, y {OU_VAR} solo con 'contains'")
                        if op in ORDER_OPS and a != DATE_VAR:
                            raise ValueError(f"{where}: las comparaciones de orden ('{op}') solo están confirmadas con {DATE_VAR}")
                        if a == DATE_VAR:
                            v = c.get("value")
                            ok = isinstance(v, str) and DATE_RE.fullmatch(v)
                            if ok:
                                try:
                                    datetime.strptime(v, "%Y-%m-%dT%H:%M:%S.000Z")
                                except ValueError:
                                    ok = False
                            if not ok:
                                raise ValueError(f"{where}: la fecha de {DATE_VAR} debe ser una fecha válida con formato "
                                                 f"aaaa-mm-ddThh:mm:ss.000Z (p. ej. 2022-03-30T11:23:27.000Z), no '{v}'")
                        if "value" not in c or not isinstance(c["value"], (str, bool)):
                            raise ValueError(f"{where}: el valor de {a} debe ser un texto o un booleano (true/false)")
                        if isinstance(c["value"], str):
                            check_value(c["value"], where)
                        if op == "contains" and (not isinstance(c["value"], str) or '"' in c["value"] or not c["value"]):
                            raise ValueError(f"{where}: el valor de {OU_VAR} debe ser el alias de una OU, sin comillas dobles")
                        if a in FIXED_VALUES and c["value"] not in FIXED_VALUES[a]:
                            raise ValueError(f"{where}: '{c['value']}' no es un valor de {a} (valores: {', '.join(sorted(FIXED_VALUES[a]))})")
        else:
            check_id(n.get("id"), "paso")
            if "notify" not in n and not n.get("name"):
                raise ValueError(f"el paso {n.get('id')} no tiene 'name'")


def walk(flow):
    """Recorre todos los nodos (incluidos los de las ramas)."""
    for n in flow:
        yield n
        if "gateway" in n:
            for b in n["gateway"]["branches"]:
                yield from walk(b.get("flow", b.get("steps", [])))


class Builder:
    def __init__(self, spec):
        self.spec = spec
        self.flows = []     # (id, source, target, name, condition)
        self.incoming = {}
        self.outgoing = {}
        self.nodes = {}     # id -> dict(kind, name, col, row, data)
        self.n = 0
        self.row = 0
        self.maxcol = 1
        self.warnings = []

    def flow(self, source, target, name=None, condition=None):
        self.n += 1
        fid = f"Flow_{self.n}"
        self.flows.append((fid, source, target, name, condition))
        self.outgoing.setdefault(source, []).append(fid)
        self.incoming.setdefault(target, []).append(fid)
        return fid

    def node(self, nid, kind, name, col, row, data=None):
        if nid in self.nodes:
            raise ValueError(f"id duplicado: {nid}")
        if nid in FIXED_IDS and kind not in ("start", "end", "last", "cancel", "tailnotify"):
            raise ValueError(f"el id {nid} está reservado")
        self.nodes[nid] = dict(kind=kind, name=name, col=col, row=row, data=data or {})
        self.maxcol = max(self.maxcol, col)

    def check_id(self, value, where):
        v = str(value if value is not None else "").strip()
        if not v:
            raise ValueError(f"falta el id de notificación en {where}: cada cliente tiene las suyas, no hay valor por defecto")
        if v.startswith("@") and self.spec.get("_draft"):
            return
        if not v.isdigit():
            raise ValueError(f"{where}: '{v}' no es un id de notificación (debe ser el id numérico de Anjana)")

    def add_flow(self, flow, src, name, cond, col):
        """Encadena los nodos de una secuencia; termina en FINAL_EXEC (o en una bifurcación)."""
        for i, nd in enumerate(flow):
            if "gateway" in nd:
                if i != len(flow) - 1:
                    raise ValueError(f"la bifurcación {nd['gateway'].get('id')} debe ser el último nodo de su secuencia")
                g = nd["gateway"]
                self.node(g["id"], "gateway", g.get("name", ""), col, self.row)
                self.flow(src, g["id"], name, cond)
                seen = set()
                has_when = any("when" in b for b in g["branches"])
                if has_when and g.get("allValues"):
                    raise ValueError(f"{g['id']}: 'allValues' solo se puede usar si todas las ramas usan 'values'")
                if has_when:
                    self.warnings.append(f"{g['id']}: con ramas 'when' el script no puede comprobar que toda combinación de valores "
                                         "tenga rama; si ninguna condición se cumple, el objeto queda bloqueado, y si se cumplen "
                                         "varias, se toma la primera. Revise la cobertura (p. ej., una rama con == y otra con != "
                                         "sobre el mismo atributo)")
                for bi, b in enumerate(g["branches"]):
                    if "when" in b:
                        cond = when_condition(b["when"])
                    else:
                        dup = seen.intersection(b["values"])
                        if dup:
                            raise ValueError(f"{g['id']}: valores repetidos entre ramas: {dup}")
                        seen.update(b["values"])
                        cond = condition_for(g["attribute"], b["values"])
                    if bi > 0:
                        self.row += 1
                    self.add_flow(b.get("flow", []), g["id"], b.get("name"), cond, col + 1)
                if g.get("allValues"):
                    missing = [v for v in g["allValues"] if v not in seen]
                    extra = [v for v in seen if v not in g["allValues"]]
                    if missing:
                        raise ValueError(f"{g['id']}: valores de {g['attribute']} sin rama (el objeto quedaría bloqueado): {missing}")
                    if extra:
                        raise ValueError(f"{g['id']}: valores que no existen en {g['attribute']}: {extra}")
                return
            nid = nd["id"]
            if "notify" in nd:
                self.check_id(nd["notify"], f"la notificación {nid}")
                self.node(nid, "notify", nd.get("name", "Notification"), col, self.row, {"code": nd["notify"]})
                self.flow(src, nid, name, cond)
                src, name, cond = nid, None, None
            elif nd.get("automatic"):
                self.node(nid, "auto", nd["name"], col, self.row)
                self.flow(src, nid, name, cond)
                self.flow(nid, "FINAL_REJECT_EXEC", "KO", KO)   # también en los automáticos: preparado para cualquier decisión
                src, name, cond = nid, "OK", OK
            else:
                self.check_id(nd.get("notificationCode"), f"el paso {nid}")
                if not nd.get("validatorRole"):
                    raise ValueError(f"el paso {nid} no tiene validatorRole")
                self.node(nid, "user", nd["name"], col, self.row, nd)
                self.flow(src, nid, name, cond)
                self.flow(nid, "FINAL_REJECT_EXEC", "KO", KO)
                src, name, cond = nid, "OK", OK
            col += 1
        self.flow(src, "FINAL_EXEC", name, cond)

    def build(self):
        s = self.spec
        flow = normalize(s)
        if not flow:
            raise ValueError("el workflow necesita al menos un nodo")
        check_safe(s, flow)
        self.check_id(s.get("approveNotificationCode"), "approveNotificationCode")
        has_task = any("gateway" not in n and "notify" not in n for n in walk(flow))
        if has_task:   # todo paso de validación (humano o automático) tiene salida KO hacia el rechazo
            self.check_id(s.get("rejectNotificationCode"), "rejectNotificationCode")
        self.node("Event_Start", "start", "Start", 0, 0)
        self.add_flow(flow, "Event_Start", None, None, 1)
        c = self.maxcol + 1
        bottom = self.row + 1
        self.node("FINAL_EXEC", "last", "End", c, 0)
        self.node("SEND_CREATOR", "tailnotify", "Creator notification", c + 1, 0, {"code": s["approveNotificationCode"]})
        self.node("Event_End", "end", "", c + 2, 0)
        self.flow("FINAL_EXEC", "SEND_CREATOR")
        self.flow("SEND_CREATOR", "Event_End")
        if "FINAL_REJECT_EXEC" in self.incoming:
            self.node("FINAL_REJECT_EXEC", "last", "Reject", c, bottom)
            self.node("CANCEL_EXEC", "cancel", "Cancel", c + 1, bottom)
            self.node("SEND_USER", "tailnotify", "Notification for the Responsible", c + 2, bottom, {"code": s["rejectNotificationCode"]})
            self.node("Event_reject_End", "end", "", c + 3, bottom)
            self.flow("FINAL_REJECT_EXEC", "CANCEL_EXEC")
            self.flow("CANCEL_EXEC", "SEND_USER")
            self.flow("SEND_USER", "Event_reject_End")
        return self.render(s)

    def io(self, nid):
        return "".join(f"      <incoming>{f}</incoming>\n" for f in self.incoming.get(nid, [])) + \
               "".join(f"      <outgoing>{f}</outgoing>\n" for f in self.outgoing.get(nid, []))

    def render(self, s):
        pid = s["id"]
        out = [HEADER, f'  <process id="{attr(pid)}" name="{attr(s.get("name", pid))}" processType="None" isClosed="false" isExecutable="true">\n']
        mi = ('      <multiInstanceLoopCharacteristics activiti:collection="MODULE_ORGANIZATIONAL_UNIT">\n'
              '        <completionCondition xsi:type="tFormalExpression">${ACCEPTED != \'true\'}</completionCondition>\n'
              '      </multiInstanceLoopCharacteristics>\n')
        for nid, n in self.nodes.items():
            k, d = n["kind"], n["data"]
            if k == "start":
                out.append(f'    <startEvent id="{nid}" name="Start">\n{self.io(nid)}      <outputSet />\n    </startEvent>\n')
            elif k == "end":
                out.append(f'    <endEvent id="{nid}">\n{self.io(nid)}      <inputSet />\n    </endEvent>\n')
            elif k == "gateway":
                out.append(f'    <exclusiveGateway id="{attr(nid)}" name="{attr(n["name"])}">\n{self.io(nid)}    </exclusiveGateway>\n')
            elif k == "user":
                out.append(f'    <userTask id="{attr(nid)}" name="{attr(n["name"])}">\n      <extensionElements>\n'
                           f'        <activiti:field name="validatorRole">\n          <activiti:string>{escape(d["validatorRole"])}</activiti:string>\n        </activiti:field>\n'
                           f'        <activiti:field name="notificationCode">\n          <activiti:string>{escape(str(d["notificationCode"]))}</activiti:string>\n        </activiti:field>\n'
                           f'      </extensionElements>\n{self.io(nid)}{mi}    </userTask>\n')
            elif k == "auto":
                out.append(f'    <userTask id="{attr(nid)}" name="{attr(n["name"])}">\n      <extensionElements>\n'
                           '        <activiti:field name="automatic">\n          <activiti:string>true</activiti:string>\n        </activiti:field>\n'
                           '        <activiti:field name="validatorRole">\n          <activiti:string>automatic</activiti:string>\n        </activiti:field>\n'
                           f'      </extensionElements>\n{self.io(nid)}{mi}    </userTask>\n')
            elif k == "last":
                out.append(f'    <serviceTask id="{nid}" name="{n["name"]}" implementation="##WebService" activiti:class="{DELEGATE}LastExecutionJavaDelegate">\n{self.io(nid)}    </serviceTask>\n')
            elif k == "cancel":
                out.append(f'    <serviceTask id="{nid}" name="Cancel" implementation="##WebService" activiti:class="{DELEGATE}CancelTaskWorkflowDelegate">\n{self.io(nid)}    </serviceTask>\n')
            elif k in ("notify", "tailnotify"):
                out.append(f'    <serviceTask id="{attr(nid)}" name="{attr(n["name"])}" implementation="##WebService" activiti:class="{DELEGATE}SentNotificationJavaDelegate">\n'
                           f'      <extensionElements>\n        <activiti:field name="notificationCode" stringValue="{attr(d["code"])}" />\n      </extensionElements>\n{self.io(nid)}    </serviceTask>\n')
        for fid, src, tgt, name, cond in self.flows:
            nm = f' name="{attr(name)}"' if name else ""
            if cond:
                out.append(f'    <sequenceFlow id="{fid}"{nm} sourceRef="{attr(src)}" targetRef="{attr(tgt)}">\n'
                           f'      <conditionExpression xsi:type="tFormalExpression">{escape(cond)}</conditionExpression>\n    </sequenceFlow>\n')
            else:
                out.append(f'    <sequenceFlow id="{fid}"{nm} sourceRef="{attr(src)}" targetRef="{attr(tgt)}" />\n')
        out.append("  </process>\n")
        out.append(self.diagram(pid))
        out.append("</definitions>\n")
        return "".join(out)

    def diagram(self, pid):
        """Diagrama (bpmndi) con una rejilla simple, para que el workflow se pueda abrir en un editor BPMN."""
        size = {"start": (32, 32), "end": (32, 32), "gateway": (50, 50)}
        pos = {}
        for nid, n in self.nodes.items():
            w, h = size.get(n["kind"], (100, 80))
            cx, cy = 60 + n["col"] * 170, 70 + n["row"] * 120
            pos[nid] = (cx - w / 2, cy - h / 2, w, h)
        out = [f'  <bpmndi:BPMNDiagram id="Diagram_{attr(pid)}" name="{attr(pid)}" resolution="96">\n',
               f'    <bpmndi:BPMNPlane bpmnElement="{attr(pid)}">\n']
        for nid, (x, y, w, h) in pos.items():
            marker = ' isMarkerVisible="true"' if self.nodes[nid]["kind"] == "gateway" else ""
            out.append(f'      <bpmndi:BPMNShape id="{attr(nid)}_di" bpmnElement="{attr(nid)}"{marker}>\n'
                       f'        <dc:Bounds x="{x:g}" y="{y:g}" width="{w}" height="{h}" />\n      </bpmndi:BPMNShape>\n')
        for fid, src, tgt, _, _ in self.flows:
            sx, sy, sw, sh = pos[src]
            tx, ty, tw, th = pos[tgt]
            out.append(f'      <bpmndi:BPMNEdge id="{fid}_di" bpmnElement="{fid}">\n'
                       f'        <di:waypoint x="{sx + sw:g}" y="{sy + sh / 2:g}" />\n'
                       f'        <di:waypoint x="{tx:g}" y="{ty + th / 2:g}" />\n      </bpmndi:BPMNEdge>\n')
        out.append("    </bpmndi:BPMNPlane>\n  </bpmndi:BPMNDiagram>\n")
        return "".join(out)


def validate(xml_text):
    """Comprobaciones estructurales mínimas. Devuelve lista de errores."""
    ns = {"b": "http://www.omg.org/spec/BPMN/20100524/MODEL", "a": "http://activiti.org/bpmn"}
    root = ET.fromstring(xml_text.encode("utf-8"))
    proc = root.find("b:process", ns)
    errors = []
    idlist = [e.get("id") for e in proc if e.get("id")]
    if len(idlist) != len(set(idlist)):
        errors.append("ids duplicados")
    ids = set(idlist)
    outs, ins = {}, {}
    for f in proc.findall("b:sequenceFlow", ns):
        for ref in ("sourceRef", "targetRef"):
            if f.get(ref) not in ids:
                errors.append(f"{f.get('id')}: {ref}={f.get(ref)} no existe")
        c = f.find("b:conditionExpression", ns)
        outs.setdefault(f.get("sourceRef"), []).append(c.text if c is not None else None)
        ins.setdefault(f.get("targetRef"), []).append(f.get("id"))
    for t in proc.findall("b:userTask", ns):
        fields = {fl.get("name"): (fl.findtext("a:string", namespaces=ns) or fl.get("stringValue"))
                  for fl in t.findall("b:extensionElements/a:field", ns)}
        conds = outs.get(t.get("id"), [])
        if fields.get("automatic") != "true" and (not fields.get("validatorRole") or not fields.get("notificationCode")):
            errors.append(f"{t.get('id')}: falta validatorRole o notificationCode")
        if sorted(conds) != sorted([OK, KO]):   # humano o automático: siempre las dos salidas
            errors.append(f"{t.get('id')}: un paso de validación (también el automático) debe tener salidas OK y KO")
    for st in proc.findall("b:serviceTask", ns):
        if len(outs.get(st.get("id"), [])) != 1:
            errors.append(f"{st.get('id')}: una tarea de servicio debe tener una única salida")
    for g in proc.findall("b:exclusiveGateway", ns):
        if any(c is None for c in outs.get(g.get("id"), [])):
            errors.append(f"{g.get('id')}: todas las salidas del gateway necesitan condición")
    nodes = {e.get("id") for e in proc if e.get("id") and not e.tag.endswith("sequenceFlow")}
    for nid in nodes:
        if nid != "Event_Start" and nid not in ins:
            errors.append(f"{nid}: nodo inalcanzable")
    return errors


def resolve_placeholders(spec, ids):
    """Sustituye los ids de notificación "@CLAVE" por su valor en ids. Devuelve los no resueltos."""
    pending = set()

    def res(v):
        if isinstance(v, str) and v.startswith("@"):
            key = v[1:]
            if key in ids and str(ids[key]).strip():
                return str(ids[key])
            pending.add(key)
        return v

    for k in ("approveNotificationCode", "rejectNotificationCode"):
        if k in spec:
            spec[k] = res(spec[k])
    for n in walk(normalize(spec)):
        if "notificationCode" in n:
            n["notificationCode"] = res(n["notificationCode"])
        if "notify" in n:
            n["notify"] = res(n["notify"])
    return pending


def main():
    args = list(sys.argv[1:])
    if not args:
        print(__doc__)
        sys.exit(1)
    draft = "--draft" in args
    if draft:
        args.remove("--draft")
    try:
        ids = {}
        if "--ids" in args:
            i = args.index("--ids")
            if i + 1 >= len(args):
                raise ValueError("falta el fichero después de --ids")
            ids = json.load(open(args[i + 1], encoding="utf-8"))
            del args[i:i + 2]
        spec = json.load(open(args[0], encoding="utf-8"))
        outdir = args[1] if len(args) > 1 else "."
        pending = resolve_placeholders(spec, ids)
    except ValueError as e:
        print(f"ERRORES:\n- {e}")
        sys.exit(2)
    except (KeyError, TypeError, AttributeError, IndexError, OSError) as e:
        print(f"ERRORES:\n- especificación o fichero no válido ({type(e).__name__}: {e}); revise el formato en references/workflows-bpmn.md")
        sys.exit(2)
    if pending and not draft:
        print("ERRORES:\n- ids de notificación sin resolver: " + ", ".join(sorted(pending)) +
              " (pase --ids ids.json, o --draft para un borrador no desplegable)")
        sys.exit(2)
    spec["_draft"] = draft
    try:
        builder = Builder(spec)
        xml_text = builder.build()
    except ValueError as e:
        print(f"ERRORES:\n- {e}")
        sys.exit(2)
    except (KeyError, TypeError, AttributeError) as e:
        print(f"ERRORES:\n- especificación no válida ({type(e).__name__}: {e}); revise el formato en references/workflows-bpmn.md")
        sys.exit(2)
    errors = validate(xml_text)
    if errors:
        print("ERRORES:\n- " + "\n- ".join(errors))
        sys.exit(2)
    if pending:   # el borrador queda marcado dentro del propio fichero, no solo en pantalla
        xml_text = xml_text.replace("?>\n", "?>\n<!-- BORRADOR - NO DESPLEGAR: ids de notificación sin resolver: "
                                    + ", ".join(sorted(pending)) + " -->\n", 1)
    path = os.path.join(outdir, f"{spec['id']}.bpmn20.xml")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(xml_text)
    if pending:
        print(f"BORRADOR (NO DESPLEGAR): {path} — sustituir ids de notificación: {', '.join(sorted(pending))}")
    else:
        print(f"OK: {path}")
    for w in builder.warnings:
        print(f"AVISO: {w}")


if __name__ == "__main__":
    main()
