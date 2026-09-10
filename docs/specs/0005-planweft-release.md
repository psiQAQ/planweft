# SPEC-0005：PlanWeft 单包与公开发布

目标版本 0.4.0。历史 RC 保留；正式版直接冻结唯一准确归档，先发布到 `next`，远端验收后再把同一不可变版本提升到 `latest`。

产品身份 planweft，主 Skill project-docs，命令 pw-，OpenCode 工具 pw_。
固定 PWF v3.17.0 与状态协议不变；历史文档、上游归属和现有计划不迁移。

唯一 npm 包同时提供 bin、Pi 显式资源和 OpenCode V1 exports；完整目录及运行依赖
必须随包携带。安装 CLI 支持 add/list/doctor/update/remove、agent、project/global、
skill-only、copy/symlink、dry-run。精确版本进入持久存储，不能依赖 npx 临时缓存。

受管理市场身份按 host/scope 区分；原生 scope 不支持时拒绝。全局市场注册与项目启用
分别记账。更新/卸载检查所有权及用户修改，重复加载拒绝，跨项目版本隔离。
每一步记录实际结果；部分成功不是安装成功。GUI 与 Hermes 扫描限制保持可见。

验收采用 `release/support-policy.json` 和 acceptance schema 3。五宿主准确产物、安装、升级、
回退、卸载、用户修改保护、重复注册检测、显式 Skill 读取、默认 advisory 与明确禁用均为
`required`；任一非 `Passed` 阻塞发布。Codex 显式维护到独立冷读为正式工作流基线。

Pi explicit/auto 维护与冷读分别按证据定级；其他宿主自动采用、五宿主 autonomous/gated
自动续跑和其余十个平台适配为实验性；实际模型上下文/恢复/stopping 也不替代正式控制契约。
离线 default advisory、明确禁用、cap 和 stall 回归为必需门禁。模型范围遵循
是公开评测，不是安全隔离保证；失败影响对应工作流定级，但仅在必需工作流中阻塞整个包。

结果使用 `Passed / Failed / Inconclusive / Not Run`，聚合状态由子场景计算，门禁根据策略
计算 `release_blocking`。复用证据必须绑定原包/目标包、逐文件 manifest 差异、受影响检查和
reviewer；准确产物、最终安装/卸载、用户文件保护和显式 Skill 读取不得复用。独立 review
在 prepublication/promotion 两阶段分别绑定策略摘要、最终包摘要及全部结果。promotion 的新会话
加载是无新模型调用的原生发现/加载探针。缺失认证与未执行的真实宿主检查保持 `Not Run` 并说明原因。

发布前审计拟公开历史和附件。公开 Git/npm 已获授权；个人全局安装和自身接管不在范围。
详细取舍见 ADR-0009；历史 reproduction/checkpoint 不因新策略回写为成功。
