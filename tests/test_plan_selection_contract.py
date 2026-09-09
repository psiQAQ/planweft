"""Exercise the helper states behind the Skill's selection decision table.

These are real script contracts, not proof that a model follows the prose.
"""
import importlib.util
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('sh') and shutil.which('bash'), 'Shell helpers unavailable')
class PlanSelectionContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('selection_builder', ROOT / 'scripts/build-plugin.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        upstream, _ = builder.read_upstream()
        cls.tree = builder.transform(upstream)

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix='pw-selection-')
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.project = self.root / '项目 with spaces'
        self.project.mkdir()
        self.skill = self.root / 'installed skill'
        prefix = 'skills/project-docs/'
        for name, (data, _) in self.tree.items():
            if name.startswith(prefix) and name[len(prefix):].startswith(('scripts/', 'templates/')):
                target = self.skill / name[len(prefix):]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith('PWF_') and key not in {'PLAN_ID', 'PLANNING_DISABLED'}}

    def resolve(self, **bindings):
        return subprocess.run(['sh', str(self.skill / 'scripts/resolve-plan-dir.sh')],
                              cwd=self.project, env={**self.env, **bindings},
                              capture_output=True, text=True, timeout=10)

    def snapshot(self):
        return {str(p.relative_to(self.project)): p.read_bytes()
                for p in self.project.rglob('*') if p.is_file()}

    def test_missing_and_rejected_selection_share_zero_empty_result_without_writes(self):
        (self.project / 'notes').mkdir()
        (self.project / 'notes/work.md').write_text('Prior task context\n')
        before = self.snapshot()
        for bindings in ({}, {'PLAN_ID': 'missing-task'}, {'PLAN_ID': '../other'},
                         {'PWF_PLAN_ROOT': str(self.root / 'missing-project')}):
            with self.subTest(bindings=bindings):
                result = self.resolve(**bindings)
                self.assertEqual((result.returncode, result.stdout), (0, ''))
                self.assertEqual(self.snapshot(), before)

    def test_legacy_plan_is_not_selected_named_output_and_is_not_modified(self):
        (self.project / 'task_plan.md').write_bytes(b'Approved existing root plan\r\n')
        before = self.snapshot()
        result = self.resolve()
        self.assertEqual((result.returncode, result.stdout), (0, ''))
        self.assertEqual(self.snapshot(), before)

    def test_named_initializer_requires_no_preexisting_id_and_reports_actual_files(self):
        (self.project / 'notes').mkdir()
        old = self.project / 'notes/work.md'
        old.write_bytes(b'Original task context\r\n')
        result = subprocess.run(['bash', str(self.skill / 'scripts/init-session.sh'), 'Export maintenance'],
                                cwd=self.project, env=self.env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        match = re.search(r'^PLAN_ID=(.+)$', result.stdout, re.M)
        self.assertIsNotNone(match)
        plan_id = match[1]
        selected = self.project / '.planning' / plan_id
        self.assertEqual((self.project / '.planning/.active_plan').read_text().strip(), plan_id)
        for name in ('task_plan.md', 'findings.md', 'progress.md'):
            self.assertTrue((selected / name).is_file(), name)
        self.assertFalse((self.project / 'task_plan.md').exists())
        self.assertEqual(old.read_bytes(), b'Original task context\r\n')
        before = self.snapshot()
        resolved = self.resolve(PLAN_ID=plan_id)
        self.assertEqual(resolved.returncode, 0)
        self.assertEqual(Path(resolved.stdout.strip()).resolve(), selected.resolve())
        # A new task-selected read does not run initializer again or invent a suffix.
        self.assertEqual(self.snapshot(), before)

    def test_rejected_binding_does_not_fall_back_to_existing_other_task(self):
        task = self.project / '.planning/other'
        task.mkdir(parents=True)
        (task / 'task_plan.md').write_text('Unrelated task\n')
        (self.project / '.planning/.active_plan').write_text('other\n')
        (self.project / 'task_plan.md').write_text('Legacy plan\n')
        before = self.snapshot()
        result = self.resolve(PLAN_ID='missing')
        self.assertEqual((result.returncode, result.stdout), (0, ''))
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()
