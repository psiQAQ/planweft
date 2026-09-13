# PlanWeft 0.5.1 `latest` promotion readback

日期：2026-09-13。此附件补充记录维护者完成 dist-tag promotion 后的只读官方 registry 查询；它不修改已通过的 candidate policy、evidence JSON 或其附件摘要。

## 查询结果

```text
latest: 0.5.1
next: 0.5.1
```

```json
{
  "version": "0.5.1",
  "dist.integrity": "sha512-FkcshU28V8p4l8CO98AY4ZvGzHzUiQ/CnkBMRujHQOQbQRbB5Eg+YQ7jf1GMfqUKNE76+TFEK20OKjyAXx0PJg==",
  "dist.tarball": "https://registry.npmjs.org/planweft/-/planweft-0.5.1.tgz"
}
```

官方 tarball SHA-256 为 `8071dee2ffe8c0500e739e17723cf307d3c29276055bbc5a8d1c860358419b28`，与 prepublication 及 promotion gate 的 `package_sha256` 一致。
