# PLAN-0008：PlanWeft 0.4.0

状态：实现和本地验证完成，候选发布进行中；本仓继续使用既有 plans，不采用根三文件。

1. 身份与目录：完成。旧产物检查字节和执行位；保留修改冲突；14 平台及六市场。
2. 单 npm 与安装器：完成。精确版本、原生范围、安装记录、失败恢复、所有权保护。
3. 生命周期、发布工具及独立审查：本地完成；四核心原生生命周期 Passed；Codex 模型与冷读 Passed。
4. 中英文文档、证据：完成，见 REP-0008；四批提交已合并本地 master@165b061。
5. Git/npm 候选发布、远端验收、稳定提升：进行中。npm 登录已成功；公开 Git 仓库已创建但尚未推送。

下一步：npm 首次发布要求额外浏览器认证，当前发布进程等待认证；随后校验远端字节与实际安装。完成历史隐私处理后推送。

干净源码 master@165b061 已准备候选 tarball（4,730,676 字节），SHA-256 `fd1f7e0f67b6ee623275c6396da250a6bab18f9467c5aa1b1401097efd151949`。此摘要对应已准备的 rc.1 包，后续验收脚本与状态文档提交不改变该归档。

门槛：0.4.0 不得跳过 Codex/Claude/Pi/OpenCode 真实模型验收。后三宿主尚缺认证，Not Run。
Windows/macOS CI、默认交互 trust 确认、远端多版本生命周期、npm trusted publisher 尚未完成。
8 个历史证据附件含本机路径或 owner/group；历史重写需用户对具体方案确认，尚未擅自改写。

依据与证据：[REP-0008](../reproduction/0008-planweft-candidate.md)、[REV-0008](../reviews/0008-installer-and-release-review.md)。

新增范围：用户要求 DSH；原 npm 发布认证等待已取消，以免先发布缺少新增平台的旧包。后续使用 PLAN-0009 完成 DSH 后重新构建，原 rc.1 tarball 仅为历史候选，不能作为新分发。
