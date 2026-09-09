"""Actual initialization must not create a second live phase/status record."""
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


class RecordTemplatesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = module('pw_record_builder', 'scripts/build-plugin.py')
        cls.records = module('pw_records', 'overlays/planweft/record_templates.py')
        cls.upstream, _ = cls.builder.read_upstream()
        cls.tree = cls.builder.transform(cls.upstream)

    def test_all_template_copies_and_locales_have_one_live_state_source(self):
        seen = set()
        for path, (content, _) in self.tree.items():
            if not path.endswith('/templates/progress.md') and path != 'templates/progress.md':
                continue
            with self.subTest(path=path):
                locale = re.search(r'/i18n/project-docs-([^/]+)/', '/' + path)
                locale = locale[1] if locale else 'en'
                seen.add(locale)
                words = self.records.LOCALES[locale]
                text = content.decode()
                self.assertNotRegex(text, r'\b(?:pending|in_progress)\b')
                self.assertNotRegex(text, r'(?m)^### ' + re.escape(words['phase']) + r' [12][:：]')
                self.assertIn('### ' + words['work'], text)
                self.assertIn(words['live'], text)
                self.assertGreaterEqual(text.count('[task_plan.md](task_plan.md)'), 4)
        self.assertEqual(seen, set(self.records.LOCALES))

    def test_build_reads_utf8_even_with_a_windows_legacy_default(self):
        original=Path.read_text
        def legacy_default(path,*args,**kwargs):
            if not args and kwargs.get('encoding') is None:
                kwargs['encoding']='cp1252'
            return original(path,*args,**kwargs)
        with patch.object(Path,'read_text',legacy_default):
            upstream,metadata=self.builder.read_upstream()
            tree=self.builder.transform(upstream)
            platforms=self.builder.distributions(tree,metadata)
        self.assertEqual(tree,self.tree)
        self.assertIn('opencode',platforms)
        self.assertIn('dsh',platforms)

    def test_findings_guidance_reaches_default_analytics_and_localized_templates(self):
        for path, (content, _) in self.tree.items():
            if '/templates/' not in '/' + path or Path(path).name not in {'findings.md', 'analytics_findings.md'}:
                continue
            locale = re.search(r'/i18n/project-docs-([^/]+)/', '/' + path)
            words = self.records.LOCALES[locale[1] if locale else 'en']
            # Upstream has no localized analytics template. The builder fills
            # that absent asset from the canonical English template unchanged.
            if locale and Path(path).name == 'analytics_findings.md':
                self.assertEqual(content, self.tree['skills/project-docs/templates/analytics_findings.md'][0])
                words = self.records.LOCALES['en']
            with self.subTest(path=path):
                self.assertIn(words['observations'], content.decode())

    def test_initializer_patches_preserve_task_plan_and_existing_file_guards(self):
        for path, (raw, _) in self.upstream.items():
            if not path.endswith(('init-session.sh', 'init-session.ps1')):
                continue
            target = self.builder.map_path(path)
            original = self.builder.identity_text(raw.decode())
            result = self.records.transform(target, original)
            locale = re.search(r'/i18n/project-docs-([^/]+)/', '/' + target)
            words = self.records.LOCALES[locale[1] if locale else 'en']
            title = '# ' + words['findings'] + '\n'
            with self.subTest(path=path):
                # Everything before the findings body, including the complete
                # task_plan here-doc and skip-existing branches, is unchanged.
                self.assertEqual(original.split(title)[0], result.split(title)[0])
                self.assertEqual(original.count('Test-Path'), result.count('Test-Path'))
                self.assertEqual(original.count('[ ! -f'), result.count('[ ! -f'))
                self.assertNotIn('### ' + words['current'] + '\n', result)
                self.assertIn(words['observations'], result)

    def test_patch_guards_reject_drift_and_do_not_apply_twice(self):
        path = 'skills/project-docs/templates/progress.md'
        text = self.upstream['skills/planning-with-files/templates/progress.md'][0].decode()
        for changed in [text.replace('### Phase 2:', '### Phase 3:'),
                        text.replace('**Status:** in_progress', '**Status:** complete'),
                        self.records.transform(path, text)]:
            with self.subTest(changed=changed[:30]):
                with self.assertRaises(ValueError): self.records.transform(path, changed)
        path = 'scripts/init-session.sh'
        text = self.upstream[path][0].decode()
        with self.assertRaises(ValueError):
            self.records.transform(path, text.replace('### Current Status', '### Other heading', 1))

    def test_opencode_fallback_gets_the_same_record_guidance(self):
        path = '.opencode/packages/opencode-planweft/src/core.ts'
        text = self.tree[path][0].decode()
        for name, guidance in [('findings.md', self.records.LOCALES['en']['observations']),
                               ('progress.md', self.records.LOCALES['en']['live'])]:
            block = text.split('"' + name + '": [', 1)[1].split('].join("\\n")', 1)[0]
            self.assertIn(json.dumps(guidance), block)
            self.assertNotIn('Current Status', block)

    def test_upstream_contract_adaptation_is_limited_to_two_progress_tokens(self):
        path='tests/test_template_transparency.py'
        original=self.upstream[path][0].decode()
        expected=original.replace('"### Phase 1: [Title]"','"### Recorded work"').replace(
            '"### Phase 2: [Title]"','"[task_plan.md](task_plan.md)"')
        self.assertEqual(self.records.transform(path,original),expected)
        with self.assertRaises(ValueError):self.records.transform(path,expected)

    def install_skill(self, directory, locale):
        root = directory / ('插件 files ' + locale)
        prefix = 'skills/' + ('project-docs' if locale == 'en' else 'i18n/project-docs-' + locale) + '/'
        for path, (content, mode) in self.tree.items():
            if not path.startswith(prefix): continue
            relative = path[len(prefix):]
            if not relative.startswith(('scripts/', 'templates/')): continue
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            target.chmod(mode)
        return root

    def initialize_and_preserve(self, executable, extension, locale, template):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = self.install_skill(root, locale)
            project = root / '任务 project'
            project.mkdir()
            script = skill / 'scripts' / ('init-session.' + extension)
            if extension == 'sh':
                command = [executable, script.as_posix()]
                if template == 'analytics': command += ['--template', 'analytics']
            else:
                command = [executable, '-NoProfile', '-NonInteractive', '-File', str(script)]
                if template == 'analytics': command += ['-Template', 'analytics']
            environment = {k: v for k, v in os.environ.items()
                           if not k.startswith('PWF_') and k not in {'PLAN_ID', 'PLANNING_DISABLED'}}
            # Avoid invoking user profiles or importing unrelated Python code.
            environment['PYTHONDONTWRITEBYTECODE'] = '1'
            def run():
                result = subprocess.run(command, cwd=project, env=environment,
                                        capture_output=True, timeout=45)
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            run()
            words = self.records.LOCALES[locale]
            progress = (project / 'progress.md').read_text(encoding='utf-8-sig')
            findings = (project / 'findings.md').read_text(encoding='utf-8-sig')
            plan = (project / 'task_plan.md').read_text(encoding='utf-8-sig')
            self.assertIn(words['live'], progress)
            self.assertNotIn('### ' + words['current'], progress)
            self.assertIn(words['observations'], findings)
            self.assertIn('in_progress', plan)
            self.assertIn('pending', plan)
            if template == 'analytics':
                self.assertIn('### Query Log', progress)
                self.assertIn('## Data Sources', findings)
            # A second initialization must not touch user records, including
            # CRLF and edits made after the initial creation.
            expected = {}
            for name in ('task_plan.md', 'findings.md', 'progress.md'):
                expected[name] = (project / name).read_bytes() + '\r\n用户修改\r\n'.encode()
                (project / name).write_bytes(expected[name])
            run()
            self.assertEqual({name: (project / name).read_bytes() for name in expected}, expected)

    @unittest.skipUnless(shutil.which('bash'), 'Bash unavailable; actual initialization Not Run')
    def test_actual_shell_default_analytics_and_five_locales(self):
        for locale, template in [('en', 'default'), ('en', 'analytics')] + [(x, 'default') for x in ('zh', 'zht', 'ar', 'de', 'es')]:
            with self.subTest(locale=locale, template=template):
                self.initialize_and_preserve(shutil.which('bash'), 'sh', locale, template)

    @unittest.skipUnless(shutil.which('pwsh') or shutil.which('powershell'), 'PowerShell unavailable; actual initialization Not Run')
    def test_actual_powershell_default_analytics_and_five_locales(self):
        executable = shutil.which('pwsh') or shutil.which('powershell')
        for locale, template in [('en', 'default'), ('en', 'analytics')] + [(x, 'default') for x in ('zh', 'zht', 'ar', 'de', 'es')]:
            with self.subTest(locale=locale, template=template):
                self.initialize_and_preserve(executable, 'ps1', locale, template)


if __name__ == '__main__':
    unittest.main()
