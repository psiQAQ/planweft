[简体中文](platforms.md) | [English](platforms.en.md)

RC7 已通过 [OIDC](https://github.com/psiQAQ/planweft/actions/runs/34333285542) 发布到 next，远端准确字节一致，五镜像无模型原生安装/移除/重装 Passed。固定 Node 24.20.0 后的[三系统安装器 CI](https://github.com/psiQAQ/planweft/actions/runs/34334806556) 也已 Passed；这不代表 Windows/macOS 真实 Agent 模型已验证。

RC7 独立维护/冷读：Codex Passed；Pi 未采用计划、读取禁用配置且冷读有无依据归因，Failed；OpenCode 当前/历史实现记录矛盾且冷读漏报，Failed；DSH 功能与交接核心 Passed，但读取超出范围的宿主环境元数据，整体 Failed，未见凭据/业务/旧聊天内容。当前准备 RC8 入口决策与记录校验修复。Claude 兼容端点明确授权及模型验收仍待完成。下方表格是各历史版本的证据，不替代最终稳定验收。见[发布：中文](releasing.md) / [English](releasing.en.md)。

## 0.4.0 候选验证

单 npm 包提供安装器、Pi 资源和 OpenCode V1 入口。正式发布要求 Codex、Claude Code、Pi、OpenCode 和 DSH 五个平台全部通过；其余十个平台仍为实验性。已有本地生命周期证据保留，准确归档、真实模型与远端安装分别验收。Linux、Windows、macOS 安装器 CI 已通过，首次 Windows 故障注入路径问题已修复；[运行记录](https://github.com/psiQAQ/planweft/actions/runs/34242500572)。[发布：中文](releasing.md) / [English](releasing.en.md)。下方 0.3.0 证据继续作为历史记录。

# 跨平台设计

PlanWeft 0.4.0 将同一套文件规划与文档协作规则，生成适合 15 个宿主的独立分发目录。共享的是工作流和状态协议；安装入口、事件格式、缓存、信任与续跑能力沿用各宿主的原生机制。

项目目标与设计来源见项目介绍：[简体中文](../README.md) | [English](../README.en.md)。安装、更新、回退和卸载步骤见安装指南：[简体中文](installation.md) | [English](installation.en.md)。本页说明平台结构与能力边界，不重复安装操作步骤。

| 平台 | 静态检查 | 协议检查 | 原生生命周期（Linux） | 模型维护（Linux） |
| --- | --- | --- | --- | --- |
| Codex | Passed | Passed | Passed (RC5 same-version; RC3/4 upgrade/rollback) | Passed (RC4; independent review) |
| Claude Code | Passed | Passed | Passed (RC5 same-version; RC3/4 upgrade/rollback) | RC4 Flash code Passed; planning adoption Failed |
| Pi | Passed | Passed | Passed (RC5 same-version; RC3/4 upgrade/rollback) | RC4 initial consistency Failed; reviewed correction Passed |
| OpenCode V1 | Passed | Passed | Passed (RC5 same-version; RC3/4 upgrade/rollback) | RC4 maintenance Passed; cold-read accuracy Failed |
| Cursor | Passed | Passed | Not Run | Not Run |
| Copilot CLI | Passed | Passed | Not Run | Not Run |
| Gemini CLI | Passed | Passed | Not Run | Not Run |
| Hermes | Passed | Passed | Not Run | Not Run |
| Factory | Passed | Not Run | Not Run | Not Run |
| CodeBuddy | Passed | Not Run | Not Run | Not Run |
| Kiro | Passed | Not Run | Not Run | Not Run |
| Continue | Passed | Not Run | Not Run | Not Run |
| Mastra Code | Passed | Not Run | Not Run | Not Run |
| Agents | Passed | Not Run | Not Run | Not Run |
| DeepSeek Harness / DSH | Passed | Passed (RC3 sandbox protocol) | Passed (RC5 same-version; RC3/4 upgrade/rollback) | RC4 initial consistency Failed; reviewed correction Passed |

RC4 五个宿主的真实 npm RC3 → RC4 → RC3 → RC4 → 卸载均通过，包括 Pi/OpenCode/DSH 原生包入口；这些无模型检查不证明新会话模型行为。公开 Git marketplace 与 Windows/macOS 真实宿主分别记录。Pi RPC 与 OpenCode debug 是实际宿主加载，不是模型调用；非核心宿主的 0.3.0 安装结果不冒充 0.4.0 实测。

Codex 模型场景使用隔离容器及显式的 hook trust bypass；该结果证明已审查 hooks 的运行行为，不代表默认交互式信任确认流程已通过。

本轮五镜像验收的逐项结果见内部 [REP-0010](reproduction/0010-five-agent-release.md)（中文）；上表已有证据不替代最终稳定归档验收。

## 一份来源，生成多种原生目录

构建采用“固定上游源码 + 本地扩展 + 确定性生成”。当前底座是 PWF v3.17.0，提交 `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`；常规构建不读取研究子模块、个人插件缓存或网络。

| 层次 | 位置 | 职责 |
| --- | --- | --- |
| 固定来源 | `vendor/planning-with-files/` | 原始源码归档、逐文件清单、来源与 MIT 许可，不直接修补归档 |
| 共享扩展 | `overlays/planweft/` | 文档协作规则、模板、产品身份与安装资源 |
| 原生适配 | `overlays/planweft/native/` | 宿主 manifest、事件桥接、组件布局与安装资源定位 |
| 预编译资源 | `overlays/planweft/opencode-compiled/` | 绑定源码摘要的 OpenCode V1 编译结果；维护者编译，安装者使用成品 |
| 生成器 | `scripts/build-plugin.py` | 应用身份映射及补丁，生成全部平台目录、六种 catalog 和内容清单 |
| 分发 | `dist/<host>/planweft/` | 自包含安装源；各包保留 `LICENSE`、`UPSTREAM.json` 和所需运行资源 |
| 兼容镜像 | `plugins/planweft/` | 继续保留的 Codex 生成镜像，与 `dist/codex/planweft/` 一致 |

维护者修改生成源后重新构建，不分别手改平台副本。`dist/manifest.json` 记录产品版本、上游提交、平台路径、逐文件摘要、执行位和整体摘要。`--verify` 只读检查缺失、多余、内容与执行位漂移。生成器仅清理明确管理的产物，并保留根 catalog 中不属于本插件的条目。

PWF 的根目录隐藏文件夹承载了它的多个平台适配。本仓把共享实现集中在来源与 overlays 中，安装内容集中到 `dist`；根隐藏文件夹承担宿主发现入口。因此，根目录是否出现某个平台的同名文件夹，不等于是否支持该平台。

目录是可审阅的安装源，持续更新由宿主渠道负责。构建不再产生平台 ZIP；发布准备器仍可产生 npm 原生 `.tgz`，并为 Gemini/Hermes 生成包根 Git 发布树。维护细节见[上游与分发维护（工程记录，中文）](upstream-maintenance.md)。

## 六种 marketplace 独立发现

以下路径相对于仓库根，catalog 的 `name` 元数据均为 `planweft`。它们使用各宿主自己的 schema；注册其中一种不会替其他宿主注册。没有通用根 `marketplace.json`，以免发现优先级选中另一平台的包。

| 宿主 | 仓库发现入口 | 指向的目录 |
| --- | --- | --- |
| Codex | `.agents/plugins/marketplace.json` | `dist/codex/planweft/` |
| Claude Code | `.claude-plugin/marketplace.json` | `dist/claude/planweft/` |
| Cursor | `.cursor-plugin/marketplace.json` | `dist/cursor/planweft/` |
| Copilot CLI | `.github/plugin/marketplace.json` | `dist/copilot/planweft/` |
| Factory / Droid | `.factory-plugin/marketplace.json` | `dist/factory/planweft/` |
| CodeBuddy | `.codebuddy-plugin/marketplace.json` | `dist/codebuddy/planweft/` |

实际注册 ID 以宿主列表为准：Droid 的注册名还取决于来源目录、仓库和 pin，不能直接从 JSON 的 `name` 推断。Git marketplace 发布必须同时包含 catalog 和被引用的目录；单独托管 JSON 不会让相对路径文件自动可下载。Cursor 使用原生 UI，不能由 catalog 的存在推导出通用管理 CLI。

## 14 个平台的包形状与分发渠道

下表描述 0.3.0 已生成的入口及采用的渠道；原生入口存在不表示真实宿主安装或事件执行已经通过。实际状态见后面的验证矩阵。

| 平台 / `host` | 包内主要入口 | 分发与更新设计 | 官方依据 |
| --- | --- | --- | --- |
| Codex / `codex` | `.codex-plugin/plugin.json`、Skills、hooks | Git marketplace；刷新来源、重新安装、新会话；hooks 信任独立处理 | [plugins](https://developers.openai.com/codex/plugins/)、[hooks](https://learn.chatgpt.com/docs/hooks) |
| Claude Code / `claude` | `.claude-plugin/plugin.json`、Skills、commands、hooks | Git marketplace；市场刷新与插件更新分开；重载或新会话生效 | [marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) |
| Pi / `pi` | 根 `package.json`、`SKILL.md`、TypeScript Extension | npm `pi-package` 一起分发 Skill 与 Extension；本地路径可原位引用；固定版本通过换 pin 升级 | [packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md) |
| OpenCode / `opencode` | 根 npm `package.json`、预编译 `dist/index.js`、Skills、loader 模板 | V1 npm 或本地包；插件与独立发现的 Skill 配对；换版本并重启，不要求用户编译 | [plugins](https://opencode.ai/docs/plugins/)、[Skills](https://opencode.ai/docs/skills/) |
| Hermes / `hermes` | 根 `plugin.yaml`、`__init__.py`、`skills/project-docs/` | 包根 Git 发布树与完整 SHA；Skill 从同提交复制并配对；当前原生安装被宿主扫描拒绝 | [plugins](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins/) |
| Cursor / `cursor` | `.cursor-plugin/plugin.json`、Skills、hooks | 原生本地插件与 Marketplace/团队 Git 入口；刷新和更新由 UI 管理 | [plugins](https://cursor.com/docs/plugins) |
| Gemini CLI / `gemini` | 根 `gemini-extension.json`、Skills、`hooks/hooks.json` | 包根 `release/gemini` Git 分支；原生 Extension 显式跟踪分支更新 | [reference](https://geminicli.com/docs/extensions/reference/)、[releasing](https://geminicli.com/docs/extensions/releasing/) |
| Copilot CLI / `copilot` | 根 `plugin.json`、Skills、`hooks.json` | 原生 marketplace 与 plugin 更新；本地 path 源原位加载；CLI 结果不覆盖 IDE/云端能力 | [CLI reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference) |
| Mastra Code / `mastracode` | `.mastracode/skills/` 与独立 hooks 配置 | 完整 Skill 目录加按需合并的 hooks；显式更新本插件管理的文件 | [configuration](https://code.mastra.ai/configuration) |
| Kiro / `kiro` | 根 `plugin.json`、Skills、配套脚本 | Skill-only Power；IDE 安装与更新，CLI v3 发现 IDE 已安装 Power | [installation](https://kiro.dev/docs/powers/installation/)、[CLI v3](https://kiro.dev/docs/cli/v3/new-features/#powers-auto-pickup) |
| Continue / `continue` | `.continue/skills/project-docs/`、可选 prompts | 完整 Skill 目录；固定 checkout 或手工更新，无独立包 updater | [Skill loader](https://github.com/continuedev/continue/blob/main/extensions/cli/src/util/loadMarkdownSkills.ts) |
| Factory / `factory` | `.factory-plugin/plugin.json`、Skills | 原生 Git marketplace 与 plugin 更新；本版只注册 Skill | [plugins](https://docs.factory.ai/harness/plugins) |
| CodeBuddy / `codebuddy` | `.codebuddy-plugin/plugin.json`、Skills | 原生 Git marketplace 与 plugin 更新；版本递增并重载；本版只注册 Skill | [reference](https://www.codebuddy.ai/docs/cli/plugins-reference)、[marketplaces](https://www.codebuddy.ai/docs/cli/plugin-marketplaces) |
| 通用 Agents / `agents` | `.agents/skills/project-docs/` | 完整 Skill 放入所选宿主发现目录；可选第三方 Skills 安装工具，无通用 runtime 或 updater 保证 | [Agent Skills](https://agentskills.io/specification) |

## 包内资源与项目状态分开

脚本、模板和语言资源从实际安装的插件或 Skill 目录解析；任务记录从目标项目解析。安装缓存不是项目目录，插件更新也不承担项目状态迁移。原生适配使用宿主给出的包根或等价定位方式，例如 Cursor 的 `CURSOR_PLUGIN_ROOT`、Copilot 的 `PLUGIN_ROOT`、Gemini 的 `${extensionPath}` 和 OpenCode 的 `import.meta.url`。

主入口保持 `project-docs`，辅助命令使用 `pw-`，OpenCode 工具使用 `pw_`。Codex/Claude 保留其支持的语言入口布局与调用策略；采用可移植 Skill 布局的平台把语言变体放入主 Skill 的 `references/language-variants/`，用 `GUIDE.md` 作为显式读取资源，避免递归扫描重复发现主 Skill。Pi 同样携带语言资源；复制完整主 Skill 时，这些资源必须一起保留。

运行时保留 `PLAN_ID`、`PWF_*`、`PLANNING_DISABLED` 及 PWF 磁盘协议；Kiro 延续 `.kiro/plan` 平台布局。三文件、attestation、ledger 和长期文档不由安装器删除或改写。自动恢复只读取项目文件；会话历史读取仍要求显式调用。多 Agent 沿用一个计划 owner、worker 各自记录的规则，独立任务绑定不同计划或 worktree；本插件使用宿主已有 Agent 能力，不增加统一调度服务。

## hooks 以原生能力为边界

默认使用提醒模式，显式 autonomous/gated 行为受各宿主实际能力限制。Skill 发现、hook 定义合法、实际执行、上下文送达和继续执行是不同层次，不能相互代替。

| 平台或类型 | 本版集成 | 能力边界 |
| --- | --- | --- |
| Codex | 原生会话、工具、压缩、权限与 Stop 事件；Windows launcher | 安装不自动授予 hooks 信任；有 launcher 不等于 Windows 已实测 |
| Claude Code | 生命周期 hooks；Python 快速路径与 Shell fallback | 插件与 standalone 路线不能重复启用执行 hooks |
| Pi | TypeScript Extension、命令、状态栏与缓存策略 | 执行模式须显式激活，继承原生续跑限制 |
| OpenCode V1 | 原生工具、上下文注入、压缩处理与 idle follow-up | V1 适配，不宣称兼容不同行为的 V2 协议 |
| Cursor | `sessionStart`、`postToolUse`、`stop` bridge | 脚本协议已测，真实 GUI 事件触发未测 |
| Copilot CLI | `sessionStart`、`postToolUse`、`agentStop` bridge | 提醒输出不含批准工具调用的 `permissionDecision: "allow"` |
| Gemini CLI | `SessionStart`、`BeforeAgent`、`AfterTool`、`PreCompress` bridge | PreCompress 的 `systemMessage` 是用户提示，不当作模型上下文注入 |
| Hermes | 原生 Python 插件与 `pre_verify` 集成 | 触发和次数受宿主限制；当前安装失败，不能声明运行通过 |
| Mastra Code | Skill 与独立 hooks 配置 | 按需合并配置，不覆盖已有项目 hooks |
| Kiro、Continue、Factory、CodeBuddy、通用 Agents | Skill、Power 或目录发现 | 不由安装包装推导出完整执行 hooks 或原生停止门禁 |

读取、诊断和宿主规划模式不应初始化或改写项目记录；项目规则与用户范围始终优先。Cursor、Gemini、Copilot、Mastra 的部分继承行为仍以根 `task_plan.md` 为中心，命名计划和只读支持以对应实现与验证为准。严格只读或需要完全关闭时，使用宿主的禁用机制；`PLANNING_DISABLED=1` 仅在已验证的适配路径上作为充分开关，不承诺识别所有自然语言只读请求。attestation 不是人工批准，gated 检查也不是正确性证明。

同一会话只启用一套规划插件的执行 hooks。doctor 及安装说明用于发现可检测的重复来源；本插件不自动卸载原版 PWF。hooks 私有缓存、安装缓存和项目记录分别验证。

## 更新属于宿主生命周期

更新依次涉及来源、安装内容、当前进程或会话、信任与项目状态。市场刷新只更新来源信息；是否替换安装内容由宿主决定，替换文件也不保证当前会话已重载。Claude/CodeBuddy 等缓存依赖插件版本，发布时需要递增版本。

默认由用户显式更新。固定版本通过选择新版本或提交升级；自动更新只引用宿主自己的设置。无原生 updater 的 Skill 目录通过固定 checkout 或完整替换受管目录更新，清理旧版遗留并保留用户修改。插件回退不会回退任务中修改的项目文档。

Pi 把 Skill 与 Extension 打进同一个包。OpenCode 的插件和独立 Skill 记录相同版本、来源及内容摘要。Hermes 同样要求配对，但不虚构 `skills install --ref`：可复现路线从同一 SHA checkout 复制完整 Skill；Skills Hub 跟踪默认分支的路线不能保证与插件原子升级。

发布准备器为 Gemini/Hermes 输出以安装文件为根的 Git 分支树。Gemini 需要根 Extension manifest；Hermes 安装器支持子目录，但提取后不保留 `.git`，因此本仓选择包根发布树保留仓库元数据。Gemini 跟踪 `release/gemini`，Hermes 使用 `release/hermes` 树的完整提交 SHA；后续准备可承接先前 Git 历史。

这些是已实现的本地发布准备能力。Git URL 和 npm 身份需要发布者显式提供，当前仓库没有声称已上线的安装地址。准备输出不执行 push、npm publish、市场上架或个人全局安装。具体操作及旧安装身份迁移见安装指南：[简体中文](installation.md) | [English](installation.en.md)。

## 已验证范围

以下汇总 2026-09-08 的既有 0.3.0 验证记录，本次双语文档调整未重跑真实宿主或扫描器。14 个目录在该轮通过静态与构建一致性检查；“本地生命周期”指安装 A → 更新 B → 回退 A → 卸载，包含新增、修改和删除文件，不等于远程已发布 Git/npm 渠道验证。

| 平台 / 实测版本 | 协议或发现证据 | 原生安装 | 本地生命周期 | 实际加载范围 |
| --- | --- | --- | --- | --- |
| Codex 0.153.4 | Passed，真实 `skills/list` | Passed | Passed，重新安装完成更新 | Passed，真实 exec + 本地合成响应验证信任、注入、新会话恢复与禁用 |
| Claude Code 2.1.263 | Passed，结构与继承 hook 协议 | Passed | Passed；卸载后可留 orphan cache | Not Run，未认证模型会话 |
| Pi 0.85.1 | Passed，Extension 54 tests | Passed，实际 npm tarball | Passed | Not Run，未在模型会话验证 Extension 激活 |
| OpenCode V1 1.18.29 | Passed，真实 debug 发现三项 `pw_` 工具及唯一主 Skill | Passed | Passed，本地包与新进程 | Passed，debug 加载并直接执行工具；模型调用与会话内 reload 为 Not Run |
| Gemini CLI 0.58.0 | Passed，四事件脚本协议 | Passed | Passed，保留信任/安装确认 | Not Run，未认证模型会话 |
| Copilot CLI 1.0.83 | Passed，原生输出协议 | Passed | Passed；本地源原位加载，卸载禁用发现，源目录保留 | Not Run，未认证模型会话 |
| CodeBuddy 2.147.0 | Passed，Skill/catalog | Passed | Passed；卸载后可留 orphan cache | Not Run，未认证模型会话 |
| Factory Droid 0.213.0 | Passed，实际安装元数据 | Passed | Passed，核对真实 `installPath` | Not Run，未认证模型会话 |
| Hermes 0.21.1 | Passed，包根与资源契约 | **Failed**，默认 Plugin Guard 拒绝 | Not Run | Not Run |
| Cursor | Passed，三事件脚本协议 | Not Run，GUI/账号不可用 | Not Run | Not Run |
| Kiro | Passed，Power/Skill 与缓存脚本路径契约 | Not Run，GUI 不可用 | Not Run | Not Run |
| Continue | Passed，完整 Skill/目录静态 | Not Run | Not Run | Not Run |
| Mastra Code | Passed，静态与禁用协议 | Not Run | Not Run | Not Run |
| 通用 Agents | Passed，标准目录静态 | Not Run，未指定宿主 | Not Run | Not Run |

八个可安装宿主还核对了三文件、用户笔记、批准 spec、已接受 ADR 和既有 reproduction，生命周期前后内容一致。原生卸载与缓存物理删除分别记录；临时测试 profile 最终清理不等于宿主已清空 orphan cache。

Hermes 使用官方提交 `9fd44b4dfc44138b9e5d5689acb56c438364ff7b`，最终目录安装被默认扫描器判为 dangerous，报告 **41 findings**；初次运行是 42。测试没有关闭扫描器或改用手工发现路径把失败记为通过。

全部实测在 Linux x86_64 隔离配置下进行，没有使用个人认证或调用付费模型。Windows、macOS、GUI 安装、远程发布渠道、新版真实模型维护和冷读试用为 **Not Run**。Codex 合成响应证明 hook 送达，OpenCode debug 证明加载与直接执行，两者都不证明模型语义质量。

完整复现、原始日志及限制见 [REP-0006（工程记录，中文）](reproduction/0006-native-distributions.md)。设计契约见 [SPEC-0004（工程记录，中文）](specs/0004-native-distributions.md) 与 [ADR-0007（工程记录，中文）](adr/0007-native-distributions.md)。旧 0.2.0 记录保留为历史证据，不替代 0.3.0 分发验证。

RC4 补充：Codex/Claude 公开 Git 市场的安装、同提交刷新、缓存内容核对、卸载和注销 Passed；未调用模型，不表示 Git 跨版本升级已验收。Pi 完成态计划的 parity 注入和新会话恢复复验 Passed；进行中显式执行循环另有停止及上限证据，不能据完成态探针宣称进行中只读恢复。Pi 首次维护的主计划阶段/错误摘要不一致，独立语义检查该项 Failed；后续按独立反馈纠正两项记录并通过新冷读，原失败保留。这条明确反馈路线不单独证明自动 Skill 加载或自动触发审查。

资源与隔离补充：测试器在快照读取前剪枝安装缓存，并限制容器 CPU、RAM、Swap、进程与 tmpfs。Claude/Pi/OpenCode 的同 HOME 实测中，更新/移除 A 保持 B 不变；Codex/DSH 拒绝不支持的项目 scope 且无写入。这证明隔离，不证明被移除侧所有原生缓存均消失。Claude Pro 实际读取中文 Skill 后仍未采用 PWF，中断的外层运行保持 Incomplete、冷读 Not Run；Flash 失败同样保留。


当前候选 RC10 已通过三系统 CI、OIDC 及官方归档字节验证；但 Claude 独立维护语义 Failed，Pi 原生相对路径触发 doctor 回归且维护模型未启动。RC11 修复在开发中。OpenCode 的具体模型直连授权已补齐；五宿主严格门槛未通过，正式 0.4.0 未发布。
