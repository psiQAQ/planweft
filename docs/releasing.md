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
工作流使用 Node 24 与 npm 11.5.1+；不保存长期发布 token。配置完成后用候选版本验证 OIDC。
7. 从真实 npm/Git 源测试安装、升级、回退和卸载。稳定版必须有 Codex、Claude、Pi、OpenCode 四平台
真实模型维护与独立冷读证据；缺失认证、GUI、OS 实测单独记 Not Run，不将 synthetic responses 当模型验证。
8. 只有稳定版门槛全部 Passed，才发布 0.4.0 到 next，完成远端冒烟后提升 latest，并创建 v0.4.0 GitHub Release。
候选版本不使用 latest。发布配置不会自动开启插件信任或个人全局安装。

依据：[npm trusted publishers](https://docs.npmjs.com/trusted-publishers/)。本轮验证状态见内部记录
[PLAN-0008](plans/0008-planweft-release.md)（中文）。官方商店上架需要各宿主另行审核。
