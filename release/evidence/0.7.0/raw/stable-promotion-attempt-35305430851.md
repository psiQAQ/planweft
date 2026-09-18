# 0.7.0 stable promotion retry

Workflow `35305430851` on `master@a3bf020eeba933226450024899f9258f9c8a8531` was retried after the npm account/package setting was changed to require two-factor authentication and disallow bypass 2FA tokens.

The workflow passed:

- `npm whoami` with the `release/NPM_TOKEN` secret;
- registry candidate/readback validation;
- the P1 promotion gate against the exact archive SHA-256 `ddbdc57572341aa912885102b36f8c0e13ea4e07312930380e74fbe790445745`.

It failed at the guarded command:

```text
npm dist-tag add planweft@0.7.0 latest --registry=https://registry.npmjs.org
```

npm returned `EOTP` and requested a one-time password. The setting does not make this non-interactive tag mutation usable by the existing workflow; Trusted Publisher/OIDC also does not authenticate `npm dist-tag add`. No stable tag mutation occurred. Registry readback remains `latest=0.6.0`, `next=0.7.0`.

This is a preserved Failed retry, not a Passed promotion result. No token value or OTP was recorded.
