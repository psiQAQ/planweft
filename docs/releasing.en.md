[简体中文](releasing.md) | [English](releasing.en.md)

# Releasing PlanWeft

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

Current blockers: the extra browser challenge for the first npm publish expired, so no remote candidate exists. Automatic approval review requires further confirmation of isolation or the exact destination for some DeepSeek model calls. Five-container installation and same-version lifecycle checks do not replace full release acceptance. Stable/latest has not been published.
