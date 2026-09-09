# Resolve installed resources and keep manual scratch in scope

[English](local-operations.md) | [简体中文](local-operations.zh.md)

Use these examples only for an authorized operation. Read-only tasks do not create scratch directories. Replace each argument with the location already supplied by the host or the authorized project; do not discover it through settings, receipts or a whole-filesystem search.

## Resolve the host-listed Skill once

A relative symlink target is relative to the link's parent, not the project's cwd. Resolve the actual `SKILL.md` before locating its sibling `scripts`, `references` or `templates`. With Python available:

```python
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding="utf-8")

skill = Path(sys.argv[1]).resolve(strict=True)
if not skill.is_file() or skill.name != "SKILL.md":
    raise ValueError("Expected the host-listed SKILL.md")
print(skill.parent)
```

Pass the host-listed Skill file as the first argument. Use the returned directory as `<installed Skill>` in the documented helper commands; keep the helper's cwd at the authorized project. This reads the supplied path, not host configuration. A missing or unexpected path is an error to diagnose from the provided location, not permission to search unrelated files. Use the platform's equivalent link resolution when Python is unavailable.

## Allocate manual scratch inside the authorized project

For an authorized manual reproduction or counterfactual check, make the allocation and cleanup part of that same check. With Python available:

```python
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding="utf-8")
import tempfile

project = Path(sys.argv[1]).resolve(strict=True)
if not project.is_dir():
    raise ValueError("Expected the authorized project directory")
with tempfile.TemporaryDirectory(prefix=".pw-scratch-", dir=project) as directory:
    scratch = Path(directory).resolve(strict=True)
    print("manual scratch:", scratch.relative_to(project))
    # Run the authorized manual check here, using scratch for every output.
```

Pass the authorized project directory as the first argument. Record the actual relative scratch path and result with the check; the context manager removes only the directory it created, including on an exception. This example does not itself perform a verification. Do not use an unowned fixed `/tmp` path or change the whole agent process's `TMPDIR`: host-private temporary data must remain separate. Existing test-framework temporary files and controller-owned fixtures are separate observations; do not infer their location from a manual check or change approved tests merely to claim scope coverage.

## Inspect only named planning variables when needed

The resolver normally consumes its documented settings itself. If diagnosing a binding requires inspecting values, choose the exact needed names from that helper’s documentation and look each one up directly. For example:

```python
import json
import os
import sys
sys.stdout.reconfigure(encoding="utf-8")

needed = ("PLAN_ID", "PWF_PLAN_ROOT", "PLANNING_DISABLED")
print(json.dumps({key: os.getenv(key) for key in needed}, ensure_ascii=False))
```

Remove unneeded names; add a documented `PWF_*` name only for the operation being diagnosed. `null` means unset and differs from an empty value. Do not enumerate the environment with `env`, `printenv`, `set` or `os.environ.items()` and then filter it: filtering the output does not avoid the initial enumeration. This is a task-level lookup rule, not process environment isolation; Python and the host still inherit their normal environment. The example writes no project records. See Python [os.getenv](https://docs.python.org/3/library/os.html#os.getenv).

Sources: Python documents [Path.resolve](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve) for canonical link resolution and [TemporaryDirectory](https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryDirectory) for explicit parent placement and context-manager cleanup. These APIs do not establish the task's authorization or prove that a model will follow the examples.
