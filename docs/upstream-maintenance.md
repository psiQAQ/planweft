# 固定上游、扩展与原生分发维护

Program Design 0.3.0 继续固定 PWF v3.17.0、提交 `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`。来源快照、扩展与确定性生成沿用 [ADR-0006](adr/0006-pwf-derived-runtime.md)；目录分发和原生更新渠道见 [ADR-0007](adr/0007-native-distributions.md)。研究子模块仍保留 3.16.1 历史版本，普通构建不读取研究子模块、个人缓存或网络。

## 维护入口

| 入口 | 职责 | 修改边界 |
| --- | --- | --- |
| `vendor/planning-with-files/upstream.json` | 仓库、tag、commit、tree、archive、摘要与许可 | 导入器生成；版本号不能代替提交及摘要验证 |
| `vendor/planning-with-files/v3.17.0.tar.gz`、`inventory.json`、`LICENSE` | 原始归档、逐文件 SHA/size/mode、MIT 许可 | 不直接修补 archive；更新来源需干净固定 checkout |
| `overlays/program-design/` | 共享产品文案、规则、模板、安装说明 | 修改生成源，不分别编辑平台副本 |
| `overlays/program-design/native/` | 宿主原生 manifest、hooks、资产路径适配 | 原生包装变更须与官方协议及真实加载验证对应 |
| `overlays/program-design/opencode-compiled/` | 与 source hash 绑定的预编译 V1 文件 | 使用编译脚本更新，不手改 JS 或摘要 |
| [PATCHES.md](../overlays/program-design/PATCHES.md) | 运行时补丁与对应上游位置 | 与 builder 中实际变更保持一致 |
| [import-pwf.py](../scripts/import-pwf.py) | 从已有固定 checkout 导入 | 不下载；检查 HEAD、tag、clean status 和许可 |
| [build-plugin.py](../scripts/build-plugin.py) | 身份映射、运行时补丁、14 个目录及六种 catalog | Python 标准库，正常构建不编译、不联网 |
| [compile-opencode.py](../scripts/compile-opencode.py) | 维护者预编译与复验 | 使用临时目录和已有锁文件；不改业务项目依赖 |
| [prepare-native-release.py](../scripts/prepare-native-release.py) | npm 包与 Git 发布树的本地准备 | 不 push、npm publish 或写个人宿主配置 |
| `dist/`、`plugins/program-design/`、六个原生 catalog | 目录分发、manifest、Codex 兼容镜像、发现入口 | 生成物；每次源变化重建并 verify |

每个分发保留上游 MIT 的 `Copyright (c) 2026 Ahmad Adi`、许可全文及 `UPSTREAM.json`。本地 metadata 不把上游作者、仓库或版本当作 Program Design 发布身份；原 URL 是来源证据，不能字符串替换成不存在的安装地址。

## 重建与回归

以下命令从仓库根执行。常规 overlay 修改不需重新导入上游：

```bash
git status --short
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
```

只有明确升级/重建来源时，才从已取得的干净固定 checkout 执行 `python3 scripts/import-pwf.py /path/to/clean-pwf-v3.17.0`。OpenCode 源码变化时，先更新预编译文件，再普通构建：

```bash
python3 scripts/compile-opencode.py --install
python3 scripts/compile-opencode.py --check --install
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
```

编译器在临时目录按锁文件准备依赖；普通 build 检查 source hash，拒绝使用过期中间产物。OpenCode 用户得到预编译 V1 包；本地安装只在独立插件目录安装锁定运行依赖，npm 安装由宿主包管理器处理，不要求用户重新编译 TypeScript。

`--verify` 检查当前输入与生成文件、额外文件和执行位，不代表宿主已加载或 hooks 已可信。builder 只维护声明的生成目标并清除其旧文件；不得把用户资料放入 `dist`、Codex 镜像或把目标改成业务项目配置。构建中断后重新执行构建与 verify，未通过前不交付。

完整回归开发树继续用新目录：

```bash
python3 scripts/build-plugin.py --tree /tmp/program-design-regression-new
python3 scripts/build-plugin.py --tree /tmp/program-design-identity-new --identity-only
```

`--tree` 不是发布包，不能与 `--verify` 混用，目标已存在时拒绝。`--identity-only` 仍含适配器禁用、内联 Python 隔离及 doctor 补丁，不等于未修改原始基线；原始基线从固定 archive 单独解压。测试入口、运行依赖和不同验证层见 [tests/README.md](../tests/README.md)。

`.gitattributes` 约束普通文本 LF，并让 Windows `.cmd`/`.bat` 保留原始 CRLF；不要手改生成 launcher 消除换行提示。复制目录保留隐藏文件及执行位。对 shell 权限、中文空格路径和 Windows launcher 的通过声明须有实际环境证据。

## 准备原生发布

普通 build 直接生成 `dist/<host>/program-design/`，不产出 ZIP。六种 catalog 位于仓库根，统一名 `program-design`，指向相应平台目录；Git marketplace 必须发布 catalog 和被引用 payload。Codex 的 `plugins/program-design/` 保持兼容镜像。

