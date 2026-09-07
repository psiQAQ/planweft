# 测试与 smoke 入口

在仓库根目录运行离线回归，无第三方 Python 依赖，不会调用 Docker、模型或真实认证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/experiments/check-entry-contract.py .
```

第一条验证参数解析及副作用边界；第二条独立从 CLI/main 边界验收 13 个场景，包括默认值、帮助、repo-copy、多个合法场景，以及 enabled 成功/失败时是否执行 handoff。合法路径用假进程和假 HOME，不代表真实模型或 Windows 验证。

## 真实模型 smoke

[run-plugin-smoke.py](run-plugin-smoke.py) 是需要明确模型运行授权的 Linux 容器实验脚本。它会访问已有 Codex 认证和 Docker，并产生完整任务与运行记录。这里只列用法；离线回归不执行这条命令。

```bash
python3 tests/run-plugin-smoke.py --output /tmp/program-design-smoke-new --model gpt-5.6-terra --cases enabled repo-copy --timeout 360
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--output` | 必填 | 新输出目录；存在则拒绝覆盖 |
| `--model` | 必填 | 真实运行使用的模型 |
| `--image` | `agent-memory-lab/codex:local` | 已有 Docker 镜像 |
| `--cases` | 下列七个常规场景 | 一次选择一个或多个不同合法场景；可额外选择 repo-copy |
| `--timeout` | `360` | 每次执行的正整数秒数；零、负数与非整数均拒绝 |

默认场景：`enabled`、`unenabled`、`unrelated`、`readonly`、`conflict`、`blank`、`evidence-gap`；额外合法场景为 `repo-copy`。`handoff` 是 enabled 成功后的内部阶段，不接受用户指定；enabled 失败时不会运行它。

未知场景、解析所得列表中的重复项（例如 `--cases enabled enabled`）或非正超时都以退出码 **2** 和清楚的参数错误结束，发生在创建输出目录及其父目录、调用 Docker、定位认证之前。`--help` 以退出码 **0** 给出帮助，也不执行这些副作用。依据见 [argparse 摘要](../docs/reference/python-argparse.md)。

## 固定基线的配对试用

[run-maintenance-comparison.py](experiments/run-maintenance-comparison.py) 仅复现 [PLAN-0004](../docs/plans/0004-paired-maintenance-trial.md) 的一次实验：固定旧基线 `a5f072e`，安装/不安装两种条件，四次实施与四次无插件冷读。它不是通用评测框架，也不用于日常离线回归。

运行需要重新具备模型授权、已有镜像和认证；输出必须是仓库外的新目录：

```bash
python3 tests/experiments/run-maintenance-comparison.py --output /tmp/program-design-paired-new
```

真实结果、执行限制及证据解包方式见 [REP-0004](../docs/reproduction/0004-paired-maintenance-trial.md) 和[证据说明](../docs/reproduction/evidence/0004/README.md)。本轮没有正式启用本仓库自身管理。
