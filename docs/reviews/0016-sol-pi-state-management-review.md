# REV-0016：SoL-Pi P0 状态管理源码审查

日期：2026-09-17。状态：**独立审查 Not Run；R0 阻塞**。

## 范围

本记录覆盖用户冻结的 P0 接口、`overlays/planweft/state/`、`bin/planweft.mjs`、`scripts/build-plugin.py`、生成的 `lib/state/` 与 15 个宿主 bundle，以及 `tests/state-evidence.test.mjs` 和 `tests/test_state_evidence.py`。不把主 Agent 的自审视为独立 reviewer 结论，也不把离线测试视为真实 Agent/模型回归。

## 主 Agent 第二遍核对

- `.planweft-state/` 与安装器 `.planweft/` 使用不同路径；未显式 init 时不会创建任务 store。
- `record` 只读取 JSON 和 regular file，流式复制并记录 SHA-256；输入中的 `execution.command` 没有执行路径。
- Receipt 将 `observed_result`、`interpretation`、`criteria`、来源和 Artifact 摘要分层；`Passed`、`Failed`、`Inconclusive`、`Not Run` 不由 exit code 推断。
- `verify` 检查 Receipt 绑定、Artifact 摘要和字节范围 quote；`recall` 有有限读取预算。
- Markdown 追加有写前 hash、二次 hash、journal、冲突拒绝和显式 `recover --apply`；journal 的目标与恢复 payload 做路径/regular-file 校验。
- builder 生成根 `lib/state/`、宿主包共享状态和 Skill 内 wrapper/core；`build-plugin.py --verify` 当前无 drift。

## 已执行但不替代独立审查的证据

- `node --test tests/state-evidence.test.mjs`：4 tests Passed。
- `python3 -m unittest tests.test_state_evidence -v`：2 tests Passed。
- `npm test`：124 Passed，1 skipped。
- `build-plugin.py --verify`：15 个宿主和 shared-state 全部 0 differences，Passed。
- 真实 Agent/model regression：Not Run，未用离线结果替代。

## 结论与退出条件

当前实现可以继续保留在 P0 功能分支，但不能据此宣称 R0 已通过。需要一名只读取项目文件、无旧聊天/预期答案的独立源码 reviewer，核对 schema/path/receipt/recovery 的边界并将结论追加为 Passed 或带具体阻塞的 Inconclusive；在此之前不发布 0.6.0、不创建或推送正式 tag。
