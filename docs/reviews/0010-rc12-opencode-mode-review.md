# RC12 OpenCode 原生模式入口独立审查

状态：**Passed（静态设计审查）**。模型行为、准确 RC12 归档与发布验收 **Not Run**。本审查不改变 RC11 原始评估或独立审查结论。

审查者：独立 `skill_entry_review` subagent。范围：只读核查生成器与编译入口的差异；仅写本审查文档，不修改运行实现、不启动模型或容器。回归和构建一致性证据由主 Agent 补充。

## 依据与最小修复

RC11 OpenCode 维护的原生记录 `raw/model.stdout:2` 已交付主 Skill，其中明确默认 `advisory`。但 `:30` 的 `pw_init` 调用显式传入 `mode: autonomous`（call `call_00_ijn9LlaaqNp2GdkLouZE3564`）；固定维护任务未选择该模式。原生工具说明此前只介绍 `autonomous` / `gated` 及其效果，没有说明省略参数的默认路线。宿主 `opencode run --auto` 与 PWF 规划模式是不同接口，前者不能充当用户对后者的明确选择。

本次修复限定在模型实际看见的原生工具选择面：

- `pw_init.description` 说明省略 `mode` 为默认 advisory，仅在用户明确请求对应模式时传入 autonomous / gated；一般维护授权不代表选择该模式。
- `mode.describe` 提供相同的省略与显式选择规则。
- 生成器仅在 enhanced OpenCode 映射后的 `src/index.ts` 应用两处替换；每个旧字符串必须恰好出现一次，否则停止生成并要求审查。

编译后 `index.js` 的实际 diff 恰好是上述两条描述。它针对原生 schema 中缺少默认选项的具体问题，没有继续向主 Skill 前部堆叠规则。未发现需要扩大到新 helper、状态字段或授权 boolean 的依据。

## 保持的运行语义与限制

`initPlan` 的默认和显式运行逻辑不变：省略 `mode` 仍归入既有空值 / `legacy` 路线，不调用 `applyV3Mode`；显式 autonomous / gated 仍按原协议写模式、nonce、停止计数与 attestation。字符串 `advisory` 不是该参数当前接受的值，正确的默认使用方式是**省略参数**，不能建议传 `mode=advisory`。

本次没有改变参数类型、必填性、模式校验、初始化流程、工具权限或 PWF 磁盘协议。两条说明是选择指导，不能在运行时证明用户授权，也不能强制模型服从。静态通过不能证明新的真实维护会话会保持默认模式，更不能关闭 RC11 的范围越界或记录错误。

主 Agent 应补充：两处描述的受控 diff / guard 反例、默认省略与显式模式的既有行为回归、编译产物一致性，以及新准确包的原生模型验收。本审查未执行这些测试。

## 源码摘要

以下为本次实际读取文件的 SHA-256，绑定工作区候选补丁，不表示这些文件已经发布为 RC12。

| 文件 | SHA-256 |
| --- | --- |
| `scripts/build-plugin.py` | `cdde71f4f200d5aa4224499fc55e0b0651a5c0e65854fa49088aae04fe848b1d` |
| `overlays/planweft/opencode-compiled/dist/index.js` | `a189e78721ac895c987b1a12575a08ecbfac585dc308a989b9f084c47154dac1` |
| `overlays/planweft/opencode-compiled/dist/core.js` | `b1548dc5ce5e5d6ec9d8cee35b53d827f0521b734892abdd08dadd751a4307d9` |
| `overlays/planweft/opencode-compiled/manifest.json` | `4a7c1ff634e670d6826affcdd3eb86f9697766a1ebecd655fb27f3e6b7d2b55a` |

## 附：宿主设置读取的只读根因核查

两次失败不能合并为同一种加载前故障。按原始原生调用与返回核对：

| 场景 | 实际顺序 | 可以支持的判断 |
| --- | --- | --- |
| Claude RC10 | `raw/model.stdout:348` 调用 Skill，`:350` 宿主交付完整正文及明确 Base directory，`:626` 才 Read `/workspace/.claude/settings.json` | 是 Skill 正文交付后的范围违背，不能解释成没有先获得路径或正文。 |
| Pi RC11 | `:495` 提交含 `cat .pi/settings.json` 的 Bash，`:519` 返回该调用实际内容；`:1520` 才提交 Skill read，`:1531` 返回正文 | 是 Skill 正文加载前的实际配置读取。`:495` 与 `:519` 是同一 call 的提交 / turn_end 重复呈现，不是两次执行。 |

