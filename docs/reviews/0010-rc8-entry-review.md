# RC8 entry and plan-selection independent review

结果：**Passed（源码与小型离线契约审查；未发现阻塞问题）**。这不是模型采用行为验收，也不替代准确 RC8 包或正式 0.4.0 验收。

范围：六语言 entrypoints、plan-selection.md / plan-selection.zh.md、build-plugin.py 的相应差异、test_plan_selection_contract.py 和 test_skill_entrypoints.py。只读取源码、在临时目录运行离线测试；没有修改被审文件、生成分发物、运行 Docker 或模型。

## 契约核查

- **空输出分支已修复。** 入口第 2 步不再以 exit 0 / “valid selection” 推断可初始化；按非空 PLAN_ID 拒绝、根绑定无效、多命名计划未选定、有效所选计划、legacy 根计划及真正无计划分别处理。引用说明明确不能清除绑定去获取别的计划。对应固定 resolver 的拒绝返回行为，四个真实 Shell 契约测试覆盖无计划与拒绝同为 0/空输出，以及禁止回退到另一计划。
- **例外未扩大或删除。** 六语言均保留只读、诊断、宿主规划模式、简单任务、明确禁止新增记录/采用、旧计划必须权威，以及书面研究产物不授权额外计划层级。本开发仓库不自动接管；一般“最小改动/沿用资料”不再被当作禁止初始化。范围检查发生在分支表之前；未增加写文件 hook。
- **项目根和安装路径分离。** 脚本来自宿主提供的 Skill 绝对位置；工作目录必须是授权目标项目，非空 PWF_PLAN_ROOT 必须与目标一致。引用明确 canonical init 不自动 cd 到该变量，对应实际脚本中 PLAN_ROOT="${PWD}/.planning"。无需读取 Pi settings 或安装 receipt 查找资源，直接对应 RC7 Pi 的禁读问题。
- **解释器与初始化布局准确。** resolver 是 POSIX sh；canonical English init 是 Bash。入口和引用明确 PowerShell、本地化 legacy 及 Mastra 旧副本不保证命名计划/PLAN_ID，而使用其实际 cwd 三文件；不虚构参数。缺失个别记录时，不再次运行命名初始化器另建计划；引用要求只补缺失模板或按实际接口处理。Shell 命名初始化离线测试实测中文/空格项目路径和旧 notes CRLF 字节保留。
- **记录职责修复有实质内容。** 六语言将 observation date/revision、before/after 范围、任务前已有修改纳入主流程字段，完成检查要求与最终文件核对“当前行为”并追加更正。该步骤在模型重写模板后仍可见，直接对应 OpenCode RC7 读取新模板后覆盖 findings、保留 stale current claims 的失败；没有增加第二动态状态来源，也未授权修改批准需求。
- **语言边界一致。** en/zh/zht/de/es/ar 对应分支、cwd 约束、实际 initializer 差异、单一状态、失败记录、独立冷读与历史 Passed 的规则一致。新增参考只有中英文；其他入口明确链接英文参考，未声称存在另外四种参考译本。
- **渐进披露与独立目录资源。** 触发 description 缩短，原先已作身份映射的宿主 description 原文保存在该入口自己的 PWF manual 的 Adapter metadata 段，而非丢弃。main entry 仍保留 session-history 显式授权、默认提醒、PLANNING_DISABLED、不同停止能力和 INSTALL 指引。构建器给每份 Skill 加入两份 selection reference；检查全部 15 个平台的 42 份有手册入口，selection 文件和 adapter metadata 均存在。此检查使用内存 distributions(compiled=False)，未写 generated。

## 非阻塞的清晰度与覆盖建议

1. zh/zht 表格的“没有 PWF 计划或待纠正绑定”可以改成“没有 PWF 计划，且没有待纠正绑定”，en 的 “No PWF plan or pending binding exists” 可以同样写成 neither/nor。现有拒绝行和前文已明确不初始化，当前不是行为漏洞；显式合取更便于模型和读者判断。
2. 当前新增 4 个测试覆盖核心无计划/拒绝/legacy/named-init 状态，但没有运行 PWF_PLAN_ROOT 与 cwd 不同的反例、多个命名计划未选定、PowerShell或全部 localized init。源码说明已准确，相关未测项应保持 Not Run，不能用这 4 项泛化为所有 initializer 实测通过。
3. ar/de/es/zht 将第 1/3/4 步写为列表、第 2 步写为 heading；不会改变语义，但统一成 heading 可避免 Markdown 渲染自动重编号。这不是本次发布阻塞。

## 实际验证

- `python3 -m unittest discover -s tests -p test_plan_selection_contract.py -v`：**Passed，4 tests**。
- `python3 -m unittest discover -s tests -p test_skill_entrypoints.py -v`：**Passed，2 tests**。
- 内存构建资源核查：**Passed，15 platforms / 42 manual-bearing entries / 0 missing references or adapter metadata**。首次审核脚本使用 `./references/...` 键，导致 reviewer 自身 KeyError；规范化路径后重跑成功，不是产品失败。
- PowerShell 实际执行、模型默认匹配、新拒绝/初始化分支的真实会话、完整上游迁移回归、编译分发、最终准确包一致性：**Not Run by this reviewer**，由主 Agent 对应验收负责。

