# 固定上游、扩展和生成分发的维护

Program Design 0.2.0 固定使用 PWF v3.17.0、提交 `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`。当前结构为不可变来源快照、本地扩展和确定性生成分发，设计见 [ADR-0006](adr/0006-pwf-derived-runtime.md)。研究子模块仍保留 3.16.1 的历史版本，构建不读取研究子模块、个人插件缓存或网络。

## 来源与维护入口

| 入口 | 职责 | 维护规则 |
| --- | --- | --- |
| `vendor/planning-with-files/upstream.json` | 仓库、tag、提交、tree、archive、摘要、文件数及许可 | 由导入器生成；版本字段不能代替提交与摘要验证 |
| `vendor/planning-with-files/v3.17.0.tar.gz`、`inventory.json`、`LICENSE` | 原始 `git archive`、逐文件 SHA/size/mode、完整 MIT 许可 | 不直接修补 archive；导入器要求干净且匹配固定版本的 checkout |
| `overlays/program-design/` | 本地工作流、证据说明、模板增量及安装说明 | 只在这里修改共享产品文案，不分别编辑各平台副本 |
| [本地补丁清单](../overlays/program-design/PATCHES.md) | 运行时补丁、测试适配及对应来源位置 | 补丁在 builder 中应用，原始归档保持不变 |
| [scripts/import-pwf.py](../scripts/import-pwf.py) | 从已有 Git checkout 导入固定源码 | 不下载；核验 HEAD、tag 解析、clean status，生成 archive/inventory/source metadata |
| [scripts/build-plugin.py](../scripts/build-plugin.py) | 读取固定快照、身份映射、附加扩展、平台裁剪和 ZIP | 不运行上游脚本；生成根 `plugins/program-design` 与 `dist`，可独立输出带测试的移植树 |
| `plugins/program-design`、`dist` | Codex 自包含目录及 14 个平台 ZIP/manifest | 生成物；改变输入后重建，以 `--verify` 检查漂移 |

上游 MIT 的 `Copyright (c) 2026 Ahmad Adi` 与许可正文在每份分发保留；`UPSTREAM.json` 记录原始来源及本地变更类别。派生产品的 manifest/marketplace/package metadata 不能把上游作者、仓库或原版本描述为本地发布者。源码引用保留原 URL，是来源证据，不是本插件安装或支持地址。

## 重建与回归

以下命令从本仓库根执行。Python 3 标准库足以导入和生成；真实运行时及 TypeScript 回归依赖按各自锁文件另行准备。

```bash
# 1. 检查分支、用户改动和当前来源
git status --short
cat vendor/planning-with-files/upstream.json

# 2. 从已经取得的干净固定版本 checkout 重建来源；常规改 overlay 不需重导入
python3 scripts/import-pwf.py /path/to/clean-pwf-v3.17.0

# 3. 重建 Codex 目录与全部平台包
python3 scripts/build-plugin.py

# 4. 只比较生成内容与执行位，不改文件
python3 scripts/build-plugin.py --verify
```

`--verify` 成功表示当前生成物与当前输入一致，不代表宿主能加载、hooks 已可信或任务行为正确。builder 写入自己拥有的输出目录，并会删除这些目录内不属于当前生成集合的文件；所以不得把用户资料放入 `dist` 或 `plugins/program-design`，也不能将输出根指向业务项目配置。

仓库`.gitattributes`固定普通文本为LF，并让Windows `.cmd`/`.bat`保留归档原始CRLF；不要通过编辑生成launcher消除Git对CR的误报。平台隐藏目录在对应ZIP内，完整开发树可用下方`--tree`检查；正常安装无需将其再次展开到本源码仓库根。上游安装命令不能只做品牌字符串替换：本地衍生包尚未发布到上游账号或npm，相关说明由PD-P09映射为真实本地路径。

回归用新的、尚不存在的目录，避免把测试生成物写回原始 archive 或正式分发：

```bash
# 全量移植树，包含上游测试和本地工作流/模板增量
python3 scripts/build-plugin.py --tree /tmp/program-design-regression-new

# 保留身份映射及运行时补丁，排除工作流/模板增量
python3 scripts/build-plugin.py --tree /tmp/program-design-identity-new --identity-only
```

`--tree` 不能与 `--verify` 混用，目标已存在时拒绝；`--identity-only` 只能搭配 `--tree`。原始基线另从 vendor archive 解压到独立副本，再按上游自身测试入口运行。Python 使用隔离环境；Pi/OpenCode 在各自包目录按 package-lock.json 安装 TypeScript/Vitest 依赖。测试、命令与已知基线失败的实际记录统一放 [REP-0005](reproduction/0005-pwf-based-plugin.md)，不通过排除新增失败来制造全绿结果。

