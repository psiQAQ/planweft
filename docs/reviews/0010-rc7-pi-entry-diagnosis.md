# RC7 Pi 入口诊断（只读设计审查）

结论：应把主 Skill 第 2 步的“selection is valid”抽象判断替换成可观察结果与操作的分支表，并直接采用宿主已提供的 Skill 路径。无需新增自动写入 hook、调度器、计划状态格式或安装依赖。此次不实现代码、不启动模型、不改原始证据。

## 1. 真实失败对应

准确包为 `0.4.0-rc.7`，SHA-256 `e3d67af7dcba154a3800e39c19ec06a7f40b874d3b92dc7b7517bed85cc4bed2`。

证据组：`/var/tmp/planweft-040/pi-rc7-records`。maintenance/raw/model.stdout SHA-256 `6777dbb95b0b24952d1e78b66f653310501b768adee50aa75d648eb9aa30b2e2`。

- 原生第 1019/1023 行：实际读取并返回精确 RC7 Skill，含“旧 non-PWF 记录不能替代初始化”。这不是 Skill 未发现。
- 第 7839/7845 行：实际 resolver 输出为空、rc=0、`.planning` 不存在；`PLAN_ID` 与 `PWF_PLAN_ROOT` 未设置。
- 模型读取 init-session 源码但未执行，明确把缺少 selector 与 README 指向 notes/work.md 解释为保留旧权威状态的理由。结果为 **零个** task_plan，不是两个计划冲突或计数器问题。
- 第 1018/1026 行：为了定位安装读取 `.pi/settings.json`，违反固定实验禁读宿主配置的范围；结果仅为包路径，没有证据表明泄露凭据。
- README 只给工作记录链接，AGENTS 只要求保留用户改动、最小任务修改；没有禁止新增记录、禁止采用 PWF 或要求旧记录永远权威。此次错误例外是模型推断，不能归因于用户禁令。

## 2. PWF 固定源码契约

依据 vendor 固定 v3.17.0，对应提交 `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`。源码归档 SHA-256 `4175b623648517c1a0cbff782d789fe9f542cc638e5b12c38559bcf445cafb6a`。本审查通过构建器 read_upstream 在内存读取，未改归档。

