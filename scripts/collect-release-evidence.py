#!/usr/bin/env python3
"""Collect bounded test outputs with private paths redacted and normalized tar ownership."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

NAMES = {'summary.json', 'environment.json', 'cleanup.json', 'pytest.junit.xml',
         'assessment.json', 'before.json', 'after.json', 'process.json', 'invocation.json',
         'prompt.txt', 'stdout.jsonl', 'stderr.txt', 'trace-analysis.json', 'offline-tests.json',
         'independent-byte-checks.json', 'tracked.diff', 'changes.json', 'model-exit.json'}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', action='append', default=[], metavar='LABEL=DIRECTORY')
    p.add_argument('--file', action='append', default=[], metavar='LABEL=FILE')
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    if args.output.exists(): p.error('Output must be new')
    sources = {}
    for value in args.run:
        label, root = value.split('=', 1)
        if not re.fullmatch(r'[a-z0-9-]+', label): p.error('Invalid label')
        root = Path(root)
        for item in sorted(root.glob('*')) + sorted(root.glob('*/*')):
            if item.is_file() and not item.is_symlink() and (item.name in NAMES or item.suffix == '.log'):
                sources[label + '/' + str(item.relative_to(root))] = item
    for value in args.file:
        label, name = value.split('=', 1)
        if not re.fullmatch(r'[a-z0-9.-]+', label): p.error('Invalid label')
        sources[label] = Path(name)
    manifest = {}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(args.output, 'w:gz', format=tarfile.PAX_FORMAT) as archive:
        for name, source in sorted(sources.items()):
            raw = source.read_bytes()
            content = raw.decode('utf-8')
            content = re.sub(r'/home/psi(?=[/\\"\s]|$)', '/home/USER', content)
            content = content.replace('/home/USER/workspace/program-design', '/workspace/planweft')
            # Redact account names in evidence metadata without altering public repository identities.
            data = content.encode()
            manifest[name] = {'original_sha256': hashlib.sha256(raw).hexdigest(),
                              'public_sha256': hashlib.sha256(data).hexdigest(), 'redacted': data != raw}
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
        data = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
        info = tarfile.TarInfo('manifest.json'); info.size = len(data); info.mode = 0o644
        archive.addfile(info, io.BytesIO(data))
    print(json.dumps({'files': len(sources), 'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}))

if __name__ == '__main__': main()
