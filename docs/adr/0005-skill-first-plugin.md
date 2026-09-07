# ADR-0005：以单一 Skill 实现文档协作首版

状态：Accepted；日期：2026-09-07；需求：SPEC-0002 PD-01～07，用户本次明确授权。

## 问题、备选与决定

用户选择完整协作流程、项目启用后按任务自动使用、仓库交付。ADR-0004 曾约束先验证只读原型再扩写；本决定因新需求重新讨论并替代其对本版文档编辑的限制，保留此前实验为历史。

| 方案 | 取舍 |
| --- | --- |
| 继续人工描述 Markdown 流程 | 已能工作，但不满足可安装复用需求 |
| 单 Skill 组织现有 Agent 工具 | 满足分发及协作，无新的存储/同步/写回引擎；依赖模型和宿主权限 |
| 独立 CLI、写回引擎、hooks | 尚无必要性证据，增加状态与跨平台维护成本 |

选择第二项。旧决定对专用引擎的保守取舍继续保留；不声称只读产品或双平台门槛已经通过。

## 依据与本地差异

R-21 `Create a plugin manually` 提供单 Skill 封装；R-12 `Best practices` 支持先用指令及触发测试。P-04 `.codex-plugin/plugin.json` 和 `skills/writing-plans/SKILL.md` 为分发/计划先例；P-03 `Keep It Lightweight: Progressive Rigor` 为逐步采用；R-04 是历史自包含计划方法，P-06 `Stage 3: Reader Testing` 为独立读者方法。

单 Skill、项目启用、逐文件引用和独立依据 reviewer 的组合来自用户需求及本地选择，不冒称上游已有完整实现。无须安装整体上游 workflow，当前没有新增需登记原创性的机制。

## 后果与确认

插件包自包含；已有项目不迁移目录。description 和正文限定启用，自动匹配不是强制保证；以正负样例检验漏用、越界维护等风险。

安装、行为、审查与平台结果分别记录于 [REP-0003](../reproduction/0003-project-docs-plugin.md)、[REV-0003](../reviews/0003-project-docs-plugin-review.md)。正式自身接管另经 ADR-0003 与迁移 ADR，本次不在根 AGENTS 启用插件。
