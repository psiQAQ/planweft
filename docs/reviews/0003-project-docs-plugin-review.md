# REV-0003：首版插件设计与依据审查

状态：**Passed（设计依据与所列实施证据 review）**。日期：2026-09-07。独立 reviewer：`plugin_evidence_review` subagent。基线：`4041f46`，审查对象为该基线上的未提交工作区；没有以基线 commit 冒充新增文件版本。

## 范围和方法

直接读取插件全部五个文件、repo marketplace、SPEC-0002、ADR-0005、R-12/R-21，以及相关既有 ADR、导航和创新记录。打开官方原文，读取 P-03/P-04/P-06 的实际固定文件，并比较 checkout 与 Git index 的 gitlink。第三方 Skill 仅为研究材料，没有执行其流程。

首次审查时，主 Agent 仍在完善引用台账和运行测试；当时先审设计，安装、模型行为、清理和最终引用覆盖留待实际证据。下文按轮次保留审查过程，最终状态以末节为准。没有使用主 Agent 的预期答案替代观察。

## 来源存在与设计支持

| 来源及实际定位 | 来源存在 | 支持范围与本地差异 |
| --- | --- | --- |
| [R-21 官方原文](https://developers.openai.com/plugins/build/plugins)，Create a plugin manually、Install a local plugin manually、Marketplace metadata、How local marketplaces work | 已打开正文 | 支持单 Skill 包装、根目录相对 source.path、注册与缓存副本分离；不证明本插件已安装或加载 |
| [R-12 官方原文](https://learn.chatgpt.com/docs/build-skills)，Optional metadata、Best practices | 已打开正文 | 支持默认允许隐式匹配、指令优先及触发测试。项目 opt-in 是用户要求的 Skill 判断约定，并非宿主强制权限 |
| [P-03 concepts](../../.submodule/Fission-AI/OpenSpec/docs/concepts.md)，Keep It Lightweight: Progressive Rigor | checkout/gitlink 均为 `e062b9572be933564ba3899d059377dfa1393e32` | 支持最轻可验证规格；不要求引入 OpenSpec 引擎或固定所有目录 |
| [P-04 manifest](../../.submodule/obra/superpowers/.codex-plugin/plugin.json)、[writing-plans](../../.submodule/obra/superpowers/skills/writing-plans/SKILL.md)，Overview、Plan Document Header | checkout/gitlink 均为 `b36e0829c6d0140e93cfef2ca599b1b07d4a7797` | 有真实 Skills 分发和自包含计划先例；本地未照搬强制子流程、TDD 或目录结构 |
| [P-06 doc-coauthoring](../../.submodule/anthropics/skills/skills/doc-coauthoring/SKILL.md)，Stage 3: Reader Testing | checkout/gitlink 均为 `41bbe19d1a1a7eaab5e7bb9050a417e5c6cffc8f` | 支持无历史读者提问、核查和修订；并非现成的来源审计器，专职依据 reviewer 来自用户需求 |

R-12/R-21 中文文件为简短要点摘要，保留作者、访问日期、原文、许可未确认及本地解读边界，没有声称取得全文翻译许可。P-04 虽有其他组件字段，本版采用官方最小包装，不据上游 manifest 推导不必要能力。

## 设计发现与处理

| 核查点 | 结果 |
| --- | --- |
| 安装、项目启用和当前任务调用混淆 | 正文明确区分三者，README 及引用资料不是启用；显式调用不越过项目禁止或授权范围。没有新增自动改 AGENTS 的机制 |
| 工作流超出请求、只读任务写入 | 入口先限制请求范围，再维护相关文档；无关任务不启动文档管理。是否遵守需行为测试，文本本身不是运行保证 |
| 包依赖研究仓库 | Skill 唯一相对引用指向包内 evidence.md；没有脚本、研究库绝对路径或子模块运行依赖。README 中 REP-0003 为开发结果导航，不是 Skill 运行依赖 |
| 擅自改变原决定 | ADR-0004 明确允许用户新需求重开，ADR-0005 说明替代范围并保留旧实验；专用引擎仍暂缓，Windows 与迁移未冒称通过 |
| 自身迁移提前发生 | 根 AGENTS 仅更换计划入口，没有启用声明；ADR-0005 与 SPEC-0002 保留独立迁移门槛 |
| 新机制无先例却宣称原创 | 本版为既有 Markdown/Skill 与用户要求组合，没有新状态协议或写回引擎；创新记录为空合理 |
| 更简单方式 | ADR 比较继续手工描述、单 Skill、专用工具；单 Skill 满足用户明确要求的可安装复用，不需为首版增加脚本 |
| marketplace 名称 personal | 与既有 catalog 可能重名；README 已提示先核查来源。临时安装验证需隔离注册与缓存，不应操作用户已有同名 catalog。保留为使用限制，无设计阻断 |

首次设计审查没有发现需修改插件设计的阻断项；当时引用台账和运行结果尚待核查，仅此阶段不足以判定整体 Passed。后续回查结论见末节。

## 审查快照 SHA-256

以下为首次设计审查时实际读取的文件字节；最终若内容有实质变化，仅重审受影响部分。

| 文件 | SHA-256 |
| --- | --- |
| `plugins/program-design/.codex-plugin/plugin.json` | `32b4e04e26e0262eca50e6823c22f49a061285f8fb3497d29dc66a34597d72c9` |
| `.agents/plugins/marketplace.json` | `5969d4408f83cf5fafb9ecbf153b45daaf3b8887280df3b6f8092eb0d94a2243` |
| `plugins/program-design/README.md` | `96afaa7b454c892b73963c41989b5d9c5e948f90e09d93dbda5896fcd1bea44e` |
| `plugins/program-design/skills/project-docs/SKILL.md` | `4c1700c75673811b01b3f3943311a5afacbe02250eb3fe4620d943437b84ebd9` |
| `plugins/program-design/skills/project-docs/agents/openai.yaml` | `267c6efff9a2cd2543ea7d26db5c81b1c45d8645e790666b56bc62ea0f811565` |
| `plugins/program-design/skills/project-docs/references/evidence.md` | `f714a1fcb351eed748fbe160cc30b2ed8a614269b745bf20fdc2c68b60bb6a70` |
| `docs/specs/0002-project-docs-plugin.md` | `bf82602e13ae54239ce81565eca22718d3770d7b5848044a045a4bb60b172de6` |
| `docs/adr/0005-skill-first-plugin.md` | `3d853448bac1e52fb8d0dfeb8c03695b6b62faba5356acef3aadffe8e3562dc6` |
| `docs/reference/codex-skills.md` | `318ec57e158264ac9fef1720d5b271dbff7f415f2c19b2cbcfe23b4a7da42f60` |
| `docs/reference/codex-plugins.md` | `cfd9fe27428141a1ae2c245c9af11e8c6ccfbac0ca3fff2cf7c92e59d1908654` |

## 首次审查时的实施验证边界

- 本 reviewer 不负责亲自运行插件校验器、安装或模型行为测试；首次审查尚未回查运行证据，不将官方来源存在记为实现 Passed。
- 当时引用台账逐文件覆盖、测试输出与结论、缓存/容器清理等待主 Agent 提供证据，已在后续轮次回查。
- Windows 原生运行、本仓库正式自身接管：当前 Not Run；Linux 容器不能替代这两项。

## 第二次检查：引用覆盖与实验工具

主 Agent 补入本轮引用台账后，reviewer 逐项核对插件、metadata、规格/ADR、导航、测试工具和资料摘要的来源映射。P-04 `Execution Handoff`、P-12 `More Information` / `Confirmation` 及 R-18 `Filling in information` 的位置存在；用户需求与本地实验安排没有伪装成外部标准。生成证据关联脚本及实际调用，避免为每份快照虚构设计依据。

实验脚本使用临时分发副本、逐案例独立工作区、tmpfs 个人目录；原始输入、文件 before/after、CLI 输出和分发 SHA 分开保存。新容器执行交接，没有共享旧聊天；未启用、无关任务、只读、冲突、空项目、缺失依据为可判定的有限样例，不是准确率 benchmark。脚本没有机械语义打分，末尾断言只检查执行与清理；主 Agent 必须人工核对实际结果。

| 发现或限制 | 第二次审查时的处理状态 |
| --- | --- |
| 首轮没有 Docker `-i`；第二轮使用 `--ignore-user-config`，安装记录不能证明 Skill 加载 | 主 Agent 说明环境失败并修正；reviewer 已在当前脚本确认 `-i` 存在且不再忽略临时 config。旧轮不能计入插件行为 Passed |
| 将所有远程内置插件缓存当本插件残留 | 当前代码只检查 personal/program-design 并重新 list，范围正确；其他内置插件不属于本轮卸载目标 |
| 环境文件保存分发 SHA，未单列测试脚本 SHA | 本报告追加脚本内容 SHA；当时复现文档仍需记录精确执行命令，收尾时已补入。测试通过不能仅从最终源码推断 |
| `set -e` 使模型运行失败时不继续打印 lifecycle 汇总 | stdout/stderr 和失败结果仍保存，容器最终移除；缺少 lifecycle 的失败案例不能声称安装或卸载步骤均通过 |
| 模型正文声称使用 Skill 不足以证明加载 | 正例须检查工具轨迹实际读取已安装 cache 中的 SKILL.md；文件变化与最终回答另作语义核对 |

第三轮已结束的 `unenabled` 与 `unrelated` 原始输出已抽查：前者只改 README，后者回答 42 且无文件改动；两者安装列表中含启用的 0.1.0，卸载后本插件缓存无文件。第二次审查时其余案例与最终清理尚在运行，整轮结论留待后文实际回查。

第二次检查文件 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `tests/run-plugin-smoke.py` | `734e2478a28f95a3899d1f149d4d02b12ba5729aaa7379792ddaeb69372b2dd9` |
| `docs/design-references.md` | `e2ee7123d9cdad844c19971432ca1cc0e87e81e1a7eb731cda71eefc3077e4f5` |

## 第三次检查：实际运行与语义核对

直接读取入库 run-03 的原始 prompt、before/after、CLI 工具输出、最终回答、lifecycle 和 cleanup，不只依赖 mechanical-summary。对读取输出与当前 SKILL.md 字节进行核对，分发 SHA 与首次设计快照一致。

| 场景 | 独立核查结果 |
| --- | --- |
| enabled | 实际读到已安装缓存 Skill；只改 guide/work 两文件，保留原目录、约定、历史和 user-note 中未提交追加内容。计划准确写入本轮 Not Run、依据与 Windows 下一步 |
| unenabled / unrelated | 前者仅改标题，后者回答 42 且无文件变化；没有 Skill 读取记录，符合负例预期 |
| readonly / conflict | 实际读取缓存 Skill，需求与所有项目文件字节不变；准确区分 Windows 待办、历史 Linux 观察与当前未验证状态 |
| blank | 实际输出含完整已安装 SKILL.md；仅建一份规格，需求、验收和接续信息充分，没有永久启用或新增多余模板 |
| evidence-gap | 实际读取缓存 Skill，仅在现有计划记录候选、无依据、阻塞和下一步；无联网或机制实现。Not Run 指候选机制研究/运行验证，实际执行过 git diff --check 等文档差异检查 |
| handoff | 独立新容器回答所引文件确实支持目标、已完成和下一步，正确区分历史 Passed 与当前 Not Run；没有文件变化 |
| repo-copy | 第三轮未带实现源码和原 Git 历史，读者报告限制有依据；该输入不满足副本验收。主 Agent 修正夹具后定向复测，不能计该轮通过 |

每项 lifecycle 有安装的 program-design@personal 0.1.0、enabled=true，之后 installed 列表为空，本插件缓存无文件，marketplace removal 返回结果。依据限定为 CLI 返回和脚本观察，不声称桌面 UI 或 Windows 已测。

第三轮 cleanup 原始记录：本轮容器列表为空、原容器保留、镜像不变、临时目录删除。reviewer 检查了产生这些字段的脚本及实际记录，未另行访问 Docker socket；最终额外实验资源清理由主 Agent 收尾确认。

### 审查中发现与纠正

reviewer 初次按 `exit_code == 0` 筛选读取命令，误判 blank 没有加载正文。主 Agent 指出其复合命令先 sed 读取 Skill，后 rg 在空项目未找到 AGENTS 而退出 1。reviewer 回读 `item.completed` 的 `status=failed` 事件，确认 aggregated_output 包含当前 SKILL.md 完整内容，撤回该发现。该命令整体失败不否认前段真实读取，不能用单一退出码替代内容证据；无需为该误判重跑模型。

现有八项语义结论在有限样例范围内成立，没有观察到需改 Skill 的实质问题。内部自动委派、联网搜索、Windows、自身正式接管等未覆盖项继续 Not Run。

## 最终定向回查与结论

第四轮 run-04 的实际 prompt 明确副本含第一方文本源码，但不含原 Git 历史、研究子模块和历史原始实验输出；快照确实包含 manifest、marketplace、Skill 及测试脚本。读者实际工具输出含完整缓存 Skill，before/after 相同；回答识别交付文件、收尾中状态、Not Run 项和下一步，没有把快照省略内容当原仓库缺陷。该轮生命周期和清理记录均符合预期。

run-04 environment 中 runner SHA-256 为 `0283f1b6588bb710e45b91bb1163315dc54386e47ba1e0a3ed37c96c786002ef`，reviewer 与当前 tests/run-plugin-smoke.py 字节复核一致；插件分发 SHA 与首次审查相同。第三轮脚本旧快照的 SHA 留在前文，不能混同两个版本。

定向读者拿到的是收尾前快照，因此“尚未收尾、定向结果待回填”与其输入一致。后续主 Agent 更新状态和证据链接不等于最终 commit 又经过一次冷读；本报告没有作此额外保证。读者将“八个场景和 handoff”并列的措辞略有计数含混；实际有效场景是第三轮七个任务样例加一次 handoff，共八项，另加第四轮 repo-copy，结论按保存的 case 列表判定。

独立 review 无剩余阻断项：来源实际存在、借鉴范围成立、逐文件依据覆盖成立；第三轮八项与第四轮副本案例的实际结果支持 REP-0003 相应有限结论。静态 validator 和最终宿主清理仍以主 Agent 执行记录为证据，本 reviewer 没有另行运行它们。Windows、桌面 UI、联网先例检索、插件内自动 reviewer、多模型、自身迁移等未运行项保持原限制，不因为本报告 Passed 而转为已验证。

主 Agent 最终收尾报告：本轮标签容器为空，原有 10 个容器 ID 和镜像 ID 保持不变；4 个宿主临时结果目录已归档后删除。此项为主 Agent 的最终执行证据补充，reviewer 未再次运行容器检查；没有扩展前述语义结论。
