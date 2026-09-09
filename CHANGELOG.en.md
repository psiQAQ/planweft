[简体中文](CHANGELOG.md) | [English](CHANGELOG.en.md)

# Changelog

## 0.4.0-rc.5 (in development)

- Fix resource paths for Stop, plan selection and SessionStart in the Codex plugin distribution; preserve the upstream standalone layout.
- Add independently copied package tests for gating, recursion, cap, stall, opt-out and invalid plan binding. Real-host verification of the new exact candidate remains pending.

## 0.4.0-rc.4

- Add root npm main and ./server entries for the existing compiled OpenCode V1 plugin, fixing silent omission by the native npm resolver.
- Preserve the RC3 npm failure; validate a new exact archive and remote version without replacing published bytes.

## 0.4.0-rc.3

- DSH hooks use sandbox-writable private temporary snapshots, host session binding and bounded per-turn reminder state. Permissions and Stop payloads remain native.
- Unplanned DSH implementation tasks receive the same conditional Skill reminder as OpenCode. Broken state and explicit bindings remain fail-closed.
- RC2 was published through GitHub OIDC with an exact matching npm archive; its OpenCode maintenance trial passed. DSH model failures remain recorded until a new archive passes.

## 0.4.0-rc.2

- OpenCode now reminds authorized multi-step tasks to load project-docs when no plan exists; simple/read-only tasks remain outside initialization.

- Anchor the DSH profile bundle entry to its own patch and require an actual boot check.
- Allow a version-matched Skill alongside an OpenCode npm plugin, while rejecting duplicate runtimes and mismatched versions.
- Add five-host containers, exact-artifact gates, public-history sanitization and three-OS installer CI. Stable requires all five hosts.
- RC1 is public; retain its model failures and the distinction between registration and actual loading in the evidence.

## 0.4.0-rc.1 (2026-09-08, candidate)

- Renamed to PlanWeft; project-docs and the PWF state protocol remain.
- One npm package, 15 platform directories and six marketplaces.
- Explicit-scope installer with exact versions, links/copies, modification protection and lifecycle receipts.
- Stable release requires live acceptance on four core hosts. Historical 0.3.0 evidence does not replace current validation.

- Added DeepSeek Harness native profile bundles, the official hook bridge and Skill-only installation, with isolated Linux native lifecycle validation.
