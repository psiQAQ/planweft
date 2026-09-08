# REP-0006：0.3.0 原生目录与更新验证

日期：2026-09-08；需求：[SPEC-0004](../specs/0004-native-distributions.md)；实施状态：[PLAN-0006](../plans/0006-native-distributions.md)。本轮固定 PWF v3.17.0 / `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`，产品版本 0.3.0；0.3.1 仅为生命周期测试 fixture。

14 个目录、六种 catalog、两种 npm 原生包和两个包根 Git 发布树均已实现。验证在 Linux x86_64 中使用隔离 HOME、缓存与项目，不读取个人认证、不调用付费模型，也没有发布或 push。当前结果不能推导 Windows/macOS、远程 Git/npm 渠道或 GUI 已通过。0.2.0 证据仍为历史记录。

## 检查方法与实际结果

| 层级 | 本轮结果 | 范围与限制 |
| --- | --- | --- |
| 目录与构建 | Passed | 14 个平台目录、六 catalog、Codex 镜像；重复生成一致，缺失/多余/字节/执行位漂移拒绝且只读；中文/空格路径、CRLF、独立复制、旧路径与许可证检查 |
| 原生发布准备 | Passed | 实际 npm pack 内容、预编译 OpenCode、输入/输出绑定；Gemini/Hermes 分支根、连续发布父提交、增改删；无 remote 或公开身份时仅输出本地坐标 |
| 本地回归 | Passed，52 tests 与 13 项入口契约 | 实际脚本、CLI 参数、缓存核对与保护边界，不等于模型语义质量；额外资源契约覆盖 Kiro 缓存路径和单独复制 Skill 后语言资源可达 |
| 原始上游 | Passed | pytest 721 passed、63 skipped、798 subtests；Pi 54 tests，OpenCode 34 tests、typecheck/build |
| 移植开发树 | Passed | pytest 721 passed、63 skipped、851 subtests；Pi 54 tests，OpenCode 34 tests、typecheck/build；原生包装另外执行本地与宿主测试 |
| 独立审查 | 见 [分发审查](../reviews/0006-native-distribution-review.md)、[运行时审查](../reviews/0006-native-runtime-review.md) | 分别检查来源、生成器与发布绑定、安装文档、native adapter/hook；作者不独立审查自己的实现 |

上游对照使用 Python 3.14.4、pytest 9.1.1、PyYAML 6.0.3，Node.js 22.22.1，以及隔离 PATH 中的 GNU mkdir 9.7。本机默认 uutils mkdir 0.8.0 的并发问题已在 REP-0005 复现；本轮不改变系统命令，也不宣称默认工具组合全部通过。63 个 skip 的具体条件保存在 JUnit/summary，多数需要 PowerShell。OpenCode 锁定依赖 ini 的 Node 最低版本警告仍保留，当前检查通过不代表达到该依赖声明的全部支持条件。

## 逐平台验证矩阵

“原生更新”列指本地 A→B→A，包含内容变化及旧文件删除；与远程已发布渠道分开。目录静态检查统一 Passed；下面单独列出更高层证据。

| 平台 / 本次宿主 | 包内协议或原生发现 | 原生安装 | 本地更新 / 回退 / 卸载 | 新进程或会话的实际加载 |
| --- | --- | --- | --- | --- |
| Codex 0.153.4 | Passed，app-server skills/list；implicit policy 另作静态检查 | Passed | Passed，重新安装实现更新；逐文件核对 | Passed，真实 exec + 本地 Responses fixture：未信任无注入、已审信任注入、新会话恢复、禁用无注入 |
| Claude Code 2.1.263 | hook 结构检查及继承协议 Passed | Passed | Passed，marketplace/plugin update，原生卸载后仍有 orphan cache | Not Run，未认证模型会话 |
| Pi 0.85.1 | 原始/移植 Extension 54 tests Passed | Passed，实际 npm tarball | Passed，显式安装新版本及回退 | Not Run，未启动模型会话验证 Extension 激活 |
| OpenCode V1 1.18.29 | Passed，真实 debug 命令发现三项 pd_ 工具与唯一主 Skill | Passed，本地预编译包+file URL+独立 Skill | Passed，切换本地包与新进程，移除后不再发现 | Passed，debug 加载后直接执行工具，返回各版本及包内模板探针标记；模型调用/会话内 reload Not Run |
| Gemini CLI 0.58.0 | 四事件脚本协议 Passed | Passed | Passed，extensions update；保留本地目录信任/安装确认 | Not Run，未认证模型会话 |
| Copilot CLI 1.0.83 | 原生输出协议 Passed，无 permissionDecision allow | Passed | Passed；本地 catalog 为 live source，卸载禁用发现，原目录保留 | Not Run，未认证模型会话 |
| CodeBuddy 2.147.0 | Skill/catalog 检查 Passed | Passed | Passed；原生卸载后可留 orphan cache | Not Run，未认证模型会话 |
| Factory Droid 0.213.0 | 原生安装元数据检查 Passed | Passed | Passed；按实际 installPath 检查，注册名取宿主列表 | Not Run，未认证模型会话 |
| Hermes 0.21.1 | 包根与资源契约 Passed | **Failed**，默认 Plugin Guard 拒绝 | Not Run，安装未完成 | Not Run |
| Cursor | 三事件脚本协议 Passed | Not Run，GUI/账号不可用 | Not Run | Not Run |
| Kiro | Power/Skill 静态与缓存脚本路径契约 Passed | Not Run，GUI 不可用 | Not Run | Not Run |
| Continue | 完整 Skill/原生目录静态 Passed | Not Run | Not Run，文档说明手工更新 | Not Run |
| Mastra Code | Skill/hooks 配置静态与禁用协议 Passed | Not Run | Not Run，文档说明受管文件更新 | Not Run |
| 通用 Agents | Agent Skills 目录静态 Passed | Not Run，未指定通用宿主 | Not Run，文档说明目录安装 | Not Run |

