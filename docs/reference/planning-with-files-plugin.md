# planning-with-files：插件与本项目的相似点

来源 P-01：[OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files)。作者 Ahmad Adi / OthmanAdi；本地固定 commit `d47a61950e784fc4237ba10ddc1e9e198bd0f275`，manifest 版本 3.16.1。访问与源码阅读日期：2026-09-08。许可 MIT，版权和许可见[上游 LICENSE](../../.submodule/OthmanAdi/planning-with-files/LICENSE)。本文为中文定向摘要及本地分析，不是全文翻译或安装说明。

本条是在本轮配对实验开始后，按用户补充要求整理；未改变试用的冻结提示、源码或参考输入。项目原已作为真正的 Git submodule 收录，不重复添加仓库或更新固定版本。

## 实际入口与原文要点

| 定位 | 可核查内容 |
| --- | --- |
| [Codex manifest](../../.submodule/OthmanAdi/planning-with-files/.codex-plugin/plugin.json)（[固定原文](https://github.com/OthmanAdi/planning-with-files/blob/d47a61950e784fc4237ba10ddc1e9e198bd0f275/.codex-plugin/plugin.json)） | 单个插件声明 `skills: ./.agents/skills/`，另声明 `hooks: ./hooks/codex-hooks.json`；不能把独立安装路径 `.codex/skills/` 当此 manifest 的加载根 |
| [插件实际 Skill](../../.submodule/OthmanAdi/planning-with-files/.agents/skills/planning-with-files/SKILL.md) 的 FIRST: Restore Project State、Quick Start、File Purposes（[固定原文](https://github.com/OthmanAdi/planning-with-files/blob/d47a61950e784fc4237ba10ddc1e9e198bd0f275/.agents/skills/planning-with-files/SKILL.md)） | 用持久文件保存计划、发现和进度；先解析任务所属计划再恢复；缺文件才创建、保留现有工作；共享计划由一个协调者维护。自动恢复限项目文件，读取会话存储需要用户显式请求相应模式 |
| [Codex hooks 描述](../../.submodule/OthmanAdi/planning-with-files/hooks/codex-hooks.json)（[固定原文](https://github.com/OthmanAdi/planning-with-files/blob/d47a61950e784fc4237ba10ddc1e9e198bd0f275/hooks/codex-hooks.json)） | 独立声明生命周期事件，并通过插件根定位脚本；这是该项目的实现选择，不能替代宿主官方能力与版本说明 |
| [插件操作测试](../../.submodule/OthmanAdi/planning-with-files/tests/test_codex_plugin_operations.py) 的 `test_manifest_selects_one_skill_root_and_codex_only_hooks`、`test_plugin_commands_are_cache_rooted_and_do_not_fallback_to_standalone`（[固定原文](https://github.com/OthmanAdi/planning-with-files/blob/d47a61950e784fc4237ba10ddc1e9e198bd0f275/tests/test_codex_plugin_operations.py)） | 有针对 Skill 根目录、宿主专用 hooks、插件缓存路径的测试；本轮只读源码，没有运行上游测试 |
| [评估说明](../../.submodule/OthmanAdi/planning-with-files/docs/evals.md) 的 Test 5 / What this test does not measure / Reproducing | 上游数字具有版本、任务、作者评分及原始实验材料限制；不用于证明 program-design 的效果 |

## 与本项目的比较及取舍

| 共同问题 | 可借鉴内容 | 本项目当前差异与验证办法 |
| --- | --- | --- |
| 长任务和新会话丢失进度 | 计划、发现、验证结果落入文件，接续时核对实际差异 | project-docs 沿用项目现有文档，不要求固定三个文件；用无旧聊天的冷读验证能否找到下一步 |
| 插件安装后读取错误的 Skill 或脚本 | manifest 指向明确入口，测试缓存路径和安装表面的一致性 | 当前仅一个 Skill、没有 hooks 脚本；核查真实安装及实际读取，不能凭源码存在就判定加载 |
| 多人或多 Agent 改写共享状态 | 一个共享计划维护者、明确任务所属文件 | 本项目已有分工及保护用户改动原则；本轮只验证保留未提交内容，不宣称已验证并发协调 |
| 自动恢复可能带来额外读取和维护负担 | 将项目文件恢复与显式会话历史读取分开 | 首版只按任务读取普通文档；不增加 transcript replay、计划锁、指纹或门禁。若以后需要，先记录真实失败与最小验证 |

研究边界：该版本实际 Skill 正文仍有 `CLAUDE_PLUGIN_ROOT` / `CLAUDE_SKILL_DIR` 与 Claude 安装路径示例。Codex 专用 hooks 描述不能证明所有正文命令均可直接用于 Codex；将来采纳时应核对具体路径与宿主行为。

结论：这是直接相关的参考实现，尤其适合借鉴文件接续、插件入口校验和实验限制披露。其 hooks、固定文件约定及复杂恢复机制是可研究的取舍，不构成本仓库当前必须复制的功能需求。此轮只补参考材料，不安装或运行该插件；上游实际运行、Windows 行为与效果复核均 **Not Run**。

返回 [参考索引](README.md)。
