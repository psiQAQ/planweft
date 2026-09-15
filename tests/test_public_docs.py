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
        for base in ('README', 'docs/installation', 'docs/platforms',
                     'docs/how-it-works', 'docs/reference/runtime-map',
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
            'README.md': ('## 里面有什么', '受管分发', '静态 manifest/源码审计'),
            'README.en.md': ("## What's inside", 'managed distributions', 'static manifest/source audit'),
        }
        for filename, markers in expected.items():
            text = (ROOT / filename).read_text()
            with self.subTest(filename=filename):
                for marker in markers:
                    self.assertIn(marker, text)
                for source_path in ('bin/planweft.mjs', 'lib/installer.mjs',
                                    'overlays/planweft/', 'dist/manifest.json',
                                    'build-plugin.py', 'project-docs'):
                    self.assertIn(source_path, text)

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

        for filename in ('docs/reference/runtime-map.md',
                         'docs/reference/runtime-map.en.md'):
            text = (ROOT / filename).read_text()
            with self.subTest(filename=filename):
                for host in manifest['platforms']:
                    self.assertIn(f'| `{host}` |', text,
                                  f'{filename}: missing manifest host {host}')
                for event in hook_events:
                    self.assertIn(f'`{event}`', text,
                                  f'{filename}: missing registered Hook event {event}')

        for filename in ('docs/how-it-works.md', 'docs/how-it-works.en.md'):
            text = (ROOT / filename).read_text()
            with self.subTest(filename=filename):
                self.assertIn('sequenceDiagram', text)
                self.assertIn('PLANNING_DISABLED=1', text)


if __name__ == '__main__':
    unittest.main()
