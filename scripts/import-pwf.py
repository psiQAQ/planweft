#!/usr/bin/env python3
"""Import the approved PWF commit as an immutable archive, without fetching."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7'
TAG = 'v3.17.0'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Existing clean upstream Git checkout')
    args = parser.parse_args()

    def git(*argv):
        return subprocess.check_output(['git', '-C', str(args.source), *argv])

    if git('rev-parse', 'HEAD').decode().strip() != COMMIT:
        parser.error('HEAD does not match the approved upstream commit')
    if git('rev-parse', TAG + '^{}').decode().strip() != COMMIT:
        parser.error('release tag does not resolve to the approved commit')
    if git('status', '--porcelain').strip():
        parser.error('upstream checkout must be clean')
    raw = git('archive', '--format=tar', COMMIT)
    inventory = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        for entry in archive:
            if entry.isdir():
                continue
            if not entry.isfile():
                parser.error('unexpected non-regular upstream entry: ' + entry.name)
            data = archive.extractfile(entry).read()
            inventory[entry.name] = {'sha256': hashlib.sha256(data).hexdigest(),
                                     'size': len(data), 'mode': oct(entry.mode)}
    output = ROOT / 'vendor/planning-with-files'
    output.mkdir(parents=True, exist_ok=True)
    # GzipFile avoids platform-dependent gzip.compress OS header bytes.
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', filename='', mtime=0) as zipped:
        zipped.write(raw)
    packed = buffer.getvalue()
    archive_name = TAG + '.tar.gz'
    (output / archive_name).write_bytes(packed)
    (output / 'inventory.json').write_text(json.dumps(inventory, indent=2, sort_keys=True) + '\n')
    manifest = {'repository': 'https://github.com/OthmanAdi/planning-with-files',
                'tag': TAG, 'commit': COMMIT,
                'tree': git('rev-parse', 'HEAD^{tree}').decode().strip(),
                'archive': archive_name, 'sha256': hashlib.sha256(packed).hexdigest(),
                'file_count': len(inventory), 'license': 'MIT'}
    (output / 'upstream.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (output / 'LICENSE').write_bytes(git('show', COMMIT + ':LICENSE'))
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
