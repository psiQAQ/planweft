# REV-0016：SoL-Pi P0 状态管理源码审查

日期：2026-09-17。状态：**初审 Failed；整改复核已通过离线源码/夹具门禁；R0 仍需 cold-read 与发布门禁**。

## 范围

本轮按规格、ADR、源文件、生成器和测试重新取证；结论不沿用前一版自审中的正向判断。覆盖用户冻结的 P0 接口、`overlays/planweft/state/`、`bin/planweft.mjs`、`scripts/build-plugin.py`、生成的 `lib/state/` 与 15 个宿主 bundle，以及 `tests/state-evidence.test.mjs` 和 `tests/test_state_evidence.py`。本记录是源码级 review pass，不宣称第三方/真实 Agent/模型回归已执行。

## 已确认的正向边界

- `.planweft-state/` 与安装器 `.planweft/` 使用不同路径；未显式 init 时不会创建任务 store。
- `record` 只读取 JSON 和 regular file，流式复制并记录 SHA-256；输入中的 `execution.command` 没有执行路径。
- `verify` 会检查 Receipt 绑定、Artifact 摘要和字节范围 quote；`recall` 有有限读取预算，但其完整性缺口见 F-01。
- Markdown 追加具备写前 hash、二次 hash、journal、冲突拒绝和显式 `recover --apply` 的主路径；恢复并发和 payload 校验缺口见 F-04。
- builder 生成根 `lib/state/`、宿主包共享状态和 Skill 内 wrapper/core；`build-plugin.py --verify` 当前无 drift。

## 阻塞发现

| ID | 优先级 | 位置 | 证据与影响 |
| --- | --- | --- | --- |
| F-01 | P0 | `overlays/planweft/state/core.mjs:427-442` | `recallArtifact` 只检查对象存在并直接读取，不重新计算 SHA-256。独立临时夹具先记录 Artifact、再篡改对象，`recall` 返回 `tampered`，而同一 Receipt 的 `verify` 返回 `valid: false`。读取入口因此可把已损坏内容交给后续消费者，违反“recall 字节/完整性一致”和 S04。 |
| F-02 | P0 | `core.mjs:169-203, 234-258, 309-326, 367-412` | `capture_completeness` 默认被写成 `complete`、`origin` 默认被写成 `imported`，且没有枚举/来源真实性校验；任意 truthy `execution` 都输出 `reported`，任意 truthy `criteria` 都输出 `declared`。`freshness`、适用性、来源等级和实际执行证据没有独立语义，Receipt 可在没有相应证据时形成过强声明。 |
| F-03 | P0 | `core.mjs:84-92`、`cli.mjs:57-66` | direct-child 检查条件是恒假的：`path.dirname(resolved) !== parent` 不可能成立。独立夹具中的 `.planning/group/nested-plan` 被成功初始化并绑定为 `legacy-root`；同时显式 `--plan-dir`/`PLAN_DIR` 未由 CLI 限制在当前授权项目下。S02 的 named/legacy/wrong-binding/multiple-candidate 边界未被可靠保护。 |
| F-04 | P0 | `core.mjs:456-494` | `recoverTransaction` 不取得 store owner lock，也不验证 journal 的 store/plan/receipt 绑定；写入 `after.bin` 后不重新计算目标 hash 或 payload hash，就把 journal 标成 `committed`。恢复期间的并发 writer 可能竞争目标，损坏 payload 也可能被提交。 |
| F-05 | P0 | `core.mjs:152-163, 338-355` | Artifact 流式复制和 Markdown 替换均没有 `fsync`/等价 flush，也没有发布后的重新读取核对；计划明确要求写/flush/recheck 并将崩溃恢复作为契约。现有 happy-path journal 测试不能证明重启后的持久性或不会产生假 complete。 |
| F-06 | P0 | `core.mjs:107-150, 279-287, 445-453` | `doctor` 只返回 Receipt 数量、未完成 journal 和基础 capabilities，不扫描 missing/damaged references、stale evidence、storage budget、local-only 或 stale lock。lock 是无 owner/时间信息的裸目录，进程中断后可能永久阻塞；store 结构/能力值也只做很浅的校验。 |
| F-07 | P0 | `core.mjs:251-258, 291-294` | `record` 仅校验 excerpt 元数据和引用的 SHA，不在写 Receipt 前核对 `quote` 与 Artifact 字节；错误逐字引用可以先被发布，只有后续 `verify` 才暴露。这不满足不可发布错误摘录的 P0 验收语义。 |
| F-08 | P0 | `tests/state-evidence.test.mjs:56-167`、`tests/test_state_evidence.py:12-51` | 当前新增测试只有 Node 4 个和 Python 2 个主路径/生成一致性用例。没有覆盖 CRLF/二进制/空/大文件、截断/unknown exit、10 个固定 seed 的中断注入、重启、并发 worker/过期 lock、坏 schema/缺失引用、安装更新回退卸载、跨会话/跨机器 local-only。按计划 S03、S06–S13 及 M2/M3/M4 门禁，不能把现状标为 P0 完成。 |

这些问题不是单纯的真实 Agent/模型缺失；其中 F-01、F-03 已由本轮临时夹具复现，F-02、F-04、F-05、F-06、F-07 可直接由源码路径确认。修复前不能通过 R0。

## 场景覆盖判定

