# 测试与 smoke 入口

在仓库根目录运行离线回归，无第三方 Python 依赖，不会调用 Docker、模型或真实认证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tests/experiments/check-entry-contract.py .
```

第一条验证分发、脚本协议、参数解析及副作用边界；第二条独立从 CLI/main 边界验收历史 smoke 的 13 个场景，包括默认值、帮助、repo-copy、多个合法场景，以及 enabled 成功/失败时是否执行 handoff。合法路径用假进程和假 HOME，不代表真实模型或 Windows 验证。

`test_pwf_distribution.py` 直接复制 `dist/<host>/planweft/` 并调用目录内脚本。0.3.0 验证 14 平台目录、schema version 2 清单、逐文件 SHA-256 与执行位、规范 JSON 的树摘要、无残留 ZIP、Codex 兼容镜像，以及确定性重建。另对增、删、改、执行位和镜像漂移执行 `--verify`，要求拒绝漂移且不写任何文件。

原有脚本协议检查继续覆盖唯一自动主入口、命令身份、计划选择与错误拒绝、三文件保护、attestation、Codex JSON 协议、禁用与去重、模板解析、旧插件诊断和 Python 同名模块隔离。它们不模拟一个完整真实 Agent，也不替代宿主安装证据。历史 0.2.0 数量与实测结果保留在 [REP-0005](../docs/reproduction/0005-pwf-based-plugin.md)，不能作为 0.3.0 已通过的证据。

`test_pwf_installation.py` 检查原生安装入口、独立运行必需资产和虚构发布源，并检查 OpenCode 的预编译入口及相对模块齐全。在中文及空格安装、项目路径中，测试按 Gemini 官方 `${extensionPath}` 替换执行 `hooks/hooks.json` 的四条 hook 命令；关闭时要求输出 `{}`，安装目录、项目与私有缓存保持不变。这些属于静态安装与脚本协议检查，不算真实宿主加载验证。

`test_native_distribution.py` 检查六种根 catalog 各自指向正确的 `dist` 目录，构建保留其他插件条目，以及 smoke 预检在安装前拒绝内容、执行位、符号链接或来源路径漂移。没有调用 npm、远端 Git、宿主 CLI 或模型。

`test_native_hooks.py` 复制实际 Cursor、Copilot、Gemini 目录，验证原生 JSON 字段、中文与空格路径、计划/只读关闭、显式 attestation 的 gate 边界和篡改后的拒绝。这是包内脚本协议测试；实际宿主是否触发 hook 需要另行证据。

## 固定上游与移植回归

构建只使用 Python 标准库；运行上游测试另需 [requirements-test.txt](../requirements-test.txt) 中固定的 pytest 和 PyYAML。使用已有 Python 3.12+ 测试环境，或在依赖安装已获授权时建立独立环境：

```bash
python3 -m venv /tmp/pw-test-venv
/tmp/pw-test-venv/bin/python -m pip install -r requirements-test.txt

# 原始699文件快照：baseline，不应用本地改动
python3 scripts/run-upstream-tests.py baseline --python /tmp/pw-test-venv/bin/python --output /tmp/pw-baseline-new --with-node

# 固定来源 + 身份映射 + 本地扩展：migrated
python3 scripts/run-upstream-tests.py migrated --python /tmp/pw-test-venv/bin/python --output /tmp/pw-migrated-new --with-node

