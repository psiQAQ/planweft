# REP-0008：PlanWeft 0.4.0-rc.1 验证

2026-09-08；Linux 隔离配置。候选版可进入 next，稳定 0.4.0 尚未达到四宿主模型门槛。
原始运行目录在发布工作机独立保留；公开附件只收集测试输出、快照和摘要，脱敏本机路径并清空 tar owner/group。
[证据归档](evidence/0008/local-validation.tar.gz) 内 manifest 分别记录原始与公开 SHA-256；
[独立审查](../reviews/0008-installer-and-release-review.md)。

| 检查 | 结果 | 边界 |
| --- | --- | --- |
| 目录确定性、14 平台、六 catalog、单 npm 实际内容 | Passed | prepare-native-release 校验逐文件与执行位 |
| Python 回归 | Passed | 56 tests，76.797 秒 |
| Node 安装器回归 | Passed | 17 tests，涵盖故障、所有权、两项目隔离 |
| 原始上游 | Passed | 721 passed，63 skipped，798 subtests；Pi/OpenCode Vitest/typecheck/build |
| 迁移上游 | Passed | 721 passed，63 skipped，851 subtests；仅迁移测试接受产品候选版本 |
| Codex/Claude/Pi/OpenCode 本地原生生命周期 | Passed | 隔离 npm A/B fixture；安装、更新、回退、卸载、重装，新增/修改/删除文件 |
| Codex 真实 hooks 注入及恢复 | Passed | 原生容器场景；使用显式审查后的 trust bypass |
| Codex 真实模型维护及无旧会话冷读 | Passed | 最终维护 295.734 秒；冷读 50.829 秒；独立语义复核通过 |
| Claude/Pi/OpenCode 模型维护及冷读 | Not Run | 未配置这些宿主的模型认证 |
| 默认交互 hook 信任确认、Windows/macOS 宿主、GUI | Not Run | 环境或交互未完成；CI 已配置，不视作已执行 |
| 远端 npm/Git 生命周期、OIDC、稳定提升 | Not Run | 另行追加发布记录；不能用本地 fixture 替代 |

Pi 使用真实 RPC 读取唯一命令/Skill；OpenCode debug 实际加载 pw_init/pw_status/pw_check 与唯一 Skill；
Codex、Claude 核对原生插件缓存的 A/B 文件内容。原生加载不等于模型会话。项目三文件及批准需求保持逐字未变。
测试 A/B 在真实 tarball 上加入明确的 fixture 文件并生成本地 rc.2，未发布 rc.2；不将它们冒充原样远端包。

保留的失败：首次 Codex 维护虽修复代码，但未把旧活跃计划单向指向 task_plan，故 Failed；
在融合 Skill 的完成核对中加入此检查后重跑 Passed。首次迁移回归的 Hermes 版本正则拒绝 prerelease，
仅调整迁移测试的产品版本期望后全套通过，未改固定上游归档。早期磁盘配额与 Pi 项目信任发现见同目录附件。

复现入口（输出必须为仓库外新目录；宿主 CLI 另行安装到隔离目录）：

```bash
python3 scripts/build-plugin.py --verify
node tests/installer.test.mjs
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/prepare-native-release.py --output /tmp/pw-candidate-check --repository-url https://github.com/psiQAQ/planweft
python3 tests/run-installer-lifecycle.py --archive /tmp/pw-candidate-check/npm/planweft-0.4.0-rc.1.tgz --host claude --cli-dir /path/to/isolated/claude/bin --output /tmp/pw-claude-check
python3 tests/run-pwf-smoke.py --help
python3 scripts/collect-release-evidence.py --help
```

本轮不迁移本仓库现有计划，不修改个人插件配置。公开 Git 历史的 8 个隐私附件仍待用户选择处理方案；
npm allowlist 不包含这些历史附件，候选 tarball 隐私扫描独立通过。
