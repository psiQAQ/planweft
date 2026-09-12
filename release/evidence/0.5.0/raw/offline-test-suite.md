# 0.5.0 离线测试

日期：2026-09-13。合并后的 `master` 已执行 `npm run check`：构建器的
`--verify` 对 15 个平台及公开产物返回零差异；Node 安装器为 123 Passed、1 Skipped，
DSH Hook shell 为 3 Passed。

同一实现批次还执行了文档交接、模板、分发和 release-gate 的离线 unittest 夹具；
PowerShell 夹具因本机没有 PowerShell 保持 Skip，其余该批次夹具通过。
