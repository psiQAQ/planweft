# ADR-0008：一个 npm 包及遵循原生能力的安装器

状态：接受；实现与验证见 PLAN-0008。

独立 Pi/OpenCode 包增加身份、配对和更新成本。采用唯一 planweft 包；保留嵌套平台目录，
根 pi 字段和 exports 指向各自入口，CLI bin 独立，避免 OpenCode 将其他导出误作插件。

借鉴 Vercel Skills 固定提交 1682051d48c34f5eb135e6475c1a965dce05e820 的
[installer](https://github.com/vercel-labs/skills/blob/1682051d48c34f5eb135e6475c1a965dce05e820/src/installer.ts)
和 [lock](https://github.com/vercel-labs/skills/blob/1682051d48c34f5eb135e6475c1a965dce05e820/src/skill-lock.ts)
的集中存储/链接思想，不依赖它安装完整插件。

本地扩展：CLI 管理市场按 host/scope 哈希命名；原生缓存与受管理资源分别处理；
插件与 Skill 配对状态、逐步失败和用户修改保护均进入安装记录。不同于共享单市场，
项目更新不能改变其他项目的精确版本。代价是多份市场登记、显式清理及部分失败恢复。

Node 根依赖实际携带 OpenCode runtime dependency；Pi optional peer 由真实宿主解析验证。
不绑定个人缓存，不绕过 hook 信任或 Hermes 扫描，不把 Skill-only 标为完整插件。
