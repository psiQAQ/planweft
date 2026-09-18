# ADR-0013: add recoverable P1 checkpoints and a local deterministic reducer

- Status: Accepted for 0.7.0 implementation
- Date: 2026-09-18
- Related spec: [0009-sol-pi-state-checkpoints](../specs/0009-sol-pi-state-checkpoints.md)

## Decision

Keep the P0 task store and add schema 2 with explicit migration. A checkpoint
is a local, opt-in snapshot of all three PWF files. It is proposed in read-only
dry-run mode and applied under the existing single-owner lock after before-hash
and semantic-preservation checks. Complete phase details may be shortened only
when the full source is recoverable from the checkpoint; unresolved and
protected state stays active.

Implement reduction as a standard-library deterministic parser over verified
artifacts. Facts carry exact byte-range quotes. Interpretation is separate and
never upgrades source provenance or turns a quote into a root-cause claim.

## Alternatives rejected

1. Native host context compaction: it is outside the task store's authorization
   and has no stable byte-recovery contract.
2. A remote/model reducer: it introduces data classification, budget, privacy
   and untrusted-output obligations that are outside this release.
3. Rewriting a schema-1 store in place during ordinary `record`: migration
   could surprise existing tasks, so upgrade is explicit and backed up.
4. Deleting completed phase content: it breaks PWF counts and makes recovery
   dependent on an unverified summary; only a recoverable snapshot permits the
   active-document reduction.

## Consequences

P1 adds local disk usage for checkpoint snapshots and a second explicit write
action. It provides deterministic source-linked reduction and recovery, but
does not claim global atomicity, universal semantic understanding or model
cost savings. Offline fixtures can validate correctness; real Agent/model
and token/cost measurements remain `Not Run` by policy.
