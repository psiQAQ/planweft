# 变更记录

## 0.7.0（P1 checkpoint/reducer 正式发布）

- 新增显式 `planweft state upgrade`，schema 1 store 保持只读，升级保留 store identity、迁移前备份和回退证据。
- 新增确定性 `state checkpoint --dry-run|--apply`，保留 Phase 标题、状态、未决事项、约束和 before/after 快照，支持冲突拒绝、重启恢复和幂等重放。
- 新增有限格式 `state reduce` 与 `state quote-verify`，只输出带 SHA-256/字节范围逐字引用的源事实，不生成解释、不启用远程 reducer。
- 新增 S14–S16、故障注入、schema 升级、数据保护、四路离线消融和 P1 发布门禁；真实 Agent/model、tokens/cost 和真实不同 Agent 接续保持 `Not Run`。

## 0.6.0（P0 状态证据正式发布）

- 新增默认关闭、任务侧 `.planweft-state/` 与安装器 `.planweft/` 分离的状态证据存储。
- 提供 `planweft state init|record|verify|recall|doctor|recover --dry-run`，支持 Artifact/Receipt、SHA-256、来源与完整性分层、逐字引用校验、幂等键、写前 hash、transaction journal、冲突拒绝和显式恢复。
- 记录和验证只处理数据，不重新执行 Receipt 中的命令；不启用远程 reducer，也不改变默认 advisory Hook。
- 本版发布门禁覆盖确定性离线、生成一致性、准确产物、隔离安装、项目文件冷读和独立源码/promotion review；真实 Agent/model、tokens/cost 和真实不同 Agent 接续保持 `Not Run`。

## 0.5.1（已发布至 `next` 和 `latest`；`v0.5.1` 为正式 source tag）

- 新增可选、人工可读的 `Documentation Map`：在已有文档索引中记录职责、实际位置、更新触发条件和生成来源，不要求迁移、脚手架或机器状态。
- `project-docs` 按任务路径、AGENTS、README、受限的 CODEX 和已有文档索引导航；模板、角色说明和输出目录不会被目录名自动认定为已启用或权威。
- 发布 gate 与可信发布 workflow 改为严格绑定同一 `0.5.x` policy、evidence 和 npm archive，保留 0.5.0 与 0.4.0 记录。
- 在候选归档、registry 静态安装和独立 promotion evidence 均通过后，维护者将同一不可变归档提升至 `latest`；最终 source record 由 annotated `v0.5.1` tag 标记。
- 在 tag 创建后，以同一 `v0.5.1` 创建公开的 [GitHub Release](https://github.com/psiQAQ/planweft/releases/tag/v0.5.1)，不附加新构建产物。

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
