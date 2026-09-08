---
description: "Starte Manus-artige Dateiplanung. Erstelle task_plan.md, findings.md, progress.md für komplexe Aufgaben."
disable-model-invocation: true
---

Follow project-docs scope rules: read-only requests and host plan mode do not initialize or update project files. Resolve the task-owned plan first; never create a competing root plan.

Lies den deutschen Skill-Text aus dem ersten dieser Pfade, der existiert, und folge ihm genau:

- `$HOME/.claude/skills/project-docs-de/SKILL.md`
- `${CLAUDE_PLUGIN_ROOT}/skills/i18n/project-docs-de/SKILL.md`

Existiert keiner der beiden Pfade, rufe die program-design:project-docs Skill auf und arbeite auf Deutsch weiter.

Wenn die drei Planungsdateien nicht im aktuellen Projektverzeichnis existieren, erstelle sie:
- task_plan.md — für Phasen, Fortschritt und Entscheidungen
- findings.md — für Forschung und Erkenntnisse
- progress.md — für Sitzungsprotokolle

Dann führe den Benutzer durch den Planungs-Workflow. Alle Planungsdateien müssen auf Deutsch sein.

Die Statuskennzeichen bleiben wörtlich englisch (`**Status:** in_progress`, `**Status:** complete`), weil `check-complete.sh` sie mit `grep -F` sucht. Eine Übersetzung würde das Abschluss-Gate abschalten.
