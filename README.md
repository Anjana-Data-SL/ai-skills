# ai-skills

Skills de IA de Anjana Data para asistentes de código compatibles con el formato de skills de Claude (`SKILL.md` con frontmatter).

> **Copia de solo lectura.** La fuente que se mantiene vive en el repositorio interno de Anjana Data (`ai-tools-functional`). Los cambios se proponen allí y se reflejan aquí; los PRs directos a este repositorio no son el canal de contribución.

## Skills

| Skill | Descripción | Versiones de Anjana |
|---|---|---|
| [`skill-anjana-config`](skills/skill-anjana-config/) | Configura Anjana Data Platform por API REST: usuarios, unidades organizativas, roles, permisos, atributos, taxonomías, entidades, menús, lineage, idiomas, notificaciones, filtros y workflows BPMN. | 25.1, 25.2, 26.1 |

## Estructura

```
skills/
  <nombre-de-la-skill>/
    SKILL.md        punto de entrada: frontmatter y reglas de uso
    README.md       descripción corta de la skill
    references/     detalle por tema, se carga bajo demanda
    scripts/        utilidades auxiliares (opcional)
```

## Uso

Copia o enlaza la carpeta de la skill al directorio de skills de tu asistente (por ejemplo `~/.claude/skills/` en Claude Code). El asistente la carga cuando la petición encaja con su `description`, o con su trigger `[skill-anjana-config]`.

`skill-anjana-config` opera contra un entorno Anjana real: pide la versión, la URL del entorno y si es producción, y solo crea configuración nueva. Cualquier modificación o borrado exige confirmación explícita. Pruébala primero en un entorno que no sea de producción.

## Seguridad

Los secretos (tokens, contraseñas) no deben ir nunca en la línea de comandos ni en el repositorio; la skill los lee de ficheros temporales privados. Si encuentras un problema de seguridad, no abras un issue público: escribe al equipo de Anjana Data por los canales oficiales.

## Licencia

GNU General Public License v3.0. Consulta [LICENSE](LICENSE).
