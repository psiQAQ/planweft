#!/usr/bin/env python3
"""Create an isolated, sanitized master history; never changes source refs or pushes.

Only reproduction evidence is rewritten. Commit identities, dates, messages,
parents and executable bits are preserved; rewritten commit/blob IDs are mapped.
Historical digests inside evidence remain original observations, not new hashes.
"""
import argparse
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile


def sanitize(data, name, depth=0):
    if depth > 12:
        raise ValueError('Nested archive depth exceeds audit limit')
    if name.endswith(('.tar.gz', '.tgz', '.tar')):
        output = io.BytesIO()
        changed = False
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as source:
            with tarfile.open(fileobj=output, mode='w', format=tarfile.PAX_FORMAT) as target:
                for original in source:
                    item = copy.copy(original)
                    body = source.extractfile(original).read() if original.isfile() else None
                    new = sanitize(body, item.name, depth + 1) if body is not None else None
                    changed |= new != body or bool(item.uid or item.gid or item.uname or item.gname)
                    item.uid = item.gid = 0
                    item.uname = item.gname = ''
                    item.pax_headers = {k: v for k, v in item.pax_headers.items()
                                        if k not in {'uid', 'gid', 'uname', 'gname'}}
                    if new is not None:
                        item.size = len(new)
                    target.addfile(item, io.BytesIO(new) if new is not None else None)
        if not changed:
            return data
        raw = output.getvalue()
        return raw if name.endswith('.tar') else gzip.compress(raw, mtime=0)
    if name.endswith('.zip'):
        output = io.BytesIO()
        changed = False
        with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(output, 'w') as target:
            for item in source.infolist():
                body = source.read(item)
                new = sanitize(body, item.filename, depth + 1)
                changed |= body != new
                target.writestr(item, new)
        return output.getvalue() if changed else data
    # Replace only the audited local home prefix, including JSON-escaped paths.
    return re.sub(rb'/home/psi(?=[/\\"\s]|$)', b'/home/USER', data)


def git(repo, *args, data=None):
    return subprocess.run(['git', '-C', str(repo), *args], input=data,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout


def rewrite(source, output, expected):
    head = git(source, 'rev-parse', 'refs/heads/master').decode().strip()
    if head != expected:
        raise ValueError('Source master changed')
    if output.exists():
        raise ValueError('Output must not exist')
    git(source, 'clone', '--bare', '--no-hardlinks', str(source), str(output))
    git(output, 'remote', 'remove', 'origin')
    for ref in git(output, 'for-each-ref', '--format=%(refname)').decode().splitlines():
        git(output, 'update-ref', '-d', ref)
    commits, blobs, trees = {}, {}, {}
    records = []
    for commit in git(source, 'rev-list', '--reverse', '--topo-order', head).decode().splitlines():
        raw = git(source, 'cat-file', 'commit', commit)
        header, message = raw.split(b'\n\n', 1)
        if b'\ngpgsig ' in header or b'\nmergetag ' in header:
            raise ValueError('Signed commits need explicit signature handling')
        old_tree = header.splitlines()[0].split()[1].decode()
        if old_tree not in trees:
            git(output, 'read-tree', old_tree)
            for entry in git(source, 'ls-tree', '-rz', old_tree, 'docs/reproduction/evidence').split(b'\0'):
                if not entry:
                    continue
                meta, path = entry.split(b'\t', 1)
                mode, kind, blob = meta.decode().split()
                if kind != 'blob':
                    continue
                name = path.decode()
                key = (blob, name)
                if key not in blobs:
                    original = git(source, 'cat-file', 'blob', blob)
                    new = sanitize(original, name)
                    replacement = git(output, 'hash-object', '-w', '--stdin', data=new).decode().strip()
                    blobs[key] = replacement
                    if replacement != blob:
                        records.append({'path': name, 'original_blob': blob, 'public_blob': replacement,
                                        'original_sha256': hashlib.sha256(original).hexdigest(),
                                        'public_sha256': hashlib.sha256(new).hexdigest()})
                if blobs[key] != blob:
                    git(output, 'update-index', '--cacheinfo', mode, blobs[key], name)
            trees[old_tree] = git(output, 'write-tree').decode().strip()
        lines = []
        for line in header.splitlines():
            if line.startswith(b'tree '):
                line = b'tree ' + trees[old_tree].encode()
            elif line.startswith(b'parent '):
                line = b'parent ' + commits[line.split()[1].decode()].encode()
            lines.append(line)
        new = b'\n'.join(lines) + b'\n\n' + message
        commits[commit] = git(output, 'hash-object', '-t', 'commit', '-w', '--stdin', data=new).decode().strip()
    git(output, 'update-ref', 'refs/heads/master', commits[head])
    git(output, 'symbolic-ref', 'HEAD', 'refs/heads/master')
    # Validate every transformed blob recursively again; sanitization is idempotent.
    for record in records:
        data = git(output, 'cat-file', 'blob', record['public_blob'])
        if sanitize(data, record['path']) != data:
            raise ValueError('Sanitized blob failed second audit')
    report = {'original_head': head, 'public_head': commits[head], 'commits': commits,
              'changed_blobs': records, 'scope': 'docs/reproduction/evidence only',
              'historical_digest_policy': 'Original digests remain historical; consult this mapping.',
              'remote_updated': False}
    (output / 'sanitization.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-head', required=True)
    args = parser.parse_args()
    if not re.fullmatch('[a-f0-9]{40}', args.expected_head):
        parser.error('Expected head must be a full SHA')
    if args.output.exists() or args.source.resolve() in args.output.resolve().parents:
        parser.error('Output must be new and outside source')
    result = rewrite(args.source.resolve(), args.output.resolve(), args.expected_head)
    print(json.dumps({k: result[k] for k in ['original_head', 'public_head', 'remote_updated']}))


if __name__ == '__main__':
    main()
