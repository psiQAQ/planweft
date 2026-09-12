# REV-0014：0.5.1 文档职责映射源码审查

状态：**Passed（独立源码审查）**；日期：2026-09-13。独立 reviewer：`role_map_source_review` subagent；主 Agent 负责处理发现和运行最终门禁。

## 范围与方法

只读核对 Documentation Map 的 Skill 导航范围、AGENTS/CODEX 发现顺序、Hook 与 handoff marker 边界、构建生成关系、版本化 release policy/evidence/archive 绑定、发布 workflow 和对应离线夹具。审查不读取旧聊天、不修改文件、不执行发布。

## 发现与处理

| 编号 | 发现 | 处理 | 回审结果 |
| --- | --- | --- | --- |
| P2 | gate 只核对嵌入版本，未绑定 policy 文件名和 evidence 版本目录 | 对 0.5.1+ 强制 `support-policy-<version>.json` 与 `release/evidence/<version>/`；新增错名与跨版本目录拒绝夹具 | Passed |
| P1 | 新命名规则会拒绝冻结的 0.5.0 `support-policy-0.5.json` | 只为 `0.5.0` 保留该历史文件名例外；伪造的 `support-policy-0.5.0.json` 仍拒绝 | Passed |
| P2 | 中英文发布说明遗漏 0.5.0 历史例外 | 在两份说明中明确例外，且禁止为统一命名改写历史 policy/evidence | Passed |

## 结论与边界

- Optional Documentation Map 只由 Skill 作为受限导航约定消费；Hook helper 不读取或写入映射，marker、计划选择、cap 和 stall 语义不变。
- AGENTS 保持默认规则入口；CODEX 仅在任务命名或既有入口链接后读取。模板、角色说明和目录名不会自动注册能力。
- policy、evidence 目录和 archive 内版本现在严格一致；附件仍必须位于 evidence 根目录下且哈希匹配。
- 独立复核运行 `tests/test_document_release_gate.py`，**7/7 Passed**；`git diff --check` Passed。此前的地图、交接和生成一致性定向契约均通过。

本报告不替代完整离线测试、可信发布或 registry 静态安装；这些实际结果由 [REP-0014](../reproduction/0014-document-role-map.md) 和 `release/evidence/0.5.1/` 记录。
