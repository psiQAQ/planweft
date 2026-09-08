# REV-0006：原生分发生成器、发布准备与安装依据审查

日期：2026-09-08。结论：本轮发现的四个问题均已修复并通过独立复验，受审生成器、发布准备与安装文档未见剩余阻断项。本报告不作为全宿主运行通过的声明。

## 独立性与范围

本 reviewer 未编写 `scripts/build-plugin.py`、`scripts/compile-opencode.py`、`scripts/prepare-native-release.py`、SPEC-0004、ADR-0007 和安装维护文档；实际读取这些文件、生成 catalog、预编译清单及真实 npm 归档后提出问题。实现者完成修复，本 reviewer 复验。

本 reviewer 编写过 `overlays/program-design/native/`、`tests/test_native_hooks.py` 和 `tests/run-marketplace-lifecycle.py`。**这些文件不属于本报告的独立代码通过范围**，由其他 reviewer 检查。本文中的 Copilot/CodeBuddy 原生命令是本 reviewer 实际执行的观测；它们证明列出的管理行为，不替代对测试控制器或运行时的独立审查。其他成员执行的测试另作证据阅读，不能冒认本 reviewer 亲自执行。

本轮没有提交或推送，没有 npm publish、市场上架、模型调用或个人宿主配置安装。测试 URL `https://example.invalid/program-design.git` 与 npm scope `pd-test-fixture` 只用于本地身份变换 fixture，不代表公开安装地址。

## 受审输入

以下为完成修复并通过本报告复验的 SHA-256；冻结在最终目录构建后。不能由版本号推定其字节与任意历史测试相同。

| 文件 | SHA-256 |
| --- | --- |
| `scripts/build-plugin.py` | `dd49b36568542070ea51b8a15838f7846254dd17a718d9fd2e37b018c977b9e9` |
| `scripts/compile-opencode.py` | `051e5d5c8ae3fa8daddd3b2d4078c2c4375456af082a323be27d9ee2af213606` |
| `scripts/prepare-native-release.py` | `b6bf7c40e5ca7628bc7004921839561edb0ff5cc2b98e4045a3ed85b0e42112e` |
| `.gitattributes` | `98d68aa4a08a47badea35aa758728a486e1d8b9d7848bb72b265daabbf8046f1` |
| `docs/specs/0004-native-distributions.md` | `fa85517f3ac4f92d9ebacce412e3bf826237429b02c66f3b8a4143cb5197daf7` |
| `docs/adr/0007-native-distributions.md` | `37d6a6fd4c52167232bb6045dc1c2bd1ac453206701f2a45a89131ba9677d130` |
| `overlays/program-design/install/INSTALL.md` | `22afb0379e6a6313ddfc187617ead5e3c9736f2273f2c6928f4aeb17b1856991` |
| `overlays/program-design/install/opencode.md` | `72d95eeb84af845609e7ce59af621d8435a9d07c04ade52cd66776ff22a667ee` |
| `overlays/program-design/BUILD.md` | `32422d83c97c1f6f317ddf245b206e9cb5f4ad9f2e9ef3d57a21ca78125b4fe0` |
| `docs/platforms.md` | `60ae2cfe32a3761e9112e15dedabd7b13a8865de3a5d2d0ae25ac9dc55563e4f` |
| `docs/upstream-maintenance.md` | `7e2cd7e3acd656af54705c307b833aebff8d21eab75d6fe3a34a43104f957dd8` |
| `overlays/program-design/opencode-compiled/manifest.json` | `de8db943ce4ab99c0c6bfa4f2439a071b87e46b8c47f8ccf54a25840c7d4e0bd` |
| `dist/manifest.json` | `0df18a8dc00801f13c3a9d0c49540e995671e5085bbeefc4318c4ed2536f4916` |

## 发现与关闭证据

