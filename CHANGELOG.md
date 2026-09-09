[简体中文](CHANGELOG.md) | [English](CHANGELOG.en.md)

# 变更记录

## 0.4.0-rc.5（开发中）

- 修正 Codex 插件分发中 Stop、计划选择和 SessionStart 的资源路径；共享上游 standalone 布局保持原样。
- 新增独立复制包的 gated 正向、递归保护、上限、停滞、禁用与错误计划绑定回归。准确新候选包的真实宿主复验待完成。

## 0.4.0-rc.4

- 根 npm manifest 增加 main 与 ./server，指向现有 OpenCode V1 预编译入口，修复原生 npm 解析静默跳过插件的问题。
- 保留 RC3 的原生 npm 失败；修复需要新的准确包和远端验证，不覆盖已发布版本。

## 0.4.0-rc.3

- DSH hook 改用沙箱允许的私有临时快照，绑定宿主会话并在进程内按轮去重提醒，保留原生权限和 Stop payload。
- 无计划的 DSH 实施任务收到与 OpenCode 相同的条件式 Skill 提醒；损坏状态与显式绑定保持拒绝行为。
- RC2 已通过 GitHub OIDC 发布，远端归档完全一致，OpenCode 维护验收通过；DSH 原模型失败保留，待新准确包复验。

## 0.4.0-rc.2

- OpenCode 无计划时提醒已授权复杂任务读取 project-docs，简单及只读任务不初始化记录。

- 修正 DSH profile bundle 的入口定位，并将真实启动纳入验收。
- OpenCode 允许为同版本 npm 插件独立配对 Skill，继续拒绝重复 runtime 和版本冲突。
- 五宿主容器、准确归档门槛、公开历史脱敏与三系统安装器 CI；稳定版须五平台全部通过。
- RC1 已公开；其模型失败与注册成功不能证明实际加载的限制保留在验证记录中。

## 0.4.0-rc.1（2026-09-08，候选版）

- 更名 PlanWeft；保留 project-docs 与 PWF 状态协议。
- 单 npm 包、15 平台目录、六种市场入口。
- 新增显式范围安装器、精确版本、链接/复制、用户修改保护和生命周期记录。
- 稳定版由四核心平台真实验收把关。历史 0.3.0 证据不替代本次验证。

- 新增 DeepSeek Harness 原生 profile bundle、官方 hook 桥接与 Skill-only 安装；独立验证 Linux 原生生命周期。
