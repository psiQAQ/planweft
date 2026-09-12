## Scope and acceptance evidence

Keep only fields useful to this task. Link existing approved requirements instead of copying them into a second specification. This selected plan is the single dynamic task-status source.

- Scope source: keep authorized targets, prohibited reads/writes and verification limits with their actual instruction sources in the existing Goal section within the first 30 lines; do not duplicate live boundaries here.
- Success criteria and requirement source: [observable result and exact reference]
- Verification evidence: [progress entry or reproduction record; actual Passed, Failed or Not Run]
- Stable design records: [affected specification or ADR, only if needed]
- Plan owner and worker record locations: [owner and assigned records, when using multiple agents]

## Handoff evidence

Keep the current next action in `## Next Step` above, rather than duplicating a live task list here.

- Remaining blocker or approval decision: [concrete missing input, or none]
- Independent evidence review: [record and disposition, or Not Run with reason]
- Fresh-reader check: [record and discrepancy resolution, or Not Run with reason]
- Active-plan relocation: not supported; record an in-place closure or explicitly authorized archive-index update only when applicable

Attestation records bytes, not approval. Checked phases or a gate decision do not prove that acceptance criteria passed.

## Documentation Handoff

<!-- planweft-docs-status: pending -->

- Documents considered: [affected existing documents, or none]
- Rationale / evidence: [why documentation is needed or not required]
- Next action: [authorized update, verification, or closure action]

The marker has exactly one value: `pending`, `not_required`, or `complete`. It is a
read-only Hook input and not a second task status. Missing, duplicate or malformed
markers remain pending; do not set `complete` before the actual documentation result
is recorded.
