#!/usr/bin/env python3
"""Installed Skill resources remain complete without duplicate native discovery.

Builds packages in memory from fixed inputs; does not write generated artifacts.
"""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PORTABLE_HOSTS = ('cursor', 'copilot', 'gemini', 'hermes', 'opencode', 'factory', 'codebuddy', 'kiro')
LANGUAGES = ('ar', 'de', 'es', 'zh', 'zht')


class NativeResourcePathsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('pw_resource_builder', ROOT / 'scripts/build-plugin.py')
        cls.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.builder)
        upstream, provenance = cls.builder.read_upstream()
        cls.tree = cls.builder.transform(upstream)
        cls.packages = cls.builder.distributions(cls.tree, provenance, compiled=False)

    def test_copying_main_skill_retains_complete_language_resources(self):
        for host in PORTABLE_HOSTS:
            files = self.packages[host]
            main = 'skills/project-docs/'
            skill = {name[len(main):]: value for name, value in files.items() if name.startswith(main)}
            with self.subTest(host=host):
                self.assertEqual([name for name in skill if name.endswith('SKILL.md')], ['SKILL.md'],
                                 'recursive host scanners must discover only the main entry')
                self.assertIn('`references/language-variants/project-docs-<language>/GUIDE.md`',
                              skill['SKILL.md'][0].decode())
                self.assertFalse(any(name.startswith('language-variants/') for name in files))
                for language in LANGUAGES:
                    base = 'references/language-variants/project-docs-' + language + '/'
                    for required in ['GUIDE.md', 'scripts/init-session.sh', 'templates/task_plan.md',
                                     'references/evidence.md', 'LICENSE', 'UPSTREAM.json']:
                        self.assertIn(base + required, skill, host + ': ' + base + required)
                    # Packaging may normalize headers and bridge inject-plan.py,
                    # but moving a complete variant must preserve all other assets.
                    original = 'skills/i18n/project-docs-' + language + '/'
                    for name, value in self.tree.items():
                        if name.startswith(original) and not name.endswith(('/SKILL.md', '/inject-plan.py')):
                            observed=skill[base + name[len(original):]]
                            if host=='gemini' and name.endswith('/references/pwf-workflow.md'):
                                # The receiving-host capability notice is additive:
                                # retain every original manual byte and executable mode.
                                self.assertTrue(observed[0].startswith(b'## Installed adapter boundary'))
                                self.assertTrue(observed[0].endswith(value[0]))
                                self.assertEqual(observed[1],value[1])
                                continue
                            self.assertEqual(observed, value,
                                             host + ': relocated asset differs: ' + name)

    def test_codex_and_claude_keep_their_native_language_layout(self):
        for host in ('codex', 'claude'):
            with self.subTest(host=host):
                for language in LANGUAGES:
                    self.assertIn('skills/i18n/project-docs-' + language + '/SKILL.md', self.packages[host])
                self.assertFalse(any('/references/language-variants/' in name for name in self.packages[host]))

    def test_kiro_commands_use_installed_skill_and_project_working_directory(self):
        files = self.packages['kiro']
        body = files['skills/project-docs/SKILL.md'][0].decode()
        self.assertNotIn('.kiro/skills/project-docs/', body)
        self.assertIn('PD_KIRO_SKILL_ROOT=', body)
        self.assertIn('$PdKiroSkillRoot =', body)
        self.assertIn('.kiro/plan/task_plan.md', body)
        self.assertIn('.kiro/steering/planning-context.md', body)
        self.assertIn('sh "$PD_KIRO_SKILL_ROOT/assets/scripts/bootstrap.sh"', body)
        self.assertIn('pwsh -ExecutionPolicy RemoteSigned -File "$PdKiroSkillRoot/assets/scripts/bootstrap.ps1"', body)
        for command in ('session-catchup.py', 'check-complete.sh', 'check-complete.ps1'):
            self.assertIn('/assets/scripts/' + command + '"', body)
        # Exercise the documented POSIX bootstrap from a separate project,
        # with installation and project paths containing spaces/non-ASCII.
        with tempfile.TemporaryDirectory(prefix='pw-kiro-resource-') as temporary:
            base = Path(temporary)
            installed = base / 'Power cache 中文' / 'skills' / 'project-docs'
            project = base / 'Target project 中文'
            project.mkdir()
            for name, (data, mode) in files.items():
                prefix = 'skills/project-docs/'
                if name.startswith(prefix):
                    target = installed / name[len(prefix):]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    target.chmod(mode)
            home = base / 'home'
            home.mkdir()
            env = {'PATH': '/usr/bin:/bin', 'HOME': str(home), 'PD_KIRO_SKILL_ROOT': str(installed),
                   'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}
            run = subprocess.run(['sh', str(installed / 'assets/scripts/bootstrap.sh')], cwd=project,
                                 env=env, text=True, capture_output=True, timeout=20)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            for path in ('.kiro/plan/task_plan.md', '.kiro/plan/findings.md', '.kiro/plan/progress.md',
                         '.kiro/steering/planning-context.md'):
                self.assertTrue((project / path).is_file(), path)
            self.assertFalse((installed / '.kiro').exists(), 'project records must not enter the package cache')
            before = {name: (project / '.kiro/plan' / name).read_bytes()
                      for name in ('task_plan.md', 'findings.md', 'progress.md')}
            rerun = subprocess.run(['sh', str(installed / 'assets/scripts/bootstrap.sh')], cwd=project,
                                   env=env, text=True, capture_output=True, timeout=20)
            self.assertEqual(rerun.returncode, 0, rerun.stdout + rerun.stderr)
            self.assertEqual(before, {name: (project / '.kiro/plan' / name).read_bytes() for name in before})


if __name__ == '__main__':
    unittest.main()
