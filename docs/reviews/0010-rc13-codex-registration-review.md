# RC13 Codex doctor 实施独立审查

当前结论：Codex 结构化所有权检查及此次发现的两个 receipt 反例已关闭；独立 Codex 定向 42 tests Passed，projection 定向 1 test Passed。**混合模型/无模型场景的认证传递阻塞也已在下方补充复核中关闭**，原始发现和对应旧摘要仍保留。依赖声明仍待确认，NODE_PATH 开发验证不构成可发布依赖契约。

## 真实根因证据

新场景 `rc12-codex-registration-diagnostic` 安装未经修改 RC12 包后，实际采集到：唯一 CLI marketplace 的 `source_type=local`，`source` 为派生持久 registry，精确 `planweft@<catalog>` 插件 `enabled=true`。原生 `codex plugin marketplace list --json` 返回相同来源。随后准确旧包的 doctor 仍 Failed。

这补齐此前“尚未取得实际配置”的诊断限制，但该新 projection 不是原 `rc12-native-five` 容器的原件。完整配置仅绑定 SHA `91eb7b0708282521e5de9e78b192bacd9899bc24e4aae1aa5c2203982e3b3c7d`；输出只含 marketplace source/type 和 plugin enabled，未保留模型供应商配置。旧准确包 SHA 为 `7830a636cf5c36bca51883704abf8feeaf5c5a15f9583b9f8966db48da289dc3`。

## 所有权与解析复核

- Codex 分支不再全局剥离品牌、nativeId 或目录字符串。递归扫描解码 key/string，仅在准确结构路径跳过已核验的 marketplace/plugin 键身份和单个 source 值，自有 plugin 的 value 及 marketplace 其他字段保留。
- 来源需为绝对路径、local 类型及派生 registry；旧 catalog/nativeId 精确绑定，registry/payload 摘要及存在性核查，异常链接拒绝。其他普通名称 marketplace 即使使用自定义无品牌 storage 的相同来源也拒绝。
- 入口使用 fatal UTF-8 解码，TOML 错误统一诊断，不输出可能带供应商值的原始 parser 报错。重复 key、转义规划名及非法 UTF-8 有反例；合法 U+FFFD、不安全 Number、非有限数、时间类型不会跳过同一对象中的字符串检测。配置不写回，因此不以 parser 的 Number 近似改写用户数字。
- 完整安装需自有 plugin table 且 enabled=true；缺失/禁用会失败而不恢复用户设置。固定 schema 的默认 enabled 语义与此更严格的“原生安装记录完整性”检查应保持区分；此处审查的是准确原生 add 写出的显式 enabled 配置。
- 合法部分失败：marketplace-add done、native-install failed、overall failed，已校验来源可供 update dry-run 重试；doctor 仍因非 installed 失败。不将已注册市场等同于完整安装。

## 独立发现与关闭

| 发现 | 原始复现 | 当前结果 |
| --- | --- | --- |
| 完整 receipt 但 marketplace 步骤缺失、config 缺失 | 现有 fixture 建 installed 状态后删除 marketplace-add，doctor=0 | Closed：在检查 config 存在前，installed 强制 marketplace-add/native-install 均 done；永久反例覆盖缺步骤/failed/整个 steps 缺失 |
| 顶层 global 状态中 agent receipt.scope=project | 完整自有配置保持，doctor=0 | Closed：full receipt 强制当前 scope 和 receipt scope 都 global；永久反例与定向复验通过 |

这些复现仅调用 fixture 中模拟 native/npm 的 run，没有真实安装。没有修改被审查实现。

## 原始发现：混合场景认证传递（已在补充复核关闭）

当前 `run-five-agent-release.py` 的 credentials 按整个 `args.cases` 判断：只要任何场景需要模型，就读取认证并在每个场景 payload 原样传入。新增 runtime 在 Codex preflight/lifecycle 的安装和 `prepare_model` 之后才拒绝非空 secret。因此合法 `--cases preflight maintenance` 会在无模型 preflight 中先写 auth，再报 `Registration diagnostic must not receive credentials`。纯无模型组不受影响。

最小修复：runner 构造 payload 时对所有 NO_MODEL_CASES 使用 secret=None；runtime 在提取/准备认证之前拒绝无模型 case 的非空认证，作为防御检查。保留对模型场景的正常认证，不通过放宽诊断 guard 修复。补纯离线的混合 case payload 与 runtime 早期拒绝反例，验证 prepare_model/native install 尚未调用。此条为静态确定的数据流冲突，不声称已执行容器或读取实际认证。

## 持久 CLI 与依赖启动边界

runtime 的 install 闭包重新绑定 `cli` 后，后续 doctor/update/remove 指向 `verify_files` 返回的完整 npm packageRoot，而非插件 native_root。该返回点先比较输入归档内每个文件的字节，再比较平台 manifest 和执行位；因此没有改写待验 tarball，也没有将不同版本脚本替换入准确包。

首次从无 node_modules 的解包 CLI 执行 add，仅在全新隔离 Codex config 不存在时能够跳过 TOML 读取并引导持久 npm 安装。这是当前 clean-HOME 场景的前提，不代表任意用户已有 config 时都可直接运行解包目录。正常公开 npm/npx 入口必须通过明确的直接依赖提供 parser；当前 package.json/lock 尚未变更，不能宣称已完成。后续切换到持久 CLI 的执行改动尚未由本次真实 RC12 diagnostic 证明：该冻结场景的 doctor argv 仍指向解包目录。

