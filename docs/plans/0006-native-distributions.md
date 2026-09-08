# PLAN-0006：原生目录分发与更新 0.3.0

状态：实现与验证完成；日期：2026-09-08。需求来源：用户批准的 Program Design 0.3.0 完整实施计划。

## 目标与边界

将 14 平台 ZIP 改成 `dist/<host>/program-design/`，生成六种原生 marketplace，交付原生安装、显式更新、回退及卸载说明与分层证据。PWF 仍固定 v3.17.0，主 Skill 和状态协议不变。Codex 旧目录保留生成镜像。

在独立分支 `feat/native-distributions-0.3.0` 从干净 `master`（`3197f81`）实施。允许临时隔离安装官方 CLI；不改个人全局环境，不 push、发布、改 remote 或正式自身接管。继续使用本计划作为唯一实施状态入口。

## 阶段与 owner

- [x] 构建目录、清单和 marketplace；主 Agent。
- [x] 原生 manifest、运行路径和必要 hook 协议修正；native_marketplaces，限定 overlays/native。
- [x] 安装、升级与设计文档；native_skill_hosts，限定安装与设计文档。
- [x] 目录及协议回归、smoke 迁移；delivery_review，限定测试。
- [x] 原生包、Git 发布树准备与隔离生命周期；主 Agent 整合。
- [x] 独立依据/交付审查与证据；Git 按下述边界分批整理。

## 验证与完成标准

确定性构建和漂移检查、14 目录与六 catalog 完整性、npm 实际包内容、相关上游对照回归。可得 CLI 在隔离目录验证 A→B（新增/修改/删除文件）→A→卸载，分别记录市场、安装缓存、实际会话加载和项目文件保护。GUI、认证限制及缺失 OS 实测记 Not Run，不继承旧版 Passed。

## 当前记录

- 工作区初始干净；本机 Codex 0.153.4。其他 CLI 按官方来源隔离准备，版本及命令记录到本轮 reproduction。
- Git 分支创建首次遇到 sandbox 的 `.git` 只读限制；按用户明确授权申请同一命令的提权，成功创建分支。
- 固定源码、平台改造、文档和回归分工已明确；所有生成物由主 Agent 统一构建。

本轮结果：

- 14 个目录、六种 catalog、Codex 镜像、预编译 OpenCode V1、Pi npm 包及 Gemini/Hermes 发布树准备已实现。
- 本地 52 tests、13 项入口契约、确定性/清单/编译验证通过。原始与迁移各 721 pytest + 63 skip；Pi 各 54，OpenCode 各 34 及 typecheck/build 通过。
- Codex、Claude、Pi、Gemini、OpenCode、Copilot、CodeBuddy、Factory 在临时配置中执行生命周期，实际文件/版本/卸载分别检查；Codex 真实合成响应探针验证 hooks 信任、送达、恢复、禁用。
- 独立审查发现的发布身份绑定、旧 ZIP 归属、Pi 安装说明、Kiro 缓存路径和语言资源遗漏已修复并复验。
- Hermes 默认扫描拒绝：初次 42、最终 41 findings，安装 Failed，后续 Not Run；没有绕过。GUI、Windows/macOS、公开远程渠道与新版模型维护/冷读 Not Run。
- 当前仓库继续使用 docs/plans，不创建 PWF 三文件，不变更历史入口或正式自身接管。

证据和后续验证边界见 [REP-0006](../reproduction/0006-native-distributions.md) 与两份独立 review。Git 整理边界：目录与原生适配、发布准备、生命周期测试、文档与证据分别提交，合并到本地 master；从干净提交生成本地发布准备目录。最终提交与合并状态以 Git 历史为准。本轮没有 push、公开发布或个人全局安装。后续工作仅为上述未测宿主/渠道的验证，不能将其预先标为通过。
