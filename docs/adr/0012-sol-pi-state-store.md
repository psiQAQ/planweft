# ADR-0012：采用独立的任务侧 SoL-Pi 状态证据存储

- 状态：实施中，P0 schema 已冻结
- 日期：2026-09-17
- 相关计划：[SoL-Pi 状态管理实施与正式发布](../plans/2026-09-17-sol-pi-state-management.md)

## 背景

PlanWeft 需要保存 Artifact、Receipt 和恢复线索，但安装器已有 `.planweft/` 生命周期状态。混用目录会把安装成功、任务证据和宿主配置变成同一份可写状态，难以保护人工修改，也无法区分 freshness、criteria、exit code 和实际执行证据。

## 决策

采用所选计划目录下独立的 `.planweft-state/`，默认关闭，由 `planweft state init` 显式创建。Node 核心只依赖标准库，由 builder 生成到根 `lib/state/` 与各宿主包的 `state/`；Skill 包只携带数据型 wrapper 和同一份核心，不接管宿主工具。

写入使用单 owner lock、写前摘要、transaction journal 和冲突拒绝。Artifact 先以流式 SHA-256 复制到内容寻址存储，Receipt 再记录来源、完整性、观测结果和验证范围。恢复只在 `--apply` 下修改文件，不能把退出码 0 推断为阶段完成，也不提供全局原子事务承诺。

## 被拒绝的方案

1. 复用 `.planweft/`：会混淆安装器状态与任务证据，且破坏现有安装器契约。
2. `record` 重新执行命令：不可审计、可能产生副作用；因此命令字符串只作为输入数据。
3. 远程 reducer 或默认 Hook 写入：超出本地证据范围并改变既有 advisory 行为；本版本明确关闭。
4. 仅依赖 exit code：无法表达 freshness、criteria、人工判定和 `Not Run`，因此各字段分开冻结。

## 后续

Checkpoint proposal/apply、有限确定性摘录和 reducer 只在 P1 独立升级后加入；旧 schema 的写入保护、回退与升级门禁必须另行验收。