python3 scripts/build-plugin.py --verify
```

输出目录必须不存在。runner 校验来源、建立独立 Git index（上游测试会枚举 tracked 文件），隔离 PWF 环境、Python PATH 和私有缓存，保存所有命令、退出码、JUnit、跳过原因与日志。`--with-node` 明确执行 Pi/OpenCode 各自锁文件的 `npm ci` 和测试；需要网络及已安装的 Node.js/npm。省略该选项会将 Node 检查记为 Not Run，不安装任何全局依赖。Pi 上游没有单独的 typecheck/build 命令，不虚构相应通过记录。

本机 uutils `mkdir` 0.8.0 的并发原语存在已复现问题，原始 PWF 也受影响。对照运行使用已有 GNU 9.7 `gnumkdir`，显式配置下面的临时 PATH；`--tool-path` 仅用于该次回归并记录实际工具 SHA，不改变产品或系统默认命令：

```bash
mkdir -p /tmp/pw-gnu-tools
ln -s /usr/bin/gnumkdir /tmp/pw-gnu-tools/mkdir
python3 scripts/run-upstream-tests.py baseline --python /tmp/pw-test-venv/bin/python --output /tmp/pw-baseline-gnu-new --tool-path /tmp/pw-gnu-tools
python3 scripts/run-upstream-tests.py migrated --python /tmp/pw-test-venv/bin/python --output /tmp/pw-migrated-gnu-new --tool-path /tmp/pw-gnu-tools
```

以上命令仅适用于已有该 GNU 可执行文件的环境；不自动安装或假定别的机器路径一致。原生失败、GNU 对照和最小复现都保留在 REP-0005 的回归证据中。

## 0.3.0 无模型原生安装生命周期

[run-native-lifecycle.py](run-native-lifecycle.py) 使用已经安装的官方 Codex、Claude Code、Gemini CLI 或 Pi。它不安装 CLI、不继承认证或个人配置；每次命令使用临时 HOME、各宿主配置目录和独立 cache。输出目录必须是仓库外的新目录：

```bash
python3 tests/run-native-lifecycle.py --host codex --cli /absolute/path/to/codex --output /tmp/pw-native-codex-new
python3 tests/run-native-lifecycle.py --host claude --cli /absolute/path/to/claude --output /tmp/pw-native-claude-new
python3 tests/run-native-lifecycle.py --host gemini --cli /absolute/path/to/gemini --output /tmp/pw-native-gemini-new
python3 tests/run-native-lifecycle.py --host pi --cli /absolute/path/to/pi --output /tmp/pw-native-pi-new
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--host` | 必填 | `codex`、`claude`、`gemini` 或 `pi` |
| `--cli` | 必填 | 已安装的官方可执行文件；runner 不下载宿主 |
| `--output` | 必填 | 新证据目录；存在或位于本仓库内则拒绝 |
| `--timeout` | `120` | 每个 CLI 命令的秒数，范围 1–300 |

runner 先核对交付 manifest，再制作带资源增、删、改标记的 0.3.0 / 0.3.1 临时 fixture；后者是测试版本，不是发布产物。流程覆盖安装 A、更新到 B、卸载后回退 A、最终卸载和临时 profile 清理，每阶段核对安装目录的文件字节与执行位，并保护项目已有记录。原始命令、输出、输入确认、逐文件差异、runner 快照与摘要均保存。Codex 额外通过无认证的 `app-server skills/list` 观察安装缓存中的六个入口；该 API 不暴露 implicit invocation policy，不能据此声称实际自动调用行为已验证。

受保护 fixture 包含三份任务记录、用户便笺，以及固定内容的 `docs/specs/approved.md`、`docs/adr/decision.md`、`docs/reproduction/known.md`。递归前后清单真实覆盖这些嵌套文档；OpenCode 使用同一组 fixture 并逐条保存保护结果。修改或删除任一长期文档会导致失败，不能用只检查根目录三文件的旧结果证明长期文档保护。

Claude 使用原生 marketplace/plugin update；Gemini 使用记录的本地目录执行 `extensions update`，仅确认已审 fixture 的目录信任及安装/升级提示。Codex 本地 marketplace 更新通过再次 `plugin add` 验证；Pi 从实际 `npm pack` tarball 执行原生 npm-source 安装并显式替换版本。后二者不等同远端更新验证。Claude 卸载后可能保留 orphan cache，runner 分别记录注册移除与 cache 残留，最后删除整个临时 profile。上述运行不调用模型；公开 npm/Git 渠道、真实会话中的 reload 与其他 OS 仍需单独验证。

[run-opencode-native.py](run-opencode-native.py) 使用已安装的 OpenCode V1，在临时包副本中执行 `npm ci --omit=dev --ignore-scripts`，因此运行此探针需要已授权的依赖下载。它使用临时 HOME/cache、项目 loader 和单独复制的主 Skill；不继承认证或个人配置，不修改传入包：

```bash
python3 tests/run-opencode-native.py --cli /absolute/path/to/opencode --package /absolute/path/to/prepared/opencode --output /tmp/pw-opencode-native-new
```

`--package` 默认为本仓库 `dist/opencode/planweft/`，`--cli` 与 `--output` 必填，输出必须是仓库外的新目录。真实 `debug config`、`debug agent build`、`debug skill` 检查三项 `pw_` 工具和唯一 `project-docs`，核对宿主报告的 Skill 路径、全部复制内容及五种语言资源，拒绝额外变体入口；随后直接执行工具，核对 A/B/回退的实际插件版本、Skill 资源增改删、包内模板来源、移除后的发现结果，以及已有项目记录和来源包不变。`skill-fixture-delta.json` 记录三个资源变化类别，完整安装内容比较拒绝残留旧文件。debug 工具执行只读取模型元数据，fixture 模型没有真实认证且指向拒绝连接的本地地址，不发送模型请求。此探针证明本地 file URL 加载与新进程的配置切换；远程 npm 安装更新、现有会话 reload 和其他 OS 均未覆盖。每次运行保存命令日志、runner/helper 快照及摘要。

## 0.3.0 目录分发的真实模型试用入口

[run-pwf-smoke.py](run-pwf-smoke.py) 使用已存在的固定镜像 SHA、独立 tmpfs HOME 和本地 Codex 原生目录。它先核对 schema version 2 的文件与执行位清单，再复制根 catalog 与 `dist/codex/planweft/` 到临时仓库布局，交给原生 CLI 注册、安装和卸载。可先做不读取认证、不调用模型的安装预检：

```bash
python3 tests/run-pwf-smoke.py --preflight-only --output /tmp/pw-preflight-new
```

在具备 Docker、已有 Codex 认证及真实模型运行授权时执行：

```bash
python3 tests/run-pwf-smoke.py --output /tmp/pw-host-new
```

该入口不同于下方历史 0.1.0 实验，不安装到个人配置。默认记录未信任/一次性已审信任的 hooks 对照、无工具随机上下文标记、全新会话恢复、自动读取 Skill 的维护任务、无插件冷读、简单与只读请求。`--cases` 可选择子集及额外冲突场景；恢复须位于 trusted 场景之后。默认单次超时为 600 秒，合法范围 360–600；模型固定为 `gpt-5.6-terra`。使用 `--help` 查当前全部选项。

每次信任前逐文件核对已安装缓存与交付目录，包括运行脚本的执行位；仅该次临时执行采用已审的 hook-trust 参数，个人 hooks 信任不改变。真实文件差异、模型原始 JSONL、缓存校验、卸载和清理分别保存；退出码不能代替维护与冷读的语义审查。REP-0005 中的镜像、CLI 与模型结果属于历史 0.2.0；0.3.0 必须保存新的运行证据。目录预检不证明远端 npm/Git 发布安装可用，未执行的发布渠道和宿主须记为 Not Run。

## 0.1.0 历史模型 smoke

[run-plugin-smoke.py](run-plugin-smoke.py) 是需要明确模型运行授权的 Linux 容器实验脚本。它会访问已有 Codex 认证和 Docker，并产生完整任务与运行记录。这里只列用法；离线回归不执行这条命令。

```bash
python3 tests/run-plugin-smoke.py --output /tmp/planweft-smoke-new --model gpt-5.6-terra --cases enabled repo-copy --timeout 360
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
python3 tests/experiments/run-maintenance-comparison.py --output /tmp/planweft-paired-new
```

真实结果、执行限制及证据解包方式见 [REP-0004](../docs/reproduction/0004-paired-maintenance-trial.md) 和[证据说明](../docs/reproduction/evidence/0004/README.md)。本轮没有正式启用本仓库自身管理。

## 0.3.0 补充检查

`test_native_release.py` 检查发布参数无副作用拒绝、旧 ZIP 所有权、编译输入/输出篡改拒绝和 Git 发布父提交连续性。`test_native_resource_paths.py` 检查单独复制 Skill 后的完整语言资源，以及 Kiro 从安装目录定位脚本的约束。

[run-marketplace-lifecycle.py](run-marketplace-lifecycle.py) 复用隔离生命周期核心，支持 Copilot CLI 与 CodeBuddy：

```bash
python3 tests/run-marketplace-lifecycle.py --host copilot --cli /absolute/path/to/copilot --output /tmp/pw-copilot-new
python3 tests/run-marketplace-lifecycle.py --host codebuddy --cli /absolute/path/to/codebuddy --output /tmp/pw-codebuddy-new
```

[run-codex-hook-probe.py](run-codex-hook-probe.py) 用真实 Codex 和本地合成 Responses 服务检查未信任、单次已审信任、全新会话恢复及 PLANNING_DISABLED 四个场景。只在本次调用中信任已核对字节，不修改个人信任；不读取认证或发送外部模型请求。需要允许 loopback 监听；CLI 如压缩请求，Python 3.14 的标准库 zstd 用于读取该请求。此探针不验证模型理解或维护质量：

```bash
python3 tests/run-codex-hook-probe.py --cli /absolute/path/to/codex --output /tmp/pw-codex-hook-new
```

输出保存 runner、实际源清单、调用日志、合成请求与保护检查。Factory/Hermes 的一次性真实 CLI runner 和精确下载来源保存在 [REP-0006 证据](../docs/reproduction/evidence/0006/README.md) 中；Hermes 默认扫描拒绝不得写为安装通过。

## 双语公开文档

`test_public_docs.py` 核对首页、安装指南、跨平台设计、overlay 与全部平台包的语言切换和相对链接，并比较完整中英安装命令块。分发漂移测试另验证手改 `docs/installation.en.md` 会被 `--verify` 拒绝且不自动修复。实际 npm 打包由发布准备入口检查两种安装文档与英文 README 都随包携带。

这些检查证明导航、命令与分发完整性；语义翻译、比较公平性和原创归属由独立 review 核查。安装正文只修改 overlays 的中英文源，再统一构建；仓库指南是生成镜像。公开入口：[项目介绍：中文](../README.md) / [English](../README.en.md)，[安装：中文](../docs/installation.md) / [English](../docs/installation.en.md)，[跨平台：中文](../docs/platforms.md) / [English](../docs/platforms.en.md)。

## Published npm candidate

`run-registry-smoke.py --version VERSION --sha256 SHA256 --output /tmp/new-registry-run --cli-dir /isolated/host/bin` downloads the exact registry tarball, verifies its digest, exercises scoped native installs for four core hosts, removes the disposable npx cache and checks the persistent runtime, and loads the direct Pi/OpenCode npm entries. It reads no personal model credentials. Single-version update idempotence is not cross-version remote lifecycle acceptance.

## DeepSeek Harness

`run-installer-lifecycle.py --host dsh` covers isolated official DSH/pnpm profile installation, A/B payload changes, rollback, removal and config composition. `run-dsh-skill-smoke.mjs` exercises the native provider; `run-dsh-hook-probe.mjs` uses the published bridge and real subprocesses with an explicit event carrier. These probes do not invoke a model or claim model-session acceptance. See REP-0009 for source versions and actual limits.
# 五 Agent 准确归档验收（0.4.0）

`run-five-agent-release.py` 使用 `container-images.json` 的固定镜像和独立 HOME；仅挂载合成项目、准确 npm 归档与测试运行器。原 Lab 入口和清记忆脚本不参与。

```bash
python3 tests/run-five-agent-release.py \
  --archive /path/to/planweft-VERSION.tgz \
  --output /path/to/new-external-output \
  --host codex --host claude --host pi --host opencode --host dsh \
  --cases preflight lifecycle
