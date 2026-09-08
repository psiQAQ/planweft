# Program Design 本地差异清单（0.2.0 基线与 0.3.0 增量）

基准为 PWF v3.17.0、`0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`。原始归档保持逐字节不变；下列差异由 `scripts/build-plugin.py` 和本目录生成，不能在平台副本单独修改。来源清单见 `vendor/planning-with-files/inventory.json`；文件路径列使用上游原路径或相同类别的全部副本。

| ID | 上游位置 | 本地变更及原因 | 回归入口 |
| --- | --- | --- | --- |
| PD-P01 | manifest、package.json/lock、commands、平台脚本和测试中的产品/Skill身份 | 产品 `program-design`、主 Skill `project-docs`、`pd-` 命令、`pd_` OpenCode tools；保留来源链接、`PWF_*`/`PLAN_ID`/磁盘协议。覆盖反斜杠、编码的 Windows launcher、原生注册及 fallback | 原始/迁移 pytest、Pi/OpenCode；本地身份与 Windows 命令解码契约 |
| PD-P02 | 各平台/语言 `SKILL.md`、普通/自主/analytics templates | 插入 `workflow.md` 与本地证据/显式控制；保留上游主体和特定平台能力披露。语言变体只显式加载，Codex 只保留一个自动主入口；模板追加不增加 parser phase/status/checkbox token | Skill/链接检查、模板解析对照、真实维护与冷读 |
| PD-P03 | `.gemini/hooks/*.sh`、`.mastracode/hooks.json` | 给缺少关闭入口的旧适配添加 `PLANNING_DISABLED=1` 早退，分别保留 `{}` 或空输出协议。没有实现自然语言只读识别或给旧适配增加 named-plan 能力 | 9 个实际 hook 命令关闭后无注入/项目写入；原始/迁移回归 |
| PD-P04 | 各平台 `hooks/*.sh` 中的内联 Python `-c`/stdin 片段 | 增加 `-I`，避免 JSON 序列化/协议处理意外导入 cwd 中的同名模块或 `PYTHONPATH` 内容；不对依赖包内 sibling imports 的脚本入口批量加隔离参数 | cwd 同名 `json.py` 可观察副作用测试；上游解释器隔离与适配回归 |
| PD-P05 | 所有 `scripts/plan-doctor.sh` | 附加 `doctor-overlap.sh`，只检查已知原 PWF 目录并告警；目录存在不证明 hooks 正在运行，不执行旧脚本、不卸载 | 旧目录内放置可观察脚本，确认仅诊断、不执行 |
| PD-P06 | 部分平台及语言 Skill 目录、Codex/Claude catalog、Pi/OpenCode `files` | standalone Skill 补齐 canonical scripts/templates/reference/examples 与本地证据，保留已有平台副本；每个独立复制边界携带 MIT/UPSTREAM；Codex ZIP 自带本地 catalog，包不依赖子模块或个人缓存 | 14 包清单/逐文件摘要/相对链接；真实 Codex 注册、缓存核对和卸载 |
| PD-P07 | `tests/test_hermes_first_class.py::test_shell_hook_bridge_translates_inject_and_gate` | 补齐 Hermes 资产后，无效显式路径仍可找到合法包内 fallback。迁移测试先确认这个行为，再将 bridge 复制到没有脚本的隔离位置保留原 silent-noop 断言；不改变运行时 fallback 语义 | 定向 Hermes 测试与完整迁移 pytest；首轮失败保留 |
| PD-P08 | Codex生成分发 `skills/i18n/*/agents/openai.yaml` | 真实CLI会递归发现5个语言变体；为其添加Codex原生 `policy.allow_implicit_invocation: false`，保留主入口为true。不能仅以Claude frontmatter的disable-model-invocation替代Codex策略 | 官方Skill元数据契约、实际skills/list、包内原生policy测试；enabled与implicit是不同字段 |
| PD-P09 | canonical/Agents/Pi/Hermes/OpenCode Skill安装说明、OpenCode包README和分发loader | 将上游发布式命令替换为衍生包的本地安装路线，禁止身份替换虚构GitHub/npm发布源；分发loader直接加载按锁文件构建的dist，完整迁移树保留src开发入口 | 全14包安装源扫描、各平台入口与资产检查；与既有验证包逐文件比较 |
| PD-P10 | `.gemini/settings.json` 的5条hook command | 为包含`$GEMINI_PROJECT_DIR`的完整路径加双引号，并显式使用Bash运行上游0664脚本，避免空格拆词及无执行位失败；不改变脚本或事件协议 | 修复前5事件退出127，仅加引号后5事件退出126；最终直接执行settings命令，禁用输出与项目/缓存不变检查 |

测试中的身份变化只对应实际新接口，不删除上游功能断言。PD-P07 是分发完整性改变引起的 fixture 适配，原始 baseline 仍执行未经修改的测试。本轮结果及失败处理以 `docs/reproduction/0005-pwf-based-plugin.md` 为准；这里登记设计，不预先宣称每层宿主测试通过。

## 0.3.0 追加差异

下面是 0.3.0 对 PD-P06/P09/P10 的后继；上表保留 0.2.0 的原始含义。固定源码不变，目录及本地编译产物由生成器维护。

| ID | 位置 | 变化及原因 | 验证 |
| --- | --- | --- | --- |
| PD-P11 | build-plugin.py、六 root catalog、dist | 目录替代 ZIP；逐文件内容/执行位、树摘要与镜像；只迁移 manifest 确认且摘要吻合的旧归档；保留其他根配置 | 确定性、漂移拒绝且无写入、用户备份保护、实际 Git CRLF blob |
| PD-P12 | native/adapters.py、native-hook.py | 原生 manifests；Cursor/Copilot/Gemini 按各自协议注入，不输出 Copilot allow；资产从安装目录解析，状态仍在项目；native-gate 验证点位于原 attestation 之后 | 三宿主脚本协议、篡改/禁用/去重/续跑边界；独立运行时审查 |
| PD-P13 | OpenCode core.ts、Hermes paths.py/shell_hook.py、Kiro Skill | 使用随包资产或明确 env override，删除隐含旧安装 fallback；Kiro 在加载 Skill 目录解析脚本；语言支持随单独复制 Skill 携带 | 独立复制、中文空格路径、OpenCode 真实 debug 工具/模板、资源契约 |
| PD-P14 | compile-opencode.py、opencode-compiled、prepare-native-release.py | 锁定 TypeScript 预编译 V1；记录编译输入/输出摘要；scoped npm 仅改包身份时记录第二阶段输入及逐字段转换；实际 npm 包包含安装说明与全部入口 | 编译重现、过期/篡改拒绝、npm 实物、发布 Git 父提交及增改删 |
| PD-P15 | native安装说明、包 README、平台矩阵 | 当前官方原生安装/显式更新/卸载；旧 Codex 身份迁移；不生成不存在的发布地址，不把 GUI/Skill 当完整 hooks 插件 | 独立依据 review 与隔离 CLI；Hermes 拒绝、GUI/远程/其他 OS 未运行分开报告 |

0.3.0 原始/移植完整回归与各宿主结果见 REP-0006；PD-P12/P13 属于原生分发层，不能仅凭 `--tree` 上游测试通过代替其协议及实际加载验证。
