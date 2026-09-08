# 0.2.0 安装补充证据

日期：2026-09-08。用户在提交整理时要求说明各宿主安装路径。当前结果见 [REP-0005](../../../0005-pwf-based-plugin.md) 的安装补充和[独立审查](../../../../reviews/0005-installation-review.md)。原有 regression、host、local 记录保持不变。

| 文件 | 实际内容 |
| --- | --- |
| [distribution-manifest.json](distribution-manifest.json) | 本次交付14包的SHA-256，与仓库dist清单一致 |
| [build-verify.json](build-verify.json) | 当前源码重建比较，全部输出零差异 |
| [完整unittest日志](program-design-installation-full-tests-passed.log) | 29项全部通过，包含4个新增安装检查；20.531秒 |
| [安装专项日志](program-design-installation-tests-final.log) | 4项通过，Gemini五事件为严格保留原ZIP mode的实际命令 |
| [执行位失败日志](program-design-installation-tests-executable-bits-failure.log) | 仅加引号后的中间失败：五事件退出126，原脚本0664不可直接执行；没有覆盖成通过日志 |
| [skill-regression.json](skill-regression.json) 及 baseline/migrated 日志 | 原始699文件树与当前924文件移植树，各4项frontmatter、4项版本、5项发现表面检查，共13项，均退出0 |
| [source-delta.json](source-delta.json) | 对照已归档的924文件清单，只变化7个源路径：6份Markdown及Gemini settings；每个变化保存前后hash/size/mode |
| [codex-package-delta.json](codex-package-delta.json) | 当前Codex包相对之前精确安装包仅变INSTALL与主Skill安装表，其他字节与mode不变 |
| [codex-preflight.tar.gz](codex-preflight.tar.gz)、[成员清单](codex-preflight-manifest.json) | 当前精确Codex包在原固定Docker镜像中的安装、cache逐文件检查、卸载与清理；无认证挂载、无模型调用 |
| [manifest.json](manifest.json) | 本目录证据逐文件摘要；不包含自身，README不作机器结果输入 |

复现本地检查：

```bash
python3 scripts/build-plugin.py --verify
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

定向上游检查分别在新的原始/移植源码副本中进行，副本有独立Git index；使用已有PyYAML，不安装新包。逐条命令见`skill-regression.json`，通过Python unittest运行上述三个`test_*.py`。本次没有重跑全量pytest或Node编译；原生Node源码、lock及相关配置与此前测试树相同。

本次Codex预检命令为：

```bash
python3 tests/run-pwf-smoke.py --preflight-only --output /tmp/program-design-installation-preflight-02
```

该输出目录必须是新目录。首次沙箱执行无法访问Docker socket，在建输出目录后退出；第一次授权重试因同名目录存在而拒绝，换新目录后通过。早期失败仅在本轮工具输出中保留，不声称有完整归档日志。固定镜像及原有容器保留，本次临时容器与工作目录均清理。预检通用assessment里的`model_process_succeeded`字段表示控制器进程退出0；`model_not_called=true`明确说明没有模型调用，不能把它解释为新模型维护样本。

最初安装扫描的21个错源命中和Gemini五次127只有会话工具输出，独立review保留摘要；不补造原始日志。安装入口扫描、Bash关闭测试和OpenCode静态loader检查不证明其他真实宿主可用。Windows/macOS、真实OpenCode/Gemini会话及本次模型维护均Not Run。
