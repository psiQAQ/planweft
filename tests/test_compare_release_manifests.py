import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'compare_release_manifests', ROOT / 'scripts/compare-release-manifests.py')
COMPARE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COMPARE)


class CompareReleaseManifestsTests(unittest.TestCase):
    def archive(self, root, name, version, files=None):
        path = root / name
        members = {'package.json': json.dumps({'name': 'planweft', 'version': version}).encode(),
                   **(files or {})}
        with tarfile.open(path, 'w:gz') as archive:
            for member, raw in members.items():
                info = tarfile.TarInfo('package/' + member)
                info.size = len(raw)
                archive.addfile(info, io.BytesIO(raw))
        return path

    def test_inventory_and_diff_preserve_exact_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            before = self.archive(root, 'before.tgz', '0.4.0-rc.15', {'same': b'x', 'old': b'a'})
            after = self.archive(root, 'after.tgz', '0.4.0', {'same': b'x', 'old': b'b', 'new': b'c'})
            old_version, old = COMPARE.inventory(before)
            new_version, new = COMPARE.inventory(after)
            self.assertEqual((old_version, new_version), ('0.4.0-rc.15', '0.4.0'))
            self.assertEqual(old['same'], new['same'])
            self.assertNotEqual(old['old'], new['old'])
            self.assertNotIn('new', old)
            self.assertIn('new', new)

    def test_unsafe_member_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'unsafe.tgz'
            with tarfile.open(path, 'w:gz') as archive:
                raw = b'x'
                info = tarfile.TarInfo('../outside')
                info.size = len(raw)
                archive.addfile(info, io.BytesIO(raw))
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                COMPARE.inventory(path)


if __name__ == '__main__':
    unittest.main()
