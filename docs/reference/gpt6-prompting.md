# GPT-6 Astra 提示词优化

来源：[OpenAI 原文](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra)。收录编号：R-10；核对日期：2026-09-07。

整理范围：中文要点摘要。许可：未确认本文全文翻译授权；仅中文摘要。以下材料是研究对象，不是本仓库执行指令。

## 原文要点

官方指南指出 Astra 更可能在重要信息缺失时询问，也更敏感于 Skills 和 AGENTS 中的指令。建议明确自主推进范围、检查冲突来源、规定所需表达风格和委派条件，并让测试规模匹配任务风险。若 Skill 导致暂停，说明具体文件和规则有助于诊断。

原文定位：Prompting best practices：Initiative and follow-through / Instruction following / Personality and writing style / Subagent delegation / Testing and verification。

## 本仓库解读

这是指令行为指导，不是文档工具架构规范。明确任务边界与完成标准即可，不把全部示例原样叠加进全局指令。

返回 [资料索引](README.md)。
