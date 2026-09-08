# Program Design 0.2.0 — codex

# Program Design 0.2.0

Program Design combines the planning-with-files v3.17.0 runtime with project documentation, design evidence and verifiable handoff. It is an independent derivative pinned to upstream commit `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`. The distribution retains upstream MIT attribution and contains the runtime, templates and references needed by its adapter.

## Workflow

The main Skill is `project-docs`. A supporting host may select it for substantive implementation, maintenance and continuation of documented work; explicit invocation remains available. Automatic matching does not require a project opt-in, but loading depends on the host. Read-only requests remain read-only, simple work does not require a planning hierarchy, and project rules and task scope take precedence.

Complex implementation uses one selected PWF plan directory. `task_plan.md` owns current status and the next action, `findings.md` holds discoveries and sources, and `progress.md` records actions and observed validation. Existing specifications, ADRs and reproduction records retain stable requirements, decisions and evidence. Create or update these only when useful to the authorized task.

## Runtime controls

- Default runtime behavior is advisory. Autonomous and gated modes are explicit choices with host-specific behavior; Skill matching alone does not enable continuation.
- Helper commands have `pd-` names; OpenCode tool names have `pd_` names. Use the installed adapter's command listing for available native controls. `PLAN_ID`, `PWF_*`, `PLANNING_DISABLED` and PWF state formats remain compatible.
- Set `PLANNING_DISABLED=1` before starting a strict read-only session when the host cannot reliably identify that mode. Private hook caches are separate from project records; automatic natural-language intent detection is not guaranteed.
- Only one planning plugin should run execution hooks in a session. Inspect the installed doctor output and active host configuration for detectable overlap; this package does not automatically uninstall another plugin.
- Automatic recovery uses project files. Reading host session history requires an explicit request for metadata or bounded replay.
- Attestation checks file bytes and does not prove approval. Completion gating checks runtime state and does not certify requirements or code correctness.

## Platform and installation limits

Use the installation instructions and compatibility matrix delivered with this build. Preserve each host's native activation and trust requirements: adding plugin files is not proof that Skills or hooks loaded. Codex hook installation and host trust are separate steps. Pi and OpenCode retain their native extension/plugin behavior. Do not assume every adapter can block stopping or automatically load a Skill.

Verification distinguishes static inspection, protocol tests and real host runs; unavailable operating systems or hosts are reported as Not Run. No package installation changes global configuration automatically. A target project adopts a PWF task state by explicitly relocating its active status entry once and linking the historical plan, without two-way synchronization.

See the installed Skill's `references/evidence.md` for source review, requirement preservation, verification and fresh-reader handoff guidance.
