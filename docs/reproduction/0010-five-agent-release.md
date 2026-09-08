# REP-0010：五 Agent 容器验收与公开发布

状态：实施与验证进行中，尚未发布稳定版；本文件区分已观察结果和待完成项。

## 公开 RC1 与后续修复

准确发布归档版本 `0.4.0-rc.1`，SHA-256 `d72ef1e786f8aa0c63041026e716ac19f527d083f51e0b4d80624fba97c1dfdf`，来自干净提交 `1300f471a2c7f6382621293e4f901d14c062b714`。真实 npm 下载逐字一致。`next` 已发布；首次发布还自动产生 `latest`，两次不同 npm 版本的删除操作在额外认证完成后均返回 HTTP 400，尚未更正。这不是稳定版验收通过。

GitHub trusted publisher 已配置：仓库 `psiQAQ/planweft`、工作流 `publish.yml`、环境 `release`，环境分支规则仅 `master`。管理使用 npm 11.19.1 及当前 API 必需的 publish 权限；发布构建仍固定 Node 24/npm 11.11.0。OIDC 实际候选发布待验证。

| RC1 场景 | 观察与边界 |
| --- | --- |
| 五平台准确包预检/幂等生命周期 | Passed；保留基线容器 ID，无缺失。DSH 当时只验证 composed 配置，不能代替实际启动 |
| Pi 模型 | context Failed：原生注入含随机码但模型回答 NO_CONTEXT；recovery、cold-reader、readonly、skill-loading Passed。maintenance 原断言把标题格式当作历史丢失，独立审查及[显式重判](evidence/0010/pi-maintenance-reassessment.json)确认事实原字节保留；不是模型重跑 |
| Claude 模型 | context、recovery、maintenance、cold-reader、readonly、skill-loading Passed；独立维护/冷读审查通过。冷读自称“未执行命令”不准确，实际执行只读命令，未修改项目或重跑测试 |
| OpenCode 模型 | context、recovery、cold-reader、readonly、skill-loading Passed；maintenance Failed：修复代码与测试，但没有初始化唯一 PWF 计划 |
| DSH 模型 | 六项 Failed，实际启动暴露缺少日志目录及 bare import 解析失败；没有模型事件，不算完成模型调用 |
| 真实 npm 幂等安装 | Codex、Claude、Pi Passed；OpenCode Failed：同版本 npm 插件阻止独立 Skill 配对。DSH 仅配置检查成功，真实启动失败已更正，不能算运行时通过 |
| 本地 A/B fixtures | Passed：实际新增、修改、删除及更新/回退/卸载，项目文档保留；fixture 重打包不冒充准确发布归档 |

以上准确 RC1 运行、失败及工具版本另存[公开 RC1 附件](evidence/0010/rc1-published-trials.tar.gz)，1,036 项，SHA-256 `16cde8ce1503efe0dc8b6c430ce673f6387b27a6cc60e3868e85a08444791558`。随后结束的 [OpenCode RC1 模型组](evidence/0010/opencode-rc1-model.tar.gz) 单独保存 214 项，SHA-256 `9c7c9b6ff7c8117c16fcfb617c9dc4a6e82d1664d11861bf75aab2c9432f6517`。远端组挂载当时脚本且分宿主启动，DSH 新增实际启动检查没有倒算到旧运行。日志不含私有认证值；完整项目快照是合成数据。当前 RC2 回归为 Python 66 项、Node 28 项 Passed；后续修改另行复验。

RC2 修复在独立分支：DSH patch 使用宿主原生的相对 `./index.mjs` 定位、运行器配置真实日志目录并检查实际 boot；OpenCode 允许同版本 npm 插件配对 Skill，但仍拒绝完整重复安装和版本不匹配；无计划时通过已有 chat.message 提醒授权复杂任务先读取主 Skill，明确简单、只读、诊断与规划模式不初始化。上游状态格式保持不变。

## 早期候选观察（非公开 RC1 准确归档）

