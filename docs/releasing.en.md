[简体中文](releasing.md) | [English](releasing.en.md)

# Releasing PlanWeft

This page records the maintainer release process and the final 0.4.0 publication facts. See the [installation guide](installation.en.md) for user commands and [platform support](platforms.en.md) for public capability claims.

## 0.6.0 P0 state-evidence release path

The 0.6.0 path uses the versioned [`support-policy-0.6.0.json`](../release/support-policy-0.6.0.json), `release/evidence/0.6.0/`, and [`check-state-release-gate.py`](../scripts/check-state-release-gate.py). It gates deterministic offline, generated-artifact, package-install, cold-read, and review evidence. Real Agent/model behavior, tokens/cost, and real different-Agent continuation remain explicit non-blocking `Not Run` items.

The candidate workflow [35242327786](https://github.com/psiQAQ/planweft/actions/runs/35242327786) passed 362 offline Python tests and the candidate gate. The public registry reads back `planweft@0.6.0` with `next=0.6.0`, `latest=0.6.0`, and archive SHA-256 `7e913d3c43e852aaf59dbb2fc7adb3b7aa275453cf3041ec1acdebea80be9c5e`. Annotated [`v0.6.0`](https://github.com/psiQAQ/planweft/releases/tag/v0.6.0) and its GitHub Release were created and read back.

Stable npm promotion is complete: after configuring `release/NPM_TOKEN`, the public registry reads back `latest=0.6.0` and `next=0.6.0`. The earlier `E401` from [35243815030](https://github.com/psiQAQ/planweft/actions/runs/35243815030) remains preserved in `release/evidence/0.6.0/raw/stable-promotion-attempt.md` and [REV-0019](reviews/0019-sol-pi-state-management-stable-promotion-blocker.md); the successful readback is in `release/evidence/0.6.0/raw/stable-promotion-readback.md` and [REV-0020](reviews/0020-sol-pi-state-management-promotion-completion.md).

### 0.6.0 credential and fixed workflow boundary

- Candidate publication uses npm Trusted Publisher/OIDC through `publish.yml`: GitHub-hosted runner, `id-token: write`, the `release` environment, and `npm publish --tag next --provenance`; no long-lived npm publish token is required.
- Stable promotion is a separate `npm dist-tag add planweft@<version> latest` operation. The workflow therefore uses a package-scoped `NPM_TOKEN` only in the `release` environment, preflights it with `npm whoami`, then verifies the exact archive, promotion gate, dist-tag write, and public readback.
- A local `~/.npmrc` only serves commands on the local machine and does not replace the GitHub Actions secret. Never store the actual token in the repository, command-line arguments, chat, or logs.

## 0.7.0 P1 checkpoint/reducer release path

`0.7.0` uses its own [`support-policy-0.7.0.json`](../release/support-policy-0.7.0.json),
`release/evidence/0.7.0/`, and [`check-state-p1-release-gate.py`](../scripts/check-state-p1-release-gate.py).
It adds schema-2 upgrade/rollback and data protection, checkpoint before/after snapshots and recovery,
deterministic reducer quote verification, S14–S16, cold-read, fault-injection, and offline four-way
ablation evidence. Real Agent/model traffic, tokens/cost, and real different-Agent continuation remain
explicit `Not Run` items and are not release gates.

The fixed sequence is: generate one candidate with the builder on a synchronized clean `master`, run the
P1 prepublication gate, publish to `next` with Trusted Publisher/OIDC, read back the exact registry bytes
and SHA-256, update accurate promotion evidence, then use `NPM_TOKEN` in the `release` environment for
the guarded `npm dist-tag add planweft@0.7.0 latest`. Finally read back `latest=0.7.0`, `next=0.7.0`,
the tag, GitHub Release, and an isolated installation. If the version is occupied or any gate fails,
stop and preserve the evidence.

`release/NPM_TOKEN` must be an npm automation/granular token that can perform the non-interactive dist-tag
write (normally with 2FA bypass enabled). Trusted Publisher/OIDC covers `npm publish`, not the current
`npm dist-tag add`; if npm returns `EOTP`, the workflow preserves the failed attempt and leaves `latest`
unchanged.

Current status: the candidate, registry readback, `v0.7.0`, and GitHub Release passed; stable-promotion
workflow `35295422731` stopped at `npm dist-tag add` with `EOTP`, so `latest` remains `0.6.0`. The
preserved failed evidence is [`stable-promotion-attempt.md`](../release/evidence/0.7.0/raw/stable-promotion-attempt.md).

## 0.5.x static/logic release path

Each 0.5.x patch uses `release/support-policy-<version>.json`, `release/evidence/<version>/`, and
`check-document-release-gate.py` for the same version declared by `package.json`. Prepublication requires Passed rebuildable-package, offline-test,
Hook-logic, Skill/Hook-association, public-documentation, independent-source-review, and
project-files-only-cold-read records. Promotion also requires registry archive identity, temporary
static-install verification, and independent promotion review. This path never changes the frozen 0.4.0
policy or acceptance record.

The frozen 0.5.0 policy is the one filename exception: it continues to use the existing
`release/support-policy-0.5.json`; do not rewrite its policy or evidence to normalize the name.

Every Passed record names an actual attachment below the evidence JSON and its SHA-256; `package_sha256`
must equal the local npm archive passed to the gate, whose `package/package.json` must identify the same
`planweft@<version>` as the policy and evidence. The gate rejects self-references, absolute paths, `..`, escaping symlinks, missing
attachments, and digest mismatches. Prepublication checks only its own items; `--promotion` additionally
requires registry and promotion-review evidence.

### 0.5.1 formal promotion record

- Source commit: `b4a2c02bacf01ea2896f1beae5382588b5b6abd7`
- Trusted publication workflow: [34725859049](https://github.com/psiQAQ/planweft/actions/runs/34725859049)
- Official npm archive SHA-256: `8071dee2ffe8c0500e739e17723cf307d3c29276055bbc5a8d1c860358419b28`
- `next`: `0.5.1`; `latest`: `0.5.1`
- Prepublication, registry evidence, and independent reviews: Passed; attachments are in `release/evidence/0.5.1/`; an independent formal-promotion readback is in [REP-0015](reproduction/0015-planweft-0.5.1-formal-promotion.md)
- The annotated `v0.5.1` tag points at the final `master` commit containing this formal record
- GitHub Release: [v0.5.1](https://github.com/psiQAQ/planweft/releases/tag/v0.5.1), public, non-draft, non-prerelease, and with no additional build assets

The candidate-stage `next` record, policy, and attachments remain unchanged. This section only records the later maintainer-authorized dist-tag promotion, source tag, and post-tag GitHub Release.

## Frozen 0.4.0 full lifecycle (historical)

The following flow and five-host requirements are the historical schema-3 boundary for 0.4.0. They are not additional 0.5.0 gates and must not turn 0.4.0 runtime results into 0.5.0 validation.

### Pre-release checks

1. Create a clean worktree and release branch from the confirmed remote `master`. Do not copy uncommitted changes from another checkout.
2. Check the version, remote branch, latest CI, npm version availability, and dist-tags. Query them again before every external write.
3. Review public history, attachments, licenses, authors, and installation metadata. An unresolved privacy finding blocks publication.
4. Edit canonical sources and generate platform directories. Review dependency, pinned-upstream, or compiler changes separately.
5. Run build consistency, the full test suite, native lifecycles, exact-artifact checks, the authorized model acceptance set, and independent review.

```bash
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
node tests/installer.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
```

### Exact artifacts and publication order

Generate one npm tgz, `release.json`, and checksum set from the same clean commit. For a stable release, the publication workflow requires the reviewed SHA-256 as `expected_sha256`. Stop if the CI rebuild differs; do not change the expected digest to accept different bytes.

```bash
python3 scripts/prepare-native-release.py --release --output /tmp/planweft-release-new --repository-url https://github.com/psiQAQ/planweft
gh workflow run publish.yml -f expected_sha256=REVIEWED_SHA256
```

`--output` must name a new directory outside the checkout. The publication workflow uses GitHub OIDC/provenance. Do not place long-lived npm tokens in commands, chat, or logs.

Publish a stable version to `next` first. Download it from the official registry and verify bytes, SHA-256, and integrity, then complete native installation, discovery, doctor, fresh-session loading, and removal on the five core hosts. Update `latest` only after promotion evidence and independent review pass. Create the source-bound GitHub Release last.

Do not overwrite or delete a published npm version. If remote acceptance fails, keep the existing `latest` tag and failure evidence, then fix the problem in a new patch version.

### Schema 3 gate

[`release/support-policy.json`](../release/support-policy.json) classifies every host and scenario as `required`, `evidence_based`, or `experimental`. The gate calculates `release_blocking` from policy and does not trust a self-declared acceptance value.

- A `required` item must be Passed.
- Experimental Failed/Inconclusive results require an attachment and public limit ID. Not Run requires a reason.
- Fresh and reused evidence bind exact package and attachment digests. Reuse also binds source and target packages, a per-file manifest diff, affected checks, and a reviewer.
- Exact artifacts, final installation/removal, user-file protection, explicit Skill reading, and supported model workflows cannot be reused.
- Prepublication and promotion require separate independent reviews. Promotion also verifies the earlier review.
- The evidence root cannot escape the repository. Absolute paths, `..`, escaping symlinks, self-reference, and digest mismatches are rejected.

Aggregate status comes from real child scenarios. Whether an item blocks publication is separate from whether it Passed.

## 0.4.0 release record

- Source commit: `1a96dce0d25b4c92ecfc82225b94980ca37bda14`
- npm archive SHA-256: `e611338a619adabb0ba943d75460a01d83e4670dbe7d69f5d1050a1c1467c132`
- npm `latest` and `next`: `0.4.0`
- Linux, Windows, macOS, and distribution Check: Passed
- Prepublication gate, promotion gate, and independent reviews: Passed
- GitHub Release: [`v0.4.0`](https://github.com/psiQAQ/planweft/releases/tag/v0.4.0)

The only retained experimental Failed aggregate is Codex stopping. The gate-cap enabled/disabled pair uses `LIMIT-CODEX-TRACE-INCOMPLETE` because syscall attribution was incomplete. Normal session termination does not change that result.

## Historical records

RC1 through RC15 publication, failures, fixes, CI, model acceptance, and attachment bindings remain in [PLAN-0010](plans/0010-five-agent-release.md), [REP-0010](reproduction/0010-five-agent-release.md), and their checkpoint/evidence files. Those records keep their original state. This page does not repeat or rewrite them after the final 0.4.0 release.
