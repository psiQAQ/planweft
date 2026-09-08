#!/usr/bin/env python3
"""Run an authorized native CLI lifecycle in a disposable user profile, without models.

Uses synthetic A (0.3.0) and B (0.3.1) copies of the reviewed distribution.
Local replacement is not evidence of a public Git or npm update channel.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
HOSTS = ('codex', 'claude', 'gemini', 'pi')
PRODUCT = 'program-design'
CATALOGS = {'codex': '.agents/plugins/marketplace.json',
            'claude': '.claude-plugin/marketplace.json'}
MANIFESTS = {'codex': '.codex-plugin/plugin.json', 'claude': '.claude-plugin/plugin.json',
             'gemini': 'gemini-extension.json', 'pi': 'package.json'}
RECORDS = {'task_plan.md': '# User plan\n- **Status:** in_progress\n',
           'findings.md': 'Existing findings.\n', 'progress.md': 'Existing progress.\n',
           'user-note.txt': 'Uncommitted user note.\n',
           'docs/specs/approved.md': '# Approved specification\n\nStatus: approved\nRequirement: preserve existing user records during plugin maintenance.\n',
           'docs/adr/decision.md': '# Accepted decision\n\nStatus: accepted\nDecision: native plugin lifecycle operations must not rewrite project decisions.\n',
           'docs/reproduction/known.md': '# Existing reproduction\n\nResult: Passed\nEvidence: this approved fixture remains unchanged across install, update and removal.\n'}


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def inventory(directory):
    files = {}
    for path in directory.rglob('*'):
        if path.is_symlink():
            files[path.relative_to(directory).as_posix()] = {'symlink': os.readlink(path)}
        elif path.is_file():
            files[path.relative_to(directory).as_posix()] = {
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'executable': bool(path.stat().st_mode & 0o111)}
        elif path.is_dir():
            continue
        else:
            raise RuntimeError('unsupported filesystem entry: ' + str(path))
    return files


def isolated_environment(profile):
    """Only process discovery/locale is inherited; no credentials or personal config."""
    env = {name: os.environ[name] for name in ('PATH', 'LANG', 'LC_ALL') if name in os.environ}
    env.update(HOME=str(profile), USERPROFILE=str(profile),
               CODEX_HOME=str(profile / '.codex'), CLAUDE_CONFIG_DIR=str(profile / '.claude'),
               PI_CODING_AGENT_DIR=str(profile / '.pi/agent'),
               XDG_CONFIG_HOME=str(profile / '.config'), XDG_CACHE_HOME=str(profile / '.cache'),
               XDG_DATA_HOME=str(profile / '.local/share'), XDG_STATE_HOME=str(profile / '.local/state'),
               TMPDIR=str(profile / 'tmp'), GIT_CONFIG_GLOBAL=str(profile / 'gitconfig'),
               GIT_CONFIG_NOSYSTEM='1', GIT_TERMINAL_PROMPT='0',
               npm_config_cache=str(profile / '.npm-cache'),
               npm_config_userconfig=str(profile / 'npmrc'),
               npm_config_globalconfig=str(profile / 'npm-globalrc'),
               npm_config_ignore_scripts='true', npm_config_audit='false', npm_config_fund='false',
               npm_config_offline='true', NO_COLOR='1', CI='1', TERM='dumb',
               PI_OFFLINE='1', PI_TELEMETRY='0', DISABLE_TELEMETRY='1',
               DISABLE_ERROR_REPORTING='1', DISABLE_AUTOUPDATER='1',
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1', PYTHONDONTWRITEBYTECODE='1')
    for relative in ['.codex', '.claude', '.pi/agent', '.config', '.cache',
                     '.local/share', '.local/state', 'tmp']:
        (profile / relative).mkdir(parents=True, exist_ok=True)
    for name in ['gitconfig', 'npmrc', 'npm-globalrc']:
        (profile / name).write_text('')
    return env


def positive_timeout(value):
    try:
        result = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError('timeout must be an integer between 1 and 300') from error
    if not 1 <= result <= 300:
        raise argparse.ArgumentTypeError('timeout must be between 1 and 300')
    return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, choices=HOSTS)
    parser.add_argument('--cli', required=True, type=Path, help='Already installed official CLI executable')
    parser.add_argument('--output', required=True, type=Path, help='New evidence directory outside the repository')
    parser.add_argument('--timeout', type=positive_timeout, default=120)
    args = parser.parse_args(argv)
    args.cli = args.cli.expanduser().resolve()
    args.output = args.output.expanduser().resolve()
    if not args.cli.is_file() or not os.access(args.cli, os.X_OK):
        parser.error('--cli must be an existing executable; this runner does not install CLIs')
    if args.output == ROOT or ROOT in args.output.parents:
        parser.error('--output must be outside the repository')
    if args.output.exists():
        parser.error('--output already exists; refusing to overwrite evidence')
    return args


def fixture_version(source, destination, host, version):
    shutil.copytree(source, destination)
    manifest = destination / MANIFESTS[host]
    payload = json.loads(manifest.read_text())
    payload['version'] = version
    save(manifest, payload)
    # Markers are placed in real Skill resources so npm's files allowlist is exercised.
    resource = destination / ('references' if host == 'pi' else 'skills/project-docs/references')
    resource.mkdir(parents=True, exist_ok=True)
    (resource / 'pd-lifecycle-change.txt').write_text(version + '\n')
    marker = 'pd-lifecycle-delete.txt' if version == '0.3.0' else 'pd-lifecycle-add.txt'
    (resource / marker).write_text('Synthetic lifecycle fixture ' + version + '\n')
    return inventory(destination)


def compare_installed(installed, expected, removed=()):
    actual = inventory(installed)
    mismatches = [path for path, value in expected.items() if actual.get(path) != value]
    stale = [path for path in removed if path in actual]
    return {'installed_path': str(installed), 'checked_files': len(expected),
            'mismatches': mismatches, 'stale_removed_files': stale,
            'extra_files': sorted(set(actual) - set(expected)),
            'status': 'Passed' if not mismatches and not stale else 'Failed'}


class Lifecycle:
    def __init__(self, args, scratch):
        self.args = args
        self.scratch = scratch
        self.profile = scratch / 'isolated-home'
        self.env = isolated_environment(self.profile)
        self.project = scratch / '项目 user work'
        self.project.mkdir()
        for name, text in RECORDS.items():
            target = self.project / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        self.project_before = inventory(self.project)
        self.live = scratch / 'marketplace'
        self.source = self.live / 'dist' / args.host / PRODUCT
        self.commands = []
        self.summary = {'host': args.host, 'status': 'Failed', 'checks': {},
                        'scope': 'disposable user profile; fresh CLI process for every command',
                        'synthetic_versions': ['0.3.0', '0.3.1'],
                        'model_calls': 'Not Run: lifecycle commands only; no authentication inherited',
                        'remote_channel': 'Not Run: local source/tarball only; no public release is assumed',
                        'live_session_reload': 'Not Run: listing uses a fresh CLI process',
                        'network_isolation': 'minimal environment and offline npm/Pi flags; not an OS network sandbox'}
        self.installed = False
        self.pi_sources = {}

    def command(self, label, arguments, required=True, executable=None, cwd=None, input_text=None):
        command = [str(executable or self.args.cli), *arguments]
        print(json.dumps({'stage': label, 'event': 'start'}), flush=True)
        started = time.monotonic()
        try:
            input_options = {'input': input_text} if input_text is not None else {'stdin': subprocess.DEVNULL}
            result = subprocess.run(command, cwd=cwd or self.project, env=self.env,
                                    **input_options, text=True, capture_output=True,
                                    timeout=self.args.timeout)
            evidence = {'argv': command, 'exit_code': result.returncode,
                        'stdout': result.stdout, 'stderr': result.stderr}
        except subprocess.TimeoutExpired as error:
            evidence = {'argv': command, 'exit_code': None, 'timed_out': True,
                        'stdout': (error.stdout or b'').decode(errors='replace') if isinstance(error.stdout, bytes) else error.stdout,
                        'stderr': (error.stderr or b'').decode(errors='replace') if isinstance(error.stderr, bytes) else error.stderr}
        except OSError as error:
            evidence = {'argv': command, 'exit_code': None, 'stdout': '', 'stderr': str(error)}
        evidence['elapsed_seconds'] = round(time.monotonic() - started, 3)
        evidence['cwd'] = str(cwd or self.project)
        if input_text is not None:
            evidence['stdin'] = input_text
        self.commands.append({'stage': label, **evidence})
        save(self.args.output / 'commands' / (label + '.json'), evidence)
        print(json.dumps({'stage': label, 'exit_code': evidence['exit_code']}), flush=True)
        if required and evidence['exit_code'] != 0:
            raise RuntimeError('native command failed: ' + label)
        return evidence

    def publish_local_fixture(self, fixture):
        if self.source.exists():
            shutil.rmtree(self.source)
        shutil.copytree(fixture, self.source)
        if self.args.host in CATALOGS:
            relative = CATALOGS[self.args.host]
            catalog = json.loads((ROOT / relative).read_text())
            catalog['plugins'] = [entry for entry in catalog['plugins'] if entry.get('name') == PRODUCT]
            if len(catalog['plugins']) != 1:
                raise RuntimeError('expected one reviewed marketplace entry')
            version = json.loads((fixture / MANIFESTS[self.args.host]).read_text())['version']
            if 'version' in catalog['plugins'][0]:
                catalog['plugins'][0]['version'] = version
            save(self.live / relative, catalog)
            self.marketplace = catalog['name']
            self.plugin_id = PRODUCT + '@' + self.marketplace

    def prepare_pi_tarball(self, fixture, version):
        npm = shutil.which('npm')
        if not npm:
            raise RuntimeError('npm is required to verify the actual Pi tarball')
        destination = self.args.output / 'npm'
        destination.mkdir(exist_ok=True)
        result = self.command('npm-pack-' + version, ['pack', '--ignore-scripts', '--json',
                              '--pack-destination', str(destination)], executable=npm, cwd=fixture)
        details = json.loads(result['stdout'])
        tarball = destination / details[0]['filename']
        expected = {}
        with tarfile.open(tarball, 'r:gz') as archive:
            for member in archive:
                if not member.isfile():
                    raise RuntimeError('unsupported npm archive entry: ' + member.name)
                path = Path(member.name)
                if path.is_absolute() or '..' in path.parts or path.parts[0] != 'package':
                    raise RuntimeError('unsafe npm archive entry: ' + member.name)
                expected[path.relative_to('package').as_posix()] = {
                    'sha256': hashlib.sha256(archive.extractfile(member).read()).hexdigest(),
                    'executable': bool(member.mode & 0o111)}
        package = json.loads((fixture / 'package.json').read_text())
        required = [*package['pi']['skills'], *package['pi']['extensions'], 'LICENSE', 'UPSTREAM.json',
                    'templates/task_plan.md', 'scripts/init-session.sh', 'references/pd-lifecycle-change.txt']
        missing = [path for path in required if path not in expected]
        if missing:
            raise RuntimeError('Pi npm tarball omits required assets: ' + ', '.join(missing))
        self.pi_sources[version] = 'npm:' + package['name'] + '@file:' + str(tarball)
        save(self.args.output / ('npm-' + version + '.json'), {
            'tarball': tarball.name, 'sha256': hashlib.sha256(tarball.read_bytes()).hexdigest(),
            'files': expected, 'source': self.pi_sources[version]})
        return expected

    def install(self, label, version):
        host = self.args.host
        if host == 'codex':
            self.command(label, ['plugin', 'add', self.plugin_id, '--json'])
        elif host == 'claude':
            self.command(label, ['plugin', 'install', self.plugin_id, '--scope', 'user'])
        elif host == 'gemini':
            # --consent covers extension permissions; local sources additionally
            # ask for folder trust. This answer is limited to our reviewed fixture.
            self.command(label, ['extensions', 'install', str(self.source), '--consent', '--skip-settings'],
                         input_text='y\n')
        else:
            self.command(label, ['install', self.pi_sources[version]])
        self.installed = True

    def update(self):
        host = self.args.host
        if host == 'codex':
            self.command('replace-with-B', ['plugin', 'add', self.plugin_id, '--json'])
            self.summary['update_route'] = 'local marketplace source replacement, then native plugin add'
        elif host == 'claude':
            self.command('refresh-marketplace', ['plugin', 'marketplace', 'update', self.marketplace])
            self.command('update-to-B', ['plugin', 'update', self.plugin_id, '--scope', 'user'])
            self.summary['update_route'] = 'native marketplace update and plugin update from a local source'
        elif host == 'gemini':
            self.command('update-to-B', ['extensions', 'update', PRODUCT], input_text='y\n')
            self.summary['update_route'] = 'native extensions update from its recorded local source'
        else:
            self.command('replace-with-B', ['install', self.pi_sources['0.3.1']])
            self.summary['update_route'] = 'native install of a new npm tarball source for the same package name'

    def list_installed(self, label):
        args = {'codex': ['plugin', 'list', '--json'], 'claude': ['plugin', 'list', '--json'],
                'gemini': ['extensions', 'list'], 'pi': ['list']}[self.args.host]
        return self.command(label, args)

    def installed_path(self, version):
        host = self.args.host
        if host == 'pi':
            root = self.profile / '.pi/agent/npm/node_modules/program-design'
            candidates = [root] if root.is_dir() else []
        elif host == 'gemini':
            root = self.profile / '.gemini/extensions/program-design'
            candidates = [root] if root.is_dir() else []
        else:
            cache = self.profile / ('.codex/plugins/cache' if host == 'codex' else '.claude/plugins/cache')
            candidates = [manifest.parent.parent for manifest in cache.rglob(MANIFESTS[host])
                          if json.loads(manifest.read_text()).get('version') == version]
        if len(candidates) != 1:
            raise RuntimeError('expected exactly one installed ' + version + ' package, got ' + str(candidates))
        return candidates[0]

    def verify(self, label, version, expected, removed=()):
        self.list_installed('list-' + label)
        result = compare_installed(self.installed_path(version), expected, removed)
        result['project_unchanged'] = inventory(self.project) == self.project_before
        if not result['project_unchanged']:
            result['status'] = 'Failed'
        save(self.args.output / ('verify-' + label + '.json'), result)
        self.summary['checks'][label] = result
        if result['status'] != 'Passed':
            raise RuntimeError('installed bytes, removed files or project preservation failed: ' + label)
        if self.args.host == 'codex':
            self.codex_discovery(label, Path(result['installed_path']))

    def codex_discovery(self, label, installed):
        """Observe native Skill discovery without authentication or a model turn."""
        protocol, inbox = [], queue.Queue()
        with tempfile.TemporaryFile(mode='w+') as errors:
            process = subprocess.Popen([str(self.args.cli), 'app-server'], cwd=self.project,
                env=self.env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors, text=True)
            def read_events():
                for line in process.stdout:
                    try:
                        inbox.put(json.loads(line))
                    except json.JSONDecodeError:
                        inbox.put({'unparsed': line})
            threading.Thread(target=read_events, daemon=True).start()
            def request(request_id, method, params):
                process.stdin.write(json.dumps({'id': request_id, 'method': method, 'params': params}) + '\n')
                process.stdin.flush()
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    event = inbox.get(timeout=max(0.1, deadline - time.monotonic()))
                    protocol.append(event)
                    if event.get('id') == request_id:
                        return event
                raise RuntimeError('native Skill discovery timed out')
            response = {}
            try:
                initialized = request(1, 'initialize', {'clientInfo': {
                    'name': 'program-design-native-lifecycle', 'version': '0.3.0'},
                    'capabilities': {'experimentalApi': True}})
                if 'error' in initialized:
                    raise RuntimeError('native app-server initialization failed')
                process.stdin.write(json.dumps({'method': 'initialized', 'params': {}}) + '\n')
                process.stdin.flush()
                response = request(2, 'skills/list', {'cwds': [str(self.project)]})
            except queue.Empty as error:
                raise RuntimeError('native Skill discovery timed out') from error
            finally:
                process.stdin.close()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                process.stdout.close()
                errors.seek(0)
                save(self.args.output / ('skills-' + label + '.json'), {
                    'response': response, 'protocol': protocol, 'stderr': errors.read(),
                    'limitation': 'skills/list observes loading; it does not expose implicit invocation policy'})
        rows = response.get('result', {}).get('data', [])
        skills = [skill for row in rows for skill in row.get('skills', [])
                  if skill.get('pluginId') == self.plugin_id]
        expected_names = {'program-design:project-docs',
                          *{'program-design:project-docs-' + lang for lang in ['ar', 'de', 'es', 'zh', 'zht']}}
        if (len(skills) != 6 or set(skill.get('name') for skill in skills) != expected_names
                or any(row.get('errors') for row in rows)
                or not all(skill.get('enabled') is True and skill.get('scope') == 'user'
                           and str(skill.get('path', '')).startswith(str(installed) + '/') for skill in skills)):
            raise RuntimeError('native Skill discovery did not load the reviewed Codex entries')
        self.summary['checks']['discovery-' + label] = {'status': 'Passed', 'skills': len(skills),
            'implicit_invocation_policy': 'Not Verified: not exposed by skills/list'}

    def uninstall(self, label, version, required=True):
        host = self.args.host
        args = {'codex': ['plugin', 'remove', getattr(self, 'plugin_id', PRODUCT), '--json'],
                'claude': ['plugin', 'uninstall', getattr(self, 'plugin_id', PRODUCT), '--scope', 'user'],
                'gemini': ['extensions', 'uninstall', PRODUCT],
                'pi': ['remove', self.pi_sources.get(version, 'npm:program-design')]}[host]
        self.command(label, args, required=required)
        self.installed = False

    def run(self):
        self.command('cli-version', ['--version'])
        self.command('lifecycle-help', ['extensions' if self.args.host == 'gemini' else
                                      'install' if self.args.host == 'pi' else 'plugin', '--help'])
        manifest = json.loads((ROOT / 'dist/manifest.json').read_text())
        item = manifest['platforms'][self.args.host]
        original = ROOT / 'dist' / self.args.host / PRODUCT
        actual = inventory(original)
        digest = hashlib.sha256(json.dumps(actual, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if (manifest.get('schema_version') != 2 or manifest.get('version') != '0.3.0'
                or item['path'] != self.args.host + '/' + PRODUCT or actual != item['files']
                or len(actual) != item['file_count'] or digest != item['sha256']):
            raise RuntimeError('source distribution differs from the reviewed manifest')
        self.summary['source_sha256'] = digest
        fixtures, expected = {}, {}
        for version in ['0.3.0', '0.3.1']:
            fixtures[version] = self.scratch / ('fixture-' + version)
            expected[version] = fixture_version(original, fixtures[version], self.args.host, version)
            if self.args.host == 'pi':
                expected[version] = self.prepare_pi_tarball(fixtures[version], version)
            save(self.args.output / ('fixture-' + version + '.json'), expected[version])
        self.publish_local_fixture(fixtures['0.3.0'])
        if self.args.host in CATALOGS:
            args = ['plugin', 'marketplace', 'add', str(self.live)]
            self.command('register-marketplace', args + (['--json'] if self.args.host == 'codex' else []))
        self.install('install-A', '0.3.0')
        self.verify('A', '0.3.0', expected['0.3.0'])
        self.publish_local_fixture(fixtures['0.3.1'])
        self.update()
        self.verify('B', '0.3.1', expected['0.3.1'], set(expected['0.3.0']) - set(expected['0.3.1']))
        self.uninstall('remove-before-rollback', '0.3.1')
        self.publish_local_fixture(fixtures['0.3.0'])
        if self.args.host == 'claude':
            self.command('refresh-for-rollback', ['plugin', 'marketplace', 'update', self.marketplace])
        self.install('rollback-to-A', '0.3.0')
        self.verify('rollback-A', '0.3.0', expected['0.3.0'], set(expected['0.3.1']) - set(expected['0.3.0']))
        self.uninstall('uninstall', '0.3.0')
        listing = self.list_installed('list-after-uninstall')
        if self.args.host == 'claude':
            active = json.loads(listing['stdout'])
            if self.plugin_id in json.dumps(active):
                raise RuntimeError('uninstalled Claude plugin is still registered')
        else:
            cache = self.profile / { 'codex': '.codex/plugins/cache',
                'gemini': '.gemini/extensions', 'pi': '.pi/agent/npm/node_modules'}[self.args.host]
            remaining = [path for path in cache.rglob(MANIFESTS[self.args.host])
                         if json.loads(path.read_text()).get('name') == PRODUCT]
            if remaining:
                raise RuntimeError('native uninstall retained the active package: ' + str(remaining))
        self.summary['checks']['uninstall'] = {'status': 'Passed',
            'remaining_profile_cache': sorted(path for path in inventory(self.profile)
                                               if PRODUCT in path and 'cache' in path)}
        self.summary['status'] = 'Passed'

    def cleanup(self):
        if self.installed:
            self.uninstall('failure-cleanup', '0.3.1', required=False)
        if self.args.host in CATALOGS and hasattr(self, 'marketplace'):
            result = self.command('unregister-marketplace',
                                  ['plugin', 'marketplace', 'remove', self.marketplace], required=False)
            if result['exit_code'] != 0:
                self.summary['status'] = 'Failed'
                self.summary['cleanup_error'] = 'native marketplace removal failed'
        self.summary['project_unchanged'] = inventory(self.project) == self.project_before
        if not self.summary['project_unchanged']:
            self.summary['status'] = 'Failed'
        save(self.args.output / 'project-before.json', self.project_before)
        save(self.args.output / 'project-after.json', inventory(self.project))
        save(self.args.output / 'commands.json', self.commands)


def main(argv=None):
    args = parse_args(argv)
    runner_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.mkdir(parents=True)
    shutil.copy2(Path(__file__), args.output / 'runner.py')
    lifecycle = None
    with tempfile.TemporaryDirectory(prefix='pd-native-lifecycle-') as temporary:
        scratch = Path(temporary)
        lifecycle = Lifecycle(args, scratch)
        try:
            lifecycle.run()
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            lifecycle.summary['error'] = str(error)
        finally:
            lifecycle.cleanup()
    lifecycle.summary['temporary_profile_removed'] = not scratch.exists()
    lifecycle.summary['cli'] = str(args.cli)
    lifecycle.summary['runner_sha256'] = runner_digest
    save(args.output / 'summary.json', lifecycle.summary)
    print(json.dumps({'host': args.host, 'status': lifecycle.summary['status'],
                      'checks': {name: value['status'] for name, value in lifecycle.summary['checks'].items()},
                      'error': lifecycle.summary.get('error'), 'evidence': str(args.output)}, ensure_ascii=False), flush=True)
    return 0 if lifecycle.summary['status'] == 'Passed' else 1


if __name__ == '__main__':
    sys.exit(main())
