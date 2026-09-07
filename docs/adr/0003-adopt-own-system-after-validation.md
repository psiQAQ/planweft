# ADR-0003：以验证结果作为自身体系切换条件

状态：Accepted（门槛已接受，迁移尚未发生）；日期：2026-09-07；需求：REQ-10。

## 问题与备选方案

尚未实现的工具不能成为本仓库文档的可靠前提。比较立即换成新格式、长期双写、先沿用现有文档再经验证接管三种方式，选择第三种。

## 决定

工具应先在既有文档上完成发现、创建、读取、增量更新、证据维护及一次无旧对话上下文的交接；检查来源映射、历史记录和链接没有损失，并保留可恢复的旧状态。完成独立 review 后，以新的迁移 ADR 记录验证结果、映射、回退方式和切换决定。

这是本仓库根据 REQ-10 选择的验收门槛，不是外部资料保证的成熟度指标。借鉴 [ExecPlans](../reference/execplans.md) 的自包含交接、[doc-coauthoring](../../.submodule/anthropics/skills/skills/doc-coauthoring/SKILL.md) 的独立读者检查和 [OpenSpec](../../.submodule/Fission-AI/OpenSpec/docs/concepts.md) 的归档概念；不采用双份独立任务状态或预先批量重命名。

## 后果与确认

本阶段所有工具行为、Linux/Windows 产品兼容和迁移均为 Not Run。以后先接管现有职责与路径，再根据证据决定是否需要格式迁移。切换失败时回到已验证的 Markdown/Git 工作流程。
