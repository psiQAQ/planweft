# RC11 Pi 相对来源识别独立审查

本次对 `lib/installer.mjs` 的未提交修复进行独立源码复核，补充 `tests/installer.test.mjs` 的离线反例。结论：在本次检查的来源解析与重复注册边界内，没有剩余阻塞发现。没有修改安装器实现，没有运行容器、Pi、模型或联网安装。

## 原始失败与修复依据

准确 RC10 的 Pi maintenance 原始 `installer-doctor.stdout` 先报告已安装，随后将项目 `.pi/settings.json` 中的自有来源误判为另一项规划注册。实际保存的来源为 `../.planweft/versions/0.4.0-rc.10/node_modules/planweft/dist/pi/planweft`：以配置文件所在目录 `.pi/` 解析，才回到项目的持久安装目录。旧逻辑只删去记录中的绝对来源字符串，因此未能识别 Pi 原生保存的相对写法。此次依据是保留的真实宿主配置及失败日志，不是从模拟安装推断宿主行为。

修复先解析同 scope 的 Pi JSON，仅在 `packages` 中移除一个与 receipt 的 `nativeSource` 精确对应的字符串或对象 `source`，用于后续重复检测。相对路径以配置目录解析，`~/` 以指定 HOME 解析；绝对路径使用运行平台的 Node `path`。这是内存中的检测视图，未改写用户配置。

对象来源只移除 `source`，其余字段保留；等价的第二项来源、其他 scope 的来源及 metadata 中另一项规划标识仍进入原检测。没有恢复旧的全局字符串删去逻辑，也没有把所有含 `planweft` 的条目视为自有。

## 检查与反例

| 检查 | 结果 |
| --- | --- |
| 真实项目相对来源通过 doctor 和 update dry-run；receipt 不变 | Passed：原回归复验 |
| 单个对象来源，保留 Skill/Extension 筛选字段与无关配置；CRLF 和中文、空格目录 | Passed：新增离线测试 |
| 字符串与对象混合的绝对/相对等价重复、两个对象重复 | Passed：doctor 拒绝，update dry-run 拒绝 |
| 自有对象其余字段含另一项旧规划 Extension | Passed：仍拒绝，不吞掉 metadata |
| 错用项目 cwd 而非配置目录可解析成自有的路径 | Passed：拒绝错误来源 |
| 另一 scope 的对象来源恰好指向本安装 | Passed：不豁免 |
| 自有全局 `~/` 对象来源 | Passed：指定 HOME 下正确识别 |
| 上述诊断及 dry-run 对配置字节、receipt、原生命令调用数的保护 | Passed：没有写入或调用安装命令 |
| Windows 原生 `..\\` 分隔符、绝对盘符及 JSON 转义；第二项绝对来源仍拒绝 | Not Run：本机 Linux，专属测试已加入并 skip；须由 Windows CI 实际执行 |

Windows 使用原生 `path.isAbsolute/resolve/relative`，没有用 POSIX 字符串规则取代路径解析。此次不宣称覆盖 Windows 大小写别名、UNC、junction 或任意别名自动发现；不等价的写法没有新增放行豁免。对象字段中出现规划标识仍可能触发保守拒绝，本次没有扩展重复检测为通用 Pi 配置语义解释器。

## 验证与证据绑定

```bash
node tests/installer.test.mjs
```

原修复前日志：68 tests，67 Passed / 1 Failed。主 Agent 修复后日志：68 Passed。独立补测后：**77 tests，76 Passed / 1 Skipped**，新增 9 个测试计数包含分支子测试。仓库既有检查及发布 workflow 均直接运行上述 Node 入口；本机 `node --test` 只输出文件级摘要，未用其单项 Passed 代替逐项测试结果。

审查基线提交 `e79e08548c31ed8833da032f68766b36078779f4`，实际对象为该提交后的修改，以下摘要固定本次内容。公开记录只列附件名称及内容摘要，原始输出目录由本地证据清单管理。

| 文件或附件 | SHA-256 |
| --- | --- |
| `lib/installer.mjs` | `b84d93eac1ffafa5f56daed722e0e609f128b26c642c9e128455e5cceea4f13f` |
| `tests/installer.test.mjs` | `79ef9db33c95b22f1d249cbc7321d8715ad4f797adc080276ad0a21f4c48c2d8` |
| RC10 `installer-doctor.stdout` | `52b9d746a96d6ebab61ff3e387579dc761a88909cc9ba27f3fb3ec8f4f3a7805` |
| RC10 项目 `.pi/settings.json` | `27267cfae36c1aa4a26bde557652eb2b53578dd8171e127e8e2ae88ab6c0fed7` |
| `planweft-rc11-relative-before.log` | `5dbc0be7a909276ca8217ece1f962e39cf7401f07988a45780ad405794f6f344` |
| `planweft-rc11-relative-after.log` | `af0fbdf3cbcf343747b9fcf8a1001bd2ab520b105fea752b12f761d03f4c29f4` |
| `planweft-rc11-relative-independent.log` | `b09661a5a44e618983a83bc51874dd9683fa34b23c6dbcacbce62978b7813828` |

原始 RC10 Failed 没有被改写。本次只关闭安装器误报的代码与离线回归缺口；原生 install/update/remove 的模拟调用不能证明真实 Pi 生命周期或模型加载。修复后的准确候选包及最终 stable 包仍需分别取得真实宿主和发布门槛证据，Windows/macOS 实际执行结果也须单独绑定。
