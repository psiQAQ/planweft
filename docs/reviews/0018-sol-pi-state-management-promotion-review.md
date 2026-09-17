# REV-0018: SoL-Pi 0.6.0 promotion review

## Scope

This review covers only deterministic source, generated artifact, npm registry, tag, release, and isolated-install evidence for `0.6.0`. It does not call a second Agent/model, use real Agent/model traffic, or measure tokens/cost.

## Evidence reviewed

- Candidate workflow `35242327786` on `master@5c23fa3`, with 362 offline Python tests and package gates Passed.
- Public package metadata for `planweft@0.6.0`: `next=0.6.0`, `latest=0.5.1` before stable promotion.
- Registry tarball: 6,182,515 bytes, SHA-256 `7e913d3c43e852aaf59dbb2fc7adb3b7aa275453cf3041ec1acdebea80be9c5e`, and matching SHA-512 integrity.
- Isolated install from the public tarball and state CLI help readback.
- Annotated `v0.6.0` and GitHub Release readback, both resolving to commit `5c23fa3686ca7666b227c6f8cc691f864d0d5921`.

## Decision

Passed for deterministic P0 promotion. The artifact, registry identity, and release lineage agree. The stable npm promotion is authorized within this evidence boundary; real Agent/model behavior and tokens/cost remain `Not Run`.
