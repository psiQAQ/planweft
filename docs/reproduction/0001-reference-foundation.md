# REP-0001：参考资料与文档基础验证

日期：2026-09-07；环境：Linux、Git 2.53.0、系统 Python 3.14.4，无额外包。工作目录为本仓库根目录；基础提交为 `7b45c64f711952512a1dca19d67df3b0e565ca83`。本文区分实际执行与预期；产品工具尚不存在。

适用范围：下列数量断言验证基础阶段快照；收尾状态保存在 `affbff9`。后续增补来源或文档时，不直接把这些历史数量当成当前不变量；新阶段应记录自己的验收范围。

## 检查项

| 编号 | 操作与预期 | 当前结果 |
| --- | --- | --- |
| V-01 | R-00～R-19 均有明确去向、中文文件、出处和范围；审查引用是否支持主张 | Passed；独立核查两会话 32 个可见相关 URL 均有去向；6 份正文/章节译文及其余摘要通过内容核对，见 REV-0001 |
| V-02 | 第一方 Markdown 的本地文件链接有效，Git diff 无格式错误 | Passed；收尾后 34 份 Markdown、146 处本地文件链接，缺失目标 0；暂存差异检查修正许可行尾空白后通过 |
| V-03 | 12 个 gitlink、`.gitmodules`、checkout 与索引 SHA 一致；上游 checkout 无改动；书籍未收录 | Passed（当前 checkout）；12 项一致且干净，基础提交仅 54 项（含 12 个 gitlink），无书籍；全新恢复结果见下方 |
| V-04 | 根目录无个人 override，个人差异稿入库，组合说明符合官方替代语义 | Passed（静态）；根目录无 override，个人文件已提交；真实宿主加载 Not Run |

## 可重复的基本检查

```bash
git diff --check
git diff --cached --check
git submodule status
git ls-files --stage .submodule
git status --short
```

预期：前两条无输出；12 个子模块无 `-`、`+` 或 `U` 状态前缀；索引 mode 为 `160000`；状态中不含书籍、凭据或参考项目内部修改。未建立初始 commit 时，应同时检查 staged 和 untracked 文件，不能仅凭 `git diff` 为空判定没有改动。

```bash
test ! -f AGENTS.override.md
test -f profiles/personal/AGENTS.override.md
git check-ignore docs/books/example.pdf
```

预期前两条退出 0，最后一条输出被忽略的书籍目录示例路径。检查的是文件布局和忽略规则，不是模型实际加载、遵循了指令。

### 文件链接与固定版本核对

以下使用系统 Python 3，无额外依赖。在仓库根执行，检查第一方 Markdown 的普通内联本地文件链接（跳过代码块、URL 和页内锚点），以及子模块的索引、checkout、目录和 SHA。它不是通用 Markdown 解析器，不验证外部链接、标题锚点或模型行为。

```bash
python3 - <<'PY'
from pathlib import Path
from urllib.parse import unquote, urlsplit
import configparser, re, subprocess

root = Path.cwd()
files = [root / 'README.md', root / 'AGENTS.md']
files += list((root / 'profiles').rglob('*.md'))
files += [p for p in (root / 'docs').rglob('*.md')
          if 'books' not in p.relative_to(root).parts]
errors, links = [], 0
for path in files:
    fence = None
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            value = marker[1]
            if fence is None:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence):
                fence = None
            continue
        if fence or line.startswith('    '):
            continue
        for target in re.findall(r'\]\(([^\n]+?)\)', line):
            target = target.strip('<>')
            if urlsplit(target).scheme or target.startswith('#'):
                continue
            name = unquote(target.split('#')[0])
            if name:
                links += 1
                if not (path.parent / name).exists():
                    errors.append(f'{path.relative_to(root)}:{number}: {target}')

def git(*args, cwd=root):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()

config = configparser.ConfigParser()
config.read('.gitmodules')
entries = git('ls-files', '--stage', '.submodule').splitlines()
pins = {line.split('\t', 1)[1]: line.split()[1]
        for line in entries if line.startswith('160000 ')}
catalog = (root / 'docs/reference/README.md').read_text(encoding='utf-8')
assert len(pins) == len(config.sections()) == 12
for section in config.sections():
    relative = config[section]['path']
    head = git('rev-parse', 'HEAD', cwd=root / relative)
    assert pins[relative] == head and head in catalog, relative
    assert not git('status', '--porcelain', cwd=root / relative), relative
    assert config[section]['url'] == 'https://github.com/' + relative[len('.submodule/'):] + '.git'
assert set(re.findall(r'^\| (R-\d\d) ', catalog, re.M)) == {f'R-{i:02}' for i in range(20)}
print({'markdown_files': len(files), 'local_links_checked': links,
       'submodules': len(pins), 'errors': errors})
raise SystemExit(bool(errors))
PY
```

## 执行结果与恢复验证

上述内联 Python 检查已实际执行，基础提交上的输出为：

```text
{'markdown_files': 34, 'local_links_checked': 143, 'submodules': 12, 'errors': []}
```

首次对全部新文件暂存后，`git diff --cached --check` 报告 Diátaxis 许可副本的 6 处行尾空白（Failed）；移除这些格式空白、保留许可文字并标明处理后，重新暂存检查为 Passed。仅看尚未收录文件时的空 diff 不足以完成检查。

全新临时克隆恢复验证 **Passed**。在 Linux 从本地基础提交克隆主仓，再从各 GitHub HTTPS 地址下载子模块；未复用原子模块目录或对象缓存。实际步骤如下（从本仓库根开始）：

```bash
task_source=$PWD
task_restore=$(mktemp -d)
git clone --no-local "$task_source" "$task_restore/repository"
git -C "$task_restore/repository" checkout --detach 7b45c64f711952512a1dca19d67df3b0e565ca83
git -C "$task_restore/repository" -c protocol.file.allow=never submodule update --init --depth 1 --jobs 4
git -C "$task_restore/repository" submodule status
git -C "$task_restore/repository" status --porcelain
```

实际 12/12 子模块恢复成功，状态均为空格前缀、无改动；在新克隆中执行上述 Python 检查仍为 34 份 Markdown、143 个本地文件链接、12 个固定版本、错误 0。该结果证明访问日可从上游恢复这些 commit，不保证上游永远保留仓库。测试仅初始化一层，没有运行第三方脚本。

填入最终 review、计划和验证结果后，新增 3 处报告链接；工作区再次执行静态检查为 34 份 Markdown、146 个本地文件链接、12 个固定版本、错误 0。子模块和实质设计文件与基础提交相同。

## 验证限制

尚未安装本仓库的任何工具、Skill 或 hook，也未运行参考项目的安装脚本和测试。Linux/Windows 产品兼容、模型行为对照、真实个人 override 加载和自管理迁移均为 **Not Run**；这些不属于本阶段已实现能力。外部文章读取成功只说明访问成功，内容依据由独立 review 判断。

本记录中的 Passed 限于相应检查范围；具体依据审查及处理结果见 [REV-0001](../reviews/0001-evidence-review.md)。
