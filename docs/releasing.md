[简体中文](releasing.md) | [English](releasing.en.md)

# 发布 PlanWeft

本页记录维护者发布流程和 0.4.0 的最终发布事实。用户安装方法见[安装指南](installation.md)，公开支持声明见[平台文档](platforms.md)。

## 0.6.0 P0 状态证据发布路径

0.6.0 使用独立的 [`support-policy-0.6.0.json`](../release/support-policy-0.6.0.json)、`release/evidence/0.6.0/` 和
[`check-state-release-gate.py`](../scripts/check-state-release-gate.py)。该 gate 只放行确定性 P0 的离线、生成、准确产物、隔离安装、项目文件冷读以及独立 review；真实 Agent/model、tokens/cost 和真实不同 Agent 接续明确记录为非阻塞 `Not Run`，不能用 fixture 或历史证据替代。

候选发布顺序为：在同步且干净的 `master` 上生成唯一归档，运行 pre-publication gate，使用可信 workflow 发布到 `next`；从官方 registry 重新读取并核对 bytes/SHA-256/integrity，完成隔离安装，再由 promotion gate 和独立 promotion review 放行 `latest`。最后创建指向同一 `master` 提交的 annotated `v0.6.0` 和 GitHub Release。

发布后执行项目 [`AGENTS.md`](../AGENTS.md) 的分支归档规则：其他本地/远程分支先创建并推送 `archive/<branch>-<date>` annotated tag，核对归档提交后再删除，最终只保留 `master`；不删除 release tag 或尚未由发布结果保护的证据分支。

### 0.6.0 当前发布状态

