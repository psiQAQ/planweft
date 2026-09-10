[简体中文](INSTALL.md) | [English](INSTALL.en.md)

> 当前安装包：**agents**。请选择本文对应宿主的安装章节。

# 安装、更新、回退与卸载

PlanWeft 0.4.0 通过一个 `planweft` npm 包分发。安装器会为每个宿主选择正确的原生布局，并记录它管理的文件；不要把不同宿主的 `dist` 目录合并安装。

需要 Node.js 22 或更高版本，建议使用 Node.js 24 LTS。部分宿主还需要 Python 3、Bash、PowerShell 或自身的包管理器。

## 安装

项目级是默认 scope。Codex、Copilot、Gemini、Hermes 和 DSH 的完整集成只支持用户级安装，必须使用 `--global`；这些宿主仍可按项目安装 Skill-only 版本。以下示例覆盖五个正式支持的宿主：

```bash
npx planweft@0.4.0 add -a codex --global
npx planweft@0.4.0 add -a claude
npx planweft@0.4.0 add -a pi
npx planweft@0.4.0 add -a opencode
npx planweft@0.4.0 add -a dsh --global --dsh-profile headless
```

可以在一条命令中重复 `-a`。非交互调用必须明确提供宿主标识。

| 参数 | 默认值 | 作用 |
| --- | --- | --- |
| `-a / --agent` | 交互选择 | 选择一个或多个宿主 |
| `--project / --global` | `--project` | 选择项目级或用户级安装；宿主不支持时直接报错 |
| `--skill-only` | 关闭 | 只安装便携 Skill，不注册完整插件 hooks |
| `--copy / --symlink` | 优先 symlink | 控制 CLI 管理组件的安装方式 |
| `--dsh-profile NAME` | `headless` | 选择 DSH 完整集成使用的 profile |
| `--approve-pi-project` | 关闭 | 仅为本次 Pi 项目命令传入原生 `--approve` |
| `--dry-run` | 关闭 | 显示选择和目标路径，不写入 |
| `--source FILE.tgz` | 当前精确 npm 版本 | 使用与当前 CLI 身份和版本一致的本地验收包 |

宿主标识为：`codex claude pi opencode hermes cursor gemini copilot mastracode kiro continue factory codebuddy agents dsh`。前五个正式支持的宿主是 `codex`、`claude`、`pi`、`opencode` 和 `dsh`；其余适配器为实验性。

仅需要 Skill 时显式使用 `--skill-only`：

```bash
npx planweft@0.4.0 add -a opencode --skill-only --symlink
npx planweft@0.4.0 add -a dsh --skill-only
```

Skill-only 不会注册插件 hooks，也不会增加宿主原本没有的生命周期事件。

## 检查安装

安装后先检查记录与可发现状态：

```bash
npx planweft@0.4.0 list
npx planweft@0.4.0 doctor
```

再按宿主要求重载或创建新会话，并显式调用主 Skill：

| 宿主 | 新会话检查 |
| --- | --- |
| Codex | 调用 `$project-docs`，并在宿主 hooks 界面核对当前定义和信任 |
| Claude Code | 调用 `/planweft:project-docs` |
| Pi | 调用 `/skill:project-docs`；只有显式 `/pw-plan-execute` 才启动执行循环 |
| OpenCode V1 | 检查 `project-docs` 和 `pw_init`、`pw_status`、`pw_check` |
| DSH | 在所选 profile 的新会话中明确要求使用 `project-docs` |

安装成功、宿主发现、当前会话加载、hook 信任和模型实际读取是不同检查。`doctor` 不能代替新会话中的 Skill 读取。

## 更新、回退与卸载

`update` 使用当前执行的 CLI 版本。用目标旧版本的 CLI 执行同一命令就是回退；请将 `<version>` 换成需要恢复的准确版本号：

```bash
npx planweft@0.4.0 update -a pi
npx planweft@<version> update -a pi
npx planweft@0.4.0 remove -a pi
npx planweft@0.4.0 doctor -a pi
```

