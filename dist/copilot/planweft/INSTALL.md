[简体中文](INSTALL.md) | [English](INSTALL.en.md)

> 当前安装包：**copilot**。请选择本文对应宿主的安装章节。

## 统一安装器（0.4.0 候选）

唯一 npm 包是 `planweft`。下列远端命令须在对应版本发布后执行；当前验收状态以仓库发布记录为准。
默认安装完整原生集成，项目级为默认 scope。仅安装 Skill 必须显式 `--skill-only`；不会因此注册插件 hooks。

```bash
npx planweft@0.4.0-rc.3 add -a claude -a pi
npx planweft@0.4.0-rc.3 add -a codex --global
npx planweft@0.4.0-rc.3 add -a opencode --skill-only --symlink
npx planweft@0.4.0-rc.3 list
npx planweft@0.4.0-rc.3 doctor
npx planweft@0.4.0-rc.3 update -a pi
npx planweft@0.4.0-rc.3 remove -a pi
```

| 参数 | 默认值 | 作用 |
| --- | --- | --- |
| `-a / --agent` | 交互选择 | 可重复指定本文平台标识；非交互调用必须提供 |
| `--project / --global` | project | 项目级或用户级；宿主不支持时拒绝，不悄悄升级范围 |
| `--skill-only` | 关闭 | 安装完整、无其他宿主执行 frontmatter 的便携 Skill |
| `--copy / --symlink` | 优先链接 | 自动模式链接失败时报告复制；显式 symlink 失败则报错 |
| `--dsh-profile NAME` | headless | DSH 完整集成使用的用户级 profile；更新沿用已安装记录 |
| `--dry-run` | 关闭 | 只显示选择和路径，不安装、不写状态 |
| `--source FILE.tgz` | 精确 npm 版本 | 本地验收的 npm 包，身份/版本必须与正在运行的 CLI 一致 |

Pi 项目级包操作遵循原生信任检查；遇到未信任项目时，可显式追加 `--approve-pi-project`，仅为本次 Pi 命令传入 `--approve`。它会信任该项目的本地文件，不默认开启，也不改变其他宿主的信任。

平台标识：`codex claude pi opencode hermes cursor gemini copilot mastracode kiro continue factory codebuddy agents dsh`。
Node.js 22+；建议使用 Node.js 24 LTS。运行脚本还按平台需要 Python 3、Bash 或 PowerShell。

项目版本存储在 `.planweft/versions/`，安装记录在 `.planweft/installations.json`；用户级使用
`$XDG_DATA_HOME/planweft`（默认 `~/.local/share/planweft`），Windows 使用 LocalAppData。
`PLANWEFT_HOME` 可覆盖用户级存储目录，不能改变插件的原生 scope。不要提交项目 `.planweft/`。
每个精确版本包含 npm 解析的依赖和完整目录，不链接 npx 临时缓存。

`update` 使用当前执行的 CLI 版本，指定旧版本的 CLI 执行 update 即回退。已安装的 copy/symlink 和
skill-only 选择会保留。切换完整插件与 Skill-only 须先 remove 再 add。用户修改、外来文件、
重复规划插件或完整性异常会停止覆盖；`doctor` 报告实际状态。卸载保留版本存储供回退使用。
安装中断可能保留 `.operation-lock`；确认没有正在运行的安装操作、检查记录和现场后才手动移除该空锁目录。

CLI 管理市场按 host/scope 哈希独立命名，公开 Git 市场名称仍是 `planweft`。市场注册可能是用户级，
项目插件启用是另一项原生操作；安装记录分别保存结果。Codex、Copilot、Gemini 完整集成不提供项目级安装。
原生插件缓存依宿主管理，copy/symlink 只描述 CLI 管理的组件。Pi 使用完整本地包，OpenCode 使用本地 loader
与配对 Skill；不得同时从另一 npm/原生渠道加载同一插件。GUI 和 Mastra hooks 合并记录为 manual，不能视为已安装。
Hermes 默认扫描未通过，不提供绕过开关。Gemini CLI 管理的版本替换暂用 remove/add，原生 Git 渠道仍可原生 update。

