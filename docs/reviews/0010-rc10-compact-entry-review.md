# RC10 compact entry: independent source review

本次是独立源码审查，不是 RC10 模型验收。审查范围为六语言入口、`workflow.md` 的仓库特例删除、入口引用的选择/证据/控制文档及现有生成器定位方式。未修改实现、运行时、生成分发或原始 RC9 失败记录；未启动容器或模型。

## 初次结论：一个 P2 待修正

**[P2] 只读限制被压缩为“不创建记录”，未明确禁止修改已有记录。** 六语言入口第 7 行把旧版“阅读、诊断和宿主规划模式保持只读”改成不创建规划记录；英文甚至是 `need no new planning records`。反例是一个已存在 `task_plan.md`/`progress.md` 的只读诊断：追加 findings 或更新阶段没有创建新记录，却违反原只读边界。后面的 resume、阶段更新和结束记录操作可能让这个差异产生实际影响。

`overlays/planweft/workflow.md` 第 9 行仍有完整的只读禁止列表，但不能据此认为分发已保留：`scripts/build-plugin.py` 的 `transform()` 在生成 `references/pwf-workflow.md` 时明确剥离该 workflow 前缀（本次检查位于第 282 行），并以各语言短入口替换正文。`plan-selection.md` 的范围段只禁止初始化；证据文档虽提到只读请求不授权写文档，也不能代替入口本身已丢失的限制。

最小修正是六语言恢复一个短句，区分两类边界：“阅读、诊断、宿主规划模式保持只读，不创建或修改项目记录；简单任务不需要新规划记录。”保留书面研究产物的明确授权例外；不要把简单代码修改误写成全部只读，也不需要恢复整段长列表。

## 已确认正确的结构变化

- 四步保留；英文初检为 660 个空白分隔词。长度是结果，不作为正确性的验收标准。
- 主入口要求**先读 selection reference，再执行 resolver**，仍明确空输出且退出码 0 不代表无计划。三分支为有效选择恢复、被拒绝/有歧义先修正而不新建、无计划且无待纠正绑定时才在已授权实施中初始化。
- 简体“既没有计划，也没有待纠正绑定，且实施已授权”与繁体对应表达都是 `NOT plan AND NOT pending_binding AND authorized`。英文 neither/nor、德文 weder/noch、西文 sin/ni、阿文 لا…ولا… 表达等价，没有误变成 `NOT (plan AND binding)` 或逻辑 OR。
- 拒绝的非空 `PLAN_ID`、无效/越界 `PWF_PLAN_ROOT`、多个计划的归属、legacy 根布局、Bash 的 cwd 与返回 ID、PowerShell/本地化初始化器的根三文件差异、缺一份记录时不得重复 named init，都仍在强制读取的双语 selection reference 中。主入口未引入新 helper、新磁盘状态或自动写入 hook。
- 禁止新增文件/采用/改变旧权威入口的例外现在要求引用实际指令。普通“最小修改、复用资料”不构成禁止；这不要求只读或简单任务另找一条逐字禁止，也不要求重新索取已经存在的实施授权。
- 分发入口删除开发仓库专属例外，`workflow.md` 改为尊重明确项目限制，范围合理。本仓库 `docs/plans/0010-five-agent-release.md` 第 27 行仍明确“不采用本仓根三文件”，本次删除没有移除这个本地约束。
- 六语言均保留单一动态状态、旧入口一次性相对链接、历史/批准需求/用户修改保护、一个 owner 与 worker 记录、独立任务分计划或 worktree。
- 对错误或更正的结束动作改为修正仍作为当前事实的源陈述，或标记旧观察时点并链接更正，然后**实际重读受影响陈述及依据**。这能覆盖 RC9 中发现更正但关联原陈述未更新的具体缺陷；不是把所有历史观察重写成最终事实。
- 实际执行、继承结果和未执行检查的证据分类，以及新读者对历史 Passed、未重跑项、实际执行项的区分，六语言等价。主入口未把静态读码当作测试，也没有授权回填虚构的较早执行结果。
- 手动 scratch/反事实目录仍限定授权项目内任务自有目录；没有通过文字变化授权清理非自有固定路径。此处是模型行为要求，不是强制文件系统隔离，也不是既往 `/tmp` 操作通过的证明。

## 离线验证

