# PlanWeft：与 PWF 的实现对照及文档管理开发提案

状态：研究与开发建议，尚未作为仓库批准规格，也未实施代码修改。
核查日期：2026-09-12。
核查方法：固定提交的源码、Skill、Hook 配置、产品文档和参考子模块定向阅读；本次未执行完整构建、测试或真实宿主验收。

## 1. 比较口径

| 对象 | 固定版本 / 提交 | 用途 |
| --- | --- | --- |
| PlanWeft | 0.4.0；`b05add2d172ae215a0c30db34720c84edbb153ae` | 本次核查的 master 快照 |
| 实际 PWF 运行时基线 | v3.17.0；`0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7` | vendor/upstream.json 指定的构建输入 |
| PWF 参考子模块 | `d47a61950e784fc4237ba10ddc1e9e198bd0f275`；Skill 标注 3.16.1 | 研究输入，不等同于实际运行时 |

固定运行时与参考子模块不同，不自动构成错误；但后续对照、升级和验收必须注明使用哪个版本。本提案不声称覆盖 PWF 最新主分支，也不提供未经全量语义比较的“代码相似度百分比”。[S1][S2][S3]

判断：PlanWeft 是“PWF 规划运行时 + 文档维护工作流 + 原生宿主适配与分发/验收工程”，不是独立规划引擎重写，也不是仅改产品名。[S1][S4][S5]

## 2. Skill 与 Hooks：保留了什么，改变了什么

### 2.1 Skill

PWF v3.17.0 已有三文件工作记忆、命名计划与 PLAN_ID/PWF_PLAN_ROOT 选择、拒绝无效绑定后的跨任务回退、单一 owner、项目文件恢复、显式历史 metadata/replay、模式与 attestation 等能力。不能把这些列作 PlanWeft 原创新增。[S6]

PlanWeft 的主要语义增量是：

- 将主入口从通用规划调整为调查、实施、回归和交接的四步工作流；只读与简单任务不初始化记录。
- 先识别实际授权范围；禁止仅为寻找插件资源而读取宿主配置、安装收据或无关环境变量。
- 复用旧资料，但将当前目标、阶段、下一步统一到选中的 task_plan；旧入口只保留导航，不双向维护两套状态。
- progress 保存实际操作、错误与验证；findings 保存有时点的观察和来源；稳定文档在原有位置增量维护。
- 区分历史检查与本次检查；未运行是 Not Run；核对当前断言与后续更正，区分独立依据审查和无聊天上下文的冷读。
- 主 Skill 渐进加载 PWF 手册、控制说明、计划选择与证据指导，而不是要求所有任务先读全部材料。[S4][S5][S7]

这些仍主要是模型应遵循的工作规则，不等同于文件系统隔离、用户批准或实现正确性证明。[S1][S7]

### 2.2 Hooks

| 范围 | PWF 基线 | PlanWeft 0.4.0 | 结论 |
| --- | --- | --- | --- |
| Codex 注册事件 | 7 类 | 7 类 | 检查的两份 hooks 配置中，事件、matcher、命令和超时一致，顶层描述的产品名不同 |
| Claude Code 注册事件 | 6 类 | 6 类 | 事件覆盖相同；调用序列化从 command+args 变为完整带引号 shell command |
| 主 Skill 身份 | planning-with-files [R1] | project-docs | 名称与工作流定位改变，不等于新 Hook 引擎 |
| 规划文件协议 | 三文件与原有状态解析 | 保留 | PLAN_ID、PWF_*、PLANNING_DISABLED 等继续兼容 |
| 本地差异台账 | 不适用 | PD-P01～PD-P15，另有 RC 增量 | 是补丁分组数量，不是新增功能数或代码变化比例 |

Codex 的 7 类事件为 SessionStart、UserPromptSubmit、PreToolUse、PermissionRequest、PostToolUse、PreCompact、Stop；这是两个插件配置的注册数量，不是宿主所有可用事件的数量。[S8][S9][S10][S11]

实际工程差异包括：内联 Python 的 -I 隔离、旧适配禁用分支、跨平台引用与资源路径、原生协议转换、重复来源诊断、自包含包、生成产物摘要及用户文件保护。部分是运行时加固，部分是安装和分发可靠性；应分别说明。[S4]

### 2.3 当前支持边界

