# REP-0010：五 Agent 容器验收与公开发布

状态：实施与验证进行中，尚未发布稳定版；本文件区分已观察结果和待完成项。

## 公开 RC1 与后续修复

准确发布归档版本 `0.4.0-rc.1`，SHA-256 `d72ef1e786f8aa0c63041026e716ac19f527d083f51e0b4d80624fba97c1dfdf`，来自干净提交 `1300f471a2c7f6382621293e4f901d14c062b714`。真实 npm 下载逐字一致。`next` 已发布；首次发布还自动产生 `latest`，两次不同 npm 版本的删除操作在额外认证完成后均返回 HTTP 400，尚未更正。这不是稳定版验收通过。

GitHub trusted publisher 已配置：仓库 `psiQAQ/planweft`、工作流 `publish.yml`、环境 `release`，环境分支规则仅 `master`。管理使用 npm 11.19.1 及当前 API 必需的 publish 权限；发布构建仍固定 Node 24/npm 11.11.0。OIDC 实际候选发布待验证。

| RC1 场景 | 观察与边界 |
| --- | --- |
| 五平台准确包预检/幂等生命周期 | Passed；保留基线容器 ID，无缺失。DSH 当时只验证 composed 配置，不能代替实际启动 |
| Pi 模型 | context Failed：原生注入含随机码但模型回答 NO_CONTEXT；recovery、cold-reader、readonly、skill-loading Passed。maintenance 原断言把标题格式当作历史丢失，独立审查及[显式重判](evidence/0010/pi-maintenance-reassessment.json)确认事实原字节保留；不是模型重跑 |
| Claude 模型 | context、recovery、maintenance、cold-reader、readonly、skill-loading Passed；独立维护/冷读审查通过。冷读自称“未执行命令”不准确，实际执行只读命令，未修改项目或重跑测试 |
| OpenCode 模型 | context、recovery、cold-reader、readonly、skill-loading Passed；maintenance Failed：修复代码与测试，但没有初始化唯一 PWF 计划 |
| DSH 模型 | 六项 Failed，实际启动暴露缺少日志目录及 bare import 解析失败；没有模型事件，不算完成模型调用 |
| 真实 npm 幂等安装 | Codex、Claude、Pi Passed；OpenCode Failed：同版本 npm 插件阻止独立 Skill 配对。DSH 仅配置检查成功，真实启动失败已更正，不能算运行时通过 |
| 本地 A/B fixtures | Passed：实际新增、修改、删除及更新/回退/卸载，项目文档保留；fixture 重打包不冒充准确发布归档 |

以上准确 RC1 运行、失败及工具版本另存[公开 RC1 附件](evidence/0010/rc1-published-trials.tar.gz)，1,036 项，SHA-256 `16cde8ce1503efe0dc8b6c430ce673f6387b27a6cc60e3868e85a08444791558`。随后结束的 [OpenCode RC1 模型组](evidence/0010/opencode-rc1-model.tar.gz) 单独保存 214 项，SHA-256 `9c7c9b6ff7c8117c16fcfb617c9dc4a6e82d1664d11861bf75aab2c9432f6517`。远端组挂载当时脚本且分宿主启动，DSH 新增实际启动检查没有倒算到旧运行。日志不含私有认证值；完整项目快照是合成数据。当前 RC2 回归为 Python 66 项、Node 28 项 Passed；后续修改另行复验。

RC2 修复在独立分支：DSH patch 使用宿主原生的相对 `./index.mjs` 定位、运行器配置真实日志目录并检查实际 boot；OpenCode 允许同版本 npm 插件配对 Skill，但仍拒绝完整重复安装和版本不匹配；无计划时通过已有 chat.message 提醒授权复杂任务先读取主 Skill，明确简单、只读、诊断与规划模式不初始化。上游状态格式保持不变。

## 早期候选观察（非公开 RC1 准确归档）

