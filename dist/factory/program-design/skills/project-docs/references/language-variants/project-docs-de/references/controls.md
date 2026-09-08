# Explicit controls

On Codex and other skill-only routes, invoke `$project-docs` with an operation
from this table. These are explicit operations of the main Skill, not additional
automatically selected Skills. Locate helpers beside the installed `SKILL.md`;
use `.ps1` counterparts on Windows where supplied. Native plugin routes register
their own supported subset of the same `pd-` names.

| Operation | Action |
| --- | --- |
| `pd-plan`, `pd-start`, `pd-pwf` | Resolve task ownership, then use `scripts/init-session.sh` with a descriptive task name if authorized and missing; retain its printed `PLAN_ID` |
| `pd-status`, `pd-plan-status`, `pd-pwf-status` | Read the selected task's three files and run `scripts/check-complete.sh` for advisory phase counts |
| `pd-plan-attest` | Use `scripts/attest-plan.sh`; `--show` reads the digest and `--clear` removes it only when requested |
| `pd-plan-doctor` | Use `scripts/plan-doctor.sh`; distinguish filesystem evidence from actual host hook activation |
| `pd-plan-ar`, `pd-plan-de`, `pd-plan-es`, `pd-plan-zh`, `pd-plan-zht` | Use the requested bundled language variant when available, retaining the same scope and state rules |
| `pd-plan-execute` | Pi's native explicit session/plan activation; other hosts must not invent this command |
| `pd-plan-goal`, `pd-plan-loop` | Use the current host's goal or scheduled continuation feature only when explicitly requested and available; otherwise report Not Run rather than starting a shell loop |

OpenCode exposes `pd_init`, `pd_status` and `pd_check` through its native adapter.
PWF mode flags and state selectors retain their original meaning. A completed
phase count is not an assertion that tests passed. Do not run any modifying
control during a read-only request. Do not change the parent host's plan pin by
setting an environment variable only in a tool subprocess.
