"""Reject invalid lifecycle inputs before files or native processes are created."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('fixture_runner',Path(__file__).with_name('run-installer-lifecycle.py'))
runner=importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)


class FixturePreflightTest(unittest.TestCase):
    def archive(self, path, extra=None):
        with tarfile.open(path,'w') as archive:
            data=json.dumps({'name':'planweft','version':'0.4.0-rc.8'}).encode()
            item=tarfile.TarInfo('package/package.json'); item.size=len(data)
            archive.addfile(item,io.BytesIO(data))
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


if __name__=='__main__':unittest.main()
