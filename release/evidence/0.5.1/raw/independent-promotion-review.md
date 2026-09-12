# 0.5.1 独立 promotion evidence 审查

状态：Passed。日期：2026-09-13。

独立 reviewer `role_map_promotion_review` 只读取当前项目文件、0.5.1 policy/evidence 和 npm 官方 registry，不读取旧聊天、不采用其他 reviewer 结论、不修改文件。完整审查记录见 [REV-0015](../../../../docs/reviews/0015-document-role-map-promotion-review.md)。

- 官方 registry 为 `next: 0.5.1`、`latest: 0.4.0`；官方 tarball SHA-256 与 prepublication `package_sha256` 一致。
- registry identity 的 dist-tag、integrity、SHA-256 和静态安装附件均与实际观察一致。
- `--ignore-scripts` 静态安装未被误写成 Hook 或 Agent 工作流验证；`EBADENGINE` 为非阻断警告，安装退出码为 0。
- 本审查不授权或执行 `latest` promotion，不创建或核验 Git tag。
