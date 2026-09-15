[简体中文](how-it-works.md) | [English](how-it-works.en.md)

# How PlanWeft works

PlanWeft keeps the current plan, findings, and actual validation of a complex coding task in project files. It is not another task executor: the model still works within user authorization, project rules, and host permissions.

## From a task to a later handoff

```mermaid
flowchart TB
    I[Installer deploys host-specific resources] --> H[Host discovers, trusts, and loads resources]
    U[User asks for work or explicitly invokes project-docs] --> H
    H --> S[Host selects the Skill]
    S --> M[Model works within authorized scope]
    M --> P[Selected task: task_plan.md<br/>findings.md<br/>progress.md]
    M --> D[Updates existing requirements, design, or validation docs when needed]
    P --> R[A later session or collaborator resumes]
    H -. Only when full integration and relevant Hooks are enabled .-> K[Context or state check]
    K -. Read-only .-> H
```

This is a source-level relationship diagram, not a trace of a live load or model run. Hosts differ in discovery, trust, lifecycle events, and permissions; see [platform support](platforms.en.md).

### Skill and Hook have different jobs

| Part | What it does | What it does not prove |
| --- | --- | --- |
| `project-docs` Skill | Guides the model to discover relevant entry points, maintain one task state, and decide whether existing documents need authorized updates | A Skill file does not prove that the current session read it or that the model followed it |
| Host Hook | Supplies context, checks plan state, or checks the handoff marker at events the host supports and enables | A Hook does not automatically edit durable documents or prove correctness or human approval |
| `document-handoff-check.sh` | Reads the handoff section in the selected task plan and classifies it as `pending`, `not_required`, or `complete` | It does not write project documents or validate that their contents are correct |

The default mode is advisory. Gated behavior reuses an existing completion gate only when the user explicitly enables it and the original PWF conditions and host capability pass; it still does not replace code tests or human review.

## Codex conversation loop (static source path)

This diagram follows the Codex distribution's `codex-hooks.json` and `.codex/hooks/`. It shows the order in which events can participate; it does not prove that this machine installed, trusted, enabled, or actually read the Skill. Every “maintain” action remains subject to user authorization and project rules.

```mermaid
sequenceDiagram
    participant U as User
    participant C as Codex host
    participant H as PlanWeft Hook
    participant M as Model and project-docs
    participant P as Selected plan records
    participant T as Tool

    C->>H: SessionStart
    alt PLANNING_DISABLED=1
        H-->>C: Quiet; no planning context
    else No valid root, unattached session, or binding required
        H-->>C: No context, or binding notice only
    else Valid attached plan
        H->>P: Read task_plan.md / progress.md
        H-->>C: additionalContext
    end
    U->>C: UserPromptSubmit
    C->>H: Prompt Hook
    alt Read-only task or Skill not selected
        H-->>C: Do not create or edit project records
    else Host selected the main Skill
        C->>M: Provide Skill and Hook context
        M->>P: Read/maintain task_plan, findings, progress within authorization
    end

    loop Tool calls
        M->>H: PreToolUse (matched tool)
        H-->>C: allow; legacy may attach a plan frame
        alt Host asks for permission
            C->>H: PermissionRequest
            H-->>C: Read-only systemMessage
            C->>U: Host permission UI
        end
        M->>T: Authorized tool call
        T-->>M: Result
        M->>H: PostToolUse (write-like tool)
        H-->>C: Once-per-turn progress reminder
        C->>M: Skill decides whether records/durable docs need updates
    end

    opt Host prepares context compaction
        C->>H: PreCompact
        H->>P: Read plan and optional attestation
        H-->>C: systemMessage: preserve progress/phase first
    end
    C->>H: Stop
    alt Explicit gated mode and every gate condition qualifies
        H-->>C: decision:block plus fixed reason
        C->>M: Continue; record progress then reconsider
    else Ordinary advisory, read-only, or gate does not qualify
        H-->>C: Status systemMessage or no output; stop allowed
    end
```

`PLANNING_DISABLED=1` must be set before session startup; it cannot undo an invocation that already happened. With no valid attached plan, a Hook does not guess task intent, and a Skill does not gain write authority merely from a Hook reminder. Ordinary advisory behavior supplies context or reminders only; explicit gated behavior asks to continue only when Stop conditions qualify and the host protocol supports it.

### Document-maintenance lifecycle

1. `task_plan.md` is the current task's dynamic state: goal, phases, next action, blockers, evidence links, and its single `Documentation Handoff`.
2. `findings.md` records sources, observations, assumptions, and candidate decisions; `progress.md` records actual actions, errors, and validation outcomes.
3. The main Skill maintains these three records within authorized scope, and updates existing specs, ADRs, reproductions, or usage documents only when the task has real impact.
4. A Documentation Map is human navigation only, not Hook input, cache, or a second state source. Language variants localize the main Skill; they are not parallel workflows.

## Two kinds of files—keep them separate

### Installer-owned files

This is a simplified global POSIX-default data root. `PLANWEFT_HOME`, XDG settings, and the platform can change the root; it is not a guarantee of the host's final execution location.

```text
~/.local/share/planweft/
├── installations.json       # Installation scope, managed items, registration records
├── versions/
│   └── <version>/           # Receipt, lockfile, and the exact npm package
└── registries/
    └── codex/
        ├── .agents/plugins/marketplace.json
        └── payload/         # Copied self-contained Codex distribution
```

The installer manages these files and host registration. A full Codex marketplace installation uses a copied payload; do not infer that all full host installs are symlinks from support for `--symlink`. Removal deletes managed registration and payload while retaining the version store for rollback.

### Project-owned records

```text
your-project/
├── <selected task directory>/
│   ├── task_plan.md         # Goal, phases, next action, blockers, handoff decision
│   ├── findings.md          # Research, sources, assumptions, open questions
│   └── progress.md          # Actual actions, errors, validation results
└── <existing project documentation>/
    ├── requirements or specs
    ├── design decisions
    └── reproduction or validation records
```

These are document roles, not a required directory scaffold created at installation. Existing selection rules choose the task directory; small edits and read-only requests do not need a new plan. Updating or removing the plugin does not roll back or delete project records and user documents.

## Check first activation deliberately

1. The installer records the intended host and scope.
2. The host discovers, trusts, and enables the resource as required.
3. The current session loads the expected version.
4. Relevant Hooks are enabled, when the host has a full integration.
5. The model actually reads the main Skill.
6. An authorized complex task creates the expected project records.
7. A later session can recover the correct state and next action from project records alone.

Those checks are independent. `doctor` is for installation diagnostics; it cannot substitute for steps 5 through 7. See the [runtime reference](reference/runtime-map.en.md) for a readable resource and invocation map.

## An illustrative task

```text
$project-docs
Fix the crash caused by empty rows in CSV import, add a regression test, and update the affected usage guide.
Keep the existing documentation layout and record actual validation results and unfinished work.
```

Observable evidence would include task selection, real excerpts from the three records, code or documentation diffs, commands actually run and their results, and a new-session handoff without the old chat. The input above is documentation only; it does not claim that PlanWeft has completed live host/model validation for this scenario.
