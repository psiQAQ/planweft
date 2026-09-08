---
description: "Short alias for /plan. Starts Manus-style file-based planning: task_plan.md, findings.md, progress.md. Available since v3.0.0."
disable-model-invocation: true
---

Follow project-docs scope rules: read-only requests and host plan mode do not initialize or update project files. Resolve the task-owned plan first; never create a competing root plan.

Invoke the program-design:project-docs skill and follow it exactly as presented to you. Treat any arguments as the task to plan.

Create the three planning files in the current project directory if they don't exist:
- task_plan.md — for phases, progress, and decisions
- findings.md — for research and discoveries
- progress.md — for session logging

If the user asked for autonomous or gated mode in their words (for example "autonomous", "gated", "don't stop until done"), initialize with `init-session.sh --autonomous` or `init-session.sh --gated` accordingly; otherwise initialize the default way.

Then guide the user through the planning workflow.
