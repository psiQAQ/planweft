# REP-0014：PlanWeft 0.5.1 可选文档职责映射

状态：Prepublication Passed；日期：2026-09-13。需求与设计见 [SPEC-0007](../specs/0007-document-role-map.md)、[ADR-0011](../adr/0011-optional-document-role-map.md) 与 [PLAN-0012](../plans/0012-document-role-map.md)。

## 输入与范围

- 版本目标为 `0.5.1`，固定上游仍为 PWF v3.17.0。
- 映射只作为已存在索引中的人类可读导航；不创建固定使用方目录，不作为 Hook 输入或计划状态。
- candidate 仅发布至 `next`；`latest` promotion 和 `v0.5.1` tag 不在本次范围内。

## 验证记录

| 检查 | 状态 | 实际观察 |
| --- | --- | --- |
| 构建与分发一致性 | Passed | `build-plugin.py --verify` 的 15 个目标零差异；Node 24.20.0/npm 11.11.0 生成的候选归档 SHA-256 为 `8071dee2ffe8c0500e739e17723cf307d3c29276055bbc5a8d1c860358419b28`。 |
| 离线 Skill/Hook、模板与 release-gate 契约 | Passed | map、handoff、entrypoint 与 release-gate 的 17 项定向契约通过；完整离线 suite 350 项通过、1 项既有条件跳过。早先本地化入口超过 110 行的失败已保留在选中 task plan 的 progress 记录，修复后才进行本次完整重跑。 |
| 公开文档与安装器 | Passed | `test_public_docs.py` 2 项通过；`npm run check` 的安装器 123 项通过、1 项跳过，DSH hook shell 3 项通过。 |
| 独立源码审查 | Passed | [REV-0014](../reviews/0014-document-role-map-source-review.md) 记录路径绑定与 0.5.0 历史兼容修复的回审。 |
| 项目文件冷读 | Passed | [REV-0014](../reviews/0014-document-role-map-cold-read.md) 记录仅基于项目快照的目标、边界和状态可读性检查。 |
| 预发布 release gate | Passed | `check-document-release-gate.py` 已核对同版本 policy、evidence、附件摘要和候选归档。 |
| `next` candidate 与 registry 静态安装 | Not Run | 等待提交、推送和可信发布 workflow；完成后新增 promotion evidence。 |

预发布的实际结果、归档摘要与附件已写入 `release/evidence/0.5.1/prepublication.json`；未执行项不写作 Passed。`latest` promotion 与 `v0.5.1` tag 仍不在本次范围内。
