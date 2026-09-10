[简体中文](platforms.md) | [English](platforms.en.md)

# Platform support and limitations

PlanWeft 0.4.0 provides a supported core on five hosts and experimental distributions for ten more. “Supported” covers only the declared capabilities that passed acceptance. It does not imply that every host has the same hooks, continuation, or permission model.

See the [installation guide](installation.en.md) for commands. [`release/support-policy.json`](../release/support-policy.json) is the itemized policy, and [`release/acceptance.json`](../release/acceptance.json) records the results.

## Supported hosts

| Host | Installer ID | Core capabilities | 0.4.0 model workflow |
| --- | --- | --- | --- |
| Codex | `codex` | Passed | Explicit maintenance and independent cold read Passed |
| Claude Code | `claude` | Passed | No supported model workflow declared |
| Pi | `pi` | Passed | Explicit/automatic maintenance and cold read Passed under frozen conditions; evidence-rated |
| OpenCode V1 | `opencode` | Passed | No supported model workflow declared |
| DeepSeek Harness | `dsh` | Passed | No supported model workflow declared |

The five-host core covers exact package contents, runtime dependencies, installation, update, rollback, removal, reinstallation, explicit Skill reading, default advisory behavior, explicit disable behavior, project isolation, user-file protection, and duplicate-source checks. Final registry installation, native discovery, fresh-session loading, and removal also passed promotion acceptance.

These results bind the exact 0.4.0 npm archive with SHA-256 `e611338a619adabb0ba943d75460a01d83e4670dbe7d69f5d1050a1c1467c132`. A documentation change does not extend that result to another version or runtime condition.

## Experimental capabilities

The following are available but are not part of the supported 0.4.0 contract:

- Autonomous/gated continuation and real-model stopping on every host.
- Automatic model adoption outside Codex, except for the explicitly recorded frozen Pi comparisons.
- Distribution adapters for Cursor, Gemini CLI, GitHub Copilot CLI, Hermes, Mastra Code, Kiro, Continue, Factory, CodeBuddy, and generic Agent Skills.
- Model scope adherence under different hosts, models, permissions, or versions.

Experimental adapters claim only the static, protocol, or lifecycle checks that were actually completed. A directory or manifest does not prove host loading or model-level document maintenance.

## Known limitations

- The Codex gate-cap enabled/disabled pair is **Failed**. The trace still contains an unattributed syscall result, so `trace_complete=false`. The public limit ID is `LIMIT-CODEX-TRACE-INCOMPLETE`. The sessions ended normally, but that does not make the scenarios Passed.
- Other experimental stopping and model scenarios include Not Run results. Their reasons remain recorded and are not replaced by historical candidate results.
- Model scope adherence is an evaluation result, not a security boundary. The host and user configuration still control file, command, and network permissions.
- Default behavior is advisory. Gated mode uses only the stop or follow-up mechanisms provided by the host; it does not add missing lifecycle events.
- The Hermes distribution remains experimental. Historical default-scanner rejection is preserved in reproduction evidence, and this release does not promise a scanner bypass.

## Host differences

The `planweft` installer deploys each complete integration in its native layout. Codex and Claude Code use their own plugin discovery, Pi packages its Skill and Extension together, OpenCode V1 pairs a plugin with a separately discovered Skill, and DSH uses a profile bundle. GUI and Skill-only platforms may require their native UI for enablement, trust, or hook merging.

Project records are separate from plugin installation paths. Updating or removing the plugin does not delete `task_plan.md`, `findings.md`, `progress.md`, `.planning/`, attestations, ledgers, specs, ADRs, or reproduction records. Enable only one planning hook implementation in a session.

## Engineering records

Generation directories, catalogs, event protocols, resource resolution, and release-tree design are maintainer material:

- [Development and generation](development.md)
- [Upstream and distribution maintenance](upstream-maintenance.md)
- [Release and evidence maintenance](releasing.en.md)
- [0.4.0 reproduction record](reproduction/0010-five-agent-release.md)
- [Native distribution specification](specs/0004-native-distributions.md)

These records explain implementation and historical evidence. They do not expand the support contract on this page.
