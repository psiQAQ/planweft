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