构建器列出 15 个宿主目标；README 的正式核心支持是 Codex、Claude Code、Pi、OpenCode V1、DSH 五宿主。其余适配及 autonomous/gated、真实模型自动采用等不能统一称为“全部正式验证通过”。Codex gate-cap 配对的 syscall 归因限制在公开材料中仍保留 Failed。本文没有重新执行这些验收。[S1][S14]

## 3. 参考子模块：借鉴与边界

子模块清单及固定提交以 PlanWeft 索引为准。PWF 参考快照和实际运行时快照均作了定向阅读，实现对照采用实际运行时；其他方案按固定子模块阅读。上游支持一种方法，不代表方法在 PlanWeft 上的收益已验证。[S3]

| 参考方案 | 可借鉴机制 | PlanWeft 的具体落点 | 不应照搬 |
| --- | --- | --- | --- |
| planning-with-files | 工作记忆、绑定、恢复、模式与现有适配 | 保留兼容协议与原始基线回归；新增文档能力走 overlay | 再运行一套 PWF Hooks；重新发明同一规划状态 |
| OpenSpec [R2] | 当前规格与变更提案分离；变更包、合并、归档；按风险渐进加严 | findings 中候选结论经过确认后进入 specs/ADR；完成任务保留可追溯归档 | 同时维护 tasks.md 和 task_plan 两套动态状态；为适配代码自动改需求 |
| Superpowers [R3] | 可独立测试和审查的任务；精确文件、输入输出接口、规格覆盖 | 为重要任务明确输出文件、验证入口和文档影响；复用已有 reviewer | 每个小改动都强制完整工作流、重复详写代码与多轮子代理 |
| agent-markdown-memory-bank-protocol [R4] | 产品背景、当前上下文、架构、日志的职责分离 | 项目背景和架构作稳定导航；active-context 只指向现有任务计划 | 同时创建多个“下一步”源；对只读任务也强制写入 |
| cursor-memory-bank [R5] | 分层规则、按复杂度加载、reflect/archive | 任务相关加载和按需文档集合；活动资料与历史资料分开 | 把作者 token 节省比例当成本项目实测收益；把 Cursor 流程硬套所有宿主 |
| anthropics/skills 的 doc-coauthoring [R6] | 无旧上下文的读者测试，发现歧义和遗漏后修订 | 将已经采用的冷读方法做成可重复的交接回归夹具 | 把读者回答通顺等同于来源可靠或科学结论正确 |
| spec-kit [R7] | 可验证用户场景、需求标识、独立验收、量化成功标准 | 重要变更关联需求→任务→测试→相关文档；先用简单 Markdown 表 | 每项任务都部署完整规格框架，制造无消费方的元数据 |
| design.md [R8] | 结构化视觉 token 与解释正文分工；文档类型专用 schema | 为特定文档提供可选校验器；区分视觉设计与技术架构 | 把视觉 DESIGN.md 当通用架构规范；强制无 UI 项目生成视觉文件 |
| stitch-skills [R9] | 从实际资产提取、归纳并生成设计文档 | 可选 UI 文档流程，保留输入、提取来源和验证方式 | 在核心插件默认引入 Stitch MCP 或外部服务依赖 |
| rulesync [R10] | 统一来源、按宿主和 scope 生成、选择性导入与输出 | 强化现有生成器的宿主能力矩阵、管理边界及生成来源追踪 | 再写一套并行生成器；持续双向同步所有用户配置 |
| Pi [R11] | 原生生命周期与工具/命令扩展；宿主能力边界 | 共享文档检查逻辑，使用已有宿主适配器转换事件和输出 | 假设不同宿主事件等价；用私有会话存储替代项目文件恢复 |
| MADR [R12] | proposed/accepted/superseded、取舍、后果和 Confirmation | 为重要决定保留确认方式、证据和替代关系；继续用最小模板 | 为小改动都写完整 ADR；覆盖旧决定而丢失历史理由 |

对应第一方依据：[R1]～[R12]。

许可处理：PlanWeft 的来源索引注明 rtoma 与 cursor-memory-bank 固定版本未见根目录许可证，anthropics/skills 为混合许可。借鉴机制与逐字复制代码/提示词是不同操作；复用具体内容前应核对相应文件的许可，不以公开仓库可读推定可任意再分发。[S3]

## 4. 将用户给的目录转为文档管理职责

本表是建议，不要求现有项目迁移目录或一次性建立全部文件。

