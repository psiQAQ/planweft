---
description: "Implements Manus-style file-based planning for complex tasks. Creates task_plan.md, findings.md, and progress.md. Use when starting complex multi-step tasks, research projects, or any task requiring >5 tool calls. Now with automatic session recovery after /clear"
disable-model-invocation: true
---

Follow project-docs scope rules: read-only requests and host plan mode do not initialize or update project files. Resolve the task-owned plan first; never create a competing root plan.

Invoke the program-design:project-docs skill and follow it exactly as presented to you
