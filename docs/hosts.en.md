[简体中文](hosts.md) | [English](hosts.en.md)

# Host distribution and capability boundaries

PlanWeft 0.5.1 lists 15 host distribution targets in `dist/manifest.json`. A distribution target means that the package prepares resources for a host; it does not mean that the host discovered, trusted, enabled, or loaded those resources.

## How to read this page

- “Static events” come from the generated manifest, Hook configuration, or native adapter source.
- “0.4.0 formal core (version-bound)” describes the historical acceptance scope of the exact 0.4.0 archive. It does not extend automatically to 0.5.1 model behavior.
- The remaining targets are experimental distributions or Skill-only forms and must be checked separately under each host's rules.
- The 0.5.1 release checks are defined by the [version policy file](https://github.com/psiQAQ/planweft/blob/master/release/support-policy-0.5.1.json); package static checks do not replace real host regression.

## Host matrix

| Host | Distribution form | Static events or native entry point | Status |
| --- | --- | --- | --- |
| `agents` | Portable `project-docs` Skill | No execution Hook | Experimental distribution |
| `claude` | Claude plugin + Skill | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, `Stop` | 0.4.0 formal core (version-bound) |
| `codebuddy` | Plugin manifest + portable Skill | No execution Hook | Experimental distribution |
| `codex` | Codex marketplace plugin + native Skill | `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `Stop` | 0.4.0 formal core (version-bound) |
| `continue` | Portable Skill/prompt distribution | No execution Hook | Experimental distribution |
| `copilot` | Native plugin + Skill | `sessionStart`, `postToolUse`, `agentStop` | Experimental distribution |
| `cursor` | Cursor plugin + Skill | `sessionStart`, `postToolUse`, `stop` | Experimental distribution |
| `dsh` | DSH profile bundle + Skill | `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `Stop` | 0.4.0 formal core (version-bound) |
| `factory` | Plugin manifest + portable Skill | No execution Hook | Experimental distribution |
| `gemini` | Gemini extension + Skill | `SessionStart`, `BeforeAgent`, `AfterTool`, `PreCompress` | Experimental distribution |
| `hermes` | Native plugin + Skill | `pre_llm_call`, `post_tool_call`, `pre_verify` | Experimental distribution |
| `kiro` | Power/plugin manifest + Skill | No execution Hook | Experimental distribution |
| `mastracode` | Portable Skill | No execution Hook | Experimental distribution |
| `opencode` | V1 plugin + separate Skill | `chat.message`, `tool.execute.after`, `session.idle` | 0.4.0 formal core (version-bound) |
| `pi` | Skill + TypeScript Extension | `session_start`, `input`, `before_agent_start`, `tool_call`, `tool_result`, `agent_end`, `session_before_compact` | 0.4.0 formal core (version-bound) |

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

## Troubleshooting

- When context is missing, check installation records, host discovery/trust, enablement/reload, session loading, event support, and Skill reading in that order.
- The manifest, source, and directory tree establish static distribution relationships only; they do not establish host loading, model reading, or task correctness.
- Record real checks with their environment, inputs, outputs, and `Passed` / `Failed` / `Inconclusive` / `Not Run` status. Do not fill an unrun scenario with a historical result.

See the [installation guide](installation.en.md) for installation and updates, and the [architecture guide](architecture.en.md) for the runtime model.