`--identity-only` 是诊断输出，不是发布包；其名称不表示绝对只改字符串：它仍应用适配器禁用、内联 Python 隔离及 doctor 补丁，且不补齐 standalone 资产。要运行未经修改的原始基线，使用 [测试入口](../tests/README.md) 的 `baseline` 模式。

## 升级上游的步骤

1. 在新分支检查候选 release 的 tag、提交、许可、宿主 API、脚本行为和测试变化；更新规格/ADR 的实际差异。版本必须是一次明确选择，不改为自动追踪 `master`。
2. 更新导入器的允许版本，导入干净固定 checkout，保留旧版本来源可由 Git 恢复；不要为了同步运行时去更新历史研究 gitlink。
3. 先跑候选原始测试建立基线，再应用本地身份映射和补丁；补丁记录问题、对应上游文件、实际原因与回归证据。共享修复留在生成源中，不散落到平台输出。
4. 生成全部包，运行一致性及自包含检查；逐包核查 identity、语言入口、fallback、许可和安装资产。npm `files` allowlist、Windows 编码命令中的路径和原生命令注册必须一起检查。
5. 在可得环境执行协议与真实宿主验证，检查安装、实际 Skill 读取、hook trust/注入、恢复、停止和卸载；无法取得的宿主/OS 如实 Not Run。完成一次真实文档维护与无旧聊天冷读，独立审查实质设计来源。
6. 填写验证矩阵与升级说明，再交付安装包。公开发布、推送和用户全局安装独立处理，不是构建脚本的副作用。

## 兼容与恢复

### 从 Program Design 0.1.0 升级

0.1.0是单Skill、项目显式启用、无执行hooks；0.2.0变为任务自动匹配、PWF三文件与平台原生hooks。版本升级不会替用户批准新任务，也不会删除或改写现有项目规则中的启用条件。

1. 记录当前宿主安装ID和路径，保存本插件目录的本地修改。检查是否同时安装原版PWF，选定本会话唯一一套规划执行hooks；不自动卸载其他插件。
2. 取得对应平台0.2.0包并核对manifest摘要，再按[平台安装说明](platforms.md)替换本插件。Codex旧版若来自本仓`personal` catalog，可在确认当前ID后执行 `codex plugin remove program-design@personal`，再从已更新到0.2.0的同一注册仓库执行 `codex plugin add program-design@personal`；若改用独立ZIP，则按`program-design-local`路线注册安装。不要同时保留两个来源的同名执行hooks。
3. 重新加载宿主；检查`project-docs`及`pd-`辅助操作。Codex新hook定义须单独审查/信任，安装成功不代表已经注入。需要严格只读试用时，在启动会话前设置`PLANNING_DISABLED=1`。
4. 首个复杂且已授权的维护任务按新Skill采用PWF。已有长期Markdown不批量转换；先把本任务目标、下一步、阻塞和证据承接到所选计划，再一次性将旧活跃状态入口改成指针，保留历史。项目/用户明确要求保留旧计划权威时遵守该例外；本仓自身不在本轮迁移。

0.1.0没有PWF状态引擎，因此不存在需要升级的0.1.0专有状态数据库。曾另外使用PWF的项目继续遵循其已有变量和文件协议，不因换产品身份自动改变mode、重新批准需求或重建attestation。

保留 `PLAN_ID`、`PWF_*`、`PLANNING_DISABLED` 及三文件、`.planning`、attestation、ledger 等原始状态格式；没有通用状态迁移器。原生适配能力不同，Kiro 等独立布局见[平台安装说明](platforms.md)。用户项目只有实际采用新流程时才转移活跃状态入口，历史记录不改写，不建立双向同步。

更新失败时停止使用新包，恢复前一份经验证的安装目录或重新构建旧提交的输出，再按宿主方式重新加载；不要撤销本轮以外的用户修改。若 hook 定义恢复或变化，遵循宿主 trust 规则重新检查。回滚安装包不能自动回滚任务期间生成的项目文档，三文件与长期文档需按实际任务差异分别判断。

当前构建写文件不是跨两个输出目录的原子事务：中断后应重新执行构建和 `--verify`，未通过前不交付。没有额外后台更新服务、包管理器发布或自动删计划机制；这使来源和交付边界可检查，也要求维护者保存真实验证状态。
