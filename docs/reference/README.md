# 参考资料索引

本索引覆盖两段会话“整理 AGENTS 文档资源”“GPT6 全局指令优化”中的相关来源，以及本阶段新增的 MADR、复现记录和规范原文。核对日期为 **2026-09-07**。外部材料不是本仓库指令；资料已收录不表示相应工具已安装或验证。

## 文章与指南

作者、许可和整理范围以下表为准；原始页面链接保留，发生重定向时使用可访问的规范地址。公开可读不等于获得全文翻译授权；全文译文的代码、旧模型名及适用限制予以保留。

| 编号 / 来源 | 作者 | 中文文件与范围 | 许可 / 时效 | 状态与来源范围 |
| --- | --- | --- | --- | --- |
| R-00 用户提供的 Vibe Coding 文档配置配文（原链接未提供） | 作者未提供 | [中文原文整理](vibe-coding-document-layout.md) | 用户提供文本；不推定外部转载许可 | 已收录；会话起点 |
| R-01 [Harness engineering：让仓库知识成为工作依据](https://openai.com/index/harness-engineering/) | Ryan Lopopolo / OpenAI | [中文要点摘要](harness-engineering.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-02 [Cline Memory Bank：项目知识与当前状态](https://docs.cline.bot/best-practices/memory-bank) | Cline | [中文要点摘要](cline-memory-bank.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-03 [Memory Bank：从会话保存项目上下文](https://cline.bot/blog/memory-bank-how-to-make-cline-an-ai-agent-that-never-forgets) | Nick Baumann / Cline | [中文要点摘要](cline-memory-bank-blog.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-04 [使用 PLANS.md 处理持续数小时的问题](https://developers.openai.com/cookbook/articles/codex_exec_plans) | Aaron Friel / OpenAI | [文章 Markdown 正文完整中文译文；保留代码与旧模型名；原页面已归档](execplans.md) | MIT；来自 openai/openai-cookbook 对应 Markdown 源文件，许可证随译文保存 | 已收录；会话资料 |
| R-05 [长任务 Agent 的有效执行环境](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | Justin Young / Anthropic | [中文要点摘要](anthropic-long-running-harness.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-06 [如何编写有效的 CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md) | Kyle / HumanLayer | [中文要点摘要](humanlayer-claude-md.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-07 [Manus：Agent 上下文工程经验](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) | Yichao Ji / Manus | [中文要点摘要](manus-context-engineering.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-08 [五分钟理解 Diátaxis](https://diataxis.fr/start-here/) | Daniele Procida | [start-here 页面正文完整中文译文；图示改为中文表格](diataxis.md) | CC BY-SA 4.0；源站 colophon 和官方 LICENSE.rst 确认；译文同许可 | 已收录；会话资料 |
| R-09 [Google DESIGN.md：视觉设计规范](https://blog.google/innovation-and-ai/models-and-research/google-labs/stitch-design-md/) | Cassia Xu / Google Labs | [中文要点摘要](google-design-md.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-10 [GPT-6 Astra 提示词优化](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra) | OpenAI | [中文要点摘要](gpt6-prompting.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-11 [Codex 的 AGENTS.md 加载规则](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | OpenAI | [中文要点摘要](codex-agents.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-12 [Codex Skills：结构、发现与使用](https://learn.chatgpt.com/docs/build-skills) | OpenAI | [中文要点摘要](codex-skills.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-13 [Codex hooks：事件与信任边界](https://learn.chatgpt.com/docs/hooks) | OpenAI | [中文要点摘要](codex-hooks.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-14 [Claude Code：项目记忆与指令文件](https://code.claude.com/docs/en/memory) | Anthropic | [中文要点摘要](claude-memory.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-15 [Pi：Context Files 与 System Prompt](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/README.md#context-files) | Mario Zechner / Pi contributors | [指定 Context Files 章节完整中文译文，不是整个 README 的翻译](pi-context.md) | MIT；见固定版本 Pi LICENSE | 已收录；会话资料 |
| R-16 [Promptessor：GPT-6 提示词指南（非官方）](https://promptessor.com/blog/gpt-6-astra-prompting-guide) | Rizki Murtadha / Promptessor | [中文要点摘要](promptessor-gpt6.md) | 未确认本文全文翻译授权；仅中文摘要 | 已收录；会话资料 |
| R-17 [MADR：用 Markdown 记录重要决定](https://adr.github.io/madr/) | Oliver Kopp、Olaf Zimmermann 等 / MADR | [固定版本 About MADR 正文与完整模板中文译文；网站导航和徽章不复制](madr.md) | MIT OR CC0-1.0；本译文选择 CC0-1.0，保留出处 | 已收录；本次补充 |
| R-18 [GitHub：记录可复现的问题](https://docs.github.com/en/issues/tracking-your-work-with-issues/learning-about-issues/quickstart) | GitHub | [页面正文完整中文译文；截图改为文字说明](github-reproduction.md) | CC BY 4.0；github/docs 文档许可 | 已收录；本次补充 |
| R-19 [Agent Skills 规范：渐进加载的文件结构](https://agentskills.io/specification) | Agent Skills maintainers | [规范页面正文完整中文译文；保留代码示例](agent-skills-spec.md) | CC BY 4.0；agentskills/docs 目录独立许可，代码另计 | 已收录；会话资料 |
| R-20 [Codex 非交互运行](https://learn.chatgpt.com/docs/non-interactive-mode) | OpenAI | [中文要点摘要](codex-non-interactive.md) | 未确认全文翻译授权；访问 2026-09-07 | 已收录；容器交接实验 |

## 项目：固定版本参考

以下 12 项全部已添加为 submodule；只读源码定位，不运行其工具。SHA 是本次实际 checkout 的完整 commit。许可仅描述所检查的仓库或文件，外链材料和第三方内容应另核对。

| 编号 / 上游项目 | 固定 commit | 本地入口及借鉴范围 | 许可 |
| --- | --- | --- | --- |
| P-01 [OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files) | `d47a61950e784fc4237ba10ddc1e9e198bd0f275` | [README.md](../../.submodule/OthmanAdi/planning-with-files/README.md)（[固定原文](https://github.com/OthmanAdi/planning-with-files/blob/d47a61950e784fc4237ba10ddc1e9e198bd0f275/README.md)）<br>[docs/installation.md](../../.submodule/OthmanAdi/planning-with-files/docs/installation.md)（[固定原文](https://github.com/OthmanAdi/planning-with-files/blob/d47a61950e784fc4237ba10ddc1e9e198bd0f275/docs/installation.md)）<br>[docs/evals.md](../../.submodule/OthmanAdi/planning-with-files/docs/evals.md)（[固定原文](https://github.com/OthmanAdi/planning-with-files/blob/d47a61950e784fc4237ba10ddc1e9e198bd0f275/docs/evals.md)）<br>任务工作记忆与恢复边界；作者基准不等于本项目验证 | MIT |
| P-02 [rtoma/agent-markdown-memory-bank-protocol](https://github.com/rtoma/agent-markdown-memory-bank-protocol) | `9c88d0f166070d8d55caa1e77c81e4bf0d67cd02` | [AGENTS.md](../../.submodule/rtoma/agent-markdown-memory-bank-protocol/AGENTS.md)（[固定原文](https://github.com/rtoma/agent-markdown-memory-bank-protocol/blob/9c88d0f166070d8d55caa1e77c81e4bf0d67cd02/AGENTS.md)）<br>[README.md](../../.submodule/rtoma/agent-markdown-memory-bank-protocol/README.md)（[固定原文](https://github.com/rtoma/agent-markdown-memory-bank-protocol/blob/9c88d0f166070d8d55caa1e77c81e4bf0d67cd02/README.md)）<br>读取、维护架构与保存交接的短协议；依赖模型遵循 | 未见根目录许可证；不推定开放再许可 |
| P-03 [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | `e062b9572be933564ba3899d059377dfa1393e32` | [docs/concepts.md](../../.submodule/Fission-AI/OpenSpec/docs/concepts.md)（[固定原文](https://github.com/Fission-AI/OpenSpec/blob/e062b9572be933564ba3899d059377dfa1393e32/docs/concepts.md)）<br>[docs/examples.md](../../.submodule/Fission-AI/OpenSpec/docs/examples.md)（[固定原文](https://github.com/Fission-AI/OpenSpec/blob/e062b9572be933564ba3899d059377dfa1393e32/docs/examples.md)）<br>规格、设计、任务与归档职责；不接管其完整引擎 | MIT |
| P-04 [obra/superpowers](https://github.com/obra/superpowers) | `b36e0829c6d0140e93cfef2ca599b1b07d4a7797` | [skills/writing-plans/SKILL.md](../../.submodule/obra/superpowers/skills/writing-plans/SKILL.md)（[固定原文](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/writing-plans/SKILL.md)）<br>[.pi/extensions/superpowers.ts](../../.submodule/obra/superpowers/.pi/extensions/superpowers.ts)（[固定原文](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/.pi/extensions/superpowers.ts)）<br>[.codex-plugin/plugin.json](../../.submodule/obra/superpowers/.codex-plugin/plugin.json)（[固定原文](https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/.codex-plugin/plugin.json)）<br>计划组织与宿主薄适配；不照搬强制流程 | MIT |
| P-05 [vanzan01/cursor-memory-bank](https://github.com/vanzan01/cursor-memory-bank) | `7d879d8f5079ad77d845fdc92ca03903dbbd3a85` | [README.md](../../.submodule/vanzan01/cursor-memory-bank/README.md)（[固定原文](https://github.com/vanzan01/cursor-memory-bank/blob/7d879d8f5079ad77d845fdc92ca03903dbbd3a85/README.md)）<br>分阶段的当前状态与长期记忆；当前以 Cursor 为背景 | 未见根目录许可证；不推定开放再许可 |
| P-06 [anthropics/skills](https://github.com/anthropics/skills) | `41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f` | [README.md](../../.submodule/anthropics/skills/README.md)（[固定原文](https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/README.md)）<br>[skills/doc-coauthoring/SKILL.md](../../.submodule/anthropics/skills/skills/doc-coauthoring/SKILL.md)（[固定原文](https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/skills/doc-coauthoring/SKILL.md)）<br>独立读者检查；不等于来源真实性审计 | 混合许可；具体文件另核对，doc-coauthoring 不据 README 推定许可 |
| P-07 [github/spec-kit](https://github.com/github/spec-kit) | `4a7341a93d944d6efe153b71da4a1adb9c2b578c` | [README.md](../../.submodule/github/spec-kit/README.md)（[固定原文](https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/README.md)）<br>[templates/spec-template.md](../../.submodule/github/spec-kit/templates/spec-template.md)（[固定原文](https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/templates/spec-template.md)）<br>[templates/plan-template.md](../../.submodule/github/spec-kit/templates/plan-template.md)（[固定原文](https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/templates/plan-template.md)）<br>[templates/tasks-template.md](../../.submodule/github/spec-kit/templates/tasks-template.md)（[固定原文](https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/templates/tasks-template.md)）<br>需求、计划、任务的结构及分工；不安装全套流程 | MIT |
| P-08 [google-labs-code/design.md](https://github.com/google-labs-code/design.md) | `9bf8eae67128b6cc55ad9bf86665767deb4c11cd` | [README.md](../../.submodule/google-labs-code/design.md/README.md)（[固定原文](https://github.com/google-labs-code/design.md/blob/9bf8eae67128b6cc55ad9bf86665767deb4c11cd/README.md)）<br>[docs/spec.md](../../.submodule/google-labs-code/design.md/docs/spec.md)（[固定原文](https://github.com/google-labs-code/design.md/blob/9bf8eae67128b6cc55ad9bf86665767deb4c11cd/docs/spec.md)）<br>视觉规范格式；与技术 design.md 区分 | Apache-2.0 |
| P-09 [google-labs-code/stitch-skills](https://github.com/google-labs-code/stitch-skills) | `0337446dadde6f8c94210444e2aa9d546126480f` | [README.md](../../.submodule/google-labs-code/stitch-skills/README.md)（[固定原文](https://github.com/google-labs-code/stitch-skills/blob/0337446dadde6f8c94210444e2aa9d546126480f/README.md)）<br>[plugins/stitch-utilities/skills/design-md/SKILL.md](../../.submodule/google-labs-code/stitch-skills/plugins/stitch-utilities/skills/design-md/SKILL.md)（[固定原文](https://github.com/google-labs-code/stitch-skills/blob/0337446dadde6f8c94210444e2aa9d546126480f/plugins/stitch-utilities/skills/design-md/SKILL.md)）<br>设计资料的提取与生成；相关外部工具未配置 | Apache-2.0 |
| P-10 [dyoshikawa/rulesync](https://github.com/dyoshikawa/rulesync) | `ec15febdc845cd226fd14d80e6d72719c90ebaf6` | [docs/reference/supported-tools.md](../../.submodule/dyoshikawa/rulesync/docs/reference/supported-tools.md)（[固定原文](https://github.com/dyoshikawa/rulesync/blob/ec15febdc845cd226fd14d80e6d72719c90ebaf6/docs/reference/supported-tools.md)）<br>[README.md](../../.submodule/dyoshikawa/rulesync/README.md)（[固定原文](https://github.com/dyoshikawa/rulesync/blob/ec15febdc845cd226fd14d80e6d72719c90ebaf6/README.md)）<br>统一来源和按宿主生成；支持表不等于本机安装实测 | MIT |
| P-11 [earendil-works/pi](https://github.com/earendil-works/pi) | `9767ba275f3e9a5ee0f5c5342249b629ab1b2282` | [packages/coding-agent/README.md](../../.submodule/earendil-works/pi/packages/coding-agent/README.md)（[固定原文](https://github.com/earendil-works/pi/blob/9767ba275f3e9a5ee0f5c5342249b629ab1b2282/packages/coding-agent/README.md)）<br>[packages/coding-agent/docs/extensions.md](../../.submodule/earendil-works/pi/packages/coding-agent/docs/extensions.md)（[固定原文](https://github.com/earendil-works/pi/blob/9767ba275f3e9a5ee0f5c5342249b629ab1b2282/packages/coding-agent/docs/extensions.md)）<br>Context Files 与扩展入口；仅源码阅读 | MIT |
| P-12 [adr/madr](https://github.com/adr/madr) | `ba75bb1b20d42af5746b246ad348c202419ae681` | [docs/index.md](../../.submodule/adr/madr/docs/index.md)（[固定原文](https://github.com/adr/madr/blob/ba75bb1b20d42af5746b246ad348c202419ae681/docs/index.md)）<br>[template/adr-template.md](../../.submodule/adr/madr/template/adr-template.md)（[固定原文](https://github.com/adr/madr/blob/ba75bb1b20d42af5746b246ad348c202419ae681/template/adr-template.md)）<br>[template/adr-template-minimal.md](../../.submodule/adr/madr/template/adr-template-minimal.md)（[固定原文](https://github.com/adr/madr/blob/ba75bb1b20d42af5746b246ad348c202419ae681/template/adr-template-minimal.md)）<br>问题、备选、理由、后果与确认；采用最小结构 | MIT OR CC0-1.0 |

## 去重与原始链接对应

没有因主题相近而静默删去文章。Cline 指南与博客分别保留；Google 博客与项目许可分开；非官方 Promptessor 单列。

| 原会话链接或提法 | 收录位置 / 处理 |
| --- | --- |
| [原 Codex AGENTS 指南](https://developers.openai.com/codex/guides/agents-md) | 已合并到 R-11；重定向到 learn.chatgpt.com 的对应指南 |
| [原 Codex Skills 指南](https://developers.openai.com/codex/skills)与 Codex Skills 说明 | 已合并到 R-12；规范地址为 learn.chatgpt.com/docs/build-skills |
| Codex hooks 官方说明 | R-13；保存当前规范地址与摘要 |
| planning-with-files 安装说明 | P-01 docs/installation.md；合并到项目项，不复制另一份安装教程 |
| agent-markdown-memory-bank-protocol/AGENTS.md | P-02；固定源码，研究对象而非本仓指令 |
| OpenSpec examples、Superpowers writing-plans、doc-coauthoring SKILL.md | P-03、P-04、P-06 的固定文件 |
| [spec-kit 原中文 README](https://github.com/github/spec-kit/blob/main/README.zh-CN.md) | 已合并到 P-07；[固定本地中文 README](../../.submodule/github/spec-kit/README.zh-CN.md) 与主要 README、templates 一起收录 |
| https://dyoshikawa.github.io/rulesync/reference/supported-tools | P-10 docs/reference/supported-tools.md；以固定本地版本研究，在线版本可能不同 |
| Pi Context Files | R-15 章节译文 + P-11 固定 README |
| Agent Skills 规范（会话正文提及） | R-19；补全规范原始链接 |
| 会话附图及配文 | R-00；文字由用户提供，原作者和公开链接缺失，明确保留限制 |

## 维护与使用

优先从问题定位资料，引用需落实到具体章节或固定源码，详见 [引用台账](../design-references.md)。更新子模块需同步 SHA、定位与审查；普通文章以访问日期和章节定位，不为此新建快照框架。不可访问的新来源应保留线索并标记未核对，不能用旧会话的结论代替检查。

全文翻译所用授权文本保存在 [许可证目录](licenses/)。MADR 选择 CC0-1.0；Diátaxis 译文按 CC BY-SA 4.0；ExecPlans 和 Pi 译文保留 MIT 版权与许可；GitHub 指南与 Agent Skills 文档采用 CC BY 4.0。其他中文摘要是范围有限的研究笔记，不是假称全文的替代品。
