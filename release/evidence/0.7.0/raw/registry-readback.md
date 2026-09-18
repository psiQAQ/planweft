# 0.7.0 registry readback

Fresh metadata readback from `https://registry.npmjs.org/planweft` returned:

```json
{"dist-tags":{"latest":"0.6.0","next":"0.7.0"},"version":"0.7.0","archive_sha256":"ddbdc57572341aa912885102b36f8c0e13ea4e07312930380e74fbe790445745","bytes":6707526}
```

The 0.7.0 version record contains the npm shasum, SHA-512 integrity, two registry signatures, and the provenance statement published by the trusted GitHub workflow. Stable promotion was not inferred from candidate publication: `latest` still read back as `0.6.0` before the guarded promotion.
