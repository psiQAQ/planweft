---
name: project-docs-es
description: "Use for implementation/maintenance with investigation, fixes, regression tests and handoff, including existing notes. Read-only/trivial tasks do not initialize files. Use the host-listed Skill path; read it before resource lookup. Do not use host settings or installation receipts to locate resources. Uses selected project planning context. Automatic recovery reads project planning files only. Explicit requests only: --metadata / --replay. It never runs commands declared in Markdown; no network upload path. Optional gated mode can request continuation only when the host supports it."
user-invocable: true
allowed-tools: "Read Write Edit Bash Glob Grep"
hooks:
  # Generated dispatch block: the 11 IDE and language variants share one
  # template (parity locked by tests/test_skill_hook_dispatch_parity.py).
  # Candidate order, first existing file wins: PWF_SCRIPT_DIR (explicit user
  # override for workspace or other nonstandard installs), CLAUDE_SKILL_DIR,
  # host env var, host user-level install dirs, then the two .claude paths.
  # Deliberate asymmetry: only UserPromptSubmit reports an unresolved script,
  # once per prompt. PreToolUse and PreCompact fire per tool call and Stop
  # carries no plan body, so a notice there would be spam; they stay silent.
  UserPromptSubmit:
    - hooks:
        - type: command
          command: "SH=\"\"; for c in \"${PWF_SCRIPT_DIR}/skill-hook.sh\" \"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs-es/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\"; do [ -f \"$c\" ] && { SH=\"$c\"; break; }; done; if [ -n \"$SH\" ]; then sh \"$SH\" --event=userprompt; else echo \"[planweft] hook script not found; plan injection is off. Set PWF_SCRIPT_DIR to the skill's scripts directory, or install the skill to a user-level path.\"; fi; exit 0"
  PreToolUse:
    - matcher: "Write|Edit|Bash|Read|Glob|Grep"
      hooks:
        - type: command
          command: "SH=\"\"; for c in \"${PWF_SCRIPT_DIR}/skill-hook.sh\" \"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs-es/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\"; do [ -f \"$c\" ] && { SH=\"$c\"; break; }; done; [ -n \"$SH\" ] && sh \"$SH\" --event=pretool; exit 0"
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "SH=\"\"; for c in \"${PWF_SCRIPT_DIR}/skill-hook.sh\" \"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs-es/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\"; do [ -f \"$c\" ] && { SH=\"$c\"; break; }; done; [ -n \"$SH\" ] && sh \"$SH\" --event=posttool; exit 0"
  Stop:
    - hooks:
        - type: command
          command: "SH=\"\"; for c in \"${PWF_SCRIPT_DIR}/skill-hook.sh\" \"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs-es/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\"; do [ -f \"$c\" ] && { SH=\"$c\"; break; }; done; [ -n \"$SH\" ] && sh \"$SH\" --event=stop; exit 0"
  PreCompact:
    - matcher: "*"
      hooks:
        - type: command
          command: "SH=\"\"; for c in \"${PWF_SCRIPT_DIR}/skill-hook.sh\" \"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs-es/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\"; do [ -f \"$c\" ] && { SH=\"$c\"; break; }; done; [ -n \"$SH\" ] && sh \"$SH\" --event=precompact; exit 0"
metadata:
  version: "0.4.0"
disable-model-invocation: true
---

# Documentos y planificación del proyecto

Sigue estos cuatro pasos para mantenimiento o implementación con investigación, cambios, regresiones y una entrega persistente. Evalúa la tarea completa, no el tamaño del diff. Usa el idioma del usuario.

## 1. Delimitar el alcance y leer la entrada

Antes de explorar el repositorio, indica en la respuesta existente un pequeño conjunto inicial de entradas del proyecto: las rutas nombradas en la tarea, y las instrucciones de la raíz y el README si existen y el alcance del usuario permite leerlos. Filtra este conjunto inicial según las restricciones explícitas de lectura antes de leerlo. Lee primero esas entradas y amplía la selección mediante enlaces de documentación relevantes o relaciones entre implementación y pruebas, dentro del alcance autorizado. Un listado superficial de la raíz ayuda a encontrar entradas; descubrir una configuración del agente o un directorio del instalador no lo convierte en una entrada de la tarea. Inclúyelo solo si la tarea autoriza explícitamente trabajar en él y cita esa autorización. Los recursos del paquete usan por separado la ruta del Skill proporcionada por el agente, indicada abajo.

Desde esas entradas del proyecto, lee los requisitos aprobados, las notas existentes y el diff relevante; conserva los cambios del usuario. Antes de preparar la tarea, indica en la respuesta o el objetivo existente qué rama aplica y su fuente real:

- Solo lectura, diagnóstico o modo de planificación: inspecciona e informa sin modificar registros. Un documento de investigación solicitado autoriza solo ese documento.
- Tarea trivial o restricción explícita sobre archivos nuevos, adopción o autoridad del plan anterior: indica el alcance trivial o cita la restricción y su fuente; conserva la entrada de estado existente.
- Implementación sustancial autorizada: si no aplica esa restricción, indica que no se encontró una prohibición de adopción y resuelve o inicializa el plan según el paso 2. Minimizar cambios y reutilizar notas son contexto de trabajo, no una prohibición de adopción.

