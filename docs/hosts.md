[简体中文](hosts.md) | [English](hosts.en.md)

# 宿主分发与能力边界

PlanWeft 0.6.0 的 `dist/manifest.json` 列出 15 个宿主分发目标。当前产品层面将 `codex`、`claude`、`pi`、`opencode` 和 `dsh` 作为主要支持集成，其余目标按实验性适配处理。分发目标表示包为该宿主准备了资源，不表示宿主已经发现、信任、启用或实际加载这些资源。

## 如何阅读本页

- “产品状态”回答当前是否作为主要支持集成提供，或仍属于实验性适配。
- “静态事件”来自当前生成的 manifest、Hook 配置或原生适配器源码，描述包准备了哪些接入点。
- “历史验收证据”只记录已完成过的精确版本验收，不自动证明当前版本的真实宿主行为。
- 当前版本的 P0 发布检查以[版本策略文件](https://github.com/psiQAQ/planweft/blob/master/release/support-policy-0.6.0.json)为准；本版确定性静态/逻辑检查不代替真实宿主或模型回归，后者按本任务记录为 `Not Run`。

## 宿主矩阵

| 宿主 | 分发形态 | 静态事件或原生入口 | 产品状态 | 历史验收证据 |
| --- | --- | --- | --- | --- |
| `agents` | 便携 `project-docs` Skill | 无执行 Hook | 实验性 | — |
| `claude` | Claude 插件 + Skill | `SessionStart`、`UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`PreCompact`、`Stop` | 主要支持 | 0.4.0 正式核心 |
| `codebuddy` | 插件清单 + 便携 Skill | 无执行 Hook | 实验性 | — |
| `codex` | Codex marketplace 插件 + 原生 Skill | `SessionStart`、`UserPromptSubmit`、`PreToolUse`、`PermissionRequest`、`PostToolUse`、`PreCompact`、`Stop` | 主要支持 | 0.4.0 正式核心 |
| `continue` | 便携 Skill/提示词 | 无执行 Hook | 实验性 | — |
| `copilot` | 原生插件 + Skill | `sessionStart`、`postToolUse`、`agentStop` | 实验性 | — |
| `cursor` | Cursor 插件 + Skill | `sessionStart`、`postToolUse`、`stop` | 实验性 | — |
| `dsh` | DSH profile bundle + Skill | `SessionStart`、`UserPromptSubmit`、`PostToolUse`、`Stop` | 主要支持 | 0.4.0 正式核心 |
| `factory` | 插件清单 + 便携 Skill | 无执行 Hook | 实验性 | — |
| `gemini` | Gemini extension + Skill | `SessionStart`、`BeforeAgent`、`AfterTool`、`PreCompress` | 实验性 | — |
| `hermes` | 原生插件 + Skill | `pre_llm_call`、`post_tool_call`、`pre_verify` | 实验性 | — |
| `kiro` | Power/插件清单 + Skill | 无执行 Hook | 实验性 | — |
| `mastracode` | 便携 Skill | 无执行 Hook | 实验性 | — |
| `opencode` | V1 插件 + 独立 Skill | `chat.message`、`tool.execute.after`、`session.idle` | 主要支持 | 0.4.0 正式核心 |
| `pi` | Skill + TypeScript Extension | `session_start`、`input`、`before_agent_start`、`tool_call`、`tool_result`、`agent_end`、`session_before_compact` | 主要支持 | 0.4.0 正式核心 |

“无执行 Hook”不是缺少实现的占位符，而是当前分发事实：宿主可以获得 Skill 或资源，但本包不因此增加宿主原本没有的生命周期事件。

## 能力差异

完整集成由安装器按宿主布局部署。Skill-only 只提供可发现的 `project-docs` Skill，不注册完整插件 Hook。原生扩展、JSON Hook、profile bundle 和便携 Skill 的发现与信任流程不同。

默认模式是 advisory：Hook 可以提供上下文或提醒，但不会自动修改长期文档。autonomous/gated 必须显式启用；是否能续跑或阻止结束取决于宿主协议和当前条件，不会凭空增加能力。

一次任务是否真正生效，应分别检查：

1. 安装器记录了正确宿主和 scope；
2. 宿主发现、信任并启用了资源；
3. 当前会话加载了期望版本；
4. 相关 Hook 已启用（如果该宿主提供完整集成）；
5. 模型实际读取了 `project-docs` Skill；
6. 任务记录产生了预期内容；
7. 后续会话可以从项目记录恢复工作。

`doctor` 主要检查受管安装状态，不能替代第 4 至 7 项。

## 验收证据与当前支持的关系

产品状态和验收证据是两个不同维度。表中的“主要支持”描述当前安装和文档面向的核心集成；“0.4.0 正式核心”仅说明该精确归档曾完成对应范围的正式验收。0.6.0 的确定性 P0 结果不等同于真实宿主或模型环境已验证，不能由分发目录数量自动推出。

## 故障定位

- 没有上下文时，按安装记录、宿主发现/信任、启用/重载、会话加载、事件支持、Skill 读取的顺序检查。
- manifest、源码和目录树只能证明静态分发关系，不能证明宿主加载、模型读取或任务正确。
- 真实检查应记录环境、输入、输出和 `Passed` / `Failed` / `Inconclusive` / `Not Run`；不要用历史版本结果补齐未执行场景。

安装和更新方法见[安装指南](installation.md)，运行模型见[架构说明](architecture.md)。
