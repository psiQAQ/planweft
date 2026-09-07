# Codex 插件：最小封装和本地分发

来源：[OpenAI 官方 Package your plugin](https://developers.openai.com/plugins/build/plugins)。编号 R-21；作者 OpenAI；访问 2026-09-07。中文要点摘要；未确认全文翻译许可，不保存全文。

## 原文要点

`Create a plugin manually` 展示 manifest 与一个 Skill；`.codex-plugin/plugin.json` 指定身份、版本及组件，skills 位于插件根目录。

`Build your own curated plugin list`、`Install a local plugin manually` 指定 repo marketplace 位于 `.agents/plugins/marketplace.json`。source.path 相对 marketplace 根目录，而非 JSON 所在目录。`Add a marketplace from the CLI` 描述来源注册与管理，注册和安装分开。

`How local marketplaces work` 说明安装缓存和启用状态；源码更新不代表已安装副本同步。`Marketplace metadata` 分别声明安装策略、认证时机及类别。安装后以新会话核查实际能力。

## 本地解读与时效

本版采用最小 Skill 包，不从示例推断必须有 MCP、hooks 或外部账户。具体命令以本机 CLI help 及 REP-0003 实测为准。单 Skill、目录和项目 opt-in 是 ADR-0005 的本地选择，不是官方强制保证。

返回 [资料索引](README.md)。
