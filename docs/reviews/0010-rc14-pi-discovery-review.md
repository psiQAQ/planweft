# RC14 Pi RC11 Skill 发现与先行配置读取审查

结论：**已有证据没有证明插件定位缺陷；先读宿主配置的行为越界已确证。** RC11 原生预检已发现唯一 `skill:project-docs` 并给出准确绝对路径；固定 Pi 0.84.3 源码会为可隐式调用 Skill 生成含 `<location>` 的系统提示。然而原预检和模型是不同进程，当次模型最终系统提示未保留，因此不能把原生发现结果直接当作“已观察到模型接收到该条目”，也不能因日志缺失反推宿主未提供。

## 当次准确证据

- 证据组：`/var/tmp/planweft-040/pi-rc11-records`。版本 `0.4.0-rc.11`，准确包 SHA-256 `53f78985ae94c14ed589a67fb4342303ce14ea4748b825bca405e1bbf172325b`；Pi `0.84.3`，模型 `deepseek-v4-flash`，镜像 `sha256:e1ad8a1b86193e7f8439de603b7b7d4fe8c806c1b8b0195564b6115b274be89b`。冻结 runner/runtime/fixture 摘要与 summary 逐项一致。
- `native-load.stdout` 的 `get_commands` 成功响应只含一个 `skill:project-docs`。`sourceInfo.path` 为 `/workspace/.planweft/versions/0.4.0-rc.11/node_modules/planweft/dist/pi/planweft/SKILL.md`；`sourceInfo` 同时记录 project scope、package origin、对应包根 baseDir 和相对来源。描述已要求先读 host-listed Skill，且不要用 settings／receipt 定位资源。该绝对路径与模型后来成功读取的路径完全一致；安装内容核对记录为 53 文件 Passed。
- 冻结 runtime 的 `native_load()` 先用 `pi --mode rpc --no-session --approve` 请求 `get_commands`；随后维护另启 `pi --print --no-session --approve --provider release --model deepseek-v4-flash --mode json`，没有 `--no-skills`，同一安装和项目。原生预检时 `PLANNING_DISABLED=1`，维护前清除；该差异是规划扩展的激活边界，不把两个进程强称为同一模型上下文。
- `model.stdout` 按 JSON 事件从 0 计数：事件 499 的 Bash 包含 `cat .pi/settings.json`，对应 507 `tool_execution_end.isError=false`；事件 1520 才 `read` 上述准确 Skill，1523 成功。顺序明确，且固定 prompt 已禁止宿主配置读取。只核对合成任务日志，没有额外读取个人配置或认证。
- 1523 返回 Skill 正文 8,395 字符，其 frontmatter 未设置 `disable-model-invocation: true`。模型流包含 session、agent／turn／message／tool 事件，未包含 system role、原始 `<location>` 或 `systemPrompt` 字段。`<available_skills>` 字样仅见于模型自述及其流式重复，不能作为原生系统提示证据，也不复制这些内部文本作为报告依据。

## 固定镜像源码核查

源码由主 Agent 从同一完整镜像 ID 的从未启动临时容器复制到 `/var/tmp/planweft-040/pi-0843-discovery-source`；本 reviewer 没有创建／启动容器。`provenance.json` 中 10 文件大小与摘要独立核对全部一致，package version 为 0.84.3。不采用 `/tmp/pd-030-clis/pi` 的不同版本元数据。

主逻辑位于准确编译文件 `chunk-E5KXRMZK.js`，SHA-256 `0d162b1014afe5343a86c2606a1c40f5cc3cccf7d739ffd304ba54cac0b1ec50`。以下位置为解码文本的字符偏移，便于复查压缩源码，不是源映射行号：

| 函数／分支 | 偏移 | 已核对语义 |
| --- | ---: | --- |
| `formatSkillsForPrompt` | 2729712 | 过滤 `disableModelInvocation`；每个可见 Skill 输出 name、description、filePath 对应 location；说明使用 read 读取、相对路径按 Skill 父目录解析。 |
| `buildSystemPrompt` | 2733137 | 普通／custom prompt 路线均在 read tool 可用且 skills 非空时附上相同格式。 |
| `_rebuildSystemPrompt` 的资源读取 | 2845330 附近 | 同一 resourceLoader 的 `getSkills().skills` 输入 buildSystemPrompt。 |
| `get_commands` | 3638611 | 从 `session.resourceLoader.getSkills().skills` 列出 sourceInfo；它没有过滤 `disableModelInvocation`，所以“命令列出”单独不足以证明模型可见。 |
| `emitBeforeAgentStart`／prompt | 2693289／2848921 | 扩展可返回 systemPrompt 覆盖，最后赋给 agent.state.systemPrompt 后执行模型；此后实际值未包含在旧模型日志中。 |
| `runPrintMode` | 3616436 | JSON 输出 session header 与订阅的 agent events，不主动输出最终 systemPrompt。 |
| RPC `get_state` | 3633985 | 返回模型、会话、流式及计数等字段，没有 systemPrompt。 |

