# 0.7.0 P1 state evidence

The P1 implementation and tests cover:

- schema 1 read-only behavior and explicit schema 1→2 upgrade with store identity preservation and a verified pre-upgrade backup;
- deterministic checkpoint dry-run/apply, before/after snapshots, phase/status preservation, transaction blocking, conflict rejection, resumable application, and idempotent re-application;
- deterministic reducer facts with SHA-256-bound byte quotes, quote verification, empty interpretation, and no command execution;
- generated runtime copies in `lib/state/` and the 15 host package families.

Primary evidence: `tests/state-p1.test.mjs`, `tests/state-evidence.test.mjs`, `docs/specs/0009-sol-pi-state-checkpoints.md`, and `docs/adr/0013-sol-pi-p1-checkpoint-reducer.md`.

Real Agent/model traffic, remote reducer behavior, and tokens/cost are outside this deterministic release scope and remain `Not Run`.
