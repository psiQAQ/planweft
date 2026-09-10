---
name: project-docs-zh
description: "Use for implementation/maintenance with investigation, fixes, regression tests and handoff, including existing notes. Read-only/trivial tasks do not initialize files. Use the host-listed Skill path; read it before resource lookup. Do not use host settings or installation receipts to locate resources. Uses selected project planning context. Automatic recovery reads project planning files only. Explicit requests only: --metadata / --replay. It never runs commands declared in Markdown; no network upload path. It registers no lifecycle or Stop hook and never requests continuation."
user-invocable: true
allowed-tools: "Read Write Edit Bash Glob Grep"
hooks:
  # Generated dispatch block: the 11 IDE and language variants share one
  # template (parity locked by tests/test_skill_hook_dispatch_parity.py).
  # Candidate order, first existing file wins: PWF_SCRIPT_DIR (explicit user
  # override for workspace or other nonstandard installs), CLAUDE_SKILL_DIR,
  # host env var, host user-level install dirs, then the two .claude paths.
  # Deliberate asymmetry: only UserPromptSubmit reports an unresolved script,
  # once per prompt. PreToolUse and PreCompact fire per tool call and Stop
  # carries no plan body, so a notice there would be spam; they stay silent.
  UserPromptSubmit:
    - hooks:
        - type: command
          command: "SH=\"\"; for c in \"${PWF_SCRIPT_DIR}/skill-hook.sh\" \"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs-zh/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\"; do [ -f \"$c\" ] && { SH=\"$c\"; break; }; done; if [ -n \"$SH\" ]; then sh \"$SH\" --event=userprompt; else echo \"[planweft] hook script not found; plan injection is off. Set PWF_SCRIPT_DIR to the skill's scripts directory, or install the skill to a user-level path.\"; fi; exit 0"
  PreToolUse:
    - matcher: "Write|Edit|Bash|Read|Glob|Grep"
      hooks:
        - type: command
          command: "SH=\"\"; for c in \"${PWF_SCRIPT_DIR}/skill-hook.sh\" \"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs-zh/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\"; do [ -f \"$c\" ] && { SH=\"$c\"; break; }; done; [ -n \"$SH\" ] && sh \"$SH\" --event=pretool; exit 0"
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: "SH=\"\"; for c in \"${PWF_SCRIPT_DIR}/skill-hook.sh\" \"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs-zh/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\"; do [ -f \"$c\" ] && { SH=\"$c\"; break; }; done; [ -n \"$SH\" ] && sh \"$SH\" --event=posttool; exit 0"
  Stop:
    - hooks:
        - type: command
          command: "SH=\"\"; for c in \"${PWF_SCRIPT_DIR}/skill-hook.sh\" \"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs-zh/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\"; do [ -f \"$c\" ] && { SH=\"$c\"; break; }; done; [ -n \"$SH\" ] && sh \"$SH\" --event=stop; exit 0"
  PreCompact:
    - matcher: "*"
      hooks:
        - type: command
          command: "SH=\"\"; for c in \"${PWF_SCRIPT_DIR}/skill-hook.sh\" \"${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs-zh/scripts/skill-hook.sh\" \"$HOME/.claude/skills/project-docs/scripts/skill-hook.sh\" \"$HOME/.claude/plugins/marketplaces/planweft/scripts/skill-hook.sh\"; do [ -f \"$c\" ] && { SH=\"$c\"; break; }; done; [ -n \"$SH\" ] && sh \"$SH\" --event=precompact; exit 0"
metadata:

  version: "0.4.0"

disable-model-invocation: true
---

# 项目文档与任务规划

包含调查、修改、回归验证和持久交接的实施或维护任务使用以下四步。按整个任务判断，不按代码 diff 大小判断。使用用户的语言。

## 1. 明确范围，读取项目入口

探索仓库前，在已有回复中列出少量初始项目入口：任务指定的路径，以及用户范围允许读取且实际存在的根指令和 README。读取前先按明确的读取限制筛选这个初始集合。先读这些入口，再沿相关文档链接或实现／测试关系，在已授权范围内扩展。根目录浅层列举可以帮助定位入口；发现宿主配置或安装器目录，不代表它成为任务输入。仅在任务明确授权检查或修改该目录时加入，并注明授权来源。包内资源使用下方独立的宿主已提供 Skill 路径。

从这些项目入口读取批准需求、已有任务记录及相关 diff，保留用户修改。准备任务前，在已有回复或目标段中说明适用的分支及实际来源：

