# ADR-0007：按宿主生成目录并使用原生更新渠道

状态：Accepted；日期：2026-09-08；需求：[SPEC-0004](../specs/0004-native-distributions.md)。用户已批准本地实施和发布准备，公开发布仍不在本轮范围。

## 问题与决定

0.2.0 的 ZIP 可以保存版本快照，但解压本身不记录可更新来源，多数安装仍需复制文件、合并配置并清理旧文件。新增 marketplace 只有在宿主识别其协议且能取得完整 payload 时才解决更新问题。

采用一个构建入口生成 `dist/<host>/program-design/`，各宿主选择原生安装协议。Codex、Claude、Cursor、Copilot、Factory、CodeBuddy 使用各自 catalog；Pi/OpenCode 使用原生包；Gemini 使用 Extension；Hermes 使用插件与配套 Skill；Kiro 使用 Power；其余保留文件安装。默认显式更新，不增加统一更新守护进程。

| 方案 | 取舍 |
| --- | --- |
| 继续只交付 ZIP | 离线保存方便，但不能单独满足原生安装及持续更新；不作为默认输出 |
| 目录产物与宿主原生渠道 | 安装根直接可检查，版本由各宿主管理；需要维护不同入口和真实安装验证；采用 |
| 自研统一 marketplace 和更新器 | 各宿主不会因此获得相同协议，增加配置迁移与状态管理范围；不采用 |

## 分发与版本约束

普通构建不联网、不公开发布，继续从固定 PWF 快照与本地 overlay 生成。源代码保留原生语言；OpenCode 的 V1 入口在维护者侧预编译，普通安装不依赖 TypeScript 编译工具。Codex 的 `plugins/program-design/` 作为兼容镜像保留；六种 catalog 指向各自目录，不能共用一个 payload 假定 hooks/API 等价。

Git marketplace 中的目录必须真实存在于发布提交；不能只上传一个带相对路径的 HTTP JSON。Gemini/Hermes 采用专用发布分支，使相应包成为分支根；Gemini 要求根 manifest，Hermes 子目录安装搬移后不保留 `.git`，包根发布保留原生 updater 所需仓库；npm 发布包具备独立 `files` 清单与来源许可。发布准备仅生成可审查的目录和命令，不执行 Git push、npm publish 或用户全局安装。没有真实远端身份时不输出已发布结论。

更新以插件管理器的显式命令为默认入口；用户自行决定是否开启宿主自动更新。版本号、Git commit/ref 与包管理器缓存含义分别记录。更新插件文件不迁移任务数据，也不代替 hooks 信任、重新加载和实际运行检查。

## 依据与能力边界

- [Gemini 发布指南](https://geminicli.com/docs/extensions/releasing/) 支持 Git 分支与发行资产，要求根 manifest，并分别说明 Git、Release、本地来源的更新检测。发布分支是本仓满足根目录要求的实现选择。
- [Factory plugins](https://docs.factory.ai/harness/plugins) 支持原生 catalog、相对路径及 `git-subdir`，区分 marketplace commit 与 manifest version；[CodeBuddy marketplace](https://www.codebuddy.ai/docs/cli/plugin-marketplaces) 提供 Git catalog 与原生更新，不能用 HTTP catalog 的相对路径替代完整代码分发。
- [Kiro Power 创建](https://kiro.dev/docs/powers/create/) 明确允许 skills-only Power；[CLI v3](https://kiro.dev/docs/cli/v3/new-features/#powers-auto-pickup) 自动发现 IDE 安装的 Power。采用原生 UI 安装和更新，不发明 shell 管理命令。
- [Continue CLI Skill loader](https://github.com/continuedev/continue/blob/main/extensions/cli/src/util/loadMarkdownSkills.ts) 与 [导入实现](https://github.com/continuedev/continue/blob/main/extensions/cli/src/tools/skills.ts) 分别证明文件发现和模型辅助复制；未提供本项目可依赖的原生持续更新器。
- 其他宿主的官方来源、scope 与命令登记于 [平台矩阵](../platforms.md)，安装结果单独验证。PWF 适配源码是移植依据，不替代宿主协议文档。

## 后果与验收

该决定只替代 ADR-0006 中 ZIP 交付与旧安装入口的安排，固定上游、状态兼容、按需文档维护和只读边界继续有效。Factory/CodeBuddy 先采用 Skill 包装；拥有 plugin manifest 不代表新增执行 hooks 已验证。Kiro、Continue 等较窄能力仍据实说明。

维护成本由生成器、目录清单校验、原生 manifest 检查、npm 内容检查及隔离安装/更新验收承担。历史 0.2.0 证据保留，0.3.0 新链路独立记录；本地准备成功不等于公开发布或全部宿主运行通过。
