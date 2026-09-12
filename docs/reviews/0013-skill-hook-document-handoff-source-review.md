# REV-0013：0.5.0 Skill/Hook 文档交接源码审查

审查类型：独立源码/条件审查。审查范围仅限项目快照、固定 PWF 包装、0.5.0 文档与离线测试；不读取旧聊天、宿主配置或敏感文件，不修改文件，也不运行外部工作流。

## 审查问题与处理

初次审查发现以下问题，均在进入本记录前由实现方修复并进行源码复核：

| 等级 | 发现 | 处理与复核结论 |
| --- | --- | --- |
| P1 | 0.5 gate 接受自声明 Passed、任意 64 位摘要和不存在的 evidence | gate 现要求 `--archive` 的实际 SHA-256、唯一 `package/package.json` 的 `planweft@0.5.0` 身份，以及 evidence JSON 同目录下的真实附件/摘要；拒绝自引用、绝对/`..` 路径、越界 symlink 和缺失附件。 |
| P1 | README 在 0.5.0 未发布时给出 `npx planweft@0.5.0` | README 明确 0.5.0 是未发布源码目标，快速开始保留 0.4.0 registry 命令。 |
| P2 | 合法 marker 与非法/节外 marker 混用时可能被误判为 complete | 检查器统计全文 HTML status marker，要求唯一且位于唯一章节；非法、重复、错位均为 pending。 |
| P2 | archive 内 `package/package.json` 为 JSON 非对象时会以 traceback 失败 | 先验证 manifest 是 object，再按统一 `ValueError` 拒绝；夹具覆盖数组 manifest。 |

## 保持的边界

- 新 helper 位于 PWF 的 selector、gated mode、Stop recursion、in-progress、cap 和 stall 短路之后；pending 只替换已允许的单次 block reason，不建立计数器或续跑协议。
- native Hook 对无法解析的 `PLAN_ID`/`PWF_PLAN_ROOT` 不回退到 cwd 计划；新路径只读取 resolver 与 marker，不写项目文档，也不猜测授权。
- 0.4.0 policy、acceptance 和历史运行时证据没有被改写。0.5.0 的 registry/promotion 验证留待发布阶段。

## 结论

**Passed。** 修复后的静态条件与公开声明一致；未发现会放宽原 PWF gate、产生 Hook 越权写入或把历史 0.4.0 证据扩大为 0.5.0 结果的阻断项。

本审查不替代发布阶段的 registry archive identity、临时安装静态 smoke 或独立 promotion review。
