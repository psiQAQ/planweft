[中文](0010-rc14-checkpoint.md) | [English](0010-rc14-checkpoint.en.md)

# RC14 publication and Claude collection checkpoint

`0.4.0-rc.14` is published to npm `next`; stable `0.4.0` is not published. Historical RC1 on `latest` is not a stable release. This is a completed checkpoint; subsequent work is tracked in the [current plan](../plans/0010-five-agent-release.md).

- Frozen source: `6e54876bf6249bb1d83514767920fdeb793f3573`.
- Exact official-registry archive: 5,462,803 bytes; SHA-256 `9ecfd09b82d118a99f7593fa3fcd948234a334ac11f7c2e06d63e446e693b85a`. SHA-512 integrity and SHA-1 also match. [npm candidate](https://www.npmjs.com/package/planweft/v/0.4.0-rc.14).
- [Three-system CI](https://github.com/psiQAQ/planweft/actions/runs/34382490295) and [OIDC publication](https://github.com/psiQAQ/planweft/actions/runs/34383018444) Passed. Publication required the CI-rebuilt archive to match this exact digest.
- The authorized direct dependency remains `toml@4.3.0`; other dependencies were not upgraded. RC14 changes the six-language adoption branches and English/Chinese local-operation examples. Their model effectiveness requires actual task evidence.

The first Windows CI failed when its default cp1252 encoding read Chinese documentation. Explicit UTF-8 input/output and a forced-ASCII subprocess counterexample fixed it; all three systems subsequently passed. The older `2c96af78` archive is excluded from publication. An initial worktree pack failed because the container could not follow its external `.git` pointer; a self-contained isolated clone replaced it. A later short-SHA fetch failed before an inadvertently started old-source pack; that artifact is also excluded. The final archive is bound to the full commit above. The first registry query used the user's default npm mirror; strict origin validation rejected it before download. Explicit official-registry selection passed without changing personal npm settings.

The Claude reminder diagnostic used published RC13 archive `793e3f2c…09bda`, not RC14. Independent review verified two turns in one process, four serial Write calls, native results matching actual files, unchanged protected records, Docker exit code 0, and private trace cleanup. **Collection Passed; attribution Incomplete; reminder deduplication Not Run.** Actual native initialization named the managed marketplace payload, while the old harness bound the version cache. Another unfinished read lacked an observed FD creation source. Neither its `fs.watch` thread name, byte count, nor an empty hooks array proves irrelevance or successful deduplication.

The harness now checks the actual loading root against the manifest, binds the native session path, and rejects linked resources or intermediate directories. Independent findings and their closure evidence are preserved. A separate seven-hook offline preflight observed PostToolUse byte counts `187, 0, 187, 0`; it had no model and cannot substitute for actual delivery acceptance. Tracing exports only bounded numbers, fixed enumerations and digests. Authenticated raw syscall traces were destroyed in private storage; the separate no-authentication/no-network diagnostic trace remains private.

The [sanitized evidence archive](evidence/0010/rc14-candidate-and-claude-trace.tar.gz) contains 115 entries, 427,682 bytes, SHA-256 `fa2f27ca2b411618b28d7a19ea1617f5104fa6b73ba98c52fc796b2e7cff3cc8`. Its manifest binds original and public bytes separately. It includes failures, frozen harnesses, project snapshots, independent reviews and CI/registry results; it excludes credentials, reconstructible installation trees and private raw traces.

Remaining mandatory work includes five-host model behavior, permissions/stopping/deduplication, maintenance and independent handoff, followed by the exact stable archive and remote lifecycle. Windows/macOS real hosts and unexecuted GUI cases remain Not Run; three-system installer CI does not prove those scenarios.
