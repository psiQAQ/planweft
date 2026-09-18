# PlanWeft 状态证据

可选的任务侧证据存储与安装器状态分离：所选 PWF 计划目录下的
`.planweft-state/` 属于任务记录，`.planweft/` 仍由安装器管理。

显式初始化：

```text
planweft state init
```

再将 JSON 数据文件交给 `record`：

```text
planweft state record --input evidence.json
planweft state verify --receipt <receipt-id>
planweft state recall --artifact <sha256> --start-byte 0 --length 120
planweft state doctor
planweft state recover --transaction <id> --dry-run
planweft state upgrade
planweft state checkpoint --dry-run
planweft state reduce --artifact <sha256>
planweft state quote-verify --input reduced.json
```

`record` 永远不会执行 JSON 中的命令字符串；观测结果、解释、验收条件和
freshness 分别记录。普通文件以流式 SHA-256 保存并在发布前复核，拒绝不支持
的完整性/来源值、越出授权项目的路径、符号链接、已变化的 Markdown 基线及
幂等键冲突。恢复在显式提供 `--apply` 前只读。该 helper 本地离线运行，不
替换宿主工具、不启用远程 reducer，也不改变默认 advisory Hook。`doctor` 只
读报告损坏/缺失引用、lock、预算和 local-only 证据。

P1 使用 schema 2。来自 PlanWeft 0.6.x 的 schema 1 store 仍可读，但在 owner
显式运行 `planweft state upgrade` 之前拒绝所有写入；升级前会保存并校验
备份。Checkpoint 默认 opt-in：dry-run 只读，apply 保存完整 before/after
快照，并可用 `--checkpoint <id>` 恢复未完成的 apply。活动计划保留 Goal
前置内容、Phase 标题、状态和未决约束；已完成阶段的详细正文可从
checkpoint 恢复。

本地 reducer 只识别有限格式的文本和 JSON 结果字段。每条事实都带有绑定源
Artifact 的字节区间引文，`quote-verify` 会重新核对这些字节。无法识别、采集
不完整或矛盾的输入保持 unknown/limited；解释与原文分离，本版本不调用远程
模型，也不执行收据中的命令。
