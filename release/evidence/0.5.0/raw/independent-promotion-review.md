# 0.5.0 独立 promotion 审查

日期：2026-09-13。独立审查者复核 registry metadata、预发布 evidence 和受信任发布工作流。
最终结论为 Passed：`next` 指向 `planweft@0.5.0`，官方归档 SHA-256 与预发布摘要一致，
policy SHA、版本、必需检查集、附件摘要和 `release_blocking: false` 均匹配；
GitHub Actions `34707596498` 在 `master@0e1f5de` 成功完成。

审查曾发现静态安装未显式限定官方 registry。该证据已改为在 Node.js 24.20.0 临时目录中
使用 `https://registry.npmjs.org` 安装，并独立复核包身份、Skill marker 与 helper 布局，
该缺口现已解除。`latest` 保持原值，等待维护者认证后的明确 promotion 操作。
