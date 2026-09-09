# RC7 后最终发布门槛独立审查

审查范围：当前源码中的门槛、安装器测试和执行入口；只读检查，未运行容器、模型或全量测试。RC7 发布和三系统结果来自主 Agent 状态，本审查不重新证明它们。**现有入口尚不能直接产出满足全部 stable 门槛的证据集合；这主要是场景缺口，不是已证明的插件功能缺陷。** 当前未见 `release/acceptance.json`。所有最终结论须绑定尚待冻结的唯一 `0.4.0` 归档，RC 和重打包 fixture 分栏保留。

| 要求 | 已有入口及覆盖 | stable 仍需补齐的最小工作 |
| --- | --- | --- |
| 新增、修改、删除文件的升级与回退 | `tests/run-installer-lifecycle.py` 实际 npm 打包 A/B，校验三类文件、原生内容及项目记录不变；两包都加了 fixture 文件。`tests/installer.test.mjs` 也有离线覆盖。 | 从冻结 stable 派生并重跑五宿主 fixture，分别记录原始输入与 A/B 摘要，明确它们不是准确 stable。准确 stable 自身仍跑安装/卸载/重装，以及与真实 RC 的升降级。执行 fixture 前补归档预检；当前在读取归档前建输出，并使用 `extractall(filter='data')`，应检查锁定镜像 Python 是否支持，或复用 registry 入口的安全兼容解包。 |
| 共享 HOME、不同版本项目隔离 | `tests/run-project-isolation.py` 使用准确双归档，Claude/Pi/OpenCode 可执行 A 更新/删除而 B 字节与原生注册不变。Codex/DSH 明确验证不支持的项目级完整安装被拒绝。 | 用 stable+RC 重跑。这个入口设置 `PLANNING_DISABLED=1`，不能证明运行时计划或缓存隔离；Codex/DSH 的拒绝也不能代替全局插件访问两个项目的隔离。另补同 HOME、两个不同项目标记的实际上下文/恢复检查；按平台区分安装范围与运行项目。 |
| 用户修改保护、部分失败恢复 | `tests/installer.test.mjs` 有修改副本、外来目标、市场注册后失败、Pi 更新失败、Skill 复制/删除失败与重试；导入工作区 installer，宿主调用是 mock。实际生命周期脚本验证项目三文件与需求未改。 | 当前无准确包上的专门原生失败/副本冲突场景。可增加无模型场景：安装准确包后改一处自有副本，确认 update/remove 拒绝且字节不变；再用受控命令 shim 仅在指定市场/插件/配对步骤失败，其余命令转发真实 CLI，核对部分记录、原生状态及恢复/撤销。mock 保留为回归，不能标为真实宿主故障恢复。 |
| 重复 hooks 检测 | `lib/installer.mjs:161` 检查已知安装路径和五宿主注册面；DSH 额外检查 overlay；离线 installer 测试与 doctor 测试存在。 | `run-five-agent-release.py` 没有 duplicate 场景。增加准确包无模型测试，在隔离原生配置放入另一规划插件注册，确认拒绝/诊断并保护外来配置；再验证正常唯一注册。只证明可检测范围，不宣称识别所有自定义 hooks。 |
| 提醒去重 | `tests/test_pwf_distribution.py:535` 验证共享 Shell 同 turn 首次有输出、再次无输出、下一 turn 恢复；DSH facade/probe 也有协议测试。 | 尚无五宿主实际场景入口。给各原生会话安排同 turn 多次可观察工具事件，再开启下一 turn/会话，按该宿主原生事件/扩展输出确认去重与重置。单次 context 或唯一 Skill 加载不等于去重；协议测试与模型会话分开记录。 |
| 持久信任和原生拒绝 | 当前准确归档入口已支持 Codex `persisted-trust`（真实 TUI、信任前/后/新会话）；Codex/Claude/OpenCode/DSH `permission-denial`；Pi `package-approval`。 | 不需要重造入口；对最终 stable 实跑并审查原始事件及保护文件。其他停止场景中的 invocation trust bypass 不能填持久信任。Pi 原生 package approval 是其实际机制，不宣称具有工具级 deny 沙箱。 |
| 真实远端升级和新会话 | `run-registry-smoke.py --previous-version ... --previous-sha256 ...` 已实现准确远端 RC→新版本→RC→新版本→卸载，校验实际内容、缓存清除、原生卸载与项目记录。 | 最終 stable 到 next 后执行；此入口明确模型 Not Run，需保留其实际安装目录/来源并加新会话，不能另装本地包的会话冒充远端安装会话。实际两个版本没有新增/删除时，不把 fixture 覆盖改记为远端文件差异。 |
| 原生渠道 | `run-public-git-marketplace.py` 有 Codex/Claude 公开 Git 安装、同提交刷新及卸载；registry 入口有 Pi/DSH npm 单版本安装/加载/删除及 OpenCode npm 加载+Skill 配对。 | Git 入口明确 `cross_version_update: Not Run`，应照实保留。门槛单列 `native_update`：若用直接 npm/Git 渠道声明它，则需增加该渠道的真实版本切换与加载；不能用同提交刷新替代跨版本升级。OpenCode 当前末步只移除配对 Skill，`opencode.json` 的 npm plugin 条目还在；补移除插件配置并新进程检查工具消失，方可证明直接 npm 插件卸载。 |

## 门槛实现的证据边界

`scripts/check-release-gate.py` schema 2 已强制五宿主、逐场景 Passed 与存在且摘要匹配的附件，检查当前归档、冷读输入/独立会话以及 reviewer 对当前附件集合的绑定。其测试覆盖缺场景、Not Run、无附件等拒绝路径。**这些是结构与完整性检查，不是原始附件的语义证明。** 当前每个场景只有 Passed+附件要求：旧 RC raw 或 mock raw 仍可能被新的外层 stable attestation 包装；`permissions` 也不在强制 actual-host-model provenance 的检查组中。

最小补强是让各场景明确写 evidence kind、实际被测包摘要、宿主/执行器版本；fixture 单列父归档与实际 A/B 摘要，模型场景明确模型、session、隔离。收集时逐项核对原始产物元数据，独立 reviewer 绑定最终集合，不必为此引入通用证据框架。`collect-release-evidence.py` 是脱敏收集工具，不会自动判断上述场景完成。

三系统 Check workflow 已存在，但 publish workflow 本身只运行 Linux 检查；最终放行须核对**最终代码提交**的三个系统 Check 全绿，不能用 RC7 历史结果替代。发布前的本地门槛与 `--promotion` 远端门槛分开执行；后者通过后才提升 latest。若只改包外验收器，不应为获得新证据而修改待测包；一旦插件包字节改变则重新冻结并绑定所有受影响证据。

结论：优先补准确包的安全/故障场景、五宿主去重/重复注册、远端来源会话接续和 OpenCode 原生卸载断言；随后用现有入口完成最终 stable 执行。未运行场景保持 Not Run，本审查不授予 stable 发布通过。
