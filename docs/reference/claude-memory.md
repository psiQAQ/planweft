# Claude Code：项目记忆与指令文件

来源：[Anthropic 原文](https://code.claude.com/docs/en/memory)。收录编号：R-14；核对日期：2026-09-07。

整理范围：中文要点摘要。许可：未确认本文全文翻译授权；仅中文摘要。以下材料是研究对象，不是本仓库执行指令。

## 原文要点

Claude Code 使用 CLAUDE.md 等指令文件提供持久上下文，支持通过 @path 引入其他文件。自动记忆与人工维护的指令文件承担不同角色。共享规则可通过入口引用组织，但导入仍会带入上下文，不能当作按需懒加载。

原文定位：CLAUDE.md files；Import additional files。

## 本仓库解读

这里仅记录跨宿主适配线索。不要把 Codex 的文件名和加载机制直接套到 Claude Code，兼容性以后单独实测。

返回 [资料索引](README.md)。