- Passed：公开历史脱敏及独立审查，27 对提交只有八个证据 blobs 变化；已用明确 lease 更新公开 master，原 bundle 离线保留。
- Passed：准确候选包 SHA-256 `c3d7191c6f4a0775b0fbc660536d3d911feba5d0ba0d274472f3338e832c9bdd` 从脱敏后的干净源码重新打包，字节与前次归档一致。
- Passed：五宿主加强后的准确归档安装预检和同版本更新、卸载、重装均通过；含完整 npm/平台内容与原生注册检查。这是幂等生命周期，不是远端两版本升级。
- Passed：Codex 与 OpenCode 的真实模型算术冒烟；Claude 修正原生 API base URL 后，实际上下文注入和新会话文件读取通过。
- Failed（保留）：第一轮 Python 3.11 不支持 tar extraction filter；已补安全成员校验兼容。Claude 直连 base URL 多带 `/v1`；已修正。
- Failed（保留）：Pi 的字面环境变量名导致 401，宿主仍返回 exit 0；早期控制器曾错误标记进程成功，该结果不计为模型 Passed。已改用 `$PLANWEFT_MODEL_KEY`、检测原生错误事件，并加入回归。
- Passed：本地安装器 27 项测试；Python 65 项测试，最后边界修订后相关 9 项再次通过。
- Failed（保留）：GitHub 首轮 Windows CI 的故障注入使用硬编码 `/`，未触发预期错误；已修复为 `path.join`，修复后的 Linux、Windows、macOS 安装器及分发 CI 均 Passed，见 [34242500572](https://github.com/psiQAQ/planweft/actions/runs/34242500572)。

- Passed：Codex 维护、冷读、只读与 Skill 读取的自动断言；独立 reviewer 核查维护与冷读语义 Passed。冷读输入快照等于维护输出，未携带旧聊天或插件。
- 未证实：该 Codex 组旧控制器的 `original_containers_preserved=false`，旧总状态仍写 Passed；初始集合混入并发测试容器且未保存 ID，不能追溯证明服务基线保持。维护/冷读语义仍成立，整组隔离验收不计通过。控制器已排除带验证 label 的容器、保存基线与缺失 ID，并将缺失纳入失败条件。五宿主预检组的该项为 true。

证据附件：[脱敏运行附件](evidence/0010/container-trials.tar.gz)，SHA-256 `24ba7e3ffa9c863189f6f5558ed7e9c3868909343e45050d9817e61e854ab98a`。包含 799 个有原始/公开摘要映射的日志与快照；已检查既有认证值无命中。保留失败和旧控制器的原始结果，以上更正优先于其早期总状态。各 summary 的 runner/runtime 摘要属于当次执行，后续源码修订不冒充重跑；附件也不是最终稳定包的 acceptance。

## 固定条件与边界

镜像完整摘要见 `tests/container-images.json`；原镜像保持不变。DSH 派生镜像复制此前验证过的 DSH 0.1.2-rc.1 / pnpm 10.28.2 依赖树，不含认证或用户配置。初次联网构建无进展，改用该可审计的已有本地依赖；不宣称完成了在线重建验证。

模型通信直接访问现有官方 provider；不经过 MemoryProxy、不附加 Lab 身份头、不读写外部记忆、不运行旧清记忆脚本。认证只进临时容器；日志写入前脱敏已知凭据，发现命中则标 Failed 并要求安全复核。

Pi 的全计划内容探针显式采用 parity 模式并通过原生命令激活；DeepSeek 默认 cache-safe 仅提醒读取文件，不宣称默认注入完整计划。Codex 自动化维护场景的单次 trust bypass 不计正常信任；另一次原生 TUI 探针观察到 7 hooks 从未信任/未激活变为激活，随后无 bypass 的新 exec 无工具读出项目随机码。该探针使用隔离容器内 danger-full-access，不能据此声称验证了全部工具权限策略。DSH 使用本次临时会话的原生 JSONL 日志判断工具调用和停止；该采集实现尚待真实模型验证。

## 尚未完成

- RC2 修复后准确包的 DSH/OpenCode 模型复验，以及 Pi context 失败调查尚待完成。
- npm latest 标签删除失败，OIDC 发布与稳定门槛待完成。
- 五宿主最终准确归档的维护、冷读、正常信任、停止限制及语义审查尚未全部通过。
- 远端真实两版本生命周期、Git marketplace、新会话加载、OIDC 候选、稳定提升与 GitHub Release 均待完成。
- Windows/macOS 真实宿主仍为 Not Run；CI 不替代真实宿主。

RC2 修改了本地运行时 overlays；PWF 固定源码与状态协议未改。OpenCode 当前原始对照 34 项 Passed，原生未调整测试 32 Passed/2 Failed（两项有意的协议差异），显式适配断言并加入本地边界测试后 37 项 Passed；不删除原始失败日志。此前其他上游证据仍属历史定位。

对外说明：[发布：中文](../releasing.md) / [English](../releasing.en.md)，[平台：中文](../platforms.md) / [English](../platforms.en.md)。

[RC2 OpenCode 对照附件](evidence/0010/rc2-opencode-regression.tar.gz)，SHA-256 `849f0d46e2326033456666027b04a16380451d3a68f0a5cfee00aefa5d1e2fbe`；包含结构化原始结果、准确输入清单及运行日志。原始失败集合经机器核对，无额外失败或 pending。
