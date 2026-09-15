"""Public language navigation and portable installation instructions stay usable."""
import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def links(path):
    return re.findall(r'\]\(([^\s)]+)\)', path.read_text())


def commands(path):
    return re.findall(r'^```[^\n]*\n(.*?)^```', path.read_text(), flags=re.M | re.S)


class PublicDocsTest(unittest.TestCase):
    def check_pair(self, chinese, english):
        for path in (chinese, english):
            first = path.read_text().splitlines()[0]
            self.assertIn('[' + '简体中文' + '](' + chinese.name + ')', first, str(path))
            self.assertIn('[English](' + english.name + ')', first, str(path))
            for target in links(path):
                if '://' in target or target.startswith(('#', 'mailto:')):
                    continue
                relative = unquote(target.split('#')[0])
                self.assertTrue((path.parent / relative).exists(), f'{path}: missing {relative}')

    def test_public_documents_have_working_language_pairs_and_identical_commands(self):
        for base in ('README', 'docs/installation', 'docs/architecture',
                     'docs/hosts', 'docs/how-it-works', 'docs/platforms',
                     'docs/reference/runtime-map',
                     'overlays/planweft/README', 'overlays/planweft/install/INSTALL'):
            self.check_pair(ROOT / (base + '.md'), ROOT / (base + '.en.md'))
        cn = ROOT / 'overlays/planweft/install/INSTALL.md'
        en = ROOT / 'overlays/planweft/install/INSTALL.en.md'
        self.assertTrue(commands(cn), 'the complete guide includes executable installation examples')
        self.assertEqual(commands(cn), commands(en), 'translations must not change installation commands')
        for filename in ('docs/installation.md', 'docs/installation.en.md'):
            self.assertEqual(commands(ROOT / filename), commands(cn))

    def test_current_installation_guides_match_package_version(self):
        version = json.loads((ROOT / 'package.json').read_text())['version']
        for filename in ('overlays/planweft/install/INSTALL.md',
                         'overlays/planweft/install/INSTALL.en.md',
                         'docs/installation.md', 'docs/installation.en.md'):
            text = (ROOT / filename).read_text()
            with self.subTest(filename=filename):
                versions = re.findall(r'planweft@(\d+\.\d+\.\d+)', text)
                self.assertTrue(versions, f'{filename}: no concrete package version found')
                self.assertEqual(set(versions), {version})
                self.assertIn(f'PlanWeft {version}', text)

    def test_root_readmes_keep_a_bilingual_source_backed_inventory(self):
        expected = {
            'README.md': ('## 安装后 Agent 得到什么', 'project-docs Skill', '分发存在不等于'),
            'README.en.md': ('## What the agent gets after installation', 'project-docs Skill', 'distribution does not mean'),
        }
        for filename, markers in expected.items():
            text = (ROOT / filename).read_text()
            with self.subTest(filename=filename):
                for marker in markers:
                    self.assertIn(marker, text)
                for source_path in ('skills/project-docs/SKILL.md', 'hooks/',
                                    'task_plan.md', 'findings.md', 'progress.md',
                                    'project-docs'):
                    self.assertIn(source_path, text)

    def test_root_readmes_do_not_expose_engineering_history(self):
        forbidden = ('REP-', 'SPEC-', 'promotion', 'attestation', 'formal promotion',
                     'plans/', 'reproduction/', 'reviews/', 'design-references')
        for filename in ('README.md', 'README.en.md'):
            text = (ROOT / filename).read_text().lower()
            with self.subTest(filename=filename):
                for marker in forbidden:
                    self.assertNotIn(marker.lower(), text)

    def test_package_whitelist_contains_canonical_user_pages_only(self):
        files = json.loads((ROOT / 'package.json').read_text())['files']
        for filename in ('docs/installation.md', 'docs/installation.en.md',
                         'docs/architecture.md', 'docs/architecture.en.md',
                         'docs/hosts.md', 'docs/hosts.en.md'):
            self.assertIn(filename, files)
        for filename in ('docs/how-it-works.md', 'docs/how-it-works.en.md',
                         'docs/platforms.md', 'docs/platforms.en.md',
                         'docs/reference/runtime-map.md', 'docs/reference/runtime-map.en.md',
                         'docs/releasing.md', 'docs/releasing.en.md'):
            self.assertNotIn(filename, files)

    def test_legacy_pages_point_to_canonical_pages(self):
        redirects = {
            'docs/how-it-works.md': 'architecture.md',
            'docs/how-it-works.en.md': 'architecture.en.md',
            'docs/platforms.md': 'hosts.md',
            'docs/platforms.en.md': 'hosts.en.md',
            'docs/reference/runtime-map.md': '../architecture.md',
            'docs/reference/runtime-map.en.md': '../architecture.en.md',
        }
        for filename, target in redirects.items():
            with self.subTest(filename=filename):
                self.assertIn(f']({target})', (ROOT / filename).read_text())

    def test_documentation_map_has_package_safe_local_links(self):
        package_files = set(json.loads((ROOT / 'package.json').read_text())['files'])
        package_files.update({'README.md', 'README.en.md', 'CHANGELOG.md', 'CHANGELOG.en.md'})
        for target in links(ROOT / 'docs/README.md'):
            if '://' in target or target.startswith(('#', 'mailto:')):
                continue
            relative = unquote(target.split('#')[0])
            package_path = Path('docs', relative).as_posix()
            if relative == '../CHANGELOG.md':
                package_path = 'CHANGELOG.md'
            with self.subTest(target=target):
                self.assertIn(package_path, package_files)

    def test_current_user_pages_do_not_repeat_unqualified_legacy_version_claims(self):
        for filename in ('README.md', 'README.en.md',
                         'docs/architecture.md', 'docs/architecture.en.md',
                         'overlays/planweft/README.md', 'overlays/planweft/README.en.md',
                         'overlays/planweft/install/INSTALL.md',
                         'overlays/planweft/install/INSTALL.en.md'):
            with self.subTest(filename=filename):
                self.assertNotIn('0.4.0', (ROOT / filename).read_text())
        for filename in ('docs/hosts.md', 'docs/hosts.en.md'):
            text = (ROOT / filename).read_text()
            with self.subTest(filename=filename):
                self.assertIn('0.4.0', text)
                self.assertTrue('版本绑定' in text or 'version-bound' in text)

    def test_each_standalone_package_retains_both_readme_and_installation_languages(self):
        manifest = json.loads((ROOT / 'dist/manifest.json').read_text())
        for host, item in manifest['platforms'].items():
            package = ROOT / 'dist' / item['path']
            with self.subTest(host=host):
                for base in ('README', 'INSTALL'):
                    self.check_pair(package / (base + '.md'), package / (base + '.en.md'))
                self.assertEqual(commands(package / 'INSTALL.md'), commands(package / 'INSTALL.en.md'))
                for readme in (package / 'README.md', package / 'README.en.md'):
                    self.assertIn('INSTALL.md', links(readme))
                    self.assertIn('INSTALL.en.md', links(readme))

    def test_runtime_reference_covers_distributed_hosts_and_registered_hook_events(self):
        manifest = json.loads((ROOT / 'dist/manifest.json').read_text())
        hook_events = set()
        for path in sorted((ROOT / 'dist').glob('*/planweft/**/*.json')):
            payload = json.loads(path.read_text())
            hooks = payload.get('hooks') if isinstance(payload, dict) else None
            if isinstance(hooks, dict):
                hook_events.update(hooks)
        self.assertTrue(hook_events, 'the generated distributions register Hook events')

        for filename in ('docs/hosts.md', 'docs/hosts.en.md'):
            text = (ROOT / filename).read_text()
            with self.subTest(filename=filename):
                for host in manifest['platforms']:
                    self.assertIn(f'| `{host}` |', text,
                                  f'{filename}: missing manifest host {host}')
                for event in hook_events:
                    self.assertIn(f'`{event}`', text,
                                  f'{filename}: missing registered Hook event {event}')

        for filename in ('docs/architecture.md', 'docs/architecture.en.md'):
            text = (ROOT / filename).read_text()
            with self.subTest(filename=filename):
                self.assertIn('sequenceDiagram', text)
                self.assertIn('SessionStart', text)
                self.assertIn('PreCompact', text)
                self.assertIn('task_plan.md', text)


if __name__ == '__main__':
    unittest.main()
