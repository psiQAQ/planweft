# 0.3.0 原生 runtime 独立审查

日期：2026-09-08。审查者与 `native/adapters.py`、`native-hook.py` 的实现者不同。本文记录运行协议与安装资源的独立审查；发布准备、构建器和编译器由另一项审查覆盖。

## 范围与方法

- 阅读 `overlays/program-design/native/adapters.py`、`native-hook.py`、对应生成目录与 `tests/test_native_hooks.py`，核对原生事件、上下文输出、gate、项目与安装目录的分离。
- 核对 Codex Windows launcher 的生成引用和已有测试，区分静态引用成立与实际 Windows 执行。
- 使用 OpenCode V1 1.18.29 的真实 `debug config`、`debug agent build`、`debug skill` 和工具执行入口，验证预编译本地插件及单独安装的主 Skill。使用隔离 HOME/cache、无真实认证的模型元数据和临时项目，不调用模型。
- 检查语言变体是否仍位于原生扫描目录，以及从单独复制的主 Skill 能否访问其声明的支持资源。

本轮未运行真实 Windows/macOS 宿主、远程 npm 发布安装或付费模型。脚本协议测试不能替代真实宿主触发与模型接收上下文的证据。

## 发现与处理状态

| 编号 | 发现 | 影响 | 状态 |
| --- | --- | --- | --- |
| NR-01 | Kiro 的 `skills/project-docs/SKILL.md` 仍用 `.kiro/skills/project-docs/assets/scripts/` 调用 bootstrap、session-catchup 和 check-complete；原生 Power 包实际把它们放在 `skills/project-docs/assets/scripts/` | 安装到 Power/plugin cache 后，项目相对脚本路径不可达；`.kiro/plan` 与 `.kiro/steering` 作为任务记录路径的原义应保留 | 已修复；最终目录 POSIX 协议复验 Passed，Windows 与真实 Kiro 宿主 Not Run |
| NR-02 | OpenCode/Hermes 的安装说明只复制完整 `skills/project-docs/`，但该 Skill 将显式语言变体定位到 `../../language-variants/`；支持目录位于插件根，没有随主 Skill 复制 | 主 Skill 可以发现和运行，显式选择语言变体时资源不可达；插件与 Skill 的两段安装不完整 | 已修复；最终 OpenCode 真实宿主发现与资源复验 Passed，Hermes 原生安装能力仍见主报告限制 |

NR-01 在修复前的 Kiro 主 Skill 第 84、90、128、134、146、150 行均可观察到。最终说明使用 `PD_KIRO_SKILL_ROOT` / `PdKiroSkillRoot` 绑定加载的 Skill 绝对目录，保持当前目录为目标项目。独立复验从最终 `dist/kiro/program-design/` 复制资源，在含空格/中文的安装与项目路径中运行实际 bootstrap，确认只在项目生成 `.kiro/plan` 和 `.kiro/steering`，重复运行保护既有三文件。Windows 分支仍为 Not Run。

NR-02 的最终布局为主 Skill 内的 `references/language-variants/project-docs-{ar,de,es,zh,zht}/GUIDE.md`，每种语言附完整 scripts、templates、references 与来源/许可证；因此单独复制主 Skill 即带走这些资源。变体使用 `GUIDE.md` 避免成为额外 Skill 入口。最终 OpenCode `debug skill` 只发现一个 `project-docs`，其报告的实际路径与预期安装位置一致；完整复制内容逐文件匹配所选插件包，五种语言资源在 A/B/回退 A 三阶段均可达。`tests/test_native_resource_paths.py` 另覆盖八种 portable host 的完整复制与 Codex/Claude 原生布局保留。

## 其余审查结论

