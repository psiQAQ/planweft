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
                    description=re.search(r'^description: (.+)$',text,re.M).group(1)
                    self.assertLess(len(description),600)
                    manual=str(base/'references/pwf-workflow.md')
                    self.assertIn(manual,files)
                    self.assertGreater(len(files[manual][0]),1000)
                    # References and runtime helpers survive copying this folder.
                    for target in re.findall(r'\]\(([^)]+)\)',text):
                        if target.startswith('references/'):
                            self.assertIn(str(base/target),files)
                    for helper in ('resolve-plan-dir.sh','init-session.sh'):
                        self.assertIn(str(base/'scripts'/helper),files)
                    self.assertIn(str(base/'references/plan-selection.md'),files)

    def test_discovery_discloses_consent_and_actual_host_limits(self):
        for host, files in self.packages.items():
            for path, (raw, _) in files.items():
                if not (path.endswith('SKILL.md') or '/references/language-variants/' in '/' + path and path.endswith('/GUIDE.md')): continue
                with self.subTest(host=host, path=path):
                    description=re.search(r'^description: (.+)$',raw.decode(),re.M).group(1)
                    self.assertIn('selected project planning context',description)
                    self.assertIn('never runs commands declared in Markdown',description)
                    self.assertIn('no network upload path',description)
                    if host=='kiro':
                        self.assertIn('timestamps only, not agent transcript stores',description)
                        self.assertIn('registers no Stop hook',description)
                    else:
                        self.assertIn('Automatic recovery reads project planning files only',description)
                        self.assertIn('Explicit requests only: --metadata / --replay',description)
                    if host=='continue':
                        self.assertIn('registers no lifecycle or Stop hook',description)
                        self.assertIn('never requests continuation',description)
                    elif host=='gemini':
                        self.assertIn('session-end hook reports status only',description)
                        self.assertIn('does not request continuation',description)
                    elif host!='kiro':
                        self.assertIn('Optional gated mode can request continuation only when the host supports it',description)
                    if host in {'continue','gemini'}:
                        manual=files[str(PurePosixPath(path).parent/'references/pwf-workflow.md')][0].decode()
                        self.assertTrue(manual.startswith('## Installed adapter boundary'))
                        self.assertIn('does not establish this adapter',manual)
                        self.assertIn('## Adapter metadata from the fixed upstream',manual)

    def test_language_entries_are_explicit_and_use_the_same_resource_contract(self):
        for locale in ('ar','de','es','zh','zht'):
            path='skills/i18n/project-docs-'+locale+'/SKILL.md'
            text=self.tree[path][0].decode()
            self.assertIn('disable-model-invocation: true',text)
            self.assertIn((ROOT/'overlays/planweft/entrypoints'/f'{locale}.md').read_text().strip(),text)
            for token in ('PLAN_ID','PWF_PLAN_ROOT','PLANNING_DISABLED=1','task_plan.md','findings.md','progress.md'):
                self.assertIn(token,text)

    def test_adapter_manual_notice_resolves_localized_entry(self):
        for host in ('continue', 'gemini'):
            files=self.packages[host]
            for path,(raw,_) in files.items():
                if not path.endswith('/references/pwf-workflow.md'): continue
                with self.subTest(host=host,path=path):
                    self.assertTrue(raw.startswith(b'## Installed adapter boundary'))
                    entry=re.search(rb'\[entry\]\(\.\./([^/)]+)\)',raw).group(1).decode()
                    self.assertIn(str(PurePosixPath(path).parent.parent/entry),files)


if __name__=='__main__': unittest.main()
