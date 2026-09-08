# 测试与 smoke 入口

在仓库根目录运行离线回归，无第三方 Python 依赖，不会调用 Docker、模型或真实认证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/experiments/check-entry-contract.py .
```

第一条验证分发、脚本协议、参数解析及副作用边界；第二条独立从 CLI/main 边界验收历史 smoke 的 13 个场景，包括默认值、帮助、repo-copy、多个合法场景，以及 enabled 成功/失败时是否执行 handoff。合法路径用假进程和假 HOME，不代表真实模型或 Windows 验证。

0.2.0 新增的 `test_pwf_distribution.py` 直接解压交付 ZIP 并调用包内脚本，覆盖 14 平台清单、路径与许可、唯一自动主入口、命令身份、计划选择与错误拒绝、三文件保护、attestation、真实 Codex JSON 协议、禁用与去重、模板解析、旧插件诊断、轻适配关闭和 Python 同名模块隔离。离线总数与结果以 [REP-0005](../docs/reproduction/0005-pwf-based-plugin.md) 为准。它们不模拟一个完整真实 Agent，也不替代宿主安装证据。

`test_pwf_installation.py` 另检查全部平台的原生安装入口、standalone 必需资产和本地包注册路径，扫描继承说明中的虚构发布源，并在中文及空格项目路径直接执行 Gemini settings 的全部五条 hook 命令。关闭场景要求输出 `{}`、项目与私有缓存保持不变。OpenCode loader 的编译目标检查属于静态安装契约，不算宿主加载验证。

## 0.2.0 固定上游与移植回归

构建只使用 Python 标准库；运行上游测试另需 [requirements-test.txt](../requirements-test.txt) 中固定的 pytest 和 PyYAML。使用已有 Python 3.12+ 测试环境，或在依赖安装已获授权时建立独立环境：

```bash
python3 -m venv /tmp/pd-test-venv
/tmp/pd-test-venv/bin/python -m pip install -r requirements-test.txt

# 原始699文件快照：baseline，不应用本地改动
python3 scripts/run-upstream-tests.py baseline --python /tmp/pd-test-venv/bin/python --output /tmp/pd-baseline-new --with-node

# 固定来源 + 身份映射 + 本地扩展：migrated
python3 scripts/run-upstream-tests.py migrated --python /tmp/pd-test-venv/bin/python --output /tmp/pd-migrated-new --with-node

python3 scripts/build-plugin.py --verify
```

输出目录必须不存在。runner 校验来源、建立独立 Git index（上游测试会枚举 tracked 文件），隔离 PWF 环境、Python PATH 和私有缓存，保存所有命令、退出码、JUnit、跳过原因与日志。`--with-node` 明确执行 Pi/OpenCode 各自锁文件的 `npm ci` 和测试；需要网络及已安装的 Node.js/npm。省略该选项会将 Node 检查记为 Not Run，不安装任何全局依赖。Pi 上游没有单独的 typecheck/build 命令，不虚构相应通过记录。

本机 uutils `mkdir` 0.8.0 的并发原语存在已复现问题，原始 PWF 也受影响。对照运行使用已有 GNU 9.7 `gnumkdir`，显式配置下面的临时 PATH；`--tool-path` 仅用于该次回归并记录实际工具 SHA，不改变产品或系统默认命令：

```bash
mkdir -p /tmp/pd-gnu-tools
ln -s /usr/bin/gnumkdir /tmp/pd-gnu-tools/mkdir
python3 scripts/run-upstream-tests.py baseline --python /tmp/pd-test-venv/bin/python --output /tmp/pd-baseline-gnu-new --tool-path /tmp/pd-gnu-tools
python3 scripts/run-upstream-tests.py migrated --python /tmp/pd-test-venv/bin/python --output /tmp/pd-migrated-gnu-new --tool-path /tmp/pd-gnu-tools
```

以上命令仅适用于已有该 GNU 可执行文件的环境；不自动安装或假定别的机器路径一致。原生失败、GNU 对照和最小复现都保留在 REP-0005 的回归证据中。

## 0.2.0 真实宿主试用

[run-pwf-smoke.py](run-pwf-smoke.py) 使用已存在的固定镜像 SHA、独立 tmpfs HOME 和本地 ZIP。先做不读取认证、不调用模型的安装预检：

```bash
python3 tests/run-pwf-smoke.py --preflight-only --output /tmp/pd-preflight-new
```

在具备 Docker、已有 Codex 认证及真实模型运行授权时执行：

```bash
python3 tests/run-pwf-smoke.py --output /tmp/pd-host-new
```

该入口不同于下方历史 0.1.0 实验，不安装到个人配置。默认记录未信任/一次性已审信任的 hooks 对照、无工具随机上下文标记、全新会话恢复、自动读取 Skill 的维护任务、无插件冷读、简单与只读请求。`--cases` 可选择子集及额外冲突场景；恢复须位于 trusted 场景之后。默认单次超时为 600 秒，合法范围 360–600；模型固定为 `gpt-5.6-terra`。使用 `--help` 查当前全部选项。

每次信任前逐文件核对已安装缓存与交付包；仅该次临时执行采用已审的 hook-trust 参数，个人 hooks 信任不改变。真实文件差异、模型原始 JSONL、缓存校验、卸载和清理分别保存；退出码不能代替维护与冷读的语义审查。镜像摘要、实际 CLI 版本、采样限制、初次失败和最终结果见 REP-0005。

## 0.1.0 历史模型 smoke

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
