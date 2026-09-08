# Program Design 0.2.0 平台安装说明

本版提供 14 个本地 ZIP，ZIP 摘要由随版本提供的 dist/manifest.json 登记。每包解压后根目录均为 `program-design/`；同名根目录只是一份安装源，不能把不同平台依次解压到同一目录。以下命令中的 `/path/to/package/program-design` 指所选包的解压根，`/path/to/project` 指目标项目，均须替换为实际绝对路径。

安装说明依据固定 PWF 源码和生成包检查编写；它不是各宿主已运行通过的声明。安装说明不宣称真实宿主或全部 OS 已通过；实际结果由版本验证记录 REP-0005 单独给出。

## 选包与解压

`program-design-0.2.0-<platform>.zip` 的后缀指定宿主。可选值是 `codex`、`claude`、`pi`、`opencode`、`hermes`、`cursor`、`gemini`、`copilot`、`mastracode`、`kiro`、`continue`、`factory`、`codebuddy`、`agents`；`agents` 仅提供通用 Skill 表面。这些是各自独立的安装包，不需要一起安装。

本源码仓库统一生成平台适配，再放入各自 ZIP；PWF 则将适配源直接展开在根目录。原生发现路径仍须按下面的说明部署到目标项目或用户配置。无需在本源码仓库根目录复制一套所有 Agent 的隐藏目录，也无需初始化研究子模块。

如果从源码仓库开始，以下以 Pi 为例，先对照 `dist/manifest.json` 检查摘要，再解压到新的、按平台区分的目录。已经取得解压包的用户直接选择下方宿主章节。

```bash
# Linux/macOS：替换为实际路径；其他宿主替换文件名中的 pi。
sha256sum "dist/program-design-0.2.0-pi.zip" # macOS 可用 shasum -a 256
unzip "dist/program-design-0.2.0-pi.zip" -d "/path/to/packages/program-design-pi"
```

```powershell
# Windows PowerShell：不要把多个平台解压到同一目录。
Get-FileHash ".\dist\program-design-0.2.0-pi.zip" -Algorithm SHA256
Expand-Archive -LiteralPath ".\dist\program-design-0.2.0-pi.zip" -DestinationPath "C:\packages\program-design-pi"
```

此时 `program-design-pi/program-design` 是安装源，目标项目另行指定。点开头的目录在文件管理器中可能被隐藏；复制时指定完整目录，不能使用会漏掉隐藏条目的 `*` 通配符。本版尚未发布到 npm 或远端 marketplace，应使用下述本地路线。

## 通用安装规则

先核对 ZIP 的 SHA-256 与 manifest，再解压到独立目录。保留文件层级、脚本、模板、references、LICENSE 和 UPSTREAM.json；只拷贝 SKILL.md 会丢失运行依赖。复制前检查目标文件，已有同名目录应先备份再替换本插件目录；已有 `settings.json`、`hooks.json`、package.json 和其他配置只合并本插件条目。不要整体覆盖用户配置。

Shell 路线要求宿主进程能找到所用的 `sh`/`bash` 与 Python 3；Windows 使用包内适用的 PowerShell/launcher 路线，不能将 POSIX hook 配置直接当作原生 PowerShell 配置。ZIP 解压器若不保留执行位，要恢复实际 hook 命令直接调用的 `.sh` 文件执行权限。Pi 的 TypeScript Extension 由 Pi 加载；OpenCode 的本地源码安装另需 Node.js/npm 和包内锁定的构建依赖。

已确认的环境限制：本轮 Ubuntu 环境的 uutils `mkdir` 0.8.0 在并发创建同一目录时可能让两个进程都返回成功，不能可靠支撑 Shell 目录锁；GNU `mkdir` 9.7 对照及相应回归通过。在该 uutils 版本下不要并发更新共享计划，使用经验证的 GNU 工具环境。插件不替换系统工具。若安装目录位于 `noexec` 文件系统，手工调用 `.sh` 辅助脚本时用明确的 `sh`/`bash` 解释器；文件有执行位仍可能返回 126，这不等于脚本缺失。

