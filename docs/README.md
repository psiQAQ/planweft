# 文档导航

本目录按职责组织，而不是按任务复制状态。以下为可选、人工可读的 Documentation Map；它只描述现有职责，不是解析器输入、缓存或任务状态。项目没有索引时不要求创建。

| 职责 | 实际位置 | 适用范围 / 更新触发条件 | 生成来源 |
| --- | --- | --- | --- |
| 公开项目入口 | [`../README.md`](../README.md) | 公开能力、安装或版本入口变化 | 维护者编辑 |
| 项目规则 | [`../AGENTS.md`](../AGENTS.md) | 协作、验证或发布约定变化 | 维护者编辑 |
| 稳定需求 | [specs](specs/) | 已接受的需求或验收边界变化 | 需求与评审记录 |
| 架构决定 | [adr](adr/) | 已采纳取舍或后果变化 | 决策记录 |
| 实施计划 | [plans](plans/) | 跨步骤实施范围变化；动态任务状态以选中的 PWF `task_plan.md` 为准 | 计划记录 |
| 验证证据 | [reproduction](reproduction/) 与 [`../release/evidence/`](../release/evidence/) | 可复现检查或版本化发布结果形成后 | 实际检查与发布记录 |
| 独立审查 | [reviews](reviews/) | 依据审查或项目文件冷读完成后 | 独立审查记录 |
| 设计依据 | [design-references.md](design-references.md) 与 [planweft-document-management-proposal.md](planweft-document-management-proposal.md) | 来源、覆盖范围或新增机制变化 | 研究台账与原始提案 |

`commands/`、项目内 Skill 与 agent 描述只在任务或已有链接明确指向时作为模板或角色说明读取；它们不会因出现在目录中而成为已注册能力。配置、环境文件、自动执行脚本、可重建缓存和未选择日志不在此映射的权威文档范围内。

活动任务状态只由其选中的 `task_plan.md` 承担。不要在此索引复制阶段、下一步或批准状态。
