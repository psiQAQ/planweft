[简体中文](README.md) | [English](README.en.md)

> 当前安装包：**copilot**。请选择本文对应宿主的安装章节。

# PlanWeft 0.5.1

PlanWeft 把编程 Agent 的任务计划、发现和验证结果保存在项目文件中，让后续会话可以从已确认的状态继续工作。本目录是当前版本的某一宿主自包含安装包。

请按[中文安装指南](INSTALL.md)或 [English guide](INSTALL.en.md)安装，不要只复制 `SKILL.md`，也不要把不同宿主的目录合并使用。

## 工作文件

复杂任务通常维护 `task_plan.md`、`findings.md` 和 `progress.md`。稳定知识继续放在项目已有的 specs、ADR 和 reproduction 文档中。默认恢复只读取项目文件；访问宿主会话历史需要显式操作。

## 运行边界

- 默认模式只提供提醒。autonomous/gated 必须显式启用，并受宿主能力限制。
- 项目规则、用户授权、只读要求和宿主权限始终优先。
- attestation 不能证明人工批准，完成门禁也不能证明实现正确。
- 同一会话只启用一套规划执行 hooks。
- 更新和卸载不会删除项目计划或用户文档。

安装记录、宿主发现、当前会话读取 Skill 和实际 Hook 启用是不同的检查点；安装诊断不能替代当前会话中的实际读取确认。

0.4.0 的五宿主正式验收及实验性边界仍绑定其准确 npm 归档，不会因本包升级而自动延伸。当前支持范围和已知限制见仓库的[平台文档](https://github.com/psiQAQ/planweft/blob/master/docs/platforms.md)。

本包基于固定的 planning-with-files（PWF）v3.17.0，并保留其 MIT 许可和来源信息。`UPSTREAM.json` 记录固定上游版本；仓库中的开发文档记录本地扩展与生成过程。
