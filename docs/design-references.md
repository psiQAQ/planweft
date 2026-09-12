# 设计引用台账

本台账以第一方文档或代码文件为单位记录实际设计。资料目录中的 R 编号与项目 P 编号以 [统一索引](reference/README.md) 为准；其中保存原网址、作者、日期、许可及子模块完整 SHA。原文定位下列到章节，源码定位到固定 checkout 的文件；不能只因来源存在就认为设计已验证。

## 当前文件映射

| 本仓库目标文件 | 问题与设计点 | 实际来源及定位 | 借鉴、差异与需求 | 验证 / 审查入口 |
| --- | --- | --- | --- | --- |
| [AGENTS.md](../AGENTS.md) | 常驻指令过长；采用通用原则与短导航 | R-01 `We made repository knowledge the system of record`；R-10 `Instruction following`、`Testing and verification`；R-11 `How Codex discovers guidance` | 借鉴短入口及明确边界；本仓 review 要求来自 REQ-06，不归因于 GPT-6 强制要求 | ADR-0002；V-04；REV-0001 |
| [README.md](../README.md) | 新读者不知目标、现状与入口 | R-08 `The four kinds of documentation`；R-01 仓库知识章节 | 给任务导向导航和明确能力状态；内容来自 SPEC-0001，不声称已经交付工具 | V-01、V-02；REV-0001 |
| [个人 override](../profiles/personal/AGENTS.override.md) | 个人默认偏好影响普通使用者 | R-11 全局与项目文件选择；P-11 README `Context Files` | 根据官方替代语义使用差异稿+手工组合；中文、表达和 Python 偏好来自用户提供的原始全局指令及 REQ-08 | ADR-0002；V-04；真实加载 Not Run |
| [产品规格](specs/0001-document-management.md) | 建议被误写为必需或已实现功能 | P-03 `docs/concepts.md` 的 Specs、Design、Tasks；R-08 分类；用户 REQ-01～10 | 区分目标、实现候选和验收；TypeScript/Node.js 与双平台来自用户选择，非外部技术优越性结论 | ADR-0001；REV-0001 |
| [开发约定](development.md) | 设计缺少依据和阶段交接 | R-04 `Living plans and design decisions`；P-12 模板 `Confirmation`；P-06 `Stage 3: Reader Testing` | 自包含进展、决定与独立检查；证据 review 角色来自 REQ-06。读者检查不等于依据审查；Windows 条件约定来自用户既有要求 | V-01～04；REV-0001 |
| [基础阶段计划](plans/0001-reference-foundation.md) | 后续会话无法识别剩余事项 | R-04 `Progress`、`Decision Log`、`Outcomes & Retrospective`；P-01 README 规划文件分工 | 保存进度、变化和验证；不用历史模板全部强制格式，不读取完整聊天作为接续前提 | V-01；REV-0001 |
| [ADR-0001](adr/0001-use-existing-document-conventions.md) | 尚无问题证据即引入框架 | R-01 短入口；P-03 `docs/concepts.md` 的 Artifacts；P-12 最小模板 | 比较普通 Markdown、直接工具化与完整框架；选择轻量起点属于本地取舍 | REQ-01、07；REV-0001 |
| [ADR-0002](adr/0002-separate-personal-instructions.md) | 同目录 override 替换 base | R-11 全局/项目选择；P-11 README `Context Files` | 拆分位置并手工组合，避免错误叠加假设；不新增生成器 | REQ-08；V-04；REV-0001 |
| [ADR-0003](adr/0003-adopt-own-system-after-validation.md) | 新工具尚不可靠就成为自身前提 | R-04 自包含与恢复；P-06 `Stage 3`；P-03 `Archive` | 借鉴可恢复交接与归档；具体切换门槛来自 REQ-10，本地选择不伪称行业标准 | 当前迁移 Not Run；后续新迁移 ADR |
| [验证记录](reproduction/0001-reference-foundation.md) | 缺少可重现的检查证据 | R-18 `Filling in information`；R-04 `Validation and Acceptance` | 给环境、步骤、预期和实际结果。文档静态检查不等于产品测试 | V-01～04；REV-0001 |
| [review 报告](reviews/0001-evidence-review.md) | 链接存在却不支持主张 | 用户 REQ-06；P-12 `Confirmation`；P-06 独立读者方法仅作独立性启发 | 专职 reviewer 核对原文，主 Agent 处理发现；内容结论来自实际 review 过程，不把读者 Skill 说成现成引用审计器 | 报告内的审查范围、状态和发现 |
| [引用台账](design-references.md) | 设计无法追到来源和验证 | 用户 REQ-04；P-12 模板 `More Information`、`Confirmation` | 逐文件映射是本项目用户明确要求；引用粒度和状态为本地约定 | REV-0001；不对台账产生无限自审 |
| [创新记录](innovations.md) | 未查先例的想法被当成原创或必需 | 用户 REQ-05；P-12 `Considered Options`、`Pros and Cons of the Options` | 先检索、写差异和退出条件；未检出不证明不存在；当前无创新实施 | 所列检索过程；REV-0001 |
| [.gitmodules](../.gitmodules) | 参考实现随上游变化不可复核 | 用户 REQ-03；Git gitlink 的实际固定版本行为 | 12 个项目的固定 checkout；索引 SHA 与 gitlink 同步，不装运行依赖 | V-03；REV-0001 |
| [.gitignore](../.gitignore) | 保留已有本地书籍排除规则 | 用户已有文件；不是本阶段新工具设计 | 原内容 `/docs/books/` 保留，书籍不纳入本阶段来源或提交 | V-03 收录范围 |

## 交接与维护阶段的新增 / 实质修改

用户在 2026-09-07 追加授权独立交接、真实维护、最小功能取舍及本轮容器清理。原文件的设计来源继续沿用上表；下表补充本轮变化。R-20 记录实际使用的官方指南，未新增运行依赖或创新机制。

