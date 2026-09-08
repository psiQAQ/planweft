---
description: "Iniciar planificación de archivos estilo Manus. Crear task_plan.md, findings.md, progress.md para tareas complejas."
disable-model-invocation: true
---

Follow project-docs scope rules: read-only requests and host plan mode do not initialize or update project files. Resolve the task-owned plan first; never create a competing root plan.

Lee el texto de la habilidad en español desde la primera de estas rutas que exista y síguelo estrictamente:

- `$HOME/.claude/skills/project-docs-es/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/i18n/project-docs-es/SKILL.md`

Si ninguna de las dos rutas existe, invoca la habilidad planweft:project-docs y continúa trabajando en español.

Si los tres archivos de planificación no existen en el directorio del proyecto actual, créalos:
- task_plan.md — para fases, progreso y decisiones
- findings.md — para investigación y descubrimientos
- progress.md — para registro de sesión

Luego guía al usuario a través del flujo de trabajo de planificación. Todos los archivos de planificación deben estar en español.

Los marcadores de estado se mantienen literalmente en inglés (`**Status:** in_progress`, `**Status:** complete`) porque `check-complete.sh` los busca con `grep -F`. Traducirlos desactivaría la verificación de finalización.
