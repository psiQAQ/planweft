# REV-0005-D：0.2.0 交付主张与实际证据审查

日期：2026-09-08。结论：本次受审实现及已归档证据中未发现新的交付阻断问题。此结论限定于下述输入和检查；不等于全平台真实运行通过，也不将失败样本改判为通过。

## 独立性与范围

本 reviewer 未编写本轮导入器、构建器、运行时补丁、SPEC-0003、ADR-0006 或测试控制器。独立比较 [SPEC-0003](../specs/0003-pwf-based-plugin.md)、[ADR-0006](../adr/0006-pwf-derived-runtime.md)、[REP-0005](../reproduction/0005-pwf-based-plugin.md) 与实际生成源、分发和证据，不只读取主 Agent 的结论。既有 [来源与分发 review](0005-pwf-migration-review.md) 作为历史发现及关闭记录，未冒认其中测试由本 reviewer 执行。

实际读取了 importer、builder、回归 runner、真实宿主 runner 的安装/缓存/信任/评估流程、workflow overlay、平台及维护说明；检查 14 个 ZIP 和两份原始证据归档。对第三轮维护与冷读，直接读取实际提示、JSONL 分析中的工具命令与完整工具输出、前后项目快照、终答和语义审查。没有运行、安装或修改研究子模块中的工具。

本轮只写本报告，不修改实现或历史实验输出。主 Agent 同时补最终 i18n policy 的归档与索引，故既有归档中的 `final` 文件名按该轮冻结点理解；实际交付摘要以下表为准。

## 冻结输入

| 文件 | 本轮核对的 SHA-256 |
| --- | --- |
| `scripts/build-plugin.py` | `cee21bab04e953cf8d6396ea529b8078d9c7427606e06db797bdb10eb71f0399` |
| `scripts/import-pwf.py` | `ce84b946883f51d187cc519ce5c33c7a07a1eae92dd92ad99313b14230e05322` |
| `overlays/program-design/workflow.md` | `c89e52f52df2cbab0f184924cdef90258cf3082156ff7856c8e0611615a3b79f` |
| `tests/test_pwf_distribution.py` | `94d4500b70b454463941bbf9351edbd812f96af081e784be64d77637da2e387d` |
| `dist/manifest.json` | `6c3d6787602b708d017374b3e11466cd70c0ad560c21f608928288f47396e92b` |
| `dist/program-design-0.2.0-codex.zip` | `4fa81f93c4b6dfdc839f0ad34731afdab0d9a37f6a27056a76c76f64f5c91044` |

## 实际检查结果

| 检查 | 实际结果与依据 | 证明边界 |
| --- | --- | --- |
| 固定来源与构建 | importer 固定允许提交和 tag；builder 核验 archive/inventory、拒绝不安全成员及缺项。实际运行 `python3 scripts/build-plugin.py --verify`：14 平台，Codex 与 artifacts 差异均为 0 | 证明当前输入与生成物一致；不证明宿主实际加载 |
| 分发摘要、计数、许可 | 直接读取 14 个 ZIP，逐包 SHA、成员数与 manifest 相等；无重复成员；根 LICENSE 与 vendor MIT 原文一致 | 本轮未重复既有 review 的全部 547 个相对链接检查 |
| 宿主原始归档 | 原有 `raw-evidence.tar.gz` 共 501 文件，归档 SHA 及全部成员 SHA/bytes 与 `raw-manifest.json` 一致 | 这是补充 i18n 预检之前的原始归档；摘要完整性不证明每个模型断言正确 |
| 回归原始归档 | `regression-evidence.tar.gz` 共 231 文件，归档 SHA 及全部成员 SHA/size 与 manifest 一致 | 保留含失败的历史轮次，未重跑全量回归 |
| 最终源码与已测源码 | 在内存生成当前完整 transformed tree，924 个文件与归档 `source-sha256-final.json` 逐个 SHA 完全一致，无新增、删除或不同文件 | 最新 Codex i18n policy 由 distribution 阶段附加，单独核查；源码相等支持复用已测运行时证据 |
| GNU 全量结果 | 直接核对原始/迁移 summary、日志末行和 JUnit：各 721 passed、63 skipped；subtests 分别 798、851。环境明确解析到 GNU `gnumkdir` 9.7 | 不将默认 uutils 环境描述为同样可靠；63 skipped 不计入 Passed |
| Node 结果 | 原始与迁移实际 runner 记录均有 Pi test、OpenCode typecheck/build/test 成功；后续 19 文件摘要一致清单随归档保留 | 本 reviewer 未亲自执行 Node 测试；Pi 未定义独立 typecheck/build，不能补写为 Passed |
| Codex 主入口 | 实际生成的主 Skill policy 为 `allow_implicit_invocation: true`；5 个 i18n policy 均为 false。独立执行 `test_codex_has_one_automatic_main_skill_and_its_own_hooks`，1 项 Passed | 这是原生配置和本地合同检查；`skills/list` 的 `enabled` 字段不能当成隐式调用策略的观测 |

