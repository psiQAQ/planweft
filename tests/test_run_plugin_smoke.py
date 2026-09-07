#!/usr/bin/env python3
"""Regression tests for the smoke runner's side-effect-free argument checks."""
import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock


RUNNER_PATH = Path(__file__).with_name('run-plugin-smoke.py')
SPEC = importlib.util.spec_from_file_location('run_plugin_smoke', RUNNER_PATH)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class ArgumentValidationTest(unittest.TestCase):
    def assert_argument_error(self, extra_args, message):
        stderr = io.StringIO()
        with (mock.patch.object(runner.Path, 'mkdir') as mkdir,
              mock.patch.object(runner, 'run') as run,
              mock.patch.object(runner.Path, 'home') as home,
              contextlib.redirect_stderr(stderr)):
            with self.assertRaises(SystemExit) as raised:
                runner.main(['--output', '/controlled/not-created', '--model', 'test-model', *extra_args])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn(message, stderr.getvalue())
        mkdir.assert_not_called()
        run.assert_not_called()
        home.assert_not_called()

    def test_unknown_and_internal_cases_are_rejected_before_side_effects(self):
        self.assert_argument_error(['--cases', 'unknown'], "invalid choice: 'unknown'")
        self.assert_argument_error(['--cases', 'handoff'], "invalid choice: 'handoff'")

    def test_duplicate_case_is_rejected_before_side_effects(self):
        self.assert_argument_error(['--cases', 'enabled', 'enabled'], 'duplicate scenario name(s): enabled')

    def test_non_positive_timeout_is_rejected_before_side_effects(self):
        self.assert_argument_error(['--timeout', '0'], 'must be a positive integer')
        self.assert_argument_error(['--timeout', '-1'], 'must be a positive integer')

    def test_valid_case_selection_and_timeout_parse(self):
        args = runner.parse_args([
            '--output', '/controlled/not-created', '--model', 'test-model',
            '--cases', 'enabled', 'repo-copy', '--timeout', '1',
        ])
        self.assertEqual(args.cases, ['enabled', 'repo-copy'])
        self.assertEqual(args.timeout, 1)
        self.assertEqual(runner.parse_args([
            '--output', '/controlled/not-created', '--model', 'test-model',
        ]).cases, list(runner.CASES))


if __name__ == '__main__':
    unittest.main()
