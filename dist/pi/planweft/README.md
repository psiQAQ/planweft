[简体中文](README.md) | [English](README.en.md)

> 当前安装包：**pi**。请选择本文对应宿主的安装章节。

# PlanWeft 0.5.1

PlanWeft 将编程 Agent 的任务计划、调查发现和验证记录保存在项目文件中，让后续会话可以从已确认的状态继续工作。本目录是面向单个宿主的自包含安装包。

请使用[中文安装指南](INSTALL.md)或 [English guide](INSTALL.en.md)安装。不要只复制 `SKILL.md`，也不要合并为不同宿主构建的目录。

## 包含什么

| 组件 | 作用 |
| --- | --- |
| `skills/project-docs/SKILL.md` | 指导计划、调查、实施、验证和文档交接 |
| `skills/project-docs/references/` | 按需读取的详细规则 |
| `skills/project-docs/scripts/` 和 `templates/` | 只读辅助脚本和任务记录结构 |
| 宿主 Hook、扩展或命令 | 在宿主支持时把共享 Skill 接入生命周期 |
| 宿主元数据 | 帮助宿主发现包；发现仍受宿主信任和启用规则约束 |

## 如何工作

Skill 指导 Agent。Hook 只在宿主支持且启用的事件中读取状态、注入上下文或提供提醒。`task_plan.md`、`findings.md` 和 `progress.md` 始终保存在用户项目中，不属于本包。

安装、宿主发现、当前会话读取 Skill 和 Hook 启用是不同的检查。包目录或 manifest 存在，不证明宿主已经加载包，也不证明模型已经读取 Skill。

产品运行模型见仓库的[架构说明](https://github.com/psiQAQ/planweft/blob/master/docs/architecture.md)，宿主边界见[宿主说明](https://github.com/psiQAQ/planweft/blob/master/docs/hosts.md)，维护者资料见[文档导航](https://github.com/psiQAQ/planweft/blob/master/docs/README.md)。

## 运行边界

- 默认行为是 advisory；autonomous/gated 需要显式启用并依赖宿主能力。
- 项目规则、用户授权、只读要求和宿主权限优先。
- 更新和卸载不会删除项目计划或用户文档。
- 静态包检查不证明宿主加载、模型读取或任务正确。

本包保留固定的 planning-with-files（PWF）运行时及其 MIT 许可和来源信息。`UPSTREAM.json` 记录固定上游；开发和发布细节保留在仓库维护者文档中。
