# Pi：Context Files 与 System Prompt

R-15；Mario Zechner / Pi contributors。原文：[README 的 Context Files](https://github.com/earendil-works/pi/blob/9767ba275f3e9a5ee0f5c5342249b629ab1b2282/packages/coding-agent/README.md#context-files)，[本地固定文件](../../.submodule/earendil-works/pi/packages/coding-agent/README.md)。访问日期：2026-09-07。

范围：Context Files 章节（包含 System Prompt 子节）完整中文翻译，不是全部 README。Copyright (c) 2025 Mario Zechner；[MIT 许可证](licenses/pi-MIT.txt)。以下是上游说明，不是本仓库配置指令。

## 原文译文

Pi 启动时从以下位置加载 `AGENTS.md`（或 `CLAUDE.md`）：

- `~/.pi/agent/AGENTS.md`：全局文件。
- 父目录：从当前工作目录向上查找。
- 当前目录。

如果某目录包含 `AGENTS.override.md`，Pi 会加载它，替代该目录中的 `AGENTS.md` 或 `CLAUDE.md`。其他目录的上下文文件仍然拼接到一起。

这些文件用于项目指导、约定和常用命令。匹配的文件会合并到上下文。

使用 `--no-context-files`（或 `-nc`）可以禁用上下文文件加载。

### System Prompt

用项目级 `.pi/SYSTEM.md` 或全局 `~/.pi/agent/SYSTEM.md` 替换默认系统提示词。若希望追加而非替换，使用 `APPEND_SYSTEM.md`。

## 本仓库解读

该固定版本同样存在“同目录 override 替代基础文件”的行为。不同宿主仍需单独适配和实测；本阶段只阅读源码与文档，没有安装 Pi。返回 [资料索引](README.md)。
