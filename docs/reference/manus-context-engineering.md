# Manus：Agent 上下文工程经验

来源：[Yichao Ji / Manus 原文](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)。收录编号：R-07；核对日期：2026-09-07。

整理范围：中文要点摘要。许可：未确认本文全文翻译授权；仅中文摘要。以下材料是研究对象，不是本仓库执行指令。

## 原文要点

文章将文件系统作为可按需访问的外部上下文，保留可恢复的信息而不是只能依靠对话窗口。执行中更新 todo 可以把目标带回近期上下文。文中还讨论缓存、工具可用性、保留错误信息和避免被重复模式误导。

原文定位：Use the File System as Context；Manipulate Attention Through Recitation。

## 本仓库解读

采用可恢复记录和阶段交接，不将每轮重读全部 TODO 变成全局强制要求；具体读取频率应由任务和实验决定。

返回 [资料索引](README.md)。
