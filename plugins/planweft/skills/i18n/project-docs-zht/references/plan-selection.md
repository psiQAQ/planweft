# Plan selection and initialization

[English](plan-selection.md) | [简体中文](plan-selection.zh.md)

Apply the scope check in the main Skill before any initialization. Reading a project, diagnosing a problem, host plan mode, a trivial task, a ban on new records, or an instruction to preserve the old plan's authority does not authorize initialization. This reference explains the existing PWF helpers; it adds no automatic write hook.

## Read the actual helper result

Use the absolute Skill location that the host supplies. Read only the relevant project files and the installed helper interfaces. Host settings, package-manager receipts, credentials and old sessions are not needed to locate these resources.

The Shell resolver deliberately exits 0 on a refused selector. Inspect output **and** the task's allowed binding variables and project files:

- A nonempty `PLAN_ID` is a binding. Empty resolver output with that binding is a refusal, not permission to initialize a different task.
- `PWF_PLAN_ROOT`, when nonempty, must be an absolute existing authorized project root. It names the project, not its `.planning` directory. Correct invalid or out-of-scope bindings; do not silently unset them to obtain a different plan.
- Without a binding, a valid `.planning/.active_plan` identifies the selected plan. If several named plans have no task selection, resolve ownership first instead of adopting the resolver's newest directory by accident.
- Empty output with no rejected binding can mean the legacy root layout. Read an existing root `task_plan.md` and its sibling records.
- If the authorized task has neither a selected named plan nor a root PWF plan, initialize it. A missing `PLAN_ID` is the normal initial state. A README link to old task notes supplies context; only an explicit requirement to keep those notes authoritative triggers the exception in the main Skill.

## Invoke the installed initializer in the right directory

The canonical English Shell helper requires Bash. With a task name it creates `.planning/<date-slug>/` under its **working directory**, writes `.planning/.active_plan`, and prints `PLAN_ID`. It does not move into `PWF_PLAN_ROOT` for you. Ensure the working directory is the bound, authorized target project before invocation. Keep the printed ID for subsequent task operations.

The upstream PowerShell, localized legacy and older host-specific initializers (for example the standalone Mastra copy) create `task_plan.md`, `findings.md` and `progress.md` in their working directory and do not return a named-plan ID. Use those actual files, or choose an explicitly assigned task worktree when independent tasks need separation. Do not invent unsupported `-PlanDir` arguments or claim that every `.sh`/`.ps1` implements named plans. If the package lacks a counterpart, use its documented available helper.

Existing records are preserved by the helper's skip-existing checks. If a selected task is missing one record, inspect that helper's interface or copy the missing template into the selected directory; do not run the named initializer again and create a competing task. After initialization, inspect the actual paths, fill the records with the current task and dated old observations, then replace only the old live-state entry with a relative link. Keep its history and approved requirements.

These contracts come from the fixed PWF v3.17.0 `resolve-plan-dir.sh` binding guards, canonical `init-session.sh` named-plan branch, and PowerShell/localized initializer implementations shipped alongside this reference.
