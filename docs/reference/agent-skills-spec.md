# Agent Skills 格式规范

R-19；作者：Agent Skills 维护者与贡献者。[规范原文](https://agentskills.io/specification)；[Markdown 源文](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx)。访问日期：2026-09-07。

范围：该规范页面正文完整中文译文；保留示例内容与参数，移除网页 Card/Note 展示标签。文档目录的 [独立 LICENSE](https://github.com/agentskills/agentskills/blob/main/docs/LICENSE) 为 [CC BY 4.0](licenses/agentskills-CC-BY-4.0.txt)，译文采用相同许可；代码目录许可另计。译者：本仓库维护者，AI 辅助。这是访问日规范的译文，不是本仓库已经实现的 Skill 能力。

## 原文译文

### 目录结构（Directory structure）

一个 skill 是一个目录，至少包含 `SKILL.md`：

```text
skill-name/
├── SKILL.md          # 必需：元数据与指令
├── scripts/          # 可选：可执行代码
├── references/       # 可选：文档
├── assets/           # 可选：模板、资源
└── ...               # 其他任何文件或目录
```

### `SKILL.md` 格式

`SKILL.md` 必须包含 YAML frontmatter，随后是 Markdown 正文。

#### Frontmatter

| 字段 | 必需 | 限制 |
| --- | --- | --- |
| `name` | 是 | 最多 64 个字符；仅小写字母、数字和连字符，不得以连字符开头或结尾 |
| `description` | 是 | 最多 1024 个字符，非空；说明 skill 做什么及何时使用 |
| `license` | 否 | 许可证名称或随附许可文件的引用 |
| `compatibility` | 否 | 最多 500 个字符；说明目标产品、系统包、网络等环境要求 |
| `metadata` | 否 | 任意附加元数据，字符串键到字符串值的映射 |
| `allowed-tools` | 否 | 用空格分隔的、预先批准可供 skill 使用的工具字符串；实验性字段 |

最小示例：

```markdown
---
name: skill-name
description: A description of what this skill does and when to use it.
---
```

含可选字段的示例：

```markdown
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---
```

#### `name` 字段

必需字段 `name`：

- 长度必须为 1～64 个字符。
- 只能包含 Unicode 小写字母数字字符（`a-z`、`0-9`）和连字符（`-`）。
- 不得以连字符开头或结尾。
- 不得包含连续连字符（`--`）。
- 必须与父目录名称相同。

有效示例：

```yaml
name: pdf-processing
```

```yaml
name: data-analysis
```

```yaml
name: code-review
```

无效示例：

```yaml
name: PDF-Processing  # 不允许大写
```

```yaml
name: -pdf  # 不得以连字符开头
```

```yaml
name: pdf--processing  # 不允许连续连字符
```

#### `description` 字段

必需字段 `description`：长度必须为 1～1024 个字符；应描述 skill 做什么及何时使用；应包含帮助 Agent 识别相关任务的具体关键词。

较好的示例：

```yaml
description: Extracts text and tables from PDF files, fills PDF forms, and merges multiple PDFs. Use when working with PDF documents or when the user mentions PDFs, forms, or document extraction.
```

较差的示例：

```yaml
description: Helps with PDFs.
```

#### `license` 字段

可选字段 `license` 指定 skill 采用的许可。建议简短填写许可证名称，或随附许可证文件的名称。

```yaml
license: Proprietary. LICENSE.txt has complete terms
```

#### `compatibility` 字段

可选字段 `compatibility` 在提供时必须为 1～500 个字符；仅当 skill 有特定环境要求时才应填写，可说明目标产品、必需系统包和网络要求等。

```yaml
compatibility: Designed for Claude Code (or similar products)
```

```yaml
compatibility: Requires git, docker, jq, and access to the internet
```

```yaml
compatibility: Requires Python 3.14+ and uv
```

大多数 skill 不需要此字段。

#### `metadata` 字段

可选字段 `metadata` 是字符串键到字符串值的映射，客户端可以用它保存规范未定义的附加属性。建议使键名具有足够的区分度，避免意外冲突。

```yaml
metadata:
  author: example-org
  version: "1.0"
```

#### `allowed-tools` 字段

可选字段 `allowed-tools` 是用空格分隔的预先批准可运行工具字符串。这是实验性字段，不同 Agent 实现的支持可能不同。

```yaml
allowed-tools: Bash(git:*) Bash(jq:*) Read
```

#### 正文（Body content）

Frontmatter 后的 Markdown 正文包含 skill 指令，没有格式限制；编写能帮助 Agent 有效完成任务的内容即可。建议包括逐步操作、输入输出示例和常见边界情况。

Agent 一旦决定激活 skill，就会加载整个文件。较长的 `SKILL.md` 可以拆入被引用的文件。

### 可选目录（Optional directories）

除必需的 `SKILL.md` 外，skill 目录可以包含任何文件和目录。以下约定是组织常见内容的建议。

#### `scripts/`

存放 Agent 可运行的代码。脚本应自包含或清楚说明依赖，提供有用错误信息，并妥善处理边界情况。支持的语言取决于 Agent 实现，常见选择包括 Python、Bash 和 JavaScript。

#### `references/`

存放按需读取的附加文档，例如：

- `REFERENCE.md`：详细技术参考。
- `FORMS.md`：表单模板或结构化数据格式。
- `finance.md`、`legal.md` 等领域文件。

每份参考文件应保持主题集中。Agent 按需加载这些文件，因此较小文件占用的上下文也较少；引用方法见下文“文件引用”。

#### `assets/`

存放静态资源：文档或配置模板、图示或示例图片，以及查找表或 schema 等数据文件。

### 渐进披露（Progressive disclosure）

Agent 逐步加载 skill，只在任务需要时读取更多细节。Skill 应据此组织：

1. **元数据（约 100 tokens）**：启动时加载所有 skill 的 `name` 和 `description`。
2. **指令（建议少于 5000 tokens）**：激活时加载完整 `SKILL.md` 正文。
3. **资源（按需）**：只在需要时读取 `scripts/`、`references/`、`assets/` 等文件。

主 `SKILL.md` 应保持在 500 行以内；详细参考内容放入独立文件。

### 文件引用（File references）

引用 skill 内其他文件时，使用相对于 skill 根目录的路径：

```markdown
See [the reference guide](references/REFERENCE.md) for details.

Run the extraction script:
scripts/extract.py
```

从 `SKILL.md` 出发保持一层文件引用，避免很深的嵌套引用链。

### 验证（Validation）

使用 [skills-ref 参考库](https://github.com/agentskills/agentskills/tree/main/skills-ref) 验证 skill：

```bash
skills-ref validate ./my-skill
```

这会检查 `SKILL.md` frontmatter 是否有效、是否遵守命名约定。

## 本仓库解读

以上是规范译文。`name` 对 Unicode 的表述和括号里的 ASCII 示例按原文保留，实际跨宿主兼容范围以后需单独验证。行数和 tokens 是上游组织建议，不转为本仓库对所有文档的硬门槛。工具授权与加载行为仍应核对具体宿主；本阶段没有安装 skills-ref 或创建产品 Skill。返回 [资料索引](README.md)。
