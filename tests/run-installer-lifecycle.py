#!/usr/bin/env python3
"""Exercise the unified installer with real npm artifacts and isolated native CLIs.

No personal authentication is read. --cli-dir adds already installed host binaries.
Evidence stays outside the checkout; this runner does not invoke models.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]

def validate_archive(path):
    # Python 3.11 in the locked images has no extraction-filter parameter.
    # Accept only regular package members, before creating any output.
    with tarfile.open(path) as archive:
        names = set()
        for member in archive:
            name = Path(member.name)
            if (name.is_absolute() or '..' in name.parts or not name.parts
                    or name.parts[0] != 'package' or member.name in names
                    or not (member.isfile() or member.isdir())):
                raise ValueError('Unsafe or duplicate package archive member')
            names.add(member.name)
        package = json.load(archive.extractfile('package/package.json'))
        if package.get('name') != 'planweft' or not isinstance(package.get('version'), str):
            raise ValueError('Expected a versioned planweft package')
    return package


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--host', choices=['agents', 'codex', 'claude', 'pi', 'opencode', 'dsh'], required=True)
    parser.add_argument('--cli-dir', type=Path, action='append', default=[])
    args = parser.parse_args(argv)
    out = args.output.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents:
        parser.error('--output must be new and outside the checkout')
    try:
        validate_archive(args.archive)
        if any(not path.is_dir() for path in args.cli_dir):
            raise ValueError('--cli-dir must be an existing directory')
    except (OSError, ValueError, KeyError, tarfile.TarError) as error:
        parser.error(str(error))
    out.mkdir(parents=True)
    home, project = out / 'profile', out / '项目 with spaces'
    home.mkdir(); project.mkdir()
    protected = {'task_plan.md': 'approved plan\r\n', 'findings.md': 'known facts\n',
                 'progress.md': 'previous progress\n', 'docs/spec.md': 'approved requirements\n'}
    for name, value in protected.items():
        p = project / name; p.parent.mkdir(exist_ok=True); p.write_bytes(value.encode())
    env = {k: v for k, v in os.environ.items() if k in {'PATH', 'SYSTEMROOT', 'WINDIR', 'HTTPS_PROXY', 'HTTP_PROXY', 'ALL_PROXY', 'NO_PROXY', 'https_proxy', 'http_proxy', 'all_proxy', 'no_proxy'}}
    env.update(HOME=str(home), USERPROFILE=str(home), XDG_CONFIG_HOME=str(home / '.config'),
               XDG_DATA_HOME=str(home / '.local/share'), XDG_CACHE_HOME=str(home / '.cache'),
               DSH_HOME=str(home / '.dsh'), CODEX_HOME=str(home / '.codex'), CLAUDE_CONFIG_DIR=str(home / '.claude'),
               PI_CODING_AGENT_DIR=str(home / '.pi/agent'), npm_config_cache=str(out / 'npm-cache'),
               npm_config_userconfig=os.devnull, PLANNING_DISABLED='1',
               PATH=os.pathsep.join([*map(str, args.cli_dir), env['PATH']]))
    records = []
    def run(label, argv, cwd=project, input_data='y\ny\ny\n'):
        p = subprocess.run(argv, cwd=cwd, env=env, input=input_data, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=240)
        (out / (label + '.log')).write_text(p.stdout + p.stderr)
        records.append({'step': label, 'argv': argv, 'exit_code': p.returncode})
        (out / 'summary.json').write_text(json.dumps({'status': 'In Progress', 'host': args.host, 'commands': records}, indent=2))
        if p.returncode: raise RuntimeError(label + ' failed; see ' + str(out / (label + '.log')))
        return p.stdout
    # Start with the real packed bytes, then derive a clearly local test version.
    a = out / 'A'; a.mkdir()
    validate_archive(args.archive)
    with tarfile.open(args.archive) as tar: tar.extractall(a)
    a = a / 'package'
    import shutil
    b = out / 'B/package'; shutil.copytree(a, b)
    original = json.loads((a / 'package.json').read_text())['version']
    # Local fixtures must work for every candidate and never impersonate the
    # next real published version.
    next_version = original + ('.fixture.1' if '-' in original else '-fixture.1')
    for p in b.rglob('*'):
        if not p.is_file(): continue
        try: text = p.read_bytes().decode('utf-8')
        except UnicodeDecodeError: continue
        p.write_bytes(text.replace(original, next_version).encode())
    # Actual payload delta affects installed resources, not just manifest version.
    for package, version in [(a, 'A'), (b, 'B')]:
        for host in ['agents', 'codex', 'claude', 'pi', 'opencode', 'dsh']:
            platform = package / 'dist' / host / 'planweft'
            skill = platform if host == 'pi' else platform / 'skills/project-docs'
            (skill / 'lifecycle-changed.txt').write_text(version)
            (skill / ('lifecycle-removed.txt' if version == 'A' else 'lifecycle-added.txt')).write_text(version)
    archives = {}
    for label, package in [('A', a), ('B', b)]:
        result = json.loads(run('pack-' + label, ['npm', 'pack', '--ignore-scripts', '--json', '--pack-destination', str(out)], package))
        archives[label] = out / result[0]['filename']
    scope = ['--global'] if args.host in ['codex', 'dsh'] else ['--approve-pi-project'] if args.host == 'pi' else []
    def invoke(label, package, action, source=None):
        argv = ['node', str(package / 'bin/planweft.mjs'), action, '-a', args.host, *scope]
        if source: argv += ['--source', str(source)]
        return run(label, argv)
    def verify(label, version, marker):
        state_dir = home / '.local/share/planweft' if args.host in ['codex', 'dsh'] else project / '.planweft'
        rec = json.loads((state_dir / 'installations.json').read_text())['agents'][args.host]
        package_root = Path(rec['packageRoot'])
        if args.host == 'dsh':
            manifest = json.loads((home / '.dsh/profiles/headless/package.json').read_text())
            if manifest['dsh']['profile']['bundles'].count('planweft') != 1: raise RuntimeError('DSH bundle was not registered once')
            linked = (home / '.dsh/profiles/headless/node_modules/planweft').resolve()
            if linked != package_root: raise RuntimeError('DSH native link selects the wrong version')
            composed = run('native-config-' + label, ['dsh', '--profile', 'headless', '--dump-config'])
            if 'planweft/dsh' not in composed and '/dist/dsh/planweft/index.mjs' not in composed: raise RuntimeError('DSH did not compose the native bundle')
            skill = linked / 'dist/dsh/planweft/skills/project-docs'
        elif args.host in ['codex', 'claude']:
            manifest_name = '.codex-plugin/plugin.json' if args.host == 'codex' else '.claude-plugin/plugin.json'
            cache = home / ('.codex/plugins/cache' if args.host == 'codex' else '.claude/plugins/cache')
            candidates = [p.parent.parent for p in cache.rglob(manifest_name) if json.loads(p.read_text()).get('version') == version]
            if len(candidates) != 1: raise RuntimeError('Expected one actual native cache for ' + version)
            skill = candidates[0] / 'skills/project-docs'
        elif args.host == 'pi':
            skill = package_root / 'dist/pi/planweft'
            listing = run('native-list-' + label, ['pi', 'list', '--approve'])
            if str(skill) not in listing: raise RuntimeError('Pi did not register the exact version source')
            # RPC command discovery loads the actual Extension without a model call.
            proc = subprocess.Popen(['pi', '--mode', 'rpc', '--no-session', '--approve'], cwd=project, env=env,
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                stdout, stderr = proc.communicate('{"id":"planweft-discovery","type":"get_commands"}\n', timeout=20)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try: stdout, stderr = proc.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill(); stdout, stderr = proc.communicate()
            (out / ('native-rpc-' + label + '.log')).write_text(stdout + stderr)
            replies = [json.loads(line) for line in stdout.splitlines() if line.startswith('{')]
            reply = next((x for x in replies if x.get('id') == 'planweft-discovery'), {})
            commands = reply.get('data', {}).get('commands', [])
            if not reply.get('success') or sum(c.get('name') == 'pw-plan-status' for c in commands) != 1:
                raise RuntimeError('Pi did not load exactly one PlanWeft Extension')
        else:
            skill = project / ('.opencode/skills/project-docs' if args.host == 'opencode' else '.agents/skills/project-docs')
        if (skill / 'lifecycle-changed.txt').read_text() != marker: raise RuntimeError('Installed changed file differs')
        present, absent = ('removed', 'added') if marker == 'A' else ('added', 'removed')
        if not (skill / ('lifecycle-' + present + '.txt')).exists() or (skill / ('lifecycle-' + absent + '.txt')).exists(): raise RuntimeError('Installed additions/deletions differ')
        if args.host == 'opencode':
            # Local non-model provider keeps debug discovery from selecting a real service.
            config = {'autoupdate': False, 'model': 'pw-fixture/never-call', 'enabled_providers': ['pw-fixture'],
                'provider': {'pw-fixture': {'npm': '@ai-sdk/openai-compatible',
                    'options': {'baseURL': 'http://127.0.0.1:1/v1', 'apiKey': 'fixture-not-a-credential'},
                    'models': {'never-call': {'name': 'Never called'}}}}}
            (project / 'opencode.json').write_text(json.dumps(config))
            agent = json.loads(run('native-tools-' + label, ['opencode', 'debug', 'agent', 'build']))
            if not all(agent.get('tools', {}).get(n) is True for n in ['pw_init', 'pw_status', 'pw_check']): raise RuntimeError('OpenCode did not load all tools')
            skills = json.loads(run('native-skills-' + label, ['opencode', 'debug', 'skill']))
            if sum(item.get('name') == 'project-docs' for item in skills) != 1: raise RuntimeError('OpenCode main Skill discovery differs')
        records.append({'step': 'verify-' + label, 'status': 'Passed', 'installed_skill': str(skill)})
    try:
        invoke('install-A', a, 'add', archives['A'])
        invoke('doctor-A', a, 'doctor')
        verify('A', original, 'A')
        invoke('update-B', b, 'update', archives['B'])
        invoke('doctor-B', b, 'doctor')
        verify('B', next_version, 'B')
        invoke('rollback-A', a, 'update', archives['A'])
        invoke('doctor-rollback', a, 'doctor')
        verify('rollback', original, 'A')
        invoke('remove', a, 'remove')
        invoke('reinstall-A', a, 'add', archives['A'])
        invoke('remove-again', a, 'remove')
        for name, value in protected.items():
            if (project / name).read_bytes() != value.encode(): raise RuntimeError('Project record changed: ' + name)
        status = 'Passed'
    except Exception as error:
        status = 'Failed'; records.append({'error': str(error)})
    (out / 'summary.json').write_text(json.dumps({'status': status, 'host': args.host, 'commands': records,
        'input_archive_sha256': hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        'model_session': 'Not Run: installer lifecycle only', 'project_records_unchanged': all((project / n).read_bytes() == v.encode() for n,v in protected.items())}, indent=2))
    print(json.dumps({'status': status, 'output': str(out)}))
    if status != 'Passed': raise SystemExit(1)

if __name__ == '__main__': main()
