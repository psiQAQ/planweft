# Optional Documentation Map

Use this reference only when an authorized implementation needs to identify or
maintain long-term project documentation. It describes a human-readable
navigation aid; it is not a schema, parser input, cache, task-state source, or
approval record.

## Location and shape

Keep one map in an existing document index named by the task, or in an existing
`docs/README.md`. Do not create either file merely to satisfy this convention.
When the user explicitly authorizes navigation work, add the map to that named
document rather than moving existing records.

Use the project's language and a short Markdown table with these meanings:

| Role | Canonical location | Scope / update trigger | Generated from |
| --- | --- | --- | --- |
| User guide | `README.md` | Public behavior or quick-start changes | Manual |
| Project rules | `AGENTS.md` | Only through the project's instruction process | Manual |
| Design decision | `docs/adr/` | A significant approved choice changes | Manual |
| Verification evidence | `docs/reproduction/` | A check is actually run or corrected | Manual |
| Generated report | `output/reports/summary.md` | Selected as a delivery or evidence item | `scripts/report.py` |

Locations are relative links where possible. A map may use different role names
or locations; existing project conventions remain authoritative.

## Role boundaries

- `README.md` explains the project and points to durable entrypoints. Do not
  copy task logs into it.
- `AGENTS.md` holds applicable project rules. A linked or task-named `CODEX.md`
  may supplement usage guidance, but it does not replace those rules.
- Existing specifications, ADRs and reproduction records retain requirements,
  decisions and execution evidence. The selected PWF plan retains live task
  state.
- `commands/`, `.agents/skills/*/SKILL.md`, and `agents/` can describe
  templates or roles. They are not registered commands, installed Skills, or
  running agents unless the relevant host has separately configured them.
- Generated deliverables may be listed when they are selected for delivery or
  evidence. Logs and regenerable context data stay out of routine context and
  do not become an independent source of authority.

## Safety and maintenance

Follow only rows relevant to the authorized task. A map does not expand read or
write permission, authorize scripts, reveal environment values, or make a
configuration file part of the task. If an affected document has no listed
owner, record the candidate and rationale in the Documentation Handoff, then
request the missing scope decision instead of inventing a new authority.