| 本仓库目标文件 | 实际问题及设计 | 来源、借鉴与本地差异 | 验证 / 审查 |
| --- | --- | --- | --- |
| [README.md](../README.md) | 读者观察到首页阶段表述与已完成计划有张力，更新当前状态和接续入口 | REP-0002 读者 A 的实际观察；R-01 短入口方法；本地阶段选择 | 回测当前阶段；REV-0002 |
| [AGENTS.md](../AGENTS.md) | 当前计划导航转到后继任务 | 用户追加任务；沿用原通用规则，不加入个人偏好 | 链接检查；REV-0002 |
| [开发约定](development.md) | 当前计划入口同步 | 用户追加任务与 R-04 接续状态；纯导航更新 | 链接检查 |
| [产品规格](specs/0001-document-management.md) | 明确本轮已授权行为验证，候选产品不自动定稿 | 用户追加需求；沿用 REQ-01/06/09 的边界 | REV-0002 |
| [PLAN-0001](plans/0001-reference-foundation.md) | 历史完成记录关联后继任务 | R-04 Progress；保留旧验收，只追加后继链接 | 当前状态回测 |
| [PLAN-0002](plans/0002-handoff-maintenance-baseline.md) | 无历史读者测试、真实维护与容器清理 | P-06 Stage 3、R-04、R-18、R-20；八题、快照和清理范围为本地实验安排 | REP-0002；REV-0002 |
| [ADR-0001](adr/0001-use-existing-document-conventions.md) | 初始依据审查与后续冷读验证容易混淆 | REP-0002 读者观察；明确原有方法的真实验证范围 | 受影响问题回测 |
| [ADR-0004](adr/0004-defer-product-cli-after-baseline.md) | 单轮实验不足以证明专用 CLI 收益 | REP-0002 结果；R-01 仅概念启发，P-12 备选与理由；暂缓为本地取舍 | REV-0002；产品实现 Not Run |
| [REP-0001](reproduction/0001-reference-foundation.md) | 历史数量断言用于新资料集时失败 | 本次实际 AssertionError；只补适用快照说明，保留旧代码与结果 | REP-0002 |
| [REP-0002](reproduction/0002-handoff-maintenance-baseline.md) | 需要可检查的输入、预期、实际答案与环境失败记录 | P-06 Stage 3、R-18、R-20；本地题目和人工判定，不作跨模型排名 | REV-0002 |
| [容器题目](reproduction/evidence/0002-container-prompt.txt) | 保留实际实验输入 | REP-0002 八项判定与用户授权；不是新的 Agent 全局指令 | 与实际 stdin 文件一致 |
| [容器回答](reproduction/evidence/0002-codex-answer.txt) | 保存可复核的结果 | B3 实际 JSONL 最后 `agent_message` 提取；生成来源为该次运行 | 主 Agent 逐项判定；不把模型回答当外部事实来源 |
| [REV-0002](reviews/0002-handoff-maintenance-review.md) | 新实验与新来源需独立依据核查 | 用户 REQ-06；原文、差异及实验记录，分清实际行为与候选 | 报告内审查范围 |
| [资料索引](reference/README.md) | 补入实际运行指南 R-20 | 用户 REQ-02、R-20 原文；沿用元数据结构 | REV-0002 |
| [Codex 非交互摘要](reference/codex-non-interactive.md) | 临时执行参数与边界需有准确依据 | R-20 `Basic usage`、`Permissions and safety`、`Make output machine-readable`；用本机 help 确认参数 | REP-0002 实测与 REV-0002 |

## 第三方资料、译文与辅助文件（来源映射）

`docs/reference/README.md` 的目录、R/P 编号和元数据字段来自 REQ-02/03；它的内容依据每行原文与固定项目。R-00 至 R-21 对应的中文文件逐项在该索引登记，构成这些文件的来源映射，避免在此复制同一张目录。全文译文的许可文件对应 OpenAI Cookbook、Diátaxis、Pi、MADR、GitHub Docs、Agent Skills 文档的上游许可，不作为本仓库新设计。

`.submodule/` 下第三方文件以 12 个 gitlink 和上游许可追溯，不纳入第一方逐文件设计覆盖。未来若增加生成文件，关联生成源及其设计记录；新的第一方工具源码仍需在本台账逐文件登记。纯导航、命名和普通胶水关联已有需求/设计即可，不为它们编造论文依据。

## 阅读与状态

源文件定位以固定项目索引为准：[P-03 concepts](../.submodule/Fission-AI/OpenSpec/docs/concepts.md)、[P-06 doc-coauthoring](../.submodule/anthropics/skills/skills/doc-coauthoring/SKILL.md)、[P-12 完整模板](../.submodule/adr/madr/template/adr-template.md)、[P-12 最小模板](../.submodule/adr/madr/template/adr-template-minimal.md)。

来源可访问、内容支持该借鉴和本仓库效果验证是三种不同状态。基础文档依据见 [REV-0001](reviews/0001-evidence-review.md)；首版 Skill 的历史状态以 REP-0003/REV-0003 为准，该阶段未实施专用 CLI、hooks 与自身接管。后继版本以其规格和复现记录为准；未通过 review 的新条目不能标为已验证设计。

## 首版插件阶段（2026-09-07）

下表逐文件登记；上文基础阶段记录保持历史范围，当前结果以 [REP-0003](reproduction/0003-project-docs-plugin.md) 和 [REV-0003](reviews/0003-project-docs-plugin-review.md) 为准。无新增未覆盖机制，创新记录无需制造条目。

| 文件 | 问题与设计 | 精确来源与本地差异 | 验证/审查 |
| --- | --- | --- | --- |
| [plugin.json](../plugins/program-design/.codex-plugin/plugin.json) | 插件身份与单 Skill 分发 | R-21 Create a plugin manually；P-04 .codex-plugin/plugin.json；本版无 hooks/MCP，项目身份为本地 metadata | PD-01；官方 validator、安装实测；REV-0003 |
| [marketplace.json](../.agents/plugins/marketplace.json) | repo 安装入口 | R-21 Marketplace metadata / How local marketplaces work；官方生成器默认 personal、相对 source.path；不等于项目启用 | PD-01；安装/卸载；REV-0003 |
| [SKILL.md](../plugins/program-design/skills/project-docs/SKILL.md) | 相关读取、授权内维护、交接、启用边界 | R-12 How ChatGPT and Codex use skills / Best practices；P-03 Keep It Lightweight；P-04 writing-plans File Structure / Execution Handoff；R-04 Living plans；单 Skill 与 opt-in 为用户需求 | PD-02～07；正负样例及冷读；REV-0003 |
| [openai.yaml](../plugins/program-design/skills/project-docs/agents/openai.yaml) | 显示与调用提示，保留默认隐式匹配 | R-12 Optional metadata；用户选择按任务使用，不设 false | PD-02；发现与触发轨迹；REV-0003 |
| [evidence.md](../plugins/program-design/skills/project-docs/references/evidence.md) | 按需记录设计依据与创新、独立核查 | 用户 REQ-04/05/06；P-12 template/adr-template.md More Information / Confirmation；P-06 Stage 3 仅独立读者启发；审计方法为本地需求 | PD-05；语义 review；REV-0003 |
| [README.md](../plugins/program-design/README.md) | 用户安装、启用与卸载说明 | R-21 Add a marketplace from the CLI / How local marketplaces work；R-11 override 规则；命令以当前 CLI help 与实际运行复核 | PD-01/02；生命周期测试；REV-0003 |
| [0002-project-docs-plugin.md](specs/0002-project-docs-plugin.md) | 首版行为和验收边界 | 用户本轮计划和选择为需求来源；R-12/R-21 支持封装能力，不保证模型遵循 | PD-01～07；REP-0003；REV-0003 |
| [0005-skill-first-plugin.md](adr/0005-skill-first-plugin.md) | 重开旧写入取舍，选择指令型插件 | 用户新需求；R-12 Best practices、R-21 Create a plugin manually；P-03/P-04 实际先例；本地取舍不证明收益 | REV-0003；REV-0003 |
| [0003-project-docs-plugin.md](plans/0003-project-docs-plugin.md) | 实施步骤与接续状态 | R-04 Progress / Living plans；用户本轮实施范围 | REP-0003；REV-0003；REV-0003 |
| [0003-project-docs-plugin.md](reproduction/0003-project-docs-plugin.md) | 真实输入、结果、环境故障与限制分开 | R-18 Filling in information；R-20 非交互运行；SPEC-0002 为验收来源 | 实际输出和文件差异；REV-0003 |
| [0003-project-docs-plugin-review.md](reviews/0003-project-docs-plugin-review.md) | 独立来源核对和发现处理 | 用户 REQ-06；reviewer 实际检查和内容 SHA，不对报告无限递归自审 | 报告内状态；REV-0003 |
| [run-plugin-smoke.py](../tests/run-plugin-smoke.py) | 可重跑、隔离输入、安装卸载与文件快照 | PD-01～07；REP-0002 实测容器命令、R-20 机器可读输出；P-06 Stage 3 新读者；Python 标准库为本地实验胶水，无产品引擎 | REP-0003；退出码仅执行成功，语义人工判定；REV-0003 |
| [README.md](reference/README.md) | 增加本轮来源 | REQ-02；R-21 实际原文与访问日期 | REV-0003；REV-0003 |
| [codex-plugins.md](reference/codex-plugins.md) | 中文最小插件与分发摘要 | R-21 各段原文定位在摘要；未推定全文授权 | REV-0003；REV-0003 |
| [codex-skills.md](reference/codex-skills.md) | 补默认 invocation 与优先指令说明 | R-12 Optional metadata / Best practices；保留时效及自动匹配限制 | REV-0003；REV-0003 |
| [README.md](../README.md) | 当前能力、安装入口与验证状态 | 本轮用户需求、SPEC-0002 和真实 REP-0003；沿用 R-01 短入口 | 当前状态复核；REV-0003 |
| [AGENTS.md](../AGENTS.md) | 当前计划导航 | 本轮用户需求；沿用通用规则，不在本仓正式启用插件 | 链接检查；REV-0003 |
| [development.md](development.md) | 当前计划导航 | 本轮用户需求；R-04 接续入口 | 链接检查；REV-0003 |
| [0001-document-management.md](specs/0001-document-management.md) | 基础历史与后继实现范围 | 本轮用户明确授权；SPEC-0002 / ADR-0005 | 语义 review；REV-0003 |
| [0002-handoff-maintenance-baseline.md](plans/0002-handoff-maintenance-baseline.md) | 保留旧结果并关联后继 | 本轮用户需求；R-04 Progress | 链接检查；REV-0003 |
| [0004-defer-product-cli-after-baseline.md](adr/0004-defer-product-cli-after-baseline.md) | 旧决定保留并注明新需求重开 | 本轮用户授权；ADR-0005 明确替代范围，不改历史观察 | REV-0003；REV-0003 |

