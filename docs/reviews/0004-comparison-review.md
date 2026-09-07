# REV-0004：对照试用的验收与依据审查

状态：**Passed（源码、资料依据、产物与所列运行证据审查）**。对照污染和一项冷读输出缺口保留，不能据此认定插件增量效果；宿主临时目录最终清理由主 Agent 记录。日期：2026-09-08。独立 reviewer：`comparison_contract_review` subagent。共同代码基线：`a5f072e`；本文件及验收器为该基线上新增工作区文件，不属于执行 Agent 的输入。

## 验收器预审与自检

独立编写 [入口契约验收器](../../tests/experiments/check-entry-contract.py)。它通过目标脚本的 `__main__` 与 CLI 参数边界运行，不要求目标新增特定函数、测试文件或采用某一种参数验证实现。默认场景列表从冻结基线独立登记，没有从待测实现动态取值，以免错误默认值同时改变预期。

无效输入检查退出码 2、错误提示、未尝试创建目录、未尝试调用进程或定位认证、输出及上级目录不存在。有效输入用受控 `subprocess.run` 和假 HOME 执行原有调度流程，覆盖默认场景、repo-copy、多个合法场景、正数超时、enabled 成功后 handoff 和失败时不 handoff。临时文件自动删除，不实际调用 Docker、模型或真实认证。

| 自检 | 实际结果 |
| --- | --- |
| 原始基线 | 13 项中 6 项通过；7 个无效输入均先尝试 mkdir，因替身阻断而失败 |
| 临时副本补充三个最小前置检查 | 13/13 通过；补丁仅存在于自动删除的临时副本，未带回待修复文件 |
| 临时副本取消 enabled 成功条件 | `enabled-failure-no-handoff` 失败，其余通过；证明验收器能发现该条件回归 |

边界：该工具是针对冻结脚本的离线行为验收，不是敌对代码沙箱。副作用替身覆盖该脚本现有 `Path.mkdir`、`Path.home`、`subprocess.run` 接口；源码审查仍需确认实现没有引入其他副作用通道。有效执行通过 fake process 隔离外部系统，不表示真实 Docker 或模型运行已通过。

## 来源和公平性依据

