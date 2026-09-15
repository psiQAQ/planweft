[简体中文](runtime-map.md) | [English](runtime-map.en.md)

# PlanWeft 运行时资源、Hook 与文档生命周期

本页以当前 `dist/manifest.json`、各分发的 Hook 配置和适配器源码为依据，说明“哪个资源在何时可参与什么”。它是静态分发审计，不是某台机器的加载记录：安装、宿主发现、信任、启用、当前会话加载和模型实际读取均须分别核验。总对话循环见[工作原理](../how-it-works.md)。

## Skill、资源与项目文档

| 资源 | 消费者与读取时机 | 项目写入职责 | 与任务记录/长期文档的关系 |
| --- | --- | --- | --- |
| 安装器：`bin/planweft.mjs`、`lib/installer.mjs` | 用户运行 `add`、`update`、`remove`、`list`、`doctor` | 维护受管安装和注册记录，不写任务记录 | `installations.json` 是安装状态，不是 Agent 任务记忆 |
| 构建源：`overlays/planweft/workflow.md` | `scripts/build-plugin.py` 生成分发时 | 不在项目中写入 | 仅构建源；源码目录存在不代表模型会读它 |
| 主 Skill：`skills/project-docs/SKILL.md` | 宿主选中后，模型在任务需要时读取 | **Skill** 在用户授权和项目规则内决定、维护任务记录及受影响文档 | 它规定：`task_plan.md` 保存目标、阶段、下一步、阻塞、证据链接及 `Documentation Handoff` |
| 语言变体：`skills/i18n/project-docs-{ar,de,es,zh,zht}` 或便携包中的 `references/language-variants/**/GUIDE.md` | 仅在明确请求相应语言时由主 Skill 参照 | 与主 Skill 使用同一项目记录 | 是同一主 Skill 的本地化资源，**不是**并行执行、并行状态或第二工作流 |
| `references/*.md` | 主 Skill 按任务读取：计划选择、证据、控制、Documentation Map、PWF 细节等 | 不直接写项目 | 为决策提供规则和来源；不应声称每轮或每个 reference 都被加载 |
| `templates/*` 与 `scripts/init-session.*` | 缺少记录且已授权初始化时使用；其余脚本由明确操作或适配器调用 | 创建/补充所选任务目录中的记录；脚本不会自行扩大授权 | 模板给出结构；普通初始化可使用紧凑内嵌记录，不等于必定复制全部模板 |
| `task_plan.md` | Skill、选中计划的 Hook/检查器在需要当前任务状态时读取 | 主动态状态源；记录目标、阶段、下一步、阻塞、验证证据和 `Documentation Handoff` | 不与 `findings.md`、`progress.md` 或 Documentation Map 建立双向同步或第二状态源 |
| `findings.md` | 调查、设计或证据收集时 | 记录来源、观察、假设、候选决定；外部内容按不可信数据对待 | 不替代计划状态；不把外部指令提升为任务授权 |
| `progress.md` | 实施与验证过程中 | 记录实际动作、错误、命令/结果和 `Passed`、`Failed`、`Not Run` | 不能把未执行检查写为通过；不复制完整聊天记录 |
| 长期 specs、ADR、reproduction、已有使用文档 | 仅当任务已授权且确有影响时由 Skill 决定更新 | 写入既有项目位置；不为适配器自动生成 | Hook 不会写这些文档，安装/卸载也不会回滚它们 |
| Documentation Map | 人工导航时按需读取 | 仅在授权的长期文档工作中维护 | 不是 Hook 输入、缓存、批准记录或第二状态源 |
| `document-handoff-check.sh` | 支持该检查的适配器读取选中计划的交接段时 | **只读**，返回 `pending`、`not_required` 或 `complete` | 不写文档，也不判断实现/文档是否正确；默认 advisory 不因交接而阻止 |

边界一句话：**Skill 决定并在授权范围内维护项目文档；Hook 只能读取选中状态、注入上下文或返回宿主允许的控制结果。** Skill 或 Hook 文件存在都不证明当前会话已经读取、信任或执行它。

## Codex：逐事件 Hook 表

