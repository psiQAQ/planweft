"""Read-only Pi delivery fixtures must not implicitly test an execution loop."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('pw_pi_fixture_runner',Path(__file__).with_name('run-five-agent-release.py'))
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
OLD='PW_RECOVERY_'+'a'*32
NEW='PW_RECOVERY_'+'b'*32


class PiContextFixtureTest(unittest.TestCase):
    def test_pi_completed_context_and_fresh_file_recovery(self):
        before=runner.context_fixture('pi','context',OLD)
        self.assertIn('**Status:** complete\n',before['task_plan.md'])
        self.assertNotIn('**Status:** in_progress',before['task_plan.md'])
        self.assertNotIn('.mode',before)
        self.assertNotIn('<!-- pwf: closed -->',before['task_plan.md'])
        saved=dict(before)
        after=runner.context_fixture('pi','recovery',NEW,before)
        self.assertEqual(before,saved)
        self.assertIn(NEW,after['task_plan.md']);self.assertNotIn(OLD,after['task_plan.md'])
        self.assertEqual(after['task_plan.md'],before['task_plan.md'].replace(OLD,NEW))
        self.assertTrue(after['progress.md'].startswith(before['progress.md']))
        for case in ['context','recovery']:
            scope=runner.context_probe_scope('pi',case)
            self.assertEqual(scope['plan_state_under_test'],'complete')
            self.assertIn('incomplete plan',scope['excludes'])

    def test_existing_in_progress_pi_plan_is_rejected_not_rewritten(self):
        previous=runner.context_fixture('codex','context',OLD);saved=dict(previous)
        with self.assertRaisesRegex(ValueError,'preserve in-progress evidence'):
            runner.context_fixture('pi','recovery',NEW,previous)
        self.assertEqual(previous,saved)

    def test_other_hosts_keep_exact_original_in_progress_fixture(self):
        expected={'README.md':'# Context probe\n','task_plan.md':
            '# Task Plan\n\n## Goal\nReport automatically injected RECOVERY_CODE.\n\nRECOVERY_CODE: '+OLD+
            '\n\n### Phase 1: Probe\n- **Status:** in_progress\n',
            'findings.md':'# Findings\nProject files only.\n','progress.md':'# Progress\nPrepared fixture.\n'}
        for host in ['codex','claude','opencode','dsh']:
            with self.subTest(host=host):
                self.assertEqual(runner.context_fixture(host,'context',OLD),expected)
                restored=runner.context_fixture(host,'recovery',NEW,expected)
                self.assertIn('**Status:** in_progress',restored['task_plan.md'])
                self.assertIn(NEW,restored['task_plan.md'])
                self.assertEqual(runner.context_probe_scope(host,'recovery'),{})
        self.assertEqual(runner.context_fixture('pi','untrusted',OLD),expected)

    def test_execution_limit_and_passive_stopping_remain_in_progress(self):
        for case in ['continuation-limit','stopping']:
            files=runner.stop_fixture(case)
            self.assertIn('**Status:** in_progress',files['task_plan.md'])
            self.assertIn('External acceptance is pending',files['task_plan.md'])
            self.assertNotIn('.mode',files)
            self.assertEqual(runner.context_probe_scope('pi',case),{})


if __name__=='__main__': unittest.main()
