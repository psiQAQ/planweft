---
description: Show the active planweft plan (id, mode, attestation, current phase, phase counts)
disable-model-invocation: true
---

Follow project-docs scope rules: read-only requests and host plan mode do not initialize or update project files. Resolve the task-owned plan first; never create a competing root plan.

Call the `pw_status` tool and present the result as one compact block: plan id, mode, attested yes or no, current phase, phases complete / total with the in_progress count, and any nested-project conflicts it reports. Do not modify any file.
