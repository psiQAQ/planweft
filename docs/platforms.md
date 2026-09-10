[简体中文](platforms.md) | [English](platforms.en.md)

# 平台支持与限制

PlanWeft 0.4.0 对五个宿主提供正式核心支持，并为十个平台提供实验性分发。这里的“支持”只覆盖已声明并通过验收的能力，不表示所有宿主具有相同的 hooks、续跑或权限模型。

安装命令见[安装指南](installation.md)。逐项策略以 [`release/support-policy.json`](../release/support-policy.json) 为准，实际结果保存在 [`release/acceptance.json`](../release/acceptance.json)。

## 正式支持的宿主

| 宿主 | 安装标识 | 核心能力 | 0.4.0 模型工作流 |
| --- | --- | --- | --- |
| Codex | `codex` | Passed | explicit 维护和独立冷读 Passed |
| Claude Code | `claude` | Passed | 未列为正式模型工作流 |
| Pi | `pi` | Passed | explicit/auto 维护和冷读在冻结条件下 Passed，按证据定级 |
| OpenCode V1 | `opencode` | Passed | 未列为正式模型工作流 |
| DeepSeek Harness | `dsh` | Passed | 未列为正式模型工作流 |

五宿主核心能力包括准确包内容、运行依赖、安装、更新、回退、卸载、重新安装、显式 Skill 读取、默认提醒、明确禁用、项目隔离、用户文件保护和重复来源检查。最终 registry 安装、原生发现、新会话加载与卸载也已通过 promotion 验收。

这些结果绑定 0.4.0 的准确 npm 归档，SHA-256 为 `e611338a619adabb0ba943d75460a01d83e4670dbe7d69f5d1050a1c1467c132`。文档调整不会把旧版本或其他运行条件自动纳入该结论。

## 实验性能力

以下能力可以使用，但不属于 0.4.0 的正式承诺：

- 所有宿主的 autonomous/gated 自动续跑和真实模型 stopping。
- Codex 以外宿主的自动模型采用，Pi 冻结对照中明确记录的结果除外。
- Cursor、Gemini CLI、GitHub Copilot CLI、Hermes、Mastra Code、Kiro、Continue、Factory、CodeBuddy 和通用 Agent Skills 的分发适配。
- 不同宿主、模型、权限或版本下的模型范围遵循。

实验适配器只声明实际完成的静态、协议或生命周期检查。目录或 manifest 存在不能证明宿主已加载插件，也不能证明模型按预期维护文档。

## 已知限制

- Codex gate-cap 开启/关闭配对为 **Failed**：trace 中仍有无法归因的 syscall 结果，因此 `trace_complete=false`。公开限制 ID 是 `LIMIT-CODEX-TRACE-INCOMPLETE`。会话正常结束，但该事实不能把场景改写为 Passed。
- 其他实验性 stopping 和模型场景包含 Not Run。未执行的场景保留原因，不由历史候选结果补齐。
- 模型范围遵循是评测结果，不是安全边界。文件系统、命令和网络权限仍由宿主及用户配置决定。
- 默认模式是 advisory。启用 gated 也只使用宿主实际提供的停止或 follow-up 机制，不会增加宿主没有的生命周期事件。
- Hermes 分发仍是实验性；历史默认扫描拒绝记录保留在 reproduction 中，不提供绕过扫描器的安装承诺。

## 宿主差异

完整集成由 `planweft` 安装器按宿主布局部署。Codex 和 Claude Code 使用各自的插件发现方式；Pi 同包携带 Skill 与 Extension；OpenCode V1 配对插件和独立 Skill；DSH 使用 profile bundle。GUI 或 Skill-only 平台可能需要宿主界面完成启用、信任或 hooks 合并。

项目记录与插件安装位置彼此独立。更新或卸载插件不会删除 `task_plan.md`、`findings.md`、`progress.md`、`.planning/`、attestation、ledger、specs、ADR 或 reproduction。一次会话只应启用一套规划执行 hooks。

## 工程资料

生成目录、catalog、事件协议、资源定位和发布树设计属于维护者资料：

- [开发与生成约定](development.md)
- [上游与分发维护](upstream-maintenance.md)
- [发布与证据维护](releasing.md)
- [0.4.0 复现记录](reproduction/0010-five-agent-release.md)
- [原生分发规格](specs/0004-native-distributions.md)

这些记录解释实现和历史证据，不扩大本页的支持承诺。
