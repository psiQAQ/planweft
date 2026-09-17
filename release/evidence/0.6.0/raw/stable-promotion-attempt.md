# 0.6.0 stable dist-tag promotion attempt

- Candidate and promotion evidence were Passed before this attempt.
- Existing registry state before the write: `latest=0.5.1`, `next=0.6.0`.
- Local attempt: `npm dist-tag add planweft@0.6.0 latest --registry=https://registry.npmjs.org` returned `E401 Unauthorized`.
- Guarded GitHub attempt: workflow `35243815030` passed registry identity/readback and the promotion gate, then returned `401 Unauthorized` for `PUT https://registry.npmjs.org/-/package/planweft/dist-tags/latest`.
- Workflow log shows `NODE_AUTH_TOKEN` empty because the `release` environment has no `NPM_TOKEN` secret. GitHub trusted publishing's OIDC path successfully publishes packages but does not authorize a separate dist-tag mutation.
- Post-failure state: `latest=0.5.1`; no stable tag change, package overwrite, or destructive rollback was performed.

This is retained as a release-blocking credential/evidence record. The guarded promotion workflow is ready to rerun after an npm automation/access token with dist-tag write permission is configured in the `release` environment.
