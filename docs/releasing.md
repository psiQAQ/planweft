[简体中文](releasing.md) | [English](releasing.en.md)

# 发布 PlanWeft

唯一包 `planweft`；公开 Git 源 `https://github.com/psiQAQ/planweft`。
这些是发布目标，不代表当前版本已经上线。入口：[安装：中文](installation.md) / [English](installation.en.md)。

1. 审计拟公开历史和附件，确认第三方许可、作者与安装地址。保留本地历史备份；未处理隐私发现前不推送。
2. 递增 package.json 与构建器版本，刷新 OpenCode 编译绑定，再生成并核对目录。依赖更改需要更新根锁文件。
3. 执行离线回归、原始/迁移对照、隔离宿主生命周期与独立 review，按逻辑分批提交并合并 master。
4. 从干净提交准备原生产物。仅一个 npm tarball；Gemini/Hermes 是各自以插件文件为根的 Git 树。

```bash
python3 scripts/compile-opencode.py --install
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
node tests/installer.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/prepare-native-release.py --release --output /tmp/planweft-release-new --repository-url https://github.com/psiQAQ/planweft
```

`--output` 必须是仓库外的新目录。`--previous-release` 延续前次发布树的父提交。
发布后必须保留完整 release.json 与 Git 发布树；后续从已发布分支恢复历史后再生成，不强推或重建分支根。
`release.json` 记录源码提交、包内逐文件摘要、平台树及 OpenCode/Hermes 的 Skill 配对信息。

5. 首次通过交互式 npm login 完成认证，发布候选版到 next；不要在聊天或日志中粘贴 token。

```bash
npm login --registry=https://registry.npmjs.org
npm publish /tmp/planweft-release-new/npm/planweft-0.4.0-rc.1.tgz --tag next --access public --registry=https://registry.npmjs.org
```

6. 在 npm 包 Settings 配置 GitHub trusted publisher（psiQAQ / planweft / publish.yml），使用受保护 release 环境。
工作流使用 Node 24 与 npm 11.11.0；不保存长期发布 token。配置完成后用候选版本验证 OIDC。
7. 从真实 npm/Git 源测试安装、升级、回退和卸载。稳定版必须有 Codex、Claude、Pi、OpenCode、DSH 五平台
真实模型维护与独立冷读证据；缺失认证、GUI、OS 实测单独记 Not Run，不将 synthetic responses 当模型验证。
8. 只有稳定版门槛全部 Passed，才发布 0.4.0 到 next，完成远端冒烟后提升 latest，并创建 v0.4.0 GitHub Release。
候选版本不使用 latest。发布配置不会自动开启插件信任或个人全局安装。

