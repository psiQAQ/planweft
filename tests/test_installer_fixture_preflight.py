"""Reject invalid lifecycle inputs before files or native processes are created."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
import shutil
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('fixture_runner',Path(__file__).with_name('run-installer-lifecycle.py'))
runner=importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)


class FixturePreflightTest(unittest.TestCase):
    def archive(self, path, extra=None, full=False):
        with tarfile.open(path,'w') as archive:
            data=json.dumps({'name':'planweft','version':'0.4.0-rc.8'}).encode()
            item=tarfile.TarInfo('package/package.json'); item.size=len(data)
            archive.addfile(item,io.BytesIO(data))
            if full:
                for host in ('agents','codex','claude','pi','opencode','dsh'):
                    skill='dist/'+host+'/planweft/'+('' if host=='pi' else 'skills/project-docs/')+'SKILL.md'
                    item=tarfile.TarInfo('package/'+skill);item.size=1;archive.addfile(item,io.BytesIO(b'x'))
            if extra: archive.addfile(extra)

    def test_invalid_inputs_have_no_output_or_process_side_effects(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); output=root/'absent/evidence'; archive=root/'input.tar'
            link=tarfile.TarInfo('package/escape'); link.type=tarfile.SYMTYPE; link.linkname='/outside'
            for extra in (None,tarfile.TarInfo('../outside'),link,tarfile.TarInfo('package/package.json')):
                with self.subTest(extra=extra):
                    if extra is not None:self.archive(archive,extra)
                    with patch.object(runner.subprocess,'run',side_effect=AssertionError('native CLI called')):
                        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                            runner.main(['--archive',str(archive),'--output',str(output),'--host','pi'])
                    self.assertFalse(output.parent.exists())
            self.archive(archive)
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                runner.main(['--archive',str(archive),'--output',str(output),'--host','pi','--cli-dir',str(root/'missing')])
            self.assertFalse(output.parent.exists())

    def test_regular_package_is_read_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); archive=root/'input.tar'; self.archive(archive)
            self.assertEqual(runner.validate_archive(archive)['version'],'0.4.0-rc.8')
            self.assertEqual(list(root.iterdir()),[archive])

    def test_preparation_failure_preserves_failed_report_and_missing_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); archive=root/'input.tar'; self.archive(archive)
            output=root/'evidence'
            def fail(*args,**kwargs):
                (output/'项目 with spaces/progress.md').unlink()
                raise OSError('synthetic copy failure')
            with patch.object(shutil,'copytree',side_effect=fail), \
                 patch.object(runner.subprocess,'run',side_effect=AssertionError('native CLI must not run')):
                with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(SystemExit):
                    runner.main(['--archive',str(archive),'--output',str(output),'--host','pi'])
            report=json.loads((output/'summary.json').read_text())
            self.assertEqual(report['status'],'Failed')
            self.assertFalse(report['project_records_unchanged'])
            self.assertIn('synthetic copy failure',report['commands'][-1]['error'])
            self.assertTrue((output/'A/package/package.json').is_file())

    def test_pack_timeout_and_interrupt_always_leave_failed_result(self):
        for error in (KeyboardInterrupt(),runner.subprocess.TimeoutExpired('npm',240,output=b'partial out',stderr=b'partial err')):
            with self.subTest(error=type(error).__name__),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);archive=root/'input.tar';self.archive(archive,full=True);output=root/'evidence'
                with patch.object(runner.subprocess,'run',side_effect=error), \
                     contextlib.redirect_stdout(io.StringIO()),self.assertRaises(SystemExit):
                    runner.main(['--archive',str(archive),'--output',str(output),'--host','pi'])
                report=json.loads((output/'summary.json').read_text())
                self.assertEqual(report['status'],'Failed');self.assertTrue(report['project_records_unchanged'])
                if isinstance(error,runner.subprocess.TimeoutExpired):
                    self.assertEqual((output/'pack-A.log').read_text(),'partial outpartial err')

    def test_same_bytes_symlink_is_not_a_preserved_owned_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);target=root/'actual';target.write_text('same')
            (root/'progress.md').symlink_to(target)
            self.assertFalse(runner.records_unchanged(root,{'progress.md':'same'}))
            (root/'progress.md').unlink();(root/'progress.md').write_text('same')
            self.assertTrue(runner.records_unchanged(root,{'progress.md':'same'}))


if __name__=='__main__':unittest.main()
