# PLAN-0009：DeepSeek Harness 支持

状态：实现与本地验收完成；待分批提交、master 合并和重新准备候选包。
目标：平台 ID `dsh` 的统一生成、原生 profile 安装、更新、回退与卸载，以及独立 Skill。

已完成：

- 15 平台生成；单 npm 与独立 DSH 平台目录都有原生 bundle 声明和相同 ./dsh 入口。
- 用户级完整 profile（默认 headless，--dsh-profile 可选择）；原生来源链接到完整持久版本。
- Skill-only 保留项目/用户 scope；非 Git 根项目调用在 preflight 拒绝，DSH_HOME 遵循原生展开。
- 固定两个官方运行依赖与锁文件：dsh-hooks-claude-code、dsh-skill-filesystem，均 0.1.2-rc.1。用户已明确批准依赖与传递依赖变更，先前审批阻塞已解除。
- SessionStart/UserPromptSubmit/PostToolUse/Stop 使用官方桥接；按安装包定位资源，状态取各会话 cwd。
- 原生 A/B 生命周期、实际配置展开、官方 Skill provider 及真实 hook 子进程协议验证；中英文安装指南、能力边界、独立依据与失败恢复审查。

验证：Python 58 Passed；最终 Node 27 Passed。DSH 原生安装、A/B 新增/修改/删除、回退、卸载、重装与唯一 bundle Passed；真实 bridge/子进程的项目隔离、提示刷新、恢复、默认停止、下游拒绝保持和 PLANNING_DISABLED Passed。

限制：协议测试使用显式测试事件载体，不是模型会话；没有 PreCompact，PreToolUse 上下文不被 DSH 接收，Stop systemMessage 不展示。完整 gated 模型续跑、DSH 模型维护和 Windows/macOS Not Run。保持官方不同宿主能力边界，不宣称全部事件等价。

独立审查发现并处理：原生 link 绝对/相对值在部分持久化后恢复、显式 profile 与卸载身份一致、重复 hooks 的 skill-only/注释误报。所有权验证保留用户其他 profile 配置，不自动删除个人 profile 或原版 PWF。

发布：旧 rc.1 发布已取消，新平台加入后重新构建和审计，不能复用旧归档摘要。此前 Git 历史隐私确认、npm 发布认证及稳定版核心宿主模型门槛仍按 PLAN-0008 处理。
证据：[REP-0009](../reproduction/0009-dsh-skill.md)。
