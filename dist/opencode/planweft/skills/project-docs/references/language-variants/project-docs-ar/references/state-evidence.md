# PlanWeft state evidence

The optional task-side evidence store is separate from the installer store:
`.planweft-state/` belongs below the selected PWF plan directory, while
`.planweft/` remains installer-owned.

Initialize it explicitly:

```text
planweft state init
```

Then pass a JSON data file to `record`:

```text
planweft state record --input evidence.json
planweft state verify --receipt <receipt-id>
planweft state recall --artifact <sha256> --start-byte 0 --length 120
planweft state doctor
planweft state recover --transaction <id> --dry-run
planweft state upgrade
planweft state checkpoint --dry-run
planweft state reduce --artifact <sha256>
planweft state quote-verify --input reduced.json
```

`record` never executes a command string from the JSON. It records the
observed result separately from interpretation, criteria, and freshness, stores
regular files by streaming and rechecking SHA-256, and rejects unsupported
capture/origin values, paths outside the authorized project, symlinks, changed
markdown baselines, and idempotency-key conflicts. Recovery is read-only until
`--apply` is explicitly supplied. The helper is local and offline; it does not
replace host tools, enable remote reducers, or change the default advisory
Hook. `doctor` reports damaged or missing references, lock state, budgets and
local-only evidence without writing.

P1 stores use schema 2. A schema 1 store from PlanWeft 0.6.x remains readable,
but all writes are refused until the owner explicitly runs `planweft state
upgrade`; the upgrade keeps a verified pre-upgrade backup. Checkpoints are
opt-in: dry-run is read-only, while apply writes complete before/after
snapshots and can resume with `--checkpoint <id>`. The active plan retains its
goal prelude, phase headings, statuses and unresolved constraints; detailed
completed-phase text is recoverable from the checkpoint.

The local reducer recognizes only finite text and JSON result fields. Every
fact includes a byte-range quote tied to its source artifact, and
`quote-verify` rechecks those bytes. Unsupported, incomplete or contradictory
input remains unknown/limited. Interpretation is separate and this release
does not call a remote model or execute recorded commands.
