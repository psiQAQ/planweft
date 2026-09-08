# PWF 3.17.0 移植回归证据

GNU mkdir 9.7 显式控制环境中，原始与迁移版完整 pytest 均通过：各 721 passed、63 skipped；原始 798 subtests，迁移补齐独立 Skill 资产后为 851 subtests。最终 18 个 SKILL.md 文案变更另经 30 tests、127 subtests 验证。Pi 54 tests、OpenCode 34 tests 及 typecheck/build 通过；复用 Node 结果前核对了 19 个源码文件 SHA。

本机默认 `/usr/bin/mkdir` 为 uutils coreutils 0.8.0；可重复探针 100 轮有 16 轮两个并发创建者同时返回成功，GNU 对照为 0。原始和移植 PWF 因而都可能丢失并发 phase 更新。保留生产锁实现，未更换系统工具；全量通过结果使用显式 `--tool-path`，不能将其描述成默认工具环境全部通过。源码的先检查、后创建与错误处理之间存在竞争窗口，与本地最小复现一致。[uutils 0.8.0 源码](https://github.com/uutils/coreutils/blob/0.8.0/src/uu/mkdir/src/mkdir.rs#L198)

## 文件

- `regression-evidence.tar.gz`：所有保存的原始/迁移测试轮次、命令、环境、日志、JUnit、失败 fixture、并发 trace、生成输入和最终源码 SHA 清单。没有 node_modules、venv、缓存、认证文件或重复的上游图片源码。
- `manifest.json`：归档内逐文件 SHA-256/size 与归档自身摘要。
- `summary.json`：最终结果与验证限制；历史失败也保留在归档中。
- `probe-mkdir.py`：独立于 PWF 的可重复并发目录创建探针，非零退出表示该次检查失败。

## 复现

先按仓库 `requirements-test.txt` 准备 Python 环境，再运行 `scripts/run-upstream-tests.py baseline` 或 `migrated`。必须指定已有 `--python` 和全新 `--output`；`--with-node` 显式执行 npm ci。默认不替换任何工具。

本机控制实验使用一个临时目录，其中 `mkdir` 链接到已有 `/usr/bin/gnumkdir`，然后显式传 `--tool-path`。runner 会记录实际工具路径与 SHA。工具控制目录和系统二进制未打入归档。Windows/macOS 与真实宿主试用结果需查看各自记录，本证据不代替它们。
