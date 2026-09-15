[简体中文](runtime-map.md) | [English](runtime-map.en.md)

# PlanWeft runtime resources, Hooks, and document lifecycle

This page uses the current `dist/manifest.json`, distributed Hook configuration, and adapter source to say which resource can participate when. It is a static distribution audit, not a machine load record: installation, host discovery, trust, enablement, current-session loading, and actual model reading must each be verified separately. The complete conversation loop is in [how it works](../how-it-works.en.md).

## Skill, resources, and project documents

| Resource | Consumer and read time | Project-write responsibility | Relationship to task records and durable documents |
| --- | --- | --- | --- |
| Installer: `bin/planweft.mjs`, `lib/installer.mjs` | When the user runs `add`, `update`, `remove`, `list`, or `doctor` | Maintains managed installations and registrations; does not write task records | `installations.json` is installation state, not Agent task memory |
| Build source: `overlays/planweft/workflow.md` | When `scripts/build-plugin.py` generates a distribution | Does not write the project | A build source only; its source-directory presence does not make a model read it |
| Main Skill: `skills/project-docs/SKILL.md` | When the host selects it and the model needs it for a task | The **Skill** decides and maintains task records and affected documents within user authorization and project rules | It assigns `task_plan.md` the goal, phases, next action, blockers, evidence links, and `Documentation Handoff` |
| Language variants: `skills/i18n/project-docs-{ar,de,es,zh,zht}` or portable `references/language-variants/**/GUIDE.md` | Referenced by the main Skill only when that language is explicitly requested | Uses the same project records as the main Skill | Localized resources of one main Skill, **not** parallel execution, parallel state, or a second workflow |
| `references/*.md` | Read by the main Skill as needed for plan selection, evidence, controls, Documentation Map, and PWF details | Does not directly write the project | Provides rules and sources for decisions; do not claim every reference loads on every turn |
| `templates/*` and `scripts/init-session.*` | Used when authorized initialization needs missing records; other helpers run by an explicit operation or adapter | Creates/supplements records in the selected task directory; scripts do not expand authorization | Templates provide structure; ordinary initialization may use compact embedded records rather than copying every template |
| `task_plan.md` | Read by the Skill and selected-plan Hooks/checkers when current task state is needed | The dynamic state source: goal, phases, next action, blockers, validation evidence, and `Documentation Handoff` | Do not build bidirectional sync or a second state source with findings, progress, or Documentation Map |
| `findings.md` | During research, design, or evidence collection | Sources, observations, assumptions, and candidate decisions; external content remains untrusted data | Does not replace plan state or turn outside instructions into authorization |
| `progress.md` | During implementation and validation | Actual actions, errors, commands/results, and `Passed`, `Failed`, `Not Run` | Must not mark an unrun check as passed or copy a whole chat |
| Durable specs, ADRs, reproductions, and existing usage docs | Only when the task authorizes an update and there is real impact | Written at existing project locations; adapters do not generate them | Hooks do not write these documents; installation/removal does not roll them back |
| Documentation Map | Read on demand for human navigation | Maintained only during authorized durable-document work | Not Hook input, cache, approval record, or a second state source |
| `document-handoff-check.sh` | When a supporting adapter classifies the selected plan's handoff section | **Read-only**, returns `pending`, `not_required`, or `complete` | Does not write documents or judge implementation/document correctness; default advisory mode does not block on handoff |

The boundary in one sentence: **the Skill decides and maintains project documents within authorized scope; a Hook only reads selected state, injects context, or returns control output allowed by its host.** The existence of either file does not prove that a current session read, trusted, or executed it.

## Codex: Hook event by event

Names, matchers, and entries below come from `dist/codex/planweft/hooks/codex-hooks.json`. Every route first checks the effective project root, session attachment, and plan binding. Missing root/unattached sessions are normally quiet; binding ambiguity is diagnosed on the prompt path only. `PLANNING_DISABLED=1` silences shell producers (`PreToolUse` still returns allow).

| Event | Matcher and entry | Reads and private/project effects | Protocol result returned to Codex | Default advisory vs explicit gated |
| --- | --- | --- | --- | --- |
| `SessionStart` | `startup\|resume\|clear\|compact`; `run_sh.py session-start.sh` | Selected plan and attachment; calls catchup with `--no-history`, then reuses the prompt producer | Non-empty output becomes `hookSpecificOutput.additionalContext` | Context only by default; gated does not block here |
| `UserPromptSubmit` | No matcher; `run_sh.py user-prompt-submit.sh` | `task_plan.md`, `progress.md`, plan/attestation/attachment; clears a private per-turn reminder marker | Non-empty output becomes `hookSpecificOutput.additionalContext`; binding requirement returns a notice | Advisory context by default; gated remains start-of-turn context |
| `PreToolUse` | `Bash\|apply_patch\|Edit\|Write`; `pre_tool_use.py` → `pre-tool-use.sh` | Selected `task_plan.md`; legacy mode may frame plan data on stderr; does not write the project | `decision: allow`; stderr becomes `hookSpecificOutput.additionalContext` | Allows and reminds by default; autonomous/gated omit per-tool plan recitation and cannot use this to block ordinary writes |
| `PermissionRequest` | No matcher; `permission_request.py` | Resolves the selected plan and checks `task_plan.md`; no cache or project write | `systemMessage` asks the person to review current phase before approval | Always read-only and never blocks the request; gated does not turn approval into a gate |
| `PostToolUse` | `apply_patch\|Edit\|Write`; `post_tool_use.py` → `post-tool-use.sh` | Selected `task_plan.md`; writes a once-per-turn private marker in `XDG_CACHE_HOME` / `~/.cache` / temp, never the plan | Non-empty output becomes `hookSpecificOutput.additionalContext`, reminding the model about progress/phase status | Advisory; never edits records and does not force continuation |
| `PreCompact` | `*`; `run_sh.py pre-compact.sh` | Selected `task_plan.md`, optional attestation; no project write | `continue: true` and a `systemMessage` to preserve progress before compaction | Diagnostic only and never blocks compaction; gated does not turn it into document writing |
| `Stop` | No matcher; `stop.py` → `stop.sh`, timeout 30 seconds | Selected `task_plan.md`, `.mode`, ledger/gate counter; does not write durable docs | Normally status `systemMessage`; a qualifying gate returns `decision: block` with a fixed reason | Default is advisory. Only explicit gated mode with an in-progress phase, no recursion, remaining cap, and ledger progress requests host continuation; otherwise stop is allowed |

