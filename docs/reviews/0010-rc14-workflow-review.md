# RC14 工作流分支与本地操作独立审查

结论：所审改动没有发现阻塞性设计错误。它把已有的例外判断改为可观察的三分支动作，并给出资源链接解析及项目内手工临时目录的具体例程；没有新增自动写文件 hook、批准机制或第二份状态记录。它仍是待固定任务／模型验证的行为干预，不能宣称已经修复 Claude、Pi、DSH 或 OpenCode 的真实维护失败。

## 依据与语义边界

背景采用 `/tmp/planweft-rc13-maintenance-repair-analysis.md`（SHA-256 `3e638f2e6dcd3c93cdf06f633c5e9a1ba0e2967d0d22361157182387f4cd8199`）中对原始失败的分类。旧入口已包含正确例外和禁止句；因此本次新增价值是执行动作及归因证据，而不是声称原来完全缺少边界。源码 diff 与完整英文入口核对后：

- 六语言共同要求在现有回复或 Goal 说明实际适用分支：只读／诊断／宿主规划模式不修改；简单任务说明范围；明确限制须引用原句和来源；其余已授权实质实施说明未发现禁止采用的指令，然后进入原有 resolver／初始化流程。用户及项目已有权限仍为前提，未把“没有禁止”单独当作授权，也不新建判断文件。
- `task_plan.md` 的唯一动态状态、已有计划绑定失败处理、批准需求与用户修改保护、自动恢复文件边界及独立冷读均保留。真正禁止新增文件／旧计划必须权威的任务仍可走例外，不改写固定维护任务或用显式调用替代自动匹配。
- 六语言新增分支、实际来源、资源链接、手工临时路径记录语义一致；中英文操作文档互链，代码块逐字相同。其他语言引用英文及简体中文操作说明，并未伪称有六份本地操作译文。
- 结构化分支能否改变 Claude 已完整读取但仍误判的行为，仍需观察“引用了哪条实际规则／没有禁止的结论／解析与初始化实际执行”。Pi 在读取 Skill 之前的配置访问不可能仅凭正文保证消失；应继续核对宿主实际 discovery location 和读取顺序。

## 例程审查

1. `Path(host_supplied_skill).resolve(strict=True)` 正确按符号链接父目录解释相对 target，并由真实 `SKILL.md` 的 parent 定位资源；缺失路径、非文件、非 `SKILL.md` 名称显式失败。例程不搜索配置、收据或全盘，不改变 helper cwd。它只接受宿主已提供的位置；不能以此宣布所有宿主都会提供有效 location，也不是对恶意并发链接替换的沙箱承诺。
2. `TemporaryDirectory(prefix='.pw-scratch-', dir=resolved_project)` 使用显式已授权项目；输出实际相对目录，context manager 清理本次创建目录且覆盖常规异常。注释明确需把真正手工检查和所有输出放入块内；空例程不是已经完成检查的证据。中文／空格参数无需 shell 插值。没有全局修改 Agent TMPDIR，不会把宿主私有临时数据有意导入项目。
3. 文档正确区分模型手工 scratch、既有测试框架临时文件及控制器 fixture；不从默认 TemporaryDirectory 推断旧运行的实际目录，也不为覆盖声明改批准测试。清理保证限定正常退出或 Python 异常，不承诺 SIGKILL、断电后的自动清理。
4. 本次只给 Python 示例，并要求无 Python 时使用平台等价解析；没有新增运行依赖或声称验证了所有 PowerShell／无 Python 环境。测试作用是验证例程，不验证模型自动选择使用它。

## 构建与离线核查

