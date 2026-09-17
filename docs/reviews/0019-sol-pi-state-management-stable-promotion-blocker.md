# REV-0019: SoL-Pi 0.6.0 stable promotion blocker

## Result

The deterministic `0.6.0` candidate is published and read back from npm as `next=0.6.0`; the annotated Git tag and GitHub Release are also read back. Stable promotion is not complete because the authorized npm dist-tag write path has no credential.

## Observed evidence

- Local `npm dist-tag add` returned `E401 Unauthorized`.
- Guarded GitHub workflow `35243815030` passed the registry candidate checks and promotion gate, then returned `401 Unauthorized` with an empty `NODE_AUTH_TOKEN` for the dist-tag PUT.
- Repository and `release` environment secret listings contain no usable `NPM_TOKEN`.
- `latest` remains `0.5.1`; no existing stable version was overwritten.

## Boundary

This is an external authorization blocker, not a source, test, package, or registry-identity failure. Real Agent/model regression and tokens/cost remain intentionally `Not Run` and are not needed to resolve this blocker.
