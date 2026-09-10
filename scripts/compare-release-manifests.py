#!/usr/bin/env python3
"""Write the schema-1 per-file npm archive diff required for evidence reuse."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(path):
    files = {}
    with tarfile.open(path, 'r:gz') as archive:
        for item in archive:
            name = PurePosixPath(item.name)
            if (name.is_absolute() or '..' in name.parts or not name.parts
                    or name.parts[0] != 'package' or not (item.isfile() or item.isdir())):
                raise ValueError('Unsafe npm archive member: ' + item.name)
            if item.isdir():
                continue
            relative = str(name.relative_to('package'))
            if relative in files:
                raise ValueError('Duplicate npm archive member: ' + relative)
            files[relative] = hashlib.sha256(archive.extractfile(item).read()).hexdigest()
    if 'package.json' not in files:
        raise ValueError('npm archive lacks package.json')
    with tarfile.open(path, 'r:gz') as archive:
        package = json.load(archive.extractfile('package/package.json'))
    if package.get('name') != 'planweft' or not isinstance(package.get('version'), str):
        raise ValueError('Unexpected npm package identity')
    return package['version'], files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--target', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--reviewer', required=True)
    parser.add_argument('--affected-check', action='append', default=[])
    args = parser.parse_args()
    if args.output.exists():
        parser.error('--output must be new')
    if not args.reviewer.strip():
        parser.error('--reviewer must be non-empty')
    try:
        source_version, source = inventory(args.source)
        target_version, target = inventory(args.target)
        changed = [{'path': name, 'before_sha256': source.get(name),
                    'after_sha256': target.get(name)}
                   for name in sorted(set(source) | set(target))
                   if source.get(name) != target.get(name)]
        if not changed:
            raise ValueError('Source and target archives have no file differences')
        payload = {
            'schema_version': 1,
            'source_version': source_version,
            'source_npm_sha256': sha256(args.source),
            'target_version': target_version,
            'target_npm_sha256': sha256(args.target),
            'changed_files': changed,
            'affected_checks': list(dict.fromkeys(args.affected_check)),
            'reviewer': args.reviewer,
        }
    except (OSError, ValueError, KeyError, tarfile.TarError, json.JSONDecodeError) as error:
        parser.error(str(error))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'changed_files': len(changed), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
