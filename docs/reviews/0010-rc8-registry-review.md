# RC8 registry runner independent review

Reviewed current local diff against HEAD `b60b812d5ee7fc0f85e9d04a11e09c024ad8ad72`. Reviewer changed no repository files and ran no Docker/model/network commands. This report is the only persistent review output.

## Verdict

**Changes requested: one P2 blocker for the stated complete-uninstall acceptance.** The ordinary offline suites pass; they miss a reproducible dangling-symlink false positive. No other concrete blocking defect was established.

## P2: a dangling OpenCode Skill link passes complete removal

Location: `tests/run-registry-smoke.py:222`; the pre-existing installer lane has the same check at line 370.

The post-removal check uses `Path.exists()`. A leftover `.opencode/skills/project-docs` symlink whose target has been removed returns false from `exists()`. Native Skill discovery also returns no Skill, so all removal assertions pass despite an owned component remaining in the project. The old lane's loader/Skill checks have the same blind spot.

Independent offline reproduction used `NativeFixture` from the new tests. The normal mocked native removal was followed by inserting a dangling Skill link. `direct_npm_lifecycle('opencode', NEW, None, ...)` returned:

```text
runner_status Passed
remaining_owned_skill_symlink True
exists_check False
```

This establishes a validation defect, not an observed bug in the real installer. Fix component-presence checks with `exists() or is_symlink()` (or `os.path.lexists`) and add a negative-control fixture where tools/Skill discovery are empty but the dangling link remains. Apply the same rule to the old installer lane if it continues to claim full removal.

## Other reviewed behavior

- **Pi binding:** install/upgrade/rollback/reupgrade use exact npm spec strings. Registration must be unique; real RPC command metadata ties both extension and Skill to the expected npm version, base directory and exact resource path. Full expected package bytes and distribution file sets are compared. After removal, native list and RPC commands/Skill must be absent. An RPC process terminated after a successful discovery reply is explicitly handled; this is discovery, not a completed model session.
- **OpenCode binding:** only the owned npm config entry is changed; paired Skill bytes and discovered location are verified. The fixed 1.18.22 cache lookup selects `packages/planweft@VERSION/node_modules/planweft`, verifies the exact dependency/package version and rejects fallback to retained old/unversioned caches. Successful fresh native discovery plus this pinned-layout contract support the binding. Tool discovery does not directly expose runtime sourceInfo: cache-path selection is a source-contract inference, not an independently emitted loaded-module path.
- **DSH binding:** native profile registration is unique; composed bundle file URL resolves to the selected package's DSH entry; package and Skill-tree bytes are checked. Removal requires dependency/bundle registration absence and no composed PlanWeft block. `--help` is a boot/help observation, not model-time Skill matching or tool permissions. The returned scope correctly says model discovery is separate.
- **Uninstall scope:** the checks concern registered/discoverable resources and owned project entries. They do not promise erasure of every native/package-manager cache or dependency artifact. Do not describe retained native caches as verified deleted.
- **Permissions/model claims:** no model prompt is submitted by the direct lifecycle; output explicitly uses `model_sessions: Not Run`. The OpenCode baseline permission value is preserved through removal. This does not prove normal permission approval/denial, model capability, hook behavior, or full sandbox confinement.
- **Wrapper preflight:** host/version/digest pairing, timeout, output restrictions, image-lock shape and credential-free proxy rules are checked before resource inspection, directory creation or Docker. Resource headroom precedes Docker; exact image identity precedes output creation. The wrapper provides these guarantees; the older smoke script alone is not a replacement for wrapper headroom/credential-proxy preflight.
- **Resource bounds:** execution is serial with CPU 2, memory/swap total 3 GiB, PID limit 256, /tmp tmpfs 512 MiB and an outer 1–600 second bound. RAM/disk headroom is checked before starting and between hosts. On failure/timeout, later hosts remain Not Run.
- **Owned cleanup:** a unique random container name plus `planweft.registry-run` label is checked before removal; foreign-owner labels are not deleted. Removal is rechecked. Successful, verified cases may delete only their own rebuildable npm-cache; failed/unverified evidence caches stay intact. This does not provide general filesystem or Docker cleanup.
- **Evidence binding:** wrapper freezes runner and image lock and binds worker result to requested versions/digests plus runner SHA. Cleanup failure forces the wrapper case to Failed; worker success cannot override mismatched artifact evidence.

## Actual verification

```text
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_registry_native_lifecycle.py
9 tests Passed

PYTHONDONTWRITEBYTECODE=1 python3 tests/test_registry_containers.py
9 tests Passed

Independent dangling-link negative control
Reproduced false Passed as described above
```

No model/container run was performed by this reviewer. Existing evidence was read without modification:

- `<private-evidence-root>/rc7-direct-native-registry/pi/run/summary.json`: Passed; exact rc.6 -> rc.7 -> rc.6 -> rc.7 -> remove sequence; 3884 package files checked at each selected version.
- Same run's OpenCode worker: Failed with `Native npm package is missing`; original native_channels entry remains In Progress. This is retained pre-fix evidence and does not prove the new cache-path implementation passed a real host.
- Both above used runner SHA `ad40b87b5f7cda74d7e252ff9eaa96612f91ebdd69b5667c1e0011b693d721f2`. New OpenCode/DSH real-run results were not supplied as completed evidence to this review; they remain Not Run here.

## Reviewed file SHA-256

`ff7c40b0410116d40a9ccc4c7f686bc07256ae316d9c15df819552e49bb77cbd`  tests/run-registry-smoke.py
`3f167f8d85c36bec87846b1166589ff4d22fad763d6a666149c0192f45e439e1`  tests/test_registry_native_lifecycle.py
`6ae0078428f560ba733c8ae5295c4e01871b4ad9109c64f29a54a414324db81d`  tests/run-registry-containers.py
`53a77188f51be5a0111f6b94582e55e757e99a339f2ad5225ecff71d082a5bee`  tests/test_registry_containers.py


## Follow-up: P2 closed after correction

**Final review verdict: no remaining blocker from this review.** The original false-Passed reproduction and initial findings above remain as historical evidence.

The implementation now routes both removal lanes through `verify_opencode_removed` (`tests/run-registry-smoke.py:128`). It rejects a component when either `exists()` or `is_symlink()` is true. The direct npm lane calls it at line 231; the managed installer lane calls it with `managed=True` at line 379, checking both the Skill and loader paths. The helper only inspects and raises; it does not delete the leftover link or modify configuration.

The new direct negative control actually runs the lifecycle against the fake native CLI, leaves a dangling Skill link after unpair, and now requires RuntimeError instead of Passed. It also confirms the link remains observable and unrelated permission/autoupdate values survive. The managed tests independently leave dangling Skill and loader links, require rejection, preserve the links and user configuration bytes, then verify the clean absent state succeeds.

Independent verification after the correction:

```text
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_registry_native_lifecycle.py
Ran 11 tests in 0.115s
OK (no skips)
```

This closes the previously established acceptance false positive. It does not retroactively change the original real-run results and is not a new model/container execution. Other scope limitations in the initial review remain applicable.

Corrected file SHA-256:

`f6249a8471c4ebaef76fe550662a572e5ada9bceb28533919d7e948f16e81c42`  tests/run-registry-smoke.py
`cd6a4424eb4243f267121ce2ef94394cf4bc7e2d3574604bc85d2844deca4360`  tests/test_registry_native_lifecycle.py
