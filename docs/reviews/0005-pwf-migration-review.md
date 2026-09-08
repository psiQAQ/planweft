# REV-0005：PWF 移植来源与分发审查

日期：2026-09-08；状态：已完成本范围独立复审，所列 P2 均关闭，旧适配能力差异保留为明确限制。范围是本轮实际读取的固定来源、构建器、移植内存树、14 个最终 ZIP 及有限 Shell 协议验证，不是全部平台运行验收。真实宿主、完整回归及模型维护结果另见 REP-0005，不从本报告推定。

## 独立性与检查范围

reviewer 没有编写导入器、构建器或运行时补丁；本轮参与编写了 SPEC-0003、ADR-0006 和安装说明，因此这些自写文档不在本报告的独立审查结论内。对实现的检查从固定上游源码和实际生成结果开始，不以主 Agent 的通过声明替代证据。

实际读取：PWF v3.17.0 的 Skill、Codex/Claude manifests/hooks、Pi/OpenCode package、Hermes 插件注册与资产解析、Cursor/Gemini/Copilot/Mastra hooks、Kiro bootstrap、Continue/Factory/CodeBuddy 安装表面；第一方 `scripts/import-pwf.py`、`scripts/build-plugin.py` 和 workflow overlay。官方 hooks 的 manifest/trust/多个匹配来源行为已于本日在线核对；Pi 本地 package 安装语义对照研究目录中固定官方 packages 文档。没有安装或运行研究工具。

初检输入 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `scripts/build-plugin.py` | `92a5df35a368dab5b31e4eb7955a6cf902f7c44da7bd795cfa5a05f2be3f9666` |
| `scripts/import-pwf.py` | `ce84b946883f51d187cc519ce5c33c7a07a1eae92dd92ad99313b14230e05322` |
| `overlays/program-design/workflow.md` | `13f006361677c88caf46ae3b34453b7954462df0592aefd66ae4477efd0c569b` |

初检用 Python 标准库导入 builder，在内存调用 `read_upstream()`、`transform()`、`distributions()`；没有运行上游脚本，也没有将审查用产物覆盖正式输出。此后 builder 若有变化，结果须更新到新摘要。

## 已确认的证据

| 检查 | 实际观察 | 边界 |
| --- | --- | --- |
| 固定来源与导入 | importer 核验 HEAD、tag 解析及 clean status；archive/inventory 经 builder 读取验证，699 个原始文件 | 不是远端 tag 长期不可变的保证；当前允许提交固定在源码 |
| 路径映射唯一性 | 699 个源路径按 `map_path` 映射，无目标碰撞 | 不能代替字符串内调用路径检查 |
| 平台根许可 | 14 个内存分发均含与原始 LICENSE 字节一致的 MIT 许可 | 单独复制 Skill/plugin 子目录的许可见发现 R5 |
| Codex Windows 编码入口 | 7 个 EncodedCommand 解码均指向 `PLUGIN_ROOT/.codex/hooks/pwf-hook.cmd`，传入 plugin_dispatch.py；目标包有相应 launcher/dispatcher | 仅解码与存在性核查，未在真实 Windows 执行 |
| OpenCode 构建路线 | 本地源码 package 的 main/exports 指向 dist；安装说明改用锁文件安装、build 与 re-export dist | 尚未在本 reviewer 的真实 OpenCode 中验证 |
| 历史状态 | `.planning`、PWF 环境变量和计划文件仍沿用原协议；Kiro 保留不同原生布局 | 根文件旧适配不能据此宣称命名任务隔离 |

## 发现与处理