| 检查 | 结果 | 限制 |
| --- | --- | --- |
| `python3 -m unittest discover -s tests -p test_skill_entrypoints.py -v` | Passed，4 tests | 入口/元数据/资源契约，不证明模型遵守 |
| `python3 -m unittest discover -s tests -p test_plan_selection_contract.py -v` | Passed，4 tests | 实际 Shell helper 行为；未启动宿主 |
| 以内存 `transform()` + `distributions(..., compiled=False)` 检查全部 Skill/GUIDE 的 `references/` 与 `templates/` 相对链接 | Passed，15 平台、702 个链接，无缺失 | 未写出 generated，也未重新编译 OpenCode |
| 六语言分支、例外及记录收尾语义逐项阅读 | 除上述只读 P2 外未发现新的阻塞差异 | 人工源码审查，不是多语言模型行为成绩 |
| 新准确 RC10 模型验收 | Not Run | 主 Agent 后续对新准确包执行；不能沿用 RC9 或以显式调用替代自动匹配 |

初次源码 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `entrypoints/en.md` | `8e503e3184583f24c90469e14867053f4c711b034f0b0bcce52855a8473e0c68` |
| `entrypoints/zh.md` | `29f7120c4365d79c83f56e631079a4a733c301ff77960c68cbbac4b75343c425` |
| `entrypoints/zht.md` | `97029e789f1062ef90457937c606f2800f4883454cffe6362b166e961d1a9910` |
| `entrypoints/de.md` | `ae750dc9a5a7a5ac18b2a8f5235edf0a602c5ff0ba67c6e370c653a473cd4da8` |
| `entrypoints/es.md` | `a5b674d2373b98a0228b7ca9f3bbca33539647549bd5b249e126cb8bbca08ffd` |
| `entrypoints/ar.md` | `94eacf37f4981635658e4f854eb690088d878b69ef1010cba37e060b81f1c054` |
| `overlays/planweft/workflow.md` | `2935b0403a38d3cda0e1ce3d6d2b09d865d192569934091fcfc93f0db94f6f23` |
| `scripts/build-plugin.py` | `aca28a7aa68b84bc2b02e733500161aaf312d33548f883f19f6ff55b0f4da335` |
| `references/plan-selection.md` | `1600bb8e6b34a4e4b1f36dc7f644ec987ea9d2af778b50c4f895142386d7a745` |
| `references/plan-selection.zh.md` | `762c22a5889dc02765a87e16e1fbbaca7f6ca0c31ec030e7ecd1e031cf531f7e` |

上表 `entrypoints/` 和 `references/` 均相对于 `overlays/planweft/`。后续修正应追加关闭记录，保留本次发现，不用新的源码摘要冒充初次受审内容。

## 只读 P2 关闭与摘要采集时点更正

主 Agent 修正后，reviewer 再次实际读取六语言第 7 行。英文明确 `stay read-only: neither create nor modify project records`；简体为“保持只读，不创建或修改项目记录”，繁体对应“不建立或修改專案記錄”；德文 `keine Projektaufzeichnungen anlegen oder ändern`、西文 `no crean ni modifican registros del proyecto`、阿文 `لا تنشئ سجلات المشروع ولا تعدّلها` 均明确禁止创建和修改。简单任务另句处理为不需要新计划，没有错误扩大成简单代码修改全部只读。书面研究产物的明确授权例外仍保留。

**该 P2 在源码层面关闭，本轮 compact entry 审查 Passed。** 没有因此将未执行的新准确包模型验收改成 Passed，也没有变更 RC9 的失败分类。本次关闭仅重新读取实际源文件及计算摘要，未启动容器、模型或生成分发。

**纠正前表时间标签：** 首次缺陷判定来自当时读取到的旧正文（英文 `need no new planning records`，中文“不创建规划记录”）。reviewer 发出 P2 后，主 Agent 与审查并行修改；后续摘要采集时修复已经落盘。因此前表标为“初次源码 SHA-256”不准确：其中六语言摘要实际上绑定修正后的源码，不是含缺陷的旧版本。本次重新计算与前表完全相同。保留原发现和这次明确更正；没有留存旧版本完整文件摘要，不为它构造一个声称实测的摘要。

最终实际复核的六语言 SHA-256：

| 文件（相对于 `overlays/planweft/`） | SHA-256 |
| --- | --- |
| `entrypoints/en.md` | `8e503e3184583f24c90469e14867053f4c711b034f0b0bcce52855a8473e0c68` |
| `entrypoints/zh.md` | `29f7120c4365d79c83f56e631079a4a733c301ff77960c68cbbac4b75343c425` |
| `entrypoints/zht.md` | `97029e789f1062ef90457937c606f2800f4883454cffe6362b166e961d1a9910` |
| `entrypoints/de.md` | `ae750dc9a5a7a5ac18b2a8f5235edf0a602c5ff0ba67c6e370c653a473cd4da8` |
| `entrypoints/es.md` | `a5b674d2373b98a0228b7ca9f3bbca33539647549bd5b249e126cb8bbca08ffd` |
| `entrypoints/ar.md` | `94eacf37f4981635658e4f854eb690088d878b69ef1010cba37e060b81f1c054` |
