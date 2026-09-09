# PLAN-0010：五 Agent 验收与正式发布

## 当前状态（唯一当前入口）

实施中，正式 `0.4.0` 未发布。RC15 已发布至 npm `next`；历史 `latest=RC1` 不代表稳定版。RC15 已冻结源码 `4fa210fa767df81e44a815b0e6ff98926b5e976f` 与准确归档 SHA-256 `3cdb78d2c001278d61f28fb23f6233eacf39a371c462c32622c39ab6dd8c8b45`，三系统/分发CI `34387525440`、OIDC `34387986832` 与官方远端准确字节均Passed。新六语言入口选择、按名查变量及单独环境门槛已独立审查，41项定向测试/134子场景、301项完整Python测试（1 Skipped）和构建一致性通过；依赖69个非根条目不变。RC14四宿主独立总体均有范围或记录缺口，不能以自动Passed放行；详见[RC15检查点](../reproduction/0010-rc15-checkpoint.md)。RC15 Claude完整新Skill后仍读取禁止settings；Pi实际未读Skill/未采用计划并用项目外手工scratch；OC自动维护/冷读Passed但独立记录Failed，两份已有文档修正/新冷读独立Passed，但owner末答将本轮pw_check误归历史单列Failed；DSH自动Passed但独立环境枚举和findings准确性Failed。Claude RC14真实逐Write输出去重及原生消费已独立Passed，特定提醒的模型投递NotRun。Codex完整停止采集修复高层/raw顺序和hook配置ID代次，51测试及独立8追加反例Passed；原流离线独立确认正常停止/关闭对照/实际续跑，新停滞退出与对照含卸载独立Passed。原Failed/中断/未执行卸载保留；gate-cap仍有未完成syscall归因缺口，不能整体放行。Claude RC15无工具上下文/恢复及SessionStart来源独立Passed（95附件），UPS不能单独归因。已经向用户提出是否允许对未通过DeepSeek宿主做预先声明的Pro对照，未答复前不改变固定Flash配置；其余验收继续。

RC14 已通过 OIDC 发布到 npm `next`，官方 registry 下载字节与准确本地归档一致。独立审查后的六语言采用分支和中英本地操作例程已生成全部15平台；初次 CI Windows 默认 cp1252 读取中文失败，已用显式 UTF-8 最小修复，保留原失败。新冻结源码 `6e54876bf6249bb1d83514767920fdeb793f3573`，准确归档 SHA-256 `9ecfd09b82d118a99f7593fa3fcd948234a334ac11f7c2e06d63e446e693b85a`；旧 `2c96af78` 归档已排除发布，不覆盖历史。新三系统安装器、例程和 distribution Check `34382490295` 全部通过，OIDC `34383018444` 通过，远端包 5,462,803 bytes；SHA-256/SHA-512/SHA-1 均与预期一致。公开审计4个新提交、88个去重blob、4325个递归payload、7个已知凭据匹配检查无发现。

Claude 新增仅供诊断的私有进程追踪：独立审查初始7类对抗反例修复后均拒绝，65项定向回归及86个子场景 Passed。冻结源码的无模型实际七hook预检已绑定脚本读取、输出通道与EOF，四次 PostToolUse 实际字节为187、0、187、0；旧缺少插件ROOT及误拒普通pread读取的两次预检保留。该结果不证明真实 Claude 模型投递／去重，真实 RC13 traced diagnostic 已完成两轮四次Write且通过独立收集核查，但归因 Incomplete：实际native init加载受管marketplace payload，旧测试器绑定cache；另有创建来源未捕获的线程read返回?。已经补正确来源与会话路径绑定（41项定向回归通过），随后补采FD创建事件，独立审查36测试+5额外反例通过，受控inotify/Netlink/close复用解析完成；同一无模型轨迹原Incomplete和新Complete并存。新RC14真实trace collection Passed、13个hook归因Complete，4次PostToolUse实际187/0/187/0写读一致且EOF；模型投递/逐Write绑定仍交独立审查，不因宿主读到字节直接认定模型收到。RC14 Claude 自动维护/冷读检查均Passed，但独立语义总体Failed：完整Skill加载后成功读取禁止的`.claude/settings.json`且最终否认；记录另有hex抄写及首次0 tests遗漏。默认采用、修复/反事实回归、项目内scratch及独立冷读分别有通过证据，不抵消范围越界。已补已知直接配置文件调用反例检测（不能替代shell/间接访问独立核查）；Pi/OpenCode/DSH 该组已完成：Pi/OC有无关安装资料读取，OC还保留当前过期事实；DSH功能与记录通过但env枚举违反范围。原自动结果和独立结论分别保留。追踪原文只在私有临时目录，导出限额数字／摘要后删除；元数据预算按实际预检从32KiB改为256KiB并增加超限反例。

