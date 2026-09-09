"""No Docker/network calls: validation, limits, serial execution and owned cleanup."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('run-registry-containers.py')
spec = importlib.util.spec_from_file_location('registry_containers', SCRIPT)
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
RAM = {'available_memory_bytes': 4 * runner.GIB, 'free_disk_bytes': 8 * runner.GIB}


class RegistryContainerTests(unittest.TestCase):
    def argv(self, root, *extra):
        return ['--host', 'pi', '--version', '0.4.0', '--sha256', 'a' * 64,
                '--output', str(root / 'evidence'), *extra]

    def test_invalid_arguments_precede_output_resources_and_docker(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bad_lock = root / 'bad.json'; bad_lock.write_text('{"schema_version":1,"hosts":{"pi":{"image":"pi:latest"}}}')
            for extra in [['--version', 'latest'], ['--sha256', 'short'], ['--previous-version', '0.4.0-rc.7'],
                          ['--previous-version', '0.4.0', '--previous-sha256', 'b' * 64],
                          ['--timeout', '601'], ['--timeout', '0'], ['--host', 'other'],
                          ['--output', str(root)], ['--output', str(runner.ROOT / 'not-created')],
                          ['--output', str(root / 'bad,path')], ['--image-lock', str(bad_lock)]]:
                with self.subTest(extra=extra), patch('sys.stderr', new_callable=io.StringIO), patch.object(runner, 'resource_preflight') as resources, \
                     patch.object(runner.subprocess, 'run') as run, self.assertRaises(SystemExit) as raised:
                    runner.main(self.argv(root, *extra))
                self.assertEqual(raised.exception.code, 2)
                resources.assert_not_called(); run.assert_not_called()
                self.assertFalse((root / 'evidence').exists())

    def test_authenticated_proxy_is_rejected_without_docker_or_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(runner.os.environ, {'HTTPS_PROXY': 'http://name:secret@proxy.invalid'}, clear=True), \
                 patch('sys.stderr', new_callable=io.StringIO), patch.object(runner.subprocess, 'run') as run, self.assertRaises(SystemExit):
                runner.main(self.argv(root))
            run.assert_not_called(); self.assertFalse((root / 'evidence').exists())

    def test_headroom_thresholds_and_missing_meminfo(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'new'
            for memory, disk, passes in [(4, 8, True), (3, 20, False), (6, 7, False)]:
                with self.subTest(memory=memory, disk=disk), \
                     patch.object(runner.shutil, 'disk_usage', return_value=SimpleNamespace(free=disk * runner.GIB)), \
                     patch.object(Path, 'read_text', return_value=f'MemAvailable: {memory * 1024**2} kB\n'):
                    if passes: self.assertEqual(runner.resource_preflight(output), RAM)
                    else:
                        with self.assertRaises(RuntimeError): runner.resource_preflight(output)
                self.assertFalse(output.exists())
            with patch.object(runner, 'resource_preflight', side_effect=RuntimeError('resource')), \
                 patch.object(runner.subprocess, 'run') as run, self.assertRaises(RuntimeError):
                runner.main(self.argv(Path(temporary)))
            run.assert_not_called(); self.assertFalse((Path(temporary) / 'evidence').exists())

    def test_cleanup_is_label_bound_and_verified_before_cache_deletion(self):
        cases = [(['',], True, False), (['id', 'other-owner'], False, False),
                 (['id', 'token', ''], True, True), (['id', 'token', 'id'], False, True)]
        for responses, removed, rm in cases:
            with self.subTest(responses=responses), patch.object(runner, 'docker_output', side_effect=responses), \
                 patch.object(runner.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run:
                result = runner.cleanup_container('owned-name', 'token')
            self.assertEqual(result['container_removed'], removed)
            if rm: self.assertEqual(run.call_args.args[0], ['docker', 'rm', '-f', 'owned-name'])
            else: run.assert_not_called()
        with patch.object(runner, 'docker_output', side_effect=RuntimeError('daemon unavailable')):
            self.assertFalse(runner.cleanup_container('owned', 'token')['container_removed'])

    def test_only_successful_owned_case_npm_cache_is_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            case = Path(temporary); cache = case / 'run/npm-cache'; cache.mkdir(parents=True)
            bootstrap = case / 'run/cli-bootstrap'; bootstrap.mkdir()
            (bootstrap / 'dependency').write_text('installed temporary CLI dependency')
            (cache / 'rebuildable').write_text('cache')
            (case / 'run/failure-profile').write_text('preserve')
            for passed, removed in [(False, True), (True, False)]:
                runner.clear_success_cache(case, passed, {'container_removed': removed})
                self.assertTrue(cache.exists())
                self.assertTrue(bootstrap.exists())
            self.assertEqual(runner.clear_success_cache(case, True, {'container_removed': True})['status'], 'removed')
            self.assertFalse(cache.exists()); self.assertTrue((case / 'run/failure-profile').exists())
            self.assertFalse(bootstrap.exists())

    def execution(self, root, *, timeout=False, cleanup=True, wrong_binding=False):
        commands = []
        def fake_run(argv, **kwargs):
            commands.append(argv)
            if argv[:3] == ['docker', 'image', 'inspect']:
                return SimpleNamespace(returncode=0, stdout=argv[3] + '\n')
            self.assertEqual(argv[:2], ['docker', 'run'])
            host = argv[argv.index('--host') + 1]
            case = root / 'evidence' / host / 'run'; case.mkdir()
            (case / 'npm-cache').mkdir(); (case / 'npm-cache/retain-on-failure').write_text('cache')
            if timeout: raise subprocess.TimeoutExpired(argv, kwargs['timeout'])
            data = {'status': 'Passed', 'version': '0.4.0', 'npm_sha256': 'a' * 64,
                    'previous_version': None, 'previous_npm_sha256': None,
                    'runner_sha256': hashlib.sha256((runner.ROOT / 'tests/run-registry-smoke.py').read_bytes()).hexdigest()}
            if wrong_binding: data['npm_sha256'] = 'b' * 64
            (case / 'summary.json').write_text(json.dumps(data))
            return SimpleNamespace(returncode=0)
        with patch.object(runner, 'resource_preflight', return_value=RAM), \
             patch.object(runner.subprocess, 'run', side_effect=fake_run), \
             patch.object(runner, 'cleanup_container', return_value={'status': 'Passed' if cleanup else 'Failed', 'container_removed': cleanup}) as clean, \
             patch.dict(runner.os.environ, {'TMPDIR': '/private/temp', 'DEEPSEEK_API_KEY': 'not-forwarded'}, clear=True):
            code = runner.main(self.argv(root, '--host', 'opencode'))
        return code, commands, clean

    def test_limits_frozen_inputs_sequential_execution_and_success_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            code, commands, clean = self.execution(root)
            self.assertEqual(code, 0); self.assertEqual(clean.call_count, 2)
            runs = [a for a in commands if a[:2] == ['docker', 'run']]
            self.assertEqual([a[a.index('--host') + 1] for a in runs], ['pi', 'opencode'])
            for argv in runs:
                for flag in ['--read-only', '--cpus=2', '--memory=3g', '--memory-swap=3g', '--pids-limit=256']:
                    self.assertIn(flag, argv)
                self.assertIn('/tmp:mode=1777,size=512m', argv)
                self.assertIn('TMPDIR=/results/tmp', argv)
                self.assertNotIn('DEEPSEEK_API_KEY', str(argv)); self.assertNotIn('/private/temp', str(argv))
                self.assertTrue(any(x.endswith('dst=/source/tests,readonly') for x in argv))
            frozen = root / 'evidence/frozen'
            self.assertEqual((frozen / 'run-registry-smoke.py').read_bytes(), (runner.ROOT / 'tests/run-registry-smoke.py').read_bytes())
            self.assertFalse((root / 'evidence/pi/run/npm-cache').exists())
            self.assertEqual(json.loads((root / 'evidence/summary.json').read_text())['status'], 'Passed')

    def test_timeout_or_unverified_cleanup_stops_next_host_and_preserves_cache(self):
        for timeout, cleanup in [(True, True), (False, False)]:
            with self.subTest(timeout=timeout, cleanup=cleanup), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                code, commands, clean = self.execution(root, timeout=timeout, cleanup=cleanup)
                self.assertEqual(code, 1); self.assertEqual(clean.call_count, 1)
                self.assertEqual(len([x for x in commands if x[:2] == ['docker', 'run']]), 1)
                self.assertTrue((root / 'evidence/pi/run/npm-cache/retain-on-failure').exists())
                self.assertEqual(json.loads((root / 'evidence/summary.json').read_text())['hosts']['opencode']['status'], 'Not Run')

    def test_worker_pass_cannot_hide_an_artifact_binding_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            code, commands, clean = self.execution(root, wrong_binding=True)
            self.assertEqual(code, 1); self.assertEqual(clean.call_count, 1)
            self.assertTrue((root / 'evidence/pi/run/npm-cache').exists())
            self.assertEqual(json.loads((root / 'evidence/pi/container.json').read_text())['reason'], 'worker failed or evidence binding differs')

    def test_image_identity_mismatch_precedes_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(runner, 'resource_preflight', return_value=RAM), \
                 patch.object(runner, 'docker_output', return_value='sha256:' + '0' * 64), \
                 self.assertRaisesRegex(RuntimeError, 'identity mismatch'):
                runner.main(self.argv(root))
            self.assertFalse((root / 'evidence').exists())


if __name__ == '__main__': unittest.main()
