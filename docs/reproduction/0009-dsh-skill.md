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


## 原生 bundle 与 hooks 完成记录

后续用户明确允许两个官方运行依赖，审批阻塞已解除。根 package.json/package-lock.json 固定 0.1.2-rc.1；OpenCode 默认 export 保留，新增 ./dsh 和 dsh.bundle.patch。

- Passed：最终完整 Python 58 项；独立 reviewer 与主流程 Node 27 项。
- Passed：官方 DSH 0.1.2-rc.1 / pnpm 10.28.2，隔离 profile 原生 A/B 安装、更新、回退、卸载、重装与唯一 bundle 配置展开；每个版本核对文件新增/修改/删除，项目三文件/批准需求逐字保留。
- Passed：真实官方 bridge + 实际 shell/Python 子进程，使用显式事件载体验证跨项目隔离、每次提示刷新、SessionStart 恢复、默认 Stop 不续跑、下游权限拒绝不被放宽，以及 PLANNING_DISABLED。此为协议测试，不是完整模型会话。
- Not Run：DSH 模型维护、完整 gated 模型续跑、Windows/macOS；原生 npm 远端来源待候选发布。

桥接差异：官方没有 PreCompact，PreToolUse 纯上下文被丢弃，故不注册；默认 Stop 的 systemMessage 官方不展示，保留该限制。首轮 probe 错把 PWF 每次 UserPromptSubmit 刷新当作去重契约而失败，第二轮被官方 Stop 警告触发，二者均保留原始记录；最终断言按真实上游语义记录，没有修改 PWF 固定运行时来消除失败。

独立审查两轮修复：原生写入相对 link 后失败的恢复、显式 profile 参数与卸载一致、重复 hooks 检测对 Skill-only 及注释的误报。最终 reviewer 指纹：

- lib/installer.mjs：`5f521c7195419e3a040aaaf1ca22265a01e017ab95a91e78aca10f8abdb60df2`
- tests/installer.test.mjs：`33045b75d40c39516d6f0057b0ed2f596bed45aace60d175a6a146de550a6f93`

[完整原生证据](evidence/0009/native-validation.tar.gz) 含原始与脱敏摘要。真实生命周期复测使用审查修正版；之后的变动仅为重复 hook 文本检查及说明，由新增定向故障测试覆盖，没有把旧包摘要冒充最终发布摘要。

复现入口：

```bash
python3 tests/run-installer-lifecycle.py --host dsh --archive /path/to/planweft-candidate.tgz --output /tmp/new-dsh-lifecycle --cli-dir /path/to/isolated/dsh/node_modules/.bin
node tests/run-dsh-hook-probe.mjs /path/to/managed/node_modules/planweft /tmp/new-dsh-hook-probe
```