A hard `Stop` block never means “an incomplete plan always blocks.” If mode, phase, recursion flag, cap, or progress does not qualify, it falls back to allowing stop. It also does not establish that code, documents, or human review passed.

## Distribution matrix for every host

The event column is the package's registered execution events. “No execution Hook” is an explicit distribution fact, not a missing value. Native extension/plugin events are not JSON Hooks. Every row still requires host discovery, trust, enablement, and live-load verification.

| Host | Main Skill / distribution form | Registered events or native bridge | Context injection? block/continue? | Limits |
| --- | --- | --- | --- | --- |
| `agents` | Portable `project-docs` Skill | **No execution Hook** | No automatic context; no block/continue | Relies on host Skill discovery and model reading |
| `claude` | Claude plugin + `project-docs` | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, `Stop`; `hooks/claude-hook.sh` | Host-protocol injection; gated can use the Stop mechanism | Event availability and trust remain Claude-controlled |
| `codebuddy` | Plugin manifest + portable Skill | **No execution Hook** | No automatic context; no block/continue | Copied files do not prove GUI/host enablement |
| `codex` | Codex marketplace plugin + native Skill layout | The seven events above; `.codex/hooks/*.py/.sh` | Context injection; only an explicit gated qualifying Stop can request `decision:block` | Verify marketplace discovery, Hook trust, session binding, and Skill reading separately |
| `continue` | Portable Skill/prompt distribution | **No execution Hook** | No automatic context; **never requests continuation** | A static package does not add lifecycle capability the host lacks |
| `copilot` | Native plugin + `project-docs` | `sessionStart`, `postToolUse`, `agentStop`; `hooks/native-hook.py` | `additionalContext` injection; Stop uses only the host return shape | No prompt-submit/pre-tool permission decision is registered; experimental adapter |
| `cursor` | Cursor plugin + `project-docs` | `sessionStart`, `postToolUse`, `stop`; `hooks/native-hook.py` | `additional_context` injection; gated is follow-up only, bounded by `loop_limit` | `beforeSubmitPrompt`/`preToolUse` are not portable injection surfaces here |
| `dsh` | DSH profile bundle + Skill | `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `Stop`; official Claude command-hook bridge | Injection at bridge events; Stop depends on DSH bridge protocol | No `PreCompact` or `PreToolUse` bridge; profile install/merge remains separate |
| `factory` | Plugin manifest + portable Skill | **No execution Hook** | No automatic context; no block/continue | Host UI discovery, trust, and enablement are not proved by the manifest |
| `gemini` | Gemini extension + `project-docs` | `SessionStart`, `BeforeAgent`, `AfterTool`, `PreCompress`; `hooks/native-hook.py` | `hookSpecificOutput.additionalContext` / `systemMessage`; no Stop registered | Session end is status notification only; no continuation request |
| `hermes` | Hermes native plugin + Skill | Native `pre_llm_call`, `post_tool_call`, `pre_verify` | Context injection; gated `pre_verify` can request `action: continue` | Not a JSON Hook; continuation is bounded by Hermes' verification loop |
| `kiro` | Kiro Power/plugin manifest + Skill/steering assets | **No execution Hook** | No automatic context; no block/continue | Discoverable Kiro resources do not mean this package registered lifecycle; records stay in target workspace |
| `mastracode` | Portable Skill distribution | **No execution Hook** | No automatic context; no block/continue | Hook merging may need manual host action; copied files do not prove loading |
| `opencode` | Locally compiled OpenCode V1 plugin + separate Skill | `chat.message`, `tool.execute.after`, `session.idle`; `dist/index.js` | Can append context/post-write reminder; gated uses `session.idle` follow-up and cannot block original completion | Plugin and Skill are discovered separately; do not double-register loader and npm copy |
| `pi` | Pi Skill + TypeScript Extension | Native `session_start`, `input`, `before_agent_start`, `tool_call`, `tool_result`, `agent_end`, `session_before_compact` | Context/reminders; gated uses bounded `followUp` auto-continuation, not a hard block | Pi approval/enablement is required; Extension events are not JSON Hooks |

## Fault isolation and evidence boundary

- If a new session has no expected context, check “installer record → host discovery/trust → enable/reload → session binding → event support → actual Skill reading” separately; do not collapse it into “enabled.”
- Strict read-only work needs a control the host supports before session startup. `PLANNING_DISABLED=1` stops planning context on verified paths, but natural-language wording cannot undo a Hook that already fired.
- Static manifest, JSON, source, and these tables prove **distribution declarations and code paths**, not live host loading, model reading, permission outcomes, or task behavior. Record executed validation in `progress.md`; mark unexecuted validation `Not Run`.
