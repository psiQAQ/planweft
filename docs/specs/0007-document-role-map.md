# SPEC-0007：可选文档职责映射

状态：Accepted；日期：2026-09-13。需求来源：用户批准的 PlanWeft 0.5.1 实施计划。

## 目标与边界

让 `project-docs` Skill 在已授权的实质实施任务中，利用项目已有文档索引理解文档职责与候选维护位置，而不强制用户采用预设目录。映射是人类可读的导航信息；它不取代 `task_plan.md`、项目规则、批准需求或已有稳定文档。

本规格不增加 JSON 映射、缓存权威、CLI、目录迁移、固定脚手架或 Hook 状态。Hook 不读取映射；既有 Documentation Handoff marker、PWF selector、attestation、cap、stall 和宿主适配保持不变。

## 接口与验收

仅在任务命名的现有文档索引，或已存在且在授权范围内的 `docs/README.md` 中，可维护一个人类可读的 `Documentation Map` 表格：

| Role | Canonical location | Scope / update trigger | Generated from |
| --- | --- | --- | --- |

列标题和内容可使用项目语言；相对链接优先。Skill 从任务路径、适用 AGENTS、README、任务命名或已链接的 `CODEX.md`，以及该已有索引扩展读取。没有索引时继续通常的受限导航，不创建任何文件。

| 编号 | 要求 | 验收 |
| --- | --- | --- |
| DM-01 | 可选映射 | 不存在映射或索引时，Skill 不创建脚手架、不阻塞任务。 |
| DM-02 | 职责而非目录 | README、AGENTS、稳定规格/ADR、计划、证据与已选择交付物可作为角色；实际路径由项目决定。 |
| DM-03 | 受限发现 | `CODEX.md` 仅在任务指定或已读入口链接时读取；不因映射相邻目录读取配置、环境、缓存、脚本或未选择日志。 |
| DM-04 | 条件资源 | `commands/`、`.agents/skills/*/SKILL.md`、`agents/` 仅是模板或角色规格，除非宿主另行注册。 |
| DM-05 | 状态与 Hook 边界 | 映射不承担任务状态、批准或 Hook 输入；Documentation Handoff 继续只记录实际考虑与维护结果。 |

## 验证边界

0.5.1 以生成入口关联、离线夹具、构建一致性、版本化 release gate、公开文档、独立源码审查和项目文件冷读为验收。0.5.0 与 0.4.0 保持各自历史证据范围，不被本规格重写。