本轮 evidence 下的生成记录统一关联 tests/run-plugin-smoke.py、REP-0003 的实际调用和判定；输入、输出及快照不是外部权威资料，不逐份虚构引用。

## 定向阅读与配对试用（本轮工作区）

需求来源：用户确认的“定向阅读与真实维护任务对照试用”计划；插件冻结 0.1.0。以下文件的验证状态以 REP-0004、REV-0004 为准，实验准备不代表模型试用已经通过。

| 本仓库目标文件 | 问题、实际来源及定位 | 借鉴与本地差异 | 验证 / 审查 |
| --- | --- | --- | --- |
| [试用计划](plans/0004-paired-maintenance-trial.md) | P-01 `docs/evals.md` 的 Test 5 / Reproducing；用户配对条件 | 冻结输入、按内容验收，限制两对样本结论；不沿用上游分数或目录评分 | REV-0004 预审、REP-0004 |
| [阅读比较](reproduction/0004-reading-comparison.md) | R-01 仓库知识；P-03 Progressive Rigor；R-05 Incremental progress；P-06 Stage 3；P-01 评分限制；R-22 | 逐问题说明借鉴和验证，不把概念启发当本地效果 | REV-0004 原文核查 |
| [试用结果](reproduction/0004-paired-maintenance-trial.md) | 用户保留完整轨迹要求；R-18 预期/实际；P-01 实验限制 | 分开记录代码、文档、冷读、时间和用量，不合成总分 | 实际运行证据；REV-0004 |
| [审查报告](reviews/0004-comparison-review.md) | 用户专职 reviewer 要求；P-06 独立读者仅作启发 | 外部依据审查与模型冷读分开；不冒充插件自动委派 | 报告范围与处理结果 |
| [配对运行器](../tests/experiments/run-maintenance-comparison.py) | 用户 ABBA、隔离、八会话与清理要求；既有 `tests/run-plugin-smoke.py` 的 CLI 插件生命周期 | 一次实验脚本，固定基线/提示/资源、容器 tmpfs 认证、禁用多 Agent；非产品运行时 | 预审、manifest、真实轨迹与 cleanup.json |
| [实施提示](../tests/experiments/maintenance-task.txt) | 用户入口行为需求与环境边界 | 仅给任务和共同材料，不给评分器或实现答案；保留原治理 | 运行前冻结；REV-0004 |
| [冷读提示](../tests/experiments/cold-read-task.txt) | P-06 Stage 3 Reader Testing；用户冷读需求 | 不带旧聊天，要求定位和执行已有验证；统一无插件 | 四次 reader 轨迹；REV-0004 |
| [独立入口验收器](../tests/experiments/check-entry-contract.py) | 用户非法输入/副作用/handoff 合同；R-22 Exiting methods | 标准库替身走 argv/main 边界；不依赖修复采用特定函数，源码审查补充替身边界 | 基线、临时正确补丁与 handoff 变异自检；REV-0004 |

新增 R-22 中文摘要按上游 argparse 文档登记在参考索引；该文件及索引为来源材料/导航，不产生新的产品机制。实验生成的 JSON、日志与差异统一关联配对运行器及冻结输入，不逐份重复外部引用。

用户在本轮实验启动后补充要求研究 planning-with-files 插件；[插件比较摘要](reference/planning-with-files-plugin.md) 关联 P-01 固定 manifest、实际 Skill、hooks 描述与操作测试。这里只增加来源与取舍分析，不作为已采用 hooks/恢复引擎的设计依据；冻结实验输入不变。独立核查见 REV-0004。

### 入口修复的最终整合

| 本仓库目标文件 | 实际设计及问题 | 精确依据与本地差异 | 验证 / 审查 |
| --- | --- | --- | --- |
| [run-plugin-smoke.py](../tests/run-plugin-smoke.py) | 解析阶段拒绝未知/重复场景和非正超时，副作用延后；保留 handoff 调度 | R-22 `choices`、`type`、`Exiting methods`；用户 PLAN-0004 合同；选取匿名样本 08a618d4 的标准库实现，未采用额外 handoff 抽取 | 主机/容器离线测试；独立 13/13；REV-0004 |
| [test_run_plugin_smoke.py](../tests/test_run_plugin_smoke.py) | 原脚本没有参数边界回归 | 用户标准库 mock、无真实 Docker/认证要求；选取 08a618d4 产物，验证错误退出与未调用副作用，不宣称其自身覆盖完整调度 | 4 项 unittest；独立 grader 补 help/default/handoff；REV-0004 |
| [测试说明](../tests/README.md) | 新会话需发现离线验证和真实运行边界 | 用户使用说明及交接要求；R-22 错误语义；R-08 操作指南分类；参数以实际源码为准 | 冷读发现用于整理；最终命令实跑与链接检查；该说明未另做冷读；REV-0004 |
| [证据说明](reproduction/evidence/0004/README.md) | 完整轨迹体积大但须可恢复，不能只保存成功结论 | 用户保留全量输入/轨迹/失败与清理要求；P-01 `Reproducing` 的材料限制作为反面核对；tar/gzip 只用于保存生成证据，不是产品数据格式 | 146 个原始文件逐 SHA 回查；REV-0004 |

