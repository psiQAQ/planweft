# 变更记录

## 0.5.0（`next` 已发布；`latest` promotion 待维护者认证）

- 新增 `task_plan.md` 文档交接 marker；由 `project-docs` Skill 判断并在已授权范围维护文档，Hook 只读提醒。
- 显式 gated 且原 PWF gate 已满足时，pending 交接只细化该次 block 原因；不改变 selector、attestation、cap 或 stall。
- 0.5.0 采用静态/逻辑、独立源码审查和冷读门禁；不把 0.4.0 历史证据转写为本版结果。

## 0.4.0（2026-09-10）

- 发布统一的 `planweft` npm 包和安装 CLI，覆盖 Codex、Claude Code、Pi、OpenCode V1、DSH 及十个实验性平台适配器。
- 固定 planning-with-files v3.17.0，保留三文件计划协议、命名计划、attestation、ledger、禁用开关和有界续跑控制。
- 增加按需项目文档维护、设计依据检查、独立 review 和冷读交接规则。
- 为五个核心宿主提供准确产物、安装、更新、回退、卸载、重新安装、项目隔离、用户文件保护、重复来源检查和显式 Skill 读取。
- 将 Codex 显式维护到独立冷读列为正式工作流；Pi explicit/auto 对照按冻结证据定级。
- 引入 schema 3 发布门禁和 `release/support-policy.json`，保留 Failed、Inconclusive 和 Not Run 的原始含义。
- 通过 `next` 验收后将同一不可变归档提升到 `latest`。0.4.0 npm 归档 SHA-256 为 `e611338a619adabb0ba943d75460a01d83e4670dbe7d69f5d1050a1c1467c132`。

已知限制：autonomous/gated 和非正式模型工作流仍为实验性。Codex gate-cap 开启/关闭配对因 syscall 归因不完整保留为 Failed，限制 ID 为 `LIMIT-CODEX-TRACE-INCOMPLETE`。

## 预发布历史

0.4.0-rc.1 至 rc.15 用于验证 OIDC 发布、确定性构建、五宿主生命周期、模型维护、冷读和发布门禁。候选版本中的失败与修正没有改写为稳定版结果。逐轮状态、命令和附件保存在 [PLAN-0010](docs/plans/0010-five-agent-release.md)、[REP-0010](docs/reproduction/0010-five-agent-release.md)和相关 checkpoint/evidence 文件中。
