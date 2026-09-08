# REV-0007：公开文档的双语与来源归属审查

日期：2026-09-08。Reviewer：readme_positioning；主 Agent 负责修改和验证。审查对象为本轮工作区，基线为 `ff9e6a4`。本 reviewer 没有直接编辑 README、安装指南、平台设计或运行时实现，但此前提供了 README 比较表的双语建议及来源分析。因此，对比较与归属段的核对属于来源复核，不能把该范围称为完全独立于内容形成的审查；安装、平台及 README 其余整合内容由不同作者编写。

## 范围与方法

- 比较 `README.md` 与 `README.en.md` 的产品范围、工作流、比较表、归属和能力边界；核对同一事实是否在两种语言中保留。
- 读取固定研究 checkout 中 OpenSpec `docs/concepts.md`、Superpowers `skills/writing-plans/SKILL.md` 与 `.pi/extensions/superpowers.ts`、doc-coauthoring `SKILL.md`、MADR 完整模板；从受追溯的 PWF v3.17.0 归档读取主 Skill 与 `docs/workflow.md`。精确提交由 [资料索引](../reference/README.md) 和 [引用台账](../design-references.md) 登记。
- 对照本地 `overlays/program-design/workflow.md`、`references/evidence.md`、构建/分发清单及 [REP-0006](../reproduction/0006-native-distributions.md)。区分提示约定、运行时机制、已执行证据与未运行场景。
- 安装文档全文按宿主章节对照；同时检查代码块与官方引用集合是否相同。平台文档全文与 REP-0006 的逐平台记录对照；施工中的缺失链接不作为最终缺陷。

## README 审查结果

**Passed：未发现阻断性来源或能力主张问题。** 中英均将比较限定为本仓固定参考版本的关注点，不作效果排名；引用链接指向同一组固定原文。比较与归属段的独立性限制如上，已请主 Agent 安排未参与该段建议的 reviewer 补查。

| 核查点 | 结果及依据 |
| --- | --- |
| PWF 的继承边界 | 三文件、恢复和状态协议列作直接移植；README 明确 PWF 已建议长期知识另存，与固定 `docs/workflow.md` 的 After Completion 一致，没有把此划分认领为本地首创 |
| OpenSpec 与 Superpowers | 说明只借鉴职责分离、与风险相称的严谨度、可接续计划和薄适配；未宣称集成其完整引擎或必需 Skill 链 |
| doc-coauthoring 与 MADR | 冷读检查归于前者；依据审查另列本地要求；ADR 结构归于后者，未把它描述成任务恢复运行时 |
| 本地贡献 | 工作流整合、生成器、适配修复和发布准备指向实际本仓实现；明确“原创实现”不等于方法首创或已证明跨平台效果一致 |
| 自动化与文档行为 | 自动匹配限定支持的宿主；默认提醒、显式运行模式与信任要求有边界；独立 review 是 Skill 约定，不声称存在新增调度服务或必然自动完成 |
| 状态与证据 | 14 平台目录与版本匹配分发清单；8 宿主历史生命周期、Hermes 安装拒绝及 GUI/OS/远程/模型 Not Run 与 REP-0006 对应；不把文档变化视为新的宿主实测 |
| 双语入口 | 两份首页均有双向语言切换，公开安装/平台导航均提供中英链接；工程资料保留原语言并标注，未伪造英语副本 |

非阻断文字发现（已关闭）：英文任务步骤 2 的 `authorized complex implementation` 比中文“获准执行的复杂工作”略窄，也不完全覆盖前文的调查和设计用途。主 Agent 已改为 `authorized complex work`，reviewer 复核一致。

## 安装指南与随包介绍

**Passed：未发现需要修正的实质双语差异。** 已逐宿主核查 `overlays/program-design/install/INSTALL.md` / `INSTALL.en.md`，并对照随包 `README.md` / `README.en.md`。

- 14 宿主的发现目录、完整包复制、安装 scope、更新来源、重载与卸载边界两种语言一致。17 个 fenced 代码块逐字相同；23 个官方引用 URL 的集合相同。
- Codex hooks 信任与安装分开；Pi 显式激活、OpenCode V1 预编译包与独立 Skill 配对、Hermes SHA 配对与扫描拒绝、Droid 实际注册名、Copilot 原位加载，以及 Skill-only 平台的限制均在英文保留。
- 中英均把当前无公开 Git/npm 地址写清楚；发布参数不是可直接安装的已上线坐标。文档说明显式更新、完整替换、防止混版和保留项目记录，不引入统一 updater。
- Hermes 的 42/41 findings 属于历史包观察，明确本次双语修改未重跑扫描。随包文档没有依赖仓库外层 `docs/` 才能解释安装所需步骤；主 Skill 的引用采用包内路径。
- 每份随包文档开头提供双语入口，安装指南的重复引用也同时给出中英版本。英文随包首页保留了只读开关的适配验证限制，没有扩大 `PLANNING_DISABLED=1` 的保证范围。

## 跨平台设计

**Passed：两项发现修正后复核通过，未留未解决实质发现。** `docs/platforms.md` / `platforms.en.md` 均有 7 个对应章节，19 个官方 URL 的集合相同；九个实际运行过插件管理或加载检查的宿主版本一致，Hermes 仍保留安装 Failed。

| 发现 | 影响 | 处理与复核 |
| --- | --- | --- |
| P2：初稿对不能识别只读的宿主统一建议设置 `PLANNING_DISABLED=1`，没有保留安装指南的适配验证限定 | 容易被理解为单个环境变量能在所有 14 个平台充分关闭运行行为 | 作者在两种语言中补齐：严格只读或完全关闭使用宿主禁用机制；环境变量只在已验证适配路径上充分；补充部分继承路径仍围绕根计划。reviewer 复核与安装指南一致，Closed |
| P2：验证章节未明确本次双语文档与既有同日同版本宿主证据的区别 | 读者可能把 0.3.0 历史宿主或 Hermes 扫描结果当作当前文档字节的复验 | 两种语言均明确本次双语调整未重跑真实宿主或扫描器，既有结果对应原 0.3.0 交付；尾句也明确版本范围。Closed |

原生包入口、六 catalog、14 平台渠道、安装资产与项目记录分离，以及状态/语言资源说明两种语言一致。逐平台矩阵与 REP-0006 保持同样的静态、协议、安装、生命周期、实际加载区分；没有将目录存在、协议测试、Codex 合成响应或 OpenCode debug 扩大为模型语义效果验证。官方 Codex 插件链接在线打开后正常重定向到 [Plugins](https://learn.chatgpt.com/docs/plugins)，没有发现失效。

## 独立性补充

README 比较与原创段另由未参与这些建议的 bilingual_install reviewer 复核，其具体结果见本轮另行保存的审查记录或主 Agent 的验证记录。本报告的比较段只记录已经执行的来源核对，不认领另一位 reviewer 的结论。安装与跨平台正文由其他 Agent 编写，本 reviewer 对这两组内容的审查独立于其写作。

## 验证边界

本次为文档与来源审查，没有重新运行真实宿主、模型维护或冷读实验。README 的对应段落仅引用 0.3.0 历史验证。生成物包含英文文件、链接有效性及运行文件不变由主 Agent 的本轮检查另记；本报告不以源码阅读替代这些检查。
