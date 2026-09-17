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
```

`record` 永远不会执行 JSON 中的命令字符串；观测结果、解释、验收条件和
freshness 分别记录。普通文件以流式 SHA-256 保存并在发布前复核，拒绝不支持
的完整性/来源值、越出授权项目的路径、符号链接、已变化的 Markdown 基线及
幂等键冲突。恢复在显式提供 `--apply` 前只读。该 helper 本地离线运行，不
替换宿主工具、不启用远程 reducer，也不改变默认 advisory Hook。`doctor` 只
读报告损坏/缺失引用、lock、预算和 local-only 证据。
