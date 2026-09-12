# REP-0013：PlanWeft 0.5.0 Skill/Hook 文档交接

状态：静态/逻辑实现验证完成；发布与 promotion 未执行。需求与边界见
[SPEC-0006](../specs/0006-skill-hook-document-handoff.md)、
[ADR-0010](../adr/0010-skill-hook-document-handoff.md) 和
[PLAN-0011](../plans/0011-skill-hook-document-handoff.md)。

## 输入与范围

- 用户提供的研究提案已原样纳入：`planweft-document-management-proposal.md`，SHA-256 为 `e1cafbf781c7a3f3a4e2e7efd149102ec10ee932571e9f91563e868220ef824d`。
- 版本为 `0.5.0`；固定上游仍为 PWF v3.17.0。
- 本记录只覆盖本地构建、夹具、静态包清单、源码审查和项目文件冷读；不包含 npm registry 发布或 dist-tag 变更。

## 已执行验证

| 检查 | 结果 | 实际观察 |
| --- | --- | --- |
| `python3 scripts/build-plugin.py` 与 `--verify` | Passed | 15 个平台、Codex mirror、manifest、marketplace 与公开文档均为零差异；生成物仅由构建器更新。 |
| `npm run check` | Passed | 构建一致性通过；Node 安装器 123 Passed、1 Skipped，DSH shell 3 Passed。 |
| 非容器 Python 回归 | Passed | 297 项通过、1 项 Skip；覆盖 marker、release gate、native Hook、模板、Skill entrypoint、PWF 包装、公开文档、选择与发布策略。容器专用模块未纳入本次执行。 |
| `npm pack --dry-run --json` | Passed | 识别 `planweft@0.5.0`，报告 4,339 个可打包成员、5,258,664 bytes 和完整性值；不落地产物、不发布。 |
| `git diff --check` | Passed | 无空白错误。 |
| 独立源码审查 | Passed | [REV-0013 source review](../reviews/0013-skill-hook-document-handoff-source-review.md) 复核 marker、Hook 边界、archive/evidence gate 与公开声明。 |
| 独立项目文件冷读 | Passed | [REV-0013 cold read](../reviews/0013-skill-hook-document-handoff-cold-read.md) 恢复目标、职责、历史限制与后续 registry 阶段，并发现后已修复的文档/门禁问题。 |

`test_project_isolation` 与 `test_review_feedback` 的参数拒绝夹具会打印预期的 argparse 错误；其 unittest 分组仍以零退出码通过。

## 门禁逻辑结果

`support-policy-0.5.json` 与 `check-document-release-gate.py` 的夹具验证了：Passed 记录必须绑定传入 archive 的 SHA-256、archive 内唯一的 `package/package.json`（`planweft@0.5.0`）以及 evidence JSON 目录内的实际附件/摘要；错误包身份、篡改 archive、非法/越界/缺失附件、附件摘要不符和非对象 manifest 都被拒绝。

这些是 gate 实现的离线逻辑证据，不是一次 0.5.0 发布放行。预发布 gate 只能在干净的发布提交生成唯一 `.tgz` 和证据附件后执行。

## 后续发布阶段

| 项目 | 状态 | 原因 |
| --- | --- | --- |
| registry archive identity、registry 静态安装、promotion review | Not Run | 尚未发布到 `next`；不得以本地 dry-run 代替官方 registry 证据。 |
| `latest` promotion、annotated `v0.5.0` tag 与远端写入 | Not Run | 需在预发布和 promotion 证据齐备后单独授权/执行。 |

0.4.0 的历史记录保持在其原有文档与 policy 中，未被写作本版 Passed。
