"""Prove the existing PWF selectors retain task scope only in selected sections.

Synthetic plan files are fixture data, not model adoption or native delivery.
No runtime injection rules or upstream state formats are changed.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class ScopeRecoveryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('scope_builder',ROOT/'scripts/build-plugin.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        original,_=builder.read_upstream()
        cls.tree=builder.transform(original)
        cls.temp=tempfile.TemporaryDirectory(prefix='pw-scope-selector-')
        cls.addClassCleanup(cls.temp.cleanup)
        file=Path(cls.temp.name)/'inject-plan.py'
        file.write_bytes(cls.tree['scripts/inject-plan.py'][0])
        spec=importlib.util.spec_from_file_location('scope_inject',file)
        cls.inject=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.inject)

    def test_goal_retains_scope_in_head_and_smart_but_late_appendix_does_not(self):
        boundary='Task instruction: edit only project sources; do not read host settings; no project-external scratch. 来源：本次用户任务。'
        prefix='# Task Plan: export fix\n\n## Goal\n\nFix the export.\n'
        body='\n## Next Step\n\nRun tests.\n\n## Current Phase\n\nPhase 1\n\n## Phases\n\n### Phase 1: Verify\n**Status:** in_progress\n'
        padding='\n'.join('Historical line '+str(i) for i in range(40))+'\n'
        previous=prefix+body+padding+'\n## Scope and acceptance evidence\n'+boundary+'\n'
        corrected=prefix+boundary+'\n'+body+padding+'\n## Scope and acceptance evidence\nSee Goal.\n'
        for crlf in [False,True]:
            for name,select in [('head30',lambda data:self.inject.head_lines(data,30)),
                                ('smart',self.inject.smart_plan_extract)]:
                with self.subTest(crlf=crlf,selector=name):
                    encode=lambda text:text.replace('\n','\r\n' if crlf else '\n').encode()
                    self.assertNotIn(boundary.encode(),select(encode(previous)))
                    selected=select(encode(corrected))
                    self.assertEqual(selected.count(boundary.encode()),1)
                    self.assertIn(b'Run tests.',selected)

    def test_localized_and_mixed_headings_require_actual_selector_fallback(self):
        boundary='用户任务：只处理指定项目；不读宿主设置。'
        prefix='# 任务计划\n\n## 目标\n'+boundary+'\n'
        localized=prefix+'\n## 阶段\n### 阶段 1\n**Status:** in_progress\n'
        mixed=prefix+'\n## Phases\n### Phase 1\n**Status:** in_progress\n'
        injector=self.inject.Injector('fixture',env={})
        for newline in ['\n','\r\n']:
            with self.subTest(newline=newline):
                encoded=lambda text:text.replace('\n',newline).encode()
                self.assertIsNone(self.inject.smart_plan_extract(encoded(localized)))
                self.assertIn(boundary.encode(),injector.plan_view(encoded(localized),30,True)[0])
                self.assertNotIn(boundary.encode(),injector.plan_view(encoded(mixed),30,True)[0])
                canonical=mixed.replace('## 目标','## Goal')
                self.assertEqual(canonical.count('## Goal'),1)
                self.assertIn(boundary.encode(),injector.plan_view(encoded(canonical),30,True)[0])


if __name__=='__main__':unittest.main()