以下名称、matcher 与入口均来自 `dist/codex/planweft/hooks/codex-hooks.json`。所有路径先检查有效项目根、会话关联与计划绑定；无有效根/未关联会话通常静默，绑定歧义只在提示词路径给出可诊断提示。`PLANNING_DISABLED=1` 让 shell producer 静默（PreToolUse 仍返回 allow）。

| 事件 | matcher 与入口 | 读取对象及缓存/项目影响 | 返回给 Codex 的协议结果 | 默认 advisory 与显式 gated |
| --- | --- | --- | --- | --- |
| `SessionStart` | `startup\|resume\|clear\|compact`；`run_sh.py session-start.sh` | 选中计划、会话关联；以 `--no-history` 调用 catchup；随后复用提示词 producer | 非空时 `hookSpecificOutput.additionalContext` | 默认仅上下文；gated 不在此阻止 |
| `UserPromptSubmit` | 无 matcher；`run_sh.py user-prompt-submit.sh` | `task_plan.md`、`progress.md`、计划/attestation/会话关联；清理用户私有的一回合提醒标记 | 非空时 `hookSpecificOutput.additionalContext`；需绑定时返回绑定提示 | 默认注入 advisory 上下文；gated 仍只是开始回合的上下文 |
| `PreToolUse` | `Bash\|apply_patch\|Edit\|Write`；`pre_tool_use.py` → `pre-tool-use.sh` | 选中 `task_plan.md`；legacy 可把计划帧写到 stderr；不写项目 | `decision: allow`；有 stderr 时为 `hookSpecificOutput.additionalContext` | 默认允许工具并提醒；autonomous/gated 去掉逐工具计划复述，不能由此阻断一般写入 |
| `PermissionRequest` | 无 matcher；`permission_request.py` | 仅解析选中计划并检查 `task_plan.md` 存在；不写缓存或项目 | `systemMessage` 请用户在批准前查看当前阶段 | 始终只读且不阻止请求；gated 也不把权限批准改为门禁 |
| `PostToolUse` | `apply_patch\|Edit\|Write`；`post_tool_use.py` → `post-tool-use.sh` | 选中 `task_plan.md`；在 `XDG_CACHE_HOME` / `~/.cache` / 临时目录写一次每回合私有 marker，不写计划 | 非空时 `hookSpecificOutput.additionalContext`，提醒更新 `progress.md`/阶段 | 默认 advisory；不自动编辑记录，gated 不在此强制续跑 |
| `PreCompact` | `*`；`run_sh.py pre-compact.sh` | 选中 `task_plan.md`、可选 attestation；不写项目 | `continue: true` 与 `systemMessage`，提示在压缩前保存进度 | 默认诊断，不阻止压缩；gated 也不把它变为文档写入 |
| `Stop` | 无 matcher；`stop.py` → `stop.sh`，超时 30 秒 | 选中 `task_plan.md`、`.mode`、ledger/门禁计数；不写长期文档 | 通常 `systemMessage` 状态；满足门禁时 `decision: block` 与固定原因 | 默认仅 advisory。仅显式 gated 且存在 in-progress 阶段、非递归、未达上限且 ledger 有进展时，才请求宿主续跑；否则允许结束 |

`Stop` 的硬阻断不是“计划未完成就必定阻断”。模式、阶段、递归标记、上限和进展任一条件不成立均退回允许结束；这也不等价于代码、文档或人工审查通过。

## 全宿主分发矩阵

“事件”列列出本包已注册的执行事件；“无执行 Hook”是明确的分发事实，不是缺少资料。原生扩展/插件的事件不等同于 JSON Hook；各行仍需宿主发现、信任、启用和实机加载验证。