据此，“在此次资源集合与 read 可用、不被后续覆盖的条件下应生成准确 location”是有源码支持的推断；仍不把它写成当次直接观测。当前没有坏链接、错误安装路径或缺少 Skill 注册的证据，因而不建议为此次越界先修改 installer 或复制布局。

## 下一次最小采集建议

1. **保留现成原生发现 projection。** 仅保存 `project-docs` 条目数量、name、description、sourceInfo 的 path/source/scope/origin/baseDir、对应 Skill 字节摘要及 frontmatter 可隐式调用标志；记录 CLI／镜像／准确包、PID、项目、时间和采集命令。未知或多条来源保持失败，不能任选 first。现有独立预检已足以诊断注册；若改为与维护同一 RPC 进程先 `get_commands` 再 `prompt`，须明确这是 collector/transport 变更，不伪装成原 print 模式无变化复验。
2. **需要证明实际系统条目时，单独增加只观察的诊断。** 固定源码支持 `before_agent_start` 事件提供 `systemPrompt`，且 `ctx.getSystemPrompt()` 可读当前值；可由外部诊断观察器在已核对加载顺序的最后位置只投影 `<available_skills>` 中 project-docs 条目，记录系统提示整体 SHA 与 read 是否启用，返回 undefined、不改文本、不注册模型工具、不给模型新增任务指示。必须证明观察器之后无其他覆盖，并核对最终 agent.state 赋值路径；无法证明时标为“观察点上的 prompt”，不声称最终送达。新增观察器是诊断环境变化，不能直接替代未经观察器的准确包维护验收，也不是插件原生投递证据。
3. **不要用不合适导出补洞。** `get_state` 没有该字段；`export_html` 虽可导出 state.systemPrompt，却拒绝 `--no-session` 的内存会话，并带完整 entries／工具内容，不是当前范围内最小元数据方案。不要为了采集而读取旧会话、个人 settings、auth 或整段 provider 请求／响应头。只处理本次合成项目、公开 Skill 条目及摘要，异常保留有限错误而不泄露整个 prompt。
4. **沿用真实顺序判据。** 后续继续记录首次项目入口读取、首次 Skill 读取、任何 settings／receipt 读取及成功结果；自动 Skill 先读后再解析资源才是目标。发现列表正确不等于行为已遵循，完整 Skill 读取也不能撤销此前配置越界。

本次仅做既有合成日志与固定源码的只读核查；未运行模型、Docker、认证操作或安装，未修改原证据。旧自动 Passed 不代替独立语义范围审查，旧失败不被本报告改写。

## 证据绑定（相对证据组）

- `summary.json`: `793188d263a23b9e37b98e098600fd2259aaf5b947746f392ae67f71a00f4f72`

- `runner.py`: `1c32bab865e205a3150c8aedf82e5e1edb686bd100711edb00335b569c2d234c`

- `runtime.py`: `1c7772f17a96a87257841003d1076f1e52fdd4c9befeac8a3525ef5b121957d7`

- `fixture.py`: `34185c82cb4b6056f6fb8597cc4a44a513535af298738a3a8be5e9be7ee470d7`

- `pi/maintenance/raw/native-load.stdout`: `63e08464ecde604d313cb500ae014660581209cd595591a8da5604877768a76f`

- `pi/maintenance/raw/native-load.json`: `0678ed3b64655cab05b6a445ae906204caaffac33fa6cfb08fbb6d9ff7b13968`

- `pi/maintenance/raw/model.stdout`: `314fe26007e44b5143b1d26e74d588bc22b90a06c8c65ee84246ea2cd5583a7c`

- `pi/maintenance/raw/model-invocation.json`: `a575582bf8302b312e5b9bae0441cf2e86ae3c5a4635c4415e046aa44b48f9f4`

- `pi/maintenance/raw/model.json`: `f024cb206dd702ff5e8b7ce7948ea96431a16e157a0f4b19b82f1a3842d93213`

- `pi/maintenance/raw/installed-content.json`: `82c1fc56691a4b3df10155d9d5b9f17ac574eae37f1041c1a3c8572d39bf1dd9`

- `pi/maintenance/raw/version-pi.stdout`: `e470244f5d207065cacf7314a910c7cff5fc8334840dc42426d62da3e661f580`

- 固定源码 `provenance.json`: `5b43080ec097e968629c91ae33e7122a3c6dff26115ac352e5d5290350c0e1ee`