```

模型场景需另行提供现有认证文件引用，并事先取得真实模型调用授权。`--model-config` 只读取已部署 upstream YAML 中所选官方 DeepSeek URL/key；不挂载完整配置，不发送 Lab 身份头；Codex 通过 `--codex-auth` 指定既有认证。不要在参数或公开日志中写密钥。

`context recovery` 必须按此顺序运行；`maintenance cold-reader` 同样配对。冷读复制维护后的项目文件，使用全新会话。自动断言只证明明确观察项，语义结论需要独立 review；不支持的事件或缺失记录不得当作 Passed。准确归档测试与 `run-installer-lifecycle.py` 的合成 A/B 变体分开报告。

远端回归接受 `--version/--sha256` 和成对的 `--previous-version/--previous-sha256`；只有真实下载的两个版本才能证明远端 A→B→A→B→卸载。单版本只证明幂等。模型新会话和公开 Git marketplace 是独立验收项。

以上为内部开发文档；对外说明见 [发布：中文](../docs/releasing.md) / [English](../docs/releasing.en.md)。

Model trials can use `--direct-provider-config /private/tmpfs/provider.json` instead of the legacy `--model-config`. The private JSON must contain exactly `base_url` and `api_key`; only the official DeepSeek HTTPS hostname is accepted, without user info, query strings, or gateway fields. Keep this file outside projects and evidence, restrict it to the current user, and remove it after trials. Credentials reach containers via stdin and remain in tmpfs. No private configuration should be committed.

OpenCode 实际平台运行时对照（锁定依赖安装在新临时目录）：

```bash
python3 scripts/run-opencode-tests.py --output /tmp/planweft-opencode-regression-new
```

保留上游原字节测试、原生未调整结果，以及两项明确本地差异的适配结果：无计划 Skill 提醒、安装包/显式模板来源。附加测试验证无写盘、去重、禁用及项目模板不能替换安装资源；协议通过不代替模型验收。


## 原生停止证据

`run-five-agent-release.py` 提供 `stopping`、`gated-continuation`、`gate-cap`、`gate-stall`；Pi 使用 `stopping` 和独有 `continuation-limit`，不模拟 Shell ledger gate。非 DSH 的 cap/stall 要先运行同夹具的 `gate-cap-disabled` / `gate-stall-disabled`，否则参数校验拒绝执行。所有场景需要准确归档和隔离模型认证，按既有授权使用。

计数访问由 Linux inotify 在模型进程期间观察，不能提供 PID 归因；负对照同样读取时保持 Failed。DSH 另外记录原生 Stop block/pass。Pi RPC 等到 settled、空队列和自然 EOF；不在首个 agent_end 结束。新运行保存 runner、runtime、fixture 源码与摘要。`scripts/reassess-stop-evidence.py --run RUN --output NEW_JSON` 可重判历史原始数据，明确不是模型重跑且不改原文件。
# 进程归因补充

`run-five-agent-release.py --trace-gate-processes` 仅接受 Codex/Claude 的停止场景和记录 `gate_trace.strace=6.1` 的固定派生镜像锁。不会自动安装 strace 或更换原镜像。使用 `gate_process_trace.py` 的 syscall 集合和摘要绑定解析；正负对照都要求完整 trace，原始 argv 不导出。`test_gate_process_trace.py` 覆盖快照误归因、异步调用、PID/FD 复用等反例。该可选 Linux 证据路线不代表 Windows/macOS 的真实宿主验证。

OpenCode 停止场景使用 `opencode_server_probe.py`，固定 1.18.22 的原生 serve/SSE/Session API。仅发送一次初始提示，保留消息 parentID、idle 和状态对账，观察至少 5 秒静默；不把原生 CLI 首次 idle 当作异步续跑完成，也不宣称存在 native settled。超时、权限请求、工具调用、断流、模型错误和清理异常均失败；原始事件先经 runtime 脱敏再保存。`test_opencode_server_probe.py` 为离线 transport/process fixtures，真实 HTTP/模型证据见 REP-0010。


### Pi 上下文探针与执行循环

Pi 的 `/pw-plan-execute` 同时启用 hooks 与未完成计划的续跑，parity 全文注入并不是独立的只读模式。`context` / `recovery` 新探针使用新建的完成态合成计划，完整采集到 `agent_settled`，并记录 `probe_scope`，仅证明完成态计划的注入和新会话文件恢复。不会把既有进行中计划改成完成态；该前置条件不满足时拒绝运行。`continuation-limit` 保持进行中计划，单独验证执行循环；默认未激活停止也单独验证。旧进行中只读探针产生的实际续跑与写入保留为 Failed，不通过截断首轮改判。


### 公开 Git 与审查反馈闭环

`run-public-git-marketplace.py --host codex|claude --commit <完整公开master SHA> --version <版本> --output <新目录>` 使用固定镜像和无认证的隔离 HOME，核对公开 Git 与缓存内容、执行位、同提交市场刷新、重装、卸载及注销。它不调用模型，不声称覆盖 Git 跨版本更新；容器清理失败返回失败。运行脚本副本和摘要一并保存。

`run-review-feedback.py` 复用实际五宿主 controller 的 owner 与冷读分支。输入必须提供准确包、原维护 `after.json`、原自动 assessment、独立 review JSON 及各自 SHA-256；目前限 Pi/DSH。review v1 绑定宿主、准确包、原快照和 assessment，并保存原语义 Failed、原任务范围、允许修正的已有记录路径与具体发现。代码、测试、批准需求及用户内容必须此前验证通过，本轮字节保持不变。新容器只获得原项目文件和简短事实反馈；后续冷读只获得修正后的项目文件，不获得 review、旧聊天、历史或安装缓存。

所有输入/参数在创建输出、访问认证或 Docker 前校验，单模型场景限 30–600 秒。该入口不修改原运行；成功完成自动边界检查也仅标 `Awaiting independent semantic review`，仍需独立核对发现是否真正修正、状态与错误记录是否准确。Docker bootstrap 只记录退出/超时/耗时，不归档可能含私有配置的输出；原生 runtime 的脱敏诊断在可用时保留，报告明确此限制。两阶段与原失败分别留存，不能称首轮维护从未失误。

### 资源约束与中断恢复

五宿主模型测试保持串行。容器限制 2 CPU、3 GiB RAM、256 个进程，`--memory-swap=3g` 禁止额外占用 Swap；HOME tmpfs 上限 2 GiB，临时目录 512 MiB。共享 HOME 安装隔离使用同样 CPU/RAM/进程限制；HOME、项目、源包和安装临时文件置于输出磁盘目录，容器 `/tmp` 为 512 MiB tmpfs。限额导致的失败必须保留，不能标为宿主不支持；运行结束核对并清理本次容器。

`/tmp` 可能是内存文件系统。大安装缓存、构建工作目录优先放在有余量的磁盘目录；仅清理确认不再被进程引用的本次可重建依赖/下载缓存，保留准确 tarball、原始失败、源码和日志。`project_snapshot` 在读取前剪枝顶层安装目录，避免把缓存全部载入内存后再过滤；嵌套同名文档仍被核对。模型启动前保存 before 与 In Progress，意外终止不能补写成 Passed。

共享 HOME 原生隔离入口为 `tests/run-project-isolation.py`，显式传入 `--host`、新旧 `--archive`/`--old-archive`、对应 `--sha256`/`--old-sha256` 和新的 `--output`；超时 `--timeout` 默认 240 秒。Claude/Pi/OpenCode 检查 A 旧版本、B 新版本，更新/移除 A 后 B 的来源、版本和内容保持不变；Codex/DSH 检查不支持的项目 scope 在写入前拒绝。全程无模型、关闭 hooks，不作为 hook 去重或模型权限验收。

## RC6 资源与逐场景发布门槛

五宿主入口在访问认证/Docker 前检查 4 GiB 可用内存及输出磁盘 8 GiB 空间，输出应使用磁盘目录（如 `/var/tmp/planweft-validation-new`），避免大型缓存占用 tmpfs。每个模型场景限时 30..600 秒；仍使用 2 CPU、3 GiB 内存且不额外使用 Swap、256 PID。先确认容器已移除，再删除自有 `agents={}` 的未引用版本缓存，保留项目记录、收据、快照和日志；无法确认时停止新场景。

稳定验收使用 acceptance schema 2：每个总项下列出 `observations.scenarios`，逐场景包含 Passed 和摘要绑定的实际附件。准确所需场景由 `scripts/check-release-gate.py:required_scenarios` 定义。旧 schema 1 不放行；当前没有历史稳定 acceptance 需要自动迁移。候选版仍仅允许 next。


### 原生跨 scope 重复注册预检

```bash
python3 tests/run-fixture-containers.py --scenario native-duplicate \
  --host opencode --archive /path/to/planweft-VERSION.tgz \
  --sha256 EXACT_SHA256 --output /var/tmp/planweft-native-duplicate-new