| ID / 级别 | 触发、问题及影响 | 当前处理 |
| --- | --- | --- |
| R1 / P2 | Claude marketplace 最初仍标 3.17.0、上游 owner 和跨 60+ Agent 宣传，导致派生包身份与 plugin manifest 不一致 | Closed；直接解析最终 Claude ZIP，owner 为 Program Design contributors，插件 identity/version 为 program-design / 0.2.0；真实宿主安装另验 |
| R2 / P2 | identity_text 的 Windows 正则只匹配双反斜杠；canonical 与多个宿主 Skill 中单反斜杠 `skills\program-design` 指向不存在目录 | Closed；正则现覆盖一个或多个反斜杠；最终 89 个 Skill 未残留错误 `skills/program-design` 或反斜杠形式；7 个编码 launcher 路径与目标存在性仍正确 |
| R3 / P2 | canonical Skill 被用于 Codex/Pi 等包，但显式 history 命令仍 fallback 到用户 Claude Skill 路径；独立安装后正文命令不可用 | Closed；增强阶段移除 history 代码块中的 Claude 路径假设，改为已读取 Skill 的绝对同目录 helper，保留 metadata/replay 显式授权边界；最终 89 个 Skill 逐代码块复核 |
| R4 / P2 | doctor 只枚举新 project-docs 的 Claude/agents 目录，不查原 PWF，未对多安装表面告警；不能兑现可检测重叠的说明 | Closed；加入只读旧目录探测；实际在临时项目预置 `.agents/skills/planning-with-files` 后运行包内 doctor，输出原版安装提示与“不证明激活”说明，项目文件快照不变 |
| R5 / P2 | ZIP 根有 MIT 许可，但手工 standalone 安装只复制 Skill/Hermes plugin 子目录后没有 LICENSE/UPSTREAM | Closed；最终 89 个 Skill 安装根均有原文 LICENSE 与 0.2.0 UPSTREAM；Hermes 插件根另有两文件；Pi/OpenCode npm allowlist 保留许可 |
| R6 / P2 | Continue Skill 的三模板本地链接目标缺失；Hermes、CodeBuddy 各缺 reference.md/examples.md；包内 common 同名文件无法支持文档所述 standalone 拷贝路线 | Closed；仅补缺失资产并保留宿主已有文件；最终 89 个 Skill 的 547 个包内相对链接均可解析，Continue 三模板及 Hermes/CodeBuddy 说明存在 |
| R7 / 能力限制 | Cursor/Gemini/Copilot/Mastra 部分旧 hooks 直接读根 task_plan.md；Mastra/Gemini 部分入口未检查 PLANNING_DISABLED | 关闭缺口已修；5 个 Gemini 脚本和 4 个 Mastra command 实际设置 PLANNING_DISABLED=1 后立即返回，项目快照不变。root-only 机制保留；workflow 和安装文档明确缺少命名并发计划同等能力，不作为未披露兼容宣称 |
| R8 / P2 | Codex ZIP 最初只有 plugin manifest，没有可独立注册的 marketplace；只有源码仓库能按既有命令安装 | Closed；最终 ZIP 中 `.agents/plugins/marketplace.json` 为 program-design-local，source.path 为 `./`，能指向同包插件根；文档给出当前 CLI add/remove 命令，真实安装由 REP-0005 承接 |
| R9 / P2 | Continue 的 `.prompt` 未进入仅处理 `.md` 的辅助入口映射；仍为 program-design 名称且无只读/所属计划前置规则，正文直接初始化根三文件 | Closed；最终为 `.continue/prompts/pd-plan.prompt` / `name: pd-plan`，前置只读及任务所属计划约束，旧文件不再分发 |

以上发现来自实际源码、内存分发或安装层级检查；没有将假想平台风险列作确认 bug。R7 的保留属于已披露能力差异，不能在兼容矩阵中再写为全平台相同选择器、门禁或模式识别。

## 最终复审与新增补丁

最终审查同时检查实际 ZIP 字节与生成源，不只检查内存树。`python3 scripts/build-plugin.py --verify` 输出 14 平台，Codex/产物差异均为 0。逐包复核 manifest 中的 ZIP 摘要与文件数；每包 INSTALL 与受审 overlay 一致。89 个 Skill 的许可/来源与 547 个包内相对链接均通过断言。Hermes 的 Skill 注册、pd 命令 tuple 和 OpenCode `findSkillDir` 已指向 project-docs；OpenCode 仍是带锁文件的源码包，安装需要本地构建。

对 inline Python `-I` 补丁，读取 builder 的具体替换范围和最终 hook 命令：仅给 Shell hooks 的内联 Python 增加 isolated mode，不移除用绝对包内路径显式导入 Codex helper 的代码。独立临时目录用同名 `json.py` 写标记文件，普通 `python3 -c 'import json'` 确实加载该项目文件；清除标记后实际执行最终 Gemini before-model/before-tool、Copilot pre-tool/session-start 四个 hook，全部输出可解析 JSON，均未加载该文件。说明该补丁覆盖已测 cwd module-shadowing 场景，不据此宣称全面 Python sandbox。

