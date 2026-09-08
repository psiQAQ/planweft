# Codex 语言变体发现与原生策略附录

这是主归档之后的两次**无模型、无认证挂载**预检。原始归档和失败记录未覆盖。

真实 `skills/list` 确认：CLI 0.149.1 递归发现主 Skill 与 ar/de/es/zh/zht 五个嵌套变体，均已启用，`errors=[]`。旧系统校验器对 `i18n` 缺少 SKILL.md 的报错没有在实际宿主重现。

最终 Codex 包仅新增五份 `agents/openai.yaml`，各自设 `allow_implicit_invocation: false`；主入口的 `true` 保留。源包与实际安装缓存逐字节一致，七条原生 hooks 元数据、安装、卸载和清理仍通过。既有文件与运行时均未变。

**观测边界：** `SkillsListResponse` 的实际 schema 没有 policy 或 implicit 字段。列表中的 `enabled=true` 不能解释为“允许隐式调用”；加 false 后列表仍相同。本轮证实原生策略文件已安装与宿主发现正常，没有额外调用模型来直接观察语言变体的隐式选择抑制。

- [完整前后预检归档](skill-discovery.tar.gz)
- [逐文件 SHA 清单](skill-discovery-manifest.json)
- [包差异、策略原文、真实名称与 schema 字段](skill-discovery-summary.json)

当前最终 Codex ZIP SHA-256：`4fa81f93c4b6dfdc839f0ad34731afdab0d9a37f6a27056a76c76f64f5c91044`。此前主归档的 `preflight-final` 指当时最终包 `8177bbdb...`，应结合本附录阅读。至此共 14 次真实模型会话、6 次无模型预检。
