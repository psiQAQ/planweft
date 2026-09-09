"""Execute the shipped examples across linked installs and bounded scratch."""
from pathlib import Path
import re
import os
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class LocalOperationsTest(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='pw-local-operations-')
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.project=self.root/'项目 with spaces';self.project.mkdir()
        (self.project/'user-note.txt').write_text('preserve user edit\n')
        self.examples=re.findall(r'```python\n(.*?)\n```',(ROOT/'overlays/planweft/references/local-operations.md').read_text(encoding="utf-8"),re.S)

    def execute(self,example,argument):
        return subprocess.run([sys.executable,'-c',example,str(argument)],cwd=self.project,
                              env={**os.environ,'PYTHONIOENCODING':'ascii'},encoding='utf-8',capture_output=True)

    def test_bilingual_examples_match_and_resolve_chained_relative_link(self):
        localized=re.findall(r'```python\n(.*?)\n```',(ROOT/'overlays/planweft/references/local-operations.zh.md').read_text(encoding="utf-8"),re.S)
        self.assertEqual(self.examples,localized)
        self.assertEqual(len(self.examples),3)
        installed=self.root/'安装 cache'/'skills'/'project-docs';installed.mkdir(parents=True)
        (installed/'SKILL.md').write_text('# Real Skill\r\n')
        middle=self.root/'中间 link';middle.mkdir()
        try:
            (middle/'entry').symlink_to(Path('../安装 cache/skills/project-docs'),target_is_directory=True)
            (self.project/'skill-link').symlink_to(Path('../中间 link/entry'),target_is_directory=True)
        except OSError as error:
            self.skipTest('Native symlink creation unavailable: '+str(error))
        result=self.execute(self.examples[0],self.project/'skill-link/SKILL.md')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(Path(result.stdout.strip()),installed.resolve())
        self.assertFalse((self.project/'scripts').exists())

    def test_missing_or_non_skill_location_fails_without_search(self):
        for target in [self.project/'SKILL.md',self.project/'user-note.txt']:
            with self.subTest(target=target.name):
                result=self.execute(self.examples[0],target)
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(result.stdout,'')
        self.assertEqual(sorted(p.name for p in self.project.iterdir()),['user-note.txt'])

    def test_planning_lookup_does_not_enumerate_environment(self):
        # Reject iteration and access to any unrelated key, not just its output.
        prefix = """import os
class NamedEnvironment:
    def get(self, key, default=None):
        assert key in ('PLAN_ID', 'PWF_PLAN_ROOT', 'PLANNING_DISABLED'), key
        return {'PLAN_ID': '计划 one', 'PWF_PLAN_ROOT': ''}.get(key, default)
    def __iter__(self):
        raise AssertionError('environment enumerated')
    def items(self):
        raise AssertionError('environment enumerated')
os.environ = NamedEnvironment()
"""
        result=self.execute(prefix+self.examples[2],self.project)
        self.assertEqual(result.returncode,0,result.stderr)
        import json
        self.assertEqual(json.loads(result.stdout),{
            'PLAN_ID':'计划 one','PWF_PLAN_ROOT':'','PLANNING_DISABLED':None})
        self.assertEqual(sorted(p.name for p in self.project.iterdir()),['user-note.txt'])

    def test_manual_scratch_is_project_owned_and_cleaned_on_error(self):
        marker='# Run the authorized manual check here, using scratch for every output.'
        for fail in [False,True]:
            example=self.examples[1].replace(marker,
                '(scratch / "中文 output.txt").write_text("synthetic output")\n'
                '    assert scratch.parent == project\n'
                +('    raise RuntimeError("synthetic manual check failed")' if fail else '    assert (scratch / "中文 output.txt").is_file()'))
            result=self.execute(example,self.project)
            self.assertEqual(result.returncode==0,not fail,result.stderr)
            relative=result.stdout.strip().removeprefix('manual scratch: ')
            self.assertTrue(relative.startswith('.pw-scratch-'))
            self.assertEqual(Path(relative).name,relative)
            self.assertFalse((self.project/relative).exists())
            self.assertEqual((self.project/'user-note.txt').read_text(encoding="utf-8"),'preserve user edit\n')
            self.assertEqual(sorted(p.name for p in self.project.iterdir()),['user-note.txt'])


if __name__=='__main__':unittest.main()