依据：[npm trusted publishers](https://docs.npmjs.com/trusted-publishers/)。本轮验证状态见内部记录
[PLAN-0010](plans/0010-five-agent-release.md)（中文）。官方商店上架需要各宿主另行审核。

## 五容器门槛与准确产物

稳定归档必须由 `scripts/check-release-gate.py` 校验五平台证据。每项记录绑定版本、npm SHA-256、实际附件及其 SHA；模型记录标识实际镜像、CLI、模型、runner 和 session。冷读来自不同会话，输入摘要必须等于维护结果快照；独立审查绑定当前本地证据，提升 latest 前还须绑定远端证据。校验器保证证据完整性和一致性，不独立证明结论正确。

发布工作流的 `expected_sha256` 输入用于核对 CI 重建的准确归档；稳定版必填，不能通过替换期望摘要放行差异。验收附件存放在 npm 包外，避免摘要自引用。候选包可以进入 next，不能提升 latest；真实远端 RC→stable→RC→stable 验证完成后，才通过现有交互认证更新 latest 并创建 Release。OIDC 发布权限不等于 npm dist-tag 管理权限。

本轮已备份并清理公开 master 历史，GitHub 仓库已公开；旧记录中的“尚未推送”仅属于当时状态。原始历史和清理后附件通过内部 [映射](reproduction/evidence/0010/history-sanitization.json) 关联。清理不撤回其他人的旧副本。

RC1 已于本轮发布，远端 SHA-256 与验收归档一致。首次发布在指定 next 后仍自动生成 latest，认证完成后的标签删除请求仍返回 HTTP 400，尚未更正；不将候选标签状态视为稳定验收通过。GitHub trusted publisher 已建立，release 环境只允许 master。配置命令使用 npm 11.19.1 的 `--allow-publish`（旧 11.11.0 的 trust 请求缺少当前 API 必填 permissions 字段）；发布工作流仍固定 npm 11.11.0。后续 RC2/RC3/RC4 已验证 OIDC；五宿主最终门槛继续补齐。

RC2 已通过 [GitHub OIDC](https://github.com/psiQAQ/planweft/actions/runs/34248506886) 发布到 next，CI 重建及真实 npm 下载均匹配冻结 SHA-256 `3948cb9c4cd03f1505966b95e22729177cb09a4af28296fd1ef7be2dd0349754`。OpenCode 维护通过独立审查；当时 DSH 上下文与维护失败留待后续修复。

RC3 曾通过 [OIDC 工作流](https://github.com/psiQAQ/planweft/actions/runs/34264091642) 发布到 `next`。干净源码 `7d690010fbf8705129d3fb44b2556bb6a0fa7de6`、CI 重建及 npm 远端归档均绑定 SHA-256 `09ea0e4dceb88c9b845af851916356c44f3447071e0d1311dc38841639705060`；[三系统 CI](https://github.com/psiQAQ/planweft/actions/runs/34262987621) 通过。DSH 修复后的注入与恢复已有实际证据，但维护采用/文档准确性仍有失败；OpenCode 六项停止场景通过原生 server 的 5 秒静默观察，不宣称宿主提供 settled。正式 `0.4.0` 尚未发布，`latest` 仍是 RC1；当时试用版本为 `planweft@0.4.0-rc.3`。详细状态：[中文](platforms.md) / [English](platforms.en.md)。

RC4 已通过 [OIDC 工作流](https://github.com/psiQAQ/planweft/actions/runs/34267947801) 发布到 `next`，修复 OpenCode 原生 npm 入口。冻结源码 `1d1c76c1d6048fd67fa6ef1b614e11b999106db6`，远端归档 SHA-256 为 `c6f54319befc8c43c559fd4c5af2eb6ca3d1b626e6c0b3fd65cb67c11d9d318b`，与本地和 CI 重建逐字一致；[三系统 CI](https://github.com/psiQAQ/planweft/actions/runs/34267221127) 通过。当时试用版本为 `planweft@0.4.0-rc.4`；当前候选见下段。上述 RC3 记录保留历史归档身份；稳定版门槛仍未通过，`latest` 仍指向 RC1。

RC5 已通过 [OIDC](https://github.com/psiQAQ/planweft/actions/runs/34317038628) 发布到 `next`，[三系统 CI](https://github.com/psiQAQ/planweft/actions/runs/34316870816) 通过。冻结源码为 `c3bb9d870429e304149ca58b0e804ea55f4b537a`，准确 npm SHA-256 为 `f9123657773eb95cfe3df79b3f55669f12b37203bf2a593c1e749da1676069b3`，远端字节及 npm integrity 均匹配。该阶段试用版本为 `planweft@0.4.0-rc.5`。正式 0.4.0 未发布，latest 仍为 RC1。当前失败与收集器限制见[跨平台状态：中文](platforms.md) / [English](platforms.en.md)。

## RC6 已发布与 RC7 修复准备

RC6 已通过 [OIDC](https://github.com/psiQAQ/planweft/actions/runs/34322158954) 发布，准确归档 SHA-256 为 `c531188e46d268048ca0ab559baa358fc70af07277cb0001c521951234525799`，[三系统 CI](https://github.com/psiQAQ/planweft/actions/runs/34322062209) Passed。当前源码准备 RC7，修复初始化 progress 重复状态及 findings 观察时点；不覆盖 RC6。公开渠道仍以 registry 查询为准。稳定版清单升级为 schema 2：每个总项还必须提供逐场景 Passed 与准确附件，包括默认自动采用、去重、停止上限、权限隔离和远端升降级。Pi 使用原生包批准场景，不宣称具有逐工具拒绝沙箱。历史 RC 和 schema 1 不替代当前稳定归档的实际验收。

真实验收串行运行，场景最多 600 秒；不足 4 GiB 可用内存或 8 GiB 输出磁盘空间时不启动容器。容器限 2 CPU、3 GiB 且无额外 Swap、256 PID。确认场景容器消失后才清理自有未引用缓存；原始失败、项目记录、准确包和历史备份保留。


## RC7 已发布，RC8 修复中

RC7 源码 `7e66ee9214364ffa5f00a04a8d040e4ace082980` 已经 [OIDC 发布](https://github.com/psiQAQ/planweft/actions/runs/34333285542)，准确 npm SHA-256 为 `e3d67af7dcba154a3800e39c19ec06a7f40b874d3b92dc7b7517bed85cc4bed2`。远端字节及 integrity 均一致；固定 Node 24.20.0 的[三系统 CI](https://github.com/psiQAQ/planweft/actions/runs/34334806556) 通过。

RC7 尚有计划采用、观察时点和测试范围失败，当前源码准备 RC8，不覆盖 RC7，不发布稳定 0.4.0。原失败和独立审查见[平台状态：中文](platforms.md) / [English](platforms.en.md)。原生 npm 升降级测试与无模型容器入口正在补齐；最终准确 stable 包、远端新会话及五平台门槛仍须完整执行。latest 当前仍指向 RC1，不把这一遗留标签当作正式版本。


RC8 开发复验恢复发现阶段的能力与授权边界；721 项迁移回归通过。Pi、OpenCode、DSH 的 RC6↔RC7 原生 npm 生命周期通过，保留此前失败。上述均不是最终稳定归档验收；RC8 发布与模型复验待执行。


RC8 已由 OIDC 发布到 next，Check 34339605601 三系统通过；远端 5386708 bytes，SHA-256 `d6f34542495d811cc3171af0f6db96f30b1ef3089289fc740e4a4686a27d4a78`。五镜像安装/移除/重装通过。Pi、OpenCode 的自动维护检查通过，但独立审查分别发现加载前越界读取/未执行验证声明和项目范围外的手工临时目录；这些失败保留，不能放行稳定版。RC9 开发修复针对这些具体触发点，未发布，模型效果待验。

RC9 已由 OIDC 发布且准确归档校验、三系统 CI Passed。Claude 已获官方 DeepSeek 兼容端点直连授权并完成模型试验，但跳过计划初始化；Pi、OpenCode、DSH 的独立检查仍发现记录准确性或授权范围问题。RC10 正在修复，尚未发布；RC9 原始 Failed 保留，正式 0.4.0 未通过门槛。
