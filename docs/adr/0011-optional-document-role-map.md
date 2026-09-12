# ADR-0011：使用可选人类可读的文档职责映射

状态：Accepted；日期：2026-09-13；需求：[SPEC-0007](../specs/0007-document-role-map.md)。

## 决定

采用存在于已有文档索引中的 Markdown `Documentation Map` 作为可选导航约定。Skill 在任务授权范围内将其视为文档候选提示；没有映射时沿用任务路径、AGENTS、README 和已有链接的受限导航。映射不由 Hook、helper 或 parser 消费。

`AGENTS.md` 保持项目规则的默认入口。`CODEX.md` 仅在任务显式指定或已有入口链接时作为补充指南读取。README、稳定需求/决定、计划、证据与已选择交付物各自保留原位置和所有权。

## 取舍

不采用固定目录模板：现有项目的 `DESIGN.md`、memory-bank、架构文档或其他布局仍可使用，迁移不证明采用成功。

不采用 JSON、缓存或新 CLI：它们会重复计划/批准状态并要求人工维护；本需求只需人类可读导航。`commands/`、项目本地 Skill 目录与 Agent 角色文件不因存在就视为已被宿主注册。配置、环境、脚本、可再生成上下文和未选择日志不进入例行发现。

ADR-0010 的单一交接 marker 与 Hook 边界不变；本 ADR 只增加 0.5.1 的 Skill 导航能力。
