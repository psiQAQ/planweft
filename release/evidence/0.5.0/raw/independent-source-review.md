# 0.5.0 独立源码审查

日期：2026-09-13。独立审查者以只读方式复核合并后的 `master`，结论为 Passed，
无发布阻断项。审查确认 0.5 policy 只包含静态/逻辑和 registry promotion 项，
冻结的 0.4 policy、SPEC-0005、ADR-0009、PLAN-0010 和 REP-0012 未被改写。

审查还确认：Hook 保持既有 selector、gated mode、in-progress、cap、stall 和递归短路；
文档交接检查器只在既有 block 后细化原因，且为只读。`build-plugin.py --verify`
对 15 个平台和生成物返回零差异；文档交接夹具 4 项通过，release gate 夹具 3 项通过。

审查发现的 `release_blocking` JSON 数字可替代 Boolean 的 P2 已修复；`0` 和 `1`
反例现被拒绝，并由同一离线夹具复核通过。
