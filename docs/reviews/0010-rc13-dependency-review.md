# RC13 直接依赖闭合独立审查

当前结论：用户批准范围内的 `toml: "4.3.0"` 直接依赖与 root lock 已闭合；其余依赖没有升级。独立测试无需 NODE_PATH，打包预览包含所需 CLI 与实现。**发布 workflow 的依赖安装遗漏已在下方补充复核关闭**；准确新包的真实宿主验收尚未执行。

## 已核查事实

- 根 `package.json.dependencies` 和 `package-lock.json.packages[""].dependencies` 同为精确 `toml: "4.3.0"`。
- 对照 HEAD，lock 中 **69 个非根 package entries 全部逐项相同**，其他 lock 顶层字段也相同，没有升级其他包。
- 本地解析实际位于仓库 `node_modules/toml/index.js`，包版本为 4.3.0；index/compiler/parser 三份源码摘要与前次核对过 registry integrity 的准确 tarball 相同。
- 清除 NODE_PATH 后运行 `node --test-name-pattern='Codex' tests/installer.test.mjs`：**42 Passed**。不再借助个人或临时宿主缓存作为解析器解析来源。
- `npm pack --dry-run --ignore-scripts --json` 显示 `lib/installer.mjs`、`bin/planweft.mjs`、`package.json` 均在包内，共 4060 项文件。node_modules 不随包捆绑；发布 manifest 的直接 dependencies 由 npm 正常安装。这是打包预览，不是冻结归档或远端安装证明。
- `lib/installer.mjs`、`five_agent_runtime.py`、`run-five-agent-release.py` 摘要与上一份已关闭审查对应版本完全一致，没有新增未审实现变化。

## 工作流发现

`.github/workflows/check.yml` 的三系统 installer job 已在 Node 设置后、测试前运行固定 lock 的 `npm ci --ignore-scripts --omit=dev --no-audit --no-fund --registry=https://registry.npmjs.org`。

本次复核时 `.github/workflows/publish.yml` 仍只有 global npm CLI 版本安装，之后直接执行 installer tests，没有安装项目依赖。global npm 不是本项目的 toml 依赖来源。干净发布 runner 会缺失 parser，不能以本机已有 node_modules 的通过结果替代。需在发布测试前增加与检查 job 对应的 npm ci；本发现已通知主 Agent，保持待关闭，不修改 workflow。

## 边界与资源

本次没有安装依赖、运行容器或模型；读取主 Agent 已安装的依赖，并执行已有离线测试和本地 pack dry-run。dry-run 专属 npm cache 已精确清理，测试和预览日志保留。用户依赖授权不等于当前准确候选或 stable 已通过验收；仍需正常分发入口、干净依赖安装、准确新归档及远端生命周期证据。

| 对象 | SHA-256 |
| --- | --- |
| `package.json` | `ce3f96e86a502559c6f63bfcc8db9659221ca31bca6fc8f1c7268c3512e453e3` |
| `package-lock.json` | `edb3b725b413d6fd5d1e41d66a98bf902c2d2622f0896076726cf82285a0ccde` |
| `check.yml` | `0cdab4ac8bd66dfe49e3030b079ac87157b3ae6f1e1114cb84f107faf9df8e25` |
| `publish.yml`（补齐前） | `5d6cf57a65e43aeb93cbabc0d8b032393fbc31fcb669f2ca837c26e135fd5c0d` |
| `lib/installer.mjs` | `36df1782fc41e445800c6e629eec764d4b5f19429e0e8f4b26874bf6d2802f21` |
| `tests/five_agent_runtime.py` | `ac5463b3914011a69919b3c871011476e15a96bfc7fdbb4741d070cb503615da` |
| `tests/run-five-agent-release.py` | `253a067d33fe46ac4cdcd957ecb5653e75a5ba7de3fd51bd5581b96a69dd2922` |
| `toml/index.js` | `a852aecec75bb4bebabe9c0c7e72fb9c76bba5fc243779f8f55cfe941447be1a` |
| `toml/lib/compiler.js` | `57bc506a200d23601dede27466de58382b16f0efe611e92419dcc168a6df481d` |
| `toml/lib/parser.js` | `d17b974a0c453d8fab1ec1d7966f211b0004bd89a9456615c61bfc488db8b759` |
| `planweft-rc13-dependency-independent-tests.log` | `c70f7c3de8ee0787de954a89279dd9a05deea836ef282614442c8f660b2f543c` |
| `planweft-rc13-pack-dry-run.json` | `98321b4ceb806bce0578275972708a2af2c48249dc12c0418602bc49130739d1` |

## 补充复核：发布工作流已闭合

主 Agent 已在 `publish.yml` 的 installer 测试前添加与检查 job 相同的固定 lock `npm ci --ignore-scripts --omit=dev --no-audit --no-fund --registry=https://registry.npmjs.org`。独立复核确认位置正确，发布 runner 不再依赖预先存在的 node_modules；此发现关闭。关闭后 `publish.yml` SHA-256：`186cd0acae061d5e953ab58d03b8fa9c80fd8a98edff57262085019ec975258d`。前述补齐前摘要与原始发现保留。

再次对照 HEAD，69 个非根 lock 条目仍完全一致。当前根 manifest 为 `0.4.0-rc.13`，其 package/lock 摘要仍与前表一致。未因解决直接依赖而升级其他包。

本机 Node v22.22.1 对既有 `ini@7.0.0` 的 engine 范围 `^22.22.2 || ^24.15.0 || >=26.0.0` 不满足；这是原锁定传递依赖的环境限制，不是本次 toml 版本升级。安装与开发测试成功不能证明整个依赖集合支持此本机 Node 版本。主 Agent 计划使用 Node24.19 镜像及 CI24.20 再验，二者满足该范围；本报告不将计划当作实际 CI/容器 Passed。主 Agent 报告本机完整回归123 Passed / 1 Windows Skipped，独立复验范围仍为前述42项。

当前依赖声明、锁定关系、发布文件和 CI 安装入口在源码范围内闭合，没有新增阻塞。准确新归档冻结、正常分发安装与真实宿主验收仍待取得证据；本次打包预览不是正式发布验收。
