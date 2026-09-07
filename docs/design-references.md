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

来源可访问、内容支持该借鉴和本仓库效果验证是三种不同状态。基础文档依据见 [REV-0001](reviews/0001-evidence-review.md)；首版 Skill 的状态以 REP-0003/REV-0003 为准，专用 CLI、hooks 与自身接管未实施。未通过 review 的新条目不能标为已验证设计。

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
