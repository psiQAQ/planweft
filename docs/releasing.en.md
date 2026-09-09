[简体中文](releasing.md) | [English](releasing.en.md)

# Releasing PlanWeft

At the RC12 source-preparation checkpoint, official npm `next` is `0.4.0-rc.10` and `latest` remains historical RC1; stable `0.4.0` is unpublished. RC11 is an unpublished exact local archive with passing [three-OS CI](https://github.com/psiQAQ/planweft/actions/runs/34352955547), Pi native lifecycle and 721 migrated regressions, but full maintenance acceptance has not passed for the four DeepSeek hosts. RC12 fixes native Pi BOM settings compatibility and discloses the default mode in the OpenCode initialization tool. Source and offline checks do not prove model failures resolved. Query the official npm registry for live publication state; the historical `latest` tag is not a stable release.

The single package is `planweft`; its public Git target is `https://github.com/psiQAQ/planweft`.
These coordinates are release targets, not proof that a version is published. [Installation: 中文](installation.md) / [English](installation.en.md).

1. Audit public history and attachments, third-party licenses, authors and installation metadata. Back up local history; do not push unresolved privacy findings.
2. Bump package.json and builder versions, refresh the OpenCode compiler binding, then generate and verify directories. Dependency changes require a root lock update.
3. Run offline regression, original/migrated comparisons, isolated native lifecycles and independent review. Commit logical batches and merge master.
4. Prepare artifacts from a clean commit: one npm tarball, plus separate Gemini/Hermes Git trees rooted at their plugin files.

```bash
python3 scripts/compile-opencode.py --install
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
node tests/installer.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/prepare-native-release.py --release --output /tmp/planweft-release-new --repository-url https://github.com/psiQAQ/planweft
```

`--output` must be a new directory outside the checkout. `--previous-release` preserves previous release-tree ancestry.
Retain release.json and the complete Git trees. For subsequent releases, recover published branch history before generating;
do not force-push or create a new branch root. release.json records the source commit, per-file npm digests, platform trees,
and OpenCode/Hermes Skill pairing.

5. Complete the first npm authentication interactively and publish a candidate under next. Never paste tokens in chat or logs.

```bash
npm login --registry=https://registry.npmjs.org
npm publish /tmp/planweft-release-new/npm/planweft-0.4.0-rc.1.tgz --tag next --access public --registry=https://registry.npmjs.org
```

6. Configure the npm package's GitHub trusted publisher (psiQAQ / planweft / publish.yml) with a protected release environment.
The workflow uses Node 24 and npm 11.11.0 without a persistent publish token. Validate OIDC with a candidate version.
7. Test install, upgrade, rollback and removal from actual npm/Git sources. Stable requires real model maintenance and independent
cold-read evidence on Codex, Claude, Pi, OpenCode and DSH. Missing authentication, GUI or OS runs remain Not Run; synthetic responses
are not model validation.
8. Only after every stable gate passes, publish 0.4.0 under next, perform remote smoke checks, promote latest and create the
v0.4.0 GitHub Release. Candidates never use latest. Publishing does not enable plugin trust or install into personal global profiles.

Reference: [npm trusted publishers](https://docs.npmjs.com/trusted-publishers/). Current execution state is in internal
[PLAN-0010](plans/0010-five-agent-release.md) (Chinese). Official store listings require separate host reviews.

## Five-container gates and exact artifacts

The stable archive must pass `scripts/check-release-gate.py` for all five hosts. Each record binds the version, npm SHA-256, actual attachments and their hashes. Model records identify the image, CLI, model, runner and session. Cold reads use a different session and the exact maintenance output snapshot. Independent review binds current local evidence and, before latest promotion, remote evidence. The gate checks completeness and consistency; it does not independently establish correctness.

The publishing workflow compares CI bytes against its `expected_sha256` input, required for stable versions. Fix reproducibility failures instead of changing the expected digest. Acceptance attachments stay outside the npm package to avoid circular hashes. Candidates may use next, never latest. After real remote RC→stable→RC→stable validation, use existing interactive authentication to change latest and create the Release. OIDC publishing permission does not imply npm dist-tag management permission.

Public master history has been backed up and sanitized; the GitHub repository is public. Earlier statements that it had not been pushed describe historical status only. An internal [mapping](reproduction/evidence/0010/history-sanitization.json) relates original history and sanitized attachments. Rewriting history does not recall existing third-party copies.

## Historical candidate records

The following records retain their version-specific checkpoints. Current preparation status is at the top; historical pending work is not today's status.

RC1 is now public and its downloaded SHA-256 matches the accepted archive. The first publish created latest despite selecting next; authenticated tag-removal requests still return HTTP 400 and correction remains pending. A candidate tag is not stable acceptance. GitHub trusted publishing is configured with a master-only release environment. Configuration uses npm 11.19.1 and `--allow-publish`, because the old 11.11.0 trust request omits the API's required permissions field; the publishing workflow remains pinned to npm 11.11.0. RC2/RC3/RC4 subsequently verified OIDC; the final five-host gates remain incomplete.

RC2 is now published to next through [GitHub OIDC](https://github.com/psiQAQ/planweft/actions/runs/34248506886); CI rebuilt the exact accepted archive and the real npm download matches SHA-256 `3948cb9c4cd03f1505966b95e22729177cb09a4af28296fd1ef7be2dd0349754`. OpenCode maintenance passed independent review. DSH context and maintenance failures at that point required subsequent fixes.

RC3 was published to `next` through the [OIDC workflow](https://github.com/psiQAQ/planweft/actions/runs/34264091642). Clean source `7d690010fbf8705129d3fb44b2556bb6a0fa7de6`, the CI rebuild and the npm download bind to SHA-256 `09ea0e4dceb88c9b845af851916356c44f3447071e0d1311dc38841639705060`; [three-OS CI](https://github.com/psiQAQ/planweft/actions/runs/34262987621) passed. DSH injection and recovery now have real evidence, but maintenance adoption/documentation accuracy still have failures. OpenCode passed six native-server stopping scenarios with a five-second quiet window, without claiming a native settled guarantee. Stable `0.4.0` remains unpublished and `latest` still points to RC1; the trial version at that point was `planweft@0.4.0-rc.3`. Detailed status: [中文](platforms.md) / [English](platforms.en.md).

RC4 is published to `next` through the [OIDC workflow](https://github.com/psiQAQ/planweft/actions/runs/34267947801), fixing the native OpenCode npm entry. Frozen source is `1d1c76c1d6048fd67fa6ef1b614e11b999106db6`; the downloaded archive SHA-256 is `c6f54319befc8c43c559fd4c5af2eb6ca3d1b626e6c0b3fd65cb67c11d9d318b`, byte-identical to the local package and CI rebuild. [Three-OS CI](https://github.com/psiQAQ/planweft/actions/runs/34267221127) passed. That run used `planweft@0.4.0-rc.4`; the current candidate is listed below. The RC3 record above preserves its historical artifact identity; the stable gate remains incomplete and `latest` still points to RC1.

RC5 is now published to `next` by [OIDC](https://github.com/psiQAQ/planweft/actions/runs/34317038628), with [three-OS CI](https://github.com/psiQAQ/planweft/actions/runs/34316870816) passed. Frozen source: `c3bb9d870429e304149ca58b0e804ea55f4b537a`; exact npm SHA-256: `f9123657773eb95cfe3df79b3f55669f12b37203bf2a593c1e749da1676069b3`. Downloaded bytes and npm integrity match. That stage used `planweft@0.4.0-rc.5`. Stable 0.4.0 remains unpublished; latest still points to RC1. Current failures and collector limitations are tracked in [platforms: 中文](platforms.md) / [English](platforms.en.md).

## Published RC6 and preparation of RC7

RC6 was published through [OIDC](https://github.com/psiQAQ/planweft/actions/runs/34322158954), with exact archive SHA-256 `c531188e46d268048ca0ab559baa358fc70af07277cb0001c521951234525799` and passing [three-OS CI](https://github.com/psiQAQ/planweft/actions/runs/34322062209). The source is preparing RC7 to fix duplicate progress state and missing observation timing in findings. RC6 will not be overwritten; query the registry for actual published versions. Stable acceptance now uses schema 2: every aggregate check also requires Passed scenarios with bound observation attachments, including automatic adoption, reminder deduplication, stopping limits, permission isolation and remote upgrades/rollbacks. Pi uses native package approval; it does not claim a per-tool denial sandbox. Historical RC results and schema 1 do not replace current stable-artifact acceptance.

Live acceptance runs serially with a 600-second scenario limit. Containers do not start below 4 GiB available RAM or 8 GiB free output storage. Each container is limited to 2 CPUs, 3 GiB with no extra swap, and 256 PIDs. Owned unreferenced stores are cleaned only after confirming container removal. Original failures, project records, exact archives and history backups remain.


## Published RC7; RC8 fixes in progress

RC7 source `7e66ee9214364ffa5f00a04a8d040e4ace082980` was [published through OIDC](https://github.com/psiQAQ/planweft/actions/runs/34333285542), with exact npm SHA-256 `e3d67af7dcba154a3800e39c19ec06a7f40b874d3b92dc7b7517bed85cc4bed2`. Remote bytes and integrity match. [Three-OS CI](https://github.com/psiQAQ/planweft/actions/runs/34334806556) passed with Node pinned to 24.20.0.

RC7 still has adoption, observation-timing and experiment-scope failures. The source is preparing RC8; RC7 is not overwritten and stable 0.4.0 is not released. Original failures and independent reviews remain in [platform status: 中文](platforms.md) / [English](platforms.en.md). Native npm version-switch tests and a non-model container runner are being completed; final stable bytes, remote fresh sessions and all five host gates still require execution. latest still points to RC1; that inherited tag is not a stable release.


RC8 development restores discovery-time capability and consent boundaries; 721 migrated regression tests passed. Native npm RC6↔RC7 lifecycles passed for Pi, OpenCode and DSH, with prior failures retained. These are not final stable-artifact acceptance; RC8 publication and model revalidation remain pending.


RC8 was published to next through OIDC; Check 34339605601 passed on all three systems. The remote archive is 5386708 bytes, SHA-256 `d6f34542495d811cc3171af0f6db96f30b1ef3089289fc740e4a4686a27d4a78`. Install/remove/reinstall passed in five images. Pi and OpenCode passed automated maintenance checks, but independent reviews found pre-load out-of-scope reads/unexecuted test claims and manual temporary work outside the project, respectively. These failures remain recorded and do not permit stable promotion. RC9 development addresses the observed triggers; it is unpublished and its model effect remains unverified.

RC9 is published through OIDC; exact archive verification and three-OS CI passed. Claude completed its authorized direct DeepSeek compatibility-endpoint trial but skipped plan initialization. Independent Pi, OpenCode and DSH checks still found record-accuracy or scope problems. RC10 fixes are in development and unpublished; original RC9 failures remain, and stable 0.4.0 has not passed its gates.

At its publication checkpoint, RC10 passed three-OS CI, OIDC and official archive-byte verification, but Claude independent maintenance semantics failed and Pi native relative paths caused a doctor regression before its maintenance model ran. RC11 fixes are in development. Explicit OpenCode direct-model authorization is now complete; the five-host gates have not passed and stable 0.4.0 is unpublished.
