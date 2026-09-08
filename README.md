# Program Design

研究并构建面向 Agent 的本地项目文档管理工具：让长期知识、当前任务、设计依据和验证结果能够被持续维护，并供新会话和人类读者使用。

[Program Design 0.2.0](plugins/program-design/README.md) 以固定的 PWF v3.17.0 为底座，提供 `$project-docs`、文件规划与恢复、原生 hooks 和 14 个平台分发，默认附加按需文档维护、依据审查与交接规则。源码、构建和验证记录都在本仓库；各平台的实际支持层级见 [兼容与安装说明](docs/platforms.md) 和 [REP-0005](docs/reproduction/0005-pwf-based-plugin.md)。本仓库继续使用原有文档入口，没有正式自身接管。

## 从哪里开始

| 需求 | 入口 |
| --- | --- |
| 理解产品目标与当前范围 | [0.2.0 规格](docs/specs/0003-pwf-based-plugin.md)；[基础目标](docs/specs/0001-document-management.md) |
| 安装或升级插件 | [各平台安装](docs/platforms.md)；[分发清单与 SHA-256](dist/manifest.json) |
| 接续本阶段工作 | [0.2.0 实施记录](docs/plans/0005-pwf-based-plugin.md)；[既有配对维护计划](docs/plans/0004-paired-maintenance-trial.md) |
| 构建和同步上游 | [固定来源与维护流程](docs/upstream-maintenance.md) |
| 阅读文章与参考实现 | [资料索引](docs/reference/README.md) |
| 核查某个文件为什么这样设计 | [引用台账](docs/design-references.md) |
| 查看未被先例覆盖的想法 | [创新记录](docs/innovations.md) |
| 了解开发和审查方式 | [开发约定](docs/development.md) |
| 运行分发、运行时及上游回归 | [测试说明](tests/README.md) |
| 查看实际验证及限制 | [0.2.0 结果](docs/reproduction/0005-pwf-based-plugin.md)；[0.1.0 历史试用](docs/reproduction/0004-paired-maintenance-trial.md) |

## 本地构建

Python 3 标准库即可从仓库内固定快照重建；不联网、不读取研究子模块或个人插件缓存：

