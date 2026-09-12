# SPEC-0006：Skill/Hook 文档交接

状态：Accepted；日期：2026-09-13。需求来源：用户明确批准的 PlanWeft 0.5.0 实施计划。

## 目标与边界

在固定 PWF v3.17.0 协议上，让 `project-docs` Skill 在已授权的实质实施任务中发现相关项目文档、完成必要维护并留下可恢复的交接判断。Hook 只读取该判断、提示模型和在既有显式 gated 条件已满足时细化阻断原因。

本规格不增加面向用户的文档 CLI、JSON 映射、数据库、缓存权威、第二动态状态、自动批准、自动归档移动或证据删除。既有 `pw-*` 控制保留为兼容与排障入口，不是日常维护前提。

## 接口与验收

选中的 `task_plan.md` 仅有一个以下章节及 marker：

```md
## Documentation Handoff
<!-- planweft-docs-status: pending -->
- Documents considered: …
- Rationale / evidence: …
- Next action: …
```

marker 只可为 `pending`、`not_required`、`complete`。缺失、重复、错位或非法值按 `pending` 处理；PWF 的 `### Phase`、`**Status:**`、PLAN_ID、PWF_PLAN_ROOT 和三文件协议不变。

| 编号 | 要求 | 验收 |
| --- | --- | --- |
| DH-01 | Skill-first 判断 | 从任务路径、AGENTS/README 和相关链接/实现关系扩展读取；不全仓扫描或读取宿主设置、聊天和敏感文件。 |
| DH-02 | 有授权的最小维护 | Skill 只在用户与项目规则许可时修改已有稳定文档；不得为满足流程自动创建导航/固定脚手架，批准需求、活动计划目录和唯一证据不得自动改写、移动或删除。 |
| DH-03 | 默认无阻断 | advisory、禁用、只读和无 Stop 能力宿主不因交接状态阻断。 |
| DH-04 | 显式门禁兼容 | 原 PWF 已通过选择、attestation、in-progress、cap 与 stall 条件时，pending 仅细化该次 block 原因；不另建计数或续跑机制。 |
| DH-05 | 可分发与可检查 | 所有生成 Skill 说明同一接口；含门禁的包装携带私有只读检查器；离线测试覆盖标记、选择、禁用和门禁边界。 |

## 验证边界

0.5.0 只将构建、脚本逻辑、资源关联、安装包静态 smoke、独立源码审查和无旧聊天冷读作为发布证据。Docker、五 Agent 运行时、真实宿主和真实模型行为不运行、不作为此版本门禁；0.4.0 的历史证据保持其原始适用范围，不转写为 0.5.0 结果。
