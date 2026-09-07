# MADR：用 Markdown 记录重要决定

R-17；作者：Oliver Kopp、Olaf Zimmermann 等 MADR 贡献者。官网：[About MADR](https://adr.github.io/madr/)。本译文采用 P-12 固定版本 `ba75bb1b20d42af5746b246ad348c202419ae681` 的 [docs/index.md](../../.submodule/adr/madr/docs/index.md) 和 [完整模板](../../.submodule/adr/madr/template/adr-template.md)，与官网所部署版本可能有差异。核对日期：2026-09-07。

范围：About MADR 正文完整中文翻译（含 News、例子、历史版本及模板展开）；网站导航、徽章和构建元数据不复制，站内相对链接改为上游对应链接。源码允许 MIT OR CC0-1.0，本译文选择 [CC0-1.0](licenses/madr-CC0-1.0.txt)。译者：本仓库维护者，AI 辅助。下面是参考材料，不是要求安装 npm 包或套用全部模板。

## 原文译文

Markdown Architectural Decision Records（MADR，读音 `[ˈmæɾɚ]`）：值得记录的重要决定。

架构决定（AD）是有理由支持的软件设计选择，用于回应具有架构重要性的功能或非功能需求。它由架构决策记录（ADR）保存，一份记录详细说明一个决定及其理由。MADR 是用结构化方式精简记录重要架构决定的模板。

相关论文：[Markdown Architectural Decision Records: Format and Tool Support](https://dblp.org/rec/conf/zeus/KoppAZ18.html)。

### 动态（源文件所列历史记录）

- 2024-09-17：[MADR 4.0.0 发布](https://github.com/adr/madr/releases/tag/4.0.0)，提供 bare 和 minimal 模板。
- 2024-09-02：[4.0.0-beta 发布](https://github.com/adr/madr/releases/tag/4.0.0-beta)。为了突出架构决策，将全名写为 Markdown Architectural Decision Records；仍能用于其他决定，但重点是架构。
- 2023-04-05：发表 [如何创建 ADR，以及不该怎样创建](https://medium.com/olzzio/how-to-create-architectural-decision-records-adrs-and-how-not-to-93b5b4b33080) 和 [如何审查 ADR，以及不该怎样审查](https://medium.com/olzzio/how-to-review-architectural-decision-records-adrs-and-how-not-to-2707652db196)，讨论隐喻、模式、反模式和检查清单，不限于 MADR。
- 2022-11-22：MADR 1.0 发布五周年，发表 [MADR 模板的解释与提炼](https://medium.com/olzzio/the-markdown-adr-madr-template-explained-and-distilled-b67603ec95bb)。
- 2022-10-09：3.0.0 发布，主要把 Positive Consequences 与 Negative Consequences 合并为 Consequences，使语法与备选方案的 Pros and Cons 更一致。[变更记录](https://github.com/adr/madr/blob/develop/CHANGELOG.md#300--2022-10-09)。
- 2022-05-17：3.0.0-beta 发布；除模板改进外，全名曾改为 Markdown Any Decision Records，以响应 [ADR 是否可以记录任何决定](https://ozimmer.ch/practices/2021/04/23/AnyDecisionRecords.html) 的讨论，缩写仍是 MADR。
- 2021-04-25：MADR 示例被用于 [从架构决定到设计决定](https://medium.com/olzzio/from-architectural-decisions-to-design-decisions-f05f6d57032b) 和 [ADR = Any Decision Record?](https://medium.com/olzzio/adr-any-decision-record-916d1b64b28d)。
- 2021-04-08：[Design Practice Repository](https://leanpub.com/dpr) 推荐 MADR；[在线活动说明](https://socadk.github.io/design-practice-repository/activities/DPR-ArchitecturalDecisionCapturing.html) 也讨论决策捕获。
- 2020-09-29：在 [DocGen2](https://dysdoc.github.io/docgen2/index.html) 的主题报告中介绍在开发者工作位置捕获决定，[幻灯片](https://speakerdeck.com/koppor/markdown-architecturaldecisionrecords-capturing-decisions-where-the-developer-is-working)。
- 2019-07-08：被 Olaf Zimmermann 的 [Architectural Decisions — The Making Of](https://ozimmer.ch/practices/2020/04/27/ArchitectureDecisionMaking.html) 引用；[Medium 短版](https://medium.com/@docsoc/y-statements-10eb07b5a177)。此处日期照源文件保留。
- 2018-04-13：被 [@vanto 的 ADR 演讲](https://speakerdeck.com/vanto/a-brief-introduction-to-architectural-decision-records) 提及。
- 2018-04-03：上述论文发表。

### 概述

架构决定是影响架构的功能或非功能需求对应的软件设计选择。例如 Java 与 JavaScript、IntelliJ 与 Eclipse IDE、SLF4J 与 java.util.logging，或无限撤销与有限撤销之间的取舍。不要过分狭义地理解“架构”；任何可能以某种方式影响架构的决定都可以属于此类。

写下决定和对决定做版本管理，都应尽可能容易。

哪些决定具有架构重要性仍有争论。我们认为重要决定都应结构化保存，因此提供 MADR 模板。本仓库用 Markdown 和 ADR 文件提供记录决定的方式。

### 例子

```markdown
# 使用普通 JUnit5 完成高级测试断言

## 背景与问题

如何编写可读的测试断言？如何为高级测试编写可读断言？

## 考虑的方案

* 普通 JUnit5
* Hamcrest
* AssertJ

## 决定

选择“普通 JUnit5”，因为它是标准框架，而其他框架的额外功能不足以抵消引入新依赖的代价。
```

更多内容见 [示例](https://adr.github.io/madr/examples.html) 和 MADR 自身的 [决定](https://adr.github.io/madr/decisions/)，[源码](https://github.com/adr/madr/tree/develop/docs/decisions)。最新版完整模板（含占位符与说明）见 [releases](https://github.com/adr/madr/releases/latest)。点击 tag 可查看该版本仓库；愿意尝试开发版可看 [开发模板](https://github.com/adr/madr/blob/develop/template/adr-template.md)。[CHANGELOG](https://github.com/adr/madr/blob/develop/CHANGELOG.md#changelog) 记录发布版与开发版的差异。

### 在项目中使用 MADR

#### 初始化

在项目创建 `docs/decisions`，将 MADR 的 [template 目录](https://github.com/adr/madr/tree/develop/template) 中的全部文件复制进去。原文给出的 npm 方法是：

```sh
npm install madr && mkdir -p docs/decisions && cp node_modules/madr/template/* docs/decisions/
```

#### 新建 ADR：手工方式

1. 把 `docs/decisions/adr-template.md` 复制为 `docs/decisions/NNNN-title-with-dashes.md`，NNNN 是下一个序号。
2. 编辑新文件。

也可使用其他 [文件命名约定](https://github.com/joelparkerhenderson/architecture-decision-record#file-name-conventions-for-adrs)，但现有工具可能因此不适用。

文件名遵循 `NNNN-title-with-dashes.md`：[ADR-0005](https://github.com/adr/madr/blob/develop/docs/decisions/0005-use-dashes-in-filenames.md)。NNNN 连续递增，假设单仓库不会超过 9,999 份 ADR；标题使用小写与连字符，与 adr-tools 一致；`.md` 表明 Markdown 文件。将决定放在 `decisions/`，既靠近其他文档又保持分离。

#### 新建 ADR：自动方式

源文件此处写明：当前没有支持 MADR 3.0.0 的工具。这是该固定版本中的历史文字，不作为 2026 年全部工具现状的调查结论。

#### 检查 ADR 格式

Markdown 允许多种风格，因此可能不一致。[markdownlint](https://github.com/DavidAnson/markdownlint#markdownlint) 用于提示这些问题。初始配置位于 `template/.markdownlint`，可用于 GitHub workflow；[示例 workflow](https://github.com/adr/madr/blob/develop/.github/workflows/lint.yaml)。

### 大型项目和产品开发中的 MADR

大型项目可能积累数百份记录，查找变得困难。MADR 不强制仓库或目录组织方式，下面是社区建议。

#### 分类

可以建立子目录，将记录按类别放入其中。例如按照系统架构：

```text
decisions/
  backend/
    0001-use-quarkus.md
  ui/
    0001-use-vuejs.md
```

目录名让类别显式可见。代价是编号只在类别内唯一，不再全仓唯一。最好让分类原则与代码等其他产物一致；按架构结构只是一个选项，也可以按功能分解。这是一项应较早确定的元决策。子目录之外的替代方案见 [ADR-0010](https://github.com/adr/madr/blob/develop/docs/decisions/0010-support-categories.md)。

### 完整模板

原页面在这里展开开发版模板；下文按本地固定模板翻译。元数据和多处章节为可选项，可根据需要删除，不能把它们误解为全部必填。

```markdown
---
# 这些元数据都是可选的，可以删除任意一项。
status: "{proposed | rejected | accepted | deprecated | … | superseded by ADR-0123}"
date: {最后更新决定的日期 YYYY-MM-DD}
decision-makers: {参与决策的人员}
consulted: {征询意见并双向交流的人员，通常是领域专家}
informed: {仅需单向同步进展的人员}
---

# {能够代表所解决问题与所选方案的短标题}

## 背景与问题

{描述背景和问题，例如用两三句话的自由文本或情境故事。也可以采用问题形式。可以链接协作看板或问题管理系统。明确决定范围，例如指明或链接组件、连接器等架构结构要素。}

<!-- 本节可选，可以删除。 -->
## 决策驱动因素

* {驱动因素 1，例如期望的软件质量、关注点、约束或推动选择的因素}
* {驱动因素 2}
* … <!-- 驱动因素数量不限 -->

## 考虑的方案

* {方案 1 的标题}
* {方案 2 的标题}
* {方案 3 的标题}
* … <!-- 方案数量不限 -->

## 决定

选择“{方案 1 的标题}”，因为{理由，例如这是唯一满足决定性驱动条件的选项 | 解决了因素 {因素} | … | 在下面的比较中最合适}。

<!-- 本节可选，可以删除。 -->
### 后果

* 好处：{正面后果，例如改善一项或多项期望质量，…}
* 坏处：{负面后果，例如牺牲一项或多项期望质量，…}
* … <!-- 后果数量不限 -->

<!-- 本节可选，可以删除。 -->
### 确认

{描述如何确认 ADR 的实施或符合情况。是否有自动或人工的适应性检查？如果有，列出并解释用法。所选设计及实现是否符合决定？例如设计/代码 review 或使用 ArchUnit 等库的测试有助于验证。虽然本节归为可选，但许多 ADR 都包含它。}

<!-- 本节可选，可以删除。 -->
## 各方案的优缺点

### {方案 1 的标题}

<!-- 本项可选，可以删除。 -->
{例子 | 描述 | 更多信息的链接 | …}

* 好处：{论据 a}
* 好处：{论据 b}
<!-- 如果论据既不明显支持也不明显反对，使用“中性”。 -->
* 中性：{论据 c}
* 坏处：{论据 d}
* … <!-- 优缺点数量不限 -->

### {其他方案的标题}

{例子 | 描述 | 更多信息的链接 | …}

* 好处：{论据 a}
* 中性：{论据 b}
* 坏处：{论据 c}
* …

<!-- 本节可选，可以删除。 -->
## 更多信息

{可以补充支持决定的证据或信心、记录团队共识、确定何时怎样实施决定以及是否和何时重新讨论。也可以链接其他决定和资料。}
```

### 历史版本

| 版本 | 分支 | 对应入口 |
| --- | --- | --- |
| 1.x | release/v1 | [README](https://github.com/adr/madr/blob/release/v1/README.md) |
| 2.x | release/v2 | [README](https://github.com/adr/madr/blob/release/v2/README.md) |
| 3.x | release/v3 | [index](https://github.com/adr/madr/blob/release/v3/docs/index.md) |

分支命名遵循 [git flow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)。

### 许可

该作品采用 MIT 和 CC0 双重许可，可以选择其中一种使用。

```yaml
SPDX-License-Identifier: MIT OR CC0-1.0
```

## 本仓库解读

采用背景、备选、决定、后果和确认这些必要信息，不安装模板工具，也不为所有编辑创建 ADR。目录名采用用户指定的 `docs/adr/`，属于本地选择。以上保留源文的历史信息和命令，不视作本仓库操作要求。返回 [资料索引](README.md)。
