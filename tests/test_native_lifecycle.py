#!/usr/bin/env python3
"""Offline input, isolation and installed-byte verification for the native runner."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_lifecycle', ROOT / 'tests/run-native-lifecycle.py')
RUNNER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RUNNER)


class NativeLifecycleBoundaryTest(unittest.TestCase):
    def test_existing_nested_documents_are_preserved_and_drift_fails_cleanup(self):
        with tempfile.TemporaryDirectory(prefix='pd-lifecycle-records-') as temporary:
            root = Path(temporary)
            lifecycle = RUNNER.Lifecycle(SimpleNamespace(host='gemini', output=root / 'evidence'), root)
            required = {'docs/specs/approved.md', 'docs/adr/decision.md', 'docs/reproduction/known.md'}
            self.assertTrue(required <= set(lifecycle.project_before))
            lifecycle.summary['status'] = 'Passed'
            lifecycle.cleanup()
            self.assertTrue(lifecycle.summary['project_unchanged'])
            for name in sorted(required):
                target = lifecycle.project / name
                original = target.read_bytes()
                for mutation in ['modify', 'delete']:
                    with self.subTest(name=name, mutation=mutation):
                        if mutation == 'modify':
                            target.write_bytes(original + b'Unexpected replacement\n')
                        else:
                            target.unlink()
                        lifecycle.summary['status'] = 'Passed'
                        lifecycle.cleanup()
                        self.assertFalse(lifecycle.summary['project_unchanged'])
                        self.assertEqual(lifecycle.summary['status'], 'Failed')
                        target.write_bytes(original)

    def test_opencode_rejects_invalid_paths_before_installing_dependencies(self):
        spec = importlib.util.spec_from_file_location('opencode_native', ROOT / 'tests/run-opencode-native.py')
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory(prefix='pd-opencode-args-') as temporary:
            root = Path(temporary)
            output = root / 'missing-parent/evidence'
            source = root / 'package'
            source.mkdir()
            (source / 'package-lock.json').write_text('{}')
            base = ['--cli', sys.executable, '--package', str(source), '--output', str(output)]
            with patch.object(runner.subprocess, 'run', side_effect=AssertionError('must not install or launch')):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    runner.main(base)
                self.assertFalse(output.parent.exists())
                (source / 'dist').mkdir()
                (source / 'dist/index.js').write_text('export const fixture = true')
                for target in [ROOT / 'opencode-evidence', source]:
                    with self.subTest(target=target), contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit):
                            runner.main(base[:-1] + [str(target)])
                self.assertFalse(output.parent.exists())
                self.assertEqual((source / 'package-lock.json').read_text(), '{}')

    def test_catalog_cleanup_failure_cannot_leave_a_passed_summary(self):
        with tempfile.TemporaryDirectory(prefix='pd-lifecycle-cleanup-') as temporary:
            root = Path(temporary)
            lifecycle = RUNNER.Lifecycle.__new__(RUNNER.Lifecycle)
            lifecycle.args = SimpleNamespace(host='codex', output=root / 'evidence')
            lifecycle.project = root / 'project'
            lifecycle.project.mkdir()
            lifecycle.project_before = {}
            lifecycle.installed = False
            lifecycle.marketplace = 'fixture'
            lifecycle.commands = []
            lifecycle.summary = {'status': 'Passed'}
            lifecycle.command = lambda *args, **kwargs: {'exit_code': 1}
            lifecycle.cleanup()
            self.assertEqual(lifecycle.summary['status'], 'Failed')
            self.assertEqual(lifecycle.summary['cleanup_error'], 'native marketplace removal failed')

    def test_invalid_arguments_and_help_do_not_create_output_or_start_a_cli(self):
        with tempfile.TemporaryDirectory(prefix='pd-lifecycle-args-') as temporary:
            output = Path(temporary) / 'missing-parent/evidence'
            base = ['--cli', sys.executable, '--output', str(output)]
            cases = [([], 2), (['--help'], 0), (base + ['--host', 'other'], 2),
                     (base + ['--host', 'codex', '--timeout', '0'], 2),
                     (base + ['--host', 'codex', '--timeout', 'bad'], 2),
                     (['--host', 'codex', '--cli', sys.executable, '--output', str(ROOT / 'evidence')], 2)]
            with patch.object(RUNNER.subprocess, 'run', side_effect=AssertionError('must not launch a CLI')):
                for argv, code in cases:
                    with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaises(SystemExit) as raised:
                            RUNNER.main(argv)
                        self.assertEqual(raised.exception.code, code)
                        self.assertFalse(output.parent.exists())
            existing = Path(temporary) / 'existing'
            existing.mkdir()
            marker = existing / 'keep.txt'
            marker.write_text('keep')
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                RUNNER.main(['--host', 'pi', '--cli', sys.executable, '--output', str(existing)])
            self.assertEqual(marker.read_text(), 'keep')

    def test_isolated_environment_does_not_inherit_auth_or_user_configuration(self):
        with tempfile.TemporaryDirectory(prefix='pd-lifecycle-env-') as temporary:
            profile = Path(temporary) / 'profile'
            inherited = {'PATH': '/usr/bin', 'HOME': '/personal-home',
                         'CODEX_HOME': '/personal-codex', 'CLAUDE_CONFIG_DIR': '/personal-claude',
                         'GEMINI_CLI_HOME': '/personal-gemini', 'OPENAI_API_KEY': 'fake-secret',
                         'ANTHROPIC_API_KEY': 'fake-secret', 'GOOGLE_APPLICATION_CREDENTIALS': '/private.json',
                         'GITHUB_TOKEN': 'fake-secret', 'NODE_OPTIONS': '--require /personal-code.js',
                         'PWF_TRUSTED_PYTHON': '/untrusted-python', 'PYTHONPATH': '/personal-modules'}
            with patch.dict(os.environ, inherited, clear=True):
                environment = RUNNER.isolated_environment(profile)
            for key in ['GEMINI_CLI_HOME', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY',
                        'GOOGLE_APPLICATION_CREDENTIALS', 'GITHUB_TOKEN', 'NODE_OPTIONS',
                        'PWF_TRUSTED_PYTHON', 'PYTHONPATH']:
                self.assertNotIn(key, environment)
            for key in ['HOME', 'CODEX_HOME', 'CLAUDE_CONFIG_DIR', 'PI_CODING_AGENT_DIR',
                        'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'npm_config_userconfig']:
                path = Path(environment[key])
                self.assertTrue(path == profile or profile in path.parents)
            self.assertEqual(environment['npm_config_offline'], 'true')

    def test_version_fixture_and_cache_checks_detect_added_changed_deleted_and_executable_files(self):
        with tempfile.TemporaryDirectory(prefix='pd-lifecycle-byte-') as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            (source / 'gemini-extension.json').write_text(json.dumps({'name': 'program-design', 'version': '0.3.0'}))
            executable = source / 'hook.sh'
            executable.write_text('#!/bin/sh\nexit 0\n')
            executable.chmod(0o755)
            first, second = root / 'A', root / 'B'
            a = RUNNER.fixture_version(source, first, 'gemini', '0.3.0')
            b = RUNNER.fixture_version(source, second, 'gemini', '0.3.1')
            self.assertTrue(set(a) - set(b), 'fixture must include a removed resource')
            self.assertTrue(set(b) - set(a), 'fixture must include an added resource')
            self.assertTrue(any(a[key] != b[key] for key in set(a) & set(b)))
            installed = root / 'installed'
            shutil.copytree(second, installed)
            self.assertEqual(RUNNER.compare_installed(installed, b, set(a) - set(b))['status'], 'Passed')
            deleted = next(iter(set(a) - set(b)))
            (installed / deleted).write_bytes((first / deleted).read_bytes())
            result = RUNNER.compare_installed(installed, b, set(a) - set(b))
            self.assertEqual(result['status'], 'Failed')
            self.assertEqual(result['stale_removed_files'], [deleted])
            (installed / deleted).unlink()
            (installed / 'hook.sh').chmod(0o644)
            self.assertIn('hook.sh', RUNNER.compare_installed(installed, b)['mismatches'])
            self.assertEqual(json.loads((source / 'gemini-extension.json').read_text())['version'], '0.3.0')


if __name__ == '__main__':
    unittest.main()
