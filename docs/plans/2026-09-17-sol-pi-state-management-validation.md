# SoL-Pi 移植计划：文档交付验证与基线问题

日期：2026-09-17。对应[实施计划](2026-09-17-sol-pi-state-management.md)。本记录是文档交付时的观察，不是功能实现或发布验收。实施 Agent 在 M0 中先核对本记录。

## 已提交的设计输入

主计划共 559 行，涵盖 P0/M0–M4/R0、P1/M5–M6/R1、数据契约、路径边界、可恢复写入、诊断、检查点、确定性 reducer、16 个测试场景及发布流程。`docs/README.md` 提供人工导航；它不是运行时输入或当前任务状态。

主计划与导航的检查对象为 `c8ad2a4eedb2b08a3c1bd0f5f5fa4f89070905a6`。相对基线 `46abb8fbca94abf3d46fd2500f105967d16a30f5`，当时的 diff 只有主计划新增和导航增加一行，共 560 行新增、无删除；本验证记录及导航中的记录链接随后补入，同样属于 docs-only 变更。

本轮没有实现新 helper、修改源代码或生成目录，没有改变版本、依赖、tag、registry 或历史 release evidence。独立依据 review、项目文件冷读和新功能测试尚未执行，均为 Not Run，已列为实施门禁。

## 实际 CI 观察

通过 GitHub Actions 的 job steps 与完整 distribution 日志核对了以下两个准确提交。基线检查是在短期分支刚从 master 创建、尚未加入本次文档时运行；不能把它误称为包含新计划的运行。

- 基线提交：`46abb8fbca94abf3d46fd2500f105967d16a30f5`；[run 35214325981](https://github.com/psiQAQ/planweft/actions/runs/35214325981)。
- 文档提交：`c8ad2a4eedb2b08a3c1bd0f5f5fa4f89070905a6`；[run 35214912716](https://github.com/psiQAQ/planweft/actions/runs/35214912716)。

| 检查 | 基线提交 | 文档提交 |
| --- | --- | --- |
| installer / Ubuntu | Passed | Passed |
| installer / Windows | Passed | Passed |
| installer / macOS | Passed | Passed |
| distribution：`python3 scripts/build-plugin.py --verify` | Failed | Failed |
| distribution：完整 Python unittest discover | Not Run（前置步骤失败，CI skipped） | Not Run（前置步骤失败，CI skipped） |
| distribution：release preparation | Not Run（前置步骤失败，CI skipped） | Not Run（前置步骤失败，CI skipped） |

三个 installer job 的实际步骤包括 Node 安装器测试、DSH hook shell 测试、Python record_templates 与 local_operations 测试；这不等于完整 Python suite、真实模型工作流或发布门禁已通过。

两个 distribution 日志报告的差异名称和数量相同：15 个宿主目录各有 `INSTALL.md` / `INSTALL.en.md` 两项差异，Codex mirror 同样两项，`manifest.json` 一项，`docs/installation.md` / `docs/installation.en.md` 两项。`marketplaces`、retired directories 和 retired archives 的差异为零，最终 `verified: false`，退出码 1。

日志入口：[基线 distribution job 105179061012](https://github.com/psiQAQ/planweft/actions/runs/35214325981/job/105179061012)、[文档 distribution job 105180983908](https://github.com/psiQAQ/planweft/actions/runs/35214912716/job/105180983908)。

结论范围：生成一致性失败在本次文档加入之前已经存在，本次两文件 diff 未修改报错的规范源或生成文件。这里证明的是已有基线生成差异，不是其具体根因已完成定位；不得据此把 Failed 改成 Passed，也不得把以上 CI 结果自动延伸到后续实现提交。

本轮没有在独立本地 checkout 运行完整测试或 `git diff --check`；这些检查保持 Not Run。主 Agent 完成了接口读取、关键文档回读及远端提交文件范围核对，不冒充独立 reviewer。

## M0 的前置处理

先同步并检查当前 master 是否已修复该差异。若仍存在，在隔离工作区保存 `--verify` 的失败结果，比较 `overlays/planweft/install/INSTALL*.md`、builder 与生成安装文档，识别规范源与生成产物为何不一致。不要凭差异数量直接假定根因，也不要手改 `dist/**`。

确认正确的规范源后，使用既有 builder 重建，检查实际 diff，并将必要基线修复作为独立提交；不要把它与 SoL-Pi 新功能混在一个无法归因的变更中。随后重新执行实施计划第 13.1 节的检查并记录真实结果，再开始新功能的性能/行为 baseline。无法修复时保留阻塞，不声称已经具备可发布基线。

本轮短期分支名为 `docs/sol-pi-state-management-20260917`。只有确认其提交已由 master 保护后才可清理；本验证记录不证明合并或删除已经发生。不要为了清理分支而丢弃独立历史。
