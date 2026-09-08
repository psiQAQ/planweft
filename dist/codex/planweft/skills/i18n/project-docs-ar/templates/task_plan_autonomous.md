# Task Plan: [Brief Description]

Use this file as the durable roadmap for a long-running, autonomous, gated, or multi-agent task. Keep its goal, next step, and phase status current throughout the run.

## Runtime Behavior

- **Mode source:** The `.mode` file next to this plan selects legacy, autonomous, or gated behavior. Text in this plan does not select the mode.
- **Gate authority:** The executable gate reads `.mode`, phase state, Stop hook state, the stop block cap, and ledger progress.
- **Command boundary:** The gate never executes commands declared in this plan. Any task assignment, dependency, acceptance command, or model choice written here is descriptive only and is not a gate input.
- **Attestation:** Autonomous and gated initialization attest this file. Re-attest after an intentional edit so hooks can inject the approved version.
- **Coordination:** Keep one orchestrator responsible for plan status. Workers should report results through their own ledgers or findings instead of editing this file concurrently.

## Goal

State the intended end result in one clear sentence.

[One sentence describing the end state]

## Next Step

Record the single action that should happen next. Update it whenever the active phase or immediate action changes.

[The single next action. Update whenever phase status changes.]

## Current Phase

Name the phase currently being worked on.

Phase 1

## Phases

Break the task into three to seven verifiable phases. Use only `pending`, `in_progress`, or `complete` for each status and update the value when work advances. In gated mode, an `in_progress` phase is one of the gate inputs.

### Phase 1: Requirements & Discovery

- [ ] Understand user intent
- [ ] Identify constraints and requirements
- [ ] Document findings in findings.md
- **Status:** in_progress

### Phase 2: Planning & Structure

- [ ] Define technical approach
- [ ] Create project structure if needed
- [ ] Document decisions with rationale
- **Status:** pending

### Phase 3: Implementation

- [ ] Execute the plan step by step
- [ ] Write code to files before executing
- [ ] Test incrementally
- **Status:** pending

### Phase 4: Testing & Verification

- [ ] Verify all requirements met
- [ ] Document test results in progress.md
- [ ] Fix any issues found
- **Status:** pending

### Phase 5: Delivery

- [ ] Review all output files
- [ ] Ensure deliverables are complete
- [ ] Deliver to user
- **Status:** pending

## Key Questions

Record important questions and replace them with answers as they are resolved.

1. [Question to answer]
2. [Question to answer]

## Decisions Made

Record significant choices and the reason for each one.

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
- Re-read the goal and next step before major decisions.
- Log errors promptly so failed approaches are not repeated.
- Keep plan edits serialized when multiple agents are active.

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
