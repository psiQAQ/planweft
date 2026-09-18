# PlanWeft checkpoints and deterministic reduction

Checkpoint is an opt-in task-side operation. It is not native host context
compaction and it never runs a command recorded in a receipt.

```text
planweft state checkpoint --dry-run
planweft state checkpoint --apply
planweft state checkpoint --checkpoint <id> --apply
```

`--dry-run` calculates a candidate without writing. `--apply` first stores the
complete `task_plan.md`, `findings.md` and `progress.md` before/after images,
then replaces only safely reducible completed phase details. The candidate
must preserve the plan prelude, phase headings, status literals, unfinished
phases and protected constraints. If a target changed, an incomplete
transaction exists, or the candidate is not smaller, the operation stops.

If a process stops during apply, the checkpoint remains in the task store.
Run `planweft state checkpoint --checkpoint <id> --apply` to resume. Unrelated
manual edits are conflicts and are never overwritten. Checkpoint snapshots are
local and remain protected by the task store's ignore policy.

The P1 reducer is deterministic and local:

```text
planweft state reduce --artifact <sha256> --json > reduced.json
planweft state quote-verify --input reduced.json --json
```

It extracts recognized test counts, failure/timeout/error lines and known JSON
fields. Each fact carries an artifact hash, byte range, line numbers and the
exact UTF-8 quote. Unsupported or incomplete input is reported as unknown or
limited. Facts do not become explanations; interpretation is a separate field,
and this helper has no remote model or command-execution path.
