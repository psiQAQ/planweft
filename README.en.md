[简体中文](README.md) | [English](README.en.md)

# PlanWeft

PlanWeft keeps a coding agent's task plan, findings, and validation record in the project. A later session or collaborator can continue from those files without relying on chat history.

The current source target is **0.5.0 (unreleased)**. It uses a pinned planning-with-files (PWF) v3.17.0 runtime and adds a document-handoff interface managed by the `project-docs` Skill and read by Hooks. The registry installation entry point remains the published 0.4.0 until 0.5.0 completes its static/logic gate and later promotion.

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

## 0.5.0 validation boundary

| Capability | Status |
| --- | --- |
| Rebuildable package, package static checks, Hook logic, Skill/Hook association, and document-handoff marker | Required for 0.5.0 |
| Independent source review and project-files-only cold read | Required for 0.5.0 |
| Docker, five-Agent runtime, real-host, or real-model behavior | Not Run for 0.5.0 and not a release gate |
| 0.4.0 five-host installation and lifecycle acceptance | Historical evidence; not automatically transferred to 0.5.0 |

Unrun checks are never reported as Passed. The 0.5.0 document handoff is advisory by default; it reuses an existing PWF block budget only after the user explicitly enables gated mode and the original PWF conditions pass. The 0.4.0 five-host and syscall limits remain historical. See [SPEC-0006](docs/specs/0006-skill-hook-document-handoff.md) for the full boundary.

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

The project is distributed as one `planweft` npm package. The 0.4.0 release assets, exact archive digest, and acceptance records remain available from the [v0.4.0 GitHub Release](https://github.com/psiQAQ/planweft/releases/tag/v0.4.0).
