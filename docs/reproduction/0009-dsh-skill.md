# REP-0009：DSH Skill-only 增量验证

范围：15 平台中的新增 DSH Skill-only；原生 profile hooks 未实现，未发布。

- Passed：Node 20 项安装器回归，包含 DSH 根目录范围、两版本文件新增/修改/删除、回退、用户修改保护、卸载、DSH_HOME 空白与 tilde。
- Passed：官方 npm `@deepseek-ai/dsh-skill-filesystem@0.1.2-rc.1` 实际发现唯一 project-docs、读取准确路径和完整资源、修改正文后的再次加载。该场景为复制部署、关闭 watcher，不是模型会话、CLI 全链路或软链接 provider 验证。
- Passed：生成器 verify；安装入口与公开源约束定向检查。
- 首轮完整 Python 回归：55 Passed、1 Failed（安装入口清单遗漏新增 dsh）；补齐显式清单后受影响安装契约重跑通过。未隐藏或倒改首次结果。
- Not Run：DSH profile hooks、原生插件生命周期、模型使用、Windows/macOS。

[脱敏证据](evidence/0009/skill-validation.tar.gz)。归档 manifest 提供原始/脱敏摘要。
复现：`node tests/installer.test.mjs`、`python3 -m unittest discover -s tests -p test_pwf_installation.py`；
官方 provider 运行使用 `node tests/run-dsh-skill-smoke.mjs ISOLATED_NODE_MODULES NEW_OUTPUT`，输出须为仓库外新目录。

独立依据 reviewer 首次发现 state/lock 与最近 Git 根不一致及 DSH_HOME 展开错误。
修正为非 Git 根调用在 preflight 拒绝，并按官方 home-paths 保留非空值、展开 tilde、空白回退。
reviewer 回审通过并独立重跑 Node 20 Passed。

复核指纹：

- lib/installer.mjs：`aaa856e229df576c12eb54ccca390a3e6477e1141c95f0b0c691f7105ef87e06`
- tests/installer.test.mjs：`102c6a7354366c709516274b75403dd59dae3c89ae4210e1c5ff1e54736bcc6f`
- tests/run-dsh-skill-smoke.mjs：`5d4b1e6ab8b8d3adc5bf8324504d23e5d42cc8485f6d37e0b29ceb2470c4c729`

完整集成的官方依赖变更被自动审批拒绝，等待用户确认；package.json 和 package-lock.json 均保持不变。