- 用户授权的直接依赖 `toml@4.3.0` 已落地，69 个非根 lock 条目完全不变。干净 npm 安装后的安装器 123 Passed / 1 本机 Windows Skipped、Python 228 项（1 Skipped、无失败）、构建一致性 Passed。RC13 三系统 Check `34371767391`、OIDC `34372409182`、公开审计和远端准确字节校验均 Passed。
- RC13 五宿主准确原生 preflight/lifecycle 均 Passed；此组仅为同版本更新与卸载，不冒充两版本升级/回退或模型门槛。Codex 自有来源校验缺陷已通过准确新包实际修复，RC12 原失败和额外诊断保留。
- 真实 npm RC4 → RC13 → RC4 → RC13 → 卸载五宿主均 Passed，Pi/OpenCode/DSH 另有原生 npm 入口/配对资源检查。该组不含模型会话或公开 Git marketplace；RC4 为历史已验证可用的旧版基线，RC10 的已知缺陷不撤销。正式版仍须另行执行 RC13 ↔ 稳定版全流程。
- RC13 Codex 原三模型边界的自动结果均 Passed，但旧独立报告仍 Incomplete：提醒去重有原生序列，权限拒绝有保护文件证据（使用 hook trust bypass，不能计持久信任）；旧高层 exec 流不能排除 code-mode 工具。新完整 app-server 采集已独立 Passed：原生 TUI 授权前无上下文，授权后 SessionStart/UserPromptSubmit 输出进入模型上下文，第三个新进程/线程只从项目文件恢复 owner 的新值。三次都无模型工具；旧失败不改写。其他依赖高层流的停止/无工具断言仍须补齐原生证据。
- Claude 双回合采集器修复并经独立审查：12 项采集器、25 项执行器离线测试 Passed。首轮真实 Failed 保留；修复后原生四次 Write、两回合请求绑定及私有日志清理通过独立采集审查。外层汇总因 replay 字符串误当 content blocks 崩溃，原 summary 仍 Incomplete；已最小修复，使用原始事件离线补充评估，不重跑模型。Docker 退出码未保留，不从 controller Passed 推断。去重仍为 Not Run：原生日志不能明确证明每次匹配 hook 的空 stdout；两条 matcher 日志不等于两个插件。无引用的遗留版本缓存清理另有记录。
- RC12 OpenCode 维护仍 Failed、冷读 Passed（有限制）；历史精确字符串原断言为误报，但旧 notes 独立当前状态、findings 过期事实和 progress 漏记错误是实质缺陷。RC11 四宿主维护及原始失败保留。无新因果干预时不重复模型任务挑选成功，不以显式调用替代自动匹配。
- 原生信任/权限、各宿主去重与续跑、维护/交接、准确稳定包和远端全门槛仍未完成。不提升 latest 或创建正式 Release。已有发布、模型直连和直接依赖授权不重复询问。

资源：模型/重型容器串行，2 CPU、3 GiB 内存且无额外 Swap、256 PID、单场景600秒；启动前检查4GiB可用RAM和8GiB磁盘。只清理已结束且无引用的本次缓存，保留准确包、失败、项目快照和历史备份，不改其他服务。此前保留的 RC12 parser 开发缓存已在实际直接依赖安装通过后验证无引用并释放 104,680,735 bytes；远端成功场景按记录清理自有 npm/CLI bootstrap 缓存。本仓继续现有文档入口，不做根三文件接管。

证据与逐项来源：[REP-0010](../reproduction/0010-five-agent-release.md)、[独立审查](../reviews/0010-five-agent-release-review.md)。

## 已批准实施顺序与阶段历史（非当前状态）

状态：实施中。用户确认五核心门槛、隔离备份后脱敏公开历史、优先复用现有模型服务。

1. 历史：备份原始 refs；隔离清理 reproduction 证据，复核提交/文件映射后以明确 lease 更新 master。
2. 验收：固定五镜像，隔离入口；先证明无外部记忆，再运行真实模型。准确归档和合成 A/B 分开记录。
3. 发布门槛：五平台安装、注入、恢复、停止、维护、冷读、权限与独立审查；提升 latest 前增加远端多版本。
4. 发布：首个 RC、OIDC RC、准确 stable 归档、next 远端验收、latest 与 Release。不可覆盖已发布版本。

