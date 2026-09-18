# PlanWeft Checkpoint 与确定性摘录

Checkpoint 是任务侧的显式 opt-in 操作，不接管宿主的 context compact，也永远
不会执行 Receipt 中记录的命令。

```text
planweft state checkpoint --dry-run
planweft state checkpoint --apply
planweft state checkpoint --checkpoint <id> --apply
```

`--dry-run` 只计算候选，不写文件。`--apply` 先保存
`task_plan.md`、`findings.md`、`progress.md` 的完整 before/after 快照，再只
替换安全可缩减的已完成 Phase 详细内容。候选必须保留计划前置内容、Phase
标题、状态字面量、未完成 Phase 和受保护约束。如果目标发生变化、存在未完成
事务，或候选没有变小，操作会停止。

进程在 apply 中断时，checkpoint 会保留在任务 store 中。使用
`planweft state checkpoint --checkpoint <id> --apply` 继续。人工无关修改会被
视为冲突，绝不覆盖。Checkpoint 快照是本地数据，继续受任务 store 的 ignore
策略保护。

P1 reducer 是本地确定性实现：

```text
planweft state reduce --artifact <sha256> --json > reduced.json
planweft state quote-verify --input reduced.json --json
```

它提取已识别的测试计数、失败/超时/错误行和已知 JSON 字段。每条事实都携带
Artifact hash、字节区间、行号和逐字 UTF-8 引文。无法识别或不完整的输入报告
为 unknown 或 limited。事实不会自动变成解释；解释是独立字段，本 helper 不
访问远程模型，也没有命令执行路径。