| 事实 | 源码依据 | 对入口的影响 |
| --- | --- | --- |
| resolver 空输出并不唯一表示“无计划”；非法根绑定也空输出且 rc=0 | [resolve-plan-dir.sh L20–44](https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/skills/planning-with-files/scripts/resolve-plan-dir.sh#L20) | 不能以退出 0 当作选择有效，更不能将任何空输出都变成初始化许可 |
| 非空 PLAN_ID 是绑定；无目录、无效 slug 或 containment 失败时终止解析，仍 rc=0 | [同文件 L300–326](https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/skills/planning-with-files/scripts/resolve-plan-dir.sh#L300) | 已设置 selector 而未解析出计划时，修正选择；不回退、不另建一个替代任务 |
| 未设置 selector 时可从 active pointer / newest named plan 解析；都没有时空输出，调用方检查根 task_plan | [同文件 L4–14](https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/skills/planning-with-files/scripts/resolve-plan-dir.sh#L4)、L271–329 | “未设置 PLAN_ID”是正常无显式选择状态，不是初始化前置条件失败；必须区分 legacy 根计划与完全无 PWF 计划 |
| canonical English Shell 给任务名即启用具名计划；无参数是根三文件 legacy 模式 | [init-session.sh L4–17、L95–99](https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/skills/planning-with-files/scripts/init-session.sh#L4) | Pi 主 Skill 可明确调用带任务名的 Bash initializer，不必预先设置 PLAN_ID |
| Shell 具名初始化生成 ID、目录、三文件、active pointer，打印 PLAN_ID；碰到同名目录会增加后缀 | [同文件 L377–402](https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/skills/planning-with-files/scripts/init-session.sh#L377) | 调用后必须使用其实际输出并核对三文件；不能在新会话重复初始化，不能预先猜 ID |
| initializer 的 PLAN_ROOT 来自 PWD/.planning；create_files_in 跳过已有三文件 | [同文件 L337–384](https://github.com/OthmanAdi/planning-with-files/blob/0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7/skills/planning-with-files/scripts/init-session.sh#L337) | PWF_PLAN_ROOT 绑定与工作目录必须先对齐；不能用 root pin 解析 A 却在 B 初始化；既有记录不覆盖 |

Pi 本地适配还在 `dist/pi/planweft/extensions/planweft/plan.ts:205–225` 明确：空 selector 继续正常解析；隔离开启且多计划时不采用 shared pointer/newest fallback。不能让 Shell 的 newest fallback 绕过宿主的多会话隔离拒绝。

## 3. 最小执行流程替换建议

修改位置为 `overlays/planweft/entrypoints/en.md:13–19`、对应中文第 13–19 行及另四语言的同源第 2/3 步。用下表**替换**“If selection is valid”段落，不另加重复强调段或再前置一份流程。

先沿用第 1 步的范围检查：只读/诊断/宿主 plan mode 不初始化；简单任务不建计划；明确禁止新增或采用、明确旧计划必须继续权威时按用户规则工作。明确要求的书面调研产物例外保留，不顺带建立规划层级。本插件开发仓库仍须另行授权接管。

随后在已确认的目标项目根，以已读取 Skill 的绝对路径定位 helper，用解释器执行（resolver 用 `sh` 或 PowerShell；canonical initializer 用 `bash`），只使用本任务已提供的 PLAN_ID/PWF_PLAN_ROOT，不扫描完整环境或宿主配置。

| 实际观察（按顺序判断） | 下一步 |
| --- | --- |
| 根绑定无效、非空 PLAN_ID 解析为空、宿主报任务隔离歧义，或现存计划/指针无法确认归属 | 停止计划选择并修正绑定/确认所属任务；不取消 selector 来强行回退，不把“rc=0”当作有效结果 |
| 解析出了本任务合法目录，且 task_plan.md 存在 | 读取该目录三文件并接续；缺少的辅助记录在本任务范围内处理，不另建第二任务 |
| 无显式 selector/绑定错误、无命名计划，解析为空，但目标根 task_plan.md 存在 | 按 PWF legacy 兼容读取根三文件；不因希望使用具名目录而迁移既有合法计划 |
| 无显式 selector/绑定错误、无命名计划、目标根也没有 task_plan.md | 这是正常的“尚未初始化”。对第 1 步确认属于该工作流的已授权任务，执行包内 initializer；旧 notes/work.md 只提供初始资料，不代表已有 PWF 计划 |

读取 `.planning` 选择信息仅限本项目已允许的文件。若空输出伴随可疑现存指针/候选目录，不猜测“无计划”；保留 fail-closed 分支。

Pi canonical Shell 初始化后：读取实际输出的目录与 PLAN_ID、核对三文件确实存在、填写目标/当前阶段/下一步与实际来源，然后一次性把旧工作记录动态状态入口改成相对链接。保留旧历史、批准需求与用户修改。必须完成这个可观察的后置条件后再进入实现阶段；“读过 init-session 源码”不是已初始化。

### 跨语言/解释器不能虚构的差异

固定 PWF 的 canonical `init-session.ps1` 只有 ProjectName/Template/Autonomous/Gated 参数，按 cwd 写根三文件，不提供具名目录/PLAN_ID 输出；五种 i18n 的 Shell/PowerShell initializers 同样为 legacy 根布局。当前入口笼统写“或 .ps1 并使用输出 PLAN_ID”并非所有 adapter 的真实能力。

本次最小文案修复应说明“采用包内 initializer 实际支持的布局并核对位置”：canonical English Shell 用输出的具名路径；legacy helper 用已确认工作根三文件，不捏造 -PlanDir 或 PLAN_ID 输出。若任务已绑定具名计划或多 worker 共用项目，不能让 legacy helper在项目根另建竞争计划，应复用所属计划或按既有独立 worktree 规则隔离。这是保持原生差异，不要求本轮改写 PowerShell runtime。

## 4. Pi 已有的 Skill 绝对路径

**Fact：Pi v0.84.3 的原生提示格式已提供 Skill 文件路径。** `formatSkillsForPrompt` 给每个可自动调用的 Skill 输出 location=filePath，并提示相对资源按该 Skill 目录解析；loadSkills 将显式资源路径解析到绝对路径。[Pi skills.ts L332–350、L441–455](https://github.com/earendil-works/pi/blob/v0.84.3/packages/coding-agent/src/core/skills.ts#L332)

默认与 custom prompt 的 read-tool 分支都会加入该技能列表。[Pi system-prompt.ts L57–60、L146–149](https://github.com/earendil-works/pi/blob/v0.84.3/packages/coding-agent/src/core/system-prompt.ts#L146)

**实际运行佐证：** `/var/tmp/planweft-040/pi-rc6-project-approval/pi/package-approval/raw/native-project-approved.stdout` 的 `skill:project-docs` sourceInfo.path 是绝对 SKILL.md 路径、baseDir 为对应包目录；project origin 明确。RC7 本身也成功读取了精确包内 Skill，因此不能归因于安装资源不可定位。

**证据边界：** RC7 model.stdout 不保存完整 system prompt，所以不能声称直接截获了那一会话的 available_skills XML；这里是固定官方源码协议与真实原生资源登记的交叉依据。

最小替换句意：先使用宿主 Skill 列表提供的 location/filePath，或刚刚成功读取的 SKILL.md 路径；取其父目录作为唯一安装资源根。该路径已足够时，不重新发现安装、不读取 `.pi/settings.json`、HOME 配置或个人缓存列表。如果宿主确未提供路径，才报告资源定位不足并采用该宿主已有公开资源接口；不要猜个人配置位置或广搜磁盘。对其他宿主使用同一“已提供位置”原则，不硬编码 Pi XML。

## 5. 验证与最小下一步

先用不调用模型的契约场景验证表格分支：无变量+旧 notes→初始化；legacy 根计划→接续；有效具名→接续；错误 PLAN_ID/错误根绑定/隔离多计划→拒绝回退；明确只读/禁新增/旧权威要求→不初始化；有资源 location→不需读取配置。Shell 与 legacy PowerShell/语言 helper 的实际输出分别断言，不以相同 API 假设代替测试。

随后才以同一固定维护任务和模型验证默认匹配，任务提示不新增显式 Skill 调用或正确答案；应看到实际初始化、三文件、旧状态入口迁移和仅授权路径读取。冷读使用最终文件新建会话，不能把先前错误答案传给新读者。保留 RC7 失败并关联具体入口变更；记录模板本身在此次 Pi 失败中没有被执行，不能当作模板修复失败或成功。

本诊断不保证文案修改可让任意模型必然遵循流程；它消除的是已证实的执行歧义，并保留所有拒绝与用户范围分支。后续真实运行仍须按实际证据决定 Passed/Failed。