```

该场景目前支持 Pi/OpenCode：从准确归档完成真实 global 安装及原生发现，然后执行同包 project `add --dry-run`，要求拒绝并保持原生配置和项目文件；再检查自有 doctor/update 预检与移除记录。Pi 的 `list` 仅证明包注册，不替代 RPC Extension 实际加载。OpenCode 的工具及 Skill 发现也不证明两个 handlers 已执行。此项称为“防止第二套原生注册”，不称为运行时提醒去重；实际模型消息投递另行验收。

包装器在创建输出和 Docker 调用前校验归档、参数与资源，串行限制 2 CPU、3 GiB、无额外 Swap、256 PID、600 秒；失败中止后续宿主，保留失败和原始记录并核对容器清理。默认 `--scenario payload-delta` 仍是修改后 A/B fixtures，与准确发布归档的此项预检证据分开。

Codex `--cases reminder-dedup` 使用同一 app-server thread 的两个串行 turn，原生 TUI 信任，不使用信任绕过。收集 `hook/started` / `hook/completed`、fileChange 与 raw protocol；按线程、轮次、hook ID、准确安装源绑定，检查每轮首次提醒与后续抑制。仅支持 Codex，其他宿主启动前报错。模型文字复述、背景读取计数器或第二次 SessionStart 不作为提醒去重证据；首次 SessionStart 可以位于第一 turn/started 后，但必须早于任何 reset/tool 且完整成功。观察结束后关闭所属服务器，不冒充服务器自然退出。原始检查器失败的重判须新建带摘要的派生审查，不覆盖原结果。
