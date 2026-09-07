# ADR-0001：先用普通 Markdown 建立证据基础

状态：Accepted；日期：2026-09-07；决策依据：用户确认的 REQ-01、REQ-07。

## 背景与问题

本仓库尚无工具实现。直接引入七个命令、固定三个 Skills 和自定义元数据，会把前序讨论中的建议当成必需能力，无法检验复杂度是否解决了实际问题。

## 考虑的方案

- 用普通 specs/plans/ADR/reproduction 加引用、创新台账启动。
- 立即实现前序 `docctl` 设计。
- 安装一个完整规范驱动框架并采用其全部工作流。

## 决定与依据

选择第一种。参考 [Harness engineering](../reference/harness-engineering.md) 的短入口与仓库知识、[OpenSpec](../../.submodule/Fission-AI/OpenSpec/docs/concepts.md) 对规格和执行产物的区分，以及 [MADR](../reference/madr.md) 的问题、备选方案、决定和后果结构。

本仓库保留四个常见目录，由 Git 版本管理；不照搬 OpenSpec 的引擎、强制模板或 ExecPlans 的全部强制流程。TypeScript/Node.js 是用户选择的后续实现方向，不是上述文章规定的技术栈。

## 后果与确认

优点是能立即积累真实需求和可查证依据；代价是暂时依靠人工/Agent 按工作约定维护，尚无自动一致性保证。基础阶段已完成逐文件依据 review 和静态检查；新读者行为检查由后续 [PLAN-0002](../plans/0002-handoff-maintenance-baseline.md) 单独记录，工具收益留待行为实验。此处补清验证范围，不把依据 review 等同于无历史上下文的交接实测。
