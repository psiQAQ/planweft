# REP-0005：PWF 底座移植与分层验证

日期：2026-09-08，Asia/Shanghai。0.2.0 已生成14个平台包。本记录区分源码/分发、协议、真实宿主与模型样本，不用一层的通过代替另一层。需求见 [SPEC-0003](../specs/0003-pwf-based-plugin.md)，决定见 [ADR-0006](../adr/0006-pwf-derived-runtime.md)，进度见 [PLAN-0005](../plans/0005-pwf-based-plugin.md)。

## 固定输入与环境

| 项目 | 实际值 |
| --- | --- |
| 上游 | PWF v3.17.0；提交 `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`；tree `990b7c3fae286292eac40c58ba9fd697c0f2fe1e` |
| 原始快照 | 699个tracked文件；归档SHA-256 `4175b623648517c1a0cbff782d789fe9f542cc638e5b12c38559bcf445cafb6a`；保留MIT和Ahmad Adi版权 |
| 研究子模块 | PWF 3.16.1 / `d47a61950e784fc4237ba10ddc1e9e198bd0f275`保持不变；构建不读取它 |
| 本机 | Ubuntu 26.04.1、Linux x86_64、Bash 5.3.9、系统Python 3.14.4、Node 22.22.1、npm 9.2.0 |
| 测试Python | 独立Python 3.12.14，pytest 9.1.1、PyYAML 6.0.3；独立XDG/npm缓存与Git index |
| 真实宿主 | 固定既有Docker镜像 `sha256:aa46e31c71577eb37c1e1d856427d9d159ddd5a41aa92472af722838b1c3a159` 内Codex CLI 0.149.1；模型 `gpt-5.6-terra` |
| 本机CLI盘点 | Codex 0.153.4；PATH未发现Claude、Pi、OpenCode、Hermes、Gemini、PowerShell；不是完整机器安装普查 |
| 当前分发manifest | SHA-256 `2b42c50f302eacffeb31a9d2794062ef24eb31e4dbb5ed0403b3cb6793650e4b`；每包摘要见 [manifest](../../dist/manifest.json)；安装补充前的 `6c3d6787…` 保留于历史宿主证据 |

来源在 [vendor](../../vendor/planning-with-files/upstream.json) 与逐文件inventory登记。命令、环境、原始失败、JUnit、模型完整轨迹及清理记录保存在[证据目录](evidence/0005/README.md)；重建/回归步骤见 [tests/README](../../tests/README.md)。

## 回归与分发

| 检查 | 结果 | 验证范围 |
| --- | --- | --- |
| 原始pytest | **Passed：721 passed、63 skipped、798 subtests** | 原始归档、不改断言；最终明确指定GNU mkdir环境 |
| 移植pytest | **Passed：721 passed、63 skipped、851 subtests** | 身份、workflow、模板及完整资产；增加的53个subtests来自新增共享副本枚举 |
| 最终Skill文本增量 | **Passed：30 tests、127 subtests** | GNU全量后18份Skill的状态承接句变化；定向frontmatter/引用合同 |
| Pi Vitest | **Passed：原始54、移植54** | 原生Extension逻辑；上游没有独立typecheck/build命令，不虚构该项通过 |
| OpenCode | **Passed：原始34、移植34，均typecheck/build通过** | 原生tools、上下文/压缩/idle逻辑；包内lock安装；最终19个Node源码文件SHA与已测试版本一致 |
| 本地unittest | **Passed：29** | 原有25项，加4个安装补充测试；最新日志见 installation，原local目录保留25项历史输出 |
| 既有独立入口合同 | **Passed：13/13** | CLI/main参数、副作用和handoff调度；假进程不代表模型 |
| 确定性构建 | **Passed** | 独立临时源码根两次重建全部输出一致；故意改生成Skill后verify返回1且不写文件；最终verify零差异 |
| 包/链接/许可 | **Passed：14 ZIP、89 Skill、547相对链接** | 独立review；standalone根有准确MIT/UPSTREAM，引用与必要资产齐全 |
| 身份与原生接口 | **Passed** | manifests、包/命令注册、OpenCode `pd_`、Windows编码launcher、catalog和fallback；旧身份仅保留在来源及只读重复安装诊断中 |

上游回归沿用 `.github/workflows/tests.yml` 的pytest、Pi、OpenCode三条CI线路。原始快照中的历史辅助材料仍保留；内联旧hook示例的 `test_clear_recovery.sh` 不作为当前运行时证据。63个跳过主要为PowerShell/Windows行为，逐项原因保存在JUnit/summary，不算通过。

最终源码的924文件SHA清单、所有回归轮次及Node一致性对照见[回归归档](evidence/0005/regression/README.md)。没有把某个失败轮次的总体退出码改写成成功。

