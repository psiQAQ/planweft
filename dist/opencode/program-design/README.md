# Program Design 0.3.0 — opencode

# Program Design 0.3.0

Program Design combines the planning-with-files v3.17.0 runtime with project documentation, design evidence and verifiable handoff. It is an independent derivative pinned to upstream commit `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`. The distribution retains upstream MIT attribution and contains the runtime, templates and references needed by its adapter.

## Workflow

The main Skill is `project-docs`. A supporting host may select it for substantive implementation, maintenance and continuation of documented work; explicit invocation remains available. Automatic matching does not require a project opt-in, but loading depends on the host. Read-only requests remain read-only, simple work does not require a planning hierarchy, and project rules and task scope take precedence.

Complex implementation uses one selected PWF plan directory. `task_plan.md` owns current status and the next action, `findings.md` holds discoveries and sources, and `progress.md` records actions and observed validation. Existing specifications, ADRs and reproduction records retain stable requirements, decisions and evidence. Create or update these only when useful to the authorized task.

## Runtime controls

- Default runtime behavior is advisory. Autonomous and gated modes are explicit choices with host-specific behavior; Skill matching alone does not enable continuation.
- Helper commands have `pd-` names; OpenCode tool names have `pd_` names. Use the installed adapter's command listing for available native controls. `PLAN_ID`, `PWF_*`, `PLANNING_DISABLED` and PWF state formats remain compatible.
- Use the host’s disable controls for a strict read-only session. `PLANNING_DISABLED=1` is sufficient only on adapter routes with verified disable behavior. Private hook caches are separate from project records; automatic natural-language intent detection is not guaranteed.
- Only one planning plugin should run execution hooks in a session. Inspect the installed doctor output and active host configuration for detectable overlap; this package does not automatically uninstall another plugin.
- Automatic recovery uses project files. Reading host session history requires an explicit request for metadata or bounded replay.
- Attestation checks file bytes and does not prove approval. Completion gating checks runtime state and does not certify requirements or code correctness.

## Platform and installation limits

Each host has a self-contained directory at `dist/<host>/program-design/` in the source repository. There is no ZIP extraction step. Read this package's `INSTALL.md` and use the section for the host named at the top; the package root is an installation source, not the target project. Keep its complete scripts, templates, references, license and provenance.

Use native marketplaces where supported, Pi packages, the precompiled OpenCode V1 package, Gemini extensions, Hermes plugins with their paired Skill, and Kiro Powers. Continue, Mastra and generic Skills retain their documented file routes. These formats do not provide identical runtime behavior. Factory and CodeBuddy packages expose the Skill without enabling unverified execution hooks. Kiro Powers are installed and updated in the IDE; CLI v3 automatically discovers IDE-installed Powers.

Updates are explicit by default. Refreshing a marketplace, updating an installed plugin, reloading the host and trusting changed hooks are separate operations. Codex hook installation and trust remain separate steps. Local-path sources may require this source repository to be updated and rebuilt before the host can load a new version. Preserve local source directories while a host references them.

Verification distinguishes static inspection, protocol tests and real host runs; unavailable operating systems or hosts are reported as Not Run. Building or preparing a release does not install plugins, change user configuration, push Git branches or publish npm packages. A prepared Git URL or npm identity is not a published endpoint until separately released and verified. Installation scope follows the host command documented in `INSTALL.md`.

Package updates and uninstallation preserve project plans and evidence. A target project adopts a PWF task state by explicitly relocating its active status entry once and linking the historical plan, without two-way synchronization.

See the installed Skill's `references/evidence.md` for source review, requirement preservation, verification and fresh-reader handoff guidance.
