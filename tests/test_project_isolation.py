"""Guard the native shared-HOME runner's validation and evidence boundaries."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('run-project-isolation.py')
spec = importlib.util.spec_from_file_location('project_isolation', SCRIPT)
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)


def package(path, version, extra=None):
    with tarfile.open(path, 'w:gz') as archive:
        data = json.dumps({'name': 'planweft', 'version': version}).encode()
        member = tarfile.TarInfo('package/package.json'); member.size = len(data)
        archive.addfile(member, io.BytesIO(data))
        if extra: archive.addfile(extra)
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ProjectIsolationTest(unittest.TestCase):
    def test_pi_relative_source_is_bound_to_project_settings_directory(self):
        project = Path('/synthetic/项目 A')
        expected = str(project / '.planweft/versions/1/package')
        self.assertEqual(runner.pi_project_sources({'packages':['../.planweft/versions/1/package']},project),[expected])
        self.assertEqual(runner.pi_project_sources({'packages':[expected]},project),[expected])
        self.assertEqual(runner.pi_project_sources({'packages':['npm:planweft@1']},project),[])
        self.assertNotIn(expected,runner.pi_project_sources({'packages':['../.planweft/versions/2/package']},project))
        self.assertEqual(runner.pi_project_sources({'packages':[expected,expected]},project).count(expected),2)

    def inputs(self, root):
        old, new = root / 'old.tgz', root / 'new.tgz'
        old_sha = package(old, '0.4.0-rc.3'); new_sha = package(new, '0.4.0-rc.4')
        return ['--host', 'claude', '--archive', str(new), '--sha256', new_sha,
                '--old-archive', str(old), '--old-sha256', old_sha,
                '--output', str(root / 'evidence')]

    def test_invalid_inputs_precede_docker_and_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); argv = self.inputs(root)
            cases = [['--sha256', '0' * 64], ['--timeout', '0'], ['--timeout', '601'],
                     ['--output', str(root)], ['--output', str(runner.ROOT / 'not-created')],
                     ['--archive', str(root / 'missing')], ['--worker'], ['--host', 'unknown']]
            for extra in cases:
                with self.subTest(extra=extra), patch.object(runner.subprocess, 'check_output') as read, \
                     patch.object(runner.subprocess, 'run') as run:
                    with self.assertRaises(SystemExit) as error: runner.main(argv + extra)
                    self.assertEqual(error.exception.code, 2)
                    read.assert_not_called(); run.assert_not_called()
                    self.assertFalse((root / 'evidence').exists())

    def test_archive_rejects_escaping_and_link_members(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'bad.tgz'
            for name, kind in [('package/../escape', tarfile.REGTYPE), ('package/link', tarfile.SYMTYPE),
                               ('package/package.json', tarfile.REGTYPE)]:
                with self.subTest(name=name):
                    item = tarfile.TarInfo(name); item.type = kind; item.linkname = '/outside'
                    digest = package(path, '0.4.0-rc.4', item)
                    with self.assertRaisesRegex(ValueError, 'Unsafe or duplicate'):
                        runner.inspect_archive(path, digest)

    def test_cleanup_failure_forces_failure_and_run_is_archived(self):
        image = json.loads((runner.ROOT / 'tests/container-images.json').read_text())['hosts']['claude']['image']
        for remaining in ['', 'leftover']:
            with self.subTest(remaining=remaining), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); argv = self.inputs(root)
                success = SimpleNamespace(returncode=0, stdout='', stderr='')
                with patch.dict(runner.os.environ, {'PATH': '/usr/bin'}, clear=True), \
                     patch.object(runner.subprocess, 'check_output', side_effect=[image, remaining]), \
                     patch.object(runner.subprocess, 'run', return_value=success) as run:
                    self.assertEqual(runner.main(argv), 1 if remaining else 0)
                self.assertEqual((root / 'evidence/runner.py').read_bytes(), SCRIPT.read_bytes())
                self.assertIn('--read-only', run.call_args_list[0].args[0])
                state = json.loads((root / 'evidence/container.json').read_text())
                self.assertEqual(state['container_removed'], not remaining)


if __name__ == '__main__': unittest.main()