只启用一套规划执行 hooks；安装 Program Design 不会自动卸载 PWF。主 Skill 名称是 `project-docs`，默认可按任务匹配，项目规则和只读要求始终优先。辅助命令需显式使用；语言变体不是额外的默认自动入口。先以简单的只读状态请求检查加载，再在已授权维护任务中初始化计划。

## Codex、Claude Code、Pi、OpenCode

### Codex：使用仓库 marketplace

Codex ZIP 自带名为 `program-design-local` 的本地 marketplace，可直接从完整解压根安装：

```bash
codex plugin marketplace add /path/to/package/program-design
codex plugin add program-design@program-design-local
codex plugin list
```

源码仓库 `.agents/plugins/marketplace.json` 另有 `personal` marketplace 指向 `plugins/program-design`。使用仓库安装源时：

```bash
codex plugin marketplace add /path/to/program-design-repository
codex plugin add program-design@personal
codex plugin list
```

在新会话显式使用 `$project-docs` 检查实际读取。安装来源是本地 repository，不是尚未公开发布的 npm/GitHub 插件地址。ZIP 中 Codex manifest、`skills/`、`hooks/codex-hooks.json` 和 `.codex/hooks/` 必须留在同一个插件根；不能单独复制到全局 Skills 后期待插件 hooks 自动生效。

