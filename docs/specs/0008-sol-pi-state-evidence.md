# SoL-Pi 状态证据规格

状态证据是 PlanWeft 的可选任务侧记录层，用于保存实现计划、生成物和验收收据之间的可复核关联。它不是安装器状态 `.planweft/`，也不是宿主工具的替代品。

## 范围

- 状态目录固定为所选计划目录下的 `.planweft-state/`；未显式执行 `state init` 时不创建。
- `store.json` 绑定 `store_id`、`plan_id`、schema version 和能力开关。当前 schema 为 `1`，checkpoint 与远程 reducer 明确关闭。
- 生成物以流式方式复制到 `.planweft-state/artifacts/sha256/<前两位>/<SHA-256>`，发布前 flush 并复核；Receipt 只引用摘要、字节数、来源等级、介质类型和完整性状态，不保存绝对路径。
- Receipt 记录 `execution`、`observed_result`、`interpretation` 与 `criteria` 为不同字段；exit code 不自动把阶段标为完成。
- Artifact 的 `capture_completeness` 只能是 `complete`、`truncated` 或 `unknown`；`origin` 区分 `controlled_capture`、`imported`、`reported`、`derived`，不得用默认值升级来源。`freshness` 独立于 `criteria`，未知时必须显式保留 `unknown`。
- `excerpts` 只允许引用已登记 Artifact 的字节范围，并在 `verify` 时逐字节校验 UTF-8 引文。
- 任务文件追加必须携带写前 SHA-256；冲突拒绝，transaction journal 只提供有限恢复，不宣称全局原子事务。

## CLI 合同

```text
planweft state init
planweft state record --input <JSON-file>
planweft state verify --receipt <receipt-id>
planweft state recall --artifact <sha256> --start-byte <n> --length <n>
planweft state doctor
planweft state recover --transaction <id> --dry-run
```

`record` 的 JSON 是数据输入；其中出现的命令字符串永远不会被执行。`PLANNING_DISABLED=1` 时 `init`、`record` 和 `doctor` 只返回 disabled/read-only 结果。`recover` 默认 dry-run，`--apply` 是显式恢复写入。`doctor` 只读报告 schema、预算、lock、损坏/缺失引用、stale 和 local-only 状态。

## 验收边界

S01–S13 覆盖初始化隔离、流式摘要、Receipt、引文、幂等键、freshness/criteria 分离、路径越界、symlink、人工修改保护、事务 journal、重启恢复和跨会话读取。真实 Agent/模型回归与真实 token/cost 仍按发布计划单独标记 `Not Run`，不能由离线 CLI 测试替代。
