# Codex Skills：结构、发现与使用

来源：[OpenAI 原文](https://learn.chatgpt.com/docs/build-skills)。收录编号：R-12；核对日期：2026-09-07。

整理范围：中文要点摘要。许可：未确认本文全文翻译授权；仅中文摘要。以下材料是研究对象，不是本仓库执行指令。

## 原文要点

Skill 以含 name 和 description 的 SKILL.md 为入口，可带脚本、参考资料和资源。宿主支持显式调用，也可根据描述选择匹配的 Skill。详细内容在使用时读取；本地发现与通过插件分发属于不同环节。

原文定位：How ChatGPT and Codex use skills；Where Codex loads local skills；Distribute skills with plugins。

可选 agents/openai.yaml 的 allow_implicit_invocation 默认 true；false 禁止隐式匹配，仍可显式调用。原文 `Best practices` 建议先使用指令，只有需要确定性行为或外部工具时才添加脚本，并通过实际提示测试触发范围。

## 本仓库解读

只保留真正影响决策的指导。自动匹配不是必然触发的保证，Skill 数量与脚本需求在后续行为试验后确定。

返回 [资料索引](README.md)。