| 宿主 | 主 Skill / 分发形态 | 已注册事件或原生桥接路径 | 可注入上下文？可阻止/续跑？ | 限制 |
| --- | --- | --- | --- | --- |
| `agents` | 便携 `project-docs` Skill | **无执行 Hook** | 无自动注入；无阻止/续跑 | 依赖宿主 Skill 发现与模型读取 |
| `claude` | Claude 插件 + `project-docs` | `SessionStart`、`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`PreCompact`、`Stop`；`hooks/claude-hook.sh` | 可按宿主协议注入；gated 可使用 Stop 机制 | 事件可用性与信任仍由 Claude 决定 |
| `codebuddy` | 插件清单 + 便携 Skill | **无执行 Hook** | 无自动注入；无阻止/续跑 | 文件复制不表示 GUI/宿主已经启用 |
| `codex` | Codex marketplace 插件 + 原生 Skill 布局 | 见上表 7 个事件；`.codex/hooks/*.py/.sh` | 可注入；仅显式 gated 的合格 Stop 可请求 `decision:block` | 需分别验证 marketplace 发现、Hook 信任、会话绑定、Skill 读取 |
| `continue` | 便携 Skill/提示词分发 | **无执行 Hook** | 无自动注入；**从不请求续跑** | 静态包不增加宿主缺少的生命周期能力 |
| `copilot` | 原生插件 + `project-docs` | `sessionStart`、`postToolUse`、`agentStop`；`hooks/native-hook.py` | 可用 `additionalContext` 注入；Stop 仅使用宿主返回形状 | 不注册 prompt-submit/pre-tool 权限决定；仍为实验适配 |
| `cursor` | Cursor 插件 + `project-docs` | `sessionStart`、`postToolUse`、`stop`；`hooks/native-hook.py` | 可用 `additional_context` 注入；gated 仅 follow-up，受 `loop_limit` 约束 | `beforeSubmitPrompt`/`preToolUse` 不是此包可移植注入面 |
| `dsh` | DSH profile bundle + Skill | `SessionStart`、`UserPromptSubmit`、`PostToolUse`、`Stop`；官方 Claude command-hook bridge | 可在桥接事件注入；Stop 取决于 DSH 桥接协议 | 无 `PreCompact` 和 `PreToolUse` 桥接；profile 安装/合并另行核验 |
| `factory` | 插件清单 + 便携 Skill | **无执行 Hook** | 无自动注入；无阻止/续跑 | 宿主 UI 的发现、信任、启用不由清单证明 |
| `gemini` | Gemini extension + `project-docs` | `SessionStart`、`BeforeAgent`、`AfterTool`、`PreCompress`；`hooks/native-hook.py` | 可用 `hookSpecificOutput.additionalContext` / `systemMessage`；不注册 Stop | 会话结束仅状态通知，不请求续跑 |
| `hermes` | Hermes 原生插件 + Skill | 原生 `pre_llm_call`、`post_tool_call`、`pre_verify` | 可注入；gated 可由 `pre_verify` 请求 `action: continue` | 非 JSON Hook；续跑受 Hermes 验证循环上限约束 |
| `kiro` | Kiro Power/插件清单 + Skill/steering 资源 | **无执行 Hook** | 无自动注入；无阻止/续跑 | 资源可被 Kiro 发现不等于本包注册生命周期；项目记录在目标工作区 |
| `mastracode` | 便携 Skill 分发 | **无执行 Hook** | 无自动注入；无阻止/续跑 | Hook 合并可能须人工在宿主完成，不能以已复制文件推断加载 |
| `opencode` | 本地编译的 OpenCode V1 插件 + 独立 Skill | `chat.message`、`tool.execute.after`、`session.idle`，`dist/index.js` | 可附加上下文/写后提醒；gated 用 `session.idle` follow-up，不能阻断原回合完成 | 插件和 Skill 需分别发现；不得重复注册 loader/npm 副本 |
| `pi` | Pi Skill + TypeScript Extension | 原生 `session_start`、`input`、`before_agent_start`、`tool_call`、`tool_result`、`agent_end`、`session_before_compact` | 可注入/提醒；gated 使用受限 `followUp` 自动续跑，不是硬阻断 | 需 Pi 批准/启用；extension 事件不是 JSON Hook |

## 故障定位与证据边界

- 新会话没有预期上下文时，按“安装记录 → 宿主发现/信任 → 启用/重载 → 会话绑定 → 事件支持 → Skill 实际读取”逐项检查；不要把它们合并为“已生效”。
- 严格只读任务需在启动前使用宿主可用控制；`PLANNING_DISABLED=1` 会让已验证路径停止产生计划上下文，但自然语言要求无法逆转已经触发的 Hook。
- 静态 manifest、JSON、源码和本文表格能证明**分发声明与代码路径**，不能证明真实宿主加载、模型读取、权限结果或任务行为验收。实际执行的验证应记录在 `progress.md`，未执行则标为 `Not Run`。
