"""Copied compact entries keep executable resources and conditional manuals."""
import importlib.util
from pathlib import Path, PurePosixPath
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]


class SkillEntrypointTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('entry_builder',ROOT/'scripts/build-plugin.py')
        cls.builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.builder)
        upstream,provenance=cls.builder.read_upstream()
        cls.tree=cls.builder.transform(upstream)
        cls.packages=cls.builder.distributions(cls.tree,provenance,compiled=False)

    def test_core_entries_are_bounded_and_self_contained(self):
        for host in ('codex','claude','pi','opencode','dsh'):
            files=self.packages[host]
            for name,(raw,_) in files.items():
                if not (name.endswith('/SKILL.md') or name=='SKILL.md'): continue
                with self.subTest(host=host,entry=name):
                    text=raw.decode(); base=PurePosixPath(name).parent
                    self.assertLess(len(text.splitlines()),110)
                    manual=str(base/'references/pwf-workflow.md')
                    self.assertIn(manual,files)
                    self.assertGreater(len(files[manual][0]),1000)
                    # References and runtime helpers survive copying this folder.
                    for target in re.findall(r'\]\(([^)]+)\)',text):
                        if target.startswith('references/'):
                            self.assertIn(str(base/target),files)
                    for helper in ('resolve-plan-dir.sh','init-session.sh'):
                        self.assertIn(str(base/'scripts'/helper),files)

    def test_language_entries_are_explicit_and_use_the_same_resource_contract(self):
        for locale in ('ar','de','es','zh','zht'):
            path='skills/i18n/project-docs-'+locale+'/SKILL.md'
            text=self.tree[path][0].decode()
            self.assertIn('disable-model-invocation: true',text)
            self.assertIn((ROOT/'overlays/planweft/entrypoints'/f'{locale}.md').read_text().strip(),text)
            for token in ('PLAN_ID','PWF_PLAN_ROOT','PLANNING_DISABLED=1','task_plan.md','findings.md','progress.md'):
                self.assertIn(token,text)


if __name__=='__main__': unittest.main()
