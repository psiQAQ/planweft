# PLAN-0005：PWF 底座与多平台插件 0.2.0

状态：Complete（本轮实施与可得环境验证已交付，平台限制另列）；日期：2026-09-08。需求来源：用户明确批准的 Program Design 0.2.0 实施计划。

## 目标与边界

以 PWF v3.17.0（`0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`）为固定底座，交付独立、自包含的 program-design 0.2.0 平台分发。保留原生多语言运行时、状态协议与平台适配；默认任务自动匹配与 advisory 模式，附加按需文档、依据与交接维护。

成功标准：源码来源可核查、构建可重复、移植与本地增量有回归、可用宿主隔离试用及冷读有真实证据、不可用平台明确 Not Run。原研究子模块及历史保持不变；不推送、发布、全局安装或正式自身接管。本计划按本仓库已有文档流程维护，不初始化 PWF 根计划。

## 阶段

- [x] 固定源码与基线测试，记录原始失败。
- [x] 新规格/ADR，身份映射、构建和全量平台分发。
- [x] 整合文档规则、模板和本地行为回归。
- [x] 上游/移植/分发测试及隔离宿主试用。
- [x] 独立依据审查、冷读、验证说明与交付。

## 当前进展与下一步

已检查初始工作区干净，基线为 `2dca0f6`；独立分支 `feat/pwf-based-plugin-0.2`。已核验固定 tag/commit 并导入 699 文件完整快照；生成 14 平台包及 Codex 工作目录，确定性生成检查通过。PWF 原始基线在隔离环境下 pytest 721 Passed / 63 skipped、Pi 54 Passed、OpenCode 34 Passed 及 typecheck/build Passed。

最终GNU工具环境中原始/移植pytest均721 Passed、63 skipped，迁移851 subtests；Pi54、OpenCode34及typecheck/build Passed。本地25 tests、13项独立入口合同、确定性构建与14包完整性通过。真实Codex第三轮自动读取主Skill并采用唯一PWF计划、重定向旧入口、完成维护与独立冷读；最终包另经无模型安装/缓存/卸载验证。独立审查发现均已修正或作为平台差异明确披露。

交付入口：[安装与兼容](../platforms.md)、[分发清单](../../dist/manifest.json)、[验证结果](../reproduction/0005-pwf-based-plugin.md)、[完整证据](../reproduction/evidence/0005/README.md)、[来源与维护](../upstream-maintenance.md)。当前无需继续本轮实施；后续若要真实Windows/macOS/其他宿主验证、公开发布或自身接管，应作为相应范围的新工作。

限制：本机uutils mkdir0.8.0并发原语失败，需已验证GNU环境；真实gated循环及其他宿主/OS Not Run；语言变体原生implicit策略已安装，API不直接暴露策略执行；一次证据缺口样本的引用格式失败保留。细节以REP为准，不把这些限制转换为通过。

## 错误与处理

| 观察 | 原因与处理 |
| --- | --- |
| 默认 sandbox 下 git clone 报 failed to open socket: Operation not permitted | 网络限制；按已授权范围升级为下载公开固定版本到临时目录，不修改项目 remote |
| 原始 pytest 首轮部分注入为空、找不到 python | 使用可写的独立 XDG_CACHE_HOME 和 venv PATH 后全量通过；保留原输出，不算上游缺陷 |
| 移植首轮测试大量身份/枚举错误 | 测试快照建立独立 Git index，并对命令、Skill 名及版本做明确身份映射；未删除上游回归断言 |
| 多语言 description 的 JSON escape 被 re.sub 当替换指令 | 使用 callable replacement，保留原始能力披露并附加本地规则 |
| Hermes旧缺脚本fixture在补齐包后失效 | 保留合法bundle fallback，再用孤立bridge测试真正缺脚本；原始测试不变 |
| 并发phase测试间歇丢状态 | 原始上游亦复现；独立mkdir探针与源码定位到uutils0.8.0错误成功语义，GNU9.7对照通过，不重写锁或替换系统工具 |
| 前两轮维护只更新旧计划 | 去除夹具环境误限制后仍复现；明确复杂实施即任务采用、先承接状态再改旧指针，第三轮通过 |
| Codex语言变体只有Claude显式标记 | 真实skills/list发现全部6项，补5个Codex原生implicit=false配置；保留主入口true |

验证及发现保存到本轮 reproduction 和设计依据记录；完成后本计划链接最终证据。

## 后续提交整理与安装说明补充

用户后续要求按功能边界分批提交、合并本地主分支，随后明确暂不push，并要求解释及落实不同Agent的安装方式。保留14平台生成分发；README新增选包表与根目录布局说明，包内安装说明同步增强。独立安装审查发现虚构发布源、OpenCode分发loader和Gemini路径/执行位问题，已统一修复并通过29项本地回归、原始/迁移各13项Skill检查、当前精确Codex包无模型安装/卸载预检。来源差异与验证限制见REP-0005安装补充；本仓库仍未正式自身接管。