| ID | 严重性 | 原问题及影响 | 修复与独立复验 |
| --- | --- | --- | --- |
| NR-01 | P1 | scoped npm 发布会修改 OpenCode `package.json` 与 lock 的身份字段，但保留将原始二者计入的编译 `source_sha256`；若将它解释为发布包输入摘要，就出现不可复现的来源声明。实际内存重放证实原始输入摘要相等、改名后的输入摘要不等 | **Closed**。编译清单新增原始逐文件 `inputs`；发布包保留原始编译 `source_sha256`/`inputs`，另记 `packaging_source_sha256`/`packaging_inputs` 及精确四字段 `identity_transform`、变换摘要。独立读取 scoped 准备目录和最终 `.tgz`，核对两组摘要/清单、before/after 字段、BUILD 入包及 JavaScript 字节不变，全部 Passed |
| NR-02 | P2 | Factory 示例注册任意 `/abs/repo` 后写死 `program-design@program-design`；Droid 注册名来自来源路径/仓库等，不以 catalog `name` 为唯一依据，实际临时来源名 `source` 时安装 ID 为 `program-design@source` | **Closed**。INSTALL 先执行 `droid plugin marketplace list`，再用实际 `REGISTERED_NAME` 安装/更新/卸载；平台矩阵区分 catalog 字段与注册名。官方文档及另一成员的 Droid 0.213.0 原生命令均支持该差异 |
| NR-03 | P2 | 旧 ZIP 清理使用宽 glob `program-design-*-HOST.zip`，会命中同目录的 `program-design-backup-codex.zip` 等非生成备份 | **Closed**。`retired_archives()` 仅认旧 schema 1 manifest、产品/版本/host/精确文件名及匹配内容 SHA，拒绝 symlink；未知备份保留，修改过的已登记 ZIP 报错保留。独立执行新增 release tests，登记对象/备份/被修改对象/schema 2 场景通过 |
| NR-04 | P2 | Pi 的 npm `files` 未包含 `INSTALL.md`；最终 `.tgz` 中 README 要求读取本包该文件，但文件不存在，目录测试无法发现 npm allowlist 截断 | **Closed**。Pi allowlist 和 npm 归档验证器已要求 `INSTALL.md`；对最终 scoped `.tgz` 重新读取，许可、来源、安装说明全部存在，且 archive 清单、字节和执行位与准备目录一致 |

问题原样记录，不把“已发现并修复”改写为最初实现从未失败。NR-01 的修复不重编译仅有发布身份变化的 JavaScript；其合理性由变换限定为 JSON 身份字段、编译输出字节未变及两阶段来源记录共同支持。SHA 清单证明内容一致性，不构成第三方签名或发布真实性证明。

## 生成与发布边界复核

- 普通 builder 从固定 vendor 归档和 overlay 生成 14 个 `dist/<host>/program-design/` 目录及 Codex 兼容镜像，不联网、不执行编译工具、不修改宿主安装目录。`write_tree` 只清理声明目标内的旧文件；安全路径校验拒绝越界/反斜线成员和 symlink，catalog 写入不遍历清理整个仓库。
- `--verify` 对文件集合、内容与执行位逐项比较，不执行写入；普通构建在清理旧 ZIP 前确认旧清单所有权与内容。仓库外用户备份不因相似命名被删除。`--tree` 要求新目标，仍是开发回归树而非安装分发。
- OpenCode 普通 build 检查当前 `src/`、`package.json`、lock、tsconfig 的合成摘要，并逐个校验预编译输出；源码过期、编译输出篡改和额外文件被拒绝。`compile-opencode.py --install` 在临时目录按已有 lock 执行 `npm ci --ignore-scripts`，再执行 TypeScript 编译；`--node-modules` 允许维护者提供已有工具链，并检查 TypeScript 版本。该后者检查不等同于验证调用者提供的整个 node_modules 供应链。
- 发布准备先 `build-plugin.py --verify`，要求新建且位于 checkout 外的输出目录；成对验证 URL/scope，拒绝凭据 URL 和无效 scope。它只执行本地 npm pack 与本地 Git 仓库操作，不设置发布 remote、不 push、不 publish。`release.json` 明确记录 `source_commit` 与 `source_dirty`；本轮 scoped fixture 的 `source_dirty=true`，不能描述成干净已提交发行版。
- 独立调用 Git 分支准备函数，以 A/B 两代不同文件集验证：B 保留 A 为父提交，删去旧文件，保留新增文件执行位，`git status` 干净，`git remote` 为空。此结果证明本地 `--previous-release` 延续历史的基础机制，不证明远端 branch protection、Git 推送或服务器配置。
- `.gitattributes` 的 `dist/** -text -whitespace` 保留生成字节并关闭该目录的 Git 空白诊断，不会跳过 builder 内容校验。独立临时仓库设置 `core.autocrlf=true`，将带 CRLF 和行尾空格的 dist 文件加入 index，读取 staged blob 与原始字节完全一致；工作区字节也未变。

