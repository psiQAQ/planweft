# 0.5.1 Skill 与 Hook 关联

状态：Passed。日期：2026-09-13。

- `tests/test_skill_entrypoints.py` 验证生成的语言入口受长度约束、说明 Skill-first 默认路径、兼容控制入口、授权边界和资源契约。
- `tests/test_document_handoff.py` 验证所有生成入口含相同的 handoff 与 optional map 摘要。
- `tests/test_documentation_map_contract.py` 验证所有生成 Skill 都带有同字节的 `references/documentation-map.md`。
- `python3 scripts/build-plugin.py --verify` 确认 `dist/**` 与插件镜像均由生成器产生，15 个目标零差异。

因此 map 是 Skill 的受限导航资源，不是 Hook 输入；不支持 Stop 的包装仍保持提醒-only。