```bash
# 仅准备本地候选，不提供或假设远端身份
python3 scripts/prepare-native-release.py --output /tmp/program-design-release-new

# 下一候选承接先前生成的 Git 分支历史
python3 scripts/prepare-native-release.py --output /tmp/program-design-release-next \
  --previous-release /tmp/program-design-release-new
```

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--output` | 必填 | 仓库外尚不存在的输出目录，避免覆盖已有发布或递归打包 |
| `--previous-release` | 不提供 | 读取先前准备输出，沿用发布分支历史，后续发布可正常快进 |
| `--repository-url` | 不提供 | 真实 Git 仓库 URL；与 npm scope 成对提供，不自动设置 remote |
| `--npm-scope` | 不提供 | 真实 npm scope；与仓库 URL 成对提供，生成 `@scope/program-design-pi` 和 `@scope/program-design-opencode` |

准备器校验真实 npm tar 内容，跳过包生命周期脚本，产出来源与内容清单。没有真实身份时仍可本地审阅/安装，不输出已存在的远端地址或可直接公开安装结论。即使提供身份，也只是待发布坐标，必须在获得发布授权并实际发布后再次核验。

Gemini 的 `release/gemini` 与 Hermes 的 `release/hermes` 分支树把单个 host 包置于根。后续候选使用 `--previous-release` 承接历史，不依赖强推。Gemini 原生 `--ref release/gemini` 支持显式 update 跟踪分支；Hermes 插件使用该发布树完整 40 位 SHA，升级需要显式新 pin。Hermes Skill 没有等价 `--ref`，从同 SHA checkout 复制完整 Skill，发布/安装记录须保留 plugin 与 Skill 的配对。

Pi 原生 npm 更新依赖已发布包，OpenCode 配置使用已发布预编译包的明确版本。Cursor/Kiro 的市场管理和安装部分使用原生 UI，不能以有 catalog 为由声称 CLI 已提供相同命令。Continue、Mastra 和 generic Skills 采用手工或固定 checkout 更新；不新增统一服务。

## 升级与验证

1. 明确选择新产品版本或候选上游版本；检查官方宿主 API、安装/更新语义和许可变化，不自动追踪上游主分支。上游升级需要新的原始回归基线，不修改历史研究 gitlink。
2. 在生成源更新版本与适配。Claude/CodeBuddy 等缓存依赖 plugin version，应每次发行递增；只移动 Git ref 或只刷新 catalog 不保证已装插件刷新。
3. 重建目录、catalog 和需要变化的预编译输入，检查 manifest、npm `files`、引用路径与来源许可。Git 发布树和 npm 包作为真实安装输入检查，不能只检查源 package.json。
4. 在隔离来源、宿主配置和项目目录中验证 A 安装 → B 更新（新增、改动、删除文件）→ 回滚 A → 卸载。分别记录 catalog、缓存内容、当前会话、Skill 读取、hook 信任/执行，并确认项目计划与无关配置未改动。
5. Windows、GUI、账号或宿主不可得时标记 Not Run；协议或目录测试通过不能代替真实宿主结果。0.2.0 [REP-0005](reproduction/0005-pwf-based-plugin.md) 保持历史原样，0.3.0 新链路另记证据。
6. 实质设计交独立依据 review，再按已授权范围交付。推送、公开市场上架、npm publish 和用户全局安装不由构建脚本隐式执行。

## 旧安装迁移与恢复

0.2.0 用户先记录宿主列表里的实际 ID、scope、安装路径和本地修改，选择本会话唯一一套规划 hooks。新版本直接使用目录与原生来源，旧解压目录不会自动转成可更新安装。

Codex 旧 ID 可能是 `program-design@personal` 或 `program-design@program-design-local`。移除实际旧 ID，向仓库根注册新 `program-design` catalog，再安装 `program-design@program-design` 并新建会话；不同时保留旧来源执行 hooks。旧 catalog 无其他使用者时再清理。其余宿主按 [安装说明](../overlays/program-design/install/INSTALL.md) 保持 scope，先保存修改，再替换本插件拥有的完整路径，避免旧文件残留。

0.1.0 是单 Skill 和显式项目启用，后继版本引入 PWF 三文件与宿主生命周期；升级不会批准新任务或删除项目规则的启用条件。已有长期 Markdown 不批量转换；实际采用工作流时才承接目标、下一步、阻塞和证据，将旧活跃入口改成单向指针，保留历史。项目明确要求保留旧计划权威时遵守；本仓自身不因插件更新迁移到根 PWF 计划。

保留 `PLAN_ID`、`PWF_*`、`PLANNING_DISABLED`、三文件、`.planning`、attestation、ledger 格式；Kiro 的独立布局按平台说明处理。没有通用状态迁移器。更新失败时恢复前一份完整包或重建旧提交，按原 scope 安装/加载并重新检查 trust；包回滚不自动回滚任务期间修改的项目资料。
