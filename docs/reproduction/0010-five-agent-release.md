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
