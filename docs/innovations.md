# 创新与资料未覆盖的设计

截至 0.3.0，本仓库有已实现的工作流扩展、确定性分发、宿主适配与验证工具，但没有据先例检索和独立审查确立的方法首创声明。README 中的“原创实现”指本地编写的扩展与组合贡献；文件规划、ADR、冷读和生成分发本身各有已有方案。实现归属见 [引用台账](design-references.md) 和 [补丁清单](../overlays/program-design/PATCHES.md)。目录命名、引用台账和个人偏好分离仍属于需求/本地取舍。

## 新想法的处理

先说明实际问题和最小验证，再检索官方文档、GitHub 实现及已收录子模块。检索组合使用问题描述、机制名称和近义词，记录日期、查询与范围；沿相关结果检查具体源码。找到先例后补入 [资料索引](reference/README.md)，并更新 [引用台账](design-references.md)。

如果没有找到足够相近的实现，新增下表记录。只能说“本次检索未找到”，不能把未检出写成不存在，也不能以此绕过必要性审查。

| 字段 | 应记录的内容 |
| --- | --- |
| ID、状态、目标文件 | 候选/验证中/采用/放弃；对应本仓库文件和需求 |
| 问题与已有方案不足 | 可观察的问题；为何普通文档或现有实现不足 |
| 检索证据 | 日期、查询词、搜索渠道/范围、打开的来源及结论 |
| 最接近的实现 | 本地参考位置、差异及适用限制 |
| 新设计与成本 | 超出资料的部分、维护负担及最小实现 |
| 验证与退出条件 | 如何证伪、何时删除或退回已有方案 |
| 独立 review | 来源核对、必要性结论、报告位置 |

## 基础阶段检索记录（2026-09-07，历史）

2026-09-07，围绕常规决策记录和复现文档检索 `site:adr.github.io architecture decision records`、`site.github.com architecture decision record references related decisions`、`site:docs.github.com issue forms steps reproduce expected behavior`。实际打开 MADR 官网/模板、ADR 官方目录和 GitHub Issues quickstart，发现已有合适先例，已收录为 R-17/R-18 与 P-12，因此没有新建创新机制。查询结果仅作为线索，最终依据定位到原始文档或固定源码。

基础阶段曾将来源指纹、写入锁、自动安装列为待设计能力，当时没有全面检索或实施。后续 0.2.0/0.3.0 实际采用了上游 attestation、固定来源与文件摘要、宿主原生安装渠道；具体范围以对应规格和复现记录为准。这些实现不使早期候选自动成为获批创新；新增机制仍按上述流程核查。

## 0.4.0 安装器组合设计

已检索 Vercel Skills installer/lock、Pi packages、OpenCode V1 plugins 和 npm trusted publishing。
本地扩展为一个包承载多入口，并将 host/scope 市场身份、依赖完整性与逐步失败收据组合；
链接、内容摘要、staging 和原生包管理均是已有机制，不作首创主张。依据见 ADR-0008 与引用台账。
