[简体中文](releasing.md) | [English](releasing.en.md)

# Releasing PlanWeft

This page records the maintainer release process and the final 0.4.0 publication facts. See the [installation guide](installation.en.md) for user commands and [platform support](platforms.en.md) for public capability claims.

## Pre-release checks

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

## Exact artifacts and publication order

Generate one npm tgz, `release.json`, and checksum set from the same clean commit. For a stable release, the publication workflow requires the reviewed SHA-256 as `expected_sha256`. Stop if the CI rebuild differs; do not change the expected digest to accept different bytes.

```bash
python3 scripts/prepare-native-release.py --release --output /tmp/planweft-release-new --repository-url https://github.com/psiQAQ/planweft
gh workflow run publish.yml -f expected_sha256=REVIEWED_SHA256
```

`--output` must name a new directory outside the checkout. The publication workflow uses GitHub OIDC/provenance. Do not place long-lived npm tokens in commands, chat, or logs.

Publish a stable version to `next` first. Download it from the official registry and verify bytes, SHA-256, and integrity, then complete native installation, discovery, doctor, fresh-session loading, and removal on the five core hosts. Update `latest` only after promotion evidence and independent review pass. Create the source-bound GitHub Release last.

Do not overwrite or delete a published npm version. If remote acceptance fails, keep the existing `latest` tag and failure evidence, then fix the problem in a new patch version.

## Schema 3 gate

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
