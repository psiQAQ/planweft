[简体中文](README.md) | [English](README.en.md)

> PlanWeft 0.4.0-rc.1 is a release candidate. Stable 0.4.0 requires live acceptance on Codex, Claude Code, Pi and OpenCode. See the [release checklist](docs/releasing.en.md) / [中文](docs/releasing.md).

# PlanWeft

**Keep an agent's progress, design rationale and validation results in the project so later sessions and collaborators can continue the work.**

PlanWeft is a file-based planning and project documentation plugin for coding agents. It uses **planning-with-files (PWF) v3.17.0** as its pinned runtime and adds selective documentation maintenance, design-evidence checks and verifiable handoffs to the default planning and recovery workflow.

It is intended for feature development, maintenance, investigations and design work that span sessions: continuing the current task while retaining confirmed requirements, significant decisions and observed validation. Small changes maintain only the necessary records, following the project's existing layout and rules.

| Reading goal | 中文 | English |
| --- | --- | --- |
| Install, update, roll back and uninstall | [安装指南](docs/installation.md) | [Installation guide](docs/installation.en.md) |
| Understand host adapters, distribution and capability differences | [跨平台设计](docs/platforms.md) | [Cross-platform design](docs/platforms.en.md) |

## Design principles

**Use project files to carry working context.** Complex tasks keep goals, findings and actions in a selected PWF plan directory. New sessions recover from project records; reading host session history still requires an explicit invocation. One owner maintains each plan, workers use separate records, and independent tasks use separate plans or worktrees.

**Give task records and durable documents distinct responsibilities.** The three planning files serve the task in progress. Stable knowledge moves into the project's existing specifications, ADRs and reproduction records when needed. Small changes do not require a full document set, and approved requirements are not rewritten just to match the current code.

| Record | Responsibility |
| --- | --- |
| `task_plan.md` | The current task's single dynamic status: goal, phases, next action, blockers and evidence links |
| `findings.md` | Research findings, sources, assumptions and candidate decisions |
| `progress.md` | Actual actions, errors, tests and observations |
| specs | Intended behavior, boundaries and approved acceptance requirements |
| ADR | Significant design choices, alternatives, rationale and consequences |
| reproduction | Environments, reproduction steps, results and limitations worth retaining |

**Separate evidence review from handoff review.** Substantive designs need precise sources; gaps require a record of searches actually performed and what remains unverified. Important designs receive an independent evidence review. Important handoffs receive a reader check without the old conversation. Both use existing host Agent capabilities. These are Skill instructions, with no additional scheduling service.

**Keep automation boundaries explicit.** Supporting hosts may match the main `project-docs` entry to a task. The default runtime is advisory; autonomous/gated modes and native execution are selected explicitly according to the host. Project rules, user scope, read-only requests and host trust take precedence. Attestation checks file contents and completion gates check state; neither proves human approval or semantic correctness.

## How a task progresses

1. Read the project entry points and task constraints, then locate existing specifications, decisions and validation material.
2. For authorized complex work, resolve or initialize the task's PWF plan. Reading, diagnosis and simple work retain their appropriate minimal scope.
3. Record findings and actual operations while implementing, minimally update affected documents, and preserve the user's existing edits.
4. Record validation as Passed, Failed or Not Run. Compare approved requirements with actual results and explain limitations.
5. Apply independent evidence review or a fresh-reader handoff as the task warrants, and leave an actionable next step.

These practices depend on the agent reading and following the Skill correctly. The plugin provides records, recovery and host adapters; task outcomes still require validation.

## Comparison with related approaches

This comparison uses the fixed versions actually consulted by this repository. It describes focus and influence, without ranking performance. Links point to the original material.

