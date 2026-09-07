# REP-0001：参考资料与文档基础验证

日期：2026-09-07；环境：Linux，Git 与系统 Python 3 可用。工作目录为本仓库根目录。本文区分实际执行与预期；产品工具尚不存在。

## 检查项

| 编号 | 操作与预期 | 当前结果 |
| --- | --- | --- |
| V-01 | R-00～R-19 均有明确去向、中文文件、出处和范围；审查引用是否支持主张 | 待独立 review |
| V-02 | 第一方 Markdown 的本地文件链接有效，Git diff 无格式错误 | 待执行最终检查 |
| V-03 | 12 个 gitlink、`.gitmodules`、checkout 与索引 SHA 一致；上游 checkout 无改动；书籍未收录 | 子模块已添加，最终复核待执行 |
| V-04 | 根目录无个人 override，个人差异稿入库，组合说明符合官方替代语义 | 静态检查待执行；真实宿主加载 Not Run |

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

## 验证限制

尚未安装本仓库的任何工具、Skill 或 hook，也未运行参考项目的安装脚本和测试。Linux/Windows 产品兼容、模型行为对照、真实个人 override 加载和自管理迁移均为 **Not Run**；这些不属于本阶段已实现能力。外部文章读取成功只说明访问成功，内容依据由独立 review 判断。

本记录在最终检查后补入执行输出摘要，不将预期结果填写为 Passed。
