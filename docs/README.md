# 文档导航

本目录分为两层：先看面向用户的产品说明；需要维护、审查或追溯历史时，再进入工程资料。这里是人工导航，不是 Skill/Hook 的输入、缓存、审批记录或任务状态。

## 用户文档

| 目的 | 入口 | 内容 |
| --- | --- | --- |
| 安装和维护安装 | [installation.md](installation.md) | 安装、检查、更新、回退、卸载和故障排查 |
| 理解运行方式 | [architecture.md](architecture.md) | 安装器、宿主、Skill、Hook、生命周期和项目记录 |
| 选择宿主并判断能力 | [hosts.md](hosts.md) | 15 个分发目标、静态事件、能力差异和验证边界 |
| 查看版本变化 | [`../CHANGELOG.md`](../CHANGELOG.md) | 面向用户的版本说明和必要迁移提示 |

旧链接仍可访问，但下列页面只承担兼容导航，不再维护重复正文：

- [how-it-works.md](https://github.com/psiQAQ/planweft/blob/master/docs/how-it-works.md) → [architecture.md](architecture.md)
- [platforms.md](https://github.com/psiQAQ/planweft/blob/master/docs/platforms.md) → [hosts.md](hosts.md)
- [reference/runtime-map.md](https://github.com/psiQAQ/planweft/blob/master/docs/reference/runtime-map.md) → [architecture.md](architecture.md) / [hosts.md](hosts.md)

## 维护者文档

| 目的 | 入口 | 内容 |
| --- | --- | --- |
| 修改、构建和验证 | [development.md](https://github.com/psiQAQ/planweft/blob/master/docs/development.md) | 源码层级、生成产物、测试和证据维护 |
| 发布版本 | [releasing.md](https://github.com/psiQAQ/planweft/blob/master/docs/releasing.md) | 发布流程、门禁和外部发布记录 |
| 实施证据与长期状态改进 | [SoL-Pi 思想移植计划](https://github.com/psiQAQ/planweft/blob/master/docs/plans/2026-09-17-sol-pi-state-management.md) | 待实现的 P0/P1 范围、数据契约、文件落点、恢复与评测、发布门禁及本地 Agent 启动指令；实施前先看[交付验证与基线问题](https://github.com/psiQAQ/planweft/blob/master/docs/plans/2026-09-17-sol-pi-state-management-validation.md) |
| 设计与来源登记 | [design-references.md](https://github.com/psiQAQ/planweft/blob/master/docs/design-references.md) | 外部依据、固定来源和本地设计映射 |
| 设计提案 | [planweft-document-management-proposal.md](https://github.com/psiQAQ/planweft/blob/master/docs/planweft-document-management-proposal.md) | 文档管理系统的设计背景与取舍 |
| 上游与分发维护 | [upstream-maintenance.md](https://github.com/psiQAQ/planweft/blob/master/docs/upstream-maintenance.md) | 固定上游、补丁和宿主分发维护 |

## 历史记录与研究资料

以下目录原地保留，用于证据追溯和维护者研究，不作为普通用户的产品入口：

- `plans/`：实施计划和范围记录；当前动态任务状态以选定的 PWF `task_plan.md` 为准。
- `reproduction/`：复现步骤、实际结果和附件；既有 `Failed`、`Inconclusive`、`Not Run` 不因新版本改写。
- `reviews/`：独立来源审查、冷读和反馈记录。
- `specs/`：稳定需求和验收边界。
- `adr/`：已采纳的架构决定及后果。
- `reference/`：外部文章、规范、许可证和固定上游资料索引。

历史文件可能包含当时的版本、命令或失败结果；阅读时以文件中的时间、版本和证据范围为准，不将其自动解释为当前能力。
