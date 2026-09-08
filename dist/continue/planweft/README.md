[简体中文](README.md) | [English](README.en.md)

> 当前安装包：**continue**。请选择本文对应宿主的安装章节。

# PlanWeft 0.3.0

PlanWeft 是面向 AI Agent 的文件规划与项目文档协作插件。它以 [planning-with-files v3.17.0](https://github.com/OthmanAdi/planning-with-files/releases/tag/v3.17.0) 为底座，在当前任务的规划、记录与恢复流程上，附加长期文档维护、设计依据审查和可复核交接。它是独立衍生插件，固定上游提交为 `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`，保留 MIT 署名与许可。

**安装、更新、回退与卸载：**[简体中文](INSTALL.md) | [English](INSTALL.en.md)。请按当前包标明的宿主选择章节。安装包是运行资源的来源；目标项目是任务记录的存放位置。

## 工作方式

主 Skill 为 `project-docs`。支持的宿主可在实质实现、维护和文档续接任务中自动匹配，也保留显式调用。自动匹配不要求项目预先启用，但实际加载由宿主决定。阅读与诊断请求保持只读；简单任务不强制建立计划层级；项目规则和用户范围优先。

复杂实施沿用一个选定的 PWF 计划目录。`task_plan.md` 管理当前状态与下一步，`findings.md` 保存发现和来源，`progress.md` 记录操作及实际验证结果。既有规格、ADR 和复现记录承接稳定需求、设计决定与证据；只有任务需要时才创建或最小更新。

重要设计交给独立依据 reviewer 核查；重要交接让未读取旧聊天的新读者从项目文件检查。使用宿主现有 Agent 能力，不增加调度服务。具体指导见主 Skill 的 `references/evidence.md`。

## 运行边界

- 默认提醒模式。Autonomous、gated 是显式选择，行为取决于宿主；Skill 匹配本身不会开启自动续跑。
- 辅助命令采用 `pw-` 前缀，OpenCode 工具采用 `pw_` 前缀。可用命令以当前适配器为准；`PLAN_ID`、`PWF_*`、`PLANNING_DISABLED` 与 PWF 状态格式保持兼容。
- 严格只读会话使用宿主的关闭机制。`PLANNING_DISABLED=1` 仅在已验证的适配路径上作为充分开关；不保证自动识别所有自然语言只读意图。hooks 私有缓存与项目记录分别管理。
- 同一会话只启用一个规划插件的执行 hooks。通过 doctor 和当前宿主配置检查可检测的重复项；安装本插件不会自动卸载 PWF。
- 自动恢复只读取项目文件。会话历史的 metadata 或有界 replay 需要显式请求。
- Attestation 校验文件内容，不代表人工批准；gated 检查运行状态，不证明需求或代码正确。

## 分发与来源

源码仓库为 14 个宿主生成独立的 `dist/<host>/planweft/`。各包包含对应适配所需的运行时、模板、参考资料、`LICENSE` 和 `UPSTREAM.json`。安装与更新使用各宿主的原生渠道；不生成平台 ZIP，也不承诺不同宿主具备相同 hooks 能力。Factory、CodeBuddy 与 Kiro 提供 Skill 包装；Kiro 在 IDE 管理 Power，CLI v3 自动发现 IDE 已安装的 Power。

默认显式更新。刷新 marketplace、更新插件、重载会话与信任变更后的 hooks 是不同操作；本地路径安装需要保留来源目录。已准备的 Git/npm 坐标不等于已公开发布。验证分别记录静态检查、协议测试和真实宿主结果；未运行的环境记为 Not Run，失败保留实际结果。详见[安装说明（中文）](INSTALL.md) / [Installation guide (English)](INSTALL.en.md)。

包更新和卸载保留目标项目的计划与证据。项目正式采用本流程时，一次性把旧活跃计划的状态入口转向 PWF 计划并保留历史，不实施双向同步。构建和发布准备不会安装插件、改写个人配置、push 或发布 npm 包。
