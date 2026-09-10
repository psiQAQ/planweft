# 开发与证据维护

本页面向 PlanWeft 维护者。用户安装和支持范围分别见[安装指南](installation.md)与[平台文档](platforms.md)。

## 开始和接续工作

先读取仓库 `AGENTS.md`，再按任务需要定位 specs、plans、ADR 和 reproduction。复杂任务使用选定的 planning-with-files 计划目录；独立任务使用不同计划或 worktree。修改前检查分支、工作区和已有 diff，避免覆盖用户内容。

任务状态写入 `task_plan.md`，调研与来源写入 `findings.md`，实际命令、错误和验证写入 `progress.md`。稳定需求和设计结论进入长期文档，不把完整聊天记录复制进仓库。

## 规范源与生成产物

平台包由固定上游快照和本地 overlays 生成。维护者只修改规范源：

| 内容 | 规范源 | 生成结果 |
| --- | --- | --- |
| 包内项目介绍 | `overlays/planweft/README*.md` | 所有 `dist/<host>/planweft/README*.md` 与 Codex 镜像 |
| 安装指南 | `overlays/planweft/install/INSTALL*.md` | `docs/installation*.md` 和所有包内 `INSTALL*.md` |
| 共享工作流和资源 | `overlays/planweft/` | 各宿主需要的 Skills、hooks、commands 和 references |
| 宿主适配 | `overlays/planweft/native/` | 原生 manifest、桥接和资源布局 |
| 固定运行时 | `vendor/planning-with-files/` | 经过身份映射的 PWF 文件 |

不要手工编辑 `dist/**` 或 `plugins/planweft/**`。生成器维护六种根 catalog、自包含平台目录、逐文件摘要、执行位和整体 manifest；它只清理自己管理的产物。

```bash
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
```

OpenCode 预编译产物绑定源码摘要。只有相关源码变化时才运行编译步骤；不要为了文档修改刷新依赖、编译器或固定上游版本。

## 对外文档与工程记录

README、安装指南、平台页、CHANGELOG 和 GitHub Release 正文只保留用户需要执行或判断的内容：产品用途、命令、支持级别、限制和回退方法。

以下内容留在工程记录中，并由用户文档链接到对应章节：

- 生成器、catalog、manifest 和发布树结构；
- hook 事件映射、资源定位、缓存和宿主协议差异；
- 发布门禁 schema、证据复用、附件摘要和 reviewer 绑定；
- 候选版本逐轮状态、失败、修正和真实模型输出；
- 固定上游来源、补丁清单、设计引用和创新判断。

对外文档不能把历史结果写成当前实测，也不能因能力非阻塞而把 Failed、Inconclusive 或 Not Run 改成 Passed。

## 设计与依据

产品行为以 specs 为准，实施阶段计划保存在 plans，重要取舍进入 ADR，可复现验证进入 reproduction。外部资料和许可证登记在[设计引用台账](design-references.md)与[资料索引](reference/README.md)。固定上游及 `.submodule/` 是研究输入，不在常规构建中安装或执行。

实质设计变更需要独立依据 review。审查至少核对来源是否支持本地结论、公开声明是否超出证据、替代方案是否准确，以及 Not Run 是否被明确保留。重要交接另做不带旧聊天的冷读检查；依据 review 和交接 review 不能互相替代。

## 验证入口

文档或生成源变化至少运行：

```bash
python3 scripts/build-plugin.py --verify
python3 -m unittest tests.test_public_docs
npm run check
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

`tests/README.md` 记录更细的测试与证据入口。验证报告使用 Passed、Failed、Inconclusive、Not Run；未运行的检查必须说明原因。

## 发布与历史

当前发布流程、schema 3 门禁、准确产物和外部写入检查见[发布文档](releasing.md)。0.4.0 的逐轮候选历史保存在 [PLAN-0010](plans/0010-five-agent-release.md) 与 [REP-0010](reproduction/0010-five-agent-release.md)，原始 checkpoint 和 evidence 不因后续成功而回写。