审核没有修改上游归档或原始失败证据。RC7 Pi/OpenCode 的真实失败仍应保留；此修复只有在准确新包的固定任务验证后才能判定解决模型行为问题。

## 追加复审：发现阶段披露与宿主目录复用

本节保留上面的初次审查，不把后续发现覆盖成从未失败。以下均为源码、内存分发与离线测试证据，不代表模型验证通过。

### 初次失败与已完成修复

- 缩短 description 后，上游原始公开披露测试出现 **3 Failed / 718 Passed / 63 Skipped**；原始运行证据保留。问题是发现阶段未披露关键能力与同意边界，不能仅凭手册仍含原文就认为原契约等价。
- 新 `skill_description(path)` 恢复了简洁的任务触发、项目文件恢复、显式 `--metadata` / `--replay`、不执行 Markdown 声明的命令、无上传路径和宿主特定续跑限制。完整上游原句仍留在对应来源段，description 的本地任意 300 字符上限改为 600。无需调整原始上游披露测试。
- 首次只按源码路径生成 description，独立运行新增 `test_skill_entrypoints.py` 暴露 **7 个 subtest Failed**：Gemini 主 Skill，以及 Continue 主 Skill 和五份语言变体，在最终分发中复用了 canonical 文件，仍带通用 gated 描述，缺少各自实际限制。
- 在 `native.adapt()` 后按最终接收宿主重新生成 frontmatter 后，独立复跑 **3 tests Passed**，上述七项错误关闭。该步骤保留原模式位、正文和其他 frontmatter，不改 hooks 或执行权限。触发词改为 `handoff, including existing notes`，避免将已有 notes 暗示为新任务的前置要求。

### 共享手册来源说明与新发现

Continue/Gemini 的共享手册原文含 “lifecycle hooks inject” 和 conditional gated 说明。仅写 fixed upstream 区分了版本，不能可靠区分当前接收宿主。新增 `Installed adapter boundary` 将 Continue 无 lifecycle/Stop/continuation、Gemini session-end status-only/no continuation 放在来源原文之前，并明确来源材料不能确定当前适配器的事件或权限；原 metadata 原文保留。此说明的语义是充分且必要的。

独立逐份链接核查进一步发现，新增 notice 的 `../SKILL.md` 在 Gemini 五份已降为 `GUIDE.md` 的语言参考中不存在；相同五份 GUIDE 的 frontmatter 也未被只匹配 SKILL.md 的接收宿主改写覆盖。三项本地测试当时仍 Passed，因为只枚举 SKILL.md。已反馈给主 Agent：按真实入口选择链接目标，并将 demoted language GUIDE 纳入对应元数据检查。它们不是自动发现主 Skill，不能把这五处等同于前述七项发现阶段错误；但不能宣称全部语言资料已正确。最终关闭结果见本节后续补充。

### 上游契约未改写

独立从固定归档读取原文件，并与内存迁移文件对照：

- `tests/test_public_capability_disclosure.py` 迁移内容严格等于原文的既有 `identity_text()` 映射；没有扩大 `_description` 读取范围、删断言或跳过测试。
- **21 个 assert 的 AST 完全一致**（在原文施加相同身份映射后对照）。
- 原测试 SHA-256：`bce54e9a28ba41ac40d558730121797785f39e0c320b8495f524a59a3fb3e804`。
- 迁移测试 SHA-256：`fb7af1c1d73ba3e7d4eb35c8bd697fd8519b6f9836e225e9ff78f35e45f4dd95`。
- 固定上游归档 SHA-256 仍为 `4175b623648517c1a0cbff782d789fe9f542cc638e5b12c38559bcf445cafb6a`。

完整上游回归、准确打包和模型场景由主 Agent 独立执行；本 reviewer 没有运行容器或模型。

### 最终定向复验：语言 GUIDE 与手册链接问题关闭

**Passed；本轮独立审查未留阻塞项。** 本结论仅关闭上述源码/生成资源问题。

- 最终接收宿主的 description 改写现在也覆盖 `references/language-variants/.../GUIDE.md`，所以 Gemini 五份语言参考明确披露 status-only/no continuation；保留这些文件作为显式参考的布局，未重新创建可重复自动发现的 Skill。
- 手册 notice 在每份手册所属的入口目录内选择实际存在的 `SKILL.md` 或 `GUIDE.md`；都不存在时构建报错。新增链接检查逐份验证 Continue/Gemini 手册的目标存在，Gemini 五个错误链接关闭。
- 原手册内容和模式位保留：Gemini 的资源差异测试只允许前置 notice，要求完整原始字节仍为最终文件尾部、模式位完全一致，其余原资源等值断言保持。
- 独立运行 `python3 -m unittest discover -s tests -p test_skill_entrypoints.py -v`：**Passed，4 tests**。
- 独立运行 `python3 -m unittest discover -s tests -p test_native_resource_paths.py -v`：**Passed，3 tests**。

未重跑全量、未运行模型/容器，也未修改被审实现文件。前述失败、发现和更正仍保留；正式发布门槛及真实模型行为的结论不由这些定向测试代替。
