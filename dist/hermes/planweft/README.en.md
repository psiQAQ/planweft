[简体中文](README.md) | [English](README.en.md)

> Package: **hermes**. Use this host's installation section.

# PlanWeft 0.4.0

PlanWeft keeps a coding agent's task plan, findings, and validation results in project files so later sessions can continue from confirmed state.

This directory is a self-contained package for one host. Follow the [中文安装指南](INSTALL.md) or [English guide](INSTALL.en.md). Do not copy only `SKILL.md`, and do not merge directories made for different hosts.

## Working files

Complex tasks normally maintain `task_plan.md`, `findings.md`, and `progress.md`. Durable knowledge stays in the project's existing specs, ADRs, and reproduction documents. Default recovery reads project files only; access to host session history is explicit.

## Runtime boundaries

- Default behavior is advisory. Autonomous/gated behavior requires explicit activation and depends on the host.
- Project rules, user authorization, read-only requirements, and host permissions take precedence.
- Attestation does not prove human approval, and a completion gate does not prove correctness.
- Enable only one planning hook implementation in a session.
- Updates and removal do not delete project plans or user documents.

Version 0.4.0 supports the core lifecycle and protection contract on Codex, Claude Code, Pi, OpenCode V1, and DSH. Other adapters and automatic continuation remain experimental. See the repository's [platform documentation](https://github.com/psiQAQ/planweft/blob/master/docs/platforms.en.md) for the full matrix.

This package uses a pinned planning-with-files (PWF) v3.17.0 runtime and retains its MIT license and provenance. `UPSTREAM.json` identifies the pinned source; repository development documentation records local extensions and generation.
