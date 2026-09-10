[简体中文](README.md) | [English](README.en.md)

> 当前安装包：**mastracode**。请选择本文对应宿主的安装章节。

# PlanWeft 0.4.0

PlanWeft 把编程 Agent 的任务计划、发现和验证结果保存在项目文件中，让后续会话可以从已确认的状态继续工作。

本目录是某一宿主的自包含安装包。请按[中文安装指南](INSTALL.md)或 [English guide](INSTALL.en.md)安装，不要只复制 `SKILL.md`，也不要把不同宿主的目录合并使用。

## 工作文件

复杂任务通常维护 `task_plan.md`、`findings.md` 和 `progress.md`。稳定知识继续放在项目已有的 specs、ADR 和 reproduction 文档中。默认恢复只读取项目文件；访问宿主会话历史需要显式操作。

## 运行边界

- 默认模式只提供提醒。autonomous/gated 必须显式启用，并受宿主能力限制。
- 项目规则、用户授权、只读要求和宿主权限始终优先。
- attestation 不能证明人工批准，完成门禁也不能证明实现正确。
- 同一会话只启用一套规划执行 hooks。
- 更新和卸载不会删除项目计划或用户文档。

0.4.0 对 Codex、Claude Code、Pi、OpenCode V1 和 DSH 的核心生命周期与保护能力提供正式支持；其他适配器和自动续跑能力为实验性。完整矩阵见仓库的[平台文档](https://github.com/psiQAQ/planweft/blob/master/docs/platforms.md)。

本包基于固定的 planning-with-files（PWF）v3.17.0，并保留其 MIT 许可和来源信息。`UPSTREAM.json` 记录固定上游版本；仓库中的开发文档记录本地扩展与生成过程。
