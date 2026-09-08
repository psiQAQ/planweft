# REV-0007：项目介绍与双语分发审查

## 独立复核补充：项目介绍与双语生成边界

日期：2026-09-08。审查者：`bilingual_install`，未编写根 README、比较表、生成器或 native adapter。该审查者编写了包内 README 与安装文档源，因此**不将这些文件的全文内容列为独立审查通过**。

实际读取范围：

- [根中文 README](../../README.md) 与 [根英文 README](../../README.en.md) 全文，重点核对五项参考方案、原创贡献限定和验证边界；两份 README 的 24 个链接目标相同，逐段核对未发现实质语言差异。
- [引用台账](../design-references.md) 的基础映射、首版 Skill 和 0.3.0 原生分发条目；[工作流扩展](../../overlays/program-design/workflow.md) 全文与 [创新记录](../innovations.md) 的当前归属、检索及历史限制。
- 固定 PWF v3.17.0 源码归档中的 `skills/planning-with-files/SKILL.md` 与 `docs/workflow.md`；`vendor/planning-with-files/upstream.json` 的 tag、commit 和归档来源。`docs/workflow.md` 第 115–127 行已经区分任务工作记忆与长期文档，并建议按需保存 ADR/docs；README 没有把这一分工冒称为本仓首创。
- OpenSpec 固定提交 `e062b9572be933564ba3899d059377dfa1393e32` 的 `docs/concepts.md` 中 Specs、Progressive Rigor、Changes 与 Artifacts；Superpowers 固定提交 `b36e0829c6d0140e93cfef2ca599b1b07d4a7797` 的 `skills/writing-plans/SKILL.md` 与 `.pi/extensions/superpowers.ts`；doc-coauthoring 固定提交 `41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f` 的阶段结构与 Reader Testing；MADR 固定提交 `ba75bb1b20d42af5746b246ad348c202419ae681` 的完整 ADR 模板。实际子模块 HEAD 与 README 所链提交一致。
- [生成器](../../scripts/build-plugin.py) 的本轮 diff、`distributions()` 文档注入、`public_installation_files()` 和 `inventory()`/`tree_digest()`，以及 [native adapter](../../overlays/program-design/native/adapters.py) 的本轮 diff；另读取 [发布准备](../../scripts/prepare-native-release.py) 的 npm 清单检查与 Git 发布树实现，以及 [REP-0006](../reproduction/0006-native-distributions.md) 的结果与限制。

结论：**Passed（本次静态独立复核范围）**，未发现须修复的实质问题。比较表的关注点和借鉴关系有上述固定原文支持；本地实现归属与“方法首创尚未确立”分开。`project-docs` 的维护、依据和交接要求实际存在于工作流扩展，README 同时声明依赖 Agent 遵循，未将 Skill 文字当作语义效果证明。

生成变更增加英文 README/INSTALL 的包含、按宿主提示和仓库安装指南镜像；`public_installation_files()` 只由安装源生成两份受管文档并替换对应导航，未引入安装或运行逻辑。native adapter 的两处修改只扩展文档 allowlist。检查当时已有生成文件的非 Markdown 差异仅为 `dist/manifest.json`、Pi/OpenCode 的 `package.json` 与 OpenCode `BUILD.json`，没有运行脚本、预编译 JavaScript 或 hooks 变化。这支持“本轮为双语文档交付改动”，不替代构建一致性和 npm 实物检查。

限制：没有重新运行宿主安装、hooks 或模型任务，也没有重新测量与其他方案的效果。八个宿主的生命周期与 Hermes 拒绝仍为 REP-0006 的历史结果；本次对英文文档的检查不扩展那些证据的有效范围。安装全文作为本人产出，应由其他 reviewer 独立核对。

### 后续发现闭环：README 源目录与安装包的相对链接

主 Agent 的首轮单元测试发现：包内 README 使用的 `INSTALL.md` / `INSTALL.en.md` 在生成包根可达，但同样的链接在 `overlays/program-design/` 源目录不可达。主 Agent 已将两个 README 源改为 `install/INSTALL.md` / `install/INSTALL.en.md`，并在生成器仅处理 README 时将这两种链接扁平化回安装包根。

独立复核该修复的脚本 diff，并检查两份源的全部四处安装引用以及 Codex、Pi、OpenCode、Hermes、Kiro 生成 README 对应引用，源路径与包内目标均实际存在，**Passed**。替换只涉及这两个明确的 Markdown 链接目标，不改变 Skill、运行时或安装命令。这里确认的是路径修复；完整单元测试的最终结果由主 Agent 的复验记录报告。