Gemini/Mastra 的 9 个关闭入口和 doctor 重叠探测在独立临时目录执行；前后项目文件内容快照一致。临时目录由 TemporaryDirectory 清理，无需修改个人配置或全局安装。未运行相应真实宿主进程，这些结果是脚本/协议级 Passed。

最终受审输入 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `scripts/build-plugin.py` | `1e1c84ead8a160c975ade4c0aabbc12a8b893aed57493f9a69449df3f5c988d4` |
| `scripts/import-pwf.py` | `ce84b946883f51d187cc519ce5c33c7a07a1eae92dd92ad99313b14230e05322` |
| `overlays/program-design/workflow.md` | `ad23d7eebc2ab108d86020f897bd68f0c2f3e573baf3992da08f110c83a77205` |
| `overlays/program-design/doctor-overlap.sh` | `24e2ed6772068833fd40999f88e1aeeca06b9f8079768da314ee9489d84030bf` |
| `overlays/program-design/install/INSTALL.md` | `105c98bc66a9d4083b7eb9bb63b16d6e50cc66d147d9b2c3e2710572b18477b0` |
| `dist/manifest.json` | `b0c79a5629e7f2a0e299bb71312cea8b0c68e64ff7e8b7eae200c8084ec22e49` |

## 验证限制与交接

本 reviewer 未执行完整 pytest、Vitest、真实模型任务或 Windows/macOS 宿主；对应结果统一由 [REP-0005](../reproduction/0005-pwf-based-plugin.md) 承接。主 Agent 报告的上游基线数量不作为本报告独立执行的 Passed。

本范围未发现剩余阻断项。安装命令的当前 Codex CLI 名称已直接通过 `--help` 核对为 `plugin add/remove`；这只证明命令解析表面，不是插件实际加载。若之后修改上表的冻结输入，需针对改动重跑有关检查；后续新增差异按下节单独记载，完整回归结果和真实模型会话不由本 reviewer 代为认领。

## 新增差异复核：测试 fixture、回归与说明

本补充仅检查主 Agent 在上次冻结后新增的 builder 测试 fixture 适配、分发测试和文档差异，没有重复全部 ZIP 审查。reviewer 以前参与编写的规格、ADR、平台及维护说明主体仍不转为自己的“独立审查通过”；本节只核对主 Agent 新增内容与实际源码的对应。

| 新增范围 | 核对与实际结果 |
| --- | --- |
| Hermes bridge fixture / PD-P07 | 查看固定上游 `_candidate_script_dirs()`、原测试与 builder 替换。补齐资产后，原 bridge 按既有顺序找到包内 fallback；新测试先断言该行为，再把单个 bridge 复制到无脚本的临时安装根，保留原 `{}` silent-noop 断言。只在 enhanced 树中改测试，不改运行时；目标断言数量不等于 1 时 builder 明确拒绝继续 |
| fixture 的定向运行 | 在两个独立临时副本分别执行原始 baseline 和 enhanced 的 `HermesFirstClassTests.test_shell_hook_bridge_translates_inject_and_gate`，两者各 1 项 Passed；enhanced 保留 inject/gate/未知事件/缺脚本断言，未删除原功能验收 |
| 新 CLI 构建测试 | 测试实际复制 scripts/overlays/vendor 到独立根，调用 builder 两次比较生成物，再故意修改生成 Skill；`--verify` 返回 1、指出路径且不覆盖被修改目录及 dist。不是调用相同计算函数来证明自身正确 |
| 独立运行新增相关测试 | 只定向运行 5 项：真实 CLI 重建与漂移、每 Skill 许可/来源、9 个旧适配关闭命令、Gemini cwd/PYTHONPATH 同名 json.py 隔离、doctor 不执行旧插件。5 项 Passed，15.823 秒；不冒充本 reviewer 跑过完整 25 项 |
| 首页、开发与测试说明 | 新入口对应 SPEC-0003/PLAN-0005 和本地 dist；命令、Python/Node 依赖、可选 `--with-node`、smoke 参数与源码匹配。描述把协议检查、真实宿主和语义判断分开，没有将旧 0.1.0 结果转换为新版本通过 |
| 维护说明、逐文件台账、PATCHES | `--identity-only` 现明确仍保留运行时补丁、不补 standalone 资产；原始基线应使用 baseline 模式。PD-P01～07 对应实际生成器分支及原始文件，普通胶水不包装成新原创机制；PD-P07 的 fixture 原因、原断言与运行时不变均有来源支持 |

