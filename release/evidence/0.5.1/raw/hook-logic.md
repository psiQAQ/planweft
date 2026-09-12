# 0.5.1 Hook 静态逻辑

状态：Passed。日期：2026-09-13。

- `tests/test_document_handoff.py` 验证 `Documentation Handoff` 的缺失、非法、重复与三种有效状态，以及 gated、只读、禁用、cap、stall 和 Stop 能力差异。
- `tests/test_documentation_map_contract.py` 验证 map 不作为 handoff helper 输入；包含映射、配置、环境、缓存、模板、局部 Skill、agent 和未选择日志的夹具不触发读取或写入。
- 17 项 map、handoff、entrypoint 与 release-gate 定向测试通过；Hook 仍只读地处理既有 handoff 状态。

本版本没有把 Documentation Map 加入 Hook 分类、阻断预算或命令执行路径。