- 新引用在 `transform(enhanced=True)` 的现有每个 Skill 资源附加阶段集中复制，字节直接来自 overlays，mode 为 0644；共享源未手工改 dist。现有 `--identity-only` 路线保持不加入融合工作流。
- 独立执行内存中的 `read_upstream()` → `transform()` → `distributions(compiled=False)`：固定上游提交 `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7` 的归档和清单校验通过；15 个平台共 87 个引用此例程的 SKILL／GUIDE 入口，其相对链接全部能在对应包内解析，均与两份 overlay 原字节及 0644 一致。该过程未写 dist、未编译 OpenCode、未安装、未运行容器或模型。
- 按平台入口计数：Codex 6、Claude 6、Pi 1、OpenCode 6、Hermes 6、Cursor 6、Gemini 6、Copilot 6、Mastra 7、Kiro 5、Continue 7、Factory 6、CodeBuddy 6、Agents 7、DSH 6。计数只表示含新增引用的入口；不声称每平台所有入口或所有语言主入口完全同构（例如 Kiro 保留原 Power 差异）。
- 只读检查 `tests/test_local_operations.py`：提取实际发布文档代码块，覆盖双语代码相等、多层相对目录链接、中文／空格路径、CRLF Skill、缺失／错误文件名失败、正常／异常 scratch 清理以及用户文件字节保护。主 Agent 正执行这些示例测试，本次没有重复运行，也不把源码测试意图写成执行 Passed。

## 验收限制与后续观察

静态语义及上述内存分发核查 Passed。模型行为、准确 RC14／stable npm 包、新会话自动匹配、Windows／macOS 等价例程本审查 Not Run。后续固定模型／任务应分别保留：Skill 实际读入及先后顺序；采用分支实际来源；选定计划与真实初始化；手工 scratch 实際目录；最终错误／历史事实／旧状态入口的实际读回。若仍失败须保留失败及绑定具体差异，不能无变化重试挑选成功。原有 owner 收尾失败没有被本次例程自动消除。

## 审查时源码 SHA-256

- `overlays/planweft/entrypoints/ar.md`: `78df7fe3b9653c5cc399bceddc335d02ea903e48d2cbc78e3956ef48f7695714`

- `overlays/planweft/entrypoints/de.md`: `496cf5b7ebe0a0c50d1497865b7d265ccc27037e171101f8c29f07364c218c09`

- `overlays/planweft/entrypoints/en.md`: `7e072195e539a09391ef1f1e6ea15d626a0fc134320236701c3c47c823285991`

- `overlays/planweft/entrypoints/es.md`: `41d83e6d9fe6588de11789c523ab1074fa59d0da228426ad585e39d0d6686e7d`

- `overlays/planweft/entrypoints/zh.md`: `ca799becc67c81adca694f51c4c054366574729c074259f1de2046989322eb7b`

- `overlays/planweft/entrypoints/zht.md`: `f8f46350f88efc58105f6555733dc79ba3f27c44898e8fe16f153dd005b974bd`

- `overlays/planweft/references/local-operations.md`: `7a34cf5f97dc56ce29c74f7c100ee42b6243977f896fc377480166bf8446e734`

- `overlays/planweft/references/local-operations.zh.md`: `a87fa68fd8e4ca8c993210694d2a5ee7c641d474bc2cdeabdfb88e36bb51cf5a`

- `scripts/build-plugin.py`: `918eae073358f142e7960f1860f3e73a3665f249cfa9d274b6e8aa83e098c309`

- `tests/test_local_operations.py`: `b20c3c879d51838db5685b5d98a2c289386032caf2cfc028e7c5bd1c13647e59`

## 后续来源注释与版本绑定补充

主 Agent 在两份 local-operations 末尾添加 Python 官方 Path.resolve／TemporaryDirectory 依据链接，明确这些只说明链接与生命周期语义，不证明授权或模型遵循；代码例程未变。builder 仅版本进至 0.4.0-rc.14，不改变此前复制两引用的逻辑。此次只核对本地 diff 与新增说明，不将链接再次浏览或模型执行算作已做。此前语义结论及验证限制不变。

- `overlays/planweft/references/local-operations.md` 当前 SHA-256 `87bae340e7c33931bc2170b47dbe7e6cc74de24850f2f63ca2a476c6751ba131`

- `overlays/planweft/references/local-operations.zh.md` 当前 SHA-256 `34530e9e5d9095190054b7b00e643df9d7f38d488f81a6d2a3248b3cfe2835a5`

- `scripts/build-plugin.py` 当前 SHA-256 `ceca2ba68a04f564d428af6a4062ea9075e0d2379f066048de7ffcfe9294a32a`
