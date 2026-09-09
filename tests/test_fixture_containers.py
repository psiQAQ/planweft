"""Offline fixture-wrapper boundary checks; not native lifecycle evidence."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('fixture_wrapper',Path(__file__).with_name('run-fixture-containers.py'))
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class FixtureWrapperTest(unittest.TestCase):
    def args(self,root):
        archive=root/'input.tgz'
        with tarfile.open(archive,'w:gz') as tar:
            data=b'{"name":"planweft","version":"0.4.0-rc.8"}'
            item=tarfile.TarInfo('package/package.json');item.size=len(data);tar.addfile(item,io.BytesIO(data))
        return ['--host','pi','--archive',str(archive),'--sha256',hashlib.sha256(archive.read_bytes()).hexdigest(),
                '--output',str(root/'evidence')]

    def test_invalid_inputs_have_no_docker_or_output_effect(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);args=self.args(root)
            for extra in (['--sha256','0'*64],['--timeout','601'],['--host','unknown']):
                with self.subTest(extra=extra),patch.object(runner.registry,'docker_output') as docker, \
                     contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):runner.main(args+extra)
                docker.assert_not_called();self.assertFalse((root/'evidence').exists())

    def test_resource_shortage_does_not_create_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);args=self.args(root)
            with patch.object(runner.registry,'resource_preflight',side_effect=RuntimeError('low resources')), \
                 patch.object(runner.registry,'docker_output') as docker:
                with self.assertRaisesRegex(RuntimeError,'low resources'):runner.main(args)
                docker.assert_not_called();self.assertFalse((root/'evidence').exists())

    def test_timeout_is_archived_cleanup_checked_and_next_host_not_started(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);args=self.args(root)+['--host','dsh','--timeout','41']
            def docker(args):return args[2]
            with patch.object(runner.registry,'resource_preflight',return_value={'fixture':True}), \
                 patch.object(runner.registry,'docker_output',side_effect=docker), \
                 patch.object(runner.registry,'cleanup_container',return_value={'status':'Failed','container_removed':False}), \
                 patch.object(runner.subprocess,'run',side_effect=runner.subprocess.TimeoutExpired('fixture',41)) as launch:
                self.assertEqual(runner.main(args),1)
            self.assertEqual(launch.call_count,1);self.assertEqual(launch.call_args.kwargs['timeout'],41)
            command=launch.call_args.args[0]
            for limit in ('--cpus=2','--memory=3g','--memory-swap=3g','--pids-limit=256','/tmp:mode=1777,size=512m'):
                self.assertIn(limit,command)
            report=json.loads((root/'evidence/summary.json').read_text())
            self.assertEqual(report['status'],'Failed');self.assertEqual(report['hosts']['dsh']['status'],'Not Run')
            self.assertFalse(report['hosts']['pi']['cleanup']['container_removed'])
            self.assertEqual(report['hosts']['pi']['npm_cache']['status'],'preserved')


if __name__=='__main__':unittest.main()
