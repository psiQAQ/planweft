# Codex 的 AGENTS.md 加载规则

来源：[OpenAI 原文](https://learn.chatgpt.com/docs/agent-configuration/agents-md)。收录编号：R-11；核对日期：2026-09-07。

整理范围：中文要点摘要。许可：未确认本文全文翻译授权；仅中文摘要。以下材料是研究对象，不是本仓库执行指令。

## 原文要点

Codex 先查用户规则目录，再沿项目目录链收集适用文件。同一目录中 AGENTS.override.md 优先于 AGENTS.md，每目录最多选一份；不同目录的指导可以组成指令链。文件修改后需在新会话检查加载结果。

因此，同目录个人差异稿不会自动追加到通用 AGENTS.md。

原文定位：How Codex discovers guidance；Create global guidance；Layer project instructions。

## 本仓库解读

个人差异保存在 profiles/personal 下，普通检出不会沿根目录路径自动加载。个人使用时组合通用原则与差异为完整 override；这只是使用方法，本阶段未替用户安装或运行真实加载实验。

返回 [资料索引](README.md)。