本机已安装的旧 `plugin-creator/validate_plugin.py` 实跑为 **Failed**：拒绝manifest的 `hooks` 字段，并把 `skills/i18n` 容器误当作缺少SKILL.md的直接Skill。输出保存在local证据。这两项与当前官方/宿主契约不同：[Codex hooks文档](https://learn.chatgpt.com/docs/hooks) 支持插件hooks，真实CLI已成功安装、发现7类hooks并送达上下文；同一CLI的skills/list实际递归发现主入口及5个语言变体且errors为空。保留原布局，不修改已安装系统Skill；仓库契约与实际加载分别补充验证。

## 并发失败与工具环境限制

原生工具环境偶发 `test_concurrent_distinct_phase_updates_are_not_lost`：两个writer都返回0，但只保留一个完成状态。各20轮对照中，沙箱内原始/移植各失败3次，沙箱外原始失败9次、移植失败2次。Shell trace及失败文件保留，stdout正常、stderr为空，未观察到mv错误。原始锁脚本经纯身份映射后与移植逐字节相同。

缩小到两个进程同时创建同一不存在目录、期间不删除目录的100轮探针：首个最小实验有11轮双成功；随后用交付的可重复探针运行，本机uutils coreutils 0.8.0有16轮双成功，已有GNU `gnumkdir` 9.7为0/100。GNU环境下，原始/移植PWF并发用例各20轮均通过。这支持具体根因：mkdir的失败语义没有维护目录锁互斥。[uutils 0.8.0源码](https://github.com/uutils/coreutils/blob/0.8.0/src/uu/mkdir/src/mkdir.rs) 中先检查存在性、再将创建错误后“路径已为目录”视作成功的分支，与竞争观察一致。

未重写PWF锁或替换系统程序。回归器新增显式 `--tool-path`，记录实际工具路径/版本/SHA；最终两套pytest在GNU mkdir下均通过。**uutils mkdir 0.8.0不能用于可靠并发计划写入**，应使用已验证的GNU工具环境并遵守单一owner；安装包也披露此限制。最小复现脚本与原始数据随归档交付。

## 运行时合同与平台矩阵

| 合同 | 结果及证据层级 |
| --- | --- |
| 所属计划与会话 | Passed：resolver、错误selector/歧义拒绝、nested root、Codex session isolation、根/命名计划及计划锁回归；工具并发例外见上节 |
| 提醒与自动化 | Passed：post-tool去重、attestation、gate、停滞/续跑上限、不执行Markdown命令、自动恢复不读历史；真实脚本与原生TS回归 |
| 路径与解释器 | Passed：ZIP中文/空格安装与工作路径、CRLF/line-ending、Windows launcher静态解码、Python同名模块/PYTHONPATH隔离；Windows执行Not Run |
| 只读与缓存 | Passed：禁用后实际脚本无注入/项目修改，Gemini/Mastra九个入口；独立XDG私有缓存及上游snapshot/缓存链接保护另验。不能自动识别所有自然语言只读请求 |
| 重复安装 | Passed：doctor识别预置旧PWF目录，明确“不证明激活”；含可观察副作用的旧脚本未执行，不自动卸载 |

| 分发 | 静态 / 协议结果 | 真实宿主结果 |
| --- | --- | --- |
| Codex | Passed：独立manifest、7类事件、Windows launcher、选择/恢复/停止/只读/会话合同 | **Passed：Linux隔离安装、自动Skill读取、上下文送达、新会话恢复、advisory正常结束、卸载**；独立Stop完成通知未观测，真实gated循环及Windows/macOS Not Run |
| Claude Code | Passed：plugin/standalone dispatcher、Python快速路径/Shell fallback、事件与注入合同 | Not Run：无宿主；重复加载配置审查不能替代真实事件验证 |
| Pi | Passed：package/注册/引用及54个Extension测试 | Not Run：无宿主；命令、状态栏和显式激活未做真实交互 |
| OpenCode | Passed：34项、typecheck/build、tools和自包含源码包 | Not Run：无宿主；按lock本地源码构建，不宣称已预编译发布 |
| Hermes | Passed：原生Python/bridge/注册、合法包内fallback、禁用/注入/验证回合合同 | Not Run：无宿主 |
| Cursor | Passed：配置、Shell注入/关闭/nested-root；PowerShell静态检查 | Not Run：无宿主/PowerShell；部分路径仍为root-plan适配 |
| Gemini | Passed：设置/资产、Shell JSON输出与5个禁用入口 | Not Run：无宿主，不提供canonical named-plan等价保证 |
| Copilot | Passed：配置、Shell停止/注入/禁用/解释器合同 | Not Run：CLI/IDE/Coding Agent未实测，PowerShell亦Not Run |
| Mastra Code | Passed：Skill/资产、4个实际hook禁用命令 | Not Run：无宿主；旧root-file提醒能力 |
| Kiro | Passed：Skill/原生assets/安装映射静态检查 | Not Run：无宿主；原生`.kiro/plan`与steering，不是canonical多计划hooks |
| Continue | Passed：Skill/引用、`pd-plan.prompt`及只读前置静态检查 | Not Run：无宿主；无执行hooks |
| Factory | Passed：Skill/脚本/引用/许可/安装表面静态检查 | Not Run：无宿主，无独立原生执行hook配置 |
| CodeBuddy | Passed：Skill/脚本/引用/许可/安装表面静态检查 | Not Run：无宿主，无独立原生执行hook配置 |
| 通用Agents | Passed：发现路径及独立复制资产静态检查 | Not Run：不保证所有Agent支持该发现表面 |

Linux执行结果如上；Windows/macOS真实OS与宿主测试均 **Not Run**，没有对应环境。BSD模拟、Windows路径/编码静态检查不升级为真实OS通过。各安装步骤及激活差异见[平台说明](../platforms.md)。

## 真实Codex与文档行为

每次新tmpfs HOME、临时项目、独立ephemeral会话，无个人配置/历史挂载；认证只读单文件挂入后复制到容器临时内存目录，不纳入输出。只读根、2 CPU/4GB、drop capabilities；使用宿主网络/现有代理，不宣称网络隔离。每次已审信任前逐文件比对cache；个人hook trust不变。

| 场景 | 实际结果 |
| --- | --- |
| 独立ZIP安装 | Passed：本地catalog注册/安装0.2.0，cache逐文件一致，卸载后本插件cache清空 |
| hooks信任 | Passed：同次hooks/list显示7条untrusted，普通模型调用无上下文。首轮因CLI JSONL无显式skip事件保留自动Failed；补实际trust列表后定向通过 |
| 上下文与恢复 | Passed：一次性已审信任后，无工具调用精确返回仅存在plan中的随机token；另一个新会话恢复同一字段。untrusted对照只答NO_CONTEXT，项目均未改 |
| 自动匹配与维护 | Passed，第三轮：prompt/AGENTS不含Skill名或启用语句，实际从cache读主Skill；复现BOM、最小修复、1项字节回归及独立4类字节检查通过；指南、批准需求、用户dirty正确处理 |
| 单一任务状态 | Passed，第三轮：唯一`.planning/2026-09-08-utf-8-bom`含三文件；旧notes只留相对指针/历史，新plan含目标、阶段、下一步、Windows阻塞及证据，非空模板 |
| 简单请求 | Passed：只答42，无工具、无项目变化 |
| 只读请求 | Passed：启动时PLANNING_DISABLED=1，核对需求/缺失Windows证据，无修改或项目测试 |
| 批准需求冲突 | Passed：识别无BOM需求与utf-8-sig实现/弱测试的冲突，拒绝迁就实现改需求，无文件变化 |
| 证据不足 | 核心语义符合：明确SHA/锁只是候选、来源和实验不足，没有编造联网检索或已采纳结论。自动检查 **Failed**：最终答案未列具体文件名，引用可定位性不足；保留限制，不重采样变绿 |
| 独立冷读 | **Passed，第三轮**：无插件/旧聊天/源包/期望答案，从项目文件恢复需求、实际实现/测试、新状态入口、Windows下一步及限制，项目不变。首轮有越界行号及前态推断问题，保留原样本 |

前两轮虽修复代码，却只更新旧计划，PWF三文件采用验收 **Failed**。首轮提示过度禁止环境变量读取，会阻止合法resolver；澄清只禁止凭据/完整环境后仍不采用，说明有工作流歧义。最终规则明确：复杂已授权维护应用本Skill即本次采用、不另需opt-in；保留用户/项目禁止及只读/simple例外。独立review再要求先承接状态再改旧入口。

第三轮模型包与安装补充前交付包的完整SHA/delta保存在[宿主证据](evidence/0005/host/README.md)。当时Codex ZIP为 `4fa81f93c4b6dfdc839f0ad34731afdab0d9a37f6a27056a76c76f64f5c91044`；相对第三轮改变6份Skill的状态承接句、INSTALL环境说明，并新增5份语言变体原生policy，共12条路径。运行时与plugin manifest字节及已有文件权限不变。样本产物已承接状态，新plan和旧指针位于同一成功file_change；trace不能证明patch内部逐文件时序。当时包另做无模型安装预检与全部本地检查，不冒称用最终逐字节包又跑了模型。当前包另含下节安装修复，其证据单独追加。

真实skills/list确认Codex会递归发现5个语言变体，仅保留Claude的 `disable-model-invocation` 不足以支持Codex策略声明。最终为这5项加入 `agents/openai.yaml` 的 `allow_implicit_invocation: false`，主入口为true，依据[官方Skill元数据](https://learn.chatgpt.com/zh-Hans/docs/build-skills)。实际cache已逐字节核对这6份policy；skills/list的enabled表示启用，CLI0.149.1的SkillMetadata schema不暴露implicit/policy字段。因此验证范围是原生配置安装、无错误发现及配置合同，**没有将该API结果描述为隐式禁用行为的直接观测**。补充预检归档保留改前/改后schema、列表和精确包，原501成员归档不覆盖。

Docker临时目录默认noexec：直接执行有100775权限的resolver曾返回126，bash重试成功。源包与cache执行位相同，不能归因CLI丢权限。错误、重试与环境证明均保留。

所有真实任务正常结束并清理，但CLI JSON不提供可独立观察的Stop hook完成通知；不能用退出码证明该事件已交付。真实gated循环Not Run，停止/上限/停滞机制的证据来自离线协议和原生TS测试。

独立依据审查见 [REV-0005](../reviews/0005-pwf-migration-review.md)：原9项中8个实现问题关闭，root-only差异明确披露；新增状态承接问题亦关闭。维护样本内没有独立Agent（实验禁用多Agent），控制器另启无插件读者；不把样本计划内Not Run改写成模型自动完成审查。

[独立交付审查](../reviews/0005-delivery-review.md)另行核对规格/ADR、当前924文件移植树、14ZIP、回归/宿主归档、第三轮轨迹及最终差异，未发现新的阻断项。语言策略最终预检见[单独附录](evidence/0005/host/skill-discovery-README.md)，共71成员；原501成员宿主归档与231成员回归归档保持完整。

## 交付与限制

交付固定来源、补丁清单、构建/测试入口、Codex目录及14 ZIP、升级/安装说明、矩阵与完整证据。未公开发布、推送、个人全局安装或正式自身接管；原入口、研究gitlink及历史保持。

真实宿主仅Linux Codex；其他宿主、Windows/macOS与真实gated续跑Not Run。uutils并发限制、证据不足样本的引用缺口和少量模型引用/解释误差保留。少量样本不能推出普遍触发率、收益或正确性保证；阶段完成、attestation、gate不等于人工批准或需求正确性。

## 提交整理时的安装补充

用户要求说明 PWF 根隐藏目录与本仓库 `dist` 的区别，并补齐各宿主安装路径。保留 ADR-0006 的生成分发结构，README 新增14平台选包表，仓库及包内安装说明补解压、目标目录、激活与卸载步骤。独立审查还发现继承说明中的虚构发布源及 Gemini 启动错误，已在构建源修复（PD-P09/10）。[独立安装审查](../reviews/0005-installation-review.md) 与[本次证据](evidence/0005/installation/README.md)记录范围和失败。

- **Passed**：全部29项本地测试；原始及当前移植树各13项定向 Skill/frontmatter/版本/发现表面测试；确定性构建零差异。
- **Passed**：14包无虚构发布式安装入口，原生安装资产完整；OpenCode分发loader指向本地锁文件构建的dist。Gemini的5条实际配置命令在中文与空格路径以原ZIP `0664`权限成功执行，关闭输出为`{}`，项目及私有缓存不变。此前未加引号时5次127、仅加引号时5次126均如实记录。
- **Passed**：当前精确Codex ZIP在既有固定镜像内重新完成无认证、无模型安装预检，cache逐文件一致，卸载与容器清理成功。当前ZIP SHA-256为 `d0ca7189f34676d32e76a77159261c6e6af9e8d4cce1839800dc2a85ec759d2c`；相对此前精确包只改`INSTALL.md`和主Skill内的安装方式表，运行时、manifest、policy与权限不变。
- **Not Run**：本次没有重跑全量pytest、Node编译/测试或模型维护样本。与已验证924文件移植树相比，仅7个源路径变化（6份Markdown和Gemini settings）；Node运行源码/锁文件不变。OpenCode新分发loader只做静态输出契约，真实OpenCode/Gemini宿主及Windows/macOS仍未验证。

提交时另加入`.gitattributes`，让普通文本保持LF、Windows `.cmd`/`.bat`保留原CRLF，避免Git默认空白检查误报CR和跨客户端换行转换。原始证据关闭文本转换及空白告警，保留unittest失败输出实际携带的行尾空格和原始摘要；没有重写证据、上游归档或系统配置。
