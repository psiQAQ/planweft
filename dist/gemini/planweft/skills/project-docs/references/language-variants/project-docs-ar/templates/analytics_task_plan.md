# Task Plan: [Analytics Project Description]

Use this file as the durable roadmap for a data analytics or exploration session. Keep phase status current as the analysis advances.

## Goal

State the analytical question or intended deliverable in one clear sentence.

[One sentence describing the analytical objective]

## Current Phase

Name the phase currently being worked on.

Phase 1

## Phases

Use only `pending`, `in_progress`, or `complete` for each status.

### Phase 1: Data Discovery

- [ ] Identify and connect to data sources
- [ ] Document schemas and field descriptions in findings.md
- [ ] Assess data quality (nulls, duplicates, outliers, date ranges)
- [ ] Estimate dataset size and query performance
- **Status:** in_progress

### Phase 2: Exploratory Analysis

- [ ] Compute summary statistics for key variables
- [ ] Visualize distributions and relationships
- [ ] Identify outliers and anomalies
- [ ] Document initial patterns in findings.md
- **Status:** pending

### Phase 3: Hypothesis Testing

- [ ] Formalize hypotheses from exploratory phase
- [ ] Select appropriate statistical tests
- [ ] Run tests and record results in findings.md
- [ ] Validate findings against holdout data or alternative methods
- **Status:** pending

### Phase 4: Synthesis & Reporting

- [ ] Summarize key findings with supporting evidence
- [ ] Create final visualizations
- [ ] Document conclusions and recommendations
- [ ] Note limitations and areas for further investigation
- **Status:** pending

## Hypotheses

Record the questions under investigation as testable hypotheses.

1. [Hypothesis to test]
2. [Hypothesis to test]

## Decisions Made

Record analytical choices, including tests, filters, exclusions, and their rationale.

| Decision | Rationale |
|----------|-----------|
|          |           |

## Errors Encountered

Record each distinct error, the attempt number, and the resolution. Change the approach before retrying a failed action.

| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |

## Notes

- Update phase status as work progresses: `pending` to `in_progress` to `complete`.
- Re-read the goal and current phase before major analytical decisions.
- Log errors promptly so failed approaches are not repeated.
- Record query results and visual evidence in findings.md.

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