用于对照的主要命令如下；归档摘要核对使用 Python 标准库 `tarfile`、`zipfile`、`hashlib`、`json`，逐成员比较清单且不解压到项目。

```bash
python3 scripts/build-plugin.py --verify

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_pwf_distribution.PackageContractTest.test_codex_has_one_automatic_main_skill_and_its_own_hooks -v
```

## 需求、实现与行为的对应

PDB-01～04 的 vendor/overlay/生成分发、独立身份、原生适配和来源保留有实际文件与回归依据。PDB-05～08 的选择器、磁盘状态、默认 advisory 和显式 controls 继承上游实现并经移植回归；本地 workflow 将只读、批准需求、旧状态承接和长期文档维护作为指令边界，没有加入独立文档写回或调度服务。Kiro、旧 root-file adapters、Pi 显式激活及 OpenCode idle follow-up 的差异在规格和平台矩阵中明示，不可从共同文件名推出相同运行语义。

第三轮维护的实际 prompt 和项目 AGENTS 不包含 `project-docs` 名称或启用语句；trace 中先从已安装 cache 读取主 Skill，再读取批准的无 BOM 约定、实现与旧计划。实际产物将 `utf-8-sig` 最小改为 `utf-8`，测试直接比较输出字节，指南同步；批准要求、用户 dirty 文件及原 dated observation 保留。选中的 `.planning/2026-09-08-utf-8-bom` 有唯一三文件计划，含目标、阶段、下一步、Windows 阻塞与证据入口；旧 `notes/work.md` 仅保留指针与历史。由此支持 PDB-06、07、10 在该维护样本中的有限通过结论。

独立新读者的实际输入只要求从 README/项目文件恢复目标、实际完成、下一步和限制。其工具读取了旧入口、新三文件、实现与测试，终答正确区分 Linux 已记录验证和 Windows 未执行；前后快照一致。样本没有在维护模型内部自动调度独立 reviewer：控制器禁用了多 Agent，再启动无插件/历史的新读者；这是外部控制器完成的冷读验证，不能宣称模型自己完成了全部独立审查要求。

## 必须保留的发现与限制

1. **默认工具环境的并发失败仍存在。** 归档的原始/迁移失败及 uutils/GNU 对照支持环境限制，生产锁没有改写。REP 已明确不在 uutils `mkdir` 0.8.0 上依赖可靠并发目录锁。GNU 全量 Passed 不是对默认系统工具的无条件背书。
2. **模型输出有实际失败和误差。** 前两轮没有采用 PWF 三文件；第二轮 evidence-gap 的通用引用判定 Failed。语义部分符合与自动判定失败可以同时成立。第一轮冷读行号/前态问题也应保留，不将“成功运行”当作所有引用正确。
3. **最新 ZIP 没有重新跑模型维护。** 本 reviewer 直接比较第三轮冻结 ZIP 与当前 ZIP：差异为 6 份 Skill 状态承接句、INSTALL 环境说明和 5 个新增 i18n `agents/openai.yaml`。原有运行时、plugin manifest、主 Skill policy 的字节没有变化；新增 policy 影响候选入口，应以原生配置、发现/缓存和定向检查说明，不能写成已直接观测模型绝不隐式选择 i18n。
4. **状态承接内容与写入时序不同。** 新计划已包含关键状态，新文件和旧指针在同一成功 file-change 中出现；CLI 不暴露 patch 内部逐文件时序。最终规则要求先承接再重定向，但严格写入顺序并未由该轨迹单独验证。
5. **真实宿主覆盖有明确边界。** 仅 Linux Codex 有真实模型生命周期证据；正常退出不证明可单独观察的 Stop 完成事件已送达。真实 gated 循环、Windows/macOS、其余宿主均 Not Run。静态检查和协议回归不能升级为这些环境已通过。

本报告未发现需要新增运行时修改的阻断项。交付说明应继续使用分层结果，并将原有冻结包与最终新增 policy 的摘要、预检和限制分别列明；历史证据无需覆盖成最新版本。少量模型样本不支持自动匹配率、普遍正确性或优于 PWF 的效果结论。
