#!/usr/bin/env python3
"""Verify two project installations share one HOME without cross-project changes.

Uses exact local npm archives, locked native container images, and public npm
dependency downloads only. No credentials or model commands are used. Codex and
DSH instead verify unsupported project scope is rejected before any write.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
from urllib.parse import urlsplit
import uuid

ROOT = Path(__file__).resolve().parents[1]
HOSTS = ('claude', 'pi', 'opencode', 'codex', 'dsh')


def resource_preflight(output):
    existing=output
    while not existing.exists(): existing=existing.parent
    disk=shutil.disk_usage(existing).free
    match=re.search(r'^MemAvailable:\s+(\d+)\s+kB$',Path('/proc/meminfo').read_text(),re.M)
    memory=int(match[1])*1024 if match else 0
    if memory < 4*1024**3 or disk < 8*1024**3:
        raise RuntimeError('Require 4 GiB available RAM and 8 GiB free output storage')
    return {'available_memory_bytes':memory,'free_disk_bytes':disk}


def cleanup_owned(name, token):
    try:
        def read(arguments):
            return subprocess.check_output(['docker',*arguments],text=True,timeout=30).strip()
        query=['ps','-aq','--filter','name=^/'+name+'$']
        if not read(query):return {'container_removed':True}
        owner=read(['inspect','--type','container','--format',
                    '{{index .Config.Labels "planweft.isolation-run"}}',name])
        if owner!=token:return {'container_removed':False,'error':'ownership label differs'}
        subprocess.run(['docker','rm','-f',name],capture_output=True,timeout=30)
        return {'container_removed':not read(query)}
    except (OSError,subprocess.SubprocessError) as error:
        return {'container_removed':False,'error':type(error).__name__}


def save(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def snapshot(root):
    result = {}
    for path in sorted(root.rglob('*')):
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[name] = {'symlink': os.readlink(path)}
        elif path.is_file():
            result[name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'executable': bool(path.stat().st_mode & 0o111)}
        elif path.is_dir():
            result[name] = {'directory': True}
    return result


def pi_project_sources(settings, project):
    # Pi 0.84.3 stores local package paths relative to its project .pi directory
    # (package-manager.js normalizeSourceForScope/getBaseDirForScope).
    entries = settings.get('packages', [])
    return [str((project / '.pi' / value).resolve()) for value in entries
            if isinstance(value, str) and (value.startswith('.') or Path(value).is_absolute())]


def inspect_archive(path, digest):
    if not re.fullmatch('[a-f0-9]{64}', digest) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError('Archive SHA-256 mismatch')
    seen = set()
    with tarfile.open(path) as archive:
        for member in archive:
            name = Path(member.name)
            if (name.is_absolute() or '..' in name.parts or not name.parts
                    or name.parts[0] != 'package' or member.name in seen
                    or not (member.isfile() or member.isdir())):
                raise ValueError('Unsafe or duplicate npm archive member')
            seen.add(member.name)
        package = json.load(archive.extractfile('package/package.json'))
        if package.get('name') != 'planweft' or not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', package.get('version', '')):
            raise ValueError('Unexpected package identity')
    return package['version']


def worker(args):
    out = args.output
    home = out / 'profile'; home.mkdir()
    temporary=out / 'tmp'; temporary.mkdir()
    for name in ['.codex', '.claude', '.pi/agent', '.config/opencode', '.dsh']:
        (home / name).mkdir(parents=True, exist_ok=True)
    env = {key: value for key, value in os.environ.items()
           if key.lower() in {'path', 'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'}}
    env.update(HOME=str(home), USERPROFILE=str(home), CODEX_HOME=str(home / '.codex'),
               CLAUDE_CONFIG_DIR=str(home / '.claude'), PI_CODING_AGENT_DIR=str(home / '.pi/agent'),
               DSH_HOME=str(home / '.dsh'), XDG_CONFIG_HOME=str(home / '.config'),
               XDG_DATA_HOME=str(home / '.local/share'), XDG_CACHE_HOME=str(home / '.cache'),
               npm_config_userconfig='/dev/null', npm_config_cache=str(home / '.npm'),
               npm_config_registry='https://registry.npmjs.org', PLANNING_DISABLED='1',
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1', GIT_CONFIG_NOSYSTEM='1',
               GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0', TMPDIR=str(temporary))
    report = {'host': args.host, 'status': 'In Progress', 'old_version': args.old_version,
              'version': args.version, 'old_sha256': args.old_sha256, 'sha256': args.sha256,
              'shared_home': True, 'model_calls': 'Not Run: native management/discovery only',
              'hooks': 'Not Run: PLANNING_DISABLED=1',
              'uninstall_verification_scope': 'Removed-side installer receipts only; surviving B native state is checked. Full native uninstall absence is a separate lifecycle check.',
              'steps': []}
    projects = {letter: out / ('项目 ' + letter) for letter in ['A', 'B']}
    protected = {}
    for letter, project in projects.items():
        project.mkdir()
        protected[letter] = {name: (letter + ' approved ' + name + '\r\n').encode() for name in
                             ['task_plan.md', 'findings.md', 'progress.md', 'requirements.md']}
        for name, data in protected[letter].items():
            (project / name).write_bytes(data)
        if args.host == 'opencode':
            # Native discovery has no usable model provider and never submits a prompt.
            save(project / 'opencode.json', {'autoupdate': False, 'model': 'fixture/never-call',
                 'enabled_providers': ['fixture'], 'provider': {'fixture': {
                     'npm': '@ai-sdk/openai-compatible', 'options': {
                         'baseURL': 'http://127.0.0.1:1/v1', 'apiKey': 'fixture-not-a-credential'},
                     'models': {'never-call': {'name': 'Never called'}}}}})
    packages = {}
    for label, archive in [('old', args.old_archive), ('new', args.archive)]:
        target = out / ('source-' + label); target.mkdir()
        with tarfile.open(archive) as packed:
            packed.extractall(target)  # Every member was validated before output/Docker.
        packages[label] = target / 'package'

    def run(label, argv, project='A', required=True, input_data=''):
        result = subprocess.run(argv, cwd=projects[project], env=env, input=input_data,
                                text=True, capture_output=True, timeout=args.timeout)
        (out / (label + '.log')).write_text(result.stdout + result.stderr)
        report['steps'].append({'step': label, 'argv': argv, 'project': project,
                                 'exit_code': result.returncode})
        save(out / 'summary.json', report)
        if required and result.returncode:
            raise RuntimeError(label + ' failed')
        return result

    def invoke(label, action, source='new', project='A', required=True):
        argv = ['node', str(packages[source] / 'bin/planweft.mjs'), action, '-a', args.host, '--project']
        if args.host == 'pi': argv.append('--approve-pi-project')
        if action in {'add', 'update'}:
            argv += ['--source', str(args.old_archive if source == 'old' else args.archive)]
        return run(label, argv, project, required, 'y\ny\ny\n')

    def record(letter):
        return json.loads((projects[letter] / '.planweft/installations.json').read_text())['agents'][args.host]

    def verify(label, letter, source):
        rec = record(letter)
        expected_version = args.old_version if source == 'old' else args.version
        if rec['version'] != expected_version or rec['status'] != 'installed':
            raise RuntimeError('Installer selected wrong version/status')
        expected = json.loads((packages[source] / 'dist/manifest.json').read_text())['platforms'][args.host]['files']
        root = Path(rec['packageRoot']) / 'dist' / args.host / 'planweft'
        native_state = {}
        if args.host == 'claude':
            listing = json.loads(run(label + '-native-list', ['claude', 'plugin', 'list', '--json'], letter).stdout)
            selected = [item for item in listing if item.get('id') == rec['nativeId']
                        and item.get('scope') == 'project' and item.get('projectPath') == str(projects[letter])]
            if len(selected) != 1 or selected[0]['version'] != expected_version:
                raise RuntimeError('Claude native project registration differs')
            root = Path(selected[0]['installPath'])
            installed = json.loads((home / '.claude/plugins/installed_plugins.json').read_text())
            known = json.loads((home / '.claude/plugins/known_marketplaces.json').read_text())
            native_state = {'installed': installed['plugins'][rec['nativeId']],
                            'marketplace': known[rec['catalog']]}
        elif args.host == 'pi':
            listing = run(label + '-native-list', ['pi', 'list', '--approve'], letter).stdout
            if rec['nativeSource'] not in listing:
                raise RuntimeError('Pi did not select this project source')
            settings = json.loads((projects[letter] / '.pi/settings.json').read_text())
            save(out / (label + '-pi-settings.json'), settings)
            if pi_project_sources(settings, projects[letter]).count(rec['nativeSource']) != 1:
                raise RuntimeError('Pi project source missing or duplicated')
            native_state = settings
        elif args.host == 'opencode':
            agent = json.loads(run(label + '-native-tools', ['opencode', 'debug', 'agent', 'build'], letter).stdout)
            if not all(agent.get('tools', {}).get(key) for key in ['pw_init', 'pw_status', 'pw_check']):
                raise RuntimeError('OpenCode native tools not loaded')
            skills = json.loads(run(label + '-native-skills', ['opencode', 'debug', 'skill'], letter).stdout)
            entries = [item for item in skills if item.get('name') == 'project-docs']
            if len(entries) != 1:
                raise RuntimeError('OpenCode main Skill not unique')
            native_state = {'skills': entries, 'loader': (projects[letter] / '.opencode/plugins/planweft.ts').read_text()}
            if str(Path(rec['packageRoot'])).replace(' ', '%20') not in native_state['loader']:
                # file URLs also encode non-ASCII project names.
                if root.joinpath('dist/index.js').as_uri() not in native_state['loader']:
                    raise RuntimeError('OpenCode loader points at another package')
        for base in {root, Path(rec['packageRoot']) / 'dist' / args.host / 'planweft'}:
            actual = {name: data for name, data in snapshot(base).items() if not data.get('directory')}
            if actual != expected:
                save(out / (label + '-content-diff.json'), {'expected': expected, 'actual': actual})
                raise RuntimeError('Native/persistent platform contents differ')
        state = {'record': rec, 'native_state': native_state, 'native_root': str(root),
                 'native_inventory': expected, 'project_snapshot': snapshot(projects[letter])}
        save(out / (label + '-state.json'), state)
        report['steps'].append({'step': label, 'status': 'Passed', 'project': letter,
                                 'version': expected_version, 'files_checked': len(expected)})
        return state

    try:
        run('host-version', [args.host, '--version'])
        if args.host in {'codex', 'dsh'}:
            # Snapshot after --version; rejection must not create even empty state directories.
            before_home, before_project = snapshot(home), snapshot(projects['A'])
            rejected = invoke('unsupported-project', 'add', required=False)
            if rejected.returncode == 0 or not ('scope' in rejected.stdout + rejected.stderr):
                raise RuntimeError('Unsupported native project scope was not rejected')
            if snapshot(home) != before_home or snapshot(projects['A']) != before_project:
                raise RuntimeError('Unsupported project request wrote state')
            report['unsupported_project_scope'] = 'Passed: nonzero, HOME/project unchanged'
        else:
            invoke('install-A-old', 'add', 'old', 'A')
            verify('A-old', 'A', 'old')
            invoke('install-B-new', 'add', 'new', 'B')
            verify('A-after-B', 'A', 'old')
            baseline = verify('B-baseline', 'B', 'new')
            if args.host == 'claude' and record('A')['catalog'] == record('B')['catalog']:
                raise RuntimeError('Project marketplaces collided')
            invoke('update-A-new', 'update')
            verify('A-updated', 'A', 'new')
            after = verify('B-after-A-update', 'B', 'new')
            if after != baseline: raise RuntimeError('Updating A changed B')
            invoke('remove-A', 'remove')
            after = verify('B-after-A-remove', 'B', 'new')
            if after != baseline: raise RuntimeError('Removing A changed B')
            state_a = json.loads((projects['A'] / '.planweft/installations.json').read_text())
            if args.host in state_a.get('agents', {}): raise RuntimeError('A registration survived removal')
            invoke('remove-B', 'remove', project='B')
            if args.host in json.loads((projects['B'] / '.planweft/installations.json').read_text()).get('agents', {}):
                raise RuntimeError('B registration survived removal')
            report['two_project_isolation'] = 'Passed: A old/B new; update/remove A preserves B'
        if any((projects[letter] / name).read_bytes() != data for letter, files in protected.items() for name, data in files.items()):
            raise RuntimeError('Protected project records changed')
        report['protected_project_records'] = 'Passed'
        report['status'] = 'Passed'
    except Exception as error:
        report['status'] = 'Failed'; report['error'] = str(error)
    save(out / 'summary.json', report)
    return 0 if report['status'] == 'Passed' else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=HOSTS, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--old-archive', type=Path, required=True)
    parser.add_argument('--old-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=240)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 600: parser.error('Timeout must be 1..600 seconds')
    args.archive = args.archive.resolve(); args.old_archive = args.old_archive.resolve()
    args.output = args.output.resolve()
    try:
        args.version = inspect_archive(args.archive, args.sha256)
        args.old_version = inspect_archive(args.old_archive, args.old_sha256)
        if args.version == args.old_version: raise ValueError('Two distinct versions required')
    except (OSError, ValueError, KeyError, tarfile.TarError) as error:
        parser.error(str(error))
    if args.worker:
        if args.output != Path('/evidence') or not Path('/.dockerenv').exists(): parser.error('Worker is container-only')
        return worker(args)
    if args.output.exists() or args.output == ROOT or ROOT in args.output.parents:
        parser.error('Output must be new and outside checkout')
    if any(',' in str(path) for path in [args.archive, args.old_archive, args.output]):
        parser.error('Docker mount paths cannot contain commas')
    lock = json.loads((ROOT / 'tests/container-images.json').read_text())
    image = lock['hosts'][args.host]['image']
    if not re.fullmatch('sha256:[a-f0-9]{64}', image): parser.error('Invalid image lock')
    proxies = [key for key in os.environ if key.lower() in {'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy'}]
    for key in proxies:
        if key.lower() != 'no_proxy' and (urlsplit(os.environ[key]).username or urlsplit(os.environ[key]).password):
            parser.error('Authenticated proxies are outside this runner')
    resources=resource_preflight(args.output)
    actual = subprocess.check_output(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'], text=True).strip()
    if actual != image: raise RuntimeError('Locked image identity mismatch')
    args.output.mkdir(parents=True)
    script = args.output / 'runner.py'; script.write_bytes(Path(__file__).read_bytes())
    token=uuid.uuid4().hex
    name = 'planweft-project-isolation-' + token
    command = ['docker', 'run', '--rm', '--name', name, '--read-only', '--user', f'{os.getuid()}:{os.getgid()}',
               '--label','planweft.isolation-run='+token,
               '--cap-drop=ALL', '--security-opt=no-new-privileges', '--cpus=2', '--memory=3g',
               '--memory-swap=3g', '--pids-limit=256', '--network=host', '--tmpfs', '/tmp:mode=1777,size=512m',
               '--mount', f'type=bind,src={script},dst=/runner/run.py,readonly',
               '--mount', f'type=bind,src={args.output},dst=/evidence',
               '--mount', f'type=bind,src={args.archive},dst=/input/new.tgz,readonly',
               '--mount', f'type=bind,src={args.old_archive},dst=/input/old.tgz,readonly',
               *[item for key in proxies for item in ['-e', key]], '--entrypoint', 'python3', image,
               '/runner/run.py', '--worker', '--host', args.host, '--archive', '/input/new.tgz',
               '--sha256', args.sha256, '--old-archive', '/input/old.tgz', '--old-sha256', args.old_sha256,
               '--output', '/evidence', '--timeout', str(args.timeout)]
    result = None
    error = None
    remaining = 'unverified'
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=args.timeout)
        (args.output / 'container.log').write_text(result.stdout + result.stderr)
    except subprocess.TimeoutExpired as exc:
        error='TimeoutExpired'
        def text(value): return value.decode(errors='replace') if isinstance(value,bytes) else value or ''
        (args.output / 'container.log').write_text(text(exc.stdout)+text(exc.stderr))
    finally:
        cleanup=cleanup_owned(name,token)
        remaining=not cleanup['container_removed']
        save(args.output / 'container.json', {'image': image, 'runner_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
             'status':'Passed' if result and result.returncode==0 and not remaining else 'Failed',
             'exit_code': result.returncode if result else None, 'container_removed': not remaining,
             'credentials_mounted': False, 'network': 'host network and existing credential-free proxy',
             'resource_preflight':resources,'timeout_seconds':args.timeout,'error':error,'cleanup':cleanup})
    return 1 if remaining or result is None else result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