| 场景 | 本轮判定 | 依据 |
| --- | --- | --- |
| S01 | Partial | disabled/init 隔离主路径有测试；未覆盖所有只读变体。 |
| S02 | Failed | 嵌套计划被接受为 `legacy-root`；错误绑定/多个候选未覆盖。 |
| S03 | Not Run | 未见 CRLF、二进制、空文件、大文件和完整 recall 一致性矩阵。 |
| S04 | Partial/Failed | verify 能发现篡改，但 recall 可返回篡改字节；截断/unknown exit 未覆盖。 |
| S05 | Partial | 同 key 幂等和冲突有测试；真实再次运行和跨进程竞态未覆盖。 |
| S06 | Not Run | 没有逐写入点故障注入、重启和固定 seed 证据。 |
| S07 | Partial/Failed | 人工修改主路径有测试；恢复无 owner lock、过期 lock 和 worker 并发未覆盖。 |
| S08 | Partial | `..`、外部 symlink 和输入越界有测试；junction/祖先链接/Windows 路径矩阵未覆盖。 |
| S09 | Not Run | 没有 exit 0 但跳过/不全/代码变化的验收证据。 |
| S10 | Partial/Failed | doctor 无写入主路径有测试；诊断字段和坏 schema/引用完整性不足。 |
| S11 | Not Run | 未执行安装、更新、回退、卸载保留 store 的独立验证。 |
| S12 | Not Run | 未执行无聊天新会话/不同 Agent 接续。 |
| S13 | Not Run | 未执行跨机器 local-only 交接判定。 |

## 已执行的验证证据

- `PLAN_ID=2026-09-17-sol-pi-state-management-implementation node --test tests/state-evidence.test.mjs`：4 tests Passed；只能证明现有夹具，不覆盖上述缺口。
- `PLAN_ID=2026-09-17-sol-pi-state-management-implementation python3 -m unittest tests.test_state_evidence -v`：2 tests Passed。
- `PLAN_ID=2026-09-17-sol-pi-state-management-implementation python3 scripts/build-plugin.py --verify`：15 个宿主、shared-state、Codex mirror、manifest 和公开文档均 0 differences，Passed。
- `git diff --check`：Passed；工作区在 review 取证前后保持 clean。
- 此前提交已记录的 `npm test`、完整 Python discover、`test_public_docs` 结果仍分别为 Passed；这些结果不能抵消本审查发现的源码和覆盖缺口。
- 真实 Agent/model regression、真实 tokens/cost：Not Run；没有用离线测试替代。

## 结论与退出条件

本轮 review 结论为 **Failed**，不是“仅因真实 Agent 未运行而 Inconclusive”。F-01 至 F-08 中任一 P0 问题都足以阻塞 R0；当前至少有完整性读取、路径绑定、恢复并发/持久性、Receipt 语义、doctor 和测试矩阵多个阻塞。保留现有功能分支和历史证据，不合并到 master，不创建或推送 `v0.6.0`，不发布 npm/GitHub Release。

初审退出条件（整改前）：修复并测试 recall 完整性、来源/完整性/freshness schema、计划路径绑定、带 owner lock 的 recovery、写后验证和 doctor；补齐 S03/S04/S06–S13、固定 seed 故障注入及安装生命周期证据，然后重新运行 builder、全套离线门禁、项目 cold-read 和本 review。

## 2026-09-17 整改复核

本轮已在同一功能分支修复 F-01–F-08，并由 builder 重新生成所有产物；下表只记录可观察的源码/离线证据，不把真实 Agent 或模型回归写成 Passed。

| 发现 | 整改结果 | 新证据 |
| --- | --- | --- |
| F-01 recall 未校验 Artifact | **Passed** | `recall` 在返回前后校验对象 SHA-256/字节数；篡改 recall 现在返回 exit 4。 |
| F-02 来源、完整性、execution、freshness/criteria 语义过宽 | **Passed** | 增加枚举和 schema 校验；Artifact 写入完整性状态；Receipt 分离 `structure_check`、`source_check`、`execution_evidence`、`criteria_check`、`freshness_check`。 |
| F-03 计划绑定可接受嵌套/越界候选 | **Passed** | 只接受 `.planning` 直接子计划，并限制选定 project 在命令工作目录内；nested/outside fixtures 均拒绝。 |
| F-04 recovery 无 owner lock/写后校验 | **Passed** | recovery apply 取得 owner lock，校验 journal/Receipt/payload，重新计算目标 hash；固定中断状态和 lock 冲突用例通过。 |
| F-05 缺少 flush/recheck | **Passed** | JSON、Artifact staging 和 Markdown 临时文件均 flush；最终发布和 recovery 后重新读取核对。 |
| F-06 doctor 诊断不足 | **Passed** | doctor 只读报告 schema、预算、使用量、missing/damaged references、stale、local-only 和 lock；坏 schema/损坏对象/预算边界有夹具。 |
| F-07 record 可发布错误 quote | **Passed** | record 在写 Receipt 前逐字节校验 quote；错误 quote 被 exit 2 拒绝。 |
| F-08 场景与故障证据不足 | **Passed（离线范围）** | Node 状态夹具 12 Passed，含 CRLF/二进制/空/大文件、移动项目、包替换 smoke、10 个固定 seed 恢复矩阵；Python 生成一致性 2 Passed；完整 Python discover 360 Passed、1 skipped。 |

整改复核仍保留两项边界：固定 seed 矩阵验证持久化中断状态和恢复路径，不等同于付费 Agent pilot；真实 Agent/model、tokens/cost 和 S12 的真实不同 Agent 接续仍为 `Not Run`。R0 还需要项目 cold-read、准确 candidate/readback 和独立 promotion review，不能因本轮离线全绿提前发布。
