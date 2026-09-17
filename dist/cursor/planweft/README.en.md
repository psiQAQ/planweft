[简体中文](README.md) | [English](README.en.md)

> Package: **cursor**. Use this host's installation section.

# PlanWeft 0.6.0

PlanWeft keeps a coding agent's task plan, findings, and validation record in project files so later sessions can continue from confirmed state. This directory is a self-contained package for one host.

Install the package with the [Chinese guide](INSTALL.md) or the [English guide](INSTALL.en.md). Do not copy only `SKILL.md`, and do not merge directories made for different hosts.

## What is included

| Component | Role |
| --- | --- |
| `skills/project-docs/SKILL.md` | Guides planning, investigation, implementation, verification, and document handoff |
| `skills/project-docs/references/` | Detailed rules loaded as needed |
| `skills/project-docs/scripts/` and `templates/` | Read-only helpers and task-record structures |
| Host Hooks, extensions, or commands | Connect the shared Skill to the host's lifecycle when supported |
| Host metadata | Lets the host discover the package; discovery is still subject to host trust and enablement |

## How it works

The Skill guides the agent. Hooks read state, inject context, or provide reminders only at supported and enabled host events. `task_plan.md`, `findings.md`, and `progress.md` remain in the user's project and are not owned by this package.

Installation, host discovery, current-session Skill reading, and Hook enablement are separate checks. A package directory or manifest entry does not prove that the host loaded the package or that a model read the Skill.

See the repository's [architecture guide](https://github.com/psiQAQ/planweft/blob/master/docs/architecture.en.md), [host guide](https://github.com/psiQAQ/planweft/blob/master/docs/hosts.en.md), and [documentation map](https://github.com/psiQAQ/planweft/blob/master/docs/README.md) for the product model, host boundaries, and maintainer records.

## Runtime boundaries

- Default behavior is advisory; autonomous/gated behavior requires explicit activation and host support.
- Project rules, user authorization, read-only requirements, and host permissions take precedence.
- Updates and removal do not delete project plans or user documents.
- Static package checks do not prove host loading, model reading, or task correctness.

This package retains the pinned planning-with-files (PWF) runtime and its MIT license and provenance. `UPSTREAM.json` identifies the pinned source; development and release details stay in the repository's maintainer documentation.