```bash
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

输出为 `plugins/program-design/` 及 `dist/program-design-0.2.0-<platform>.zip`。这些是生成物，应修改 `overlays/program-design/` 或构建脚本后重建，不能逐份手改。每包均有独立安装说明、许可及来源清单。

## 安装到不同 Agent

**按宿主选择一个 ZIP，再按包内 `INSTALL.md` 安装到目标项目或宿主配置目录。** `dist` 中每个包都是独立的平台适配，不是需要一起安装的组件；使用多个宿主时，分别解压它们的包。

| 使用的宿主 | 安装包 | 主要安装表面 |
| --- | --- | --- |
| Codex | [codex.zip](dist/program-design-0.2.0-codex.zip) | 本地 marketplace、Skill 与受信任 hooks；也支持从本源码仓库的 marketplace 安装 |
| Claude Code | [claude.zip](dist/program-design-0.2.0-claude.zip) | 本地 marketplace 或 `--plugin-dir` |
| Pi | [pi.zip](dist/program-design-0.2.0-pi.zip) | `pi install -l` 注册本地包，包根声明 Skill 和 Extension |
| OpenCode | [opencode.zip](dist/program-design-0.2.0-opencode.zip) | `.opencode/` 下的本地源码包、插件入口和 Skill，按锁文件构建 |
| Hermes | [hermes.zip](dist/program-design-0.2.0-hermes.zip) | `HERMES_HOME` 下的 Skill 与原生插件 |
| Cursor | [cursor.zip](dist/program-design-0.2.0-cursor.zip) | 目标项目 `.cursor/`，合并 hooks 配置 |
| Gemini CLI | [gemini.zip](dist/program-design-0.2.0-gemini.zip) | 目标项目 `.gemini/`，合并 settings 中的 hooks |
| GitHub Copilot | [copilot.zip](dist/program-design-0.2.0-copilot.zip) | 目标项目 `.github/hooks/` 与 `.github/skills/project-docs/` |
| Mastra Code | [mastracode.zip](dist/program-design-0.2.0-mastracode.zip) | `.mastracode/skills/` 与合并后的 hooks |
| Kiro | [kiro.zip](dist/program-design-0.2.0-kiro.zip) | `.kiro/skills/`，导入 Skill；按授权使用原生 bootstrap |
| Continue | [continue.zip](dist/program-design-0.2.0-continue.zip) | `.continue/skills/` 与可选 prompts |
| Factory / Droid | [factory.zip](dist/program-design-0.2.0-factory.zip) | `.factory/skills/` |
| CodeBuddy | [codebuddy.zip](dist/program-design-0.2.0-codebuddy.zip) | `.codebuddy/skills/` |
| 通用 Agent Skills | [agents.zip](dist/program-design-0.2.0-agents.zip) | 支持该发现协议的宿主使用 `.agents/skills/`；不代表通用 hooks |

例如，从源码仓库准备一个 Pi 安装源（Linux/macOS，在仓库根运行；解压目标应为新目录）：

```bash
unzip "dist/program-design-0.2.0-pi.zip" -d "/path/to/packages/program-design-pi"
cd "/path/to/target-project"
pi install -l "/path/to/packages/program-design-pi/program-design"
```

Pi 本地安装记录路径，因此保留该解压目录；重启后用 `/skill:project-docs` 查看 Skill、`/pd-plan-execute` 显式启用 Extension 执行。其他平台的复制、配置合并、激活、卸载及 Windows 解压方式见 [完整安装说明](docs/platforms.md)。本版仅提供本地安装源，没有发布 npm 或远端 marketplace，不能照搬上游的远程安装命令。

### 为什么根目录没有所有 Agent 的隐藏文件夹

PWF 把 `.cursor/`、`.gemini/`、`.opencode/` 等适配源直接展开在根目录，并用同步脚本维护共享 Skill。本仓库采用 [ADR-0006](docs/adr/0006-pwf-derived-runtime.md) 的「固定上游快照 + 本地扩展 + 生成分发」：同样的原生适配位于对应 ZIP 内，安装时才放入**目标项目或用户配置目录**。Pi 包则按其 package.json 声明展平为包根。根目录保留的 `.agents/plugins/marketplace.json` 只是 Codex 的仓库安装索引。

这使共享内容可以统一生成并检查一致性，也避免在本开发仓库根放入会被多个宿主自动发现的运行配置。代价是多数平台需先选包并解压，不能直接从源码仓库根复制隐藏目录。克隆本仓库不会自动为所有 Agent 安装插件；无需初始化研究子模块即可使用分发包。

## 获取参考项目

在本仓库根目录执行以下命令，按仓库提交记录中的 gitlink 恢复参考项目：

```bash
git submodule update --init
git submodule status
```

参考项目放在 `.submodule/<owner>/<repo>`。默认仅初始化本仓库登记的一层参考项目，不递归安装它们自己的依赖，也不执行其中的脚本。更新参考版本时，单独审查新的 commit、许可和受影响的引用；不要将 `--remote` 更新当作恢复固定版本的方法。

文档可直接阅读。0.2.0 按平台保留上游 Shell、Python、PowerShell、TypeScript 运行时，具体依赖和激活方式以安装说明为准；OpenCode 源码安装需要按自带锁文件构建。上游回归需要锁定的 pytest/PyYAML 和 Pi/OpenCode 开发依赖；真实 Codex 试用另用 Docker 与已有认证。

个人偏好见 [override 差异稿](profiles/personal/AGENTS.override.md)，使用前按其中说明与通用原则手工组合。

第三方资料的许可与全文翻译范围分别见资料索引；子模块保留其上游许可。本仓库尚未作公开发布。
