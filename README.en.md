[简体中文](README.md) | [English](README.en.md)

# PlanWeft

PlanWeft keeps a coding agent's task plan, findings, and validation record in the project. A later session or collaborator can continue from those files without relying on chat history.

The current stable release is **0.4.0**. It uses a pinned planning-with-files (PWF) v3.17.0 runtime and provides accepted installation and lifecycle support for Codex, Claude Code, Pi, OpenCode V1, and DeepSeek Harness.

## Quick start

Node.js 22 or newer is required. This example installs the complete Codex integration and checks its state:

```bash
npx planweft@0.4.0 add -a codex --global
npx planweft@0.4.0 doctor -a codex --global
```

In a new session, invoke `$project-docs` explicitly and confirm that the agent reads the Skill. See the [installation guide](docs/installation.en.md) for scope, trust, and loading details on other hosts.

## What it records

A complex task normally uses three working files:

| File | Contents |
| --- | --- |
| `task_plan.md` | Goal, phases, next action, and blockers |
| `findings.md` | Research, sources, assumptions, and open questions |
| `progress.md` | Actions taken, errors, and test results |

Durable requirements, design decisions, and reproduction material remain in the project's existing specs, ADRs, and reproduction documents. PlanWeft does not require a full document set for every small change, and it does not treat host chat history as the default recovery source.

## 0.4.0 support

| Capability | Status |
| --- | --- |
| Exact artifacts, installation, update, rollback, removal, and reinstallation on Codex, Claude Code, Pi, OpenCode V1, and DSH | Supported |
| Project isolation, user-file protection, duplicate-source checks, explicit Skill reading, default advisory behavior, and explicit disable behavior on those five hosts | Supported |
| Codex explicit maintenance followed by an independent cold-read session | Supported workflow |
| Pi explicit and automatic maintenance plus cold read | Passed under the frozen 0.4.0 conditions; evidence-rated |
| Autonomous/gated behavior, automatic model adoption, and the other ten platform adapters | Experimental |

Experimental failures and Not Run results remain visible. The Codex gate-cap enabled/disabled pair is Failed because syscall attribution was incomplete (`LIMIT-CODEX-TRACE-INCOMPLETE`); this does not change the supported five-host core. See [platform support and limitations](docs/platforms.en.md) and [`release/support-policy.json`](release/support-policy.json) for the full policy.

## Boundaries

- The default mode is advisory. It does not guarantee task completion. Autonomous/gated behavior requires explicit activation and depends on the host.
- Attestation checks file contents; it does not prove human approval. Completion gates check plan state; they do not prove correctness.
- Model scope adherence is a published evaluation result, not a security-isolation guarantee. The host still owns file and command permissions.
- Enable only one planning hook implementation in a session. The installer reports detectable duplicates but does not remove other plugins automatically.
- Updating or removing the plugin does not roll back or delete project plans, user notes, specs, ADRs, or reproduction records.

## Documentation

- [Install, update, roll back, and remove](docs/installation.en.md)
- [Platform support and known limitations](docs/platforms.en.md)
- [Development and generation](docs/development.md)
- [Release and evidence maintenance](docs/releasing.en.md)
- [Test entry points](tests/README.md)
- [Design-reference ledger](docs/design-references.md)

The project is distributed as one `planweft` npm package. Release assets, the exact archive digest, and acceptance records are available from the [v0.4.0 GitHub Release](https://github.com/psiQAQ/planweft/releases/tag/v0.4.0).