更新和卸载必须沿用原安装的宿主、scope 与 DSH profile。copy/symlink 和 Skill-only 选择会从安装记录恢复；要在完整插件与 Skill-only 之间切换，先 `remove` 再 `add`。

项目版本存储在 `.planweft/versions/`，安装记录在 `.planweft/installations.json`。用户级状态使用 `$XDG_DATA_HOME/planweft`（默认 `~/.local/share/planweft`），Windows 使用 LocalAppData；`PLANWEFT_HOME` 可以覆盖用户级状态位置。不要提交项目 `.planweft/`。

卸载保留版本存储和项目文档。确认不再需要回退后，用户可以另行清理自己拥有的版本缓存；安装器不会删除未知文件。

## 用户文件与重复来源

安装器只覆盖其记录并能验证所有权的文件。以下情况会停止更新或卸载并由 `doctor` 报告：

- 受管文件被用户修改；
- 目标目录出现外来文件；
- 同一宿主发现另一套 PlanWeft、旧 `program-design` 或独立 PWF hooks；
- 安装记录、摘要或目标路径不一致；
- 另一个安装操作持有 `.operation-lock`。

更新或卸载不会删除 `task_plan.md`、`findings.md`、`progress.md`、`.planning/`、attestation、ledger、specs、ADR、reproduction 或用户笔记。插件回退也不会回退任务中已经修改的项目文档。

## 信任、禁用与宿主差异

安装不会自动授予 hooks、项目文件或命令权限。Codex、Claude Code、Pi 及其他宿主仍使用自己的信任与批准界面。Pi 的 `--approve-pi-project` 只批准本次本地包操作，不改变其他宿主设置。

默认运行模式是 advisory。需要完全关闭已验证适配路径的执行 hooks 时，在启动宿主前设置 `PLANNING_DISABLED=1`。Pi 还可用 `/pw-plan-execute reset` 回到被动状态。autonomous/gated 必须显式启用；它们在所有宿主上仍是实验性。

DSH 完整集成是用户级 profile 安装，更新和卸载必须使用相同的 `--dsh-profile`。GUI 平台或 Mastra hooks 合并可能由安装器标记为 manual，需要在宿主界面完成，不能把文件已复制当作加载成功。

Hermes 当前仍为实验性分发。历史默认扫描拒绝记录不会因安装文档精简而变成通过；安装器不提供关闭扫描器的绕过开关。

## 常见问题

**`doctor` 报告重复 hooks。** 使用各宿主的列表命令确认真实注册 ID，按原安装渠道移除旧来源。不要直接删除未知缓存，也不要让完整插件与手工 Skill/hooks 同时执行。

**更新后仍看到旧行为。** 先确认 `update` 使用了目标版本，再按宿主要求刷新 marketplace、重载插件或启动新会话。来源刷新、文件替换和当前进程重载不是同一动作。

**安装因用户修改停止。** 先查看 diff 并保存需要保留的内容。确认文件所有权后，通过原渠道恢复、迁移或移除；不要强制覆盖。

**留下 `.operation-lock`。** 先确认没有安装进程运行，检查安装记录和失败现场，再手动移除空锁目录。不要在同一项目中并发执行多个安装操作。

**需要使用本地准确包。** CLI 版本和 `--source` 包必须具有相同身份与版本：

```bash
npx planweft@0.4.0 add -a codex --global --source /absolute/path/planweft-0.4.0.tgz
```

## 从旧身份迁移

从 `program-design`、`personal` 或 `program-design-local` 迁移时，先用原宿主的列表命令确认旧注册，再通过原安装渠道移除旧执行 hooks。随后安装 PlanWeft 并创建新会话。主 Skill 仍为 `project-docs`，辅助命令前缀从 `pd-` 改为 `pw-`，OpenCode 工具前缀从 `pd_` 改为 `pw_`。

安装器不会自动卸载旧插件或原版 PWF。项目计划、批准需求和用户修改保持不变。

平台支持级别和已知限制见仓库的[中文平台文档](https://github.com/psiQAQ/planweft/blob/master/docs/platforms.md)；维护者需要的手工布局、catalog 和协议细节见[开发文档](https://github.com/psiQAQ/planweft/blob/master/docs/development.md)。