- Passed：公开历史脱敏及独立审查，27 对提交只有八个证据 blobs 变化；已用明确 lease 更新公开 master，原 bundle 离线保留。
- Passed：准确候选包 SHA-256 `c3d7191c6f4a0775b0fbc660536d3d911feba5d0ba0d274472f3338e832c9bdd` 从脱敏后的干净源码重新打包，字节与前次归档一致。
- Passed：五宿主加强后的准确归档安装预检和同版本更新、卸载、重装均通过；含完整 npm/平台内容与原生注册检查。这是幂等生命周期，不是远端两版本升级。
- Passed：Codex 与 OpenCode 的真实模型算术冒烟；Claude 修正原生 API base URL 后，实际上下文注入和新会话文件读取通过。
- Failed（保留）：第一轮 Python 3.11 不支持 tar extraction filter；已补安全成员校验兼容。Claude 直连 base URL 多带 `/v1`；已修正。
- Failed（保留）：Pi 的字面环境变量名导致 401，宿主仍返回 exit 0；早期控制器曾错误标记进程成功，该结果不计为模型 Passed。已改用 `$PLANWEFT_MODEL_KEY`、检测原生错误事件，并加入回归。
- Passed：本地安装器 27 项测试；Python 65 项测试，最后边界修订后相关 9 项再次通过。
- Failed（保留）：GitHub 首轮 Windows CI 的故障注入使用硬编码 `/`，未触发预期错误；已修复为 `path.join`，修复后的 Linux、Windows、macOS 安装器及分发 CI 均 Passed，见 [34242500572](https://github.com/psiQAQ/planweft/actions/runs/34242500572)。

- Passed：Codex 维护、冷读、只读与 Skill 读取的自动断言；独立 reviewer 核查维护与冷读语义 Passed。冷读输入快照等于维护输出，未携带旧聊天或插件。
- 未证实：该 Codex 组旧控制器的 `original_containers_preserved=false`，旧总状态仍写 Passed；初始集合混入并发测试容器且未保存 ID，不能追溯证明服务基线保持。维护/冷读语义仍成立，整组隔离验收不计通过。控制器已排除带验证 label 的容器、保存基线与缺失 ID，并将缺失纳入失败条件。五宿主预检组的该项为 true。

证据附件：[脱敏运行附件](evidence/0010/container-trials.tar.gz)，SHA-256 `24ba7e3ffa9c863189f6f5558ed7e9c3868909343e45050d9817e61e854ab98a`。包含 799 个有原始/公开摘要映射的日志与快照；已检查既有认证值无命中。保留失败和旧控制器的原始结果，以上更正优先于其早期总状态。各 summary 的 runner/runtime 摘要属于当次执行，后续源码修订不冒充重跑；附件也不是最终稳定包的 acceptance。

## 固定条件与边界

镜像完整摘要见 `tests/container-images.json`；原镜像保持不变。DSH 派生镜像复制此前验证过的 DSH 0.1.2-rc.1 / pnpm 10.28.2 依赖树，不含认证或用户配置。初次联网构建无进展，改用该可审计的已有本地依赖；不宣称完成了在线重建验证。

模型通信直接访问现有官方 provider；不经过 MemoryProxy、不附加 Lab 身份头、不读写外部记忆、不运行旧清记忆脚本。认证只进临时容器；日志写入前脱敏已知凭据，发现命中则标 Failed 并要求安全复核。

Pi 的全计划内容探针显式采用 parity 模式并通过原生命令激活；DeepSeek 默认 cache-safe 仅提醒读取文件，不宣称默认注入完整计划。Codex 自动化维护场景的单次 trust bypass 不计正常信任；另一次原生 TUI 探针观察到 7 hooks 从未信任/未激活变为激活，随后无 bypass 的新 exec 无工具读出项目随机码。该探针使用隔离容器内 danger-full-access，不能据此声称验证了全部工具权限策略。DSH 使用本次临时会话的原生 JSONL 日志判断工具调用和停止；该采集实现尚待真实模型验证。

## 尚未完成

- RC2 OpenCode 与 Pi 复验结果见下；RC3 DSH 准确包模型复验待完成。
- npm latest 标签删除失败；OIDC RC2 发布已完成，稳定门槛待完成。
- 五宿主最终准确归档的维护、冷读、正常信任、停止限制及语义审查尚未全部通过。
- 远端真实两版本生命周期、Git marketplace、新会话加载、稳定提升与 GitHub Release 均待完成。
- Windows/macOS 真实宿主仍为 Not Run；CI 不替代真实宿主。

RC2 修改了本地运行时 overlays；PWF 固定源码与状态协议未改。OpenCode 当前原始对照 34 项 Passed，原生未调整测试 32 Passed/2 Failed（两项有意的协议差异），显式适配断言并加入本地边界测试后 37 项 Passed；不删除原始失败日志。此前其他上游证据仍属历史定位。

对外说明：[发布：中文](../releasing.md) / [English](../releasing.en.md)，[平台：中文](../platforms.md) / [English](../platforms.en.md)。

[RC2 OpenCode 对照附件](evidence/0010/rc2-opencode-regression.tar.gz)，SHA-256 `849f0d46e2326033456666027b04a16380451d3a68f0a5cfee00aefa5d1e2fbe`；包含结构化原始结果、准确输入清单及运行日志。原始失败集合经机器核对，无额外失败或 pending。

## RC2 远端与真实模型更新

`0.4.0-rc.2` 从干净提交 `e707becc821709a59958a3f5a6267f476bfcf612` 冻结，SHA-256 `3948cb9c4cd03f1505966b95e22729177cb09a4af28296fd1ef7be2dd0349754`。本地固定 Node 24 镜像/npm 11.11.0 与 GitHub CI 重建字节一致；[OIDC 发布](https://github.com/psiQAQ/planweft/actions/runs/34248506886) Passed，真实 npm 下载逐字匹配。[三系统 CI](https://github.com/psiQAQ/planweft/actions/runs/34248437017) Passed。

- OpenCode：preflight、lifecycle、context、recovery、maintenance、cold-reader、readonly、simple、skill-loading 九项自动断言 Passed。独立 review 先冷读文件，再核对事件与输入输出，确认首个工具读取 project-docs、唯一计划、历史与批准需求保留、三项 Linux 回归及 Windows Not Run。
- Pi：新隔离 RC2 context/recovery 均 Passed。旧 RC1 context Failed 保留；本次成功不证明旧失败已找到确定性根因。
- DSH：实际启动、幂等生命周期、cold-reader、readonly、simple、skill-loading Passed；context/recovery Failed（模型未收到字段），maintenance Failed（未建立 PWF 计划且改变历史表述）。模型进程本身成功，不能据退出码改写行为结果。

独立 OpenCode review 注记：模型的 Error Log 写 none，但 trace 有一次已恢复的 edit 匹配失败；“全部验证 Passed”应限定为已执行 Linux 检查，Windows 未运行。迁移文字 still/will 和 Windows 下一步位置引用有小偏差，未阻断从文件恢复；原始证据不回写美化。

## RC3 DSH 沙箱修复（未发布）

在官方 LocalBash + runHook 离线调用中，RC2 hook 能注入；换成官方 SandboxBash workspace-write，HOME 缓存不可写，PWF 快照创建静默失败。同样请求仅把快照放在允许的临时目录即可返回上下文，已形成因果复现。没有关闭或放宽沙箱。

RC3 的每次 hook 用私有 mktemp 缓存并清理，native shell facade 绑定宿主 session ID、按提示轮次去重本插件 PostToolUse 上下文；保留其他输出字段、权限、stdin 和 Stop 标志。原生 shell resolve/run 完整委托。状态有界为 1,024 个最近会话。Stop 上限和停滞 ledger 继续留在计划目录。`pwf-prog` 跨调用缓存告警不跨隔离 hook 保留，作为 DSH 差异明确记录。

真实沙箱协议探针（显式事件 carrier，不是模型）在 Python/Shell 两条路径均 Passed：上下文、双项目隔离、恢复、同轮工具提醒去重、新轮提醒、Stop cap=2、无 ledger 前进时退出、其他插件上下文与权限决定保留、无计划只读提示不写项目、损坏链接不当作新项目、PLANNING_DISABLED 禁用。新准确 RC3 模型及远端验收仍待完成。

[RC2 模型与 RC3 协议附件](evidence/0010/rc2-models-and-rc3-protocol.tar.gz)，733 项，SHA-256 `c8d2f77804c4ca7798b0a9f7d7ad3044ac4b737836987ad5559a972b10e57459`。包含原始失败、成功、官方沙箱因果探针及摘要映射；已检查认证值无命中。

RC3 本地最终回归：Python 66 项、安装器 28 项、DSH shell facade 3 项 Passed；构建一致性与 diff whitespace 检查 Passed。首轮路径泄漏断言误报了合法 mktemp 路径，修正为仅允许 DSH launcher 的该模板后全量复验通过；未扩大其他平台或路径豁免。

## RC3 注册与收集器更正

第一份未发布 RC3（提交 `f9d108b`，SHA-256 `36cf77868b143f6c5518eba55cf831fb389a5e19ea49a6a3b2d1d630376d7369`）安装及生命周期通过，但 DSH context/recovery/maintenance 仍 Failed，simple 未按要求只输出 42；cold-reader/readonly/skill-loading Passed。该归档保留，不覆盖或冒充后续修复包。

独立 reviewer 用真实 Cordis 4.0.2 复现：外层 fiber 提供隔离 shell 时 bridge state=0；独立私有 provider fiber 后 bridge state=2。原协议探针直接 apply，遗漏 readiness；已改用实际 Context/plugin 生命周期及原生观察事件，保留事件 carrier 为 fixture。固定 DSH 镜像中 Python/Shell 两路径全部 Passed，包含 nativeCordisReadiness。探针开发中曾用覆盖已绑定方法错误改变 scope，已移除；本地无沙箱路径的 Stop 超时不计 Passed。

Pi 0.84.3 精确镜像源码确认 agent_settled 在扩展 followUp 后发出。收集器现等待 settled，核对 isStreaming=false、isCompacting=false、pendingMessageCount=0，再 EOF shutdown 并排空输出；超时、重启或非零退出失败。真实 fake subprocess 回归 2 tests（七种失败子场景）Passed，独立 review 通过；此项不等于 Pi 模型停止门槛已通过。

[更正与失败附件](evidence/0010/rc3-readiness-correction.tar.gz)：336 项，SHA-256 `71f11788c52563fd4365949764ebfab26784b9e03d563515aea75ae5609fdd56`。含原始模型失败、真实 Cordis 因果脚本及修复协议结果；已检查认证值无命中。修复后的准确 RC3 模型仍待复验。

## RC3 工作流与停止实测

修正包 `d635881e147c6eca4f5d19bf2d0d60d2db8b9a276e2f0255b3df9c850feec11d`（干净提交 `c6d417c`）的 DSH context/recovery 已 Passed。维护的修复、测试、历史、需求和用户修改保护均 Passed，但唯一 PWF 计划仍 Failed。独立冷读确认旧 notes/work 可接续，模型已实际读取完整主 Skill；一般“只改任务相关文件”并非禁止任务记录。新增通用澄清，保留指定文件范围等真实例外，不修改夹具授权或放宽唯一计划断言。该包未发布，后续澄清包单独冻结。

- Pi 实际停止 Passed：未 execute 的默认 auto 会话自然 settled；parity + execute 出现三条本插件 followUp、四次 start/end，最终无 streaming/compacting/pending，项目不变。
- DSH 实际 Stop：默认、cap=1 且 ledger 前进、stall 三种场景均为一次原生 pass；gated 场景为 block→pass 且有实际后续回应。默认出现两个模型 step，但只一次 Stop，不将 step 等同于 gate 续跑；原因尚未单独归因。
- Claude 默认和 gated 续轮通过；首次断言错误地将同消息 ID 的 thinking/text 流式分块算作两次回应，修正消息计数。cap/stall 仍 Failed：禁用 hooks 的负对照也发生计数读取，inotify 无 PID 来源证明。不能把访问+退出当作 guard 执行证明；原生 debug 日志已保留，继续补可归因的证据。

`scripts/reassess-stop-evidence.py` 对已有原始结果使用修正后的断言，生成新的摘要绑定结果，不改原始 assessment、不重跑模型。Pi/DSH 后验复核 Passed，Claude cap/stall 继续 Failed。双计数后态、无意外 gate 续轮及负对照已纳入验收器，Linux inotify 只记录文件名/IN_ACCESS，不读内容或宣称 PID 归因。

[实际模型、停止与后验复核附件](evidence/0010/rc3-workflow-and-stopping.tar.gz)：873 项，SHA-256 `8a71cff5685baa60e0633ecbd3e7d93671fd0275f6fa04c6f020accf2a8339aa`。包括失败、原始运行及检查器更正；已检查已知认证值无命中。Python 71 tests Passed；后续收集器/记录修订另按相关回归验证。[三系统 CI](https://github.com/psiQAQ/planweft/actions/runs/34254397887) 适用于 c6d417c，不冒充新澄清包验收。

## 主 Skill 路由复核与进程归因

准确包 `5fb24d0c3af873c97df439ac07d1f39d357c24359283871369cb1faf023731a5`（`a8f0e1b`）分别使用 `deepseek-v4-flash`、`deepseek-v4-pro` 执行 DSH 维护，均仅唯一 PWF 计划断言 Failed，独立新会话的自动冷读断言 Passed。更换模型没有解除失败；不能据此证明模型或适配器单方原因。原始运行保留，后续脱敏附件单独归档。

独立源码复核发现：reuse 未限定长期文档，无 PWF 时 Quick Start 的 “For a separate task” 分支不明确，Single-file edits 排除项未区分复杂维护；已收敛这些语义，不改夹具授权和验收断言。同时合并重复 catchup，移除主入口不适用的 Claude 六事件/turn-loop 长段，改为按需读取现有 controls；更正 Continue 能力表和 attestation 人工批准措辞。上游快照、运行时和辅助命令实现保留。新准确包的模型验证仍待运行。

进程归因初稿的 PID/FD 复用、参数提及和异步 syscall 反例会产生假阳性，未用于放行。新模块以实际脚本摘要、fork 时身份、进程代际和精确计数路径绑定证据，正负样本都要求完整解析；原始 trace 只留容器私有 tmpfs，不导出任意 argv。12 项离线回归 Passed。固定 strace 6.1 派生镜像的无模型样本及真实 `check-complete.sh --gate` cap=1 正向测试 Passed，两个计数读取均归因到摘要匹配的 gate；这不代替实际模型门槛。

OpenCode 同一准确包的默认停止、cap/stall 与禁用对照 Passed；gated 场景未观察到后续回应，继续 Failed。Claude 新进程归因模型复验被自动审批拒绝，原因是 Claude 目的地/负载的授权范围需要明确；没有绕过执行。其已有模型结果与新的无模型正向测试分开记录。

## RC3 公开产物与原生续跑

`7d690010fbf8705129d3fb44b2556bb6a0fa7de6` 冻结的 `0.4.0-rc.3` 已由 [OIDC](https://github.com/psiQAQ/planweft/actions/runs/34264091642) 发布到 next，CI 和真实 npm 下载均为 SHA-256 `09ea0e4dceb88c9b845af851916356c44f3447071e0d1311dc38841639705060`。五个固定容器的准确包 preflight/lifecycle 全 Passed，[三系统 CI](https://github.com/psiQAQ/planweft/actions/runs/34262987621) Passed。先前同版本的本地未发布归档保留，不能用于声称远端准确字节。

OpenCode 官方 1.18.22 `run` 在首次 idle 结束收集，而插件的事件回调不被等待。新增独立原生 serve + SSE 采集，只发送一次初始 prompt，要求插件第二 user reason、对应 parentID 的 assistant 完成和后续 idle，再观察至少 5 秒无新活动。真实六场景均 Passed；未参与实现的独立 reviewer 对照原始 SSE/消息/状态确认，观察窗 5.003–5.250 秒。服务器在观察后由 harness 结束，退出 -15；不冒充自然退出、原生 settled 或无限期无后续事件。cap/stall 负对照无计数读取，正例均有两个计数读取；此路线无 PID 归因，边界保留。全量 Python 90 tests Passed。

DSH 同包 flash 的单一计划已建立，但 discovery 命令失败的泛化表述不准确；[独立复核](evidence/0010/dsh-routing-independent-review.json) 将历史语义 Passed 与文档准确性 Failed 分开记录，不改原自动结果。Pro 对照仍未建立唯一 PWF 计划，维护 Failed、冷读自动断言 Passed。当前没有满足全部维护门槛的 DSH 新准确包结果，不继续以重复重试代替修复依据。

远端 RC2→RC3→RC2→RC3→卸载：Codex、Claude、Pi、DSH 全流程及适用原生入口检查 Passed。OpenCode CLI 生命周期完成，但独立 npm 原生配置没有注册 `pw_*` 工具，因此该平台总结果 Failed。独立源码诊断：官方 resolver 读取 `exports["./server"]` 或 `main`，不会选择仅有的 `exports["."]`；根 manifest 缺失对应入口。需递增候选版修复，不能覆盖已发布 RC3。

[RC3 发布、成功与失败附件](evidence/0010/rc3-release-and-native-observation.tar.gz)：1,199 项，SHA-256 `8799518eb4d6fd46c7a292033c50b98192bc3b7bf3fee0125956fcabd506e239`。附 sources.json 映射原始运行相对路径；检查已知认证值无命中、脱敏私人路径并规范归档身份。Claude 实际配置使用 DeepSeek 官方 `https://api.deepseek.com/anthropic/v1`，此前授权问题误写 Anthropic 地址已更正；新模型命令尚未获明确补充授权、未执行。

## RC4 npm 入口修复

根 manifest 的 `main` 与 `exports["./server"]` 现指向原有 OpenCode V1 预编译入口，保留根 ESM/Pi/DSH 元数据。只有产品版本递增，无依赖变化；编译 JavaScript 除版本常量外不变。打包检查直接验证 tgz 中的 manifest 与入口文件，root-only 回归明确拒绝 RC3 形式。

固定 OpenCode 1.18.22 容器在 network none 下分别复制 RC3 profile/cache，仍配置 `plugin:["planweft@0.4.0-rc.3"]`，只改副本 manifest。四组预期均满足：原始没有工具，main-only/server-only/both 均加载三个 pw_* 工具；包内其他文件摘要不变。原始缓存只读，未注入认证或调用模型。此为因果 fixture，不代替准确 RC4 或真实远端安装。

[入口因果与回归附件](evidence/0010/rc4-entry-causal.tar.gz)：21 项，SHA-256 `350fd75e92e5b506b7980be81517bd6fad633699ab3a02267869e4b060b1fd3f`。全量 Python 91 tests、安装器 28 tests、DSH facade 3 tests Passed；构建一致性通过。RC4 精确归档与远端验收待执行，DSH/Claude 的未完成门槛保持。


## RC4 OIDC 与真实 npm 生命周期

干净源码 `1d1c76c1d6048fd67fa6ef1b614e11b999106db6` 的准确归档 SHA-256 `c6f54319befc8c43c559fd4c5af2eb6ca3d1b626e6c0b3fd65cb67c11d9d318b`，OIDC 运行 34267947801 成功，CI 重建逐字相同。官方 npm 下载再次匹配，next=0.4.0-rc.4，latest=0.4.0-rc.1；未发布稳定版。三系统 CI 34267221127 成功。

五固定容器分别下载 RC3/RC4，真实执行 RC3→RC4→RC3→RC4→卸载；安装内容/执行位、持久来源、清理 npx 缓存、项目记录保护均通过。Pi 原生 npm 入口、OpenCode 三个 pw_* 工具及 Skill 配对、DSH 原生包启动与移除通过。这是无认证、无模型的远端生命周期证据；不能替代公开 Git 市场或模型会话。

RC4 Codex 六项自动检查通过：context/recovery/maintenance/cold-reader/readonly/simple。独立 reviewer 通过维护和冷读语义，保留 Windows 待验与 hook trust bypass 限制。stopping/gated-continuation 两场景因服务返回 usage limit 而失败，未重复运行或消费重置额度。

Pi 首组 context 失败：测试显式 parity 与 /pw-plan-execute 激活了未完成计划循环，首轮正确返回注入随机码，后续真实 followUp 使模型读写三文件；完整 settled 收集正确，不截断。新测试使用新建 complete 合成计划分离注入/恢复，明确不覆盖已激活进行中计划的只读恢复，原失败保留。原组 recovery/maintenance/cold-reader/readonly/simple/stopping/continuation-limit 自动检查通过；独立审查进一步发现主计划阶段与错误历史不一致，文档一致性 Failed，见 REVIEW-0010。停止测试保留默认无激活与显式执行三次续跑的区别。


公开 Git 市场补测：Codex 0.149.1 与 Claude 2.1.241 从公开仓库注册、安装、同提交刷新、卸载与注销均通过；参考树与实际缓存分别 276/268 文件（摘要和执行位）完全一致，各一份主 Skill，项目四份保护文件不变。前后公开 SHA 固定 `1d1c76c`。Codex 使用 `marketplace upgrade` 后 `plugin add` 重装，Claude 使用 marketplace/plugin update。失败的超时、入口/挂载和误用 update 命令尝试保留。最终成功运行对应 runner SHA `ff405ed49ea32356aa345546682cd55900f40a168a54873848bd480c3d365b15`；后续只读根、执行前归档、清理失败退出的收集器增强仅经三项离线回归，未重跑网络。管理命令不证明模型读取、hooks 信任或跨版本 Git 更新。


上述 RC4 已闭合运行收录于 [rc4-remote-and-models.tar.gz](evidence/0010/rc4-remote-and-models.tar.gz)，1500 文件，SHA-256 `83226f26c7613a179af77d478f914ce979c680a9802ce6aa904682b58a51f4c8`；内含 sources.json 对应原运行相对路径。归档前检查实际私有 key 无匹配，统一脱敏私人 home 与归档 owner；原准确 npm 字节证明另存包外。Codex/Pi/OpenCode 独立语义报告分别见同目录 `*-rc4-independent-review.json`，结论不可只读自动 assessment。


审查反馈实测采用同一准确 RC4、原项目快照和具体独立发现，原失败输入逐项 SHA 绑定。Pi R1/R2 修正及新冷读经独立核查 Passed，只有指定 task_plan 两处文本变化；不是首轮无误或自动触发审查的证据。DSH 第一反馈的 R1/R2/R3 实际修正与文本保护均通过独立检查，但新 collector 误读 human stdout 而非 native-events，导致假“无最终回答”，冷读未启动。保持该运行 Failed/冷读 Not Run；修正后增加原生 assistant/turn/end、缺日志不 fallback 和错误结束回归（11 tests Passed），在新目录复验，不改写原结果。


修订 collector 的 DSH 新反馈组：R1/R2/R3 纠正与无 review 的新冷读独立 Passed，两原生会话 completed；原维护 Failed、第一反馈收集器 Failed 均保留。Pi/DSH 反馈和 DSH RC4 主组见 [rc4-dsh-and-review-feedback.tar.gz](evidence/0010/rc4-dsh-and-review-feedback.tar.gz)，483 文件，SHA-256 `a42ee4be786cbfa72ca7be23cd7b6c9b44d3d62694d92232b6336458188d233a`，sources.json 映射原运行相对路径。分别以 `pi-rc4-feedback-independent-review.json` 和 `dsh-rc4-feedback-independent-review.json` 记录独立结论，不修改原 summary 的 Awaiting 状态。原输入 SHA、容器清理、非允许文本保护均通过；无缓存/执行位或首轮无误的扩大承诺。

本轮新增入口的全量 Python 回归为 107 Passed，之后两次定向修复的反馈回归分别 10/11 Passed；最终源码交由 CI 全量复验。正式 0.4.0 未发布：Codex 服务额度、Claude 明确模型端点授权、OpenCode 冷读状态误报及最终稳定准确归档的全部门槛仍未解决。候选下载与精确摘要不是稳定发布授权。

## RC5 修复准备与 RC4 补充验收

准确 RC4 的 Codex 普通停止复验 Passed，gated 的模型正常完成但无计数变化或第二轮响应，已排除先前额度错误作为当前原因。固定插件 `.codex/hooks` 三个辅助脚本沿用 standalone 的 `.codex/skills` 假设，而本插件资源位于包根 `skills`。构建器仅在 Codex 分发映射修正 Stop、resolver 和 SessionStart；独立复制的中文/空格路径包先复现五处失败，再通过 root/slug gate、递归/cap/stall/禁用、错误绑定及实际 catchup 调用。未修改固定上游源码或 standalone 比较树。

Claude Flash 的主组完成，代码维护和冷读独立 Passed，但主 Skill 未实际读取、PWF 计划未采用为真实 Failed。Pro 单变量对照实际读取中文 Skill 后仍错误地将旧 notes 作为豁免，采用 Failed；一次根目录 find 超出实验边界，未观察到凭据内容读取。Pro 模型和安装器清理已完成，外层进程在保存快照/评估前中断，冷读 Not Run，整轮 Incomplete。两份独立审查分别见 `claude-rc4-independent-review.json`、`claude-rc4-pro-independent-review.json`；不能用局部 controller Passed 替代整轮验收。

Claude 六项 Stop 溯源组均按失败保留：原始解析器无法完整归因多线程 syscall。无认证、无模型 CLI 命令复现了 `21<Bun Pool 0>` 返回值被空格截断的问题，修正后 13 项 parser 回归 Passed；其他共享描述符歧义及未解析返回仍未关闭，不宣称已完成实际溯源验收。

用户报告内存上限中断后，确认 `/tmp` 为 tmpfs，结束的 0.3.0 验证依赖/下载缓存无进程引用，清理 13 目录、约 3.97 GiB 逻辑大小。日志、源码、准确归档和 Git 备份保留；当时 `/tmp` 从 70% 降到 20%。发现快照先读取安装目录再过滤的内存隐患，改为遍历前剪枝根级缓存，回归验证既不读取缓存又保留嵌套同名文档。容器增加 RAM/Swap/PID/tmpfs 硬限额并提前保存 before/In Progress；意外中断保持未完成。

共享 HOME 无模型隔离：Claude/Pi/OpenCode 中 A 旧 RC3、B 新 RC4，更新/移除 A 后 B 原生来源、版本和完整项目内容保持不变；Codex/DSH project scope 拒绝且 HOME/项目未改变。Pi 首次错误比较相对与绝对源路径，Failed 保留；根据固定 0.84.3 `package-manager.js` 的 `getBaseDirForScope`/`relative` 语义以项目 `.pi` 解析后，新目录实测 Passed。原运行都保存各自 runner SHA，测试容器均已删除。独立 review 收窄结论：该入口只查被移除侧安装器收据和 B 的原生状态，不单独证明被移除侧原生缓存无残留；完整卸载另见 registry lifecycle，模型/hook 均 Not Run。

本地全量 Python 117 tests Passed；后续 Pi 路径回归 4 tests Passed；安装器 28、DSH facade 3 Passed。原始与迁移上游各 721 Passed、63 skipped（平台或依赖条件保留），子测试数分别 798/851。确定性构建 Passed；该组不代替准确 RC5 包或新跨系统 CI。

[本组附件](evidence/0010/rc5-path-resource-and-rc4-followup.tar.gz)：712 文件，SHA-256 `0623d06cc7cf2fb2971596b7b154d4241b9c19a98526f1b6455deca8f570ca63`，包括原始失败、停止组、Pro 中断标记、资源清理、隔离结果和回归日志；sources.json 映射各运行来源。没有覆盖原 RC4 或历史附件。RC5 准确归档、五宿主完整稳定门槛和正式发布仍未完成。

## RC5 准确候选发布与复验

RC5 冻结源码 `c3bb9d870429e304149ca58b0e804ea55f4b537a`；唯一 npm 包为 5,213,945 bytes，SHA-256 `f9123657773eb95cfe3df79b3f55669f12b37203bf2a593c1e749da1676069b3`。公开前扫描本轮五个提交、70 个唯一 blob、递归附件及该包共 4580 项负载，无凭据或私人路径发现。

[三系统 CI 34316870816](https://github.com/psiQAQ/planweft/actions/runs/34316870816) Passed；[OIDC 34317038628](https://github.com/psiQAQ/planweft/actions/runs/34317038628) 使用固定期望摘要发布到 next，重建字节匹配。真实 npm 下载的 SHA-256、SHA-512 integrity 及本地逐字比较均 Passed。latest 仍为 RC1，正式 0.4.0 未发布。

准确 RC5 Codex 组：普通停止、gated 续跑、两个 disabled 对照 Passed。普通一次、gated 两次 assistant 回复发生于各自同一原生 turn；gated 只增加两个计数器，计划保持 in_progress，其余项目快照不变，没有模型工具调用。cap/stall 仍 Failed：唯一失败为 negative_control，禁用组也有计数器 IN_ACCESS，无法归因读取进程。全部使用 invocation bypass，不证明正常持久信任；未捕获原生 Stop decision 事件。独立 reviewer 核对同意上述边界，见 `codex-rc5-stop-independent-review.json`。

从真实 npm 下载的同一准确 RC5 包，五个固定容器分别 preflight 与 lifecycle（安装、同版本 update、内容核对、移除）均 Passed；共有十个串行测试容器，全部删除，原常驻容器保持。Pi/OpenCode/DSH 原生发现或启动入口通过；该组没有模型调用，不宣称 RC4↔RC5 跨版本或最终稳定归档验收。先前一次将多个 host 放在单个 --host 后的调用被参数检查拒绝，未创建目录或容器；使用入口规定的重复 --host 后执行。

[RC5 发布与原生证据](evidence/0010/rc5-native-and-release.tar.gz)：589 文件，SHA-256 `f8d93e9f370578f10c3226a2fe65c4ba67303bdd0dad638aea62aa0b85994fba`。保留来源索引、摘要、CI 日志、Codex 原失败及五宿主原始检查，不改写早先附件。发布后的说明文档另行更新；重新生成该已发布归档必须使用上述冻结提交，而非后续文档提交。

归档完成后，确认测试收据均已注销，再清理 12 个合成项目中的可重建版本存储，共约 1193 MiB；项目记录、收据、原始日志、快照、准确 npm 包和发布树保留。清单见 `rc5-completed-cache-cleanup.json`。本轮合计清理约 5.1 GiB 逻辑缓存文件，不把磁盘回收量等同于物理内存下降量。

## RC6：修复入口和验收器（候选冻结前）

本轮从干净 master `06864c0` 开始，在独立修复分支实施。核心 Skill 改为简短任务流程，详细 PWF 手册作为包内按需引用保留；五语言变体保留独立的显式加载边界。只读、书面研究产物、旧计划迁移和批准需求限制不变。

- 首次迁移上游回归：7 Failed / 714 Passed / 63 Skipped；失败涉及描述中的能力披露及主入口模板导航。修复后原断言保持，721 Passed / 63 Skipped / 851 subtests。
- 本地最终 Python：131 Passed；Node 安装器：28 Passed；DSH facade：3 Passed。构建与验证一致。第一次本地全量在生成物尚未刷新时因漂移/编译绑定失败，保留日志，后续完整重跑通过。
- 停止归因：20 项离线反例通过；两份真实无认证 Claude CLI trace 完整解析。真实模型的未知结果仍是未解决观察项，不将离线通过等同于 cap/stall 通过。
- 资源：新增 4 GiB 可用内存、8 GiB 输出存储前检；场景最多 600 秒，容器 2 CPU / 3 GiB / 无额外 Swap / 256 PID。确认容器不存在后才清理自有无引用版本缓存；记录与准确归档保留。
- schema 2 将原总项 Passed 细分为必须有附件的实际场景；Pi 包批准与不支持原生逐工具拒绝的边界分开。模型、准确 RC6 包及远端发布验证尚待执行。

新 Codex strace 派生镜像只复制已验证 Claude trace 镜像中的 strace 6.1 及必要库，离线构建；保留原镜像。新镜像 ID `sha256:9ffeaf322318e5bfa6de76190ece94c323a3964f38e1ad426284b021b8ab5b58`；实际 CLI 与 strace 版本需运行前核对。

## RC6 发布后停止归因修复

RC6 从干净源码 `36dfe13cd03f48cbb74698c8c282732d13d19780` 冻结，[三系统 CI](https://github.com/psiQAQ/planweft/actions/runs/34322062209) 与 [OIDC](https://github.com/psiQAQ/planweft/actions/runs/34322158954) Passed。npm 下载 5,219,998 字节，SHA-256 `c531188e46d268048ca0ab559baa358fc70af07277cb0001c521951234525799`，与本地及 CI 归档一致。next 为 RC6，latest 仍 RC1；不代表稳定发布。

保留三轮 Codex 失败：首次六项均被全局共享描述符冲突阻止；识别 Codex 原生 `--gate task_plan.md` 参数后，cap 正对照能绑定 gate 和两个计数器，但正/负仍有 87/101 冲突；按子进程首事件收紧非共享快照区间后仍有 38/16 冲突。均未把后台 IN_ACCESS 当作 hook 证据。

进一步采用两遍重放：先收集实际资源共享和重叠区间，再按 FD/cwd 绑定传播未知状态。非相关宿主冲突保留在报告中；未知状态影响 gate 身份或成功读取时仍失败。复制时新增 FD、CLOEXEC、dup、目录解析、UNSHARE、区间内覆盖、PID 代次、退出、截断均有反例；只允许明确的后续覆盖清除对应未知。独立 reviewer 发现首遍错误可能被覆盖，已固定脚本字节并合并两遍错误，29 项回归 Passed。

最终准确 RC6 的 Codex 六项停止 Passed：普通停止、gated 续跑、cap/stall 及各自 disabled 对照；固定 Codex 0.149.1、gpt-5.6-terra 与 strace 6.1 派生镜像。容器全部清理、原服务集合保持，原始失败留存。此组使用单次 hook trust bypass，不能计作正常持久信任；最终独立证据审查另行记录。验收器改动不改变 RC6 npm 内容。

[RC6 离线原始失败与修复附件](evidence/0010/rc6-offline-repairs.tar.gz)：11 项，SHA-256 `0c92ff02d9f31f69a6ee8f8cf455c87c8d22f6f43e38284a383369ec67279b44`。manifest 保留原始/公开摘要，私人路径脱敏、归档身份规范化；不包含模型认证或旧聊天。

### RC6 原生权限、持久信任与维护再审查

准确远端 RC6 仍为 `c531188e46d268048ca0ab559baa358fc70af07277cb0001c521951234525799`，本阶段先修验收器，不修改已发布包。

- Codex 原生规则拒绝已实测：固定命令的 `execpolicy check` 为 forbidden；同 call_id 的实际工具调用返回 Rejected；相同写入程序在独立正控制可写，受保护项目字节未变化。只接受严格的原生调用/结果配对，不接受模型自述或拼接的输出。
- Codex 正常信任实测 Passed：未信任时 NO_CONTEXT；真实 TUI 完成项目/7 项 hooks 信任；无绕过参数的新会话自动收到计划；owner 更新计划 token 后另一个新会话收到新值。前三次失败与调试记录保留；权限拒绝场景单独使用了 hook invocation trust bypass，不能代替这项持久信任。
- OpenCode 原生 bash deny 和 DSH read-only 文件写入拒绝 Passed。DSH 首次在模型启动前因 read-only/never 与默认 preset 不匹配失败，修正隔离测试配置后观察到原生 `FS_SANDBOX_DENIED`，没有把普通文件错误算作权限拒绝。
- Pi 原生项目包批准 Passed：未批准时无 PlanWeft 命令，显式批准时为五个 `pw-` 命令及一个主 Skill。这是项目资源批准，不是逐工具沙箱。
- OpenCode 维护的历史字符串断言误报，经独立审查语义 Passed；冷读核心结论正确，保留其 progress 行号引用错误，审查给出实际 findings/旧记录来源，不改 owner 文档以迎合报告。
- Codex 维护的 1 项强化字节测试实际 Passed，但旧测试器硬性要求至少 2 项。新测试器改为同一测试在修复实现通过、原始 BOM 实现产生 assertion failure；不以方法数量代替回归敏感性。原自动 Failed 不改写。独立审查另发现真实记录缺陷：progress 初始化 Phase 1 与完成态 task_plan 冲突，findings 初始观察未标修复前；这两项仍为 Failed，需产品模板修复后复验。

原生记录、准确项目快照、冻结执行器以及失败过程归档于 [RC6 native repairs](evidence/0010/rc6-native-repairs.tar.gz)，SHA-256 `f09be91f85f0124309daac756504999829e130dc0c7387664c3e575b4eda7a0d`，1479 项。manifest 分别保留原始和公开脱敏摘要；省略物理项目树和可重建缓存，保留 before/after JSON。此附件不是稳定版验收。OpenCode 已结束场景的两份无挂载、无安装引用的原生 node_modules 共释放 109,580,458 字节，证据和锁文件保留。Claude 官方兼容端点的明确授权仍待答复，未绕过自动审查阻断。

### RC6 Pi / DSH 的维护与独立冷读

两宿主自动检查均 Passed，但独立评审保留实质 Failed：findings 仍将调查时的 BOM 实现、旧说明或计划缺失称为当前事实。Pi 还读取了固定任务明确禁止的 `.pi/settings.json`，内容为安装资源路径，无凭据；DSH 打印额外 `DSH_*` 运行时元数据，未读取其指向的会话内容，不能夸大为历史正文访问。两者冷读能区分历史 Passed 与本次重跑/未重跑，不能以此覆盖 owner 记录缺陷。

[RC6 Pi / DSH 原始记录](evidence/0010/rc6-pi-dsh-maintenance.tar.gz)，152 项，SHA-256 `177f1088e953b6e91e9f5b8936f73b1116df5f896d4ab6167ab546596ce63a05`。独立结论：[Codex](evidence/0010/codex-rc6-maintenance-independent-review.json)、[Pi](evidence/0010/pi-rc6-maintenance-independent-review.json)、[DSH](evidence/0010/dsh-rc6-maintenance-independent-review.json)。原始自动评估未改写。模型容器现已全部结束，无验收容器残留。owner 反馈入口也补齐相同 3 GiB/无额外 swap/256 PID/临时文件上限、运行前资源检查及场景结束缓存清理，12 项定向检查 Passed；该入口修复没有被记为新的真实反馈验收。

### RC7 初始化记录修复与离线回归

RC7 通过同一 overlay 修复六语言 progress 模板、Shell/PowerShell 内嵌初始化和 OpenCode fallback。progress 不再初始化第二个当前阶段；findings 指明来源和观察时点。`task_plan.md` 的阶段协议及既有项目记录跳过逻辑保持不变。没有修改已发布 RC6 或 vendor 源码。

- 本地 Python：156 Passed / 1 Skipped / 2824 subtests。后续反馈异常清理反例 13 Passed；新增迁移契约测试所在组 7 Passed / 1 Skipped / 105 subtests。PowerShell 本机缺失，实际执行 Not Run，已加入三系统 installer CI。
- Shell 实际初始化：普通、analytics、五语言路径；再次初始化保护原三文件及追加 CRLF 用户内容。
- Node 安装器 28 Passed；DSH shell facade 3 Passed；TypeScript 5.9.3 编译及确定性目录检查 Passed。
- 固定原始 PWF：721 Passed / 63 Skipped / 798 subtests。首次迁移：两个 progress 占位契约 SUBFAILED，其余 721 Passed；失败保留。独立审查后的两个 token 适配：721 Passed / 63 Skipped / 851 subtests。
- OpenCode：原始 34 Passed；迁移原始 32 Passed / 2 既有设计差异 Failed，失败集合严格匹配既有两项；类型检查及适配后全部契约 Passed。已释放两份测试 node_modules 和下载缓存共 239,019,755 字节，保留源码、锁文件和日志。

[离线记录](evidence/0010/rc7-offline-records.tar.gz) 共 28 项，SHA-256 `9eacf2a1f65e95023013e229c0ac0f34c6f880c7b55284e4d72610b3ab30f041`。这是候选准备证据，不是稳定准确归档或新宿主模型验收。RC7 发布后仍须按原固定任务复验，不采用显式调用或重复无变化试验替代自动匹配。

RC7 首次三系统 CI 的 Windows 作业在 setUpClass 阶段因默认 cp1252 读取多语言入口失败，尚未执行 PowerShell 初始化；Linux 作业 Passed，macOS 被矩阵取消。原始日志和摘要见 [编码问题记录](evidence/0010/rc7-windows-encoding.json)。修复为构建器及原生适配器显式 UTF-8 读取，新增模拟旧默认编码的回归；本地 8 Passed / 1 PowerShell Not Run，生成物未变化。矩阵关闭 fail-fast，后继 CI 各系统结果分别保留。此修复不修改已冻结 RC7 包内容，不通过更改摘要放行。

### RC7 OIDC 发布与准确远端包

公开 master `7e66ee9214364ffa5f00a04a8d040e4ace082980`；[三系统 CI](https://github.com/psiQAQ/planweft/actions/runs/34332899246) 全部成功。每个系统实际执行 9 项记录模板/初始化测试且无 skip（包括 Shell 与 PowerShell）；Linux 完整 unittest 为 160 项 Passed。原失败 Windows 作业保留，不作为通过证据。

[RC7 OIDC](https://github.com/psiQAQ/planweft/actions/runs/34333285542) 发布到 next。固定 Node 24.19.0 / npm 11.11.0 下，原冻结源码 `b51a6a3` 和 Windows 构建修复后的干净源码重建包逐字相同：5,258,313 字节，SHA-256 `e3d67af7dcba154a3800e39c19ec06a7f40b874d3b92dc7b7517bed85cc4bed2`。真实 npm 下载、SHA-512 integrity 与 SHA-1 也匹配。8 项新增提交和递归附件审计未发现私人路径、7 个已知凭据值或归档身份泄漏。

五个固定 Linux 镜像对准确 RC7 包执行预检及同版本原生安装/卸载/重新安装，共10项 Passed；这不是多版本升级或模型验收。无本次容器残留，原有容器保留；另清理 OpenCode 两场景无挂载引用的 node_modules，共 109,580,458 字节，项目证据和锁文件不变。当前 npm latest 仍是 RC1，正式0.4.0未发布；开始使用准确远端 RC7 对记录修复进行模型复验。

## RC7 准确远端维护、独立冷读及 RC8 修复依据

RC7 固定 Node 24.20.0 的 Check `34334806556` 四个 job Passed，保存全部日志并逐一确认实际 Node 版本。与先前 RC7 发布/三系统日志分开保留，不能将新 CI 当作模型验证。

| 准确 RC7 宿主 | 自动维护 / 冷读 | 独立结论与范围 |
| --- | --- | --- |
| Codex | Passed / Passed | 维护、唯一状态、观察时点与文件冷读 Passed；辅助 resolver 拒绝后恢复和残留未来时态保留为非阻塞；该维护不证明持久信任或 native deny |
| Pi | Failed / Passed | 实际没有采用计划，错误把旧记录和未设 PLAN_ID 当例外；读取禁止的宿主配置；冷读无依据称原跟踪实现为用户新增；overall Failed |
| OpenCode | Passed / Passed | 实际实现已改 utf-8，但 findings 两处仍称当前 utf-8-sig；漏记首次反事实脚本错误，冷读错误归引并漏报矛盾；overall Failed |
| DSH | Failed / Passed | 历史日期/Passed/仅历史观察实质保留，literal误报保留；功能、计划与外部独立冷读核心 Passed；扩展读取 DSH_* 超出实验范围，overall Failed；未见凭据/业务/旧聊天内容 |

四份 `*-rc7-maintenance-independent-review.json` 保存逐项判定、原始摘要及限制；主 Agent 核对所有附件摘要。DSH owner 内部子代理确实存在并执行获准测试，也收到了项目 hook 数据，不能把它称作纯文件读取盲审；外部 cold-reader 才是独立只读、无插件的新会话。原失败未重写。

脱敏准确证据包 `evidence/0010/rc7-live-records.tar.gz` 共680项，SHA-256 `641ea37db7083d18d7ad148d00af84f4e5f8c5a8c05821b58767ec16c4edbdb2`。包含原始前后JSON快照、模型trace、controller、CI、registry proof、五宿主非模型native生命周期及清理记录；省略物理项目树和可重建缓存，manifest 保存原始/公开摘要映射。所有四组模型容器已清理，原服务保留；OpenCode 后续另释放54,790,229字节已结束且无引用的依赖缓存。

RC8 以独立 [Pi 入口诊断](../reviews/0010-rc7-pi-entry-diagnosis.md) 和 [入口源码审查](../reviews/0010-rc8-entry-review.md) 为依据：用实际文件/绑定/输出分支替换 selection-valid 抽象前提，区分空返回的拒绝与正常新任务，直接使用宿主 Skill location；保留 PowerShell/legacy 与 canonical Bash 的真实初始化差异。将观察时点、用户原有修改来源及最终当前事实核对纳入主流程。description 精简且原宿主完整metadata保留在手册；没有自动写入hook或运行时状态协议变更。小型脚本契约4项与入口2项Passed；其不证明RC8模型已通过。

[门槛独立审查](../reviews/0010-rc7-gate-gap-review.md) 还确认最终 stable 缺口：准确包故障恢复/用户副本保护、实际去重/重复hook、运行项目隔离、远端新会话及完整原生渠道更新。新增native registry worker和资源受限wrapper的16项离线回归Passed，RC6↔RC7实际运行开始；仍按实际结果记录，不填造stable acceptance。


### RC8 入口和原生版本生命周期修复

RC8 尚未发布。精简 description 的首次迁移回归为 718 Passed、3 Failed、63 Skipped；发现阶段丢失能力披露，不能由后读手册替代。修复保留任务触发和显式历史读取/文件恢复/宿主续跑边界，未修改原上游披露测试的 21 个断言。随后迁移回归 721 Passed、63 Skipped、851 subtests Passed。该迁移树仍应用既有两 token progress 契约补丁，并非完全未修改的上游基线。

本地完整回归曾为 185 Passed、1 Failed、1 Skipped：Gemini 新增能力 notice 与旧“所有移动资源完全相同”断言冲突。更新为新增 notice 必须存在、原文所有字节和执行位必须保留。定向入口/资源测试 7 Passed、126 subtests Passed；输入前置验证 2 Passed、4 subtests Passed。语言 GUIDE 的错误链接和宿主摘要遗漏也保留在独立 review 中，逐项修复后复验。上述代码契约结果不证明模型采用或语义交接通过。

RC6 → RC7 → RC6 → RC7 → 卸载的真实原生 npm 生命周期：Pi、OpenCode、DSH Passed。逐步校验准确包字节、唯一原生注册及 Skill 配对；Pi/OpenCode 执行原生发现，DSH 为配置组合与启动观察，模型发现另验。项目记录保持原字节。OpenCode 前两次分别因旧缓存路径假设、宿主自动加入 schema 而 Failed，保留原记录；修复只绑定实际固定版本缓存并在 fixture 预置官方 schema，仍严格核对所有无关配置。独立 reviewer 发现悬空 Skill 链接误判卸载成功，已加入 exists/is_symlink 双检查和负对照。

脱敏附件：[rc7-native-version-lifecycle.tar.gz](evidence/0010/rc7-native-version-lifecycle.tar.gz)，159 个文件、324839 bytes、SHA-256 `97b497ece8a487ee3fab6f50cf2438c9409aed142bed781d259d71fee91e9366`。含两次原始失败、三个宿主真实完成结果、冻结执行器、逐文件原始/公开摘要；不包含可重建安装目录、缓存及认证。所有所属容器均确认删除，Passed 场景自有 npm cache 已清理，失败输入保留。

最初导出误纳入大量可重建安装副本，产生约 111 MB 的未提交临时附件；改为明确顶层日志/摘要/冻结脚本清单后，仅保留上述有界公开附件。原始输入未删除，未执行全局 prune。

开发回归原始失败/修复后日志：[rc8-development-regressions.tar.gz](evidence/0010/rc8-development-regressions.tar.gz)，SHA-256 `c0f5a9aec7839cc9a150ce678913ff2723ef6d8fa21f53cc002a683f5927df94`。源码及本地解释器日志仅作开发回归，最终包另验。


### RC8 公开候选与后续复验

`a3d6cc3c41e2f6ffe636add694b6096fb342ba81` 已推送；Check [34339605601](https://github.com/psiQAQ/planweft/actions/runs/34339605601) 三系统全部 Passed，OIDC [34339751089](https://github.com/psiQAQ/planweft/actions/runs/34339751089) Passed。npm `0.4.0-rc.8` 位于 next；远端 5386708 bytes，SHA-256 `d6f34542495d811cc3171af0f6db96f30b1ef3089289fc740e4a4686a27d4a78`，与已审计本地归档相同。latest 仍为 RC1，正式版本未发布。

五锁定镜像 preflight/lifecycle 10 个场景 Passed；仅准确本地安装、移除、重装，不替代跨版本、模型或稳定产物证据。核查无运行容器引用后清理两份已完成 OpenCode node_modules，各 54790229 bytes；原始日志、项目记录、准确包保留。

Pi RC8 固定维护和冷读的自动检查 Passed。独立审查发现自动观察仍不充分：在主 Skill 正文返回前，同批发出了读取 `.pi/settings.json` 的请求，且更早读取安装记录；不能称读过 RC8 Step2 后又忽略它。已出现的读取范围违例仍保留，不靠事后文档纠正抹去。`progress.md` 把本次未见执行的原测试命令写成已观察通过，也需纠正。最终独立 review 和后续修复另行记录；尚未通过稳定语义门槛。


RC8 独立复核结果：Pi review SHA `9a8ee80196df1ea378bfe49465089beac5d3714a4fae8981f382799382f43001`（75附件）；OpenCode `5d1a1153cefb8ca8ce162778a839da29fc4ef371de63079228da3896e42ff32f`（98附件）；DSH `501c99f50a3cdd884d74a2ff40c6edddb1498c362da520ca0a9051702fc7c7ba`（56附件），主 Agent 均逐项复核摘要。三者实际修复/回归与文件冷读有 Passed 证据，但整体均未通过严格语义/范围门槛。OpenCode 手工使用固定 `/tmp/opencode/bomreg`；DSH 修复前单测声明缺来源、恢复过的工具错误未记载，人工临时路径范围未证明（不把未观察到的路径写成已证实）。报告位于本目录 evidence/0010，自动 Passed 与原始失败保留。

RC9 开发修改针对观察到的触发点：description 在正文加载前提供宿主给出的资源路径规则；六语言工作流区分实际命令/操作及观察结果、引用历史、静态推断与 Not Run；手工 scratch/counterfactual 留在授权项目内本任务目录并确认清理归属。不增加写项目的 hook。这是模型指导，不宣称是强制权限隔离。独立 review 保留 Phase3 历史快照解释分歧，不把非共识意见虚报为新增一致失败项。

RC9 开发回归：Python 197 Passed、1 Skipped（本机无 PowerShell）、2974 subtests Passed；Node installer 28 Passed、DSH shell 3 Passed；迁移上游 721 Passed、63 Skipped、851 subtests Passed。原始上游字节和既有对照适配未改变。编译使用已有 TypeScript 5.9.3，无新增依赖。准确 RC9 归档与远端/模型验证尚待执行。


RC8 完整公开附件：[rc8-live-records.tar.gz](evidence/0010/rc8-live-records.tar.gz)，595 个文件、1055189 bytes，SHA-256 `a16db3744d4f624b8291228757005fb029fd2a351016903d3e0f9c7390eb9c60`。包括公开前审计、CI/OIDC、registry proof、五镜像原生生命周期、三个真实维护/冷读原始记录与逐文件原始/公开摘要。三份独立语义 JSON 单列，保留各自判断。

五宿主真实 A/B 夹具均 Passed（Pi 单组，OpenCode/DSH/Claude/Codex 串行组）：新增、修改、删除文件被正确升级/回退，卸载/重装与项目记录保护通过。两份 A/B 均为明确修改的本地夹具，不冒充准确发布归档；实际 A/B SHA 在各 worker summary 中。外层资源限制和失败路径经过独立审查，所有所属容器删除后才清理自有 npm cache。公开附件：[rc8-fixture-delta.tar.gz](evidence/0010/rc8-fixture-delta.tar.gz)，94 个文件、287822 bytes，SHA-256 `62629dca8ff694f5599848cf0ee0137ec1ccae4db4eb792783769d4cb778f9ea`；含执行器/依赖 helper/镜像锁快照和各步骤日志。原始准确 tarball、A/B tarball 与失败证据保留在本地；安装缓存不进入公开附件。

## RC9 准确远端维护与 RC10 修复

RC9 源码 `7646ed8e50335644acf25210622e3b35a9c3289a`；准确 npm SHA-256 `06eb7aa07a7d90761dd2b5727d572849791f0191ba0f660c3ab0040921c5d395`，5,412,758 bytes。[三系统 CI](https://github.com/psiQAQ/planweft/actions/runs/34343026093) 与 [OIDC](https://github.com/psiQAQ/planweft/actions/runs/34343163686) Passed，真实下载匹配。Claude 官方兼容端点直连已获补充授权并执行，旧授权阻塞仅属历史。

| RC9 宿主 | 自动检查与独立核查 |
| --- | --- |
| Claude | 维护唯一计划 Failed；实际首次调用 Skill、随后读取解析/初始化说明，仍未初始化；也实际读取了范围外宿主设置。独立冷读 Passed，不弥补 owner 失败。 |
| Pi | 自动维护/冷读 Passed；独立发现最终 findings 仍有被后续实验推翻的 BOM 解释。手工 TemporaryDirectory 未记录实际路径，范围未知，不能写成已证实越界或 Passed。 |
| OpenCode | 历史记录字面断言 Failed，独立历史语义 Passed；实际创建并通配清理项目外固定临时路径，范围 Failed。冷读执行了 Git 检查却宣称没有任何命令级检查，归属 Failed。 |
| DSH | 历史标点触发自动 Failed，独立历史语义 Passed；实际读取了范围外 DSH 变量名，值均遮蔽，不能夸大为凭据泄露。测试执行时点/命令参数表述仍有精度问题。 |

原始记录、四份独立审查、CI/OIDC、Pi/OpenCode 跨 scope 重复注册基线见 [RC9 附件](evidence/0010/rc9-live-records.tar.gz)：352 项，SHA-256 `56b29de334b2eccaa6e41f920dd7ceeaa241a175973a2056b3a78c3a031b6014`。主 Agent 重算四份审查的 204 项附件摘要；归档保留原始/公开摘要映射、失败与前后项目快照，省略物理安装副本及可重建缓存。所有模型容器串行、结束后移除，基线服务保留。该归档不是稳定版 acceptance。

RC10 将六语言主入口收敛为四步，详细解释器/绑定分支继续引用原有随包选择文档；没有新增自动写文件 hook 或准备调度服务。保留只读不创建也不修改记录、明确禁令与旧权威例外；通用“最小修改”不构成禁令。要求实际复读最终当前断言及更正依据，并准确区分冷读所做检查和未重跑历史。独立源码审查见 [精简入口 review](../reviews/0010-rc10-compact-entry-review.md)，行为效果仍待新准确包复验。

跨 scope 修复及原生基线见 [安装器 review](../reviews/0010-rc10-cross-scope-review.md)：RC9 在已有全局原生加载源时，项目 dry-run 仍成功，Pi/OpenCode 两宿主都复现；未真正安装第二执行链。RC10 拒绝已知路径/配置的外国来源，仍允许已核验自有更新及同版本 OpenCode Skill 配对。离线修复通过不冒充新包真实双执行去重，任意自定义 loader 识别仍有边界。

### Codex 提醒的原生证据与解析更正

使用固定 Codex `rust-v0.149.1` 源码 `ff29a44391deccde0aba0f8390337d7f3c319ea4` 的 app-server 协议，在同一 thread 中发送两次严格串行 user turn。前一轮只有 PreToolUse、无成功 fileChange，目标文件未变；模型 DONE 不算修改或 hook 成功，原 Failed 保留。第二轮启用原始事件并在提示中补充夹具已知全文，这两项变化都记录，不能单独归因 matcher 或采集开关。

第二轮实际四次合法 apply_patch 成功，每次匹配原生 fileChange、调用/结果和 PostToolUse 身份。每轮 context 次数 `[1,0]`，两次真实 raw developer 消息各含一次提醒；仅目标两文件最终为 `B\n`。原始自动报告仍 Failed，因为收集器错误拒绝首次 turn/started 后、任何 user reset/tool 之前的初始 SessionStart。修正仅允许这一完整初始生命周期，并拒绝中途/重复/不完整、身份或状态改变等事件。20 项正负测试 Passed。

独立 reviewer 使用原始协议与修正后 parser 重算，派生去重语义 Passed；原 assessment/observation 未改，修复后准确包仍须新验收。review SHA-256 `76a930eb0c96611c48741871ec34951491d2e88878fc057f9e3c938b1abcadc4`，parser `d75e90cc078ebf80bca3445f42d597019035b910ea021a31c0eba7bb13b15b91`。主 Agent 重算其 12 项原始附件摘要。见 [两轮协议、固定官方源码和独立审查](evidence/0010/rc9-codex-reminder.tar.gz)：124 项，SHA-256 `c2c4fec6a72989fee1c64192c6aa1b87a45d4e724390bbffdc66b7946bf23d6f`。

RC10 开发回归：Python 219 tests Passed / 1 skipped，最终初始 SessionStart 守卫另以 20 tests 复验 Passed；安装器 64 tests、DSH shell 3 tests Passed。迁移上游 721 passed / 63 skipped / 851 subtests passed；固定原始上游未修改，既有基线保留。本次编译一致性、目录一致性 Passed；尚无 RC10 三系统 CI 或准确包模型结果。见 [开发日志](evidence/0010/rc10-development-regressions.tar.gz)，SHA-256 `327146c993583d4dfc01d3ed0f0f16c4ec5c20bd361072f3384533dcdb0b64be`。

公开前审计发现初稿附件误含 run/tmp 的 Node 编译缓存并命中私钥格式标记；已知认证值无命中。缓存没有证据职责，导出器排除 tmp 后保留 352 项有效文件及全部 204 项审查依据，修正尚未公开的末次证据提交。原始模型失败和本地审计失败继续保留，不用格式标记推断凭据泄露。

## RC10 发布、真实缺陷与 RC11 对照

RC10 干净 `e79e08548c31ed8833da032f68766b36078779f4` 重建与初次冻结归档逐字一致，SHA-256 `fed540a7a27d9ce8e58d8535bbd1479b612ca0db8e2e62df7b9e9d9e875e8114`，5,357,766 bytes。[三系统 Check](https://github.com/psiQAQ/planweft/actions/runs/34349393062) 和 [OIDC](https://github.com/psiQAQ/planweft/actions/runs/34350081143) Passed，官方 registry 下载及 integrity 匹配。一次默认 npm mirror 元数据查询在 URL 白名单检查处停止，随后显式查询官方 registry，不修改个人 npm 配置。

Claude 自动维护与冷读 Passed，初始化和实际填记录均先于实现修改；独立维护仍 Failed：禁读宿主配置实际送达、固定项目外 scratch 备份/恢复/删除、未执行旧测试却提前写为 Passed。后续新回归负向对照实际有效，不能回填旧测试执行时点。独立冷读正确报告历史结果与自身命令检查，维护后、冷读前后快照一致。独立审查 SHA-256 `998199a5d653d7a618b28a61d75d129bd07cbdec56ed9a6caa0ceb879d22c9d4`，主 Agent 重算75项附件。

Pi 维护在模型前被 doctor 阻止。原生 `0.84.3` 保存 `../.planweft/versions/0.4.0-rc.10/node_modules/planweft/dist/pi/planweft`，相对 `.pi/settings.json`；RC10 检测只豁免绝对字符串，产生真实新回归。独立冷读只读取未维护的合成项目，不计维护交接通过。RC11 修复保留 foreign scope 与重复条目拒绝；离线首轮68项中1 Failed，修正后68 Passed，独立扩展后76 Passed/1 Windows Skipped。准确新包与 Windows CI仍待执行。

上述准确发布、两宿主原始记录、75项独立依据及资源清理见 [RC10 附件](evidence/0010/rc10-claude-pi-records.tar.gz)：139项，SHA-256 `7dde0b677002d2eea41e1bd3a59606221d0274de8f29338ce72290886e8762f5`。只清理已结束且无容器引用的8个可重建目录，共328,284,755 bytes；准确归档、失败、快照与审查保留。

RC11 范围恢复修改沿用固定 PWF 选择器，实际纯函数对照2 tests Passed，覆盖末尾 Scope 遗漏、Goal保留、纯本地化 fallback 和混合标题丢失及 LF/CRLF。全量 Python 221 tests 的首次检查有1项分发不同步失败/1 skipped；安装说明生成同步后相关24 tests Passed，不抹去首次失败。安装器76 Passed/1 Windows skipped、DSH shell3 Passed、最终目录一致性 Passed。源码记录与真实宿主/稳定验收分开。

OpenCode 的一次新模型命令在启动前被自动审批拒绝，要求明确平台/端点/负载；用户随后补充授权隔离 OpenCode 直连 `https://api.deepseek.com/v1`，仅发送合成任务、测试提示及公开插件。此前拒绝保留；尚未执行的新模型场景不能计 Passed。

[RC11 开发回归日志](evidence/0010/rc11-development-regressions.tar.gz)：10项，SHA-256 `9161fac03944948b61d9f461c4e0bb6a7411d7752fa8f0b8528792ddc25695d0`。包含原始失败和修正后的相关检查，未把开发日志当作准确 npm 包验收。