开发 NODE_PATH 仅显式引用既有准确安装中的锁定 toml4.3.0，没有新安装。本次不把此环境视为分发依赖已自包含，也不接受个人缓存兜底作为发布依据。真正从干净 npm 安装获得声明依赖并运行准确候选的场景仍待执行。

## 本次验证

- 独立 Node 定向：42 Passed（8 个父测试及分支子项）。
- 独立 Python projection：1 Passed，核对输出字段允许列表、原配置字节不变和重复 TOML 拒绝。
- 主 Agent 开发全量日志：124 tests，123 Passed / 1 Windows Skipped。
- 实际容器、模型、安装依赖：本次 Not Run。

命令使用直接 Node 入口及明确的开发 NODE_PATH；此环境说明是可复核限制，不是依赖声明替代物。

## 内容绑定

| 对象 | SHA-256 |
| --- | --- |
| `lib/installer.mjs`（关闭两项 receipt 问题后） | `36df1782fc41e445800c6e629eec764d4b5f19429e0e8f4b26874bf6d2802f21` |
| `tests/installer.test.mjs` | `53475cc30ab840e16ecaeb8488dba00cf219f9dc09dbd292b3d1b786f8437e41` |
| `tests/five_agent_runtime.py`（混合认证问题尚未修） | `b0a7473661292d403a8cc12cd7e82d12c9e52a69f0a80a86c0354433c78793d0` |
| `tests/test_container_release.py` | `805b59af0d97c7a74bbb8e0d4eef17dac6de5160c6bf6e9fb42409008c194ebd` |
| `tests/run-five-agent-release.py` | `1c32bab865e205a3150c8aedf82e5e1edb686bd100711edb00335b569c2d234c` |
| `planweft-rc13-codex-independent-tests.log` | `a2b2713c2e0347fde8d0f138f7f401fb40f364b2e4284dcabe5832ead7af14fa` |
| `planweft-rc13-projection-independent-tests.log` | `6d1674f487ffe84d81216993ffaab91e974908005485d90bf68a159aeac70fdd` |
| `planweft-rc13-installer-development-reviewed.log` | `29ddddaf3fc963f7766c2905753f17d2d566418ba29f06a09882931ef73cdaba` |
| 新 diagnostic `native-registration.json` | `03cb21e92bbdc0c53ab5cc5ce0d9b0af9692ba4d985a288992311beb23e04968` |
| 新 diagnostic `native-marketplace-list.stdout` | `fa414241669e4b865b58bc888d766789b53a62313628748b490e2548ee64dd09` |
| 新 diagnostic `installer-doctor.json` | `e142fc74c5361abce3e477cbb459ead5bf8622ea175b8dd64ba68a7c614de6d8` |

依据包括固定 [Codex config schema](https://github.com/openai/codex/blob/ff29a44391deccde0aba0f8390337d7f3c319ea4/codex-rs/core/config.schema.json)、锁定 toml4.3.0 源码及新原生 projection。原始 Failed 全部保留；当前实现结果和准确旧包失败是不同对象。

## 补充复核：混合场景认证隔离已关闭

当前 runner 统一通过 `scenario_payload` 构造实际提交给容器的 payload；`preflight`、`lifecycle`、`package-approval` 均明确设 `secret=None`，维护等模型场景仍使用原认证对象。原对象不被修改，因此同一 runner 后续模型场景仍可正常取得认证。纯无模型运行的 credentials 既有早期返回保持不变；混合运行只为模型场景读取认证，不向无模型容器传递。

runtime 在 `controller` 入口先拒绝无模型 case 的非空 secret，位置早于 `secret_values`、`setup_environment`、版本命令、包解压、`prepare_model` 和原生安装。绕过 runner 直接调用 controller 也不会先创建 HOME 或准备认证。空/None 没有实际凭据，因此通过此检查是预期行为。此前安装后的二次诊断防御检查不再成为首次拒绝点。

新增永久反例覆盖三个无模型 case 的实际 helper 输出，确认不包含合成 secret；强行给 controller 填回 secret 则抛 ValueError，并用 mock 断言 `setup_environment` 和 `prepare_model` 未调用。模型 maintenance 的 payload 与原 secret 保持一致。独立 reviewer 直接重跑该测试：**1 Passed**。主 Agent 容器入口离线组日志：**21 Passed**；均不涉及 Docker、模型或实际认证。

| 关闭后的文件/附件 | SHA-256 |
| --- | --- |
| `tests/run-five-agent-release.py` | `253a067d33fe46ac4cdcd957ecb5653e75a5ba7de3fd51bd5581b96a69dd2922` |
| `tests/five_agent_runtime.py` | `ac5463b3914011a69919b3c871011476e15a96bfc7fdbb4741d070cb503615da` |
| `tests/test_container_release.py` | `1a017c1c85c893f0ac147b098460aaa30c2e41528207e90528dbcb2e789d0993` |
| `planweft-rc13-runtime-diagnostic-tests.log` | `2b8cfa9751f5909954e87227c7d9c6cd47df0e0960e7234dccf17db0820be6e1` |
| `planweft-rc13-mixed-auth-independent.log` | `8a3bde37ba4c8968069949f493e7905380bc1b0249c21295a8f4b9e00cc3bc00` |

此前旧源码摘要及诊断保留供追溯。当前本次代码审查没有剩余实现阻塞；**明确依赖声明、干净 npm 安装、修改后准确归档的真实验收仍未完成**。新增离线 Passed 不替代这些发布条件。
