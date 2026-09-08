# PLAN-0007：项目介绍与双语公开文档

状态：Completed（文档与验证）；日期：2026-09-08。用户要求：README 以项目介绍为主，说明实现思想、同类方案比较、参考来源及原创部分；安装和跨平台设计独立成篇，对外文档中英对应并可切换；验证后合并本地 master。

## 范围和完成标准

- 首页 README.md / README.en.md：产品定位、工作流、借鉴与本地贡献、准确的能力限制；不堆放安装命令。
- 安装 docs/installation.md / installation.en.md：完整14平台安装、更新、回退、卸载；从 overlay 安装源生成，包内 INSTALL.md / INSTALL.en.md 同源。
- 跨平台设计 docs/platforms.md / platforms.en.md：构建/运行边界、宿主差异、更新来源和分层验证；引用安装指南，不重复教程。
- 随包 README/INSTALL 同时提供中英文；每份公开文档开头有双向链接，引用公开文档时同时提供中英入口。内部研究、规格、计划和原始证据保留中文/原文，链接标明语言。
- 只修改文档及必要生成/打包配置；固定PWF、版本0.3.0、运行时和状态协议不变。不发布、不push、不进行个人安装或正式自身接管。

## 工作与验证

- 主Agent：README中英、生成器/打包同步、验证和Git整合。
- bilingual_install：中英安装源和随包README。
- bilingual_platforms：中英跨平台设计。
- readme_positioning：固定来源核查及独立README归属/语言审查。

验证：中英导航与本地链接、命令块一致性、生成物漂移和独立复制、npm实物包含英文文档、OpenCode编译绑定、相关回归、运行文件相对上一提交的字节/执行位差异。文档变化不重复宣称0.3.0历史真实宿主结果为当前字节实测；没有运行的宿主检查明确说明。

Git 从干净 master ff9e6a4 开始，工作分支 docs/bilingual-project-overview。公开文档、生成配置、独立审查与54项测试已完成。运行文件相对基线未变，实际npm包包含双语文档；结果见 [REP-0007](../reproduction/0007-bilingual-public-docs.md)。无剩余内容修改待办。公开交付提交为 `7dbae89`，工程证据单独提交；Git交付采用两批提交后 fast-forward 合并本地 master，不push。合并验收以 master 包含工作分支、工作区干净及构建 `--verify` 为准。
