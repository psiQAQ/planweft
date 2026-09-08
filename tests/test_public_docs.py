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
                     'overlays/program-design/README', 'overlays/program-design/install/INSTALL'):
            self.check_pair(ROOT / (base + '.md'), ROOT / (base + '.en.md'))
        cn = ROOT / 'overlays/program-design/install/INSTALL.md'
        en = ROOT / 'overlays/program-design/install/INSTALL.en.md'
        self.assertTrue(commands(cn), 'the complete guide includes executable installation examples')
        self.assertEqual(commands(cn), commands(en), 'translations must not change installation commands')
        for filename in ('docs/installation.md', 'docs/installation.en.md'):
            self.assertEqual(commands(ROOT / filename), commands(cn))

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


if __name__ == '__main__':
    unittest.main()