- candidate workflow：[35242327786](https://github.com/psiQAQ/planweft/actions/runs/35242327786)，`master@5c23fa3`，362 个离线 Python 测试和 candidate gate：Passed。
- npm registry：`planweft@0.6.0` 已完成发布后读回，`next=0.6.0`、`latest=0.6.0`；公开归档 SHA-256 为 `7e913d3c43e852aaf59dbb2fc7adb3b7aa275453cf3041ec1acdebea80be9c5e`。
- annotated [`v0.6.0`](https://github.com/psiQAQ/planweft/releases/tag/v0.6.0) 和 GitHub Release 已创建并读回。
- stable dist-tag promotion 已完成：配置 `release/NPM_TOKEN` 后，公开 registry 最终读回 `latest=0.6.0`、`next=0.6.0`。此前 [35243815030](https://github.com/psiQAQ/planweft/actions/runs/35243815030) 的 `E401` 失败证据仍保留在 `release/evidence/0.6.0/raw/stable-promotion-attempt.md` 和 [REV-0019](reviews/0019-sol-pi-state-management-stable-promotion-blocker.md)；成功读回见 `release/evidence/0.6.0/raw/stable-promotion-readback.md` 和 [REV-0020](reviews/0020-sol-pi-state-management-promotion-completion.md)。
- 真实 Agent/model、tokens/cost 和真实不同 Agent 接续继续保持 `Not Run`。

### 0.6.0 凭据与固定 workflow 边界

- candidate 发布使用 npm Trusted Publisher/OIDC：`publish.yml` 固定使用 GitHub-hosted runner、`id-token: write`、`release` environment 和 `npm publish --tag next --provenance`，不依赖长期 npm token。
- stable promotion 不是 `npm publish`，而是独立的 `npm dist-tag add planweft@<version> latest`。因此只为 `release` environment 配置 package-scoped `NPM_TOKEN`；`promote-stable.yml` 先运行 `npm whoami` 凭据预检，再核对准确归档、promotion gate、dist-tag 写入和最终 readback。
- `release/NPM_TOKEN` 必须是允许非交互 dist-tag 写入的 npm automation/granular token（通常需启用 2FA bypass）。Trusted Publisher/OIDC 只覆盖 `npm publish`，不能为当前 `npm dist-tag add` 提供 OTP；若 token 触发 `EOTP`，工作流保留失败证据且不会改变 `latest`。
- 本机 `~/.npmrc` 只服务本机命令，不替代 GitHub Actions secret；不在仓库、命令行参数、聊天或日志中保存真实 token。

## 0.7.0 P1 Checkpoint/Reducer 发布路径

`0.7.0` 使用独立的 [`support-policy-0.7.0.json`](../release/support-policy-0.7.0.json)、
`release/evidence/0.7.0/` 和 [`check-state-p1-release-gate.py`](../scripts/check-state-p1-release-gate.py)。
它在 `0.6.0` 基础上验收 schema 2 升级/回退与数据保护、checkpoint before/after 快照和恢复、
确定性 reducer 的逐字引用、S14–S16、冷读、故障注入和离线四路消融。真实 Agent/model、
tokens/cost 及真实不同 Agent 接续仍固定为 `Not Run`，不作为发布放行条件。

发布顺序固定为：在同步且干净的 `master` 上由 builder 生成唯一 candidate，运行 P1 prepublication
gate，使用 Trusted Publisher/OIDC 发布到 `next`；从官方 registry 重新读取归档字节和 SHA-256，
更新准确的 promotion evidence；再由 `release` environment 的 `NPM_TOKEN` 执行受保护的
`npm dist-tag add planweft@0.7.0 latest`，最后核对 `latest=0.7.0`、`next=0.7.0`、tag、
GitHub Release 和隔离安装。若版本已占用或任一 gate 失败，停止发布并保留证据。

当前状态：candidate、registry readback、`v0.7.0` 和 GitHub Release 已通过；stable promotion workflow
`35295422731` 在 `npm dist-tag add` 处因 `EOTP` 停止，`latest` 仍为 `0.6.0`。失败证据保存在
[`stable-promotion-attempt.md`](../release/evidence/0.7.0/raw/stable-promotion-attempt.md)。

## 0.5.x 静态/逻辑发布路径

每个 0.5.x patch 使用与 `package.json` 同版本的 `release/support-policy-<version>.json`、
`release/evidence/<version>/` 和 `check-document-release-gate.py`。预发布要求可重建包、离线测试、Hook 逻辑、Skill/Hook 关联、
公开文档、独立源码审查及项目文件冷读均为 Passed；promotion 还要求 registry 归档身份、临时安装
静态检查和独立 promotion review。不得用此路径修改 0.4.0 的 policy 或历史验收。

冻结的 0.5.0 policy 是唯一文件名例外：它继续使用既有的 `release/support-policy-0.5.json`；不得为统一命名重写其 policy 或 evidence。

每条 Passed 记录必须引用 evidence JSON 所在目录下的实际附件及其 SHA-256；`package_sha256`
必须等于传入的本地 npm 归档摘要，且归档内 `package/package.json` 必须标识与 policy/evidence 相同的 `planweft@<version>`。
门禁拒绝自引用、绝对路径、`..`、越界 symlink、缺失附件或摘要不匹配。预发布只校验预发布项；
`--promotion` 才额外要求 registry 与 promotion review 证据。

### 0.5.1 正式 promotion 记录

- 源码提交：`b4a2c02bacf01ea2896f1beae5382588b5b6abd7`
- 可信发布 workflow：[34725859049](https://github.com/psiQAQ/planweft/actions/runs/34725859049)
- 官方 npm 归档 SHA-256：`8071dee2ffe8c0500e739e17723cf307d3c29276055bbc5a8d1c860358419b28`
- `next`：`0.5.1`；`latest`：`0.5.1`
- prepublication、registry evidence 与独立 review：Passed，附件见 `release/evidence/0.5.1/`；正式 promotion 的独立 readback 见 [REP-0015](reproduction/0015-planweft-0.5.1-formal-promotion.md)
- annotated `v0.5.1` tag 指向包含本正式记录的最终 `master` 提交
- GitHub Release：[v0.5.1](https://github.com/psiQAQ/planweft/releases/tag/v0.5.1)，公开、非草稿、非预发布，未附加新构建产物

候选阶段的 `next` 记录、policy 和附件保持原样；本节仅记录随后经维护者授权完成的 dist-tag promotion、source tag 与 post-tag GitHub Release。

## 冻结的 0.4.0 全生命周期（历史）

以下流程和五宿主要求是 0.4.0 schema 3 的历史发布边界，不是 0.5.0 的补充门禁，也不得用来把 0.4.0 的运行时结果写成 0.5.0 验证。

### 发布前检查

1. 从已确认的远端 `master` 创建干净 worktree 和发布分支。不要带入其他工作区的未提交内容。
2. 核对版本、远端分支、最新 CI、npm 版本占用和 dist-tags。外部写入前再次查询。
3. 审查公开历史、附件、许可证、作者和安装元数据。未解决的隐私问题阻塞发布。
4. 修改规范源并生成平台目录。依赖、固定上游或编译器变化必须作为单独变更审查。
5. 运行构建一致性、完整测试、原生生命周期、准确产物、模型范围内的验收和独立 review。

```bash
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
node tests/installer.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
```

### 准确产物与发布顺序

从同一干净提交生成唯一 npm tgz、`release.json` 和 checksum。稳定版的发布 workflow 必须以预审 SHA-256 作为 `expected_sha256`，CI 重建结果不一致时停止发布，不能通过修改期望摘要放行。

```bash
python3 scripts/prepare-native-release.py --release --output /tmp/planweft-release-new --repository-url https://github.com/psiQAQ/planweft
gh workflow run publish.yml -f expected_sha256=REVIEWED_SHA256
```

`--output` 必须是 checkout 外的新目录。发布 workflow 使用 GitHub OIDC/provenance；不要在命令、聊天或日志中传递长期 npm token。

稳定版先发布到 `next`。从官方 registry 重新下载并核对字节、SHA-256 和 integrity，再完成五宿主原生安装、发现、doctor、新会话加载与卸载。promotion 证据和独立 review 通过后才能更新 `latest`，最后创建指向准确源码提交的 GitHub Release。

已发布的 npm 版本不可覆盖或删除。远端验收失败时保留 `latest` 的原值和失败证据，以新 patch 版本修复。

### Schema 3 门禁

[`release/support-policy.json`](../release/support-policy.json) 为每个宿主和场景声明 `required`、`evidence_based` 或 `experimental`。门禁根据策略计算 `release_blocking`，不信任 acceptance 自行填写的放行值。

- `required` 只有 Passed 才放行。
- 实验性 Failed/Inconclusive 必须绑定附件和公开限制 ID；Not Run 必须给出原因。
- fresh/reused 证据都绑定准确包和附件摘要。复用还要绑定原包、目标包、逐文件 manifest 差异、受影响检查和 reviewer。
- 准确产物、最终安装/卸载、用户文件保护、显式 Skill 读取和正式模型工作流不得复用。
- prepublication 和 promotion 分别需要独立 review；promotion 还要复核前一阶段 review。
- evidence root 不得越出仓库，绝对路径、`..`、越界 symlink、自引用和摘要不匹配均拒绝。

聚合状态必须来自真实子场景。能力是否阻塞发布与场景是否 Passed 是两件事，不能混写。

## 0.4.0 发布记录

- 源码提交：`1a96dce0d25b4c92ecfc82225b94980ca37bda14`
- npm 归档 SHA-256：`e611338a619adabb0ba943d75460a01d83e4670dbe7d69f5d1050a1c1467c132`
- npm `latest` 与 `next`：`0.4.0`
- Linux、Windows、macOS 和 distribution Check：Passed
- prepublication、promotion 门禁和独立 review：Passed
- GitHub Release：[`v0.4.0`](https://github.com/psiQAQ/planweft/releases/tag/v0.4.0)

唯一保留的实验性 Failed 聚合项是 Codex stopping。gate-cap 开启/关闭配对因 syscall 归因不完整使用 `LIMIT-CODEX-TRACE-INCOMPLETE`；会话正常结束不能改变该判定。

## 历史记录

RC1 至 RC15 的发布、失败、修正、CI、模型验收和附件绑定保存在 [PLAN-0010](plans/0010-five-agent-release.md)、[REP-0010](reproduction/0010-five-agent-release.md)及其 checkpoint/evidence 文件中。历史记录保持当时状态，不在本页重复，也不因 0.4.0 最终发布而改写。