长期文档保护另用最终 `pd-030-records-*` 证据补验：八个可安装宿主均放置三文件、用户笔记、批准 spec、已接受 ADR 与既有 reproduction，共 7 份记录；安装、更新、回退和卸载前后逐项内容一致。另有负测试分别修改或删除三种长期文档，验证 runner 会将结果判为 Failed。原有 `pd-030-final-*` 轮次保留作为先前输入快照，不能独自证明这项补验。

所有插件安装和宿主配置使用临时目录；Codex 复用已有 CLI，其余使用本轮隔离安装的官方工具。Droid 官方二进制 SHA-256 为 `6f4cf5c65238be359c21a60c75dbbe31c90ffa6c860ed45fcc10e7fbae3250ff`。Hermes 使用官方提交 `9fd44b4dfc44138b9e5d5689acb56c438364ff7b` 的隔离 CLI。没有执行会影响个人全局 Droid 进程的安装脚本。

Codex 的本地响应服务只收到合成请求并返回固定 OK；随机标记只能来自项目计划，由实际宿主 hook 传到请求中。该证据证明送达和恢复，不证明模型理解、真实维护或冷读质量。旧版维护/冷读证据不算本次新版 Passed。新版本的自动匹配、批准需求冲突和证据不足等模型行为试用为 **Not Run**；相应运行器已迁移到目录安装，可在具备授权和环境时另行运行。

## 失败、修复与保留的限制

- 独立审查发现 scoped npm 重命名后编译绑定失配：保留原编译输入和 SHA，另记录发布输入、逐字段身份变化及摘要；实际 scoped tarball 复核通过。`example.invalid` 和测试 scope 仅为 fixture，没有声称上线。
- 旧 ZIP 清理原先按宽泛文件名匹配：改为旧 manifest 确认所有权并核对摘要；用户备份和修改过的旧包受保护。
- Pi npm allowlist 漏掉 INSTALL.md：纳入打包及 npm 实物校验；语言支持资源与主 Skill 一并携带；Kiro 示例从实际加载 Skill 的绝对目录解析脚本。
- Droid 实际 catalog 名称来自来源路径：文档改为使用列表返回的名称，不假定 JSON name 就是注册名。
- Gemini 最初未响应目录信任确认而超时；Codex fixture 最初把 TOML 顶层键误放到既有表后而超时；两个 runner 均修复，并保留初次日志和最终复验。CodeBuddy 本地监听和 OpenCode 依赖下载先遇到沙箱限制，按已授权隔离范围重试通过。
- Hermes 官方默认扫描器报告 dangerous（初次 42 findings），其中 `dns_exfil` 匹配文档的 “host … $”，`context_exfil` 匹配模板 “Include enough source context”。这是实际扫描观察；没有关闭扫描或改用手工安装伪装原生通过。最终目录复验仍被拒绝，41 findings；少的一项来自语言资源路径修复，剩余阻断规则不变。包内安装指南保留的是初次 42 项观察，最终结果以此处及 scan-comparison.json 为准。
- Cursor/Copilot/Gemini bridge 的 Python 脚本测试并非真实宿主事件触发；Gemini PreCompress 的 systemMessage 是用户提示，不宣称模型注入。停止/继续受宿主及上游 gate 边界限制。
- 原生卸载与缓存物理删除分开记录。Claude/CodeBuddy 保留的 orphan cache 不再被注册；生命周期 runner 最后删除整个隔离 profile。安装/更新均检查项目三文件及长期文档保护。

## 复现入口

```bash
python3 scripts/build-plugin.py --verify
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/experiments/check-entry-contract.py .
python3 scripts/prepare-native-release.py --output /tmp/pd-release-new
```

实际宿主 CLI、锁定回归环境及可选网络安装参数见 [tests/README.md](../../tests/README.md)。输出目录均使用新路径；不要把示例当作现存发布源。源码目录、安装缓存、项目文件、私有缓存和新会话分别核对，不以命令返回 0 代替内容检查。

原始日志、命令、runner 快照、fixture 文件清单、JUnit 与各轮摘要归档于 [本轮证据](evidence/0006/README.md)。证据中临时路径仅用于重现，无个人认证或 node_modules；公开转发前按该目录说明检查本地路径。所有未运行项保留明确限制，后续实测应新增证据而不改写本次观察。
