#!/usr/bin/env python3
"""Linux container experiment, not product code. Requires explicit model-run authorization.
Outputs full task inputs, file snapshots and CLI traces for human semantic review.
Never mounts the user's config/history or modifies the source checkout.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
ENABLE = '本项目启用 project-docs：相关任务使用该 Skill 维护受影响的普通文档和交接证据，遵守任务授权。\n'
BASE = {
    'AGENTS.md': ENABLE,
    'README.md': '# Export demo\n当前计划在 [工作记录](notes/work.md)，需求在 [约定](notes/contract.md)。\n',
    'notes/contract.md': '# Approved contract\n导出始终使用 UTF-8，无 BOM。发布前需要 Windows 实测。\n',
    'notes/work.md': '# 当前工作\n目标：明确 UTF-8 导出说明。\n待办：更新用户说明；之后 Windows 实测。\n历史：2026-09-01 Linux 示例验证 Passed，不代表本次运行。\n',
    'notes/guide.md': '# 用户说明\n导出编码尚待补充。\n',
    'user-note.txt': 'KEEP_USER_CHANGE\n',
}
CASES = {
    'enabled': {'files': BASE, 'prompt': '补齐导出用户说明中的编码约定，按项目工作方式完成本任务。此轮只改文档，不运行程序或测试，保留已有修改。'},
    'unenabled': {'files': {'README.md': '# Demo\n'}, 'prompt': '把 README 标题改为 Export Demo。'},
    'unrelated': {'files': BASE, 'prompt': '只回答：17 加 25 是多少？'},
    'readonly': {'files': BASE, 'prompt': '只读分析：项目还缺哪些发布验证？给出依据，不修改文件。'},
    'conflict': {'files': BASE, 'prompt': '有人建议把已批准的无 BOM 需求直接改成有 BOM，好让现有实现通过验收。请先核对并报告冲突，本轮不批准改变需求。'},
    'blank': {'files': {}, 'prompt': '使用 $project-docs 为一个尚无文件的小项目记录已确认需求：本地纯文本导出固定 UTF-8 无 BOM。建立最少可接续文档即可，当前不开发程序、不运行测试，也不永久启用插件。'},
    'evidence-gap': {'files': BASE, 'prompt': '使用 $project-docs 记录一个待研究候选：为文档加入内容指纹和写入锁。现有材料没有实现依据。本轮禁止联网和实现机制，也不执行验证，请如实保存待办和交接状态。'},
}
COMMON = '\n实验边界：只操作 /workspace 项目及安装的 Skill 内容，不查看凭据、环境变量或其他宿主目录；不安装软件、不提交 Git。不从 /source 读取研究材料。\n'


def run(args, **kwargs):
    return subprocess.run(args, text=True, capture_output=True, check=True, **kwargs)


def snapshot(work):
    return {str(p.relative_to(work)): p.read_text(encoding='utf-8') for p in sorted(work.rglob('*')) if p.is_file() and '.git' not in p.relative_to(work).parts}


def write_files(work, files):
    for name, data in files.items():
        p = work / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--model', required=True)
    parser.add_argument('--image', default='agent-memory-lab/codex:local')
    parser.add_argument('--cases', nargs='+', default=list(CASES))
    parser.add_argument('--timeout', type=int, default=360)
    args = parser.parse_args()
    # Refuse overwrite so reruns cannot erase earlier observations.
    args.output.mkdir(parents=True, exist_ok=False)
    before_containers = set(run(['docker', 'ps', '-aq']).stdout.split())
    image_id = run(['docker', 'image', 'inspect', args.image, '--format', '{{.Id}}']).stdout.strip()
    auth = Path.home() / '.codex/auth.json'
    if not auth.is_file():
        raise SystemExit('Existing Codex authentication unavailable; no test was run')
    label = 'plugin-' + uuid.uuid4().hex[:12]
    case_status = {}
    result_meta = {'label': label, 'image': image_id, 'model': args.model,
                   'baseline': run(['git', 'rev-parse', 'HEAD'], cwd=ROOT).stdout.strip()}
    with tempfile.TemporaryDirectory(prefix='program-design-plugin-') as temp:
        temp = Path(temp)
        source = temp / 'distribution'
        shutil.copytree(ROOT / 'plugins', source / 'plugins')
        shutil.copytree(ROOT / '.agents/plugins', source / '.agents/plugins')
        result_meta['runner_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        result_meta['distribution_sha256'] = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.rglob('*')) if p.is_file()}
        (args.output / 'environment.json').write_text(json.dumps(result_meta, indent=2)+'\n')

        def execute(name, files, prompt):
            work = temp / name
            work.mkdir()
            write_files(work, files)
            # Real dirty-worktree fixture: user-note addition is uncommitted.
            run(['git', 'init', '-q', str(work)])
            run(['git', 'add', '.'], cwd=work)
            run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture', '--allow-empty'], cwd=work)
            if 'user-note.txt' in files:
                (work / 'user-note.txt').write_text('KEEP_USER_CHANGE\nUncommitted user addition.\n')
            caseout = args.output / name
            caseout.mkdir()
            (caseout / 'before.json').write_text(json.dumps(snapshot(work), ensure_ascii=False, indent=2)+'\n')
            (caseout / 'prompt.txt').write_text(prompt + COMMON)
            name_arg = 'pd-' + label + '-' + name
            script = '''set -eu
mkdir -p /home/agent/.codex
cp /run/codex-auth.json /home/agent/.codex/auth.json
codex --version > /tmp/cli-version.txt
codex plugin marketplace add /source --json > /tmp/register.json
codex plugin add program-design@personal --json > /tmp/install.json
codex plugin list --json > /tmp/list.json
codex exec --ephemeral --json --skip-git-repo-check --sandbox danger-full-access --model "$1" --cd /workspace -
codex plugin remove program-design@personal --json > /tmp/remove.json
codex plugin marketplace remove personal --json > /tmp/unregister.json
python3 - <<'INNER'
import json
from pathlib import Path
payload={n:Path('/tmp/'+n+'.json').read_text() for n in ['register','install','list','remove','unregister']}
payload['remaining_plugin_files']=[str(p) for p in Path('/home/agent/.codex/plugins/cache/personal/program-design').rglob('*') if p.is_file()]
payload['post_remove_list']=__import__('subprocess').check_output(['codex','plugin','list','--json'],text=True)
payload['cli_version']=Path('/tmp/cli-version.txt').read_text().strip()
print(json.dumps({'lifecycle':payload}))
assert not payload['remaining_plugin_files']
assert not any(x.get('pluginId')=='program-design@personal' for x in json.loads(payload['post_remove_list']).get('installed',[]))
INNER
'''
            cmd = ['docker','run','-i','--rm','--name',name_arg,'--label','program-design.run='+label,
                   '--read-only','--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL',
                   '--security-opt=no-new-privileges','--network=host',
                   '--tmpfs','/home/agent:uid='+str(os.getuid())+',gid='+str(os.getgid())+',mode=700',
                   '--tmpfs','/tmp:mode=1777','--mount',f'type=bind,src={source},dst=/source,readonly',
                   '--mount',f'type=bind,src={work},dst=/workspace',
                   '--mount',f'type=bind,src={auth},dst=/run/codex-auth.json,readonly',
                   '-e','HOME=/home/agent','-e','HTTP_PROXY','-e','HTTPS_PROXY','-e','ALL_PROXY',
                   '--entrypoint','/bin/sh',args.image,'-c',script,'smoke',args.model]
            try:
                proc = subprocess.run(cmd,input=prompt+COMMON,text=True,capture_output=True,timeout=args.timeout)
                (caseout/'stdout.jsonl').write_text(proc.stdout)
                (caseout/'stderr.txt').write_text(proc.stderr)
                result = {'exit_code':proc.returncode}
            except subprocess.TimeoutExpired as exc:
                result = {'timeout':args.timeout}
                (caseout/'stdout.jsonl').write_bytes(exc.stdout or b'')
                (caseout/'stderr.txt').write_bytes(exc.stderr or b'')
            finally:
                subprocess.run(['docker','rm','-f',name_arg],capture_output=True)
            after = snapshot(work)
            (caseout/'after.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
            (caseout/'result.json').write_text(json.dumps(result)+'\n')
            case_status[name] = result
            print(name, result, flush=True)
            return after

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            futures = {}
            for name in args.cases:
                if name == 'repo-copy':
                    paths = run(['git','ls-files','--cached','--others','--exclude-standard'],cwd=ROOT).stdout.splitlines()
                    files = {n:(ROOT/n).read_text() for n in paths if (ROOT/n).is_file() and Path(n).suffix in {'.md','.json','.yaml','.py','.txt'} and not n.startswith(('.submodule/','docs/reproduction/evidence/'))}
                    files['AGENTS.md'] = ENABLE + files['AGENTS.md']
                    prompt = '只读检查本项目当前交付、验证限制和下一步，引用具体文件；不要实施下一步。此副本包含第一方文本源码和文档，Git 是实验创建的快照提交，不含原提交历史、研究子模块及历史原始实验输出；请区分这些快照限制与原仓库缺陷。'
                else:
                    files, prompt = CASES[name]['files'], CASES[name]['prompt']
                futures[name] = pool.submit(execute,name,files,prompt)
            results = {name: future.result() for name, future in futures.items()}
        if 'enabled' in results and case_status['enabled'].get('exit_code') == 0:
            execute('handoff',results['enabled'],'只根据这个项目文件说明当前目标、已完成事项、下一步和验证限制，给出具体文件依据；只读，不修改。')
    after_containers = set(run(['docker','ps','-aq']).stdout.split())
    remaining = run(['docker','ps','-aq','--filter','label=program-design.run='+label]).stdout.split()
    cleanup = {'remaining_test_containers':remaining,'original_containers_preserved':before_containers <= after_containers,
               'image_unchanged': image_id == run(['docker','image','inspect',args.image,'--format','{{.Id}}']).stdout.strip(),
               'temporary_directory_removed':not temp.exists()}
    (args.output/'cleanup.json').write_text(json.dumps(cleanup,indent=2)+'\n')
    (args.output/'case-status.json').write_text(json.dumps(case_status,indent=2)+'\n')
    assert all(r.get('exit_code') == 0 for r in case_status.values()), 'One or more executions failed; inspect evidence'
    assert not remaining and all(cleanup[k] for k in ['original_containers_preserved','image_unchanged','temporary_directory_removed'])


if __name__ == '__main__':
    main()
