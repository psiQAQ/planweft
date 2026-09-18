# SoL-Pi P1 checkpoints and deterministic reducer

## Scope

P1 extends the optional `.planweft-state/` task store from P0 with explicit
schema-2 upgrade, recoverable checkpoints and a local deterministic reducer.
It does not replace host tools, change advisory Hooks, execute receipt command
strings, add remote model calls or provide a global transaction guarantee.

## Checkpoint contract

`checkpoint --dry-run` is read-only. `checkpoint --apply` stores complete
before/after snapshots for the three PWF files and applies only a candidate
that preserves the Goal prelude, Phase headings, status literals, unfinished
work, blockers, constraints and evidence references. An incomplete application
is resumable by checkpoint ID; a changed target is a conflict. A candidate that
does not reduce active bytes is reported as `not_worthwhile` and is not applied.

## Reducer contract

The reducer recognizes finite text/JSON result fields and returns source facts,
not model explanations. Each fact has a quote tied to an artifact SHA-256 and
byte range. Quote verification is a separate operation. Failure, skip, timeout,
collection error and partial coverage signals are retained; unsupported or
incomplete sources remain `unknown` or `limited`.

## Upgrade and protection

Schema-1 stores are readable but write-protected until explicit `state upgrade`.
Upgrade preserves store identity, writes a verified pre-upgrade backup and
enables only the P1 local capabilities. Unknown schemas are rejected. Task
stores remain separate from installer state and are never removed by package
upgrade or uninstall.

## Validation boundary

S14–S16, fixed-seed interruption/restart cases, cold-read evidence and offline
four-way ablation are required for P1/R1. Real Agent/model traffic, tokens/cost
and real different-Agent continuation remain `Not Run` unless separately
authorized.
