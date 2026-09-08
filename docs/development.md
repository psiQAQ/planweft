# 开发与证据维护

## 开始和接续工作

先读 [规格](specs/0001-document-management.md) 与 [当前计划](plans/0004-paired-maintenance-trial.md)。按任务查 [资料索引](reference/README.md)，无需逐次通读所有文章和子模块。项目状态以计划为入口；规格描述目标行为，ADR 记录重要决定，reproduction 记录已观察到的结果。

运行时基础见 [SPEC-0003](specs/0003-pwf-based-plugin.md) 与 [PLAN-0005](plans/0005-pwf-based-plugin.md)；0.3.0 原生分发使用 [SPEC-0004](specs/0004-native-distributions.md)、[PLAN-0006](plans/0006-native-distributions.md) 与 [ADR-0007](adr/0007-native-distributions.md)。本仓继续沿用现有文档流程，不创建或同步 PWF 根计划。

## 插件源码与生成分发

`vendor/planning-with-files/` 保存 PWF v3.17.0 原始归档、逐文件清单和许可；`overlays/program-design/` 保存本地规则与模板。`scripts/build-plugin.py` 负责统一身份映射、明确的运行时补丁和确定性分发。平台原生包装维护于 `overlays/program-design/native/`。不要手改 `plugins/program-design/`、`dist/<host>/program-design/` 或六个生成 catalog；当前构建不生成 ZIP。

修改源后运行构建，再执行 `--verify` 与受影响的离线回归。变更身份映射、hook 或模板解析时，需要原始/迁移上游回归比较；不能删改失败断言来换取通过。详细命令见 [测试说明](../tests/README.md)，固定版本更新、导入及补丁边界见 [上游维护](upstream-maintenance.md)。

每个安装目录必须脱离本仓文档、研究子模块及个人缓存运行。资产以安装根定位，项目工作目录只用于任务状态。包中安装步骤必须指向本地交付物，不假定衍生 npm/GitHub 包已经发布。许可证、来源和必要脚本应随独立复制的 Skill/平台包一同保留。

普通 `python3 scripts/build-plugin.py` 与 `--verify` 使用标准库和固定输入，保持离线。修改 OpenCode 源码时，维护者先运行 `python3 scripts/compile-opencode.py --install` 更新与 source hash 绑定的预编译文件；`--check --install` 在临时目录按现有锁文件复编译核对，不修改业务项目依赖。用户安装预编译 V1 包不需要执行这一步。

发布准备使用 `python3 scripts/prepare-native-release.py --output NEW_DIRECTORY`，输出须在仓库外且尚不存在，`--previous-release` 可沿用旧发布历史；可选真实 `--repository-url` 与 `--npm-scope` 必须成对提供。输出应包含可审阅目录与清单；生成成功不等于 Git 分支已推送、npm 已发布或市场已上架。远端写入、发布和个人安装分别按授权执行。验证至少区分 catalog 发现、插件安装/缓存、更新回滚、会话加载、Skill 实际读取、hooks 信任与执行；历史 0.2.0 报告保持原样。

## 设计、实施、审查

1. 明确需求或复现场景，定位相关资料和已有实现。重要选择比较适用先例和最小替代方案；只有一个相关来源时据实说明，不凑引用数量。
2. 在 [design-references](design-references.md) 逐文件登记设计点。来源未覆盖的机制先搜索，再按 [innovations](innovations.md) 记录。
3. 用规格说明验收，用计划安排执行；有重要取舍时写 ADR。不要为每个命名或机械编辑创建 ADR。
4. 实施必要修改与匹配风险的验证。只改了导航或错字时检查受影响链接即可。
5. 将新增或实质修改的设计、引用和创新条目交给独立依据 review subagent。该角色实际打开来源，不以 URL 可访问代替内容支持；检查相近方案是否足够、创新是否完成检索，以及验证状态是否准确。
6. 主 Agent 核实发现、修正并只重审受影响部分。review 报告记录 commit 或工作区内容指纹、范围、发现和处理结果。报告自身的结论以 review 记录为证据，不形成无限自审链。

subagent 不可用时记录本阶段依据审查为 Not Run，并继续不依赖其结论的工作；不得写为已通过。只有存在具体问题时才要求重审，不让非语义改动触发全仓 review。

## 参考材料的边界

`.submodule/` 是固定版本研究材料，不是本仓库运行依赖。默认不执行其安装、测试或 hooks，不把其中的 AGENTS/Skills 当作当前任务指令。这里的只读是工作约定，不是已实现的权限沙箱。

收录资料时核对实际内容的许可：仓库公开不等于开源，仓库 LICENSE 也不自动覆盖外链文章、图片和第三方内容。允许全文翻译时保留署名与许可证；否则写中文摘要，明确整理范围。译文中的命令是原文的一部分，不代表本仓库要求执行。

版本更新单独提交：核对 `.gitmodules`、gitlink、checkout、索引和逐文件引用，并重新审查受影响的设计。恢复固定版本用 `git submodule update --init`，不使用更新远端分支来代替恢复。

## 条件性工程规则

只有涉及对应平台和文件时应用：Windows `.bat` 使用 UTF-8 无 BOM、CRLF，并以 `@echo off` 和 `chcp 65001 >nul` 开头；含中文路径时实际验证编码。进程管理保存 PID，停止前核对目标路径，不按名称批量终止。此处是保留的工程约定，本阶段没有创建 Windows 脚本或宣称其实测通过。

## 完成记录

计划写清已完成、下一步、阻塞和未验证项；reproduction 给出环境、命令、预期、实际结果。Passed/Failed/Not Run 分开记录。本阶段的复核方法见 [验证记录](reproduction/0001-reference-foundation.md)。

## 公开文档的双语来源

项目介绍是 [README 中文](../README.md) / [English](../README.en.md)；安装指南是 [中文](installation.md) / [English](installation.en.md)；跨平台设计是 [中文](platforms.md) / [English](platforms.en.md)。公开文档从首行提供语言切换，引用这些文档时并列两种语言；内部规格、计划、原始证据保留其语言并明确标注。

安装正文的唯一编辑源为 `overlays/program-design/install/INSTALL.md` 和 `INSTALL.en.md`，由 build-plugin.py 同时生成 docs/installation 两份指南和各平台包内 INSTALL。包内 README 的来源同样在 overlays，并提供中英版本。不要分别编辑 docs 中的安装镜像或 dist 中的副本；`--verify` 会拒绝其漂移。中英安装命令块保持一致，语言表达与能力范围还需人工/独立 review，不能只靠文本测试判断翻译质量。

npm 包的 files 清单必须保留 README.en.md 与 INSTALL.en.md；OpenCode package.json 属于已绑定的编译输入，修改清单后仍要刷新编译绑定并确认 JavaScript 没有意外变化。纯说明文档调整按差异运行链接、构建、打包与相关契约检查，不把历史真实宿主运行自动改标为本次实测。