亲自复跑 `python3 -B -m unittest discover -s tests -p test_native_release.py`：**4 tests Passed**，覆盖旧归档所有权、坏发布参数不创建目标、编译来源过期/输出篡改及发布 Git 历史延续。另独立执行 `test_native_distribution.NativeCatalogTest`：**2 tests Passed**，证明六 catalog 解析、保留无关 entry 及 `--verify` 前后快照不变。最终 `build-plugin.py --verify` 的 14 平台、mirror、manifest、marketplaces 和旧归档差异均为 0。

scoped npm 实物检查最初发现 Pi 安装说明缺失；修复后重新核对最终两包的摘要、完整归档清单、字节/执行位、安装说明及 OpenCode 两阶段来源、身份变换、BUILD 与语言资源，**20 项 Passed**。语言内容最终是主 Skill 下 `references/language-variants/.../GUIDE.md`，核对实际主 Skill 引用与 tar 成员，不把它描述为额外自动发现入口。复核输出 `pd-native-independent-review-final-checks.json`；被审 `release.json` SHA-256 为 `bf807ce119db4d8507eb9bef5433bc1dee4311a8b64e2fcc5d5841a1d6b51104`。

## 六个 catalog 与官方依据

以下 `source` 路径以 marketplace 仓库根为基准，不要求把宿主包混成一套目录。读取当前六份 JSON，均指向实际对应的 `dist` 安装根。各原生识别路径互相独立，添加一个市场不会替其他宿主注册。

