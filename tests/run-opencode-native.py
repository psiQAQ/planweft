#!/usr/bin/env python3
"""Exercise OpenCode V1's real local plugin/Skill loader and debug tools, without a model."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pd_native_lifecycle', ROOT / 'tests/run-native-lifecycle.py')
COMMON = importlib.util.module_from_spec(spec)
spec.loader.exec_module(COMMON)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cli', required=True, type=Path)
    parser.add_argument('--package', type=Path, default=ROOT / 'dist/opencode/program-design')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(argv)
    args.cli, args.package, args.output = (path.expanduser().resolve()
                                         for path in (args.cli, args.package, args.output))
    if not args.cli.is_file() or not os.access(args.cli, os.X_OK):
        parser.error('--cli must name an already installed official executable')
    if not (args.package / 'dist/index.js').is_file() or not (args.package / 'package-lock.json').is_file():
        parser.error('--package must contain the prepared compiled package and dependency lock')
    if args.output == ROOT or ROOT in args.output.parents or args.output.exists():
        parser.error('--output must be a new directory outside the repository')
    return args


def verify_loaded_skill(skills, installed, source, version):
    """Check the host-reported path and resources, not merely a matching name."""
    selected = [skill for skill in skills if str(skill.get('name', '')).startswith('project-docs')]
    if (len(selected) != 1 or selected[0].get('name') != 'project-docs' or
            Path(selected[0].get('location', '')).resolve() != installed / 'SKILL.md' or
            ('PD_NATIVE_SKILL_' + version) not in json.dumps(selected)):
        raise RuntimeError('native Skill discovery did not load exactly the selected main Skill')
    if COMMON.inventory(installed) != COMMON.inventory(source):
        raise RuntimeError('host-loaded Skill resources differ from the selected package')
    if [path.relative_to(installed).as_posix() for path in installed.rglob('SKILL.md')] != ['SKILL.md']:
        raise RuntimeError('supporting language resources expose additional Skill entrypoints')
    languages = ['ar', 'de', 'es', 'zh', 'zht']
    for language in languages:
        base = installed / 'references/language-variants' / ('project-docs-' + language)
        for resource in ['GUIDE.md', 'scripts/check-complete.sh', 'templates/task_plan.md',
                         'references/evidence.md', 'LICENSE', 'UPSTREAM.json']:
            if not (base / resource).is_file():
                raise RuntimeError('host-loaded Skill is missing a language resource: ' +
                                   language + '/' + resource)
    return languages


def main(argv=None):
    args = parse_args(argv)
    args.output.mkdir(parents=True)
    shutil.copy2(__file__, args.output / 'runner.py')
    shutil.copy2(ROOT / 'tests/run-native-lifecycle.py', args.output / 'lifecycle-helper.py')
    before = COMMON.inventory(args.package)
    COMMON.save(args.output / 'source-files.json', before)
    summary = {'status': 'Failed', 'checks': {}, 'model_calls': 'Not Run: native debug commands only',
               'remote_npm': 'Not Run: local file URL loader; no published npm package is assumed',
               'update_route': 'local package/configuration switch with a fresh host process',
               'live_session_reload': 'Not Run', 'source': str(args.package)}
    with tempfile.TemporaryDirectory(prefix='pd-opencode-native-') as temporary:
        scratch = Path(temporary)
        profile = scratch / 'isolated-home'
        env = COMMON.isolated_environment(profile)
        env.update(OPENCODE_DISABLE_AUTOUPDATE='1', OPENCODE_DISABLE_MODELS_FETCH='1',
                   BUN_INSTALL_CACHE_DIR=str(profile / '.bun-cache'))
        project = scratch / '项目 有空格'
        project.mkdir()
        for name, content in COMMON.RECORDS.items():
            target = project / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        protected = {name: (project / name).read_bytes() for name in COMMON.RECORDS}
        COMMON.save(args.output / 'project-before.json', COMMON.inventory(project))
        commands = []

        def command(label, arguments, executable=None, cwd=project, install=False, required=True):
            command_env = dict(env)
            if install:
                command_env.pop('npm_config_offline', None)
                # Only the explicitly authorized dependency install inherits network routing.
                for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY'):
                    if key in os.environ:
                        command_env[key] = os.environ[key]
            argv = [str(executable or args.cli), *arguments]
            print(json.dumps({'stage': label, 'event': 'start'}), flush=True)
            try:
                result = subprocess.run(argv, cwd=cwd, env=command_env, stdin=subprocess.DEVNULL,
                                        text=True, capture_output=True, timeout=120)
                evidence = {'argv': argv, 'exit_code': result.returncode,
                            'stdout': result.stdout, 'stderr': result.stderr}
            except subprocess.TimeoutExpired as error:
                evidence = {'argv': argv, 'exit_code': None, 'timed_out': True,
                    'stdout': (error.stdout or b'').decode(errors='replace'),
                    'stderr': (error.stderr or b'').decode(errors='replace')}
            COMMON.save(args.output / 'commands' / (label + '.json'), evidence)
            commands.append({'label': label, **evidence})
            print(json.dumps({'stage': label, 'exit_code': evidence['exit_code']}), flush=True)
            if required and evidence['exit_code'] != 0:
                raise RuntimeError('native command failed: ' + label)
            return evidence

        def setup_project(directory, package):
            directory.mkdir(parents=True, exist_ok=True)
            config = {'$schema': 'https://opencode.ai/config.json', 'autoupdate': False,
                'model': 'pd-fixture/never-call', 'enabled_providers': ['pd-fixture'],
                'provider': {'pd-fixture': {'name': 'No-model lifecycle fixture',
                    'npm': '@ai-sdk/openai-compatible',
                    'options': {'baseURL': 'http://127.0.0.1:1/v1', 'apiKey': 'fixture-not-a-credential'},
                    'models': {'never-call': {'name': 'Never called'}}}}}
            COMMON.save(directory / 'opencode.json', config)
            loader = directory / '.opencode/plugins/program-design.ts'
            loader.parent.mkdir(parents=True, exist_ok=True)
            loader.write_text('export { PlanningWithFiles } from ' + json.dumps((package / 'dist/index.js').as_uri()) + '\n')
            skill = directory / '.opencode/skills/project-docs'
            if skill.exists():
                shutil.rmtree(skill)
            shutil.copytree(package / 'skills/project-docs', skill)

        def check(label, version):
            command('config-' + label, ['debug', 'config'])
            agent = json.loads(command('agent-' + label, ['debug', 'agent', 'build'])['stdout'])
            required = {'pd_init', 'pd_status', 'pd_check'}
            if not all(agent.get('tools', {}).get(name) is True for name in required):
                raise RuntimeError('native tool registry did not load the three pd_ tools')
            skills = json.loads(command('skills-' + label, ['debug', 'skill'])['stdout'])
            languages = verify_loaded_skill(skills, project / '.opencode/skills/project-docs',
                fixtures[version] / 'skills/project-docs', version)
            check_result = json.loads(command('check-' + label,
                ['debug', 'agent', 'build', '--tool', 'pd_check', '--params', '{}'])['stdout'])
            result = check_result['result']
            output = json.loads(result['output'] if isinstance(result, dict) else result)
            if output.get('plugin') != version:
                raise RuntimeError('native pd_check returned a stale plugin version')
            command('status-' + label, ['debug', 'agent', 'build', '--tool', 'pd_status', '--params', '{}'])
            if any(not (project / name).is_file() or (project / name).read_bytes() != content
                   for name, content in protected.items()):
                raise RuntimeError('read-only native debug tools changed project records')
            summary['checks'][label] = {'status': 'Passed', 'plugin_version': output['plugin'],
                                       'tools': sorted(required), 'main_skills': 1,
                                       'reachable_languages': languages,
                                       'skill_added_changed_removed': 'Passed: complete installed content matches the selected fixture'}

        try:
            summary['cli_version'] = command('cli-version', ['--version'])['stdout'].strip()
            command('debug-help', ['debug', 'agent', '--help'])
            fixtures = {}
            fixtures['0.3.0'] = scratch / 'package-A'
            shutil.copytree(args.package, fixtures['0.3.0'])
            npm = shutil.which('npm')
            if not npm:
                raise RuntimeError('npm executable unavailable')
            command('npm-ci', ['ci', '--omit=dev', '--ignore-scripts'], executable=npm,
                    cwd=fixtures['0.3.0'], install=True)
            fixtures['0.3.1'] = scratch / 'package-B'
            shutil.copytree(fixtures['0.3.0'], fixtures['0.3.1'])
            for version, package in fixtures.items():
                payload = json.loads((package / 'package.json').read_text())
                payload['version'] = version
                COMMON.save(package / 'package.json', payload)
                core = package / 'dist/core.js'
                core.write_text(core.read_text().replace('export const VERSION = "0.3.0"',
                                                         'export const VERSION = "' + version + '"', 1))
                skill = package / 'skills/project-docs/SKILL.md'
                skill.write_text(skill.read_text() + '\nPD_NATIVE_SKILL_' + version + '\n')
                # These belong to the copied Skill. The host-reported install
                # path must match the complete fixture, including no stale files.
                references = skill.parent / 'references'
                (references / 'pd-lifecycle-change.txt').write_text('Selected fixture: ' + version + '\n')
                exclusive = 'pd-lifecycle-delete.txt' if version == '0.3.0' else 'pd-lifecycle-add.txt'
                (references / exclusive).write_text('Only present in ' + version + '\n')
            inventories = {version: COMMON.inventory(package / 'skills/project-docs')
                           for version, package in fixtures.items()}
            first, second = inventories['0.3.0'], inventories['0.3.1']
            delta = {'added_in_B': sorted(set(second) - set(first)),
                     'removed_in_B': sorted(set(first) - set(second)),
                     'changed_in_B': sorted(name for name in set(first) & set(second)
                                            if first[name] != second[name])}
            if not all(delta.values()):
                raise RuntimeError('A/B Skill fixtures must contain added, changed and removed files')
            COMMON.save(args.output / 'skill-fixture-delta.json', delta)
            setup_project(project, fixtures['0.3.0'])
            command('paths', ['debug', 'paths'])
            check('A', '0.3.0')
            setup_project(project, fixtures['0.3.1'])
            check('B', '0.3.1')
            setup_project(project, fixtures['0.3.0'])
            check('rollback-A', '0.3.0')
            # A separate blank project proves pd_init reads the packaged template.
            package = fixtures['0.3.0']
            template = package / 'skills/project-docs/templates/task_plan.md'
            template.write_text(template.read_text() + '\nPD_BUNDLED_TEMPLATE_PROBE\n')
            blank = scratch / '独立 初始化项目'
            setup_project(blank, package)
            command('init', ['debug', 'agent', 'build', '--tool', 'pd_init', '--params', '{}'], cwd=blank)
            if 'PD_BUNDLED_TEMPLATE_PROBE' not in (blank / 'task_plan.md').read_text():
                raise RuntimeError('native pd_init did not use the bundled Skill template')
            summary['checks']['bundled-template'] = {'status': 'Passed'}
            (project / '.opencode/plugins/program-design.ts').unlink()
            shutil.rmtree(project / '.opencode/skills/project-docs')
            agent = json.loads(command('agent-after-remove', ['debug', 'agent', 'build'])['stdout'])
            skills = json.loads(command('skills-after-remove', ['debug', 'skill'])['stdout'])
            if any(name in agent.get('tools', {}) for name in ['pd_init', 'pd_check', 'pd_status']):
                raise RuntimeError('removed local plugin is still loaded')
            if any(skill.get('name') == 'project-docs' for skill in skills):
                raise RuntimeError('removed local Skill is still loaded')
            summary['checks']['remove'] = {'status': 'Passed'}
            summary['status'] = 'Passed'
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            summary['error'] = str(error)
        finally:
            summary['protected_records'] = {name: (project / name).is_file() and
                (project / name).read_bytes() == value for name, value in protected.items()}
            summary['project_records_unchanged'] = all(summary['protected_records'].values())
            current = COMMON.inventory(project)
            COMMON.save(args.output / 'project-after.json', {name: current.get(name) for name in protected})
            summary['prepared_source_unchanged'] = COMMON.inventory(args.package) == before
            COMMON.save(args.output / 'commands.json', commands)
    summary['temporary_profile_removed'] = not scratch.exists()
    if not all(summary[name] for name in ['project_records_unchanged', 'prepared_source_unchanged', 'temporary_profile_removed']):
        summary['status'] = 'Failed'
    COMMON.save(args.output / 'summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if summary['status'] == 'Passed' else 1


if __name__ == '__main__':
    sys.exit(main())
