# RC12 Pi BOM 兼容修复独立审查

结论：此前 Pi 自有来源结构化解析引入的 UTF-8 BOM 兼容回归已在本次源码及离线测试范围内关闭。修复仅在 Pi 专用解析前移除一个开头 U+FEFF，与固定 Pi v0.84.3 原生行为一致；没有放宽重复注册或 foreign scope 检查。**真实 Pi 宿主的 BOM 场景尚未运行**，本报告不替代准确候选包或 stable 归档的验收。

## 来源与原始复现

固定官方源码中，`loadFromStorage` 及 `persistScopedSettings` 读取现有配置时均在 `JSON.parse` 前调用 `stripBom`。[读取实现](https://github.com/earendil-works/pi/blob/v0.84.3/packages/coding-agent/src/core/settings-manager.ts#L364-L379)、[持久化实现](https://github.com/earendil-works/pi/blob/v0.84.3/packages/coding-agent/src/core/settings-manager.ts#L574-L600)。`stripBom` 委托 `splitBom`，只在字符串以 U+FEFF 开头时移除一个字符，其余内容不变。[文本工具实现](https://github.com/earendil-works/pi/blob/v0.84.3/packages/coding-agent/src/utils/text.ts)。此次核查读取的是该固定版本源码，不将当前默认分支文档当作固定宿主能力。

安装器原先新增的 Pi `JSON.parse(text)` 不接受上述输入。独立复现用例在模拟原生安装后，向对应配置写入实际 UTF-8 BOM、CRLF 和 receipt 对应的相对来源，分别检查：

| 用例 | 修复前 | 修复后 |
| --- | --- | --- |
| 自有字符串来源，doctor | Failed：返回 1，而非 0 | Passed |
| 自有对象来源，update dry-run | Failed：在 Pi 专用解析处抛 SyntaxError | Passed |
| 相对来源与绝对来源重复 | Failed：抛 SyntaxError，未到要求的重复注册拒绝 | Passed：明确重复注册拒绝 |
| foreign scope 来源 | Passed：仍拒绝 | Passed：仍拒绝 |

测试的 finally 断言同时核对配置的 BOM/CRLF 原始字节、receipt 和原生命令调用数不变。重复负例要求 `Another planning registration`，没有将任意异常当作通过。原始失败日志保留；其 5 个测试计数包含父测试，结果为 1 Passed / 4 Failed。

## 修复复核与边界

实现只将 Pi 专用解析改为 `JSON.parse(text.replace(/^\uFEFF/, ''))`，正则没有 `g` 或 `m` 标志：只匹配整个字符串开头的一个 U+FEFF。空字符串、普通 JSON、单/双 BOM、空格后 BOM、JSON 值中的 BOM 和 CRLF 共 7 种边界输入，与官方 `startsWith`/`slice(1)` 写法逐项比较相等。双 BOM 仅去掉第一个，不通过任意 trim 或全局替换接受额外输入。

同 scope、已有 `nativeSource` 的入口条件、最多豁免一项来源、对象其余字段保留以及 foreign scope 的原检测都没有变更。配置只形成内存检测视图，没有落盘重写。此处全局 `json(file)` helper 不读取 Pi settings，其调用方是包元数据、安装状态、receipt、marketplace 和 DSH manifest；本次没有扩大这些独立解析器的范围。

## 验证与摘要

```bash
node --test-name-pattern='Pi UTF-8 BOM' tests/installer.test.mjs
node tests/installer.test.mjs
```

- 独立定向复验：5 Passed，包含父测试与上述 4 个子用例。
- 主 Agent 全量日志已核查：82 tests，81 Passed / 1 Skipped；跳过项为 Windows 专属路径测试，本机 Linux。
- 7 种字符串边界的同义比较：Passed。
- Docker、真实 Pi、模型及 Windows/macOS 真实执行：本次 Not Run。

审查基线提交 `438e4a9cb7b3c33cf4abe3472bc232c67b0f1d62`，包含其后的未提交修复。以下摘要绑定实际源码和保留日志；附件只列名称，避免公开本机私有路径。

| 文件或附件 | SHA-256 |
| --- | --- |
| `lib/installer.mjs` | `fbfb7cd0292250a2fd753a1acfc7458fff30b0d70d8e45a4548b58b971d8d375` |
| `tests/installer.test.mjs` | `c0118a404f4a17ca118d1bcd298cff725c65b7e86970ff5f7421afc2eec7b934` |
| `planweft-rc11-pi-bom-before.log` | `e98e04ea78551f956ecbee199781e669e5bfb005734d70fe2210b995e148a8a3` |
| `planweft-rc12-pi-bom-after.log` | `4d1d88db514c0d7f6508747d689bc25a8450da3cdc10b265a0913bc07d4b2370` |
| `planweft-rc12-installer.log` | `167bcfedda711b12b9251f78148cf7b31960bce0f683a1809f1506f92306d20e` |
| `planweft-rc12-pi-bom-independent.log` | `5640caf1130d2e8137ce183575f428f46ba2a650c7a08ad8b10462691dcb3b8f` |

此前 RC11 相对来源审查没有覆盖 BOM，本记录保留这一新增发现并补齐回归；不改写此前真实 RC10 维护失败。修复关闭指代码兼容性与离线证据，原生安装、更新及模型验收仍须绑定各自准确产物。
