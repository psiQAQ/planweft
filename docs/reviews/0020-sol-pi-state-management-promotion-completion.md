# REV-0020: SoL-Pi 0.6.0 promotion completion review

## Result

Passed for the deterministic 0.6.0 release and post-promotion public readback. This review closes the external credential blocker recorded by REV-0019 without rewriting its historical failure evidence.

## Observed evidence

| Boundary | Result |
| --- | --- |
| `release/NPM_TOKEN` name visible without exposing its value | Passed |
| npm registry `planweft@0.6.0` version and archive identity | Passed |
| Final dist-tags `latest=0.6.0`, `next=0.6.0` | Passed |
| Registry signatures and SLSA provenance metadata | Passed |
| GitHub Release `v0.6.0` and annotated tag readback | Passed |
| Historical `E401` failure retained separately | Passed |
| Real Agent/model regression and tokens/cost | Not Run by explicit scope |

The stable readback attachment is `release/evidence/0.6.0/raw/stable-promotion-readback.md`. The candidate publication path remains Trusted Publisher/OIDC through `publish.yml`; the stable dist-tag path remains a separately scoped `NPM_TOKEN` operation through `promote-stable.yml`.

## Fixed workflow boundary

`promote-stable.yml` now fails early when `NPM_TOKEN` is absent or cannot authenticate with `npm whoami`, before spending time on registry/package gate checks. It then verifies the exact candidate archive and promotion evidence, performs the dist-tag write, and requires a final public readback.

This review is limited to source, workflow contract, registry metadata, package integrity, and public release state. It does not claim real Agent/model behavior or tokens/cost measurement.