边界：不运行会清理记忆的旧 Lab 回归、不修改现有服务/个人全局配置、不采用本仓根三文件。
公开历史已脱敏并推送，映射见 REP-0010；npm RC1 已发布且远端字节一致，GitHub trusted publisher 已配置。旧 PLAN-0008 的未推送状态已过时。
原镜像锁中的 DSH 版本早于当前适配依赖；实际 CLI 版本以容器预检为准。

验证结果与剩余项在 REP-0010 汇总，未执行项不得提前标 Passed。

当前下一步：冻结 RC3 DSH 沙箱修复，完成准确归档模型复验，再测试远端两版本。RC2 已由 OIDC 发布，远端字节一致，OpenCode 九项场景和独立冷读通过；Pi context/recovery 复验通过；DSH 启动通过但上下文与维护失败，原始失败保留。Pi/DSH 直连合成模型验收已获明确授权，通过仅含官方 URL/key 的私有临时输入隔离。三系统安装器 CI 已通过。阶段 1 完成，阶段 2/3/4 部分完成；正常停止、权限、准确稳定归档和远端门槛仍需补齐。首次发布意外生成 latest，认证后删除请求仍返回 HTTP 400；保留失败，不将其视为稳定发布。

2026-09-09 接续：RC3 尚未发布。DSH 原生注册与上下文已修复并实际通过；通用维护采用边界澄清须新准确包维护复验。Pi/DSH 停止有实际证据，Claude cap/stall 来源归因、Codex/OpenCode 停止、最终稳定准确包与远端门槛仍待完成。现有失败及后验更正在 REP-0010 保留。

后续实测：DSH flash/pro 在 `5fb24d0` 包仍未创建唯一 PWF 计划，完成独立 Skill 路由审查并修正具体歧义，下一步冻结新准确包复验。OpenCode 默认与 cap/stall 通过，gated 后续回应未观察到；继续检查真实 CLI 的事件收集边界。Claude 进程归因离线反例与实际脚本通过，直连模型的新命令因自动审批要求明确服务/负载授权而暂未执行。稳定版不放行。

最新：RC3 `09ea0e4d` 已 OIDC 发布/远端字节一致，五容器本地安装和三系统 CI 通过。OpenCode 六项原生 server 停止观察及独立审查通过；远端仅其原生 npm 入口失败（缺 ./server/main），准备 RC4 最小修复。其余四宿主 RC2↔RC3 远端生命周期通过。DSH flash 文档准确性与 Pro 计划采用仍失败，不标记总体维护通过。Claude 更正后的 DeepSeek 官方兼容端点补充授权仍待答复；最终稳定准确包与远端模型门槛未完成。

2026-09-09 RC4：`1d1c76c` 已 OIDC 发布，远端准确摘要 `c6f54319` 匹配，五容器本地安装/生命周期和三系统 CI 通过。真实 RC3↔RC4 远端生命周期正在运行；Codex 前六项自动检查通过，停止两项因服务额度耗尽失败，保留原始记录。继续 Pi 远端准确归档模型验收及独立冷读审查。Claude 明确端点授权、DSH 维护失败与最终稳定门槛仍未解决。


当前验收状态（RC4）：五宿主真实 npm RC3↔RC4 升降级/卸载 Passed；Codex/Claude 公开 Git 同提交刷新 Passed。Codex 维护独立审查 Passed、停止遇额度限制；Pi 默认停止和显式三次续跑 Passed，完成态注入/恢复 Passed，但首次计划一致性 Failed，准备独立反馈修正；OpenCode 默认停止/续跑 Passed、维护历史保留的字符串误报已独立澄清，但冷读验证限制准确性 Failed。DSH 准确远端包模型组正在执行。保留首次失败，尚无稳定 acceptance 清单，不提升 latest。

DSH RC4 组已完成：注入、恢复、只读、简单任务、停止与续跑 Passed；代码维护与历史保留独立审查 Passed，记录阶段/工具错误完整性 Failed。Pi 和 DSH 均进入有原失败绑定的 review反馈纠正路线；不直接重复原prompt碰运气。

Pi 反馈闭环已独立 Passed（仅指定 R1/R2 修正与新冷读，保留首次 Failed）；DSH 首次反馈受新 collector 的错误日志来源影响而未启动冷读，实际 R1/R2/R3 修正通过独立核查，已修正 collector 并补11项回归，正在新目录验证。最终完成前仍须准确稳定归档全门槛、Codex可用额度、Claude明确端点授权及OpenCode冷读准确性问题处理。
