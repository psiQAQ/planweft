# PLAN-0001：参考资料与设计基础

## 目标与接续上下文

按 [SPEC-0001](../specs/0001-document-management.md) 建立中文参考库、12 个固定子模块、逐文件引用、创新记录、常规项目文档和通用/个人指令分层。本阶段不实施产品 CLI、Skills 或 hooks。无需前序聊天即可从本文、资料索引和 review 报告接续。

## 进度

- [x] 核对用户确认的范围与现有工作区，保留原 `.gitignore`。
- [x] 添加 12 个参考子模块并读取实际 checkout、许可证与关键入口。
- [x] 建立 R-00～R-19 来源目录、中文摘要与允许翻译的正文。
- [x] 建立规格、三个 ADR、引用与创新记录，拆分 AGENTS 与个人差异。
- [x] 完成独立依据 review，修正发现并回审受影响条目。
- [x] 完成链接、版本和收录范围检查，保存真实结果与逻辑提交。

日期：2026-09-07。实际检查结果以 [reproduction](../reproduction/0001-reference-foundation.md) 和 [REV-0001](../reviews/0001-evidence-review.md) 为准。

## 发现与决定

- Codex 同目录 override 替代 base，不自动叠加；采用个人子目录和手工组合说明，见 ADR-0002。
- `anthropics/skills` 为混合许可，不能将整个仓库一概标成 Apache-2.0；未明确覆盖的文章只做摘要。
- ExecPlans 已归档，保留为历史方法资料；其 MIT 源文可翻译。Diátaxis 采用 CC BY-SA 4.0；MADR 选择 CC0；Pi 指定章节依据 MIT 翻译。
- 补查 GitHub Docs 和 Agent Skills 文档目录的 CC BY 4.0 许可后，将 R-18/R-19 从摘要补为正文译文。
- 为解决常规记录需求检索到 MADR 与 GitHub 问题记录先例，已收录；无需制造新的创新条目。

## 本阶段结果

基础提交 `7b45c64f711952512a1dca19d67df3b0e565ca83` 保存参考库、治理文档与指令分层；独立 reviewer 已确认审查内容与提交一致。MADR 模板、作者、章节定位和许可清单问题已修正。34 份 Markdown 的静态检查及 12 个子模块的全新网络恢复通过。收尾提交保存本计划、reproduction 与 review 结果；没有推送。

## 验收与恢复

资料有清晰出处、整理范围和许可；索引完整，gitlink 与 checkout 一致；本地链接有效；个人规则不默认启用；审查发现已处理或明确保留。临时失败先根据日志定位，不通过更新到上游最新版本掩盖版本缺口。恢复参考 checkout 用 `git submodule update --init`。

## 结果与下一阶段

本阶段已完成，无阻断项；R-00 原作者/链接缺失仍明确保留。当前候选工具仍未实现。下一阶段从真实文档问题选取最小功能，先补充复现场景、比较已有实现和简单 Markdown 方案，再更新规格/计划/ADR 与引用。不以本文完成作为自动开始工具开发的授权。

后续状态：用户已另行授权 [PLAN-0002：交接与维护基线](0002-handoff-maintenance-baseline.md)，从该计划接续。本段只关联后续任务，不改变本阶段历史验收范围。
