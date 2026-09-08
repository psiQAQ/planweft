[简体中文](README.md) | [English](README.en.md)

> Package: **opencode**. Use this host's installation section.

# Program Design 0.3.0

Program Design is a file-based planning and project documentation plugin for AI agents. It builds on [planning-with-files v3.17.0](https://github.com/OthmanAdi/planning-with-files/releases/tag/v3.17.0), adding long-term documentation maintenance, design evidence review and verifiable handoff to task planning, recording and recovery. It is an independent derivative pinned to upstream commit `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`, with MIT attribution and licensing retained.

**Installation, updates, rollback and removal:** [简体中文](INSTALL.md) | [English](INSTALL.en.md). Select the section for the host identified by the current package. The installed package supplies runtime resources; the target project stores task records.

## Workflow

The main Skill is `project-docs`. A supporting host may select it for substantive implementation, maintenance and continuation of documented work; explicit invocation remains available. Automatic matching does not require prior project opt-in, but actual loading depends on the host. Reading and diagnosis remain read-only. Simple tasks do not require a planning hierarchy. Project rules and user scope take precedence.

Complex implementation uses one selected PWF plan directory. `task_plan.md` owns current status and the next action, `findings.md` holds discoveries and sources, and `progress.md` records actions and observed validation. Existing specifications, ADRs and reproduction records retain stable requirements, decisions and evidence. Create or minimally update them only when useful to the authorized task.

An independent evidence reviewer checks important designs. For important handoffs, a fresh reader who has not read the old chat checks the project files. This uses the host's existing Agent capabilities without adding a scheduling service. See the main Skill's `references/evidence.md` for guidance.

## Runtime boundaries

- Default behavior is advisory. Autonomous and gated modes are explicit choices with host-specific behavior; Skill matching alone does not enable continuation.
- Helper commands have `pd-` names; OpenCode tools have `pd_` names. Available commands depend on the installed adapter. `PLAN_ID`, `PWF_*`, `PLANNING_DISABLED` and PWF state formats remain compatible.
- Use the host's disable controls for a strict read-only session. `PLANNING_DISABLED=1` is sufficient only on adapter routes with verified behavior. Automatic recognition of every natural-language read-only intent is not guaranteed. Private hook caches and project records are managed separately.
- Only one planning plugin should run execution hooks in a session. Inspect doctor output and active host configuration for detectable overlap; installing this plugin does not automatically uninstall PWF.
- Automatic recovery reads project files only. Session-history metadata or bounded replay requires an explicit request.
- Attestation checks file content and does not represent human approval. Gated checks examine runtime state and do not prove requirements or code correctness.

## Distribution and provenance

The source repository generates independent `dist/<host>/program-design/` directories for 14 hosts. Each package contains the runtime, templates, references, `LICENSE` and `UPSTREAM.json` needed by its adapter. Installation and updates use the host's native channels. No platform ZIPs are generated, and hosts do not have identical hook capabilities. Factory, CodeBuddy and Kiro provide Skill wrappers; Kiro manages Powers in the IDE, while CLI v3 discovers IDE-installed Powers automatically.

Updates are explicit by default. Refreshing a marketplace, updating a plugin, reloading a session and trusting changed hooks are separate operations. Keep source directories used by local-path installations. Prepared Git/npm coordinates are not proof of public availability. Validation distinguishes static inspection, protocol tests and real host results. Unavailable environments are Not Run; failures retain their observed outcome. See the [installation guide (Chinese)](INSTALL.md) / [installation guide (English)](INSTALL.en.md).

Package updates and removal preserve the target project's plans and evidence. When a project formally adopts this workflow, relocate its old active status entry to the PWF plan once and retain the history, without two-way synchronization. Building or preparing a release does not install plugins, change personal configuration, push Git branches or publish npm packages.
