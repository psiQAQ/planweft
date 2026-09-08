# ADR-0006：固定 PWF 运行时并附加项目文档流程

状态：Accepted；日期：2026-09-08；需求：[SPEC-0003](../specs/0003-pwf-based-plugin.md) PDB-01～10，用户明确要求实施。

## 问题与决定

0.1.0 的单 Skill 已能分发文档协作约定，但没有任务状态选择、hook 恢复、运行时门禁和跨宿主实现。用户本轮要求以 PWF 为底座继承这些能力，再附加项目长期知识维护；这是需求变化，不是从旧配对实验推导出收益。

| 方案 | 取舍 |
| --- | --- |
| 继续只增强 0.1.0 指令 | 实现成本低，但不满足本轮移植 hooks 和多平台运行时要求 |
| 固定 PWF 快照，维护本地扩展，生成独立分发 | 保留可回归的成熟实现与宿主差异；增加上游同步、身份映射及分发检查成本；采用 |
| 全部重新实现为 TypeScript 或直接持续跟踪上游主分支 | 前者扩大语义重写风险，后者使导入不可复核；不采用 |

固定 PWF v3.17.0 / `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`。快照保留运行时、适配、模板及相关测试；本地产品规则、身份映射和必要修复独立维护，由构建生成安装包。生成物不可分别手改，构建检查按内容验证一致性。研究子模块仍是原版本的历史资料。

## 继承与附加

继承 PWF 的计划解析、三个工作文件、hooks、ledger、attestation 和显式自动化选项，保留其状态变量及磁盘格式。保留平台原生语言，不为统一技术栈重写语义；独立产品身份覆盖所有调用入口和 fallback，避免加载原 PWF。分发含上游 `Copyright (c) 2026 Ahmad Adi` 与完整 MIT 许可。

本地附加的是稳定知识维护：当前执行状态归选中 `task_plan.md`，发现和过程归 findings/progress，需长期保留的需求、决定、复现证据写入项目现有文档；不建立多份可独立变更的任务状态。不强制每次创建 specs、ADR、reproduction，也不默认建立完成归档服务。首次采用才做单向状态入口迁移。

主 Skill 安装后按任务自动匹配，保留用户和项目规则优先、只读不写、保护批准需求和历史的边界。重要设计与交接利用现有 Agent 能力独立核查，不新增调度引擎。默认提醒；gated 和摘要校验只能证明它们各自检查的条件，不承担语义验收或人工授权。

## 依据与本地差异

本轮直接依据是 [PWF 固定源码](https://github.com/OthmanAdi/planning-with-files/tree/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7)：`skills/planning-with-files/SKILL.md` 的 Restore Project State、Quick Start、File Purposes；`scripts/resolve-plan-dir.sh`、`check-complete.sh`；`.codex-plugin/plugin.json`、`hooks/codex-hooks.json`；`.pi/skills/planning-with-files/extensions/planning-with-files/` 与 `.opencode/packages/opencode-planning-with-files/`。这些是移植来源，不代表本地测试已经通过。

上游 `docs/workflow.md` 的 After Completion 明确三文件服务当前任务且无自动归档，长期保留知识需另存；本地 specs/ADR/reproduction 分工与其相容。具体逐文件引用、独立依据 reviewer 和只读覆盖规则来自 SPEC-0001 REQ-04～06、本仓既有 PD-03～07 及本轮用户要求，不冒称上游已实现完整项目治理。

Codex [官方 hooks 文档](https://learn.chatgpt.com/docs/hooks) 的 Runtime behavior、Where Codex looks for hooks 和 Plugin-bundled hooks（访问 2026-09-08）支持独立 hooks 文件、插件声明及 trust 边界；多个匹配文件均运行，所以必须分别验证重复安装与生命周期实际送达。现有系统 Skill 的旧校验器不作为当前协议的唯一依据，也不为移植而修改它。

## 替代、后果与确认

本决定替代 ADR-0005 在 0.1.0 范围内选择“仅单 Skill、无 hooks”的实现取舍，以及 SPEC-0002 PD-02 的项目显式启用前提；SPEC-0001 REQ-09 的语言和双平台方向更新为保留上游原生实现并继承全部适配。旧依据和实验保持历史，不改写为对本版的验证。专用文档写回引擎继续不实施，ADR-0003 的自身迁移限制继续有效。

新增维护成本由固定版本、导入摘要、本地补丁记录、原始/移植回归及可重建分发承担。自动匹配和文档维护依赖模型遵循；hook 事件和可续跑能力依赖宿主，不能归一化为全平台同等保障。未知宿主只读意图通过显式关闭设置补足，实际行为单独测试。

确认见 [REP-0005](../reproduction/0005-pwf-based-plugin.md) 的来源、运行、宿主和行为分层结果；独立依据 review 必须报告实际检查及未解决发现。只有实际环境与证据支持的项才标 Passed，不以本 ADR 的 Accepted 代替验证完成。
