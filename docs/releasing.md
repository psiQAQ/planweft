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

当前暂停项：npm 首次发布的额外浏览器认证已过期，尚无远端候选包；部分 DeepSeek 模型调用被自动审批要求进一步确认隔离或具体目的地。五容器安装及同版本生命周期通过不代替完整发布验收，尚未发布 stable/latest。
