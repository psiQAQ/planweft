# 0.5.1 独立源码审查

状态：Passed。日期：2026-09-13。

独立 reviewer `role_map_source_review` 只读审查实现、生成关系、Hook/Skill 边界和 release gate。其发现与修复回审见 [REV-0014](../../../../docs/reviews/0014-document-role-map-source-review.md)：

- 路径绑定缺口已修复，错名 policy 与跨版本 evidence 目录有拒绝夹具。
- 0.5.0 仅保留冻结的 `support-policy-0.5.json` 历史文件名例外；伪造的完整 patch 文件名仍被拒绝。
- 中英文发布说明已同步该例外。

审查者复核 `tests/test_document_release_gate.py` 7/7 通过和 `git diff --check` 通过；不替代完整测试或 registry 检查。
