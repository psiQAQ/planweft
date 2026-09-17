# 0.6.0 stable dist-tag promotion readback

- Readback date: 2026-09-18.
- The public npm registry reports `latest=0.6.0` and `next=0.6.0` for `planweft`.
- `planweft@0.6.0` remains present with shasum `69580c61b38e12a4d8a8c0312e6c29af599e088a`, SHA-512 integrity `sha512-AWq9R83vB570Ti6v8/PL7zZkvirKfHMe/7APJPrCjrROZzJB0LBHX8gqHYtqeebcs/uB57nq7506wNLKNnS16A==`, two registry signatures, and a SLSA provenance attestation.
- The `release` environment exposes the secret name `NPM_TOKEN`; its value was not read or recorded. The resulting registry state proves that a valid authorized dist-tag write occurred, but the available GitHub run history contains only the earlier failed promotion run, so this evidence does not attribute the successful write to an unobserved workflow run.
- The earlier `E401` attempt remains preserved in `stable-promotion-attempt.md`; this file records only the subsequent successful public readback.
- Result: Passed for the stable dist-tag and package-integrity readback. Real Agent/model behavior and tokens/cost remain `Not Run` by explicit scope.
