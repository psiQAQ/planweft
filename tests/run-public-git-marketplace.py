#!/usr/bin/env python3
"""Check public Git marketplace installation in fixed, credential-free containers.

Only Codex/Claude plugin management commands run. A same-commit refresh is not
a cross-version upgrade, a model session, or evidence of hook trust/loading.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import uuid
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'https://github.com/psiQAQ/planweft'


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def inventory(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise RuntimeError('Unexpected symlink: ' + str(path))
        if path.is_file():
            result[path.relative_to(root).as_posix()] = {
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'executable': bool(path.stat().st_mode & 0o111)}
    return result


def worker(args):
    out = args.output
    home = Path('/tmp/planweft-public-home')
    home.mkdir()
    (home / '.codex').mkdir()
    (home / '.claude').mkdir()
    project = Path('/tmp/public-project'); project.mkdir()
    protected = {name: (name + ' approved\r\n').encode() for name in
                 ['task_plan.md', 'findings.md', 'progress.md', 'requirements.md']}
    for name, data in protected.items():
        (project / name).write_bytes(data)
    env = {'PATH': os.environ['PATH'], 'HOME': str(home), 'USERPROFILE': str(home),
           'CODEX_HOME': str(home / '.codex'), 'CLAUDE_CONFIG_DIR': str(home / '.claude'),
           'XDG_CONFIG_HOME': str(home / '.config'), 'XDG_CACHE_HOME': str(home / '.cache'),
           'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null',
           'GIT_TERMINAL_PROMPT': '0', 'PLANNING_DISABLED': '1',
           'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1'}
    env.update({key: value for key, value in os.environ.items()
                if key.lower() in {'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'}})
    summary = {'host': args.host, 'repository': REPOSITORY, 'source_commit': args.commit,
               'version': args.version, 'status': 'In Progress', 'steps': [],
               'cross_version_update': 'Not Run: same-commit refresh only',
               'model_sessions_and_hooks': 'Not Run: management commands only'}

    def run(label, argv, required=True, cwd=project):
        try:
            result = subprocess.run(argv, cwd=cwd, env=env, input='', text=True,
                                    capture_output=True, timeout=args.timeout)
            (out / (label + '.log')).write_text(result.stdout + result.stderr)
            summary['steps'].append({'step': label, 'argv': argv, 'exit_code': result.returncode})
            save(out / 'summary.json', summary)
            if required and result.returncode:
                raise RuntimeError(label + ' failed')
            return result.stdout
        except subprocess.TimeoutExpired as error:
            (out / (label + '.log')).write_bytes((error.stdout or b'') + (error.stderr or b''))
            summary['steps'].append({'step': label, 'argv': argv, 'status': 'Timeout'})
            raise RuntimeError(label + ' timed out') from error

    def verify(label, expected):
        suffix = '.codex-plugin/plugin.json' if args.host == 'codex' else '.claude-plugin/plugin.json'
        cache = home / ('.codex/plugins/cache' if args.host == 'codex' else '.claude/plugins/cache')
        candidates = [p.parent.parent for p in cache.rglob(suffix)
                      if json.loads(p.read_text()).get('name') == 'planweft']
        if len(candidates) != 1:
            raise RuntimeError('Expected one native cached plugin: ' + str(candidates))
        actual = inventory(candidates[0])
        save(out / (label + '-inventory.json'), actual)
        if actual != expected:
            save(out / (label + '-difference.json'), {
                'missing': sorted(set(expected) - set(actual)),
                'extra': sorted(set(actual) - set(expected)),
                'changed': sorted(k for k in set(actual) & set(expected) if actual[k] != expected[k])})
            raise RuntimeError('Native cache differs from fixed public source')
        metadata = json.loads((candidates[0] / suffix).read_text())
        if metadata['version'] != args.version:
            raise RuntimeError('Native version differs')
        entries = [p for p in (candidates[0] / 'skills').glob('*/SKILL.md')
                   if p.parent.name == 'project-docs']
        if len(entries) != 1:
            raise RuntimeError('Expected one main project-docs Skill')
        listing = run(label + '-list', [args.host, 'plugin', 'list', '--json'])
        if 'planweft' not in listing:
            raise RuntimeError('Native registration missing')
        summary['steps'].append({'step': label + '-content', 'status': 'Passed',
                                 'file_count': len(actual), 'main_skill_count': len(entries),
                                 'sha256': hashlib.sha256(json.dumps(actual, sort_keys=True,
                                                        separators=(',', ':')).encode()).hexdigest()})

    try:
        run('host-version', [args.host, '--version'])
        reference = Path('/tmp/public-reference')
        run('reference-clone', ['git', '-c', 'credential.helper=', 'clone', '--depth=1',
                               '--branch', 'master', REPOSITORY, str(reference)])
        head = run('reference-head', ['git', 'rev-parse', 'HEAD'], cwd=reference).strip()
        if head != args.commit:
            raise RuntimeError('Public master moved; expected ' + args.commit + ', got ' + head)
        manifest = json.loads((reference / 'dist/manifest.json').read_text())
        expected = manifest['platforms'][args.host]['files']
        if manifest['version'] != args.version or inventory(reference / 'dist' / args.host / 'planweft') != expected:
            raise RuntimeError('Public source distribution manifest mismatch')
        save(out / 'expected-inventory.json', expected)
        run('marketplace-add', [args.host, 'plugin', 'marketplace', 'add', REPOSITORY])
        install = [args.host, 'plugin', 'add', 'planweft@planweft', '--json'] if args.host == 'codex' else [args.host, 'plugin', 'install', 'planweft@planweft', '--scope', 'user']
        run('install', install)
        verify('installed', expected)
        refresh_command = 'upgrade' if args.host == 'codex' else 'update'
        run('marketplace-refresh-help', [args.host, 'plugin', 'marketplace', refresh_command, '--help'])
        run('marketplace-refresh', [args.host, 'plugin', 'marketplace', refresh_command, 'planweft'])
        refresh = install if args.host == 'codex' else [args.host, 'plugin', 'update', 'planweft@planweft', '--scope', 'user']
        run('same-commit-refresh', refresh)
        verify('refreshed', expected)
        # Verify the public branch did not move during the lifecycle.
        remote = run('public-head-after', ['git', '-c', 'credential.helper=', 'ls-remote', REPOSITORY, 'refs/heads/master'])
        if remote.split()[0] != args.commit:
            raise RuntimeError('Public master changed during verification')
        remove = [args.host, 'plugin', 'remove', 'planweft@planweft', '--json'] if args.host == 'codex' else [args.host, 'plugin', 'uninstall', 'planweft@planweft', '--scope', 'user']
        run('uninstall', remove)
        if 'planweft' in run('list-after-uninstall', [args.host, 'plugin', 'list', '--json']):
            raise RuntimeError('Plugin registration survived uninstall')
        run('marketplace-remove', [args.host, 'plugin', 'marketplace', 'remove', 'planweft'])
        listing = run('marketplaces-after-remove', [args.host, 'plugin', 'marketplace', 'list'])
        if 'planweft' in listing:
            raise RuntimeError('Marketplace registration survived removal')
        if any((project / name).read_bytes() != data for name, data in protected.items()):
            raise RuntimeError('Project records changed')
        summary['project_records'] = 'Passed: unchanged'
        summary['status'] = 'Passed'
    except Exception as error:
        summary['status'] = 'Failed'; summary['error'] = str(error)
    save(out / 'summary.json', summary)
    return 0 if summary['status'] == 'Passed' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=['codex', 'claude'], required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=180)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not re.fullmatch('[a-f0-9]{40}', args.commit): parser.error('Invalid full commit SHA')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', args.version): parser.error('Invalid version')
    if not 1 <= args.timeout <= 600: parser.error('Timeout must be 1..600 seconds')
    args.output = args.output.resolve()
    if args.worker:
        if args.output != Path('/evidence') or not Path('/.dockerenv').exists(): parser.error('Worker is container-only')
        return worker(args)
    if args.output.exists() or args.output == ROOT or ROOT in args.output.parents or ',' in str(args.output):
        parser.error('Output must be a new path outside the checkout without commas')
    lock = json.loads((ROOT / 'tests/container-images.json').read_text())
    image = lock['hosts'][args.host]['image']
    if not re.fullmatch('sha256:[a-f0-9]{64}', image): parser.error('Invalid locked image')
    proxy_keys = [key for key in os.environ
                  if key.lower() in {'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'}]
    for key in proxy_keys:
        if key.lower() != 'no_proxy' and (urlsplit(os.environ[key]).username or urlsplit(os.environ[key]).password):
            parser.error('Proxy credentials are outside this credential-free runner')
    runner_bytes = Path(__file__).read_bytes()
    runner_sha256 = hashlib.sha256(runner_bytes).hexdigest()
    actual = subprocess.check_output(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'], text=True).strip()
    if actual != image: raise RuntimeError('Container image lock mismatch')
    args.output.mkdir(parents=True)
    archived_runner = args.output / 'runner.py'
    archived_runner.write_bytes(runner_bytes)
    name = 'planweft-public-git-' + uuid.uuid4().hex
    argv = ['docker', 'run', '--rm', '--name', name, '--user', str(os.getuid()) + ':' + str(os.getgid()),
            '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges', '--network=host',
            '--mount', 'type=bind,src=' + str(archived_runner) + ',dst=/runner/run.py,readonly',
            '--mount', 'type=bind,src=' + str(args.output) + ',dst=/evidence',
            '--tmpfs', '/tmp:mode=1777', *[item for key in proxy_keys for item in ['-e', key]],
            '--entrypoint', 'python3', image, '/runner/run.py',
            '--worker', '--host', args.host, '--commit', args.commit, '--version', args.version,
            '--output', '/evidence', '--timeout', str(args.timeout)]
    result = None
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=args.timeout * 18)
        (args.output / 'container.log').write_text(result.stdout + result.stderr)
    finally:
        subprocess.run(['docker', 'rm', '-f', name], capture_output=True)
        remaining = subprocess.check_output(['docker', 'ps', '-aq', '--filter', 'name=^/' + name + '$'], text=True).strip()
        save(args.output / 'container.json', {'image': image, 'repository': REPOSITORY,
             'source_commit': args.commit, 'runner_sha256': runner_sha256,
             'exit_code': result.returncode if result else None, 'container_removed': not remaining,
             'credentials_mounted': False, 'model_commands': False,
             'network': 'host network with existing credential-free proxy; no isolation claim'})
    return 1 if remaining else result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