| Approach | Primary focus | Influence on PlanWeft and differences |
| --- | --- | --- |
| **PlanWeft** | Task state, durable documents, design evidence and handoffs across sessions | Combines the approaches below on a PWF runtime, with generated host distributions; comparative effectiveness has not been established |
| [PWF v3.17.0](https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/skills/planning-with-files/SKILL.md) | Three-file task memory, recovery, hooks and planning controls | Direct runtime and state-protocol base; selective documentation maintenance and evidence/handoff checks become part of the default workflow. PWF already advises keeping durable knowledge separately |
| [OpenSpec](https://github.com/Fission-AI/OpenSpec/blob/e062b9572be933564ba3899d059377dfa1393e32/docs/concepts.md) | Behavior specifications, change proposals, design, tasks, delta specs and archiving | Informs the separation of intended behavior, design and tasks, and rigor proportional to risk; its schema and delta-merge engine are not integrated |
| [Superpowers](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/writing-plans/SKILL.md) | Executable small-task plans with files, tests and execution handoffs | Informs resumable plans and thin host adapters; its full required Skill chain is not adopted, nor is one TDD workflow imposed |
| [doc-coauthoring](https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/skills/doc-coauthoring/SKILL.md) | Gathering context, iterative document refinement and fresh-reader testing | Informs the independent-reader check; source-evidence review is a separate local requirement |
| [MADR](https://github.com/adr/madr/blob/ba75bb1b20d42af5746b246ad348c202419ae681/template/adr-template.md) | Significant decisions, alternatives, rationale, consequences and confirmation | Informs minimal ADRs for durable decisions as needed; MADR itself is not a task-recovery or plugin runtime |

PWF's [after-completion guidance](https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/docs/workflow.md) already distinguishes task working memory from durable documents. Superpowers' [native adapter source](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/.pi/extensions/superpowers.ts) is another reference for thin adapters. This repository also draws on OpenAI's repository-knowledge and resumable-plan practices, and Diátaxis' separation of documentation responsibilities. Full sources, licenses and precise influences are recorded in the [design-reference ledger (engineering record, Chinese)](docs/design-references.md) and [reference index (engineering record, Chinese)](docs/reference/README.md).

## Local additions and original implementation

This project contributes the concrete workflow integration and engineering:

- **Default documentation workflow:** the [workflow overlay](overlays/planweft/workflow.md) brings existing-document maintenance, precise sources, approved-requirement protection, validation status and independent handoffs into `project-docs`.
- **Traceable builds and distribution:** a pinned upstream snapshot, local overlays and the [generator](scripts/build-plugin.py) produce host directories. Per-file content and executable-bit digests detect drift while maintaining one product identity.
- **Host adapters and release preparation:** the [native adapter layer](overlays/planweft/native/adapters.py) handles installed-asset paths, event protocols and discovery differences. The [release preparation tool](scripts/prepare-native-release.py) produces native npm artifacts and Git release trees with the plugin at the root.
- **Validation tied to installed contents:** evidence records installed files, added/changed/deleted resources during updates, rollback, uninstall and project-document protection, separating script protocols, host loading and model behavior.

“Original implementation” here means extensions and integration written for this repository. It does not claim to have invented file-based planning, ADRs, fresh-reader testing or generated distributions, nor to have established identical behavior or effectiveness across hosts. Runtime inheritance and local differences are traceable in the [patch inventory (engineering record, Chinese)](overlays/planweft/PATCHES.md); methodological novelty is considered separately in the [innovation record (engineering record, Chinese)](docs/innovations.md).

## Current delivery and boundaries

Candidate **0.4.0-rc.1** provides 15 host directories (including DSH Skill-only), six native marketplace entry points, and preparation of Pi/OpenCode npm artifacts and Gemini/Hermes Git release trees. See the [中文安装指南](docs/installation.md) / [English installation guide](docs/installation.en.md), and the [中文跨平台设计](docs/platforms.md) / [English cross-platform design](docs/platforms.en.md) for capabilities and validation scope.

The 0.3.0 record includes local installation lifecycle checks for eight hosts. Hermes installation was rejected by its default scanner. GUI, Windows/macOS, public remote channels and new-version real-model maintenance/fresh-reader checks retain Not Run items. Historical evidence does not become a new host run when documentation changes; the cross-platform documents explain these boundaries.

This repository has not been publicly released and does not supply unverified Git/npm installation addresses. Distributions retain PWF's MIT copyright and license; other reference material follows its own licensing. This repository itself continues to use its existing document entry points and has not formally migrated to plugin-managed planning.

Maintainer material: [development conventions (Chinese)](docs/development.md) · [upstream maintenance (Chinese)](docs/upstream-maintenance.md) · [tests and evidence (Chinese)](tests/README.md). These engineering records retain their original language; the public overview, installation guide and cross-platform design have the paired Chinese and English versions above.
