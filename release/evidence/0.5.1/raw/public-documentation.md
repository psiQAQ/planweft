# 0.5.1 公开文档

状态：Passed。日期：2026-09-13。

- 更新中英文 README、CHANGELOG 和发布说明，说明 0.5.1 仅计划发布到 `next`，而 `latest` 和 `v0.5.1` tag 不在本次 candidate 范围。
- `docs/README.md` 在已存在的索引中提供可选 Documentation Map 示例，列出职责、位置、更新触发条件和来源，且不复制动态任务状态。
- `python3 -m unittest tests/test_public_docs.py -v`：2 项通过，语言对和公开命令一致。
- SPEC-0007、ADR-0011、PLAN-0012、REP-0014、两份 REV-0014 与设计引用台账记录了边界、决定、验证与依据。

公开文档不将候选发布写作已完成，也不把映射描述成强制项目结构或 Hook 状态。
