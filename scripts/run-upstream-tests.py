#!/usr/bin/env python3
"""Run pinned upstream or migrated regressions in a fresh, disposable tree.

Python test dependencies must already exist in --python; nothing installs them.
--with-node explicitly opts into npm ci from each package's checked-in lockfile.
The source repository, personal configuration, and global packages are untouched.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('planweft_builder', ROOT / 'scripts/build-plugin.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['baseline', 'migrated'])
    parser.add_argument('--output', type=Path, required=True, help='New directory for the test tree, caches, and reports')
    parser.add_argument('--python', required=True, help='Existing Python interpreter with pytest and PyYAML installed')
    parser.add_argument('--source', type=Path, help='Optional existing source to copy; baseline bytes must match the pinned archive')
    parser.add_argument('--with-node', action='store_true', help='Install locked local npm dependencies and run Pi/OpenCode checks')
    parser.add_argument('--tool-path', type=Path, action='append', default=[],
                        help='Explicit directory prepended to tool lookup after the Python environment; repeatable, never auto-selected')
    args = parser.parse_args()
    output = args.output.expanduser().absolute()
    if output.exists():
        parser.error('--output must not exist; existing runs are never overwritten')
    source = args.source.expanduser().resolve() if args.source else None
    if source and (not source.is_dir() or output.resolve().is_relative_to(source)):
        parser.error('--source must be a directory outside the new output tree and cannot contain --output')
    python = shutil.which(args.python)
    if not python:
        parser.error('--python is not an executable path or command')
    python = str(Path(python).absolute())  # Keep the venv path rather than resolving its symlink.
    tool_paths = [path.expanduser().resolve() for path in args.tool_path]
    if any(not path.is_dir() for path in tool_paths):
        parser.error('every --tool-path must name an existing directory')
    output.mkdir(parents=True)
    tree = output / 'source'
    logs = output / 'logs'
    logs.mkdir()
    env = os.environ.copy()
    cleared = []
    for key in list(env):
        if key.startswith('PWF_') or key in {
            'PLAN_ID', 'PLANNING_DISABLED', 'PLANNING_WITH_FILES_SKILL_ROOT',
            'PYTHON_BIN', 'PYTHONPATH', 'PYTHONHOME',
        }:
            cleared.append(key)
            del env[key]
    isolated = {
        'PATH': os.pathsep.join([str(Path(python).parent), *map(str, tool_paths), env.get('PATH', '')]),
        'XDG_CACHE_HOME': str(output / 'cache'),
        'npm_config_cache': str(output / 'npm-cache'),
        'PYTHONDONTWRITEBYTECODE': '1',
    }
    env.update(isolated)
    summary = {
        'mode': args.mode, 'started_at': datetime.now(timezone.utc).isoformat(),
        'environment': {'platform': platform.platform(), 'python_executable': python,
                        'overrides': isolated, 'tool_paths': list(map(str, tool_paths)),
                        'cleared_variable_names': sorted(cleared)},
        'source_override': str(source) if source else None,
        'commands': [], 'checks': {},
        'limitations': ['Protocol and regression tests do not establish real interactive host compatibility.',
                        'Only the current operating system is exercised.'],
    }

    def record(name, command, cwd):
        path = logs / (name + '.log')
        started = time.monotonic()
        with path.open('w', encoding='utf-8') as stream:
            stream.write('cwd: ' + str(cwd) + '\ncommand: ' + json.dumps(command) + '\n')
            stream.flush()
            try:
                result = subprocess.run(command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT)
                code = result.returncode
            except OSError as exc:
                stream.write(str(exc) + '\n')
                code = 127
        item = {'name': name, 'command': command, 'cwd': str(cwd), 'exit_code': code,
                'status': 'Passed' if code == 0 else 'Failed',
                'duration_seconds': round(time.monotonic() - started, 3),
                'log': str(path.relative_to(output))}
        summary['commands'].append(item)
        summary['checks'][name] = item['status']
        print(name + ': ' + item['status'], flush=True)
        if code:
            print('\n'.join(path.read_text(encoding='utf-8', errors='replace').splitlines()[-20:]), flush=True)
        return code

    exit_code = 1
    try:
        summary['environment']['resolved_tools'] = {}
        for name in ['mkdir', 'sh', 'git']:
            executable = shutil.which(name, path=env['PATH'])
            if executable:
                binary = Path(executable).resolve()
                summary['environment']['resolved_tools'][name] = {
                    'path': executable, 'resolved_path': str(binary),
                    'sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
                }
        runtime_probe = ('import json,sys,importlib.metadata; '
                         'print(json.dumps({"python":sys.version,"packages":'
                         '{p:importlib.metadata.version(p) for p in ["pytest","PyYAML"]}}))')
        if record('python-dependencies', [python, '-c', runtime_probe], output):
            raise RuntimeError('Install requirements-test.txt in the selected interpreter before running this script.')
        git = shutil.which('git')
        if not git:
            raise RuntimeError('git is required: upstream tests enumerate tracked source files.')
        builder = load_builder()
        original, manifest = builder.read_upstream()
        summary['upstream'] = manifest
        if args.mode == 'baseline':
            if source:
                for name, (data, _) in original.items():
                    candidate = source / name
                    if not candidate.is_file() or candidate.read_bytes() != data:
                        raise ValueError('Baseline source differs from the pinned archive: ' + name)
            builder.write_tree(original, tree)
            summary['source_preparation'] = 'Verified pinned archive and inventory; extracted original bytes and modes.'
        elif source:
            shutil.copytree(source, tree, ignore=shutil.ignore_patterns('.git', 'node_modules', '__pycache__', '.pytest_cache'))
            summary['source_preparation'] = 'Copied the provided migrated tree without caches, dependencies, or Git metadata.'
        else:
            if record('build-migrated-tree', [python, str(ROOT / 'scripts/build-plugin.py'), '--tree', str(tree)], ROOT):
                raise RuntimeError('Failed to generate the migrated test tree.')
            summary['source_preparation'] = 'Generated using build-plugin.py --tree.'
        if record('git-init', [git, 'init', '--quiet'], tree) or record('git-index', [git, 'add', '--all', '--force'], tree):
            raise RuntimeError('Failed to create the disposable test index.')
        junit = output / 'pytest.junit.xml'
        record('pytest', [python, '-m', 'pytest', 'tests/', '-q', '--junitxml=' + str(junit)], tree)
        if junit.exists():
            xml = ET.parse(junit).getroot()
            summary['pytest_junit_suites'] = [dict(suite.attrib) for suite in xml.iter('testsuite')]
            summary['pytest_skips'] = [
                {'test': case.get('classname', '') + '::' + case.get('name', ''),
                 'reason': case.find('skipped').get('message', '')}
                for case in xml.iter('testcase') if case.find('skipped') is not None
            ]
            summary['pytest_terminal_summary'] = (logs / 'pytest.log').read_text(encoding='utf-8', errors='replace').splitlines()[-1]
        if args.with_node:
            npm = shutil.which('npm')
            if not npm:
                raise RuntimeError('--with-node requires npm and Node.js already installed.')
            record('npm-version', [npm, '--version'], output)
            record('node-version', [shutil.which('node') or 'node', '--version'], output)
            package = 'planning-with-files' if args.mode == 'baseline' else 'project-docs'
            extension = 'planning-with-files' if args.mode == 'baseline' else 'planweft'
            packages = {
                'pi': tree / '.pi' / 'skills' / package / 'extensions' / extension,
                'opencode': tree / '.opencode' / 'packages' / ('opencode-' + extension),
            }
            for host, directory in packages.items():
                if record(host + '-npm-ci', [npm, 'ci', '--no-audit', '--no-fund'], directory):
                    summary['checks'][host + '-dependent-checks'] = 'Not Run: npm ci failed'
                    continue
                if host == 'opencode':
                    record(host + '-typecheck', [npm, 'run', 'typecheck'], directory)
                    record(host + '-build', [npm, 'run', 'build'], directory)
                record(host + '-test', [npm, 'test'], directory)
            summary['checks']['pi-typecheck-build'] = 'Not Run: upstream defines neither command nor tsconfig'
        else:
            summary['checks']['node'] = 'Not Run: enable --with-node for locked npm installs and checks'
        exit_code = int(any(command['exit_code'] != 0 for command in summary['commands']))
    except Exception as exc:
        summary['error'] = str(exc)
        print('Failed: ' + str(exc), file=sys.stderr)
    finally:
        summary['status'] = 'Passed' if exit_code == 0 else 'Failed'
        summary['finished_at'] = datetime.now(timezone.utc).isoformat()
        (output / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print('Report: ' + str(output / 'summary.json'), flush=True)
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
