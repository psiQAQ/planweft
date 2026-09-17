[简体中文](hosts.md) | [English](hosts.en.md)

# Host distribution and capability boundaries

PlanWeft 0.6.0 lists 15 host distribution targets in `dist/manifest.json`. At the product level, `codex`, `claude`, `pi`, `opencode`, and `dsh` are the primary supported integrations; the remaining targets are treated as experimental adapters. A distribution target means that the package prepares resources for a host; it does not mean that the host discovered, trusted, enabled, or loaded those resources.

## How to read this page

- “Product status” tells you whether an integration is part of the current primary supported set or remains experimental.
- “Static events” come from the current generated manifest, Hook configuration, or native adapter source and describe the entry points prepared by the package.
- “Historical acceptance evidence” records validation completed for an exact prior version; it does not automatically establish current-version host behavior.
- The current P0 release checks are defined by the [version policy file](https://github.com/psiQAQ/planweft/blob/master/release/support-policy-0.6.0.json); this deterministic static/logic scope does not replace real host or model regression, which remains `Not Run` for this release.

## Host matrix

| Host | Distribution form | Static events or native entry point | Product status | Historical acceptance evidence |
| --- | --- | --- | --- | --- |
| `agents` | Portable `project-docs` Skill | No execution Hook | Experimental | — |
| `claude` | Claude plugin + Skill | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, `Stop` | Supported | 0.4.0 formal core |
| `codebuddy` | Plugin manifest + portable Skill | No execution Hook | Experimental | — |
| `codex` | Codex marketplace plugin + native Skill | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `Stop` | Supported | 0.4.0 formal core |
| `continue` | Portable Skill/prompt distribution | No execution Hook | Experimental | — |
| `copilot` | Native plugin + Skill | `sessionStart`, `postToolUse`, `agentStop` | Experimental | — |
| `cursor` | Cursor plugin + Skill | `sessionStart`, `postToolUse`, `stop` | Experimental | — |
| `dsh` | DSH profile bundle + Skill | `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `Stop` | Supported | 0.4.0 formal core |
| `factory` | Plugin manifest + portable Skill | No execution Hook | Experimental | — |
| `gemini` | Gemini extension + Skill | `SessionStart`, `BeforeAgent`, `AfterTool`, `PreCompress` | Experimental | — |
| `hermes` | Native plugin + Skill | `pre_llm_call`, `post_tool_call`, `pre_verify` | Experimental | — |
| `kiro` | Power/plugin manifest + Skill | No execution Hook | Experimental | — |
| `mastracode` | Portable Skill | No execution Hook | Experimental | — |
| `opencode` | V1 plugin + separate Skill | `chat.message`, `tool.execute.after`, `session.idle` | Supported | 0.4.0 formal core |
| `pi` | Skill + TypeScript Extension | `session_start`, `input`, `before_agent_start`, `tool_call`, `tool_result`, `agent_end`, `session_before_compact` | Supported | 0.4.0 formal core |

“No execution Hook” is a distribution fact, not an unfinished placeholder: the host may receive the Skill or resources, but this package does not add lifecycle events that the host does not provide.

## Capability differences

The installer deploys a host-specific layout. Skill-only installation provides a discoverable `project-docs` Skill without registering complete plugin Hooks. Native extensions, JSON Hooks, profile bundles, and portable Skills have different discovery and trust flows.

Default behavior is advisory: Hooks may provide context or reminders but do not automatically edit durable documents. Autonomous/gated behavior requires explicit activation; whether a host can continue or block completion depends on its protocol and current conditions.

To confirm that a task is actually active, check these separately:

1. The installer recorded the expected host and scope.
2. The host discovered, trusted, and enabled the resources.
3. The current session loaded the expected version.
4. The relevant Hooks are enabled, if the host provides complete integration.
5. The model actually read the `project-docs` Skill.
6. The task records contain the expected results.
7. A later session can resume from the project records.

`doctor` primarily checks managed installation state and cannot replace checks 4 through 7.

## Acceptance evidence versus current support

Product status and acceptance evidence are separate dimensions. “Supported” identifies the integrations targeted by the current primary installation and documentation path. “0.4.0 formal core” only says that the exact 0.4.0 archive completed that historical acceptance scope. The deterministic P0 result for 0.6.0 does not prove equivalent behavior in a real host or model environment.

## Troubleshooting

- When context is missing, check installation records, host discovery/trust, enablement/reload, session loading, event support, and Skill reading in that order.
- The manifest, source, and directory tree establish static distribution relationships only; they do not establish host loading, model reading, or task correctness.
- Record real checks with their environment, inputs, outputs, and `Passed` / `Failed` / `Inconclusive` / `Not Run` status. Do not fill an unrun scenario with a historical result.

See the [installation guide](installation.en.md) for installation and updates, and the [architecture guide](architecture.en.md) for the runtime model.
