# REV-0017：SoL-Pi P0 项目文件 cold-read

日期：2026-09-17。状态：**Passed（文件-only 范围）**。

## 范围与限制

本轮不读取旧聊天、Agent 运行历史、个人模型配置或凭据；只读取当前 checkout 的项目文件。读取范围为：根 `README.md`/`README.en.md`、`AGENTS.md`、`docs/development.md`、`docs/releasing.md`、SoL-Pi 主计划和 validation plan、P0 spec/ADR、REV-0016 源码审查、`package.json`、`scripts/build-plugin.py`、`bin/planweft.mjs`、P0 Skill reference、`release/support-policy-0.6.0.json` 和 `check-state-release-gate.py`。

这是项目文件可读性与发布边界检查，不是 Agent/model session acceptance；本轮没有调用 Agent、模型、真实宿主会话，也没有测量 tokens/cost。

## 冷读结论

| 检查项 | 观察 | 判定 |
| --- | --- | --- |
| 当前目标 | 项目目标是将任务计划、发现和验证记录保存为可读、可接续、可核验的项目文件；本轮 P0 增加任务侧状态证据，而非替换宿主工具 | Passed |
| P0 接口 | spec 和 Skill reference 对 `init`、`record`、`verify`、`recall`、`doctor`、`recover --dry-run` 给出一致入口；`.planweft-state/` 与安装器 `.planweft/` 分离且默认关闭 | Passed |
| 证据边界 | Receipt 分离来源、完整性、执行证据、criteria/freshness；`record` 将命令字符串作为数据，不重新执行；quote 需逐字节校验 | Passed |
| 实现来源 | `overlays/planweft/state/` 是规范源，builder 生成根 `lib/state/`、宿主包和 Skill 内实现；`dist/**` 不作为手工规范源 | Passed |
| 发布边界 | `0.6.0` 使用独立 policy/evidence；确定性 P0 结果不宣称真实宿主、Agent/model 或成本结果 | Passed |
| 未完成范围 | checkpoint/reducer 属于 P1；真实 Agent/model、tokens/cost、真实不同 Agent 接续为永久 `Not Run`，除非用户另行明确要求 | Passed（限制已公开） |
| 分支治理 | `AGENTS.md` 要求发布后先以 `archive/<branch>-<date>` annotated tag 归档，再删除其他本地/远程分支，最终只保留 `master` | Passed |

## 可追溯证据

- 源码整改与离线覆盖见 [REV-0016](0016-sol-pi-state-management-review.md)，F-01–F-08 的整改复核已通过；其保留真实模型和 tokens/cost 的 `Not Run` 边界。
- P0 门禁定义见 [`release/support-policy-0.6.0.json`](../../release/support-policy-0.6.0.json) 和 [`check-state-release-gate.py`](../../scripts/check-state-release-gate.py)。
- 当前源码版本为 `0.6.0`；生成产物必须由 `scripts/build-plugin.py` 重建并用 `--verify` 核对。

本记录只证明项目文件之间的目标、接口、来源和限制没有出现会误导发布的矛盾；它不把静态 cold-read 提升为真实模型或宿主验收。