Codex 安装与 hooks 信任是两个步骤：在宿主 `/hooks` 检查并信任当前定义；更新后定义摘要改变时重新审查。宿主以 `PLUGIN_ROOT` 定位缓存包，不要求用户建立 Claude standalone 路径。多个来源的匹配 hooks 会共同执行，检查旧 PWF 或重复项目 hooks。[官方 hooks 文档](https://learn.chatgpt.com/docs/hooks)

ZIP 安装的卸载使用 `codex plugin remove program-design@program-design-local`，仓库安装使用 `codex plugin remove program-design@personal`，再查询插件列表。独立 marketplace 仅在没有其他依赖插件时移除；卸载安装包不删除项目的计划和证据。

### Claude Code：本地 marketplace 或单次插件目录

使用 `claude` ZIP；在 Claude Code 中执行：

```text
/plugin marketplace add /path/to/package/program-design
/plugin install program-design@program-design
```

本地 marketplace 在包内 `.claude-plugin/marketplace.json`，source 为当前包根。也可单次启动 `claude --plugin-dir /path/to/package/program-design`，不注册长期 marketplace。两种路线只选一种。

包内 `hooks/hooks.json` 通过插件根加载 `hooks/claude-hook.sh` 和共享 scripts；`skills/project-docs` 与 `commands/pd-*.md` 同包保留。主入口为 `project-docs`，辅助命令以宿主实际显示的 `program-design` 命名空间调用。插件 hooks 与 standalone Skill frontmatter 的激活时机不同，勿再复制同一 Skill 到 `~/.claude/skills` 形成重复执行。

若只需 standalone Skill，可将完整 `skills/project-docs/` 放入项目 `.claude/skills/` 或用户 `~/.claude/skills/`。这条路线不含插件启动时的 SessionStart 注册，不能声称与完整插件生命周期相同。卸载完整插件用 `/plugin uninstall program-design@program-design`；手工安装则仅移走本次复制的 Skill 目录。

### Pi：解压根本身是 pi-package

Pi ZIP 根下的 package.json 声明 `SKILL.md` 和 `extensions/program-design/index.ts`，无需再创建 `.pi/skills` 外壳。在目标项目目录执行：

```bash
pi install -l /path/to/package/program-design
pi list
```

`-l` 写项目 `.pi/settings.json`；省略时写用户 `~/.pi/agent/settings.json`。本地路径安装只记录路径、不复制源码，因此解压目录必须长期保留。该本地路径语义来自导入时固定的 Pi 官方 packages 文档。运行时使用宿主提供的 Pi API，无需为普通安装运行 Extension 的 Vitest 开发测试。

重启或 `/reload`，检查 `/skill:project-docs`、`/pd-plan-status`。Extension 默认先显示计划状态；显式 `/pd-plan-execute` 才启用其注入和执行循环，`/pd-plan-execute reset` 回到被动状态。`PWF_MODE` 可为 `auto`、`parity`、`cache-safe`、`notify`，配置对象仍名为 `planningWithFiles`。这属于 Pi 原生激活，不应描述为安装后所有 hooks 立即执行。续跑有平台上限，不能保证任务一定完成。

卸载项目安装使用 `pi remove -l /path/to/package/program-design`；用户安装省略 `-l`，随后 `pi list` 核对。本地源目录和项目记录由使用者分别保留或处置。

### OpenCode：项目内本地源码包

使用 `opencode` ZIP。包包含 `.opencode/packages/opencode-program-design/` 的 TypeScript 源码、package-lock.json、`.opencode/skills/project-docs/` 及可选命令。不要把尚未发布的 `opencode-program-design` 写入 npm 插件列表。

1. 将完整 `.opencode/packages/opencode-program-design/`、`.opencode/skills/project-docs/` 和 `.opencode/plugins/program-design.ts` 复制到目标同路径；需要命令时复制 `.opencode/commands/pd-*.md`。
2. 在目标本地包目录按锁文件安装构建依赖并编译：

```bash
cd /path/to/project/.opencode/packages/opencode-program-design
npm ci --ignore-scripts
npm run build
```

3. 包内 `.opencode/plugins/program-design.ts` 已提供以下入口，无需另写 loader 或注册 npm 插件；若目标已有同名入口，先检查其来源再更新：

```typescript
export { PlanningWithFiles } from "../packages/opencode-program-design/dist/index.js"
```

保留本地包的 node_modules，使编译文件能够解析 `@opencode-ai/plugin`。这是独立插件包目录的依赖，不要求把它加入业务项目根 package.json。分发入口加载刚编译的 dist；完整迁移源码树的开发入口仍加载 src，不应同时注册二者。

重启 OpenCode，检查 Skill `project-docs`、工具 `pd_init` / `pd_status` / `pd_check`，以及可选 `/pd-pwf`、`/pd-pwf-status`。原生插件通过消息事件注入、压缩事件保留接续信息；gated 利用 `session.idle` 后的 follow-up，不能阻止宿主完成原回合。不要把 Skill 的 Claude frontmatter hooks 当作 OpenCode 执行入口。

需要用户级安装时，整体本地包可放入 `~/.config/opencode/packages/`，Skill/commands/plugins 放到对应 `~/.config/opencode/` 子目录，保留相同相对层级及上述 re-export。卸载移除本次的入口、Skill、命令与独立包目录，不删除共享的 `.opencode` 配置。

## 其他平台的文件映射

以下表格给出源目录到目标目录的准确对应；复制完整目录及其内部资产。`<project>` 是目标项目根，`<user>` 是宿主使用的用户配置根。安装后重启宿主，核对其实际发现的 `project-docs`，不能以文件存在代替模型读取。

| ZIP 平台 | 从解压根复制到目标 | 配置、激活与差异 |
| --- | --- | --- |
| `hermes` | `.hermes/skills/project-docs/` → `<HERMES_HOME>/skills/project-docs/`；`.hermes/plugins/program-design/` → `<HERMES_HOME>/plugins/program-design/` | 两目录保持同一 Hermes 根；执行 `hermes plugins enable program-design`，再 `hermes plugins list` 并重启。用户根以宿主配置为准；POSIX 常见 `~/.hermes`，Windows 常见 `%LOCALAPPDATA%\hermes`。Python 插件原生注册命令；`.hermes/commands` Markdown 不是 Hermes 的注册机制 |
| `cursor` | `.cursor/skills/project-docs/`、`.cursor/hooks/` → `<project>/.cursor/` 下对应位置 | 把 `.cursor/hooks.json` 的事件条目合并到项目 hooks.json。Windows 原生 PowerShell 使用 hooks.windows.json 中条目；不要同时装两套。相对命令依赖项目 `.cursor/hooks/` 位置 |
| `gemini` | `.gemini/skills/project-docs/`、`.gemini/hooks/` → `<project>/.gemini/` 下对应位置 | 合并 `.gemini/settings.json` 的 hooks，保留原设置；命令引用 `$GEMINI_PROJECT_DIR/.gemini/hooks/`，因此该配置是项目级，不能原样改装为用户全局 hooks。宿主 Skills 需已启用；用 `/skills list` 检查 |
| `copilot` | `.github/hooks/program-design.json` 和 `.github/hooks/scripts/` → `<project>/.github/hooks/`；**`skills/project-docs/` → `<project>/.github/skills/project-docs/`** | hooks 明确依赖 `.github/skills/project-docs`，不能只复制 hooks。共享 scripts 中有同名文件时逐项核对。CLI、IDE、Coding Agent 的事件支持分别以实际版本/运行结果为准 |
| `mastracode` | `.mastracode/skills/project-docs/` → `<project>/.mastracode/skills/` | 把 `.mastracode/hooks.json` 事件合并到目标 hooks.json。仅 Skill 可放 `~/.mastracode/skills/`；hooks 的项目/用户路径和 Shell 可用性另核对 |
| `kiro` | `.kiro/skills/project-docs/` → `<project>/.kiro/skills/` | 在 Agent Steering & Skills 中导入该本地目录。资产是 `assets/scripts` / `assets/templates`，不是 canonical `scripts` / `templates`；没有默认执行 hooks |
| `continue` | `.continue/skills/project-docs/` → `<project>/.continue/skills/`；`.continue/prompts/` 中本插件 prompt → 对应 prompts 目录 | 可以改为用户 `~/.continue/` 同层级。重载 IDE；显式 prompt 辅助启动，Claude frontmatter hooks 不在此宿主执行 |
| `factory` | `.factory/skills/project-docs/` → `<project>/.factory/skills/` 或 `~/.factory/skills/` | 重启 Droid 后发现 Skill；包不提供 Factory 原生执行 hook 配置，不宣称自动停止门禁 |
| `codebuddy` | `.codebuddy/skills/project-docs/` → `<project>/.codebuddy/skills/` 或 `~/.codebuddy/skills/` | 重启后发现 Skill；包不提供 CodeBuddy 独立执行 hook 配置 |
| `agents` | `.agents/skills/project-docs/` → `<project>/.agents/skills/` 或 `~/.agents/skills/` | 通用 Agent Skills 表面，须由实际宿主支持该发现路径；不是保证任意 Agent 都执行其中 Claude frontmatter hooks 的通用运行时 |

Hermes 项目级插件另要求 `HERMES_ENABLE_PROJECT_PLUGINS=1` 并启用插件，且从项目目录启动；Desktop 使用用户级路径。其 `pre_verify` 只在宿主符合触发条件时续跑，受 Hermes 自身验证次数限制，不等同原生 Stop 拒绝。

Kiro 只有在任务授权创建项目记录、且选定 Kiro 自己的计划布局后，才执行：

```bash
sh .kiro/skills/project-docs/assets/scripts/bootstrap.sh
```

Windows 对应 `powershell -NoProfile -File .kiro/skills/project-docs/assets/scripts/bootstrap.ps1`。它按缺失文件创建 `.kiro/plan/` 三文件与 `.kiro/steering/planning-context.md`；不得在已有另一任务计划时另起竞争计划，也不在只读请求中执行。Kiro 这套原生布局不能直接宣称拥有 canonical `.planning/<id>` 选择能力。

Cursor、Gemini、Copilot、Mastra 的部分继承 hooks 仍以根 `task_plan.md` 为中心；只读、命名计划和关闭支持应以 REP-0005 的逐项结果为准，不从共同文件名称推定等价。在未验证 hook 能正确选择当前计划的宿主上，禁用这些事件，显式使用选定计划和 Skill。需要完全关闭时优先使用宿主 hook 配置；`PLANNING_DISABLED=1` 仅在相应实现已通过关闭测试的路线可作为充分开关。

## 使用与升级核对

先要求宿主只读显示当前计划路径，确认没有读到别的任务；然后在一个小型、已授权维护任务中验证一次 Skill 读取和实际事件输出。重要设计、长期文档维护、依据 review 和冷读仍需要 Agent 执行并记录证据，hooks 不会独立完成这些语义工作。

本包 UPSTREAM.json 和 LICENSE 保存上游来源；重建入口随源码仓库交付。PWF 三文件和原有状态兼容不代表允许两个插件同时维护它们；卸载也不应自动删除计划、attestation、ledger 或长期项目文档。
