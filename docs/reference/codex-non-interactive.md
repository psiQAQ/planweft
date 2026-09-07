# Codex 非交互运行与临时会话

R-20；作者：OpenAI。[官方原文](https://learn.chatgpt.com/docs/non-interactive-mode)；访问日期：2026-09-07。状态：已收录；用于本轮容器交接实验。

范围：中文要点摘要；未确认该页面全文翻译授权，不复制全文。

## 原文要点

`codex exec` 可从脚本或 CI 调用，支持从 stdin 接收任务。`--json` 输出结构化事件，便于区分运行过程与最终回答；`--ephemeral` 用于不持久保存会话运行文件。无交互调用应明确审批和 sandbox 设置。

原文定位：Basic usage；Permissions and safety；Make output machine-readable；官方页面链接到的 `codex exec` 参数说明。具体参数是否受支持仍需查看实际安装版本。

## 本仓库解读

本轮同时使用空白用户目录、独立进程和受跟踪文档快照；单独使用 `--ephemeral` 不能证明没有加载其他配置或旧知识。容器使用既有镜像中的 CLI，绕开原实验的共享记忆入口，认证仅提供给对应服务。镜像、CLI 版本、参数与实际结果在实验记录中分别列出，不据官方指南推定本机运行成功。

返回 [资料索引](README.md)。
