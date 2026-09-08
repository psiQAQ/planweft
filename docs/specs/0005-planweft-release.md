# SPEC-0005：PlanWeft 单包与公开发布

目标版本 0.4.0；先生成 0.4.0-rc.1，稳定版必须通过四核心宿主验收。

产品身份 planweft，主 Skill project-docs，命令 pw-，OpenCode 工具 pw_。
固定 PWF v3.17.0 与状态协议不变；历史文档、上游归属和现有计划不迁移。

唯一 npm 包同时提供 bin、Pi 显式资源和 OpenCode V1 exports；完整目录及运行依赖
必须随包携带。安装 CLI 支持 add/list/doctor/update/remove、agent、project/global、
skill-only、copy/symlink、dry-run。精确版本进入持久存储，不能依赖 npx 临时缓存。

受管理市场身份按 host/scope 区分；原生 scope 不支持时拒绝。全局市场注册与项目启用
分别记账。更新/卸载检查所有权及用户修改，重复加载拒绝，跨项目版本隔离。
每一步记录实际结果；部分成功不是安装成功。GUI 与 Hermes 扫描限制保持可见。

验收：构建一致、实际 npm 全量清单、两版本增改删/回退/卸载、两项目隔离、失败恢复、
中文空格路径和三 OS 安装器检查。Codex/Claude/Pi/OpenCode 在隔离 Linux 环境完成
真实生命周期和模型维护/冷读。缺失认证与非 Linux 真实宿主标 Not Run。

发布前审计拟公开历史和附件。公开 Git/npm 已获授权；个人全局安装和自身接管不在范围。
