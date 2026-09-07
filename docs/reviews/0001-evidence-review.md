# REV-0001：参考基础与设计依据审查

状态：**Passed（依据与文档静态检查）**；日期：2026-09-07。独立审查者：`evidence_review` subagent；主 Agent 负责编辑、复核并处理发现。审查绑定基础提交 `7b45c64f711952512a1dca19d67df3b0e565ca83`，reviewer 确认该提交与已审工作区相符。后续收尾只更新计划、验证记录和本报告的事实结果。

## 范围与方法

逐份读取 34 个第一方 Markdown，按 [引用台账](../design-references.md) 检查实质设计；核对 [资料索引](../reference/README.md)、R-00～R-19 中文资料、6 份许可副本和 [创新记录](../innovations.md)。直接读取两段会话，32 个可见相关 URL 均有去向，包括旧 Codex URL 和 spec-kit 中文 README。

外部依据读取 19 个 R 来源的页面或对应固定原文；R-00 依据会话提供的中文配文。对 6 份正文/指定章节译文作内容对照，对其他摘要核对实际主张和定位。检查 12 个子模块的 gitlink、checkout、索引 SHA，以及索引涉及的关键文件：包括 MADR 原文与模板、Pi Context Files、OpenSpec concepts、Spec Kit 模板、doc-coauthoring 独立读者阶段和 Superpowers 适配入口。没有审查全部子模块源码。

不执行上游项目的工作流。独立性借鉴独立读者方法，但本次实际审查职责由用户需求 REQ-06 确定，不能把现成 doc-coauthoring Skill 描述为引用真实性审计工具。

## 发现与处理

| 编号 | 发现及依据 | 主 Agent 处理 | 回审结果 |
| --- | --- | --- | --- |
| F-01 | MADR“完整模板”最初被压缩成解释段落，与 P-12 固定模板的占位结构及范围声明不符 | [madr.md](../reference/madr.md) 保留全部元数据、可选注释、章节和方案占位符 | Passed；逐段对照完整模板 |
| F-02 | Cline 博客、Anthropic harness、HumanLayer、Google 和 Promptessor 的发布机构不能代替可查的作者署名 | 索引及对应中文文件补充 Nick Baumann、Justin Young、Kyle、Cassia Xu、Rizki Murtadha | Passed；与原文署名一致 |
| F-03 | Manus、Codex、Cline、Promptessor、Google 和 OpenSpec 的若干原文定位使用泛指词或不准确标题 | 改为实际标题；无二级标题的 Google 正文使用标题后段落位置 | Passed；可定位实际内容 |
| F-04 | spec-kit 中文 README 的去向虽已覆盖，但别名表未保留完整原链接 | 补原始 URL 与固定子模块中的中文 README 链接 | Passed；文件实际存在 |
| F-05 | 初稿尚未确认 GitHub Docs 和 Agent Skills 文档目录的许可，只保存摘要 | 主 Agent 与 reviewer 分别确认 CC BY 4.0，补为正文译文，保存许可并同步索引、台账 | Passed；范围、内容及目录级许可相符 |
| F-06 | 主 Agent 暂存检查发现 Diátaxis 上游许可副本有 6 处行尾空白 | 只移除行尾空白，在译文声明该格式处理 | Passed；`git show --check` 无格式错误 |

无剩余阻断项。早期内部草案中的“两次任务”数字不在最终用户计划中；reviewer 撤回该条草案差异，不把任意次数恢复为迁移标准。ADR-0003 保留最终计划要求的生命周期、证据、交接、迁移 ADR 与回退条件。

## 三类结论

| 维度 | 结论与边界 |
| --- | --- |
| 来源可访问 / 定位存在 | Passed；R-01～R-19 原文或对应源码可核对，索引项目文件存在；R-00 原作者和公开链接缺失已如实标注，未伪造出处 |
| 依据支持设计 | Passed；逐文件区分用户要求、借鉴及本地差异；重要取舍采用普通 Markdown 起点。创新记录无已实施创新，未把有限检索写成原创证明 |
| 本仓库验证 | Passed 仅限文档静态检查：reviewer 独立执行基础提交内命令，34 份 Markdown、143 个本地文件链接、12 个子模块，错误 0；`git show --check HEAD` 通过。外部网络恢复由主 Agent 另记于 reproduction |

## 限制与后续

全文翻译范围分别为 ExecPlans 文章正文、Diátaxis start-here 正文、MADR About 与模板、Pi Context Files（含 System Prompt）、GitHub quickstart 正文、Agent Skills specification 正文。部分截图或展示组件转为文字，均有范围说明；其他文章只是要点摘要。Pi/MADR 许可副本与对应固定上游文本一致；混合或未见明确许可的参考项目没有被一概重授权。

真实个人 override 加载、模型遵循、产品 Linux/Windows 行为、参考工具运行和自管理迁移均为 **Not Run**。静态文件布局符合官方规则不等于真实宿主已加载或模型已遵循；来源存在也不等于运行效果已验证。

本次针对修正只回审受影响部分。后续新增实质设计、来源版本或创新条目时进行对应审查；导航、错字和完成状态不自动触发全仓重审。主 Agent 的实际恢复和最终收录检查见 [REP-0001](../reproduction/0001-reference-foundation.md)。
