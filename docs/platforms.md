# 平台分发、安装与更新

Program Design 0.3.0 生成 14 个独立目录 `dist/<host>/program-design/`。目录可作为原生插件、Extension、Power、npm 包或完整 Skill 安装源；不再生成 ZIP。ZIP 是静态交付容器，本身没有来源追踪、版本选择或更新机制。持续更新依赖宿主识别的来源、可访问的新版本，以及宿主的安装缓存和重载流程。

完整命令与操作步骤见 [INSTALL.md](../overlays/program-design/install/INSTALL.md)。本页记录官方支持边界与本项目选择；“支持原生安装”不代表所有真实宿主、账号和 OS 已验证通过。0.2.0 的 [REP-0005](reproduction/0005-pwf-based-plugin.md) 是历史运行证据，不能作为 0.3.0 原生包装已经通过的证明。

## 官方渠道与本仓目录

| host | 本仓原生入口 | 本地安装与 scope | 持续更新与限制 | 官方依据 |
| --- | --- | --- | --- | --- |
| `codex` | `.codex-plugin/plugin.json`、Skills、hooks | 注册仓库 catalog，再 `codex plugin add program-design@program-design`；无类推的 scope flag | 显式 marketplace upgrade → plugin remove/add → 新会话；hooks 信任独立 | [Codex plugins](https://developers.openai.com/codex/plugins/)、[hooks](https://learn.chatgpt.com/docs/hooks) |
| `claude` | `.claude-plugin/plugin.json`、Skills、commands、hooks | 仓库 catalog 安装；user/project/local scope；`--plugin-dir` 可单次加载 | Git marketplace + 版本递增；显式 update 后 reload/new session | [marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) |
| `pi` | 根 `package.json`、Skill、TypeScript Extension | `pi install [-l] /abs/package`；本地路径原位引用 | 推荐 npm 包；`pi update npm:PACKAGE`；固定版本须换 pin；Git 不假设任意子目录直装 | [packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md) |
| `opencode` | 根 npm `package.json`、预编译 `dist/index.js`、Skills、loader 模板 | 项目或用户 plugins loader；独立包安装锁定运行依赖，Skill 分别部署 | 推荐 npm；配置固定包版本，显式改版本并重启；V1 适配，不声称 V2 实测 | [plugins](https://opencode.ai/docs/plugins/)、[Skills](https://opencode.ai/docs/skills/) |
| `hermes` | 根 `plugin.yaml`、`__init__.py`、`skills/project-docs/` | 官方支持同 profile plugin + Skill；本轮 Git 安装被宿主扫描拒绝 | 本项目选包根发布分支 + 完整 SHA，Skill 配对；当前原生安装 Failed，后续生命周期 Not Run | [plugins](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins/) |
| `cursor` | `.cursor-plugin/plugin.json`、Skills、hooks | 用户 `~/.cursor/plugins/local/`；团队通过 Customize/Marketplace UI | Dashboard Git import/Refresh；Auto Refresh 需 GitHub App；公开上架审核；无通用市场管理 CLI | [plugins](https://cursor.com/docs/plugins) |
| `gemini` | 根 `gemini-extension.json`、Skills、`hooks/hooks.json` | `gemini extensions install /abs/package`；本地目录或开发 link | Git 无通用 subdir 参数；专用 `release/gemini` 分支，install `--ref` 后显式 update 跟踪该分支 | [reference](https://geminicli.com/docs/extensions/reference/)、[releasing](https://geminicli.com/docs/extensions/releasing/) |
| `copilot` | 根 `plugin.json`、Skills、hooks | 原生 catalog 或直接本地目录；plugin 不套用单 Skill 的 project scope | 原生 marketplace update + plugin update；本地 path 源原位加载，`/restart`；支持 GitHub `OWNER/REPO:SUBDIR` | [CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference) |
| `mastracode` | `.mastracode/skills/` 与项目 hooks 配置 | 完整 Skill 复制、合并本插件 hooks | 显式 checkout/替换，`/hooks` 重载配置或新会话；`/update` 更新宿主本身 | [官方 configuration](https://code.mastra.ai/configuration)；运行适配来自固定 PWF |
| `kiro` | 根 `plugin.json`、Skills；Skill-only Power | IDE Powers 添加本地包；CLI v3 自动发现 IDE 已装 Power | IDE Check for updates；多 Power Git 仓库受支持，但具体远端子目录交互未实测；未发现公开 CLI 管理命令 | [installation](https://kiro.dev/docs/powers/installation/)、[CLI v3](https://kiro.dev/docs/cli/v3/new-features/#powers-auto-pickup) |
| `continue` | `.continue/skills/project-docs/`、可选 prompts | CLI 从项目/用户 Skill 目录发现；IDE prompts 单独验证 | 手工/checkout 更新；`/import-skill` 为模型协助导入，没有包 updater 或版本 pin | [loader](https://github.com/continuedev/continue/blob/main/extensions/cli/src/util/loadMarkdownSkills.ts)、[import](https://github.com/continuedev/continue/blob/main/extensions/cli/src/tools/skills.ts) |
| `factory` | `.factory-plugin/plugin.json`、Skills | `droid plugin install … --scope project/user` | 原生 Git marketplace update + plugin update；catalog 支持相对 payload、git-subdir；本版不注册 hooks | [plugins](https://docs.factory.ai/harness/plugins) |
| `codebuddy` | `.codebuddy-plugin/plugin.json`、Skills | `codebuddy plugin install … --scope project/user/local` | 原生 Git marketplace/update；版本必须递增；`/reload-plugins`；本版不注册 hooks | [reference](https://www.codebuddy.ai/docs/cli/plugins-reference)、[marketplaces](https://www.codebuddy.ai/docs/cli/plugin-marketplaces) |
| `agents` | `.agents/skills/project-docs/` | 复制到实际支持该约定的宿主发现目录 | 没有通用市场或 updater；不是保证所有 Agent 都能执行的 runtime | [Agent Skills 规范](https://agentskills.io/specification) |

Continue 官方仓库当前声明不再主动维护；该状态限制了后续官方能力演进的预期，不能把本项目手工适配描述成官方插件服务。[官方仓库](https://github.com/continuedev/continue)

## 六个独立 catalog

下面的路径均相对于**仓库根**，名称均为 `program-design`。这里的名称指 catalog 字段；Droid 等宿主的实际注册名还取决于来源目录/仓库与 pin，安装前以 marketplace list 的返回值为准。它们由同一 build 生成，但使用宿主各自的 schema；添加其中一种 marketplace 不会自动注册其他宿主。

| 宿主 | 仓库 catalog | payload |
| --- | --- | --- |
| Codex | `.agents/plugins/marketplace.json` | `dist/codex/program-design/` |
| Claude Code | `.claude-plugin/marketplace.json` | `dist/claude/program-design/` |
| Cursor | `.cursor-plugin/marketplace.json` | `dist/cursor/program-design/` |
| Copilot CLI | `.github/plugin/marketplace.json` | `dist/copilot/program-design/` |
| Factory | `.factory-plugin/marketplace.json` | `dist/factory/program-design/` |
| CodeBuddy | `.codebuddy-plugin/marketplace.json` | `dist/codebuddy/program-design/` |

有 CLI 的宿主注册 `/abs/repo`，Cursor 使用对应 UI。Git 发布必须同时包含 catalog 与所指 payload；只托管一个 HTTP JSON 不会让相对路径下的文件自动可下载。npm 渠道与 Gemini/Hermes 发布分支不是这六个 catalog 的别名。

## 发布准备与更新策略

默认本地目录可用，远端渠道需先完成真实发布。`scripts/prepare-native-release.py --output NEW_DIRECTORY` 准备审阅用输出；输出必须在仓库外且尚不存在；`--previous-release` 可承接上次 Git 历史。可选 `--repository-url` 和 `--npm-scope` 必须成对提供真实身份。仅准备目录不会推送、发布 npm 或安装到个人配置。npm 名称映射为 `@scope/program-design-pi` 与 `@scope/program-design-opencode`；未填身份时不输出已发布安装声明。完整流程见 [上游与分发维护](upstream-maintenance.md)。

Gemini 要求根 Extension manifest；Hermes 当前安装器支持子目录，但搬出子目录后不保留 `.git`，其未固定安装的原生 updater 会拒绝 pull。因此本仓采用同仓专用发布分支树。Gemini `--ref release/gemini` 支持显式更新分支；Hermes plugin 只使用完整不可变 SHA，更新时明确替换 pin。Hermes Skill 没有等价的 `--ref` 参数，使用同 SHA checkout 复制并记录配对，不依赖未固定 Skill 导入。

本地副本更新前保存修改、替换完整本插件目录并清理旧版遗留；路径引用更新后重载。原生插件缓存更新、当前会话加载、hooks trust、项目状态分别核验。默认不启用自动更新；如果用户以后选择宿主自带自动更新，固定来源和宿主许可仍然生效。

## 运行与验证边界

本轮独立验证：Droid 0.213.0 的本地目录 catalog 安装、A→B 文件增改删更新、回滚 A 和卸载通过；注册名采用列表返回值，不从 catalog 字段推断。Hermes v0.21.1 / `9fd44b4dfc44138b9e5d5689acb56c438364ff7b` 原生 Git 安装被默认 Plugin Guard 拒绝（dangerous，初次 42、最终目录 41 findings），安装 **Failed**，更新/回滚/卸载 **Not Run**。主要匹配包括文档中“host … $”命中 `dns_exfil`、模板的“Include enough source context”命中 `context_exfil`；这是扫描规则及文本匹配的观察，不将宿主拒绝改写为通过。保留原始结果，不关闭扫描或借手工发现路线绕过。两项均未调用模型或使用个人配置。

主入口统一为 `project-docs`，但生命周期能力保持各宿主差异。Pi 需显式 `/pd-plan-execute`；OpenCode V1 是 idle follow-up；Hermes 受 `pre_verify` 触发和次数限制；Kiro 是 Power/Skill 与其 `.kiro/plan` 布局；Factory/CodeBuddy 仅 Skill。安装包装不等于新增原生停止门禁。

安装与卸载不修改任务计划、attestation、ledger 或长期文档。多版本共存、旧 PWF hooks 和旧 marketplace ID 必须分别处理。实际验收应覆盖发现/缓存/更新回滚/当前会话加载/Skill 读取/事件执行，不以目录存在或 schema 通过代替真实运行。设计约束见 [SPEC-0004](specs/0004-native-distributions.md) 与 [ADR-0007](adr/0007-native-distributions.md)。

0.3.0 完整实测分层、具体 CLI 版本与失败原因见 [REP-0006 逐平台矩阵](reproduction/0006-native-distributions.md#逐平台验证矩阵)。构建静态检查覆盖全部 14 平台；Codex、Claude、Pi、OpenCode、Gemini、Copilot、CodeBuddy、Factory 的本地生命周期已有实测；远程已发布 Git/npm 渠道尚未运行。Codex 本地合成响应服务证明真实 hook 送达，OpenCode debug 证明真实工具/Skill 发现，两者都不代表已运行真实模型维护任务。
