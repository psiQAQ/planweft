# 0.5.1 项目文件冷读

状态：Passed。日期：2026-09-13。

独立 reviewer `role_map_cold_read` 只接收项目文件快照，不读取旧聊天、主 Agent 计划或发布凭据。完整记录见 [REV-0014](../../../../docs/reviews/0014-document-role-map-cold-read.md)。

- 可从规格、ADR、计划、复现、索引与分发 reference 恢复目标及职责边界。
- 审查指出的 0.5.0/0.5.x 标题混淆、动态阶段不一致和缺少映射示例均已处理。
- 候选发布、registry 验证与 promotion 仍明确为后续步骤，不因为冷读通过而变为已发布。

本检查仅验证项目文件的可读性和声明边界，不执行构建、发布或安装。