- 实际打开 [Python argparse 官方文档](https://docs.python.org/3/library/argparse.html#exiting-methods)：现有标准库支持选项校验、帮助和错误退出；重复场景、正数要求及副作用顺序是本轮用户需求，不伪装成 argparse 自动保证。
- 实际读取 P-03 `docs/concepts.md` 的 `Keep It Lightweight: Progressive Rigor`：主张满足可验证性所需的最轻规范；本轮不按规定文件数或目录布局奖励产物。
- 实际读取 P-06 `skills/doc-coauthoring/SKILL.md` 的 `Stage 3: Reader Testing`：支持不带旧会话上下文的独立读者；本轮将读者问题固定，不给完成答案。
- 实际读取 P-01 `docs/evals.md` 的 `One Assertion Refined`、`Test 2: A/B Blind Comparison` 及 `Test 5`：上游存在因断言过度具体而修订评估的实例，早期比较也明显重视固定结构。这里只借鉴对照设计与限制披露，不据其结果认定本插件收益。
- R-01/R-05 本地摘要将仓库导航、增量记录用于本地设计启发，不是完成状态或效率的运行证据。

上述三个项目的 checkout 与 gitlink 核查分别为 P-03 `e062b9572be933564ba3899d059377dfa1393e32`、P-06 `41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f`、P-01 `d47a61950e784fc4237ba10ddc1e9e198bd0f275`；本轮未修改或执行其中工作流。

## 任务与评估方案预审

已读 [PLAN-0004](../plans/0004-paired-maintenance-trial.md) 和两份固定任务提示。实施提示提供已批准的外部行为、共同材料和环境限制，没有提供实现答案、评分器入口或文档模板；冷读提示要求从实际产物定位并执行离线回归，不附完成答案。内容维度不按特定目录、文件名或文档数量计分，没有发现此部分的阻断项。

两组共同保留原有治理，同时禁用子 Agent 委派并说明这一限制；实验外独立 reviewer 不等于插件内自动 review 已成功。控制组可能读取仓库 Skill 源码，必须依据轨迹记录，不能把“未安装”自动当作“完全未受 Skill 内容影响”。这些条件限制效果结论的适用范围。

首次验收器 SHA-256：`4ef56e636f7bd3ca3fd8f86a596a0dc9edd7d60b861ef20170c28eec4cd2a44b`。共同任务与 runner 的最终摘要值以运行前冻结清单为准。

## Runner 的运行前审查

已直接读取 [对照 runner](../../tests/experiments/run-maintenance-comparison.py)，首次预审后修订版本 SHA-256 为 `50f026e6e5f46521e68c329f95c22207485598b5c92e4b0c89c0893eb17bfd6d`。

| 核查项 | 结论 |
| --- | --- |
| 执行者输入 | 从 Git clone 后固定 checkout 到共同基线，只另加 R-22、相同未提交 README 注释及 A 的启用行；新增方案、验收器和评分答案不在基线中 |
| 研究材料 | 逐个核对 checkout 与基线 gitlink，按固定 SHA archive，并以只读目录挂入两组；不以当前工作区散文件替代上游版本 |
| before/after 及评分泄漏 | 会话挂载的 `/evidence` 仅为其子目录，含本会话输入快照、prompt 和运行记录；父级的 controller mapping、冻结清单、方案、独立 grader 未挂载。before 快照来自工作区，未夹带本轮评分文件。证据目录可被模型访问是已知环境边界，并非 OS 级信息流沙箱 |
| 条件一致性 | 实际顺序 A/B/B/A；同镜像 digest、模型、CPU/内存、超时、共同任务和研究材料；禁用 memories/multi_agent。A 增加安装及启用，B 不安装；控制组读取源 Skill 的可能性保留分析 |
| 冷读隔离 | 新容器及 tmpfs HOME，不带旧聊天，统一 B 安装条件并禁用 plugins；既有源码和产物保留。读者仍可从内容推断组别，因此不能承诺完全盲法 |
| 启用行移除 | 发现最初只移除文件首行，正文内移动会残留；主 Agent 改为按完整行定位并移除唯一匹配。多条匹配明确 preparation_failed；缺失或改写记录为产物限制，不能声称正常移除。后续需按实际记录判断各读者有效性 |
| 失败和证据 | stdout/stderr 流式落盘；超时记录并停止本轮具名容器；保存前后文件、差异、usage 和退出结果。没有按成功过滤样本；基础设施故障仍须人工分类，不凭 exit 0 判定内容通过 |
| 清理 | 内层 finally 仅删除本会话具名容器，外层仅按本轮随机 label 删除；临时工作区上下文清理，保留并比较原容器集合与固定镜像存在。实际结果要等 cleanup 原始记录，不由代码推断清理已完成 |

主 Agent 报告已做无认证镜像预检，CLI 0.149.1 / Python 3.11.2，所用 disable flags 支持；本 reviewer 未另行访问 Docker socket。输入快照 UTF-8 可读及全部 12 个 gitlink 一致由主 Agent 预检，reviewer 另行核查了本轮直接引用的三个子模块。

修订回查后没有剩余运行前阻断项，可以按冻结条件执行。该结论仅批准实验设计与已审代码，不表示模型行为、最终修复或清理结果通过。

## 运行前阶段保留的后续审查范围

运行前尚未核对匿名产物、引用、完整轨迹、冷读结果和真实清理记录，当时没有整体 Passed 结论；这些检查现已在下文各节完成，历史预审结论不替代实际证据。

## 实验启动后的补充资料审查：planning-with-files

按用户追加要求，独立回查 [插件定向比较](../reference/planning-with-files-plugin.md)、索引和引用台账。直接读取固定 P-01 的 manifest、`.agents/skills/planning-with-files/SKILL.md`、`hooks/codex-hooks.json`、`tests/test_codex_plugin_operations.py` 及 LICENSE。checkout 与 Git index gitlink 同为 `d47a61950e784fc4237ba10ddc1e9e198bd0f275`；manifest 为 3.16.1，MIT 署名 Ahmad Adi 与摘要一致。

- 实际 Codex 插件入口确为 `./.agents/skills/`，只有一个 Skill 目录；hooks 指向 `./hooks/codex-hooks.json`，不是独立安装目录。摘要没有误用 `.codex/skills/` 作为该 manifest 的入口。
- `FIRST: Restore Project State`、`Quick Start`、`File Purposes` 实际包含按任务恢复、只补缺失文件、单一共享计划维护者及显式历史读取边界；本地取舍与内容相符。
- 两个具名操作测试确实检查 Skill 根、Codex 描述及 `${PLUGIN_ROOT}` 路径。这里只读其断言，不能据此宣布真实缓存加载、Windows 命令或上游测试通过。摘要保持源码观察与本地验证方案的区别。
- 该 Skill 正文仍含 Claude 环境变量及命令示例；hook descriptor 的 Codex 专用路由不能证明正文的所有示例均可原样在 Codex 使用。本摘要仅作概念和源码比较，未提供照抄执行指令，因此此项为研究限制，不构成当前材料的阻断。
- 索引继续归入既有 P-01，未新建重复 submodule，也没有把 hooks、固定三文件或恢复机制记成本仓库已采纳能力。新增摘要不在冻结基线或允许额外输入列表中，runner 也不读取它，未改变已经启动的试用条件。

本项来源存在且比较依据成立，无剩余阻断项。审查时摘要 SHA-256：`7f6f8698a6ed98ebbc2ca08ee1e1c925a958431fbd8d4b3324a76c89bb77ffce`。上游安装、执行及效果复核均 Not Run。

## 隐藏组别的产物评审：揭盲前固定判断

仅读取主 Agent 提供的四个随机 ID 产物目录，按 ID 字母顺序比较；本节固定判断时未读取 controller mapping、运行顺序、environment 或实施轨迹。输入包含去除实验启用行后的实际文件、修改前后差异、独立验收结果、冷读回答和冷读工具事件。内容中可能显露工作方式，不据此猜测组别或声称完全盲法。

| 匿名样本 | 实现与可维护性 | 文档、历史和负担 | 冷读复核 |
| --- | --- | --- | --- |
| `08a618d4` | 独立契约 13/13；采用 argparse choices、自定义正整数转换与重复检查，未触碰内部 handoff 条件。四项单测有必要负例和合法解析，代码/测试结构最简洁，推荐作为整合基础 | 在既有计划追加维护、保留旧结果，在既有使用记录链接新复现；没有修改规则或插件。新增 REP-0004 未逐文件登记到引用台账，最终整合需补齐；记录日期问题见下文 | 实际找到并执行 unittest/py_compile，工具输出为 4 项 OK；准确说明独立审查与真实运行 Not Run，无源码/文档变化 |
| `4ce1f058` | 独立契约 13/13；手工分别判断 handoff、未知、重复、超时，错误清楚但比 choices 方案更多自定义分支。七项单测正常 | 新 plan/reproduction 内容充分且登记引用；新计划没有接入既有“当前计划”入口，但通过实际文件检索仍可发现，不把导航偏好判为失败。没有观察到历史或批准需求改写 | 实际找到并执行 7 项 unittest、py_compile 及 diff 检查，OK；准确识别审查限制并保留既有修改 |
| `50aa8b68` | 独立契约 13/13；与第一份同类实现，多出可选集合常量；六项单测满足主要边界 | 更新 AGENTS/README/development 的导航并新增 plan/reproduction，各处用途明确，不能只因文件更多判无用；README 保留人工注释。REP-0004 将内存 compile 命令称作 py_compile，是实际术语错误，冷读者也发现 | reader 说执行 6 项通过且未修改文件；所给 command event 的复合验证命令 exit 0，但 aggregated_output 为空，当前无法从该事件独立核实具体测试输出，留待原始轨迹核对 |
| `edaf048d` | 独立契约 13/13；为测试抽出 should_run_handoff，并直接测试布尔条件；该改动不是修复入口所必需，现有独立行为验收已覆盖，整合不采用这次抽取 | 在既有 plan/reproduction 追加记录，单独七行 review 明确 Not Run，没有伪造独立通过。review 待办可直接保存在计划，不必为最终交付照搬占位文件；历史和插件均保留 | 实际运行 6 项 unittest、py_compile 和 diff，工具输出 OK；准确报告未运行项及 git diff --check 不覆盖未跟踪文件的限制 |

四份均保留共同 README 人工未提交注释，reader-changes 均为空，未观察到插件能力、批准需求或历史运行结果被改写。四份新增维护记录均写 2026-09-07，而当前实验预注册日期为 2026-09-08；初审因此提出日期风险。主 Agent 随后仅提供时间核对：八会话均发生 UTC 09-07 晚间，末读者输出 mtime 为 `2026-09-07T23:16:28Z`，用户时区 Asia/Shanghai 已为 09-08，容器未配置 TZ。故撤回“日期错误”的可能判断，记录为共有的未注明时区歧义；不将其归因于某组，最终报告统一用户时区并保留原文。

推荐从 `08a618d4` 选取入口实现和紧凑单测，在主工作区复核后整合；保留独立 13 项行为验收作为包括 help/default/handoff 调度在内的另一层证据。最终台账与交接整合到本轮既有 PLAN/REP-0004，不照抄四份产物的重复文件、未注明时区日期或不同编号。本节没有合成总分，也没有作插件效果结论。

主 Agent 回查 `50aa8b68` 的原始 reader item_4，确认 exit 0 与空 aggregated_output 与提供的审查切片一致。仍可确认读者发出了验证命令且报告通过，但无法核实当时测试数量与具体输出；后续主 Agent 或 reviewer 复跑只能证明当前产物，不补造当时冷读证据。

主 Agent 披露首次独立验收只恢复三个文件，导致合法执行缺少插件分发目录；恢复完整快照后四份均为 13/13，没有重跑模型。此事件属于评分夹具错误，必须保留首次输出和修正来源，不能记为样本代码失败或偷偷删除失败记录。

## 揭盲后的轨迹、归档与清理核查

上述内容判断保存后才读取 mapping、environment、完整实施轨迹及 cleanup。顺序为 `edaf048d` A、`08a618d4` B、`4ce1f058` B、`50aa8b68` A。推荐的代码来源因此属于 B；没有据组别改变先前选择，也不能从一次选择推出 B 普遍更好。

### 实际加载与控制组内容暴露

两个 A 的 implementation item_1 都明确读取 `/home/agent/.codex/plugins/cache/personal/program-design/0.1.0/skills/project-docs/SKILL.md`；输出包含与当前分发字节一致的完整正文，足以证明实际读取，而非仅模型自述。`edaf048d` 还在 item_3 读取缓存内 evidence.md。

两个 B 的安装列表为空，未观察到主动读取已安装 Skill；但**两份均实际接触了 Skill 内容**：

- `08a618d4` item_3 的广域 rg 输出直接含源码 Skill 第 28 行，并从旧 REP-0003 before/after JSON 输出完整转义的 Skill 文本。
- `4ce1f058` item_2 的广域 rg 从旧 REP-0003 stdout/before 等文件输出完整转义的 Skill 文本。

因此“未安装”不等于“未受 Skill 内容影响”。本轮没有静默排除这些样本；证据只支持已有治理、可见插件源码及旧实验材料条件下的观察，不能声称完成纯净的 Skill 有无效果比较。大范围读取还包含大量历史实验内容，两组 token 和耗时不得直接解释为插件固有成本。

### 完整性、生命周期与资源

- 实际核对四份 implementation before：不含本轮 tests/experiments、预注册计划、review 或实验启动后新增的 P-01 比较摘要。归档中的六份 frozen-inputs 字节与 environment 的摘要全部一致。
- 两个 A 记录安装 0.1.0、enabled=true，模型后 remove/unregister 成功，后置列表及本插件缓存均为空；两个 B 及四个 reader 的前后安装列表均为空。四个 reader before 与 implementation after 的唯一差异是 A 中控制器启用行的删除；B 完全一致，四个 reader 的文件 changes 均为空。
- 八会话均 exit 0，未记录 turn.failed；result 中 usage 与各原始 turn.completed 逐项一致。metadata 的模型重试 0、人工会话干预 0 与运行轨迹一致；验收准备修正 1 是实验外事件，不能被前两项的零掩盖。
- wall_seconds 是控制器围绕容器调用的时间，包含 CLI 准备及 A 安装/卸载；不是纯模型推理耗时。input_tokens 包括上下文重复处理，cached_input_tokens 是其中缓存部分；本报告不将其相加为总量或推算费用。
- cleanup 原始记录显示本轮 label 容器为空、原容器集合保留、固定镜像存在、临时工作区删除。依据是已审 runner 产生的记录；reviewer 未另行访问 Docker socket。宿主归档准备目录仍须主 Agent 最终清理，不在该 runner cleanup 范围内。
- [raw-evidence.tar.gz](../reproduction/evidence/0004/raw-evidence.tar.gz) 内 146 个文件去除共同 `paired-maintenance/` 前缀后，逐 SHA-256 与 [raw-manifest.json](../reproduction/evidence/0004/raw-manifest.json) 及归档前原始目录一致；其中保留三个 contract-fixture-failure.json。压缩包 SHA-256 为 `7a9868b774a01b239b2b6d4e15e2e4d5b3303ad3731823c99eed3af4db462689`。

本轮发现均以事实或限制保留：控制组内容暴露、一个读者缺少具体测试输出、术语错误、时区未注明、一次验收准备错误。四份入口契约均通过与三份可见冷读测试通过的结论有实际证据；没有发现需要本轮修改插件或将其升级的阻断。Windows、真实 smoke 行为复跑、插件内自动 reviewer、联网检索专项及自身迁移仍 Not Run。最终选取修复与台账处理的定向回查见下一节。

## 最终整合定向回查

主仓库入口脚本和单测与推荐 `08a618d4` 产物逐字节一致。源码仅分离参数解析、用 argparse choices 与正整数转换验证参数、拒绝重复项；仍在任何输出路径、Docker 或认证访问前完成解析，内部 handoff 调度原式保留。最终源码 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `tests/run-plugin-smoke.py` | `334d30282ae62e28ad9adf8863bc31ea2e8400cc352d62f7a6ba8d78e3ef9429` |
| `tests/test_run_plugin_smoke.py` | `3198cbd67b3045b274c4002a679854d4e8cba6b6360b007fb467f33433d24425` |

直接回读主机及固定镜像的 final-contract JSON，各为 13/13；固定镜像 final-container-unittest.txt 实际输出 4 项 OK。主 Agent 报告主机 Python 3.14.4 单测 4 项通过，镜像为 Python 3.11.2、禁网且无认证挂载；reviewer 没有另行启动容器。上述最终离线验证不替代四份原实验的冷读输出，也不重新证明真实模型 smoke 流程。

已核对 tests/README、PLAN/REP-0004、引用台账、资料索引、证据说明及根导航。引用台账对最终代码、单测、运行器、提示、验收器、新说明和研究比较均有来源或用户需求映射；生成证据统一关联冻结运行器及实际来源。REP-0004 明确记录两个 B 的实际内容污染、A2 空测试输出、验收恢复错误及时间计量边界，没有用成功退出或最终复跑补造缺失证据。

最后发现并处理两处文档问题：development 仍称 PLAN-0003 为当前计划，现已与根入口同步至 PLAN-0004；测试说明的台账原写“两组冷读观察”，现已明确观察仅用于整理，最终新说明没有另做冷读。修订回查通过，没有因为纯导航和措辞变化扩大模型测试。

静态检查记录包含 56 个 Markdown、284 个本地链接、23 项文章来源和 12 个固定子模块，缺失列表为空；这是主 Agent 的静态执行结果，reviewer 没有另写全仓检查器。reviewer 实际运行 git diff --check，并核对插件与 marketplace 相对基线 diff 为空。根 AGENTS 仅导航更新，没有加入正式启用声明。

最终文件审查无剩余阻断项。下一轮建议修正实验暴露条件后重新预注册，属于评估方法改进，不作为本轮已验证的插件功能。主 Agent 可在保存归档后清理匿名审查副本及原始宿主临时目录，并补记真实清理结果；该后续清理不需要重审已固定的代码或模型产物。

## R-01 / R-05 官方原文补充核查

2026-09-08 独立直接打开两篇官方全文，补齐首次仅读本地摘要的范围：

- [R-01 原文](https://openai.com/index/harness-engineering/) 的 `We made repository knowledge the system of record` 明确将短 AGENTS 作为文档目录入口，逐步定位深入资料，并描述检查过期文档与链接的工具；`Entropy and garbage collection` 讨论持续发现和修正漂移。两处支持阅读比较中的短入口、资料发现和过期检查。文档过期的最直接依据在前一节末尾，不将后一节概括为专门的文档算法。
- [R-05 原文](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 的 `Incremental progress` 要求每次处理有限功能、保存进度和可恢复的 Git 状态；`Getting up to speed` 要求新会话读取进度与历史并验证环境。支持本轮记录可接续状态及独立核查实际结果的方向，但四次冷读、统一无插件等具体实验安排仍来自用户要求及 P-06。

两篇均为特定团队或任务环境的实践，未证明 program-design 的效果，也未规定本项目必须引入对应引擎、固定文件格式或常驻自动化。原文可访问，相关引用支持范围成立，无新增发现；其余已审范围未重复执行。

## 主 Agent 收尾处理

最终文件审查通过后，主 Agent 再次按归档 manifest 核对 146 个临时原文件，删除匿名评审副本、原始临时输出及本轮验证临时文件。按两个本轮标签只读查询无遗留容器，镜像仍保留；实际记录见 [final-cleanup.json](../reproduction/evidence/0004/final-cleanup.json)。此项为主 Agent 的运行结果，未冒称 reviewer 另行访问过 Docker。
