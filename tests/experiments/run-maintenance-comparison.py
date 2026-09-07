#!/usr/bin/env python3
"""One-off authorized paired trial; frozen inputs, eight isolated CLI sessions.

Run with --output outside the repository. Requires Docker and existing Codex auth.
No personal configuration is mounted; all auth copies live in container tmpfs.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'a5f072e5bca0f27c33264ce4562fd08c4ffbbd18'
IMAGE = 'sha256:aa46e31c71577eb37c1e1d856427d9d159ddd5a41aa92472af722838b1c3a159'
MODEL = 'gpt-5.6-terra'
ENABLE = '本项目启用 project-docs：相关任务使用该 Skill 维护受影响的普通文档和交接证据，遵守任务授权。\n'
NOTE = '\n<!-- Local experiment fixture: keep Windows validation separate. -->\n'


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def snapshot(root):
    result = {}
    for parent, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in {'.git', '.submodule', '__pycache__', '.pytest_cache'})
        for name in sorted(files):
            p = Path(parent) / name
            if p.is_file() and not p.is_symlink():
                result[str(p.relative_to(root))] = p.read_text(encoding='utf-8')
    return result


def hashes(files):
    return {n: hashlib.sha256(v.encode()).hexdigest() for n, v in files.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error('output must be outside the source repository')
    out.mkdir(parents=True, exist_ok=False)
    auth = Path.home() / '.codex/auth.json'
    if not auth.is_file():
        raise SystemExit('Existing Codex authentication unavailable')
    before_containers = set(run(['docker', 'ps', '-aq']).stdout.decode().split())
    run(['docker', 'image', 'inspect', IMAGE])
    label = 'paired-' + uuid.uuid4().hex[:12]
    prompt = (ROOT / 'tests/experiments/maintenance-task.txt').read_text()
    reader = (ROOT / 'tests/experiments/cold-read-task.txt').read_text()
    common = (ROOT / 'docs/reference/python-argparse.md').read_text()
    sample_ids = [uuid.uuid4().hex[:8] for _ in range(4)]
    save(out / 'controller-mapping.json', dict(zip(sample_ids, ['A', 'B', 'B', 'A'])))
    metadata = {'baseline': BASELINE, 'image': IMAGE, 'model': MODEL, 'label': label,
                'order': sample_ids, 'cpus': 2, 'memory': '4g', 'worker_timeout': 900,
                'reader_timeout': 300, 'manual_interventions': 0, 'retries': 0,
                'frozen_inputs': hashes({str(p.relative_to(ROOT)): p.read_text() for p in [
                    Path(__file__), ROOT / 'tests/experiments/check-entry-contract.py',
                    ROOT / 'tests/experiments/maintenance-task.txt', ROOT / 'tests/experiments/cold-read-task.txt',
                    ROOT / 'docs/plans/0004-paired-maintenance-trial.md',
                    ROOT / 'docs/reference/python-argparse.md']})}
    save(out / 'environment.json', metadata)
    temp_path = None
    try:
        with tempfile.TemporaryDirectory(prefix='program-design-paired-work-') as temp:
            temp_path = Path(temp)
            seed = temp_path / 'seed'
            run(['git', 'clone', '--no-local', '--no-hardlinks', '-q', str(ROOT), str(seed)])
            run(['git', 'checkout', '-q', '--detach', BASELINE], cwd=seed)
            baseline = snapshot(seed)
            save(out / 'baseline-manifest.json', hashes(baseline))
            source = temp_path / 'distribution'
            shutil.copytree(seed / 'plugins', source / 'plugins')
            shutil.copytree(seed / '.agents/plugins', source / '.agents/plugins')
            save(out / 'distribution-manifest.json', hashes(snapshot(source)))
            research = temp_path / 'research'
            research.mkdir()
            upstream = {}
            for line in run(['git', 'ls-tree', '-r', BASELINE], cwd=ROOT).stdout.decode().splitlines():
                meta, path = line.split('\t', 1)
                if not meta.startswith('160000 '):
                    continue
                sha = meta.split()[2]
                checkout = run(['git', 'rev-parse', 'HEAD'], cwd=ROOT / path).stdout.decode().strip()
                if checkout != sha:
                    raise RuntimeError('Submodule differs from baseline: ' + path)
                dest = research / Path(path).relative_to('.submodule')
                dest.mkdir(parents=True)
                data = run(['git', 'archive', sha], cwd=ROOT / path).stdout
                with tarfile.open(fileobj=io.BytesIO(data)) as archive:
                    archive.extractall(dest, filter='data')
                upstream[path] = {'commit': sha, 'archive_sha256': hashlib.sha256(data).hexdigest()}
            save(out / 'research-manifest.json', upstream)

            def execute(work, result_dir, task, arm, role):
                result_dir.mkdir()
                (result_dir / 'prompt.txt').write_text(task)
                before = snapshot(work)
                save(result_dir / 'before.json', before)
                name = 'pd-' + label + '-' + result_dir.parent.name + '-' + role
                script = '''set -eu
mkdir -p /home/agent/.codex
cp /run/codex-auth.json /home/agent/.codex/auth.json
codex --version > /evidence/cli-version.txt
python3 --version > /evidence/python-version.txt
codex features list > /evidence/features.txt
if [ "$2" = A ]; then
  codex plugin marketplace add /distribution --json > /evidence/register.json
  codex plugin add program-design@personal --json > /evidence/install.json
fi
codex plugin list --json > /evidence/plugin-list-before.json
if [ "$3" = reader ]; then extra="--disable plugins"; else extra=""; fi
set +e
codex exec --ephemeral --json --skip-git-repo-check --sandbox danger-full-access --model "$1" --disable multi_agent --disable memories $extra --cd /workspace -
status=$?
set -e
if [ "$2" = A ]; then
  codex plugin remove program-design@personal --json > /evidence/remove.json
  codex plugin marketplace remove personal --json > /evidence/unregister.json
fi
codex plugin list --json > /evidence/plugin-list-after.json
python3 - <<'INNER'
import json
from pathlib import Path
files=[str(p) for p in Path('/home/agent/.codex/plugins/cache/personal/program-design').rglob('*') if p.is_file()]
Path('/evidence/cache-cleanup.json').write_text(json.dumps({'remaining_program_design_cache_files':files}))
assert not files
INNER
exit "$status"
'''
                cmd = ['docker', 'run', '-i', '--rm', '--name', name, '--label', 'program-design.run=' + label,
                       '--read-only', '--user', f'{os.getuid()}:{os.getgid()}', '--cap-drop=ALL',
                       '--security-opt=no-new-privileges', '--cpus=2', '--memory=4g', '--network=host',
                       '--tmpfs', f'/home/agent:uid={os.getuid()},gid={os.getgid()},mode=700',
                       '--tmpfs', '/tmp:mode=1777', '--mount', f'type=bind,src={source},dst=/distribution,readonly',
                       '--mount', f'type=bind,src={work},dst=/workspace',
                       '--mount', f'type=bind,src={research},dst=/workspace/.submodule,readonly',
                       '--mount', f'type=bind,src={result_dir},dst=/evidence',
                       '--mount', f'type=bind,src={auth},dst=/run/codex-auth.json,readonly',
                       '-e', 'HOME=/home/agent', '-e', 'HTTP_PROXY', '-e', 'HTTPS_PROXY', '-e', 'ALL_PROXY',
                       '--entrypoint', '/bin/sh', IMAGE, '-c', script, 'trial', MODEL, arm, role]
                start = time.monotonic()
                result = {'role': role, 'timeout_limit': 300 if role == 'reader' else 900}
                try:
                    with (result_dir / 'stdout.jsonl').open('w') as stdout, (result_dir / 'stderr.txt').open('w') as stderr:
                        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True)
                        try:
                            proc.communicate(task, timeout=result['timeout_limit'])
                            result['exit_code'] = proc.returncode
                        except subprocess.TimeoutExpired:
                            result['timed_out'] = True
                            subprocess.run(['docker', 'rm', '-f', name], capture_output=True)
                            proc.kill()
                            proc.wait()
                finally:
                    subprocess.run(['docker', 'rm', '-f', name], capture_output=True)
                    result['wall_seconds'] = round(time.monotonic() - start, 3)
                    after = snapshot(work)
                    save(result_dir / 'after.json', after)
                    save(result_dir / 'changes.json', {p: {'before': before.get(p), 'after': after.get(p)}
                         for p in sorted(before.keys() | after.keys()) if before.get(p) != after.get(p)})
                    (result_dir / 'tracked.diff').write_bytes(run(['git', 'diff', '--binary'], cwd=work).stdout)
                    events = []
                    for line in (result_dir / 'stdout.jsonl').read_text().splitlines():
                        try:
                            item = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if item.get('type') == 'turn.completed':
                            events.append(item.get('usage'))
                    result['usage'] = events
                    save(result_dir / 'result.json', result)
                print(result_dir.parent.name, role, json.dumps(result), flush=True)

            for sid, arm in zip(sample_ids, ['A', 'B', 'B', 'A']):
                work = temp_path / sid
                shutil.copytree(seed, work)
                (work / 'docs/reference/python-argparse.md').write_text(common)
                with (work / 'README.md').open('a') as f:
                    f.write(NOTE)
                if arm == 'A':
                    (work / 'AGENTS.md').write_text(ENABLE + (work / 'AGENTS.md').read_text())
                sample = out / sid
                sample.mkdir()
                execute(work, sample / 'implementation', prompt, arm, 'implementation')
                # Remove only the exact controller addition; preserve all worker artifacts.
                agents = work / 'AGENTS.md'
                text = agents.read_text()
                count = text.splitlines(keepends=True).count(ENABLE) if arm == 'A' else 0
                removed = count == 1
                if removed:
                    lines = text.splitlines(keepends=True)
                    lines.remove(ENABLE)
                    agents.write_text(''.join(lines))
                save(sample / 'reader-preparation.json', {'controller_enable_line_removed': removed,
                     'exact_line_count': count, 'preparation_failed': count > 1,
                     'note': 'Missing or altered line is retained as an artifact limitation; reader plugins are disabled.'})
                execute(work, sample / 'reader', reader, 'B', 'reader')
    finally:
        remaining = run(['docker', 'ps', '-aq', '--filter', 'label=program-design.run=' + label]).stdout.decode().split()
        for container in remaining:
            run(['docker', 'rm', '-f', container])
        after_containers = set(run(['docker', 'ps', '-aq']).stdout.decode().split())
        save(out / 'cleanup.json', {'remaining_test_containers': run(['docker', 'ps', '-aq', '--filter', 'label=program-design.run=' + label]).stdout.decode().split(),
             'original_containers_preserved': before_containers <= after_containers,
             'temporary_workspace_removed': temp_path is None or not temp_path.exists(),
             'image_preserved': run(['docker', 'image', 'inspect', IMAGE]).returncode == 0,
             'auth_copies': 'container tmpfs; removed with experiment containers'})


if __name__ == '__main__':
    main()
