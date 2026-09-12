# Changelog

## 0.5.1 (published to `next`; `latest` promotion and tag await maintainer authentication)

- Added the optional, human-readable `Documentation Map`: an existing documentation index can record roles, actual locations, update triggers, and generated sources without migration, scaffolding, or machine state.
- `project-docs` navigates from task paths, AGENTS, README, bounded CODEX guidance, and an existing documentation index; templates, role descriptions, and output folders are not automatically treated as active or authoritative.
- The release gate and trusted publishing workflow now bind the same exact `0.5.x` policy, evidence, and npm archive while retaining 0.5.0 and 0.4.0 records.

## 0.5.0 (published to `next`; `latest` promotion awaits maintainer authentication)

- Added the `task_plan.md` document-handoff marker: `project-docs` makes the authorized documentation decision and Hooks only read and remind.
- When explicit gated mode and the original PWF gate both pass, a pending handoff only refines that block reason; selector, attestation, cap, and stall behavior are unchanged.
- 0.5.0 uses static/logic checks, independent source review, and cold reading. Frozen 0.4.0 evidence is not transferred to this release.

## 0.4.0 (2026-09-10)

- Published one `planweft` npm package and installer CLI for Codex, Claude Code, Pi, OpenCode V1, DSH, and ten experimental platform adapters.
- Pinned planning-with-files v3.17.0 while retaining its three-file planning protocol, named plans, attestation, ledgers, disable controls, and bounded continuation.
- Added selective project-document maintenance, design-evidence checks, independent review, and cold-read handoff rules.
- Accepted exact artifacts, installation, update, rollback, removal, reinstallation, project isolation, user-file protection, duplicate-source checks, and explicit Skill reading on five core hosts.
- Made Codex explicit maintenance followed by independent cold read a supported workflow. Pi explicit/automatic comparisons are evidence-rated under frozen conditions.
- Added the schema 3 release gate and `release/support-policy.json`, preserving the meaning of Failed, Inconclusive, and Not Run.
- Promoted the same immutable archive from `next` to `latest` after remote acceptance. The 0.4.0 npm archive SHA-256 is `e611338a619adabb0ba943d75460a01d83e4670dbe7d69f5d1050a1c1467c132`.

Known limitation: autonomous/gated behavior and model workflows outside the supported baseline remain experimental. The Codex gate-cap enabled/disabled pair is Failed because syscall attribution was incomplete; its limit ID is `LIMIT-CODEX-TRACE-INCOMPLETE`.

## Prerelease history

Versions 0.4.0-rc.1 through rc.15 tested OIDC publishing, deterministic builds, five-host lifecycles, model maintenance, cold reading, and release gates. Candidate failures and later fixes were not rewritten as stable-release results. Per-candidate state, commands, and attachments remain in [PLAN-0010](docs/plans/0010-five-agent-release.md), [REP-0010](docs/reproduction/0010-five-agent-release.md), and their checkpoint/evidence files.
