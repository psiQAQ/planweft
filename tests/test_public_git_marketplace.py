"""Input rejection must precede output creation and Docker/network access."""
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('run-public-git-marketplace.py')
spec = importlib.util.spec_from_file_location('public_git_marketplace', SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class PublicGitMarketplaceTest(unittest.TestCase):
    def test_bad_arguments_have_no_side_effects(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'not-created'
            valid = ['--host', 'codex', '--commit', 'a' * 40, '--version', '0.4.0-rc.4',
                     '--output', str(output)]
            cases = [valid + ['--commit', 'main'], valid + ['--version', '../bad'],
                     valid + ['--timeout', '0'], valid + ['--timeout', '601'],
                     valid + ['--output', str(runner.ROOT / 'not-created')],
                     valid + ['--output', temporary], valid + ['--worker'],
                     valid + ['--host', 'pi']]
            for argv in cases:
                with self.subTest(argv=argv), patch('sys.argv', [str(SCRIPT), *argv]), \
                     patch.object(runner.subprocess, 'check_output') as read, \
                     patch.object(runner.subprocess, 'run') as run:
                    with self.assertRaises(SystemExit) as error:
                        runner.main()
                    self.assertEqual(error.exception.code, 2)
                    read.assert_not_called(); run.assert_not_called()
                    self.assertFalse(output.exists())

    def test_inventory_rejects_symlinks_and_records_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            item = root / 'script'; item.write_bytes(b'one\r\n'); item.chmod(0o755)
            first = runner.inventory(root)
            self.assertTrue(first['script']['executable'])
            item.write_bytes(b'one\n')
            self.assertNotEqual(first['script']['sha256'], runner.inventory(root)['script']['sha256'])
            (root / 'link').symlink_to(item)
            with self.assertRaisesRegex(RuntimeError, 'symlink'):
                runner.inventory(root)

    def test_cleanup_failure_cannot_report_success_and_runner_is_archived(self):
        import json
        lock = json.loads((runner.ROOT / 'tests/container-images.json').read_text())
        image = lock['hosts']['codex']['image']
        for remaining in ['', 'owned-container']:
            with self.subTest(remaining=remaining), tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / 'evidence'
                argv = [str(SCRIPT), '--host', 'codex', '--commit', 'a' * 40,
                        '--version', '0.4.0-rc.4', '--output', str(output)]
                success = SimpleNamespace(returncode=0, stdout='', stderr='')
                with patch('sys.argv', argv), patch.dict(runner.os.environ, {'PATH': '/usr/bin'}, clear=True), \
                     patch.object(runner.subprocess, 'check_output', side_effect=[image, remaining]), \
                     patch.object(runner.subprocess, 'run', return_value=success) as execute:
                    self.assertEqual(runner.main(), 1 if remaining else 0)
                self.assertEqual((output / 'runner.py').read_bytes(), SCRIPT.read_bytes())
                self.assertIn('--read-only', execute.call_args_list[0].args[0])
                evidence = json.loads((output / 'container.json').read_text())
                self.assertEqual(evidence['container_removed'], not remaining)


if __name__ == '__main__':
    unittest.main()