| 宿主 | 识别入口与 source 结构 | 官方核对与限制 |
| --- | --- | --- |
| Codex | `.agents/plugins/marketplace.json`；`source: {"source":"local","path":"./dist/codex/program-design"}`；policy 与 category 是 Codex 字段 | [官方 Build plugins](https://developers.openai.com/plugins/build/plugins) 明确根 marketplace、本地相对路径及 policy schema；不向其他宿主复制该对象形状 |
| Claude Code | `.claude-plugin/marketplace.json`；`source: "./dist/claude/program-design"`；name/owner/plugins | [官方 marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) 支持本地相对目录、Git 和其他原生 source；ZIP 作为某些宿主的注册来源不等于本仓旧“解压再复制”拥有更新机制 |
| Cursor | `.cursor-plugin/marketplace.json`；相对 `dist/cursor/program-design`；包有自己的 `.cursor-plugin/plugin.json` | [官方 plugin reference](https://cursor.com/docs/reference/plugins) 与 [plugins](https://cursor.com/docs/plugins) 支持其原生 marketplace/manifest；官方 GUI/Dashboard 安装与 refresh 不能替写为 Claude 的 shell 命令，GUI 本轮 Not Run |
| Copilot CLI | `.github/plugin/marketplace.json`；相对 `dist/copilot/program-design`；包根 `plugin.json` | [官方 CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference) 列出该发现路径及相对 path source；不将 CLI 结果推定至 IDE 或 coding agent |
| Factory / Droid | `.factory-plugin/marketplace.json`；相对 `dist/factory/program-design`；原生包 manifest | [官方 plugins](https://docs.factory.ai/harness/plugins) 支持原生 catalog、兼容 fallback 和相对源码；注册名应读宿主列表，不能从文件中的 name 推定 |
| CodeBuddy | `.codebuddy-plugin/marketplace.json`；相对 `dist/codebuddy/program-design`；原生包 manifest | [官方 marketplaces](https://www.codebuddy.ai/docs/cli/plugin-marketplaces)、[reference](https://www.codebuddy.ai/docs/cli/plugins-reference) 加上已安装官方 CLI 2.147.0 的 help/实际行为；验证不是把 Claude 名称简单替换后的推测 |

Git marketplace 需要同时发布 catalog 与其引用的目录。裸 HTTP JSON 的相对路径不保证 payload 随之可得。Gemini 的根 `gemini-extension.json`、Hermes 的包根 Git 仓库、Pi/OpenCode 的 npm 包是不同渠道，六份 catalog 不会代为满足这些渠道的入口要求。

[Gemini 发布指南](https://geminicli.com/docs/extensions/releasing/) 支持 Git ref 与显式 update，本仓专用根目录分支可满足 Extension 的根 manifest；[Hermes plugins](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins/) 对 pinned `--ref` 要求完整 SHA 并拒绝 `update` 移动 pin。安装文档区分插件和另行发现的 Skill，同版本配对不由一个 marketplace 隐式保证。[Pi 官方 packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md) 中定向包 update 与宿主本体 update 不同；文档已按当前官方接口调整。OpenCode 安装说明明确 V1、预编译 JavaScript、独立包运行依赖及 Skill 单独发现，[官方 plugins](https://opencode.ai/docs/plugins/) 不使 npm 导出的代码自动等于 Skill 注册。

## 亲自执行的原生管理生命周期

全部测试使用新的临时来源、目标项目、HOME/XDG 和宿主配置；不继承认证。A 为最终冻结的 0.3.0 分发，B 为测试专用 0.3.1，包含新增、修改和删除的 Skill 资源。每个操作启动新的 CLI，随后比较实际安装路径的完整文件、字节和执行位，最后清理临时 profile。

| 宿主 | 实际结果 | 必须保留的语义 |
| --- | --- | --- |
| GitHub Copilot CLI 1.0.83 | A → B → 回滚 A → 卸载 Passed；三次分别核对 254 文件，均无不同/额外/遗留旧文件，目标项目未变 | 本地 marketplace path 插件 **live load，不复制缓存**。`plugin uninstall` 使其 disabled，保留原始目录及 disabled 列表项；随后 marketplace remove 才消除该来源的列表记录。测试由新进程读取，不证明存量会话 reload 或模型 Skill 读取 |
| CodeBuddy 2.147.0 | A → B → 回滚 A → 卸载 Passed；三次分别核对 252 文件，均无不同/额外/遗留旧文件，目标项目未变 | 版本缓存分别存在于原生 cache 目录；卸载移除安装记录，但保留带 `.orphaned_at` 的旧缓存。最终删除的是测试 profile，不宣称宿主原生 uninstall 抹除全部数据 |

Copilot 首轮 runner 将“卸载后列表项完全消失”误当所有宿主一致行为，造成验收失败；实物输出证明该项应当是 disabled，修正验收并保留原失败证据。`file://` 本地 Git URI 被 CLI 当作不受支持的本地路径处理，因此远端 Git clone/update 没有通过证据。

CodeBuddy 首轮受 OS sandbox 禁止绑定 loopback 影响，在插件命令启动时出现 `listen EPERM ... 127.0.0.1` 并超时；随后在获准允许该监听的执行环境重跑成功。没有复用个人认证或关闭宿主插件安全策略。最小环境不是 OS 层断网沙箱，不作“所有网络绝不发生”声明。

| 原始证据集 | summary.json SHA-256 | 被测输入 tree SHA-256 |
| --- | --- | --- |
| `pd-030-final-copilot` | `6f335f87e28b3448cd7d7cbb6e5df3b149a54aa68909fa469bb08e9f76a6b72e` | `8b6f834c181ba2d28ad14f67208d28c3e72e80881995b70e9a5d10182749e96d` |
| `pd-030-final-codebuddy` | `05405b37f33b434991f0ef1f99884060c79bd35adced9e942d30b46428d2d268` | `171e332b6ddf7d450adf7b2c81425447fbfaa70b90c85a9f4689bc0034134436` |

以上两个被测输入 tree 摘要已独立重新计算，与本报告冻结时的对应 dist 目录完全相等；更早的成功与失败轮次保留为历史。归档应保留 `commands/cli-version.json`、命令 stdout/stderr、A/B fixture、verify-A/B/rollback、项目前后清单及 summary；不能只保留一个 Passed 字样。

## 尚未证明的结果

- Copilot/CodeBuddy 的远端 Git 市场、新旧 GUI 会话加载、模型读取、hooks 信任和运行、Windows/macOS 均 **Not Run**。其中 CodeBuddy 本版仅 Skill 包装，没有为测试引入未验证 hooks。
- 其他成员的 Codex/Claude/Gemini/Pi 成功 lifecycle summary 已直接读取核对；这些是各自本地渠道证据，不将四项执行归属于本 reviewer。完整全宿主清单由最终复现报告汇总。
- Hermes 默认 Plugin Guard 对当前安装包的拒绝已在安装文档与平台矩阵保留为 **Failed**，后续原生生命周期 **Not Run**。没有用手工文件可见性替代安全扫描通过，也没有把规则匹配原因分析当成宿主已接受。
- Cursor/Kiro UI、公开市场审核、npm 公共 registry、Git 远端推送与分支保护均未执行；准备本地发布树和 fixture scope 不能消除这些限制。
- 本报告不独立批准自身编写的 adapters、native hook bridge 或对应测试，不将 0.2.0 模型证据复用成 0.3.0 新入口已跑通。最终交付须引用另一 reviewer 对这些实现的审查。

## 复现报告冷读

另按最终分层结果冷读 [REP-0006](../reproduction/0006-native-distributions.md) 与平台矩阵。两者将本地原生安装、协议/工具运行、未调用模型、远端渠道及 GUI 分开；Hermes 扫描拒绝保留 Failed，未以包根布局可识别冒充成功安装。对“所有 CLI 安装在临时目录”提出更正：Codex 实际复用已有 CLI，临时的是插件安装、profile 和项目，其他 CLI 路径以证据为准。Continue 停止主动维护的描述经[官方 README](https://github.com/continuedev/continue) 再次核实；Cursor/Kiro 对管理 CLI 采用“未发现官方接口”的限定，没有把未测 GUI 解释为产品完全不支持。

## 长期文档保护补验

共享生命周期夹具原来只有三个计划文件和 `user-note.txt`，不足以单独支撑长期文档保护的验收。补入既有 `docs/specs/approved.md`、`docs/adr/decision.md`、`docs/reproduction/known.md` 后，重新执行 Copilot 1.0.83 与 CodeBuddy 2.147.0 的 A 安装 → B 更新 → 回滚 A → 卸载/移除 marketplace。产品 dist 未修改，两轮源摘要仍与上表最终分发相等。

两宿主均 **Passed**：A、B、回滚各阶段的完整项目递归快照未变，最终七个既有记录的 SHA-256/执行位与 baseline 相等；又逐项将 baseline 摘要与夹具中既有内容计算值比较，避免仅比较两个缺项快照。安装缓存的版本增改删检查仍然通过，测试 profile 已清理。此结果限定于原生插件管理，不证明模型执行维护任务时必然保留批准需求。

| 补验证据集 | summary.json SHA-256 | records-preservation.json SHA-256 |
| --- | --- | --- |
| `pd-030-records-copilot` | `e5d225cc8270410c616f9f2d31b24a8542f69f7364ad1feac6c647a1f7629ab6` | `2ada305ecaa57e3cdb21a3df9fb92439e0df6628fd500210b7f2ca9639731596` |
| `pd-030-records-codebuddy` | `9c48d45858743637a4ac6f6906e213e70884b1c9fff3e75e6864bd3234c84c71` | `66bf7254ee3954154f590747d8ccd94cf135acd4969eb70123e6c938f6654230` |

两份证据均保存 `project-before.json`、`project-after.json`、逐阶段核对结果、`runner-snapshots/` 与 `runner-provenance.json`。共同 helper SHA-256 为 `8892a26df3bd2bdf456e90583ddbd9cd2e0d5f0141465351f55a3a122bd2999c`；marketplace driver 为 `07c2658f084138f495f2bc57f9e55741cee747f605726037d602e78b73a99648`。补验只扩大既有记录夹具，不替换先前成功/失败证据，也不改变本报告对自身编写代码的独立性限制。
