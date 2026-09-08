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

- Authorized work and constraints: [scope and boundaries]
- Success criteria and requirement source: [observable result and exact reference]
- Verification evidence: [progress entry or reproduction record; actual Passed, Failed or Not Run]
- Stable design records: [affected specification or ADR, only if needed]
- Plan owner and worker record locations: [owner and assigned records, when using multiple agents]

## Handoff evidence

Keep the current next action in `## Next Step` above, rather than duplicating a live task list here.

- Remaining blocker or approval decision: [concrete missing input, or none]
- Independent evidence review: [record and disposition, or Not Run with reason]
- Fresh-reader check: [record and discrepancy resolution, or Not Run with reason]
- Existing plan migration: [old status entry now points here, when the target project adopts this workflow; otherwise not applicable]

Attestation records bytes, not approval. Checked phases or a gate decision do not prove that acceptance criteria passed.
