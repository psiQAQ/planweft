# Program Design

研究并构建面向 Agent 的本地项目文档管理工具：持续维护长期知识、当前任务、设计依据和验证结果，供新会话和人类读者使用。

Program Design 0.3.0 固定使用 PWF v3.17.0，提供 `project-docs` Skill、文件规划与恢复及宿主适配。默认构建输出 **14 个 `dist/<host>/program-design/` 目录，不再打包 ZIP**；支持的宿主采用原生插件入口与更新渠道。目录格式、安装命令和真实宿主验证是不同层级，具体见 [平台矩阵](docs/platforms.md)。本仓库继续使用现有文档入口，没有正式自身接管。

## 从哪里开始

| 需求 | 入口 |
| --- | --- |
| 理解本次分发变化 | [0.3.0 规格](docs/specs/0004-native-distributions.md)；[架构决定](docs/adr/0007-native-distributions.md) |
| 理解继承的运行时 | [PWF 底座规格](docs/specs/0003-pwf-based-plugin.md) |
| 安装、更新或卸载 | [平台矩阵](docs/platforms.md)；[完整安装说明](overlays/program-design/install/INSTALL.md) |
| 检查生成文件和摘要 | [分发清单](dist/manifest.json) |
| 构建、同步上游及准备发布 | [维护流程](docs/upstream-maintenance.md) |
| 运行回归及查看验证分层 | [测试说明](tests/README.md)；[0.3.0 实测与限制](docs/reproduction/0006-native-distributions.md) |
| 接续既有项目文档工作 | [配对维护计划](docs/plans/0004-paired-maintenance-trial.md) |
| 阅读文章与参考实现 | [资料索引](docs/reference/README.md) |
| 核查设计依据 | [引用台账](docs/design-references.md)；[创新记录](docs/innovations.md) |
| 查看历史实验 | [0.2.0 结果](docs/reproduction/0005-pwf-based-plugin.md)；[0.1.0 试用](docs/reproduction/0004-paired-maintenance-trial.md) |

## 本地构建

正常构建只需 Python 3 标准库，从固定快照及本地扩展生成，不联网，不读取研究子模块或个人插件缓存：

```bash
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

生成物包括平台目录、原生 catalogs、`dist/manifest.json` 及 Codex 兼容镜像 `plugins/program-design/`。修改 `overlays/program-design/`、运行时适配源或构建脚本后重建，不逐份编辑生成物。OpenCode 使用预编译 V1 入口，普通用户无需编译 TypeScript；维护者修改其源码时，按 [维护流程](docs/upstream-maintenance.md) 刷新并验证编译产物。

## 安装到不同 Agent

从源码 checkout 构建后，选择对应目录。下面的目录是安装源，目标项目另行指定；完整的安装、scope、更新和信任步骤见 [INSTALL.md](overlays/program-design/install/INSTALL.md)。

| 宿主 | 安装目录 | 原生安装表面 |
| --- | --- | --- |
| Codex | [codex](dist/codex/program-design/) | 仓库 `.agents/plugins` marketplace；保留旧 Codex 镜像 |
| Claude Code | [claude](dist/claude/program-design/) | `.claude-plugin` marketplace 或单次 `--plugin-dir` |
| Pi | [pi](dist/pi/program-design/) | pi-package，本地路径或发布后的 npm 包 |
| OpenCode | [opencode](dist/opencode/program-design/) | 预编译 V1 插件，本地 loader 或发布后的 npm 包，配套 Skill 单独发现 |
| Hermes | [hermes](dist/hermes/program-design/) | 原生 Python 插件与同版本 Skill |
| Cursor | [cursor](dist/cursor/program-design/) | `.cursor-plugin` marketplace 与插件目录 |
| Gemini CLI | [gemini](dist/gemini/program-design/) | Gemini Extension，本地目录或专用发布分支 |
| GitHub Copilot | [copilot](dist/copilot/program-design/) | `.github/plugin` marketplace 与原生插件 |
| Mastra Code | [mastracode](dist/mastracode/program-design/) | `.mastracode` Skill 和原有 hooks 配置 |
| Kiro | [kiro](dist/kiro/program-design/) | skills-only Power，IDE 安装更新，CLI v3 自动发现 |
| Continue | [continue](dist/continue/program-design/) | CLI Skill、IDE Prompt；导入不提供持续更新记录 |
| Factory / Droid | [factory](dist/factory/program-design/) | `.factory-plugin` marketplace，最小 Skill 插件 |
| CodeBuddy | [codebuddy](dist/codebuddy/program-design/) | `.codebuddy-plugin` marketplace，最小 Skill 插件 |
| 通用 Agent Skills | [agents](dist/agents/program-design/) | `.agents/skills`，依赖宿主支持该发现路径 |

例如，在目标项目内注册 Pi 本地包：

```bash
cd /path/to/target-project
pi install -l /path/to/program-design-repository/dist/pi/program-design
pi list
```

Pi 本地安装记录源路径，应长期保留该目录。重启或 `/reload` 后检查 `/skill:project-docs`；`/pd-plan-execute` 才显式启用其执行流程。其他宿主的 catalog 注册源使用本仓库根目录，不能把不含 catalog 的插件目录当作 marketplace。

## 更新与发布状态

默认采用显式更新。对本地来源，先将源码 checkout 更新到选定版本、构建并执行 `--verify`，再执行宿主的更新或重新加载步骤。刷新 marketplace、更新安装缓存、重新加载和重新信任 hooks 分别检查；安装更新不删除项目计划和证据。

发布准备可在新目录中生成供检查的原生分发材料：

```bash
python3 scripts/prepare-native-release.py --output /tmp/program-design-release-new
```

成对提供的可选 `--repository-url` 与 `--npm-scope` 用于配置真实发布身份。准备脚本不 push、不执行 npm publish；未提供真实身份或尚未完成发布时，只能使用已生成的本地入口，不把上游账号、示例 URL 或 npm 名称写成可安装的已发布产品。Gemini/Hermes 的远端发布分支另在发布准备中保留包根布局。

## 参考项目与开发

在本仓库根恢复固定研究 checkout：

```bash
git submodule update --init
git submodule status
```

参考项目位于 `.submodule/<owner>/<repo>`，不是构建运行依赖。默认只初始化登记的一层子模块，不安装依赖或执行其中脚本；更新 gitlink 前单独检查提交、许可及引用，不用 `--remote` 代替恢复固定版本。

平台运行时保留所需 Shell、Python、PowerShell 和 TypeScript。可用宿主和 OS 的验证范围以实际报告为准，历史 0.2.0 结果不等于新安装链路已通过。开发规则见 [0.3.0 实施计划](docs/plans/0006-native-distributions.md) · [开发约定](docs/development.md)，个人偏好见 [override 差异稿](profiles/personal/AGENTS.override.md)。第三方资料和分发保留各自许可；本仓库尚未公开发布。
