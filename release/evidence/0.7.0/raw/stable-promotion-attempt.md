# 0.7.0 stable promotion attempt

Workflow `35295422731` on `master@5d21474` passed:

- `npm whoami` with `release/NPM_TOKEN`;
- registry candidate/readback validation;
- the P1 promotion gate against the exact registry archive;
- candidate/tag/release identity checks.

It stopped at the guarded command:

```text
npm dist-tag add planweft@0.7.0 latest --registry=https://registry.npmjs.org
```

npm returned `EOTP` and requested a one-time password. The secret is valid for identity readback but is not an automation token permitted to perform this non-interactive dist-tag mutation. No stable tag mutation occurred: registry readback remained `latest=0.6.0`, `next=0.7.0`.

This is a preserved Failed attempt, not a Passed promotion result. Replace `release/NPM_TOKEN` with an npm automation/granular token configured to bypass 2FA for this package, then rerun the same workflow with SHA-256 `ddbdc57572341aa912885102b36f8c0e13ea4e07312930380e74fbe790445745`.
