---
name: project-docs
description: "Use for implementation/maintenance with investigation, fixes, regression tests and handoff, including existing notes. Read-only/trivial tasks do not initialize files. Use the host-listed Skill path; read it before resource lookup. Do not use host settings or installation receipts to locate resources. Uses selected project planning context. Automatic recovery reads project planning files only. Explicit requests only: --metadata / --replay. It never runs commands declared in Markdown; no network upload path. Optional gated mode can request continuation only when the host supports it."
user-invocable: true
allowed-tools: "Read Write Edit Bash Glob Grep"
hooks:
  UserPromptSubmit:
    - hooks:
        - type: command
          command: "SH=\"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\"; [ -f \"$SH\" ] || SH=$(ls \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\" 2>/dev/null | head -1); [ -n \"$SH\" ] && [ -f \"$SH\" ] && sh \"$SH\" --event=userprompt; exit 0"
  PreToolUse:
    - matcher: "Write|Edit|Bash|Read|Glob|Grep"
      hooks:
        - type: command
          command: "SH=\"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\"; [ -f \"$SH\" ] || SH=$(ls \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\" 2>/dev/null | head -1); [ -n \"$SH\" ] && [ -f \"$SH\" ] && sh \"$SH\" --event=pretool; exit 0"
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "SH=\"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\"; [ -f \"$SH\" ] || SH=$(ls \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\" 2>/dev/null | head -1); [ -n \"$SH\" ] && [ -f \"$SH\" ] && sh \"$SH\" --event=posttool; exit 0"
  Stop:
    - hooks:
        - type: command
          command: "SH=\"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\"; [ -f \"$SH\" ] || SH=$(ls \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\" 2>/dev/null | head -1); [ -n \"$SH\" ] && [ -f \"$SH\" ] && sh \"$SH\" --event=stop; exit 0"
  PreCompact:
    - matcher: "*"
      hooks:
        - type: command
          command: "SH=\"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\"; [ -f \"$SH\" ] || SH=$(ls \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\" 2>/dev/null | head -1); [ -n \"$SH\" ] && [ -f \"$SH\" ] && sh \"$SH\" --event=precompact; exit 0"
metadata:
  version: "0.4.0-rc.13"
---

# Project Docs

Use this four-step workflow for maintenance or implementation combining investigation, changes, regression verification and a persistent handoff. Judge the whole task, not the size of its code diff. Use the user's language.

## 1. Establish scope and read the entrypoint

Read project instructions, approved requirements, existing task notes and relevant diff. Preserve user edits. Reading, diagnosis and host plan mode stay read-only: neither create nor modify project records. Trivial tasks need no new plan. An explicitly requested research document authorizes that document, not another planning hierarchy.

If new files, adoption or changing the old plan's authority are explicitly forbidden, cite the actual instruction and retain that authority. General advice to minimize changes or reuse notes does not establish this exception. Otherwise proceed to task preparation for authorized implementation.

Use the host-provided `SKILL.md` location for package resources. Run helpers with the authorized project as cwd. Do not inspect host settings, receipts or unrelated environment variables to locate resources; only inspect `PLAN_ID`, `PWF_*` and `PLANNING_DISABLED` when needed by the helpers.

## 2. Prepare the task before changing implementation

Read [plan selection](references/plan-selection.md) ([中文](references/plan-selection.zh.md)), then run `sh "<installed Skill>/scripts/resolve-plan-dir.sh"` or the documented PowerShell counterpart. Empty output with exit 0 alone does not mean no plan. Check the binding, including `PWF_PLAN_ROOT`, and the actual project files:

- Valid selected plan: read its three records and resume.
- Rejected binding or ambiguous selection: correct it before writing; do not create another plan.
- Neither a plan nor a pending binding exists, and implementation is authorized: run `bash "<installed Skill>/scripts/init-session.sh" "Task Name"`, or the documented initializer. Inspect and fill the files actually created before implementing; retain the returned `PLAN_ID` when provided.

Before implementation, put a concise scope summary with its actual user/project sources in the existing goal section, within the first 30 lines: authorized targets, prohibited reads/writes and verification limits. Include the task-specific instructions, not just generic project rules. Keep that summary there rather than duplicating it in a late appendix; reminders can select only the plan beginning or Goal. The plan records authority; it does not grant it. For a newly initialized plan, normalize that one heading to `## Goal`, retaining its language in the body; never add a second goal. Preserve protected existing headings: smart extraction may omit localized goals, so read the full plan instead of assuming reminders retain the scope.

Transfer this task's live state into the selected `task_plan.md`. Replace only the old entry's status/next-action fields with a relative link to it; preserve history and approved requirements. Keep one dynamic status source, with no bidirectional synchronization.

## 3. Implement and record observations

`task_plan.md` owns goal, phases, status, next action, blockers and evidence links. `findings.md` holds sources, dated observations, assumptions and candidate decisions. `progress.md` records actions, errors and verification. Re-read the plan before decisions and update after each phase; preserve `### Phase` and literal `**Status:** pending`, `in_progress`, `complete`.

Maintain affected long-term documents in their existing locations; create only useful missing records. Never change approved requirements to fit code. One owner updates shared state; workers use assigned records, and independent tasks use separate plans/worktrees. Manual scratch copies and counterfactual tests belong in task-owned directories inside the authorized project; never clear an unowned fixed path.

For checks actually executed, record the command or action, observed result and exit status when available. Inherited results cite their original record. Unexecuted checks are **Not Run**. Code inspection is not execution; later execution is not an earlier result.

## 4. Verify the records and hand off

Compare requirements, actual behavior and the final diff. For each error or later correction, fix the source statement still presented as current, or date the old statement and link its correction. Then actually re-read the affected claims and their evidence. Preserve historical observations; do not rewrite them as final behavior.

Use **Passed**, **Failed** and **Not Run** with limitations. A fresh reader reports historical Passed separately from checks they did not rerun, and accurately lists any checks they did perform. Verify that the old entry reaches the sole live plan and leave an explicit next action.

Use an independent evidence reviewer for significant design and a fresh reader for important handoff. The reader receives only project files, without old chat or expected answers. Follow [evidence guidance](references/evidence.md); resolve findings, or record unavailable independent review as Not Run.

Read [PWF details](references/pwf-workflow.md) and [controls](references/controls.md) only as needed. Default mode is advisory; automatic recovery uses project files only, session-history access requires an explicit request, and attestation is not approval. One planning plugin's hooks per session. Keep `PLAN_ID`, `PWF_*`, `PLANNING_DISABLED`; set `PLANNING_DISABLED=1` before read-only sessions when needed. Private caches stay separate. Platform capabilities follow `INSTALL.md`.

Missing-record templates: [plan](templates/task_plan.md), [findings](templates/findings.md), [progress](templates/progress.md).
