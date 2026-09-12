# ADR-0010：以 Skill 维护文档交接，以 Hook 验证确定性状态

状态：Accepted；日期：2026-09-13；需求：[SPEC-0006](../specs/0006-skill-hook-document-handoff.md)。

## 决定

采用一个嵌入所选 `task_plan.md` 的 HTML marker 作为文档交接接口。`project-docs` Skill 负责受限发现、语义判断和已授权的文档更新；Hook 仅读取 marker，并在 PWF 已经决定 gated continuation 时报告 pending 文档交接。

该接口不使用 PWF 状态 token，缺失或异常一律保守为 pending。原门禁的 selector、attestation、cap、stall 和宿主能力保持唯一实现；文档检查器不写项目文件，不解析 Markdown 中的命令。

## 取舍

不采用新 CLI/映射文件/状态服务：它们会引入重复状态和人工操作流程，且本需求没有证明其必要性。保留现有 `pw-*` 控制以避免破坏兼容性，但将其定位为显式排障工具。

不采用自动归档移动：活动 PLAN_ID 目录、相对链接和历史证据的安全迁移尚无复现需求。Skill 可以在有明确授权时更新原位关闭记录或最小归档索引。

ADR-0004、ADR-0005 和 ADR-0006 保留其历史决定与证据；本 ADR 只增加 0.5.0 的文档交接行为，不宣称替代 0.4.0 的真实宿主验证。
