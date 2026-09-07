# GitHub Issues 快速入门

R-18；作者：GitHub 文档贡献者。[英文原文](https://docs.github.com/en/issues/tracking-your-work-with-issues/learning-about-issues/quickstart)；访问日期：2026-09-07。© 2026 GitHub, Inc.

范围：访问日页面正文完整中文翻译，从 Introduction 至 Next steps；截图改为文字位置说明，网站导航和页脚不复制。文中的扩展阅读保留标题，可在原页同名链接打开。根据 [github/docs 的许可范围](https://github.com/github/docs#license)，文档采用 [CC BY 4.0](licenses/github-CC-BY-4.0.txt)，本译文采用相同许可。译者：本仓库维护者，AI 辅助。

## 原文译文

跟随这份简短的交互式指南了解 GitHub Issues。

### 介绍（Introduction）

本指南展示如何用 GitHub Issues 规划与跟踪一项工作。你将创建一个 issue 并将其拆分为 sub-issues，也会学习如何通过标签、issue 类型、里程碑、负责人和项目表达 issue 的元数据。

### 前提条件（Prerequisites）

创建 issue 需要一个仓库。你可以使用已有写权限的仓库，或新建仓库。仓库必须启用 Issues。关于新建仓库见原页链接“Creating a new repository”；如果 Issues 被禁用，启用方法见“Disabling issues”。

### 打开空白 issue（Opening a blank issue）

先创建 issue。有多种创建方式，可选择最适合工作流程的方法；本例使用 GitHub UI。其他方法见“Creating an issue”。

1. 在 GitHub 打开仓库主页。
2. 点击仓库名称下面的 **Issues** 标签。原图标出的是仓库水平导航栏中的该标签。
3. 点击 **New issue**。
4. 本例从空白 issue 开始。仓库可能使用 issue 模板或表单，鼓励贡献者提供特定信息；如果使用模板，点击 **Open a blank issue**。

### 填写信息（Filling in information）

给 issue 一个描述性标题，使读者一眼看出它讨论什么。

添加说明，解释 issue 的目的及有助于解决它的细节。例如，报告 bug 时，应描述复现步骤、预期结果和实际结果。

可以使用 Markdown 添加格式、链接、emoji 等，更多见“Writing on GitHub”。原图展示已填写标题和正文的新 issue 表单。

### 添加任务清单（Adding a task list）

也可以用纯文本跟踪尚无对应 issue 的任务，随后再将它们转为 issue。更多见“About tasklists”。原图在新 issue 正文中展示 Markdown 任务清单。

### 指派 issue（Assigning the issue）

为明确责任，可以将 issue 指派给组织中的成员。见“Assigning issues and pull requests to other GitHub users”。原图标出右侧栏的 **Assignees** 区域。

### 添加标签（Adding labels）

使用标签为 issue 分类。例如，`question` 和 `good first issue` 可以表示这是一个初次贡献者能够接手的问题。用户可以按标签筛选，找到具有特定标签的全部 issue。

可以使用默认标签或新建标签。见“Managing labels”。原图标出右侧栏的 **Labels** 区域。

### 添加 issue 类型（Adding issue types）

可以添加 issue 类型，在整个组织范围内对工作分类。见“Managing issue types in an organization”。原图标出右侧栏的 **Type** 区域。

### 将 issue 加入项目（Adding the issue to a project）

可以将 issue 加入已有项目，并填入项目元数据。更多见“About Projects”。原图标出右侧栏的 **Projects** 区域。

### 添加里程碑（Adding milestones）

可以添加里程碑，将 issue 作为按日期设定目标的一部分进行跟踪。里程碑展示目标日期临近时各 issue 的进展。见“About milestones”。原图标出右侧栏的 **Milestone** 区域。

### 提交 issue（Submitting your issue）

点击 **Submit new issue** 创建 issue。创建后仍可编辑上述字段。每个 issue 都有唯一 URL，可以分享给团队成员，或在其他 issue、pull request 中引用。

### 添加子 issue（Adding sub-issues）

可以通过子 issue 将较大的工作快速拆成较小的 issue。子 issue 在 issue 之间建立关系，使 GitHub 支持层级结构。可以创建多个层级，按团队实际需要的细节程度拆分任务，从而准确表达项目。见“Adding sub-issues”和“Browsing sub-issues”。原图突出 issue 正文下方子 issue 区域中的 **View more sub-issue options** 按钮。

### 添加 issue 依赖（Adding issue dependencies）

使用 issue dependencies 定义阻塞关系，识别哪些 issue 被其他工作阻塞，或正在阻塞其他工作。见“Creating issue dependencies”。

### 沟通（Communicating）

创建 issue 后，可以继续添加评论。通过 @mention 协作者或团队，使他们关注某条评论。要链接同仓库相关 issue，可以输入 `#` 和部分标题，再点击要链接的 issue。更多见“Writing on GitHub”。原图展示 octocat 的评论：`@hubot Do we also need to update the rocket logic?`

### 后续步骤（Next steps）

Issue 可以用于多种目的，例如跟踪想法、收集反馈、规划任务和报告 bug。

可以增加多层子 issue，把工作拆成更易管理的任务；见“Adding sub-issues”。进一步使用 GitHub Issues 的相关资料包括：

- “About issues”：了解 issue。
- “Planning and tracking work for your team or project”：了解 GitHub 规划与跟踪工具的基本用法。
- “Learning about Projects”：了解项目如何帮助规划和跟踪。
- “Using templates to encourage useful issues and pull requests”：了解如何用 issue 模板和表单鼓励贡献者提供特定信息。

## 本仓库解读

借鉴的是“填写信息”中复现步骤、预期与实际结果的组织方式；本地 reproduction 额外保存环境和验证证据。不因此创建远端 issue、采用所有元数据字段或预设自动化流程。返回 [资料索引](README.md)。
