#!/usr/bin/env python3
"""Independent, offline CLI contract check for run-plugin-smoke.py.

Usage: python3 tests/experiments/check-entry-contract.py REPOSITORY
Uses the public argv/main boundary, with process/auth substitutes. No Docker,
model, network, or real credential access occurs. Prints JSON; failure exits 1.
"""
import contextlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from unittest.mock import patch


# Frozen from a5f072e's public inputs, deliberately not imported from the target.
DEFAULT_CASES = [
    'enabled', 'unenabled', 'unrelated', 'readonly', 'conflict', 'blank',
    'evidence-gap',
]


def check_one(script, name, extra, *, invalid=False, help_only=False,
              expected_cases=(), enabled_failure=False):
    with tempfile.TemporaryDirectory(prefix='pd-entry-contract-') as temp:
        root = Path(temp)
        output = root / 'must-not-exist' / 'nested' / 'output'
        home = root / 'fake-home'
        (home / '.codex').mkdir(parents=True)
        (home / '.codex/auth.json').write_text('FAKE_TEST_CREDENTIAL\n')
        attempts = []
        executions = []
        captured = io.StringIO()
        original_mkdir = Path.mkdir

        def mkdir(path, *args, **kwargs):
            attempts.append('mkdir')
            if invalid or help_only:
                raise RuntimeError('Filesystem mutation attempted before rejection')
            return original_mkdir(path, *args, **kwargs)

        def fake_home():
            attempts.append('auth/home')
            if invalid or help_only:
                raise RuntimeError('Credential location accessed before rejection')
            return home

        def fake_run(command, *args, **kwargs):
            attempts.append('process:' + command[0])
            if invalid or help_only:
                raise RuntimeError('External process attempted before rejection')
            stdout, returncode = '', 0
            if command[:3] == ['docker', 'image', 'inspect']:
                stdout = 'sha256:offline-fixture\n'
            elif command[:2] == ['docker', 'run']:
                container = command[command.index('--name') + 1]
                case = container.split('-', 3)[3]
                executions.append(case)
                returncode = int(enabled_failure and case == 'enabled')
            elif command[:3] == ['git', 'rev-parse', 'HEAD']:
                stdout = 'a5f072e\n'
            elif command[:2] == ['git', 'ls-files']:
                stdout = 'AGENTS.md\nREADME.md\n'
            elif command[0] not in {'git', 'docker'}:
                raise RuntimeError('Unexpected process: ' + command[0])
            return subprocess.CompletedProcess(command, returncode, stdout, '')

        argv = [str(script), '--output', str(output), '--model', 'offline-fixture'] + extra
        if help_only:
            argv = [str(script), '--help']
        exit_code, error = 0, None
        with patch.object(sys, 'argv', argv), patch.object(Path, 'mkdir', mkdir), \
                patch.object(Path, 'home', fake_home), \
                patch('subprocess.run', fake_run), \
                contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            try:
                runpy.run_path(str(script), run_name='__main__')
            except SystemExit as exc:
                exit_code = exc.code
            except Exception as exc:
                exit_code = 1
                error = type(exc).__name__ + ': ' + str(exc)

        checks = {}
        if invalid:
            checks = {
                'exit_2': exit_code == 2,
                'diagnostic': 'error:' in captured.getvalue().lower(),
                'no_side_effect_attempt': not attempts,
                'no_output_ancestors': not (root / 'must-not-exist').exists(),
            }
        elif help_only:
            checks = {'exit_0': exit_code == 0, 'help_text': 'usage:' in captured.getvalue().lower(),
                      'no_side_effect_attempt': not attempts}
        else:
            checks = {
                'expected_exit': exit_code == (1 if enabled_failure else 0),
                'executed_cases': sorted(executions) == sorted(expected_cases),
            }
            if enabled_failure:
                checks['failure_reported'] = error is not None and 'One or more executions failed' in error
        return {'name': name, 'passed': all(checks.values()), 'checks': checks,
                'exit_code': exit_code, 'error': error, 'executions': executions,
                'side_effect_attempts': attempts, 'output': captured.getvalue()}


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: check-entry-contract.py REPOSITORY')
    script = Path(sys.argv[1]).resolve() / 'tests/run-plugin-smoke.py'
    results = []
    for name, extra in [
        ('unknown', ['--cases', 'unknown']),
        ('mixed-unknown', ['--cases', 'enabled', 'unknown']),
        ('duplicate', ['--cases', 'enabled', 'enabled']),
        ('duplicate-repo-copy', ['--cases', 'repo-copy', 'repo-copy']),
        ('internal-handoff', ['--cases', 'handoff']),
        ('zero-timeout', ['--timeout', '0']),
        ('negative-timeout', ['--timeout', '-1']),
    ]:
        results.append(check_one(script, name, extra, invalid=True))
    results.append(check_one(script, 'help', [], help_only=True))
    results.append(check_one(script, 'defaults', [], expected_cases=DEFAULT_CASES + ['handoff']))
    results.append(check_one(script, 'repo-copy', ['--cases', 'repo-copy', '--timeout', '1'],
                             expected_cases=['repo-copy']))
    results.append(check_one(script, 'multiple-valid', ['--cases', 'readonly', 'blank', '--timeout', '10'],
                             expected_cases=['readonly', 'blank']))
    results.append(check_one(script, 'enabled-success-handoff', ['--cases', 'enabled'],
                             expected_cases=['enabled', 'handoff']))
    results.append(check_one(script, 'enabled-failure-no-handoff', ['--cases', 'enabled'],
                             expected_cases=['enabled'], enabled_failure=True))
    passed = all(result['passed'] for result in results)
    print(json.dumps({'passed': passed, 'results': results}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
