# 定位安装资源与限制手工临时目录

[简体中文](local-operations.zh.md) | [English](local-operations.md)

这些示例仅用于已授权操作；只读任务不创建临时目录。参数来自宿主已给出的 Skill 位置或已确认的授权项目，不通过配置、收据或全盘搜索寻找。

## 一次解析宿主列出的 Skill

相对符号链接的 target 相对于链接的父目录，不是项目 cwd。先解析实际 `SKILL.md`，再定位它旁边的 `scripts`、`references`、`templates`。有 Python 时：

```python
from pathlib import Path
import sys

skill = Path(sys.argv[1]).resolve(strict=True)
if not skill.is_file() or skill.name != "SKILL.md":
    raise ValueError("Expected the host-listed SKILL.md")
print(skill.parent)
```

把宿主列出的 Skill 文件作为第一个参数。返回目录用于文档命令中的 `<安装 Skill>`；脚本 cwd 仍为授权项目。这只解析给定路径，不读取宿主配置。路径缺失或不符时，从给定位置诊断，不扩展到无关文件；没有 Python 时使用平台对应的链接解析能力。

## 在授权项目内分配手工临时目录

对已授权的手工复现或反事实检查，将分配和清理放在同一项检查内。有 Python 时：

```python
from pathlib import Path
import sys
import tempfile

project = Path(sys.argv[1]).resolve(strict=True)
if not project.is_dir():
    raise ValueError("Expected the authorized project directory")
with tempfile.TemporaryDirectory(prefix=".pw-scratch-", dir=project) as directory:
    scratch = Path(directory).resolve(strict=True)
    print("manual scratch:", scratch.relative_to(project))
    # Run the authorized manual check here, using scratch for every output.
```

把授权项目目录作为第一个参数。随检查记录实际相对临时路径和结果；context manager 仅清理它创建的目录，异常时也执行。示例本身没有完成任何验证。不使用非自有固定 `/tmp` 路径，也不修改整个 Agent 进程的 `TMPDIR`，避免宿主私有临时数据进入项目。既有测试框架临时文件、控制器自有夹具是不同观察，不从手工检查推断其位置，也不为宣称范围覆盖而改写批准的测试。

依据：Python 官方 [Path.resolve](https://docs.python.org/3/library/pathlib.html#pathlib.Path.resolve) 说明链接规范解析，[TemporaryDirectory](https://docs.python.org/3/library/tempfile.html#tempfile.TemporaryDirectory) 说明显式父目录和 context manager 清理。这些 API 不提供任务授权，也不证明模型会遵循示例。
