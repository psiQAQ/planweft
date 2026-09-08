# SPEC-0004：原生目录分发与持续更新

状态：Accepted；日期：2026-09-08；目标版本：0.3.0。用户已批准使用各宿主原生 Git marketplace、npm 与发布分支，默认显式更新；本轮不 push、不公开发布。Accepted 表示需求已确定，实际运行结果须单独记录。

## 目标与兼容边界

把 0.2.0 的 ZIP 安装源改为 `dist/<host>/program-design/` 自包含目录。保留固定 PWF v3.17.0 的运行时、产品身份和项目状态格式，补齐宿主认可的插件入口与来源注册。安装、更新、重新加载和 hooks 信任分别处理；不以统一 marketplace 文件冒充全部宿主协议。

本规格替代 SPEC-0003 的 ZIP 交付形状及相应安装步骤，不重写历史验证，不扩大运行时保障。`plugins/program-design/` 保留为 Codex 兼容镜像。项目三文件、`.planning`、attestation、ledger、长期文档和既有项目规则不由安装更新操作迁移或删除。

## 需求与验收

| ID | 要求 | 完成标准 |
| --- | --- | --- |
| PND-01 | 目录分发 | 统一生成 codex、claude、pi、opencode、hermes、cursor、gemini、copilot、mastracode、kiro、continue、factory、codebuddy、agents 共 14 个平台目录；默认构建不产出 ZIP |
| PND-02 | 确定性与自包含 | manifest 登记目录文件、摘要及执行位；`--verify` 只读检查缺失、额外文件、内容及执行位漂移；每包保留 LICENSE、UPSTREAM.json、安装说明和全部运行资产 |
| PND-03 | 原生目录发现 | Codex、Claude、Cursor、Copilot、Factory、CodeBuddy 各有原生 catalog；同一仓库中分别指向对应平台目录，统一 catalog `name` 元数据为 `program-design`；实际注册 ID 以宿主列表为准，不将另一宿主配置冒充原生支持 |
| PND-04 | 原生包入口 | Pi 使用 pi-package；OpenCode 使用预编译 V1 npm/local 包；Gemini 使用 Extension；Hermes 插件与 Skill 配套分发；Kiro 使用 skills-only Power；Continue、Mastra 和通用 Agent Skills 保留可用的文件安装表面 |
| PND-05 | 显式更新 | 每种渠道记录来源、版本、scope、更新及生效方法；catalog 刷新不能单独当作插件已更新；默认不替用户开启自动更新 |
| PND-06 | 发布准备与发布分离 | 离线准备 Git marketplace、Pi/OpenCode npm 包和 Gemini/Hermes 发布分支的内容；目标目录必须在仓库外且尚不存在；不 push、不发布 npm，不修改用户宿主配置；缺少真实仓库 URL 或 npm scope 时只说明本地可用 |
| PND-07 | 兼容已有安装 | Codex 镜像与新目录一致；记录旧 `personal`/`program-design-local` 安装 ID 迁移；其他手工安装只替换本插件文件，清理本插件旧文件，保留无关配置及项目记录 |
| PND-08 | 分层验证 | 覆盖目录漂移、catalog 到 payload、预编译包、自包含安装源、旧版到新版更新及卸载边界；可得宿主做隔离真实安装验证，其余明确 Not Run |

## 安装与发布接口

构建仍使用 `python3 scripts/build-plugin.py` 和 `--verify`；`--tree` 是回归开发树，不是平台安装包。发布准备入口为 `python3 scripts/prepare-native-release.py --output <new-directory>`，`--previous-release <directory>` 可承接上次输出的 Git 分支历史。可选 `--repository-url <URL>` 与 `--npm-scope <scope>` 必须成对提供，仅为待发布产物提供实际身份。准备目录不代表远端已存在；公开地址和 npm 包必须在发布后另行核验。

Gemini 与 Hermes 的专用发布分支把对应安装根放在分支根目录，Gemini 满足其根 manifest 要求，Hermes 保留 `.git` 供原生 updater 使用；这是本仓发布策略，Hermes 的安装器本身支持子目录。Gemini 跟踪 `release/gemini` 分支；Hermes 的 Skill 安装不能假设支持 `--ref`，复现固定版本时从固定 checkout 复制完整 Skill，并与同一提交的插件配对。npm 包在维护者端完成构建，普通用户不为安装重新编译 TypeScript；OpenCode 本地复制路线在独立包中按锁文件安装运行依赖。

Factory、CodeBuddy 的最小原生包装只承诺安装、发现和更新 Skill，不顺带启用未验证的执行 hooks。Kiro 在 IDE 中安装及显式更新 Power，CLI v3 自动发现 IDE 安装；不虚构 CLI Power 管理命令。Continue 的 `/import-skill` 是模型辅助导入，不能当作来源可追踪的自动更新器。其他无原生更新器的表面保留明确的固定 checkout/手工更新步骤，不新建后台服务。

## 验证要求

旧版升级场景包含文件内容变化、版本变化及删除文件；验证目标安装内旧文件不再被加载。还须检查中文与空格路径、执行位、npm 打包文件清单、manifest 与来源版本配对，以及隔离安装后的实际 Skill 发现。新建或变化的 hook 定义保留宿主信任流程；只读与停止行为按继承运行时的实际能力验证。

证据区分构建 Passed、协议 Passed、真实宿主 Passed 与 Not Run。0.2.0 的 REP-0005 只证明当时的来源和运行时结果，不能为 0.3.0 安装链路背书。架构决定见 [ADR-0007](../adr/0007-native-distributions.md)，使用说明见 [平台矩阵](../platforms.md)。
