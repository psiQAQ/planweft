# PLAN-0009：DeepSeek Harness 支持

目标：新增平台 ID `dsh`，统一生成、安装、更新与卸载；原生行为以官方 DSH 为准。
完成标准：独立平台包、CLI 范围与所有权保护、实际 Skill 发现、双语文档；完整 profile hooks 另需固定官方依赖和原生验证。

已完成：Skill-only 源码与 15 平台生成、最近 Git 根规则、DSH_HOME 展开、安装器生命周期测试和官方 provider 运行验证。
为保持 state/锁与 Skill 同一项目范围，DSH 项目安装要求从 Git 根执行；非根调用在任何安装写入前拒绝。
主 npm 版本暂保持未发布的 0.4.0-rc.1；旧 tarball 发布已取消，新增平台后必须重新打包审计，不复用旧摘要。

待确认：新增两个固定运行依赖：

| npm 包 | 版本 | 用途 |
| --- | --- | --- |
| @deepseek-ai/dsh-hooks-claude-code | 0.1.2-rc.1 | 运行已有 PWF command hooks，复用 DSH 官方事件/权限决策 |
| @deepseek-ai/dsh-skill-filesystem | 0.1.2-rc.1 | 从原生 bundle 的包内绝对目录提供 Skill |

影响：更新根 package.json/package-lock.json，并带入其传递依赖。适配器的资源从安装包定位，项目状态取会话 cwd。
拟增加 `dsh.bundle.patch` 与 `./dsh` export，保留 OpenCode 默认 export；DSH 使用 `dsh plugin --profile NAME add` 原生安装和 bundle 发现，不新增 marketplace。
完整 CLI 集成需要明确 profile 身份及更新/卸载所有权；默认 profile 不得被其他项目覆盖。

自动审批以 AGENTS.md 的依赖变更须确认条款拒绝了该步骤。未变更依赖清单；未以其他方式安装这两个项目运行依赖。
后续先取得对此依赖变更的确认，再实施完整 profile hooks、原生生命周期和独立审查。

验证：Node 20 Passed；官方 0.1.2-rc.1 Skill provider 唯一发现、加载与正文刷新 Passed。
完整 Python 首轮 55 Passed、1 Failed（遗漏 dsh 安装入口清单），补齐后定向安装契约 Passed；DSH hooks、模型会话、Windows/macOS Not Run。
源码研究固定于官方 c389f96bf3a9b6807cb71ed6bdad5849be0df6d8；实际运行使用 npm 已发布 0.1.2-rc.1，不把浮动 master 的声明当作已发布行为。

记录：[REP-0009](../reproduction/0009-dsh-skill.md)。工作保存在 feat/deepseek-harness，等待依赖确认后完成原生适配再合并。
