# Program Design

研究并构建面向 Agent 的本地项目文档管理工具：让长期知识、当前任务、设计依据和验证结果能够被持续维护，并供新会话和人类读者使用。

当前处于**参考资料与设计基础阶段**，交付的是中文参考库、固定版本的参考项目和普通 Markdown 工作流程。CLI、Skills、hooks、自主管理能力均尚未实现。

## 从哪里开始

| 需求 | 入口 |
| --- | --- |
| 理解产品目标与当前范围 | [产品规格](docs/specs/0001-document-management.md) |
| 接续本阶段工作 | [实施计划](docs/plans/0001-reference-foundation.md) |
| 阅读文章与参考实现 | [资料索引](docs/reference/README.md) |
| 核查某个文件为什么这样设计 | [引用台账](docs/design-references.md) |
| 查看未被先例覆盖的想法 | [创新记录](docs/innovations.md) |
| 了解开发和审查方式 | [开发约定](docs/development.md) |
| 查看实际验证及限制 | [验证记录](docs/reproduction/0001-reference-foundation.md) |

## 获取参考项目

在本仓库根目录执行以下命令，按仓库提交记录中的 gitlink 恢复参考项目：

```bash
git submodule update --init
git submodule status
```

参考项目放在 `.submodule/<owner>/<repo>`。默认仅初始化本仓库登记的一层参考项目，不递归安装它们自己的依赖，也不执行其中的脚本。更新参考版本时，单独审查新的 commit、许可和受影响的引用；不要将 `--remote` 更新当作恢复固定版本的方法。

现阶段文档可直接阅读，无需 Node.js、Python 或新依赖。未来工具方向为 TypeScript/Node.js、Codex 优先；Linux 和 Windows 的产品运行验证在工具实现阶段进行。

个人偏好见 [override 差异稿](profiles/personal/AGENTS.override.md)，使用前按其中说明与通用原则手工组合。

第三方资料的许可与全文翻译范围分别见资料索引；子模块保留其上游许可。本仓库尚未作公开发布。
