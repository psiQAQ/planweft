# REV-0015：0.5.1 文档职责映射 promotion 证据审查

状态：**Passed（独立 promotion evidence 审查）**；日期：2026-09-13。独立 reviewer：`role_map_promotion_review` subagent。审查者只读取当前项目文件、0.5.1 policy/evidence 与 npm 官方 registry；不读取旧聊天、不采用其他 reviewer 结论、不修改文件。

## 结论

- 官方 registry 当前为 `next: 0.5.1`、`latest: 0.4.0`。
- `planweft@0.5.1` 官方归档 SHA-256 为 `8071dee2ffe8c0500e739e17723cf307d3c29276055bbc5a8d1c860358419b28`，与 prepublication `package_sha256` 一致；包内 manifest 为 `planweft@0.5.1`。
- registry identity 附件中的 dist-tag、integrity 与 SHA-256 均与当前官方 registry 一致。
- `--ignore-scripts` 静态安装附件准确记录包身份、目标资源存在性及非阻断的 `EBADENGINE` 警告；没有将它误作 Hook 或 Agent 工作流验证。
- 0.5.1 policy 的 SHA-256 与 prepublication 绑定值一致，且将 registry identity、静态安装及本审查列为 promotion 必需项。

## 边界

本审查只确认 `latest` 保持 0.4.0；不包含 promotion 到 `latest`，也不包含创建、核验或发布 Git tag。静态安装不覆盖运行时回归。