Pi 的单独原生 `get_commands` 证据 `raw/native-load.stdout` 已提供 `skill:project-docs`、绝对 Skill 路径及包含 `SKILL_LOOKUP` 的完整 description。这证明安装发现表面有路径与规则，不自动证明每一次模型请求的系统提示完整包含该表面；若需调查传递丢失，应检查宿主实际渲染路径与消息装配，不应先假定丢失。Claude 则已有同一会话的完整正文返回证据。

`SKILL_LOOKUP` 限定“不要为资源定位读取 settings / receipts”；固定实验 prompt 另外明确禁止任何宿主配置读取。不能在事后仅凭 settings 中含包路径，就推断模型唯一动机是资源定位；也不能把前者有限的规则当成用户禁令的例外。本次可直接确认的是实际工具读取违反了明确实验边界。

当前没有证据显示插件运行必需模型读取 settings：Claude 返回了 Base directory；Pi 原生发现给了绝对路径；规划脚本可从 Skill 路径与项目 cwd 工作。settings 是原生安装所需的宿主配置，不应通过删除它或改变默认 scope 来隐藏失败。将安装改为隔离 HOME 的 user scope 可以形成另一个合法场景，但不能替代现有 project-scope 门槛。

可作为产品修复依据的情况，是实际发现输出遗漏路径、资源解析错误地依赖 settings、适配器给出互相冲突的操作指示，或约定的宿主权限配置没有被安装器正确接入。需先取得这些因果证据再做最小源修复。本次看到的路径与正文不支持这些缺陷已经存在，因而不建议无依据增加第三份禁读说明、自动改项目记录的 hook，或用无变化重试挑选成功。

RC11 Goal 范围摘要可帮助初始化后的上下文恢复，无法倒溯防止之前的访问，也不是工具权限层。若需要确定性阻止访问，应另行使用宿主实际支持的权限 / 沙箱，并验证配置读取和任意 Bash / Python 间接读取的覆盖范围。Pi 的包 approval 不能冒称通用逐工具文件沙箱。按路径字符串拦一个 `Read` 或 `cat` 也不是任意文件访问隔离。

原生保护场景必须分别记录：模型是否尝试、宿主是否拒绝、是否实际返回文件内容、文件是否改变。真实拒绝可以证明权限保护有效，不能证明模型从未尝试违反任务，也不能直接替代无保护的原始 prompt-compliance Failed。当前发布门槛仍应保留，不以更换模型、去除设置文件、改变固定任务或改装 scope 无变化重试来放行。

## 主 Agent 后续验证（非原独立执行）

RC12 版本提升后，编译 `index.js` 相对原 RC11 仍仅改变上述两条工具说明；`core.js` 仅改变 VERSION 常量，初始化运行逻辑不变。固定 TypeScript 5.9.3 再编译一致。原始 OpenCode 34 tests Passed；迁移原始结果 32 Passed / 2 Failed，失败集合精确等于既有记录的无计划提醒与包内模板发现差异；保留原始日志后，仅按既有两处 fixture 差异调整，37 tests Passed。没有为 mode 补丁删除行为断言或新增 skip。准确 RC12 模型效果仍 Not Run。

版本提升后的实际源码绑定如下；最初审查绑定保持，以免把早先阅读冒充后续执行。

| 文件 | SHA-256 |
| --- | --- |
| `scripts/build-plugin.py` | `f23b170ca35827c6c7a67d7767917b6c8d8e3247401419c1ca85adfa556a1643` |
| `overlays/planweft/opencode-compiled/dist/index.js` | `a189e78721ac895c987b1a12575a08ecbfac585dc308a989b9f084c47154dac1` |
| `overlays/planweft/opencode-compiled/dist/core.js` | `4d8c444b3a6b86fef56593c900c7066d0381ead0d0e7991278de8be8175b13e9` |
| `overlays/planweft/opencode-compiled/manifest.json` | `2c162757ced3d19811ec0696c2314e16968304dd8f97ebdb73d87ecc2f93bdfb` |
