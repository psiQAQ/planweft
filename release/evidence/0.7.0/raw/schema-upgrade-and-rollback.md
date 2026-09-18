# 0.7.0 schema upgrade and rollback evidence

`state upgrade` is explicit. A schema 1 store remains readable but rejects `record`, recovery apply, and checkpoint writes until the user invokes the upgrade. The upgrade:

1. acquires the single-owner lock;
2. writes `migrations/<migration-id>/store.before.json` and its hash-bound manifest;
3. preserves `store_id` and `plan_id`;
4. creates schema 2 checkpoint/migration directories and writes the upgraded store atomically;
5. validates the resulting schema and capabilities.

The P1 regression `schema 1 stores are read-only until explicit upgrade with a verified backup` passed. Checkpoint manifests retain complete before/after snapshots and an explicit resume command; unrelated edits are rejected rather than overwritten. There is no claim of a global transaction across all plan files.