从旧 `program-design`、`personal` 或 `program-design-local` 身份迁移：先检查并通过原安装渠道移除旧执行 hooks，
再安装 PlanWeft；主 Skill 仍为 `$project-docs`，辅助命令从 `pd-` 改为 `pw-`、工具从 `pd_` 改为 `pw_`。
不会自动卸载旧插件或原版 PWF。项目计划、批准需求、用户改动及 PWF 状态格式保持不变。

# PlanWeft 0.3.0 安装、更新与卸载

本版直接交付 `dist/<host>/planweft/`，不生成 ZIP。14 个 host 是 `codex`、`claude`、`pi`、`opencode`、`hermes`、`cursor`、`gemini`、`copilot`、`mastracode`、`kiro`、`continue`、`factory`、`codebuddy`、`agents`。选择一个宿主的完整目录；不要把不同平台合并安装。

以下 `/abs/repo` 是本源码仓库根，`/abs/package` 是选定的 `dist/<host>/planweft`，`/abs/project` 是目标项目，均需换成实际绝对路径。仓库包含六种平台各自识别的 marketplace catalog，名称均为 `planweft`。**marketplace 注册源使用 `/abs/repo`**；平台目录是插件 payload，不能一律用作 marketplace。只有实际包含自有 catalog 的独立包才支持额外的目录注册路线。

这些步骤描述交付接口和官方支持，不代表每个宿主及操作系统已实测通过。实际验证结果单独记录。当前未提供可确认已发布的 Git/npm 地址；所有 `REPOSITORY_URL`、`OWNER/REPO`、`@scope/...` 都是发布完成后才能替换使用的参数。

## 安装前与更新原则

从源码构建和核对：

```bash
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
```

普通构建使用 Python 3 标准库和仓库内固定输入；不会安装宿主、编译 TypeScript、修改个人配置或执行发布。`dist/manifest.json` 登记目录清单、文件摘要与执行位；`--verify` 同时检查遗漏、额外文件与权限漂移。已经取得完整发行目录的用户直接按所选宿主安装。

保留全部脚本、模板、references、LICENSE、UPSTREAM.json 与隐藏目录。复制目录时不要只复制 `SKILL.md`，也不要用会遗漏隐藏文件的 `*`。已有同名目录先保存本地修改，再替换本插件拥有的完整目录，清除旧版遗留文件；共享配置只合并或删除本插件条目。安装、更新和卸载均保留项目计划、attestation、ledger 和长期文档。

默认采用显式更新：先取得新源码或刷新原生 catalog，再更新插件，最后按宿主要求重载。固定版本或 SHA 不会自行跨越到下一版本。需要持续更新时使用下述原生 Git/npm 来源；本地复制只能在明确替换后生效，本地路径引用则依赖来源目录长期保留。没有统一后台 updater。

只启用一套规划执行 hooks。安装 PlanWeft 不会卸载 PWF；检查旧的独立 Skill、项目 hooks 与其他来源的同名插件。先验证 `project-docs` 实际被读取和当前计划路径，再在已授权维护任务中初始化计划。安装成功、当前会话加载、hooks 信任是不同状态。

Shell 路线要求宿主能找到所用解释器和 Python 3；Windows 要使用对应宿主支持的 PowerShell/launcher 配置。保留 `.sh` 执行位；位于 `noexec` 文件系统的手工辅助脚本用明确的 `sh`/`bash` 调用。0.2.0 验证曾发现 uutils `mkdir` 0.8.0 不能可靠支撑并发目录锁，GNU `mkdir` 9.7 对照通过；该历史环境限制不因包装变化而消失。不要在已知不可靠的环境并发维护同一计划。

## Codex

仓库 `.agents/plugins/marketplace.json` 指向 Codex 包；`plugins/planweft/` 是保留的兼容镜像，不是另一套手工维护源码。

```bash
codex plugin marketplace add /abs/repo
codex plugin add planweft@planweft
codex plugin list
```

