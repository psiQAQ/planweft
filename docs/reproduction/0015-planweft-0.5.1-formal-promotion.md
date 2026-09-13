# REP-0015：PlanWeft 0.5.1 正式 promotion

状态：Passed；日期：2026-09-13。该记录承接 [REP-0014](0014-document-role-map.md) 的候选归档与已通过的 promotion evidence；不重写该候选阶段的范围或结果。

## 范围

- 已发布的 `planweft@0.5.1` 归档保持不变，不重新发布、不删除版本。
- 维护者在官方 npm registry 将 `latest` 指向既有的 `0.5.1`；`next` 保持指向同一版本。
- 本记录所在的最终 `master` 提交由 annotated `v0.5.1` tag 标记；未创建 GitHub Release。

## 独立 readback

| 项目 | 结果 |
| --- | --- |
| 官方 dist-tags | `next: 0.5.1`；`latest: 0.5.1`。 |
| 包身份 | `planweft@0.5.1`；官方 tarball 为 `https://registry.npmjs.org/planweft/-/planweft-0.5.1.tgz`。 |
| 完整性 | `sha512-FkcshU28V8p4l8CO98AY4ZvGzHzUiQ/CnkBMRujHQOQbQRbB5Eg+YQ7jf1GMfqUKNE76+TFEK20OKjyAXx0PJg==`。 |
| 归档 SHA-256 | `8071dee2ffe8c0500e739e17723cf307d3c29276055bbc5a8d1c860358419b28`，与 [REP-0014](0014-document-role-map.md) 和 `promotion.json` 绑定的不可变归档一致。 |
| 发布前提 | 同版本 policy、prepublication、registry 静态安装与独立 promotion review 已在候选阶段 Passed；本次仅改变 dist-tag。 |

详细 readback 附件见 [`release/evidence/0.5.1/raw/latest-promotion.md`](../../release/evidence/0.5.1/raw/latest-promotion.md)。

## Documentation Handoff

<!-- planweft-docs-status: complete -->
- Documents considered: README、CHANGELOG、发布说明、REP-0014、0.5.1 release evidence。
- Rationale / evidence: registry 的 `latest` 已在 maintainer promotion 后指向既有 `0.5.1`，本记录保留独立官方 readback；候选阶段证据保持不改写。
- Next action: 核验包含本记录的 `master` 提交后，创建并推送 annotated `v0.5.1` tag。
