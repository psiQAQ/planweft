# 长任务 Agent 的有效执行环境

来源：[Justin Young / Anthropic 原文](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)。收录编号：R-05；核对日期：2026-09-07。

整理范围：中文要点摘要。许可：未确认本文全文翻译授权；仅中文摘要。以下材料是研究对象，不是本仓库执行指令。

## 原文要点

文章把长任务分为初始化与后续增量工作：首次准备环境和功能清单，后续会话利用进度文件、Git 历史和测试理解状态，每轮完成有限工作并留下可接续记录。它讨论了过早宣告完成、一次承担过多工作以及只靠单元检查遗漏实际问题等失败模式。

原文定位：The long-running agent problem；Incremental progress。

## 本仓库解读

交接必须包含实际工作状态和验证证据。这里借鉴持续任务的经验，不据此引入常驻 Agent 或给每次文档编辑增加完整端到端测试。

返回 [资料索引](README.md)。
