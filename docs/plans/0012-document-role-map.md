# PLAN-0012：可选文档职责映射

状态：Complete；日期：2026-09-13；需求：[SPEC-0007](../specs/0007-document-role-map.md)。

## Goal

发布 PlanWeft 0.5.1：在不增加状态引擎或固定项目结构的前提下，将可选文档职责映射分发给所有 `project-docs` Skill 入口，并以同版本静态门禁发布到 `next`。

### Phase 1: 规格与受限导航

- **Status:** complete
- 确认职责映射只在已有索引中维护，AGENTS 优先、CODEX 受限，并保留 0.5 交接 Hook。

### Phase 2: 源码、生成与版本化门禁

- **Status:** complete
- 更新 workflow/reference、所有生成入口、0.5.x policy/evidence 解析与可信发布工作流。

### Phase 3: 验证、审查与 candidate 发布

- **Status:** complete
- 离线验证、独立源码审查、项目文件冷读、预发布与 registry promotion evidence 均已通过；0.5.1 已发布到 `next`。

## Documentation Handoff

<!-- planweft-docs-status: complete -->
- Documents considered: SPEC-0007、ADR-0011、公开说明、release policy、REP-0014、独立审查与设计引用台账。
- Rationale / evidence: 已在既有 `docs/README.md` 建立可选映射，在所有生成入口分发 reference，并以 REP-0014、release evidence 与审查记录保存验证及发布结果。
- Next action: 仅在维护者认证后按独立流程评估 `latest` promotion 和 `v0.5.1` tag；本计划不执行这些操作。