Esta decisión registra la autoridad existente; no otorga permisos ni requiere otro archivo.

Localiza recursos mediante la ruta `SKILL.md` proporcionada por el agente; resuelve enlaces según [operaciones locales](references/local-operations.md) ([中文](references/local-operations.zh.md)); ejecuta scripts con el proyecto autorizado como cwd. No busques recursos en configuración del agente, recibos de instalación o variables ajenas. Consulta únicamente `PLAN_ID`, `PWF_*` y `PLANNING_DISABLED` cuando los scripts lo requieran.

## 2. Preparar la tarea antes de implementar

Lee [selección del plan](references/plan-selection.md) ([中文](references/plan-selection.zh.md)); ejecuta `sh "<Skill instalado>/scripts/resolve-plan-dir.sh"` o su alternativa PowerShell documentada. Una salida vacía con código 0 no demuestra ausencia de plan. Comprueba los archivos y enlaces de selección, incluido `PWF_PLAN_ROOT`:

- Plan seleccionado válido: lee sus tres registros y continúa.
- Selección rechazada o ambigua: corrígela antes de escribir; no crees otro plan.
- Sin plan ni selección pendiente y con implementación autorizada: ejecuta `bash "<Skill instalado>/scripts/init-session.sh" "Task Name"` o el inicializador documentado. Inspecciona y completa los archivos realmente creados antes de implementar; conserva `PLAN_ID` si se devuelve.

Antes de implementar, registra un resumen breve del alcance y sus fuentes reales del usuario/proyecto en la sección de objetivo existente, dentro de las primeras 30 líneas: destinos autorizados, lecturas/escrituras prohibidas y límites de verificación. Incluye las instrucciones concretas de la tarea, no solo reglas generales. Mantén ese resumen una sola vez allí; los recordatorios pueden seleccionar solo el inicio del plan o Goal. El plan registra la autoridad, no la concede. En planes recién inicializados, normaliza ese único título a `## Goal` y conserva el idioma en el cuerpo; no añadas otro objetivo. Conserva los títulos existentes protegidos: la extracción smart puede omitir objetivos localizados, así que lee el plan completo sin dar por hecho que el recordatorio conserva el alcance.

Transfiere el estado activo de esta tarea a `task_plan.md`. Sustituye solo estado/próxima acción de la entrada anterior por un enlace relativo al plan; conserva historia y requisitos aprobados. Una sola fuente de estado, sin sincronización bidireccional.

## 3. Implementar y registrar observaciones

`task_plan.md`: objetivo, fases, estado, próxima acción, bloqueos y evidencias. `findings.md`: fuentes, observaciones fechadas, hipótesis y decisiones candidatas. `progress.md`: acciones, errores y verificación. Relee el plan antes de decidir y actualízalo tras cada fase. Conserva `### Phase` y los literales `**Status:** pending`, `in_progress`, `complete`.

Mantén los documentos duraderos afectados en sus ubicaciones actuales; crea solo registros útiles que falten. No adaptes requisitos aprobados al código. Un owner actualiza el estado compartido; workers usan registros asignados y tareas independientes usan planes/worktrees separados. Para copias temporales manuales y pruebas contrafactuales, usa la creación y limpieza dentro del proyecto de [operaciones locales](references/local-operations.md) ([中文](references/local-operations.zh.md)); registra la ubicación real.

Registra cada comprobación ejecutada con comando o acción, resultado observado y código de salida disponible. Los resultados heredados citan el registro original; las comprobaciones no ejecutadas son **Not Run**. Inspeccionar código no es ejecutar; una ejecución posterior no ocurrió antes.

## 4. Revisar los registros y entregar

Compara requisitos, comportamiento y diff final. Para cada error o corrección posterior, corrige la afirmación fuente aún presentada como actual, o fecha la observación anterior y enlaza su corrección. Después relee realmente esas afirmaciones y evidencias. Conserva la historia, sin convertirla en comportamiento final.

Informa **Passed**, **Failed**, **Not Run** y límites. El lector nuevo distingue los Passed históricos de lo no repetido y de las comprobaciones que sí ejecutó. Verifica el enlace hacia el único plan activo y deja una próxima acción explícita.

Usa un reviewer independiente para diseños importantes y un lector nuevo para entregas importantes. Este recibe solo archivos del proyecto, sin chat previo ni respuestas esperadas. Sigue la [guía de evidencia](references/evidence.md), resuelve hallazgos o marca la revisión independiente no disponible como Not Run.

Consulta [detalles PWF](references/pwf-workflow.md) y [controles](references/controls.md) según necesidad. Modo predeterminado: recordatorios. Recuperación automática solo desde archivos del proyecto; historial de sesiones requiere solicitud explícita; attestation no es aprobación. Un plugin de planificación con hooks por sesión. Conserva `PLAN_ID`, `PWF_*`, `PLANNING_DISABLED`; usa `PLANNING_DISABLED=1` antes de sesiones de solo lectura cuando corresponda. Caché privada separada del estado; capacidades según `INSTALL.md`.

Plantillas para registros ausentes: [plan](templates/task_plan.md), [hallazgos](templates/findings.md), [progreso](templates/progress.md).
