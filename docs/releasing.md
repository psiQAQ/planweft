[简体中文](releasing.md) | [English](releasing.en.md)

# 发布 PlanWeft

本页记录维护者发布流程和 0.4.0 的最终发布事实。用户安装方法见[安装指南](installation.md)，公开支持声明见[平台文档](platforms.md)。

## 0.5.0 静态/逻辑发布路径

0.5.0 使用独立的 [`release/support-policy-0.5.json`](../release/support-policy-0.5.json) 和
`check-document-release-gate.py`。预发布要求可重建包、离线测试、Hook 逻辑、Skill/Hook 关联、
公开文档、独立源码审查及项目文件冷读均为 Passed；promotion 还要求 registry 归档身份、临时安装
静态检查和独立 promotion review。不得用此路径修改 0.4.0 的 policy 或历史验收。

每条 Passed 记录必须引用 evidence JSON 所在目录下的实际附件及其 SHA-256；`package_sha256`
必须等于传入的本地 npm 归档摘要，且归档内 `package/package.json` 必须标识 `planweft@0.5.0`。
门禁拒绝自引用、绝对路径、`..`、越界 symlink、缺失附件或摘要不匹配。预发布只校验预发布项；
`--promotion` 才额外要求 registry 与 promotion review 证据。

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