README、AGENTS 和 development 本轮仅补当前计划/测试/结果导航，沿用原入口依据并关联用户当前任务；PLAN-0004、REP-0004 和 REV-0004 保留真实结果与明确限制。参考索引补 R-22 和既有 P-01 的插件入口。没有新增产品机制或创新声明。

## PWF 底座移植阶段（2026-09-08）

需求来源是用户明确批准的 Program Design 0.2.0 实施计划。P-01 的研究 gitlink 继续固定 3.16.1；本轮移植另用下列 PWF-317 来源，不能把两个快照混为同一版本。上文“无 hooks”“单 Skill”“项目显式启用”等均保留为 0.1.0 及对应实验的历史范围，由 SPEC-0003/ADR-0006 明确替代。高 star 仅是用户选择背景，不是本地正确性或效果证据。

| 本轮来源 | 精确定位与实际支持范围 | 许可/时效 |
| --- | --- | --- |
| PWF-317：PWF v3.17.0 | [固定提交](https://github.com/OthmanAdi/planning-with-files/tree/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7)；`skills/planning-with-files/SKILL.md` 的 Restore Project State、Quick Start、File Purposes，`docs/workflow.md` 的 After Completion；支持当前工作记录、计划选择、owner 与长期知识另存 | MIT；`Copyright (c) 2026 Ahmad Adi`；源码阅读 2026-09-08；来源导入核验与实测另记 REP-0005 |
| PWF-317 运行时与宿主 | 同一固定提交的 `scripts/resolve-plan-dir.sh`、`check-complete.sh`、`plan-doctor.sh`，`.codex-plugin/plugin.json`、`hooks/codex-hooks.json`，`.pi/skills/planning-with-files/extensions/planning-with-files/`、`.opencode/packages/opencode-planning-with-files/` 及配套测试 | 上游具体实现为移植依据；源码存在不等于测试或宿主运行通过 |
| HOOKS-20260908：Codex 官方 hooks | [Hooks](https://learn.chatgpt.com/docs/hooks)：Runtime behavior、Where Codex looks for hooks、Review and trust hooks、Plugin-bundled hooks；支持插件 manifest `hooks`、包内路径、多个来源共同执行及独立 trust | OpenAI 官方说明，在线读取 2026-09-08；仅作有出处的摘要与协议依据，不推定全文转载许可 |
| SKILLS-20260908：Codex调用策略 | [构建技能](https://learn.chatgpt.com/zh-Hans/docs/build-skills) 的可选元数据：`agents/openai.yaml` 中 `policy.allow_implicit_invocation: false` 禁止隐式调用，保留显式调用 | OpenAI官方说明，在线读取2026-09-08；不能以Claude frontmatter或skills/list的enabled替代此策略 |

| 本仓库目标文件 | 问题与本地设计 | 精确依据和差异 | 验证/审查 |
| --- | --- | --- | --- |
| [SPEC-0003](specs/0003-pwf-based-plugin.md) | 独立衍生插件的版本、接口、维护边界与分层验收 | 用户批准计划；PWF-317 Skill/运行时为移植来源；本地文档治理继承 PD-03～07；自动匹配替代 PD-02 来自本轮需求 | PDB-01～10；REP-0005；实现与交付独立审查按REV范围登记 |
| [ADR-0006](adr/0006-pwf-derived-runtime.md) | 固定上游、扩展及生成分发；保留原生语言，明确替代历史 | 用户批准计划、PWF-317 具体实现；上游 `docs/workflow.md` After Completion 支持长期知识另存；HOOKS-20260908 支持 trust/重复来源边界；确定性构建为本地维护选择 | REP-0005；实现与交付独立审查按REV范围登记 |
| [PLAN-0005](plans/0005-pwf-based-plugin.md) | 当前实施进度和唯一接续位置，避免本仓提前自身接管 | 用户本轮边界；R-04 Progress；ADR-0003 的既有迁移约束 | 实际进度与 REP-0005；本计划不等于产品三文件启用 |
| [REP-0005](reproduction/0005-pwf-based-plugin.md) | 原始/移植回归、协议/宿主、只读项目/私有缓存和 OS 分层，避免证据混用 | 用户批准的四层验证；PWF-317 配套测试为回归入口；R-18 预期与实际、P-06 Stage 3 为新读者方法 | 各项由实际执行填 Passed/Failed/Not Run；预设表格不算运行 |

本轮生成运行时逐文件追溯到导入清单与身份映射/补丁；它们的批量来源是 PWF-317 的固定文件，不逐份虚构第一方原创依据。本地扩展与构建脚本应另列其实际入口和设计来源。REP-0005 中的测试输出是本轮观察证据，不是外部权威来源；历史 REP-0003/0004 不作为 0.2.0 兼容通过的依据。

## 0.4.0 能力分级发布（2026-09-10）

| 本仓库目标文件 | 问题与设计 | 实际来源及本地差异 | 验证 / 审查入口 |
| --- | --- | --- | --- |
| [ADR-0009](adr/0009-capability-tiered-release-gate.md)、[`support-policy.json`](../release/support-policy.json) | 确定性核心能力、真实模型工作流和实验适配不能用统一全绿状态表达；acceptance 不能自行决定放行 | 用户批准的 0.4.0 正式发布计划是需求来源；沿用 SPEC-0005 的准确包和不可覆盖版本原则。能力分级、schema 3、证据复用限制及 `next` 后 promotion 是本地发布治理决定，不冒充外部标准 | `tests/test_release_gate.py` 的策略完整性、状态汇总、路径/摘要、复用与 review 反例；最终独立 release review |
| [Codex trace parser](../tests/gate_process_trace.py) | 未知 syscall 返回既要 fail closed，也要留下可复核且不泄密的有界诊断 | 既有 Claude trace 的 bounded diagnostic 结构作为仓库内已测试先例；具体字段和隐私限制来自用户批准计划 | `tests/test_gate_process_trace.py` 的上限、类型、上下文缺失和秘密/路径/argv 反例；保留原 trace 离线回放 |

历史 reproduction/checkpoint 是观察证据，不作为新策略的设计权威，也不因分级发布被回写为成功。

## 0.5.0 Skill/Hook 文档交接（2026-09-13）

本节的需求来源是用户批准的 0.5.0 实施计划。用户提供的
[提案原文](planweft-document-management-proposal.md)以 SHA-256
`e1cafbf781c7a3f3a4e2e7efd149102ec10ee932571e9f91563e868220ef824d` 原样保留；它是研究输入，
不是批准规格或实施完成的证据。固定 PWF v3.17.0 的 selector、attestation、phase、cap 和 stall
实现只用于界定补丁锚点。单一 HTML marker、私有分类器和版本化静态门禁是针对本仓库约束的最小组合，
不作首创或通用安全保证。

| 本仓库目标文件 | 问题与设计 | 实际来源及本地差异 | 验证 / 审查入口 |
| --- | --- | --- | --- |
| [SPEC-0006](specs/0006-skill-hook-document-handoff.md)、[ADR-0010](adr/0010-skill-hook-document-handoff.md)、[PLAN-0011](plans/0011-skill-hook-document-handoff.md) | 让 Skill 完成授权内文档判断，Hook 仅读取交接状态；不增加 CLI、映射或第二状态引擎 | 用户批准计划、原样提案和固定 PWF 三文件/phase parser；`pending` marker 与目录不迁移为本地最小取舍 | REP-0013；REV-0013 source/cold read |
| [build-plugin.py](../scripts/build-plugin.py)、[workflow](../overlays/planweft/workflow.md)、[task_plan 增量](../overlays/planweft/templates/task_plan.append.md) | 将唯一 marker 和 Skill-first、兼容控制边界写入所有生成入口/模板 | 固定 PWF Skill/模板；用户要求不以人工命令作为日常文档维护前提。仅向已有 Stop gate 锚点注入 helper，不手改生成物 | `tests/test_document_handoff.py`、`tests/test_record_templates.py`、构建一致性 |
| [私有检查器](../overlays/planweft/document-handoff-check.sh)、[native Hook](../overlays/planweft/native/native-hook.py) | 缺失、错位、重复、非法 marker 保守为 pending；写后只提醒，显式 gated 仅细化既有 block reason | 固定 PWF `check-complete.sh` 的 selector/attestation/in-progress/cap/stall 顺序；用户限定 Hook 不写文档、不猜授权 | marker、native Hook、PWF 包装夹具；REV-0013 source review |
| [`support-policy-0.5.json`](../release/support-policy-0.5.json)、[0.5 gate](../scripts/check-document-release-gate.py) | 将 0.5 静态/逻辑门禁与冻结 0.4 schema 3 证据分离；Passed 绑定 archive 和附件摘要 | 用户批准的 0.5 范围；0.4 `check-release-gate.py` 的本地附件/摘要边界作为实现先例，不改写旧 policy | `tests/test_document_release_gate.py`；REP-0013；registry/promotion 留待发布阶段 |

0.5.0 的静态证据不能由本文或 0.4.0 历史替代；registry promotion 仍是独立发布阶段。

### 0.2.0 实施文件映射

| 第一方入口 | 具体设计及精确依据 | 本地差异与验证 |
| --- | --- | --- |
| [import-pwf.py](../scripts/import-pwf.py) | 用户固定 tag/commit、原始快照和完整清单要求；Git `rev-parse <tag>^{commit}`、`archive`、clean status；PWF-317 LICENSE | 标准库导入胶水；699 文件 SHA/size/mode、archive digest 与原始 baseline，研究 gitlink 不变 |
| [build-plugin.py](../scripts/build-plugin.py) | 用户“固定上游+扩展+生成分发”、全平台自包含与单身份映射；PWF-317 各 adapter 源码与 manifests；HOOKS-20260908 插件相对路径与trust、SKILLS-20260908原生调用策略 | 不新增调度器；原生实现保留，补丁见PD-P01～10；重复构建、漂移检测、回归、真实skills/list与REV |
| [workflow.md](../overlays/program-design/workflow.md) | PWF-317 Skill 的计划、恢复和 owner 协议；用户 PDB-04～06/08；既有 PD-03～07、P-03 Progressive Rigor、P-12 Confirmation | 前置范围优先于 PWF Create Plan First；不把 attestation/gate 当人工批准或语义正确性；真实维护与只读样例 |
| [evidence.md](../overlays/program-design/references/evidence.md) | 用户准确来源、缺证检索及独立依据 review；P-12 More Information/Confirmation；P-06 Stage 3 为冷读方法 | 依据 review 与理解冷读分开，未检索不写已检索，缺宿主记 Not Run；REV-0005 与实际试用 |
| [controls.md](../overlays/program-design/references/controls.md) | 用户辅助操作必须显式、保留原生平台能力；PWF-317 各 script、Pi registerCommand、OpenCode tools 定义 | Codex 无额外自动辅助 Skills，以主入口子操作映射真实脚本；命令/注册契约 |
| [task_plan 增量](../overlays/program-design/templates/task_plan.append.md)、[findings 增量](../overlays/program-design/templates/findings.append.md)、[progress 增量](../overlays/program-design/templates/progress.append.md) | PWF-317 各模板及 check-complete/phase-status 解析格式；用户三文件/长期文档职责 | 只加必要记录槽，不新增 parser phase/status/checkbox；原模板与增量模板运行结果对照 |
| [doctor-overlap.sh](../overlays/program-design/doctor-overlap.sh) | 用户可检测重复安装诊断；PWF-317 plan-doctor；HOOKS-20260908 多源共同执行 | 只读目录检测不等于激活判定，旧脚本不执行；独立具备可观察副作用的负样例 |
| [BUILD.md](../overlays/program-design/BUILD.md)、[PATCHES.md](../overlays/program-design/PATCHES.md) | 用户禁止平台共享副本手改及保留本地补丁清单 | 逐补丁列实际位置/原因/验证；PD-P07保留原测试边界，PD-P08明确Codex原生implicit策略 |
| [包 README](../overlays/program-design/README.md)、[包内安装说明](../overlays/program-design/install/INSTALL.md) | PWF-317 各安装表面，HOOKS-20260908；固定 Pi `packages.md`；本地包和原生注册实测 | 不使用未发布 npm 名称作为安装入口；相对链接/资源、Codex 隔离安装、其他宿主 Not Run |
| [平台说明](platforms.md)、[上游维护](upstream-maintenance.md) | 同上及用户分级验证/一次性状态入口迁移要求 | 实现、静态/协议、真实宿主分别报告；无全局自动安装、无自身接管 |
| [run-upstream-tests.py](../scripts/run-upstream-tests.py)、[requirements-test.txt](../requirements-test.txt) | PWF-317 `.github/workflows/tests.yml` 的 pytest/PyYAML 安装与三个 CI job、Pi/OpenCode package-lock 与 package scripts；首轮 PATH/cache 实际故障 | 新临时树与 Git index、独立缓存、完整日志/JUnit；本地固定实际使用的 pytest/PyYAML 版本；既有失败不被抹除 |
| [test_pwf_distribution.py](../tests/test_pwf_distribution.py) | PDB-01～10 的可执行部分；PWF-317 生命周期/选择/attestation 协议 | 对实际 ZIP、实际脚本和 CLI 检查；不将静态正文匹配视为模型行为通过 |
| [run-pwf-smoke.py](../tests/run-pwf-smoke.py) | 用户隔离安装/真实维护/无历史冷读要求；HOOKS-20260908 trust；既有 R-20 非交互、REP-0004 容器边界方法 | 新临时 HOME、固定包/CLI、随机未泄露标记、逐文件缓存核对、完整轨迹与清理；真实结果另判 |
| [REV-0005](reviews/0005-pwf-migration-review.md) | 用户重要设计独立依据检查；上述原始具体来源、生成字节与本地补丁 | reviewer 不认领自己编写的规格/安装文档的独立审查；构建/分发9发现按内容关闭与披露 |
| [独立交付review](reviews/0005-delivery-review.md) | 用户实质设计/交接核查要求；SPEC/ADR、实际源码、ZIP及全量证据为具体输入 | 新的独立reviewer核查文档主张与实际字节/轨迹；未执行的检查和最终模型包差异明确列出 |
| [首页](../README.md)、[开发说明](development.md)、[测试说明](../tests/README.md)、[.gitignore](../.gitignore) | 用户新插件、架构、安装流程与可接续交付要求；本轮源码和实际命令 | 导航/运行说明，保留旧历史与 books 忽略规则；只增加本次 Python 缓存排除 |

vendor 四文件是导入器产物，dist 与 plugins 由 builder 生成；证据归档由实际运行输出生成，均通过对应清单逐项追溯。这里不为普通打包、测试胶水新增“创新”声明。SPEC/ADR 作者与源实现 reviewer 的职责和实际范围见 REV-0005；主 Agent 负责最终证据整合。


安装补充：用户要求解释并落实各Agent安装方式；PWF-317的`sync-ide-folders.py`、各平台manifest、Gemini settings和脚本原mode为准确源证据。PD-P09将继承发布式说明改为本地ZIP路径，PD-P10针对实际127/126退出修复Gemini命令。新增[test_pwf_installation.py](../tests/test_pwf_installation.py)与[独立安装review](reviews/0005-installation-review.md)检查实际包入口和命令；[补充证据](reproduction/evidence/0005/installation/README.md)区分静态、协议与当前Codex无模型安装预检。[.gitattributes](../.gitattributes)保护可重复构建所需换行和上游Windows CRLF，不代表Windows宿主已实测。

## 0.3.0 原生分发与更新

需求来源：用户批准的 [SPEC-0004](specs/0004-native-distributions.md)；版本取舍见 [ADR-0007](adr/0007-native-distributions.md)。以下官方页面/源码在线核查日期为 2026-09-08；没有把上游 PWF 旧安装文案当成宿主当前协议。

| 第一方入口 | 精确来源与实际借鉴 | 本地实现与证据 |
| --- | --- | --- |
| [生成器](../scripts/build-plugin.py)与六 catalog | [Codex 插件](https://developers.openai.com/plugins/build/plugins)、[Claude marketplace](https://code.claude.com/docs/en/plugin-marketplaces)、[Cursor plugins](https://cursor.com/docs/reference/plugins)、[Copilot CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)、[Factory plugins](https://docs.factory.ai/harness/plugins)、[CodeBuddy marketplace](https://www.codebuddy.ai/docs/cli/plugin-marketplaces) 各自的目录入口和相对 source | 独立 catalog 指向对应 dist；目录摘要/模式与兼容镜像是本地维护选择；构建漂移、真实 CLI 缓存核对见 REP-0006 |
| [native adapters](../overlays/program-design/native/adapters.py) / [hook bridge](../overlays/program-design/native/native-hook.py) | [Cursor hooks](https://cursor.com/docs/agent/hooks)、[Copilot hooks](https://docs.github.com/en/copilot/reference/hooks-configuration)、[Gemini hooks](https://geminicli.com/docs/hooks/reference/)、PWF-317 inject-plan.py / gate 实现 | 原生输出字段、安装资产与项目 cwd 分离；不放宽工具权限；独立运行时 review、协议与 Codex 真实注入证据 |
| [OpenCode 编译器](../scripts/compile-opencode.py) / [发布准备](../scripts/prepare-native-release.py) | [OpenCode V1 plugins](https://opencode.ai/docs/plugins/)、[V2 migration](https://opencode.ai/v2/docs/migrate-v1/)、[Pi packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md)、[npm pack](https://docs.npmjs.com/cli/v11/commands/npm-pack)；PWF 固定 lock/tsconfig | 保留 V1；维护者预编译、普通构建离线；实际 npm 文件清单及编译/发布输入两阶段绑定为本地可追溯机制 |
| [发布树与安装配对](../scripts/prepare-native-release.py) | [Gemini releasing](https://geminicli.com/docs/extensions/releasing/)、[Hermes plugins](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins)、[Hermes Skills Hub 源码](https://github.com/NousResearch/hermes-agent/blob/main/tools/skills_hub_github.py) | 专用分支根满足 manifest/保留 Git 元数据；Hermes Skill 固定提交复制，无虚构 --ref；版本/内容配对并非原子更新器 |
| [安装指南](../overlays/program-design/install/INSTALL.md) / [平台矩阵](platforms.md) | [Kiro Powers](https://kiro.dev/docs/powers/installation/)、[Kiro v3 auto pickup](https://kiro.dev/docs/cli/v3/new-features/#powers-auto-pickup)、[Continue loader](https://github.com/continuedev/continue/blob/main/extensions/cli/src/util/loadMarkdownSkills.ts)、[Mastra config](https://code.mastra.ai/configuration)、[Agent Skills](https://agentskills.io/specification) | 原生 GUI 或完整 Skill 目录安装；按各宿主真实能力说明更新/卸载；Kiro 缓存资源定位，语言资源随主 Skill 独立复制 |
| [生命周期 runner](../tests/run-native-lifecycle.py)、[marketplace runner](../tests/run-marketplace-lifecycle.py)、[OpenCode probe](../tests/run-opencode-native.py)、[Codex hook probe](../tests/run-codex-hook-probe.py) | 用户 A/B、增改删、回退/卸载、项目保护要求；上述宿主官方 CLI help/实际命令；HOOKS-20260908 trust | 临时 HOME/cache、无个人认证、无模型；CLI 返回值、实际安装内容与真实事件送达分别验证；合成 provider 不作语义效果证据 |
| [REP-0006](reproduction/0006-native-distributions.md)及两份 review | 本轮实际日志、固定源码、独立审查 | 原始输出可追溯；Hermes Failed、远程/模型/GUI/OS Not Run 明列；旧证据不冒充新链路已测 |

平台目录、原生 manifest、镜像与编译中间产物均由对应脚本生成，不为每份共享副本建立不同设计来源。普通目录/打包/测试胶水不另作创新声明；状态协议与文档工作流继续采用 0.2.0 已登记来源。

## 双语公开文档整理（2026-09-08）

需求来源：用户要求 README 聚焦定位、实现思想、类似方案表格、借鉴及原创部分；安装与跨平台设计单列，中英文互链。[PLAN-0007](plans/0007-bilingual-public-docs.md) 记录范围，历史规格与证据保持原文。

| 文件或生成入口 | 实际依据与归属 | 本轮检查 |
| --- | --- | --- |
| README.md / README.en.md | SPEC-0003/0004 与已实现 workflow；PWF-317 Skill 和 workflow After Completion；P-03 concepts、P-04 writing-plans/Pi薄适配、P-06 doc-coauthoring、P-12 MADR固定模板 | 固定源码比较；直接移植、思想借鉴、本地组合明确分开，不宣称方法首创或效果排名；两名 reviewer 范围互补 |
| 安装 overlay 中英、docs/installation 中英镜像、各包 README/INSTALL 中英 | 0.3.0 已核对的官方宿主命令和 REP-0006；本轮只翻译/整理正文，保留命令、scope、限制及历史失败 | 中英文命令块/URL集合一致、原生包内容、独立语义检查；历史宿主结果不冒充双语产物实测 |
| docs/platforms.md / platforms.en.md | 固定快照、overlays/native、build/compile/prepare实际实现；六catalog协议和REP-0006矩阵 | 设计说明与安装教程分工；原生hooks、更新、恢复、发现、trust与未测范围分别解释 |
| build-plugin.py、native/adapters.py、prepare-native-release.py、编译清单 | 用户公开文档双语与单一来源要求；既有确定性生成/自包含/漂移拒绝方案 | 新增两种语言的镜像与npm files条目，运行文件差异审计；不新增运行时行为 |
| tests/test_public_docs.py、分发漂移测试与测试说明 | 用户双向导航、引用两种语言、完整安装方法要求 | 校验相对链接、语言配对、命令一致与镜像漂移；不能替代翻译语义审查 |
| innovations.md、开发约定、BUILD说明 | 已登记来源与0.2/0.3具体代码 | 修正历史候选尚未实施被误读为当前状态的问题；本地代码贡献与方法新颖性分开 |

源码比较由独立成员实际读取固定归档/子模块；浏览器也复核 OpenSpec、Superpowers 和 MADR 固定页面，PWF 页面抓取失败时使用已校验归档，不将抓取失败写成来源不存在。review 范围与参与比较草稿者的独立性限制见 [公开文档审查](reviews/0007-public-docs-review.md) 及 [README/分发独立复核](reviews/0007-readme-distribution-review.md)。

## PlanWeft 统一 npm 安装器（0.4.0）

- `lib/installer.mjs` 的集中存储、链接与显式 scope 借鉴 Vercel Skills 固定提交 [installer.ts](https://github.com/vercel-labs/skills/blob/1682051d48c34f5eb135e6475c1a965dce05e820/src/installer.ts) 和 [skill-lock.ts](https://github.com/vercel-labs/skills/blob/1682051d48c34f5eb135e6475c1a965dce05e820/src/skill-lock.ts)。代码独立实现。
- 根 npm `pi` 字段依据 [Pi packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md)；OpenCode 根 exports 与 loader 依据 [V1 plugins](https://opencode.ai/docs/plugins/)。
- scope 独立 catalog、逐步失败收据、拷贝 staging 与用户修改保护是本地组合设计，见 ADR-0008；不声称这些通用机制为首创。
- npm 发布认证依据 [trusted publishers](https://docs.npmjs.com/trusted-publishers/)。真实宿主与 npm 认证结果单独记录，不能由源码结构推定。

## DSH 增量适配（2026-09-08）

- `scripts/build-plugin.py`、`overlays/planweft/native/adapters.py`：沿用既有 portable Skill，按 [DSH filesystem provider](https://github.com/deepseek-ai/deepseek-harness/blob/c389f96bf3a9b6807cb71ed6bdad5849be0df6d8/packages/skill/skill-filesystem/README.md) 的单层扫描布局生成；不复制 DSH 源码。
- `lib/installer.mjs`：DSH Git 根、DSH_HOME 规则以官方 provider 与 [home-paths](https://github.com/deepseek-ai/deepseek-harness/blob/c389f96bf3a9b6807cb71ed6bdad5849be0df6d8/packages/util/home-paths/src/index.ts) 为依据；本地选择是在 Git 根执行安装，以复用现有 scope/锁/所有权而不新增第二套安装记录。
- 完整集成的候选依据：[官方 hook bridge](https://github.com/deepseek-ai/deepseek-harness/blob/c389f96bf3a9b6807cb71ed6bdad5849be0df6d8/packages/hooks/hooks-claude-code/README.md)、[原生 profile CLI](https://github.com/deepseek-ai/deepseek-harness/blob/c389f96bf3a9b6807cb71ed6bdad5849be0df6d8/apps/cli/README.md)。用户已确认两个运行依赖，当前已实现原生 bundle 与官方 hooks 桥接；未支持的事件及真实模型验收分别记录。
- 运行证据：`tests/run-dsh-skill-smoke.mjs` 用隔离安装的官方 npm 0.1.2-rc.1 组件执行；这与源码参考版本分开记录。安装器测试证明本地生命周期，provider runtime 证明 Skill 发现/加载，两者都不是模型使用证据。

- RC3 `native/dsh/hook.sh`、`hook-shell.mjs`、`index.mjs`：依据上述官方 bridge 的 shell resolve/run 与 stdin session 协议，以及官方 npm 0.1.2-rc.1 SandboxBash 实测。私有临时缓存与有界宿主会话去重是本地兼容组合，不宣称上游提供此实现；保留沙箱权限、其他插件输出与项目 Stop ledger。因果复现、Python/Shell 双路径及独立 review 见 REP-0010 / REV-0010；跨调用 pwf-prog 告警不支持，模型验收另列。

## RC5 Codex 分发路径修复

`build-plugin.py` 的 Codex 专属生成映射根据固定 PWF `.codex/hooks/{stop,resolve-plan-dir,session-start}.sh` 和本仓根 `skills/` 布局修正三处相对路径，原始 standalone 比较树保持不变。固定 [Codex 0.149.1 Stop 源码](https://github.com/openai/codex/blob/rust-v0.149.1/codex-rs/hooks/src/events/stop.rs#L405) 支持 `decision:block`，不能把 RC4 跳过缺失脚本的失败归因为协议不支持。独立包正向/保护回归、原始/迁移对照及真实新归档结果分别记录；来源与行为 review 见 REV-0010。

## RC6 入口与验收修复

- `scripts/build-plugin.py`、`overlays/planweft/entrypoints/`：依据 [Claude Skills 官方说明](https://code.claude.com/docs/en/skills#add-supporting-files) 的入口/按需引用组织及 description 匹配职责，将固定 PWF 手册保存在各完整 Skill 副本内，保留宿主能力与显式历史读取披露。六语言入口是本地维护的任务流程表达，不宣称能保证模型每次自动采用。
- `tests/gate_process_trace.py`：依据 [clone(2)](https://man7.org/linux/man-pages/man2/clone.2.html) 的 CLONE_FILES/CLONE_FS 共享与复制，以及 [execve(2)](https://man7.org/linux/man-pages/man2/execve.2.html) 的 FD 表解除共享；核对 [Linux v6.12 fs/exec.c](https://github.com/torvalds/linux/blob/v6.12/fs/exec.c)。本地实现用重叠区间和资源读写集合判定归因歧义，是测试采集器，不修改插件 gate。未知返回和截断仍拒绝通过。
- 历史结果与本次检查区分、schema 2 逐场景门槛、资源检查及已结束缓存清理是本轮用户批准的验收约束；具体实现与反例经独立审查，不宣称来自上游 PWF。

## RC7 记录状态一致性修复

固定 PWF v3.17.0 的 `skills/planning-with-files/scripts/init-session.sh` / `.ps1` 使用 here-doc 创建普通 progress，并硬编码初始 Current Status；`templates/progress.md` 另有动态阶段占位。本地“追加模板规则”因此没有覆盖实际默认初始化。这与已批准的 task_plan 唯一动态状态设计冲突，RC6 Codex 原生维护及独立审查确证了冲突；Pi/DSH findings 同样出现修复前观察仍称当前的缺陷。源码归档及版本摘要见 `vendor/planning-with-files/upstream.json`，独立依据与行为记录见 REV-0010 和对应 RC6 JSON。

本地最小修复为生成时替换重复状态、指向同目录 task_plan，并在 findings 提供观察时间/修订提示。它组合已有 Markdown 相对链接、PWF 追加事件记录及本仓证据区分规则，不引入第二个状态服务、同步器或自动改写既有文件。任务阶段解析保持上游协议；实测初始化内容与既有字节保护分开验证。


## RC8 可观察的计划选择与记录核对

- 主 Skill 的解析分支以固定 PWF [resolve-plan-dir.sh](https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/skills/planning-with-files/scripts/resolve-plan-dir.sh#L300) 的拒绝仍返回 0、空输出 legacy 回退和 [init-session.sh](https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/skills/planning-with-files/scripts/init-session.sh#L377) 的 PWD 命名初始化为依据。PowerShell/i18n及旧宿主副本保留根布局，不能笼统承诺 PLAN_ID 输出。此处只调整入口决策说明，未改变固定脚本或项目状态协议。
- 优先使用宿主已有 Skill location，以 [Pi v0.84.3 skills.ts](https://github.com/earendil-works/pi/blob/v0.84.3/packages/coding-agent/src/core/skills.ts#L332) 和 [system-prompt.ts](https://github.com/earendil-works/pi/blob/v0.84.3/packages/coding-agent/src/core/system-prompt.ts#L146) 为据，辅以实际 native RPC 的绝对 sourceInfo.path。未截获 RC7 完整系统提示，因此不宣称每次会话都直接观测到了同一 XML。
- 观察日期/版本、修改前后范围、最终“当前行为”事实核对和用户已有修改来源，是原有证据治理的执行字段。RC7 OpenCode 读过新模板后整体覆盖 findings，仍遗留旧实现为当前的记录；因此把这些字段纳入主入口，而非仅留在可能被替换的模板。RC7 Pi/DSH 的宿主配置/变量范围偏离保留为失败，入口只按已提供位置与规划变量定位资源。
- 独立诊断和源码审查见 REV-0010；`tests/test_plan_selection_contract.py` 实际验证空输出的两种状态、legacy 保留、具名初始化及拒绝绑定不回退。脚本契约测试不证明模型一定按文案执行，准确 RC8 模型结果仍需单独验收。


RC9 的加载前资源定位与执行证据修复直接依据固定维护任务边界和 RC8 真实工具顺序，而非新增宿主机制。见 [独立加载前审查](reviews/0010-rc8-preload-evidence-review.md)：Skill 正文返回前已提交的工具无法被正文追溯约束；description 提供规则只是新的待验证指导，不宣称强制隔离。原 PWF consent/capability 披露断言保留。已有证据表区分实际执行/历史来源/静态推断；手工 scratch 的归属遵循用户项目范围，框架隐式缓存另属宿主行为，不新增批准层。

## RC11 原生路径与范围恢复

Pi 的实际 `0.84.3` 项目安装将 package source 写为相对 `.pi/settings.json` 的 `../.planweft/...`。RC10 精确包在安装后 doctor 的原始失败与配置字节证明旧绝对字符串豁免不足；本地修复按配置目录解析已验证的自有来源，只豁免一项，保持其他 scope、重复条目及对象额外字段检查。依据与反例见 [独立路径审查](reviews/0010-rc11-pi-relative-review.md)，真实新包验证另行记录。

固定 PWF [inject-plan.py](https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/scripts/inject-plan.py) 的 PreToolUse 普通视图只取前30行，smart 选择 Goal/Next Step/Current Phase、活跃阶段及部分决定，未选择本地附加的末尾 Scope。RC10 owner 记录也漏掉任务特有范围。将简明且有实际指令来源的范围放入单一目标段，是针对提取契约的本地修复，不改状态格式、快照协议或新增 hook。新初始化的本地化计划只规范一处目标标题；受保护已有标题保持，不能保证 smart 保留时完整重读。见 [独立范围恢复审查](reviews/0010-rc11-scope-recovery-review.md)。

纯函数对照确认末尾遗漏、Goal保留及本地化/混合标题边界；不证明实际模型看到了提醒，也不能补救计划初始化前已发生的宿主配置读取。计划仅记载授权，不把注入的数据提升为权限或人工批准。

## RC12 原生配置与模式说明

固定 Pi [v0.84.3 settings-manager](https://github.com/earendil-works/pi/blob/v0.84.3/packages/coding-agent/src/core/settings-manager.ts) 读取/写回已有配置时先调用 [stripBom](https://github.com/earendil-works/pi/blob/v0.84.3/packages/coding-agent/src/utils/text.ts)，仅移除一个开头 U+FEFF。本地安装器据此修正 Pi 自有来源 JSON 解析，不修改通用 JSON、外来配置或重复检测语义；见 [BOM 独立复核](reviews/0010-rc12-pi-bom-review.md)。

OpenCode 原生 `pw_init` 选择面原先只列 autonomous/gated，遗漏省略参数的默认路径。RC11 真实会话在未选择模式时传 autonomous；本地补丁只补选择说明，不改状态与运行逻辑，不声称强制授权。来源、精确 diff 及局限见 [模式入口独立复核](reviews/0010-rc12-opencode-mode-review.md)。完整 Skill 投递后的违规不能再笼统归因于未加载；后续模型行为修复须有新的因果证据，不以重复提示或无变化重试代替。


## Codex 自有原生注册识别修复（RC13 准备）

固定 [Codex ff29a443 config schema](https://github.com/openai/codex/blob/ff29a44391deccde0aba0f8390337d7f3c319ea4/codex-rs/core/config.schema.json) 将 `marketplaces.<name>` 表的 `source_type` / `source` 与 `plugins.<name>` 的启用状态分开；RC12 额外无模型诊断的实际 TOML 投影和原生 `marketplace list --json` 与该结构一致。自有目录是持久安装来源，不能仅因路径含 `planweft` 判为第二个插件。

本地选择按解码结构校验安装记录、scope、步骤和 managed registry/payload 摘要，仅豁免精确自有 key/source；保留其他 key/value 扫描及普通别名复用同目录的拒绝。借助锁文件已有 [toml 4.3.0](https://registry.npmjs.org/toml/-/toml-4.3.0.tgz) parser 的实际源码解析 TOML，严格 UTF-8 解码在本地完成；不写回解析对象，不声称其数值精度或语法覆盖等于 Codex 完整配置校验。直接依赖声明仍待确认，当前 NODE_PATH 只用于离线开发验证，不构成分发依赖契约。来源、原始发现与处理见 [独立实施复核](reviews/0010-rc13-codex-registration-review.md)；未执行准确修改归档的真实验收。

用户随后明确允许将已有锁定 `toml@4.3.0` 声明为直接依赖。69 个非根 lock 条目逐项保持不变；check/publish 两个 CI 入口均在安装器回归前执行 `npm ci --ignore-scripts --omit=dev`。已从真实安装的依赖重跑，不再使用 NODE_PATH。依赖边界和工作流复核见 [独立依赖审查](reviews/0010-rc13-dependency-review.md)，原待确认记录作为历史保留。

## RC14 操作例程与判断分支

Python 官方 [Path.resolve](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve) 与 [TemporaryDirectory](https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryDirectory) 分别提供链接规范解析、显式父目录及 context manager 清理语义（2026-09-10 实际核查）。本地双语例程只传入宿主已列出的 Skill 路径或已授权项目；不扫描配置，不改变整个宿主的 TMPDIR。中文空格路径、多层相对链接、缺失路径和异常退出已有离线对照，不能因此宣称模型实际遵循。

采用判断由原先两段条件说明改成三个有实际来源的分支动作，沿用已有只读/简单任务/明确禁止采用的边界，不引入批准程序或决策文件。此项是对 Claude 已读取正文仍误判例外的待验证干预；PWF 或 Python 文档不证明其行为效果。见 [独立工作流复核](reviews/0010-rc14-workflow-review.md) 和 [Pi 发现复核](reviews/0010-rc14-pi-discovery-review.md)：Pi 原生预检提供准确路径，现有证据不足以认定安装定位缺陷，也未保留当次最终系统提示。不得用新示例回写旧模型失败。
