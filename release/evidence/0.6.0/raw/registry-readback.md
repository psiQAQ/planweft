# 0.6.0 registry readback

- Final metadata readback reports `version=0.6.0`.
- Before stable promotion, `dist-tags` read back as `latest=0.5.1` and `next=0.6.0`.
- The initial readback observed npm's documented asynchronous processing window: metadata appeared before the tarball attachment. A cache-busted public tarball readback then returned HTTP success and the exact archive bytes.
- Downloaded registry archive: `planweft-0.6.0.tgz`
- Downloaded bytes: `6182515`
- Downloaded SHA-256: `7e913d3c43e852aaf59dbb2fc7adb3b7aa275453cf3041ec1acdebea80be9c5e`
- Computed SHA-512 integrity: `sha512-AWq9R83vB570Ti6v8/PL7zZkvirKfHMe/7APJPrCjrROZzJB0LBHX8gqHYtqeebcs/uB57nq7506wNLKNnS16A==`
- Isolated install from the downloaded archive reported `planweft@0.6.0`; `planweft state --help` exposed `init`, `record`, `verify`, `recall`, `doctor`, and `recover --dry-run`.

The local `check-state-release-gate.py` pre-publication gate passed against the registry-downloaded archive, confirming that the public artifact still satisfies the P0 identity and evidence contract.

## Post-promotion readback

- After the stable dist-tag write, the public registry reports `latest=0.6.0` and `next=0.6.0`.
- The package metadata still reports the same version, archive shasum, SHA-512 integrity, registry signatures, and SLSA provenance attestation.
- The successful end state is independently recorded in `stable-promotion-readback.md`; the earlier `latest=0.5.1` state and `E401` failure remain historical evidence in their original attachments.