| 用户示例 | 建议处理 | 管理规则 |
| --- | --- | --- |
| README.md | 保留 | 面向使用者的用途、运行与导航；不复制长期任务日志 |
| CODEX.md | 可保留为人工指南；自动入口默认使用 AGENTS.md | CODEX.md 不是默认自动发现文件，除非显式配置 fallback；不要复制两套约定 |
| codex.config.json | 仅作为自有 wrapper 的配置（若确有读取程序） | Codex 原生配置为 .codex/config.toml 等路径；不自动改宿主设置 |
| commands/*.md | 可作为命令模板规范源 | 必须由宿主适配器注册或映射；目录存在不等于命令生效 |
| skills/*/skill.md | 使用 SKILL.md；仓库本地发现可用 .agents/skills/*/SKILL.md | 插件源码内 skills/ 可经 manifest 分发；普通根 skills/ 不能直接假定自动加载 |
| agents/*.md | 保留为可选角色规格/模板源 | 原生子代理注册按宿主实现；不能把目录里的说明文件当成已运行 Agent |
| memory/rules.md | 复用 AGENTS.md 与既有开发规范；必要时仅保留索引 | 不复制独立的第二套项目规则 |
| memory/decisions.md | 复用 docs/adr/ 或项目既有决定记录 | 单独 decisions.md 可作索引；保留 superseded 关系 |
| memory/context.json | 可再生成的缓存 | 记录来源与失效条件；不是任务权威源、批准证明或唯一恢复入口 |
| output/reports、charts、logs | 默认产物区 | 只把被选择的结果提升为交付或证据；不把全部日志自动注入上下文 |
| scripts/run_codex.sh、init_project.sh | 按实际工具链提供 | 不能默认执行；初始化幂等、保护已有文件；需要时提供 Windows 入口 |
| scripts/deploy.sh | 可选业务脚本 | 文档维护不自动授权部署 |
| .gitignore、.env.example | 按现有项目维护 | 示例环境不含真实凭据；缓存/临时产物按项目保留策略处理 |
| package.json | 仅适用需要 Node 工具链的项目 | PlanWeft 自身使用 Node，不代表被管理的 Python/Rust 等项目必须新增 package.json |

Codex 默认指令发现、SKILL.md、.agents/skills 以及 Hook/配置来源以官方文档为准。[O1][O2][O3]

### 一个可选的使用方项目示例

```text
my-codex-project/
├── README.md
├── AGENTS.md
├── .gitignore
├── .env.example
├── .codex/
│   └── config.toml                 # 可选：宿主原生配置
├── .agents/skills/
│   └── data-analysis/SKILL.md       # 可选：项目业务技能，不重复复制已装 PlanWeft
├── docs/
│   ├── README.md                   # 项目文档索引，可承载角色/路径映射
│   ├── specs/
│   ├── architecture/
│   ├── adr/
│   ├── reproduction/
│   └── archive/
├── .planning/<plan-id>/            # 命名计划示例，实际位置服从原 resolver
│   ├── task_plan.md
│   ├── findings.md
│   └── progress.md
├── commands/                      # 可选模板规范源，需宿主映射
├── agents/                        # 可选角色规格，需宿主注册
├── scripts/
├── memory/context.json            # 可选缓存，可删除后重建
├── output/
│   ├── reports/
│   ├── charts/
│   └── logs/
└── package.json                   # 仅在项目确实需要时
```

现有 README、architecture.md、DESIGN.md、TODO.md、memory-bank 或其他路径可以继续使用。插件应识别职责与所有权，不应把迁移到上述目录当作采用成功的标准。

## 5. 建议的最小功能路线

### 5.1 先建立可复现失败，再选择是否工具化

SPEC-0001 已明确：角色 JSON、来源指纹、锁、apply/doctor 等不能仅因讨论过就实施。先用实际夹具证明普通 Markdown 流程的缺口；无必要不增加新数据库、服务、schema、锁或新 CLI。[S12]

P0 建议只做“文档发现和影响检查”，可先作为现有主 Skill 的显式只读操作；若重复出现需要确定性检查的失败，再实现共享 helper。新名称 `pw-doc-check` 仅为提案名称，不是现有发布命令。

### 5.2 文档角色与唯一来源

复用现有 docs/README.md 或相当入口，用最小映射描述：文档角色、实际路径、适用范围、更新触发条件、生成来源（如有）。映射不复制文档正文和任务状态。

必须区分：

- 项目规则与批准需求：按原有授权程序变更。
- 稳定知识：架构、API、决定、使用指南；在原处维护。
- 活跃工作：所选 task_plan/findings/progress。
- 验证证据：不可把未运行写成通过；历史与当前运行有明确区别。
- 生成产物与缓存：有来源、可重建，不承担独立权威。
- 历史归档：可追溯，但默认不全量读取或注入。

### 5.3 变更影响检查

输入为已授权的变更文件集合及文档映射，输出为受影响的文档候选、缺失关联与明确豁免。第一版不承诺自动判断全部语义一致性。

例：修改公开 API 后，报告相关接口文档、示例、测试是否已有对应变更或明确说明；不是机械要求每个改动都改 README。

发现文件过期与决定修改它是两步。检查器不能自动提升权限，不能为了“检查全面”读取 .env、宿主设置、无关目录或外部聊天记录。

### 5.4 活跃资料、长期知识与归档

建议流程：观察记录 → 形成候选结论 → 在既有授权下确认 → 更新稳定文档并链接来源 → 关闭任务并归档。

重要约束：

- 未批准候选不能自动变成规格；批准必须关联真实授权来源，不能由模型填写一个 approved 字段就成立。
- 旧事实若已失效，应在原处更正或明确标记观察时点及后继更正；不能只在末尾追加互相矛盾的新段落。
- 第一阶段可原位标记关闭与建立归档索引；确有需要再移动文件。
- 不移动活动的 PLAN_ID 绑定目录；不破坏 resolver、相对链接、已有固定状态语法和历史证据。
- 需要移动时先 dry-run，列出引用变更和可恢复方式；不删除唯一原始证据，不因退出/重试产生二次损坏。
- 后续若存在明确的并发覆盖复现，可在插件拥有的文档操作中引入摘要比较式冲突拒绝；不能把它宣传为任意 Agent 文件写入的事务保证。

### 5.5 上下文预算

磁盘历史资料可以增长；一次恢复和常驻注入不应随全部历史线性增长。工作目标是完整保留当前任务的目标、范围限制、阻塞与下一步，再按任务检索证据。

当前 Codex advisory PreToolUse 路径存在 `--head 30` 注入；主 Skill 因而要求范围在前 30 行，并对本地化 Goal 提示限制。这是现有实现边界，不代表所有宿主/模式只使用 head。[S7][S13]

改进先用测试覆盖中文标题、很长的目标区块、限制位于后文等情形。然后选择兼容旧文档的语义块提取或显式最小上下文视图。超预算时应明确报告并要求按需读取，不能静默丢掉限制，也不应为了缩短内容重写受保护的批准要求。

缓存仅加速上述过程。删除缓存后应能通过项目文件恢复；缓存不能成为批准依据。

### 5.6 冷读和证据校验

将现有独立冷读做成可重复验收：读者仅收到项目文件和问题，不给旧聊天、参考答案或实现者的口头解释。检查目标、约束、已完成工作、证据、未运行项、阻塞、下一步和关键决定。

读者测试判断“文档是否够用”；独立依据 reviewer 判断“来源是否支持主张”；执行测试判断“实现行为是否符合预期”。三者分别记结果，不能互相替代。

## 6. Skill、helper、Hooks 的边界

保留完整插件形态，但不扩张成第二套 Agent 框架：

```text
一个主 Skill：任务匹配、语义判断、维护与交接
          ↓ 按需调用
共享 helper：路径/来源/链接/变更集合等确定性检查
          ↑ 原生协议适配
现有 Hooks：恢复、提示、触发轻量检查；可选且显式启用的门禁
          ↓
项目既有 Markdown、PWF 活动记录、选择性证据与归档
```

| 位置 | 可以承担 | 默认不承担 |
| --- | --- | --- |
| SessionStart / 恢复 | 解析当前计划，读取小范围导航与必要上下文 | 扫描全部历史、读取宿主聊天、初始化全套目录 |
| PreToolUse | 原有计划/范围提醒；在可用协议下检查确定性条件 | 以自然语言猜测代替授权；对所有 shell 行为提供隔离保证 |
| PostToolUse | 标记已授权变更影响，去重提醒 | 无差别改写全部文档、运行整个测试集 |
| PreCompact | 提醒保留关键状态与未解决事项 | 把全部历史压成不可追溯摘要后删除原件 |
| Stop | 轻量核对文档义务、证据与下一步 | 默认阻止一切退出、自动批准需求、强制无限续跑 |
| 显式维护操作 | 预览、语义提炼、经授权写入和归档 | 隐含部署、清理非自有文件、修改宿主权限 |

特别测试 shell 写文件路径：当前 Codex PostToolUse matcher 与 PreToolUse matcher 覆盖不同，因此不能假设每次实际文件变化都经过同一个 Edit/Write 事件。影响检查需按宿主能力及授权的最终变更集合补足；这是待验证覆盖场景，不是本次已复现漏洞。[S8]

多来源 Hooks 可同时生效。延续现有重复来源诊断，不以“后安装插件覆盖旧插件”作为假设，不自动卸载其他插件。[O3]

## 7. 分阶段验收建议

以下为拟定验收目标，均未在本轮运行，不是性能或正确率实测。

| 阶段 / 交付门槛 | 最小交付 | 合并或发布前验收 |
| --- | --- | --- |
| P0：首个文档能力 PR | 目录示例纠偏、文档角色映射、显式只读检查 | 只读模式项目零写入；无新增无用目录；旧状态入口可达唯一当前计划；不访问范围外数据 |
| P1：影响检查 PR | 基于实际变更集合的文档义务检查 | API/架构/普通修复夹具分别正确触发；允许有依据的“无需文档变更”；Bash 与原生编辑路径均覆盖 |
| P1：长任务维护 PR | 活跃/稳定/历史分层；归档预览与恢复 | 同一活动任务加入 1、10、100 个历史任务，注入始终受同一预算约束；目标/限制/下一步不丢失；链接有效 |
| P1：交接验收 | 固定冷读问题与独立判定记录 | 无旧聊天的读者能回答关键恢复问题；历史 Passed 不被误报成本次重跑；缓存删除后仍可恢复 |
| P2：五宿主逐项验收后 | 可选 UI/研究文档 profile；已验证能力矩阵 | 每项声明关联宿主版本、scope、模式和证据；未运行仍 Not Run；不要求安装参考子模块 |

回归场景至少覆盖：简单任务、只读、禁止新文件、已有权威计划、legacy 根计划、命名计划选择拒绝、多任务并行、中文标题、长记录、已有用户 diff、禁用模式、卸载/更新保护。

若普通 Markdown/Skill 已能稳定通过某场景，不必为它增加独立服务、配置文件或命令。

## 8. 在当前仓库的修改落点

维护规范源，不手工编辑生成产物。[S5]

| 内容 | 优先修改位置 |
| --- | --- |
| 主工作流与渐进阅读入口 | `overlays/planweft/entrypoints/*.md`，配套 references/workflow 规范源 |
| 三文件记录约定 | `overlays/planweft/record_templates.py` 及实际模板规范源；保留 parser token |
| 宿主事件和协议 | `overlays/planweft/native/` 与既有适配路径 |
| 打包与规范源映射 | `scripts/build-plugin.py`，必要时新增的 helper 由此分发 |
| 需求、取舍与证据 | `docs/specs/`、`docs/adr/`、`docs/reproduction/`，沿用现有设计引用台账 |
| 验收与防回退 | `tests/`，补实际失败夹具及跨宿主协议契约 |
| 自动生成结果 | `dist/**`、`plugins/planweft/**`：只生成，不手改 |

现有文档列出的验证入口如下；这里仅引用，不代表本次已运行：

```bash
python3 scripts/build-plugin.py --verify
python3 -m unittest tests.test_public_docs
npm run check
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

## 9. 提供给本地 Agent 的开发交接

先核对本地提交与本报告快照的差异，读取当前 AGENTS、后继规格和现有计划；不要把本文建议自动认定为既有批准需求。沿用原有计划及 PWF 绑定，不创建竞争状态源。

首先为“代码已变但关联文档过期”和“长任务归档后新会话恢复失真”各准备一个最小失败夹具。比较 instruction-only 与只读 helper 两种路线，只实施能够解释真实失败的最小 P0 方案。将用户给定目录作为角色映射示例而非强制脚手架；修正 Codex 原生发现约定，保护已有布局与用户配置。

需要修改时只修改规范源，保留原始 PWF 基线、现有状态解析和已正式支持的五宿主核心行为。新增 Hooks 必须有覆盖必要性、禁用行为、去重和宿主协议测试；不因为某宿主提供事件就宣称新功能已验证。任何 promotion/归档写入先说明目标及授权，不删除唯一证据，不自动改批准规格。

交付分别报告：实际修改、执行过的验证、历史引用的验证、Not Run 和仍有的限制。先通过 P0 门槛，再决定 P1/P2 是否有足够问题证据。

## 来源

下列链接固定到核查提交；官方网页是核查日访问的文档。

[S1]: https://github.com/psiQAQ/planweft/blob/b05add2d172ae215a0c30db34720c84edbb153ae/README.md
[S2]: https://github.com/psiQAQ/planweft/blob/b05add2d172ae215a0c30db34720c84edbb153ae/vendor/planning-with-files/upstream.json
[S3]: https://github.com/psiQAQ/planweft/blob/b05add2d172ae215a0c30db34720c84edbb153ae/docs/reference/README.md
[S4]: https://github.com/psiQAQ/planweft/blob/b05add2d172ae215a0c30db34720c84edbb153ae/overlays/planweft/PATCHES.md
[S5]: https://github.com/psiQAQ/planweft/blob/b05add2d172ae215a0c30db34720c84edbb153ae/docs/development.md
[S6]: https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/skills/planning-with-files/SKILL.md
[S7]: https://github.com/psiQAQ/planweft/blob/b05add2d172ae215a0c30db34720c84edbb153ae/plugins/planweft/skills/project-docs/SKILL.md
[S8]: https://github.com/psiQAQ/planweft/blob/b05add2d172ae215a0c30db34720c84edbb153ae/plugins/planweft/hooks/codex-hooks.json
[S9]: https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/hooks/codex-hooks.json
[S10]: https://github.com/psiQAQ/planweft/blob/b05add2d172ae215a0c30db34720c84edbb153ae/dist/claude/planweft/hooks/hooks.json
[S11]: https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/hooks/hooks.json
[S12]: https://github.com/psiQAQ/planweft/blob/b05add2d172ae215a0c30db34720c84edbb153ae/docs/specs/0001-document-management.md
[S13]: https://github.com/psiQAQ/planweft/blob/b05add2d172ae215a0c30db34720c84edbb153ae/plugins/planweft/.codex/hooks/pre-tool-use.sh

[S14]: https://github.com/psiQAQ/planweft/blob/b05add2d172ae215a0c30db34720c84edbb153ae/scripts/build-plugin.py

[R1]: https://github.com/OthmanAdi/planning-with-files/blob/d47a61950e784fc4237ba10ddc1e9e198bd0f275/skills/planning-with-files/SKILL.md
[R2]: https://github.com/Fission-AI/OpenSpec/blob/e062b9572be933564ba3899d059377dfa1393e32/docs/concepts.md
[R3]: https://github.com/obra/superpowers/blob/b36e0829c6d0140e93cfef2ca599b1b07d4a7797/skills/writing-plans/SKILL.md
[R4]: https://github.com/rtoma/agent-markdown-memory-bank-protocol/blob/9c88d0f166070d8d55caa1e77c81e4bf0d67cd02/AGENTS.md
[R5]: https://github.com/vanzan01/cursor-memory-bank/blob/7d879d8f5079ad77d845fdc92ca03903dbbd3a85/README.md
[R6]: https://github.com/anthropics/skills/blob/41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f/skills/doc-coauthoring/SKILL.md
[R7]: https://github.com/github/spec-kit/blob/4a7341a93d944d6efe153b71da4a1adb9c2b578c/templates/spec-template.md
[R8]: https://github.com/google-labs-code/design.md/blob/9bf8eae67128b6cc55ad9bf86665767deb4c11cd/docs/spec.md
[R9]: https://github.com/google-labs-code/stitch-skills/blob/0337446dadde6f8c94210444e2aa9d546126480f/plugins/stitch-utilities/skills/design-md/SKILL.md
[R10]: https://github.com/dyoshikawa/rulesync/blob/ec15febdc845cd226fd14d80e6d72719c90ebaf6/README.md
[R11]: https://github.com/earendil-works/pi/blob/9767ba275f3e9a5ee0f5c5342249b629ab1b2282/packages/coding-agent/docs/extensions.md
[R12]: https://github.com/adr/madr/blob/ba75bb1b20d42af5746b246ad348c202419ae681/template/adr-template.md

[O1]: https://learn.chatgpt.com/docs/agent-configuration/agents-md
[O2]: https://learn.chatgpt.com/docs/build-skills
[O3]: https://learn.chatgpt.com/docs/hooks