更新先取得新仓库内容并验证分发，再执行：

```bash
codex plugin marketplace upgrade planweft
codex plugin remove planweft@planweft
codex plugin add planweft@planweft
```

新会话显式使用 `$project-docs`。本路线不使用其他宿主的 `--scope` 参数。在 `/hooks` 检查并信任当前定义；更新后定义摘要变化时重新审查。完整插件以 `PLUGIN_ROOT` 定位资产，单独复制到全局 Skills 不会注册插件 hooks。[官方 hooks 文档](https://learn.chatgpt.com/docs/hooks)

卸载用 `codex plugin remove planweft@planweft`，再用 `codex plugin list` 核对。0.2.0 来源可能是 `planweft@personal` 或 `planweft@planweft-local`；按列表中的实际旧 ID 移除，再安装新 ID，避免重复 hooks。只在没有其他插件依赖时移除旧 marketplace。

## Claude Code

使用仓库 `.claude-plugin/marketplace.json`。以下 CLI 示例选择 user scope；项目共享用 `project`，只对当前本地项目生效用 `local`。

```bash
claude plugin marketplace add /abs/repo
claude plugin install planweft@planweft --scope user
claude plugin list
```

更新和卸载保持安装时的 scope：

```bash
claude plugin marketplace update planweft
claude plugin update planweft@planweft --scope user
# To uninstall:
claude plugin uninstall planweft@planweft --scope user
```

安装/更新后按提示 `/reload-plugins` 或新建会话，核对 `/planweft:project-docs`。单次开发可用 `claude --plugin-dir /abs/repo/dist/claude/planweft`，不与长期安装同时启用。Git marketplace 发布后可将注册源换成真实仓库；每次发布需要递增插件版本以刷新缓存。默认不启用 marketplace 自动更新。[官方 marketplace](https://code.claude.com/docs/en/plugin-marketplaces)、[插件管理](https://code.claude.com/docs/en/discover-plugins)

## Pi

`dist/pi/planweft` 本身是 `pi-package`；根 `package.json` 声明 Skill 和 Extension。在目标项目执行：

```bash
pi install -l /abs/repo/dist/pi/planweft
pi list
```

`-l` 写项目 `.pi/settings.json`；省略则写用户 `~/.pi/agent/settings.json`。本地路径只记录引用、不复制文件，因此来源目录须保留；更新该目录后 `/reload` 或重启。卸载使用 `pi remove -l /abs/repo/dist/pi/planweft`，用户安装省略 `-l`。

npm 发布完成后，使用唯一的无 scope 包：

```bash
pi install -l npm:planweft@0.4.0-rc.3
pi install -l npm:planweft@NEW_VERSION
# Remove the project installation:
pi remove -l npm:planweft@NEW_VERSION
```

固定版本用 `npm:planweft@VERSION`，升级时再次 `pi install -l` 指定新版本。当前官方 `pi update` 单独执行更新 Pi 本体；`pi update --extensions` 更新包，定向更新如上。npm/Git 安装由 Pi 处理包依赖；本地包不要求用户运行开发测试。[官方 packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md)

加载后检查 `/skill:project-docs` 和 `/pw-plan-status`。显式 `/pw-plan-execute` 才启用注入与执行循环，`/pw-plan-execute reset` 恢复被动状态。配置名仍为 `planningWithFiles`，`PWF_MODE` 支持 `auto`、`parity`、`cache-safe`、`notify`；执行循环受平台限制。

## OpenCode V1

`dist/opencode/planweft` 是带预编译 `dist/index.js` 的 npm 包，本地名为 `opencode-planweft`。普通安装不需要编译 TypeScript；本地复制路线需在插件自己的目录安装运行依赖。

1. 将完整包复制到项目 `.opencode/packages/opencode-planweft/`。
2. 在复制后的独立包目录执行 `npm ci --omit=dev --ignore-scripts`；只安装运行依赖，不修改业务项目根 package.json，也不执行 `npm run build`。
3. 将包内完整 `skills/project-docs/` 复制到项目 `.opencode/skills/project-docs/`。
4. 在项目 `.opencode/plugins/planweft.ts` 写入以下 loader；包内 `install/loader-template.ts` 也提供绝对 file URL 模板。二者选一种，不重复注册。

```typescript
export { PlanningWithFiles } from "../packages/opencode-planweft/dist/index.js"
```

需要命令时将包内 `commands/pw-*.md` 复制到 `.opencode/commands/`。用户 scope 改用 `~/.config/opencode/` 下同样的 `packages/`、`plugins/`、`skills/`、`commands/` 层级。重启后核对 `project-docs`、`pw_init` / `pw_status` / `pw_check`，以及可选 `/pw-pwf`、`/pw-pwf-status`。

本地更新时替换完整独立包和 Skill/命令副本，在独立包重新安装锁定运行依赖后重启。卸载只移除本次的 loader、独立包、Skill 和命令，保留共享 `.opencode`。插件的资产来自包内目录；目标项目是计划写入位置，二者不能互相替代。

npm 发布完成后，原生配置可使用 `"plugin": ["planweft@VERSION"]`；升级显式改成新版本并重启，卸载删除该配置项及手工安装的 Skill/命令。沿用既有配置只增删本插件条目。该路线与手工 loader 二选一。npm 路线的运行依赖由宿主包管理器安装。npm 插件代码的加载不等于 Skill 发现；仍将相同版本完整 `skills/project-docs/` 部署到上述发现目录。[官方 plugins](https://opencode.ai/docs/plugins/)、[Skills](https://opencode.ai/docs/skills/)

这是 V1 适配器。gated 通过 `session.idle` 后的 follow-up 接续，不能阻止宿主完成原回合；Claude Skill frontmatter hooks 不是 OpenCode 的执行入口。

## Hermes

**已记录的验证限制（2026-09-08）**：官方 Hermes v0.21.1、源码提交 `9fd44b4dfc44138b9e5d5689acb56c438364ff7b` 在独立配置、无认证环境中可运行插件管理，但 0.3.0 交付验证中的 Git 安装被默认 Plugin Guard 拒绝：初次为 dangerous、42 条 findings；修正语言资源路径后的最终目录复验仍为 dangerous、41 条 findings。两次原生安装均记为 **Failed**；更新、回滚和卸载记为 **Not Run**，因为安装未完成。这些数字是当时包内容的历史观察；本次双语文档调整没有重新运行 Hermes 扫描。保留原始拒绝证据，不关闭扫描、不改变文本来规避规则，也不通过手工复制将拒绝改写为通过。以下是官方支持的发现布局和管理接口，尚不能作为本包当前可成功原生安装的承诺。

将 `dist/hermes/planweft/` 整体复制到当前 Hermes profile 的 `<HERMES_HOME>/plugins/planweft/`，再将其中 `skills/project-docs/` 完整复制到**同一个** `<HERMES_HOME>/skills/project-docs/`。用户根以宿主配置为准，不能假定所有 OS 都是 `~/.hermes`。

```bash
hermes plugins enable planweft
hermes plugins list
```

重新启动 Hermes 后检查 Skill 与原生命令。插件启用与 capability grants 分别处理，更新增加能力时由宿主再次询问。手工复制的本地包更新方式是替换以上两个本插件目录；`plugins update` 不负责拉取任意本地副本。卸载使用 `hermes plugins remove planweft`，并移除本次单独复制的 Skill。

本项目远端发布选择让 `release/hermes` 分支树根直接包含 `plugin.yaml` 和 `__init__.py`。当前官方安装器虽支持 Git 子目录，但搬出子目录后不保留仓库根 `.git`，未固定安装的 `plugins update` 因而不能在其中 pull；包根发布避免这一问题。Hermes 的 `--ref` 只接受完整 40 位不可变 SHA：

```bash
hermes plugins install OWNER/REPO --ref FULL_40_CHARACTER_SHA --enable
# Upgrade the pinned plugin: select a new release-branch commit explicitly
hermes plugins install OWNER/REPO --force --ref NEW_FULL_40_CHARACTER_SHA --enable
```

`hermes plugins update planweft` 拒绝移动 pinned plugin。`hermes skills install` 不提供同等 `--ref` pin；可复现安装应从相同 SHA 的独立 checkout 复制 `skills/project-docs/`，记录 Skill 与 plugin SHA 配对，升级时同步替换。不能用一个未固定的 Skill Hub 导入代替此配对。[官方 plugin 安装、更新与卸载](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins/)

项目级插件另需 `HERMES_ENABLE_PROJECT_PLUGINS=1`，从项目启动并明确启用；Desktop 使用用户级路线。`pre_verify` 的接续受宿主触发条件与次数限制，不等于原生 Stop 拒绝。

## Cursor

本包使用 `.cursor-plugin/plugin.json`。本地开发安装将完整 `dist/cursor/planweft/` 放到 `~/.cursor/plugins/local/planweft/`，随后 Developer: Reload Window 或重启，在 Customize 检查。更新时替换该完整目录；卸载时移除本插件目录并重载。不要另复制旧项目 hooks 造成重复执行。

团队 Git 分发通过 Dashboard 导入仓库，读取仓库 `.cursor-plugin/marketplace.json`，由 Customize/Marketplace UI 安装与管理；团队 scope 与管理员策略以实际界面为准。显式 Refresh 后检查新版本；Auto Refresh 需要 GitHub App，公开市场上架需要官方审核。尚未发现统一的 `cursor plugin marketplace add/update` CLI，不能套用 Claude 命令。[官方 plugins](https://cursor.com/docs/plugins)

## Gemini CLI

根 `gemini-extension.json`、`skills/`、`hooks/hooks.json` 组成 Extension；原生 `${extensionPath}` 定位包内 hooks/资产，目标项目由事件提供。

```bash
gemini extensions install /abs/repo/dist/gemini/planweft
gemini extensions list
```

本地安装后保留来源目录。取得新版本后 `gemini extensions update planweft`，版本判断依赖本地源 manifest 变化；开发时可用 `gemini extensions link /abs/repo/dist/gemini/planweft`。本地 source 不接受 `--ref` 或 `--auto-update`。新会话核对 `/skills list`；卸载用 `gemini extensions uninstall planweft`。

Git Extension 要求 manifest 位于仓库根，没有通用 Git 子目录安装参数。本项目通过专用 `release/gemini` 分支提供该布局，真实发布后：

```bash
gemini extensions install REPOSITORY_URL --ref release/gemini
gemini extensions update planweft
```

该分支来源在显式 update 时跟踪分支的新提交；若改用不可变 ref，就不会自动跨版本。默认不加 `--auto-update`。安装通常为用户级，enable/disable 可按宿主 workspace/user scope 控制；卸载与禁用不同。[官方 Extension reference](https://geminicli.com/docs/extensions/reference/)、[发布与更新](https://geminicli.com/docs/extensions/releasing/)

## GitHub Copilot CLI

仓库 `.github/plugin/marketplace.json` 引用带根 `plugin.json` 的 Copilot 包：

```bash
copilot plugin marketplace add /abs/repo
copilot plugin install planweft@planweft
copilot plugin list
```

Git marketplace 更新与卸载：

```bash
copilot plugin marketplace update planweft
copilot plugin update planweft
# Uninstall:
copilot plugin uninstall planweft
```

本地目录 marketplace 的 path 插件原位加载，更新源目录后 `/restart` 或新会话，不必强求复制缓存更新。Copilot CLI 1.0.83 的本地 path 卸载表现为禁用并保留源文件及 disabled 记录；不再使用整个来源时，再执行 `copilot plugin marketplace remove planweft` 移除其 listing。也可直接 `copilot plugin install /abs/repo/dist/copilot/planweft`；不要与 catalog 来源重复装。插件安装没有可类推的 project `--scope`，官方该参数用于文件/URL 的单 Skill 安装。检查当前用户/profile；CLI 结果不能推定 IDE/Coding Agent 也已通过。[官方 CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)

## Factory / Droid

仓库原生 catalog 是 `.factory-plugin/marketplace.json`。此版本提供 Skill-only 插件包装，未登记 Factory 执行 hooks。**Droid 的实际 marketplace 注册名来自来源路径/仓库及 pin，可能不同于 catalog 的 `name`。** 先查看实际名称：

```bash
droid plugin marketplace add /abs/repo
droid plugin marketplace list
```

下面 `REGISTERED_NAME` 必须替换成列表中的实际注册名：本地目录名为 `planweft` 时通常是 `planweft`；隔离验证的源目录名为 `source`，实际 ID 是 `planweft@source`。

```bash
droid plugin install planweft@REGISTERED_NAME --scope project
droid plugin list --scope project
# Explicit update:
droid plugin marketplace update REGISTERED_NAME
droid plugin update planweft@REGISTERED_NAME --scope project
# Uninstall:
droid plugin uninstall planweft@REGISTERED_NAME --scope project
```

用户安装改成 `--scope user`；更新/卸载 scope 保持一致。新会话检查 `project-docs`。marketplace add 要求 catalog 源，不能传裸插件目录；Git 发布使用包含 native catalog 与 payload 的完整仓库。Droid 0.213.0 已在隔离配置中通过本地目录 catalog 的安装、A→B 更新（新增/改动/删除文件）、回滚 A 与卸载；这是插件管理及当前缓存验证，不代表模型读取或远端 Git 已通过。[官方 plugins](https://docs.factory.ai/harness/plugins)

## CodeBuddy

仓库原生 catalog 是 `.codebuddy-plugin/marketplace.json`。此版本同样只登记 Skills，不声称 frontmatter hooks 自动执行。

```bash
codebuddy plugin marketplace add /abs/repo
codebuddy plugin install planweft@planweft --scope project
# Explicit update:
codebuddy plugin marketplace update planweft
codebuddy plugin update planweft@planweft --scope project
# Uninstall and preserve plugin data:
codebuddy plugin uninstall planweft@planweft --scope project --keep-data
```

scope 可选 `user`、`project`、`local`；保持更新/卸载 scope 与安装一致。用 `/reload-plugins` 或新会话检查。每次发布递增 plugin version 以避免缓存继续使用旧包；`/plugin` 可管理自动更新，但本方案默认不启用。Git catalog 比裸 HTTP JSON 更适合本仓相对目录 payload。[官方 reference](https://www.codebuddy.ai/docs/cli/plugins-reference)、[marketplaces](https://www.codebuddy.ai/docs/cli/plugin-marketplaces)

## Kiro IDE 与 CLI v3

`dist/kiro/planweft` 根 `plugin.json` 是 Skill-only Power。在 IDE 的 Powers → Add Custom Power 选择该**完整本地目录**；在 Powers 中检查已安装条目。Kiro CLI v3 会自动发现 IDE 安装的 Powers，无需额外复制 CLI 插件。[官方创建](https://kiro.dev/docs/powers/create/)、[安装](https://kiro.dev/docs/powers/installation/)、[CLI v3 自动发现](https://kiro.dev/docs/cli/v3/new-features/#powers-auto-pickup)

更新本地来源后使用 Power 的 Check for updates / Install updates；若当前版本的本地来源未检测到变化，卸载该 Power 后重新导入新目录。卸载在 Powers 管理界面完成，随后新建会话。官方安装页支持包含多个 Power 子目录的 Git 仓库；本仓远端布局可保留多个 host，但具体远端子目录选择交互尚未实测，本文不把 `tree/.../dist/...` URL 当作已验证安装语法。

当前官方 CLI/slash command 参考没有公开 Power 安装、更新、卸载命令，CLI 支持范围是 IDE 安装后的 auto pickup。[CLI commands](https://kiro.dev/docs/reference/cli-commands/)、[slash commands](https://kiro.dev/docs/reference/slash-commands/)

Power 不提供默认执行 hooks。只有获准创建项目记录并选择 Kiro 布局时，才从目标项目工作目录显式执行所加载 Skill 目录中的 `assets/scripts/bootstrap.sh`（Windows 对应 `.ps1`）。它按缺失文件创建 `.kiro/plan/` 三文件与 `.kiro/steering/planning-context.md`。资产路径以实际安装位置为准，不硬编码项目 `.kiro/skills`；已有其他任务计划或只读任务不再创建竞争计划。该布局不等于 canonical `.planning/<id>` 选择器。

## Continue、Mastra Code 与通用 Agent Skills

这三种路线保留完整 Skill/项目配置复制，未提供跨平台原生 marketplace updater。

| host | 安装映射 | 更新、生效和卸载 |
| --- | --- | --- |
| `continue` | 包内 `.continue/skills/project-docs/` → 项目或用户 `.continue/skills/project-docs/`；可选 `.continue/prompts/` 中本插件 prompt | 更新完整 Skill/prompt 副本后新会话；卸载只删除本插件路径。CLI `/skills` 检查，显式 `/skill-project-docs`；IDE prompts 与 CLI Skills 分开验证 |
| `mastracode` | `.mastracode/skills/project-docs/` → 项目 `.mastracode/skills/`；将包内 `.mastracode/hooks.json` 的本插件事件合并到目标 hooks.json | 替换 Skill 并审查 hooks 差异，`/hooks` 重载配置或新建会话；卸载只删除 Skill 和对应 hook 条目。用户级 Skill 可置于 `~/.mastracode/skills/`，不把项目相对 hooks 原样改为全局 |
| `agents` | `.agents/skills/project-docs/` → 项目或用户 `.agents/skills/project-docs/` | 所选宿主须支持该发现路径；替换完整副本并重新加载。卸载只移除该 Skill，没有通用 plugin/update 命令 |

Mastra Code 官方支持 `.mastracode/skills` 和 `.mastracode/hooks.json`，`/hooks` 可重新加载 hooks；`/update` 更新宿主本身，不是本插件更新器。[官方配置](https://code.mastra.ai/configuration)

Continue CLI 的 `/import-skill <url-or-name>` 是由模型协助下载复制的导入入口，不记录可持续更新的 package 来源，也不是版本锁定安装器。官方仓库目前声明停止主动维护；没有据此虚构统一 updater。可保留受版本控制的安装源，在显式更新 checkout 后替换副本。[官方 Skills loader](https://github.com/continuedev/continue/blob/main/extensions/cli/src/util/loadMarkdownSkills.ts)、[导入实现](https://github.com/continuedev/continue/blob/main/extensions/cli/src/tools/skills.ts)、[维护状态](https://github.com/continuedev/continue)

## 运行能力与恢复

目录、manifest 和原生安装命令解决分发问题，不使所有宿主生命周期等价。Cursor、Gemini、Copilot、Mastra 的部分继承行为仍以根 `task_plan.md` 为中心；命名计划、只读和关闭支持以对应实现与实际验证记录为准。需要完全关闭时使用宿主的禁用机制；`PLANNING_DISABLED=1` 只在相应实现已验证的路径作为充分开关。

更新失败时恢复上一份经验证的完整包，按同一 scope 重新安装/加载，重新检查 hook trust；不要将旧文件覆盖在新版目录上留下混合版本。安装包回滚不会自动回滚计划和文档，项目状态按任务差异单独处理。原 `PLAN_ID`、`PWF_*`、三文件、`.planning`、attestation、ledger 的格式保持兼容，没有通用状态迁移器。

## DeepSeek Harness（DSH）

提供原生 DSH bundle、完整 Skill 和官方 Claude command-hook 桥接。使用已验证的 DSH `0.1.2-rc.1`；原生插件管理还需要 `pnpm` 在 PATH 中。以下 npm 命令在候选版发布后可用。

完整集成是用户级 **profile** 配置；默认 `headless`，可显式选 `web`。安装器一次管理一个 DSH profile，更新沿用记录中的 profile，切换前先卸载。CLI 将原生来源链接到持久版本目录；这属于 DSH/pnpm 管理的链接，不受 CLI `--copy` 影响。启动该 profile 后，bundle 注册 Skill 与 hooks。

```bash
npx planweft@0.4.0-rc.3 add -a dsh --global --dsh-profile headless
npx planweft@0.4.0-rc.3 doctor -a dsh --global
npx planweft@0.4.0-rc.3 update -a dsh --global
npx planweft@0.4.0-rc.3 remove -a dsh --global
```

用户可直接使用 DSH 原生命令，来源为单一 npm 包；此路线独立于 PlanWeft CLI，不能混用所有权：

```bash
dsh plugin --profile headless add planweft@0.4.0-rc.3
dsh --profile headless --dump-config
dsh --profile headless "Use project-docs for this maintenance task."
dsh plugin --profile headless remove planweft
```

本地平台目录可使用 `dsh plugin --profile headless add file:/absolute/path/to/dist/dsh/planweft` 安装。原生包声明 `dsh.bundle.patch`；无需 marketplace。升级用所需精确版本的 `add`，回退同样安装旧版本，再开启新会话；不启用后台更新。卸载只移除 PlanWeft 的 profile 依赖和 bundle，保留 profile、用户其他设置及项目记录。

项目级仅安装 Skill：

```bash
npx planweft@0.4.0-rc.3 add -a dsh --skill-only
npx planweft@0.4.0-rc.3 doctor -a dsh
npx planweft@0.4.0-rc.3 update -a dsh
npx planweft@0.4.0-rc.3 remove -a dsh
```

用户级 Skill-only 在每个命令上添加 `--global`。`--copy`、`--symlink`、`--dry-run` 沿用统一安装器规则。
项目 Skill 位于最近 Git 根的 `.dsh/skills/project-docs/`；为保证安装记录与锁同属一个项目，必须从 Git 根执行；无 Git 时使用调用目录。
用户路径为 `$DSH_HOME/skills/project-docs/`，默认 `~/.dsh/skills/project-docs/`，支持原生 tilde 展开。
手工路线复制完整 `dist/dsh/planweft/skills/project-docs/`；CLI 不接管已有手工副本。同名 Skill 按 DSH provider 优先级选择。

运行资源按包内绝对路径定位，项目状态取每个会话 cwd。支持 SessionStart、UserPromptSubmit、PostToolUse 和 Stop；没有 PreCompact，PreToolUse 纯上下文会被官方桥接丢弃，故不注册该事件的提醒。默认 Stop 不强制继续，且 DSH 不展示 PWF 的 `systemMessage` 提醒；gated 使用官方 Stop 决策通道，完整模型续跑验收尚未进行。PWF 保留每次提示刷新计划的行为，不宣称 UserPromptSubmit 去重。
只读会话可在启动宿主时设置 `PLANNING_DISABLED=1`，关闭执行 hooks；保留 Skill 的只读规则。单会话只启用一个规划 hook 来源，安装器拒绝覆盖非自有的 PlanWeft profile 注册。

RC3 的 DSH hook 使用每次调用独立的私有临时缓存，因为 workspace-write 不允许写 HOME 缓存。原生桥接的 shell 适配绑定宿主 session ID，并用有界进程内状态去重 PostToolUse 提醒；执行仍交给原沙箱，不改权限或 Stop payload。Stop 计数与停滞 ledger 保留在选定计划中。上游 `pwf-prog` 跨调用缓存告警不跨隔离 hook 保留，不将其视为 DSH 上的进度回退保护。

Linux 原生安装/A-B 更新/回退/卸载与配置加载已验证；官方桥接加真实子进程的协议测试已验证注入、跨项目隔离、恢复及权限保持。这些不代表 DSH 模型会话或 Windows/macOS 已通过。

依据：[官方 Skill provider](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md)、[官方 hook bridge](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/hooks/hooks-claude-code/README.md)、[CLI profile](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/README.md)。

完整集成还检查 home/profile patch 中已知规划 hook 的文本线索，忽略整行注释；这是保守提示检查，不是执行后的配置解析，遇到提示需核对实际来源。Skill-only 不执行此 hook 重复检查。