- 只读／诊断／宿主规划模式：只检查和报告，不修改项目记录；明确要求的书面调研只授权该产物。
- 简单任务，或明确限制新增文件、采用流程、旧计划权威：说明简单任务的范围，或引用限制原句及来源；保留原状态入口。
- 已授权的实质实施：没有上述限制时，说明未发现禁止采用的指令，再按第 2 步解析或初始化本任务。“最小修改”“沿用资料”是工作背景，不是禁止采用的指令。

该判断只记录已有授权，不授予新权限，也不另建判断文件。

资源使用宿主提供的 `SKILL.md` 位置；链接解析见[本地操作](references/local-operations.zh.md)（[English](references/local-operations.md)）；脚本 cwd 为已授权项目。不要为定位资源检查宿主配置、安装收据或无关环境变量；仅按脚本需要查看 `PLAN_ID`、`PWF_*`、`PLANNING_DISABLED`。

## 2. 修改实现前准备任务

先读[计划选择](references/plan-selection.zh.md)（[English](references/plan-selection.md)），再运行 `sh "<安装 Skill>/scripts/resolve-plan-dir.sh"` 或文档中的 PowerShell 对应入口。空输出且退出码 0 本身不等于没有计划。结合 `PWF_PLAN_ROOT` 等绑定和实际项目文件判断：

- 有有效的所选计划：读取三份记录并恢复。
- 绑定被拒绝或选择有歧义：写入前纠正，不另建计划。
- 既没有计划，也没有待纠正绑定，且实施已授权：运行 `bash "<安装 Skill>/scripts/init-session.sh" "Task Name"` 或文档中的初始化器。检查实际创建位置，实施前填好记录；如返回 `PLAN_ID` 则保留。

实施前，把带实际用户／项目来源的简明范围摘要写在现有目标段内、前 30 行中：授权对象、禁止的读取／写入和验证限制。包含本次任务的具体指令，不能只摘录通用项目规则。范围只维护在这里，不在末尾附录重复；提醒可能只选取计划开头或 Goal。计划记录授权来源，本身不授予权限。 对新初始化的计划，把这一个目标标题规范为 `## Goal`，正文保留原语言，不增加第二目标段。已有受保护标题保持原样；smart 提取可能忽略本地化目标，此时读取完整计划，不假定提醒保留了范围。

将本任务动态状态转入所选 `task_plan.md`。仅将旧入口的状态／下一步字段替换为指向它的相对链接，保留历史和批准需求。一个动态状态源，不双向同步。

## 3. 实施并记录观察

`task_plan.md` 管理目标、阶段、状态、下一步、阻塞和证据入口；`findings.md` 记录来源、带时点的观察、假设和候选决定；`progress.md` 记录操作、错误和验证。决策前重读计划，每阶段后更新；保留解析器字面格式 `### Phase` 和 `**Status:** pending`、`in_progress`、`complete`。

在原有位置维护受影响的长期文档，只创建有用的缺失记录。不得为适配代码改写批准需求。一个 owner 更新共享状态，worker 使用分配记录；独立任务使用不同计划或 worktree。手工临时副本和反事实检查按[本地操作](references/local-operations.zh.md)（[English](references/local-operations.md)）在项目内分配并清理自有目录，记录实际位置。

实际执行的检查记录命令或操作、观察结果及可获取的退出状态；继承结果引用原记录；未执行检查为 **Not Run**。读码不是执行，后来的执行不能写成先前结果。

## 4. 核对记录并交接

对照需求、实际行为和最终 diff。对每项错误或后续更正，修正仍作为当前事实的源陈述，或给旧陈述标时点并链接更正；随后实际重读受影响的陈述及其依据。保留历史观察，不改写成最终行为。

使用 **Passed**、**Failed**、**Not Run** 并说明限制。新读者分别报告历史 Passed、本次未重跑项及实际执行的检查。核对旧入口能到达唯一动态计划，留下明确下一步。

重要设计使用独立依据 reviewer，重要交接使用只接收项目文件的新读者，不提供旧聊天或预期答案。按[依据指导](references/evidence.md)处理发现；独立检查不可用则记 Not Run。

按需读取 [PWF 细节](references/pwf-workflow.md)和[控制说明](references/controls.md)。默认提醒模式；自动恢复只用项目文件，访问会话历史需明确请求，attestation 不是批准。同一会话只启用一个规划插件的 hooks。保留 `PLAN_ID`、`PWF_*`、`PLANNING_DISABLED`；必要时在只读会话启动前设置 `PLANNING_DISABLED=1`。私有缓存与项目记录分开，宿主能力以 `INSTALL.md` 为准。

缺失记录模板：[计划](templates/task_plan.md)、[发现](templates/findings.md)、[进展](templates/progress.md)。