这次独立临时 CLI 重建结果与交付 dist 一致，`dist/manifest.json` 摘要仍为 `b0c79a5629e7f2a0e299bb71312cea8b0c68e64ff7e8b7eae200c8084ec22e49`，因此先前 ZIP 审查的字节范围未变。新文件的本地 Markdown 链接目标无缺失，`git diff --check` Passed。

本次差异输入 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `scripts/build-plugin.py` | `b6aedff0dc42171a167dd489754314f6cdc73f0449928725a98a6ba29d0cfc71` |
| `tests/test_pwf_distribution.py` | `0330d87c9129657feb5e41065a97ed5acf50c0f9915790acdc592fb774ad29c4` |
| `README.md` | `72deff0fe1a6cecdf94b5fd0206e2b9a25ed0843bcb1edea75224d820d8481d9` |
| `docs/development.md` | `472174c81fa0f5e97ae8400291f5749599868116e3bc96589ddf58f338fff9b6` |
| `tests/README.md` | `d1e5565af50fb86afc20eff10b8a94493011a1d32be8c73a25300b731d80059d` |
| `docs/upstream-maintenance.md` | `89a8c236f51812b555847937c6989978a62f54676a767523709c026f0707c93a` |
| `docs/design-references.md` | `16c30318ee88888f11746f99901d76e877ca1415cb92807cd5dff50350bc30b1` |
| `overlays/program-design/PATCHES.md` | `535543576a2121bcbdefabb057b4889efa0a54366df954e1bee5acaafb9e2eae` |

本次新增范围未发现实质问题。完整回归中报告的并发锁间歇失败正在由另一 Agent 对照原始基线调查，本 reviewer 未执行该场景，不据此认定或排除运行时回归；其最终判断和限制须进入 REP-0005。真实 smoke 同样由实际执行者保留观察和语义判定，不影响本节已完成的定向检查范围。

## 最后语义差异：任务采用与旧状态承接

主 Agent 在试用后调整 workflow 的两条 Discover 规则，本 reviewer 重新对照用户批准计划、PDB-05～07 和当前规则全文。对复杂且已授权的实施任务，应用 Skill 即为本任务采用 PWF，无需再增加项目 opt-in；包含调查/复现、修复、回归和持久交接的维护任务不会仅因代码改动小而绕过工作流。这与 0.2.0 取消旧项目启用前提、默认采用 PWF 底座的要求一致，未扩展为只读或简单任务自动建文件。

检查发现原拟文“新 PWF 计划存在即替换旧 live status/next-action”为指针，可能在只有空模板时丢失旧下一步与阻塞。主 Agent 已改为先让选中计划承接本任务的 goal/phase、next action、blockers 和 evidence links，再替换旧入口；仅转移本任务 live state，保留历史与批准需求。该问题已 Closed。项目或用户明确保持旧计划权威、禁止采用时仍优先，且不创建竞争记录；不构成全项目迁移、持续同步或本仓正式自身接管。

最终 workflow SHA-256 为 `c89e52f52df2cbab0f184924cdef90258cf3082156ff7856c8e0611615a3b79f`；builder 仍为 `b6aedff0dc42171a167dd489754314f6cdc73f0449928725a98a6ba29d0cfc71`。实际读取重建后的 14 个 ZIP，89 个 Skill 均包含这份最终 workflow；新 manifest 摘要为 `dc0a26944d6641441b3140a87948d54287f5468c5821db21b230da3060bae4ac`。此次只复查变更文本和其进入生成包的事实，不重复未受影响的 hook 运行测试。

该语义审查不证明模型一定遵循新规则。主 Agent 表示第三轮模型运行启动于“先承接旧状态”补充句之前的包；应分别保留当时输入摘要、实际状态承接结果和最终包的无模型安装验证，不能把模型读取的旧字节记录为最终包。并发锁的 uutils/GNU 对照结论也由实际执行者在 REP-0005 提供，本 reviewer 不认领未执行的工具链实验。
