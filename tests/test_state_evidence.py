"""Generated state-evidence assets stay byte-identical across host bundles."""
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOSTS = ('codex', 'claude', 'pi', 'opencode', 'hermes', 'cursor', 'gemini',
         'copilot', 'mastracode', 'kiro', 'continue', 'factory', 'codebuddy', 'agents', 'dsh')


class StateEvidenceDistributionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('state_builder', ROOT / 'scripts/build-plugin.py')
        cls.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.builder)
        upstream, provenance = cls.builder.read_upstream()
        cls.tree = cls.builder.transform(upstream)
        cls.bundles = cls.builder.distributions(cls.tree, provenance, compiled=False)

    def test_shared_state_source_and_root_cli_are_generated(self):
        expected = {path.relative_to(ROOT / 'overlays/planweft/state').as_posix(): path.read_bytes()
                    for path in (ROOT / 'overlays/planweft/state').rglob('*') if path.is_file()}
        self.assertEqual(expected, {name[len('state/'):]: data for name, (data, _) in self.tree.items()
                                    if name.startswith('state/')})
        self.assertEqual((ROOT / 'lib/state/core.mjs').read_bytes(), expected['core.mjs'])
        self.assertEqual((ROOT / 'lib/state/cli.mjs').read_bytes(), expected['cli.mjs'])
        self.assertIn('state/cli.mjs', {path.relative_to(ROOT / 'dist/codex/planweft').as_posix()
                                        for path in (ROOT / 'dist/codex/planweft').rglob('*') if path.is_file()})

    def test_each_host_gets_same_core_and_data_only_wrapper(self):
        for host in HOSTS:
            with self.subTest(host=host):
                files = self.bundles[host]
                core_paths = [name for name in files if name.endswith('state/core.mjs')]
                cli_paths = [name for name in files if name.endswith('state/cli.mjs')]
                self.assertTrue(core_paths)
                self.assertTrue(cli_paths)
                self.assertEqual(files[core_paths[0]][0], self.bundles['codex']['state/core.mjs'][0])
                self.assertEqual(files[cli_paths[0]][0], self.bundles['codex']['state/cli.mjs'][0])
                wrapper = files['scripts/pw-state.mjs'][0].decode()
                self.assertIn("process.argv.slice(2)", wrapper)
                self.assertIn("state/cli.mjs", wrapper)
                self.assertNotIn('child_process', wrapper)
                entries = [name for name in files if name.endswith('/SKILL.md') or name == 'SKILL.md']
                for entry in entries:
                    base = Path(entry).parent
                    self.assertIn(str(base / 'state/core.mjs'), files)
                    self.assertIn(str(base / 'scripts/pw-state.mjs'), files)


if __name__ == '__main__':
    unittest.main()
