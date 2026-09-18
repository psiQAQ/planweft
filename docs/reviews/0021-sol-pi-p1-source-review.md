# REV-0021: SoL-Pi P1 source review

## Scope and independence boundary

This is a separate static source-review pass over the P1 implementation and its release contract. It was performed after the implementation pass and before release evidence was assembled. It did not call a second Agent/model, use real Agent/model traffic, or measure tokens/cost; those dimensions remain `Not Run`.

Reviewed source and contract:

- `overlays/planweft/state/core.mjs` and `overlays/planweft/state/cli.mjs`;
- `tests/state-p1.test.mjs` and `tests/state-p1-ablation.test.mjs`;
- `scripts/build-plugin.py`, `scripts/check-state-p1-release-gate.py`, and both release workflows;
- `docs/specs/0009-sol-pi-state-checkpoints.md`, `docs/adr/0013-sol-pi-p1-checkpoint-reducer.md`, and the P1 public references.

## Findings and disposition

| ID | Review question | Finding | Disposition |
| --- | --- | --- | --- |
| F-P1-01 | Can checkpoint reduce only safe completed phases? | Phase headings and status literals are compared before/after; incomplete, pending, failed, unresolved, constraint, timeout, and similar content is protected. | Passed; regression covers retained prelude, pending phase, constraints, and status. |
| F-P1-02 | Can a checkpoint be recovered without trusting a partial write? | Before/after snapshots, manifest hashes, an `applying` state, owner lock, write-before-hash verification, conflict rejection, and explicit resume are present. | Passed; regression simulates an interrupted applying manifest and resumes it. This is not claimed as a global transaction. |
| F-P1-03 | Are schema upgrades explicit and reversible? | Schema 1 stores remain readable but reject writes. `state upgrade` preserves store identity, writes a pre-upgrade backup and migration manifest, and then enables schema 2 capabilities. | Passed; regression checks read-only behavior, backup identity, and post-upgrade recording. |
| F-P1-04 | Can the reducer invent interpretation? | Reducer output contains source facts and byte quotes only; `interpretation` is always an empty array, and quote verification re-reads the hashed Artifact. | Passed; tampered quote and unsupported binary cases are covered by the implementation contract. |
| F-P1-05 | Can `record` execute an arbitrary command? | The input schema treats command/argv as reported execution data. The implementation archives listed files and never invokes the reported command. | Passed by source inspection and existing state-evidence regression. |
| F-P1-06 | Can generated packages drift from the source? | Builder remains the only generation path; P1 runtime and reference files are included in the builder mapping. | Pending final builder `--verify` and package archive inspection; no manual `dist/**` edits. |
| F-P1-07 | Are non-measured claims separated from offline evidence? | The policy keeps real Agent/model, tokens/cost, and real different-Agent continuation as exact `Not Run` records. | Passed; no offline result is used as a substitute. |

## Decision

Passed for the deterministic P1 source boundary after final generated-output verification. The review does not authorize claims about real Agent/model behavior, tokens/cost, remote reducer behavior, or global atomicity.