原生桥接没有把不同宿主的输出格式视为相同：Cursor 使用 `additional_context` 和 `followup_message`；Copilot 使用 `additionalContext`，结束阶段使用 `decision`/`reason`；Gemini 上下文使用 `hookSpecificOutput.additionalContext`。这些字段与各宿主官方契约一致。[Cursor hooks](https://cursor.com/docs/hooks)、[Copilot hooks](https://docs.github.com/en/copilot/reference/hooks-reference)、[Gemini hook reference](https://geminicli.com/docs/hooks/reference/)

Gemini 的 `PreCompress` 返回 `systemMessage`，这是面向用户的诊断显示，不是模型上下文注入。不能把该事件的协议输出成功表述为模型在压缩前已收到持久化提示。[Gemini hook reference](https://geminicli.com/docs/hooks/reference/)

`native-gate` 接受标记插入在上游 attestation 与 tamper 检查之后。已有协议测试覆盖默认 advisory、不具备 attestation 时拒绝、计划被篡改后即使移除 stall 标记仍拒绝、重入保护、Cursor 非正常结束及 loop 上限。Copilot 官方 `agentStop` 当前输入的 `stopReason` 为 `end_turn`，并提供 `stop_hook_active`；因此没有照搬 Cursor 的 `status` 字段过滤不是缺陷。[Copilot agentStop](https://docs.github.com/en/copilot/reference/hooks-reference#agentstop--stop)

桥接从宿主 payload 解析项目目录，在调用包内 Python 时使用 `-I -B`，避免项目同名模块参与导入或在包中产生字节码。脚本协议测试使用中文与空格路径，并检查安装目录及只读项目内容不变。它们证明脚本执行边界，不能证明宿主实际触发了相应 hook。

Codex Windows `commandWindows` 的解码结果引用了包内 launcher，已有测试验证对应文件齐全。Cursor/Gemini 的启动命令需要环境提供 `python3`；Copilot 提供独立 `powershell` 命令。当前没有真实 Windows 执行证据，不能从 Linux Python 协议检查推出 Windows 启动、环境变量替换或路径转义已经通过。

## 已观察的 OpenCode 本地宿主结果

`tests/run-opencode-native.py` 在临时包副本中安装锁定运行依赖，通过 `.opencode/plugins` loader 与 `.opencode/skills/project-docs` 运行真实宿主。审查阶段运行 `pd-030-opencode-native-02` 的结果为 Passed：

- A 0.3.0、B 0.3.1、回退 A 三阶段均发现 `pd_init`、`pd_status`、`pd_check` 和一个 `project-docs`；`pd_check` 返回相应插件版本。
- 单独空白项目中的 `pd_init` 读取带探针标记的包内模板，证实资产来自被测插件包。
- 删除本插件 loader 与主 Skill 后，新宿主进程不再发现它们。
- 原始 prepared 包、已有项目记录均未改变；临时 profile 已清理。

第一轮因 sandbox 阻止 npm 代理连接而失败；授权范围内的依赖下载重试后上述检查通过。原始失败日志和通过日志均保留。这次运行早于 NR-02 修复，不能作为语言资源修复的验收。最终运行 `pd-030-records-opencode` 基于修复后的真实 `dist` 再次通过上述全部检查，并通过五种语言资源与唯一入口的新检查；保存的 `source-files.json` 与最终 manifest 的 OpenCode 文件清单完全一致。该轮保留此前 `pd-030-final-opencode-03` 增加的 Skill 资源新增、修改和删除标记；`skill-fixture-delta.json` 明确列出三种差异，宿主报告路径内的完整资源比较在 A/B/回退 A 均通过，没有旧文件残留。较早证据仍保留，但长期文档保护以补充真实嵌套记录后的本轮为准。这里的更新是本地 file URL 与新进程配置切换；远程 npm 安装更新及已有会话 reload 均为 Not Run。[OpenCode V1 plugins](https://opencode.ai/docs/plugins/)、[OpenCode V1 Skill discovery](https://opencode.ai/docs/skills/)、[1.18.29 debug 工具执行源码](https://github.com/anomalyco/opencode/blob/v1.18.29/packages/opencode/src/cli/cmd/debug/agent.handler.ts)

## 最终复验结果

最终分发冻结后重新执行下表检查，全部退出码为 0。Codex、Claude、Gemini、Pi 的来源树 SHA 与当前 manifest 一致；OpenCode 的完整来源文件清单与 manifest 一致。五个宿主探针均保护全部七条原始项目记录，临时 profile 已删除。

最终证据核查发现此前 fixture 只有根目录三文件与用户便笺，不足以证明长期文档保护。共享 fixture 已实际加入 `docs/specs/approved.md`、`docs/adr/decision.md`、`docs/reproduction/known.md` 的固定批准内容，并支持嵌套目录初始化。下表记录的是补充后重新运行的证据；七条记录的前后 SHA/执行位相同且与原始 fixture 内容相符，逐条结果保存于各目录的 `records-protection-summary.json`。回归测试另确认修改或删除任一新增长期文档会令保护检查失败。该补充只改变 runner 与测试项目，没有改变冻结的产品目录。

| 检查 | 最终结果 | 原始证据运行目录名 |
| --- | --- | --- |
| Codex 0.153.4 | A/B/回退/卸载 Passed，每版核对 276 文件，六个 Skill 可加载；implicit policy 不由该 API 暴露 | `pd-030-records-codex` |
| Claude Code 2.1.263 | A/B/回退/卸载 Passed，每版核对 268 文件；原生卸载后 538 个 orphan cache 文件仍在，随后整体临时 profile 清理 | `pd-030-records-claude` |
| Gemini CLI 0.58.0 | A/B/回退/卸载 Passed，每版核对 256 文件；本地源更新，不是远程 Git 分支更新验收 | `pd-030-records-gemini` |
| Pi 0.85.1 | 实际 npm tarball 的 A/B/回退/卸载 Passed，每版核对 49 文件 | `pd-030-records-pi` |
| OpenCode V1 1.18.29 | 本地包 A/B/回退及 Skill 资源增改删、工具执行、唯一主 Skill 与五语言资源、包内模板、移除 Passed | `pd-030-records-opencode` |
| Kiro 最终目录协议 | POSIX bootstrap、重复运行保护、安装目录与项目分离 Passed；真实 Kiro 宿主未运行 | `pd-030-final-kiro-protocol` |

原始命令、runner/test 快照、SHA 与完整输出交由主报告统一归档。NR-01、NR-02 的实现修复和上述范围内复验已闭环；Windows、远程发布渠道、真实会话 reload 和未执行模型试用继续保留 Not Run。
