# REV-0014：0.5.1 文档职责映射项目文件冷读

状态：**Passed（项目文件冷读）**；日期：2026-09-13。独立 reviewer：`role_map_cold_read` subagent。审查者只接收项目文件快照，不读取旧聊天、主 Agent 的实施计划或发布凭据。

## 范围与方法

冷读 [SPEC-0007](../specs/0007-document-role-map.md)、[ADR-0011](../adr/0011-optional-document-role-map.md)、[PLAN-0012](../plans/0012-document-role-map.md)、[REP-0014](../reproduction/0014-document-role-map.md)、本导航页、分发的 `documentation-map.md`、版本化 policy 与选中的 `task_plan.md`。检查目标、职责边界、历史验证范围、Not Run 表述和下一步是否能仅从项目文件恢复。

## 结论

- 目标与边界可恢复：Documentation Map 只是在已有索引中的人工导航，不迁移目录、不解析为计划状态、不扩张授权，也不是 Hook 输入。
- 职责可恢复：README 是公开入口，AGENTS 是规则，spec/ADR/REP 分别保留需求、决定和实际证据；动态状态仍只在选中的 PWF `task_plan.md`。
- 分发文件和来源 reference 一致；Skill 入口只在已授权的长期文档维护工作中按受限导航读取它。
- `next` candidate 是后续步骤，`latest` promotion 和 `v0.5.1` tag 均不在本次范围内。

## 发现与处理

| 发现 | 处理 | 结果 |
| --- | --- | --- |
| 根 README 使用“0.5.0 验证范围”，易把历史范围误读为 0.5.1 已验收 | 改为 0.5.x 版本化门禁，并将 0.4.0 明确为历史证据 | Passed |
| 选中的 task plan 与静态 PLAN-0012 阶段不一致 | task plan 改为 Testing & Verification，PLAN-0012 将实现阶段标为 complete | Passed |
| REP-0014 没有区分已执行的局部检查、先前失败与正式 acceptance | REP 在最终验证前保留 In Progress；实际结果和 release evidence 在检查完成后回填 | Pending final evidence |
| `docs/README.md` 仅列职责，未展示可选映射 | 在任务已命名的既有索引中加入表格；表格不复制动态状态 | Passed |

## 限制

本审查不运行构建、测试、发布或 registry 安装，也不替代源码审查；它只能确认项目文件的可读性、边界陈述和待执行限制。正式结果以 [REP-0014](../reproduction/0014-document-role-map.md) 和 `release/evidence/0.5.1/` 的哈希绑定附件为准。
