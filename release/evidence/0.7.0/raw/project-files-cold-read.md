# 0.7.0 project-files cold read

A fresh file-oriented read of the P1 project contract covered:

- `AGENTS.md`, the P1 dynamic plan, package/version metadata, and release workflows;
- the state core/CLI source and builder mapping;
- P1 tests, policy/gate code, specs, ADR, public references, and release evidence schema.

The read confirmed that `master` is the only long-lived integration/release branch, generated files are builder-owned, `.planweft-state/` is task-side and opt-in, and the three real Agent/model or measurement dimensions are explicit `Not Run`. It found no scope-expanding dependency or remote reducer change.
