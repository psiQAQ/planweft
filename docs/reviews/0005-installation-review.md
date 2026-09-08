# Program Design 0.2.0 安装补充审查

日期：2026-09-08。审查者：独立 installation_audit subagent。

范围是安装材料、生成包的发现路径，以及 Gemini 命令在本地 Shell 中的协议行为。本次没有安装真实 Agent 宿主、联网、运行模型、修改用户全局配置或研究子模块。主 Agent 修改构建与安装材料；审查者独立编写安装回归并复核生成包。

## 结构判断

保留按平台生成 ZIP 的结构，不要求在本仓库根展开所有 Agent 的隐藏目录。固定 PWF 归档中的 `scripts/sync-ide-folders.py` 以 canonical Skill 为源同步共享资产，但保留各平台专有的 Skill frontmatter、hooks、prompts 和 package.json。本仓库的 builder 将这些安装表面放入对应分发，安装时才部署到目标项目或用户配置目录。

14 个 ZIP 对应不同平台；Pi 将原 `.pi/skills/project-docs/` 展平为 package.json 所在的安装包根。`agents` 提供通用 Skill 发现表面，不构成所有宿主共享的 hooks 实现。这种布局便于统一生成，也避免将本开发仓库直接变成各宿主的运行配置；代价是多数平台需先选包并解压。

README 已增加完整选包表、Pi 本地安装示例和布局解释；[平台安装说明](../platforms.md) 区分源码仓库、解压安装源、目标项目及用户配置，并覆盖配置合并、激活、卸载和平台差异。

## 发现与处理

| 发现 | 原始观察 | 处理及复核 |
| --- | --- | --- |
| 身份替换虚构远程安装源 | canonical、Agents、Pi、Hermes、OpenCode 的安装材料出现 `OthmanAdi/program-design`；OpenCode 还把本地包描述为已发布 npm 插件 | builder 将这些安装片段替换为本地 ZIP 路线，保留正常上游来源链接和本地 package name；扫描全部 14 个 ZIP 的 Markdown、配置及安装入口通过 |
| OpenCode 分发仍需手写入口 | 包内继承开发入口加载 `src/index.js`，而用户安装文档要求另建 `dist/index.js` 入口 | 分发入口直接 re-export 编译后的 `dist/index.js`；完整移植源码树保留开发入口。package.json、tsconfig、源码与 loader 的静态输出契约通过；包内 README 和 INSTALL 均指导 `npm ci --ignore-scripts`、`npm run build` |
| Gemini 项目路径未引用 | 中文加空格的项目路径被 Shell 拆词，5 个事件全部退出 127，错误为路径在空格处截断后的 `not found` | 路径增加双引号；继续执行暴露下面的文件权限问题 |
| Gemini 直接执行没有执行位的脚本 | 固定上游及 ZIP 中 5 个 hook 脚本均为 `0664`；仅增加引号后，按 ZIP 原始 mode 解压的 5 个事件全部退出 126，错误为 `Permission denied` | 配置改为显式 `bash "$GEMINI_PROJECT_DIR/.gemini/hooks/<name>.sh"`，保留原脚本 mode。测试没有额外添加执行位；5 个命令均成功关闭并返回 `{}` |

OpenCode 包内 README 的品牌链接已明确为派生自上游，其 commands 来源改为解压后的 OpenCode ZIP，避免再次让读者寻找本仓库根中不存在的 `.opencode/`。

## 回归证据

新增 [test_pwf_installation.py](../../tests/test_pwf_installation.py)，执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_pwf_installation.py' -v
```

| 阶段 | 结果 | 解释 |
| --- | --- | --- |
| 修改前首次复现 | Failed：3 个测试中报告 6 次 failure | 1 次安装源扫描失败包含 21 个「文件 × 问题类型」命中；另有 Gemini 5 个事件的 127 subtest failure。此阶段仅保留会话工具输出，本文为摘要，不声称存在原始落盘日志 |
| 修复安装文案并仅给 Gemini 路径加引号 | Failed：4 个测试中报告 5 次 failure | 安装源、平台入口及 OpenCode 构建契约通过；Gemini 5 个事件均为 126。退出日志另存，确认问题来自原始 mode，不推断为 `noexec` |
| 显式 Bash 入口并重建 | Passed：4 个测试，1.255 秒，`OK` | 按 ZIP 原 mode 安装后执行 settings 中全部 5 条真实命令；临时项目目录含中文与空格，stdin 为 `{}`，环境为 `PLANNING_DISABLED=1` |

最终 Gemini 协议检查验证每条命令退出 0、stderr 为空、stdout 是 JSON `{}`；目标项目中预先存在的三文件及所有目录、文件字节和 mode 均未改变，独立私有缓存目录也没有写入。一次额外 `chmod` 诊断曾用于确认权限原因，但最终测试已移除该处理，不以诊断通过作为安装包通过的证据。

安装表面检查还覆盖：

- 14 个平台的原生入口和所需 Skill、脚本、模板、依据说明存在；Copilot 从 canonical Skill 复制到 `.github/skills/project-docs/` 的映射明确。
- Claude 与 Codex ZIP 的 marketplace source 均为 `./` 并对应包根；Pi package.json 声明的 Skill 和 Extension 确实位于包根。
- 五个语言变体均带显式调用限制；Codex 另有五份原生 `allow_implicit_invocation: false`，Claude 的 13 个 `pd-` 命令均限制隐式调用。其他宿主的推荐复制路线只复制其主 Skill。

## 结论与限制

本轮发现的安装材料和 Gemini 命令启动问题已修复，最终安装回归通过；没有发现需要把所有宿主隐藏目录重新放到仓库根的理由。

静态入口和 Shell 协议检查不能证明真实宿主已经安装、发现 Skill、注入上下文或完成任务。本次 OpenCode 只核对编译输出契约，没有重新安装依赖或运行 TypeScript 编译；未运行 Gemini 的非关闭行为、真实 Gemini 会话及 Windows/macOS。既有真实宿主证据与限制继续以 [REP-0005](../reproduction/0005-pwf-based-plugin.md) 为准。
