#!/usr/bin/env python3
"""Prepare local npm packages and Git release trees. Never publishes or pushes.

The output must be a new directory outside this checkout. --previous-release
continues earlier generated Git branches without rewriting their history.
Remote installation coordinates are emitted only with an explicit repository
URL and npm scope; they describe prepared artifacts, not a published release.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def builder_module():
    spec = importlib.util.spec_from_file_location('pd_builder', ROOT / 'scripts/build-plugin.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(argv, cwd, env):
    return subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True,
                          check=True, timeout=120).stdout.strip()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n')


def npm_archive(builder, source, npm_dir, env):
    records = json.loads(run(['npm', 'pack', '--ignore-scripts', '--json',
                              '--pack-destination', str(npm_dir)], source, env))
    if len(records) != 1:
        raise ValueError('npm pack must produce exactly one archive')
    filename = records[0]['filename']
    if Path(filename).name != filename:
        raise ValueError('Unexpected npm output filename')
    packed = npm_dir / filename
    files = {}
    with tarfile.open(packed, 'r:gz') as archive:
        for item in archive:
            path = PurePosixPath(item.name)
            if path.is_absolute() or '..' in path.parts or path.parts[0] != 'package':
                raise ValueError('Unsafe npm archive member: ' + item.name)
            if item.isdir():
                continue
            if not item.isfile():
                raise ValueError('Unexpected npm archive member type: ' + item.name)
            name = str(path.relative_to('package'))
            if name in files:
                raise ValueError('Duplicate npm member: ' + name)
            files[name] = (archive.extractfile(item).read(), item.mode)
    for required in ['LICENSE', 'UPSTREAM.json', 'package.json', 'INSTALL.md']:
        if required not in files:
            raise ValueError('npm archive missing ' + required)
    package = json.loads(files['package.json'][0])
    if 'pi' in package:
        required = [*package['pi']['skills'], *package['pi']['extensions'], 'scripts/init-session.sh']
    else:
        required = ['dist/index.js', 'BUILD.json', 'skills/project-docs/SKILL.md',
                    'skills/project-docs/scripts/init-session.sh']
    for path in required:
        if path not in files:
            raise ValueError('npm runtime missing ' + path)
    return {'name': package['name'], 'version': package['version'],
            'archive': 'npm/' + filename, 'sha256': builder.sha(packed.read_bytes()),
            'files': builder.inventory(files)}


def git_tree(builder, host, files, output, previous, env):
    destination = output / 'git' / host
    branch = 'release/' + host
    destination.parent.mkdir(exist_ok=True)
    if previous:
        source = previous / 'git' / host
        if run(['git', 'status', '--porcelain'], source, env):
            raise ValueError('Previous release Git tree is dirty: ' + host)
        run(['git', 'clone', '--quiet', '--no-hardlinks', '--branch', branch,
             str(source), str(destination)], output, env)
        # A generated branch repository is not an implicit publishing remote.
        run(['git', 'remote', 'remove', 'origin'], destination, env)
        tracked = run(['git', 'ls-files', '-z'], destination, env).split('\0')
        for name in tracked:
            if name and name not in files:
                builder.safe_name(name)
                (destination / name).unlink()
    else:
        destination.mkdir()
        run(['git', 'init', '--quiet', '--initial-branch=' + branch], destination, env)
    builder.write_files(files, destination)
    run(['git', 'add', '--all'], destination, env)
    if not previous or run(['git', 'diff', '--cached', '--name-only'], destination, env):
        run(['git', '-c', 'user.name=Program Design build',
             '-c', 'user.email=build@program-design.invalid', 'commit', '--quiet',
             '--no-gpg-sign', '-m', 'Release program-design ' + builder.VERSION + ' for ' + host],
            destination, env)
    return {'branch': branch, 'commit': run(['git', 'rev-parse', 'HEAD'], destination, env),
            'tree_sha256': builder.tree_digest(files), 'directory': 'git/' + host}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--previous-release', type=Path)
    parser.add_argument('--repository-url')
    parser.add_argument('--npm-scope')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output == ROOT or ROOT in output.parents:
        parser.error('--output must be a NEW directory outside this checkout')
    if bool(args.repository_url) != bool(args.npm_scope):
        parser.error('--repository-url and --npm-scope must be provided together')
    if args.repository_url:
        parsed = urlparse(args.repository_url)
        if (parsed.scheme not in {'https', 'ssh'} or not parsed.hostname or parsed.password
                or (parsed.username and not (parsed.scheme == 'ssh' and parsed.username == 'git'))
                or parsed.query or parsed.fragment):
            parser.error('Use a credential-free HTTPS or ssh://git@host repository URL')
        args.npm_scope = args.npm_scope.removeprefix('@')
        if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.npm_scope):
            parser.error('Invalid npm scope')
    previous = args.previous_release.resolve() if args.previous_release else None
    if previous and not (previous / 'release.json').is_file():
        parser.error('--previous-release must contain release.json')
    builder = builder_module()
    # Verify the exact directory outputs and source binding before copying.
    subprocess.run([os.sys.executable, str(ROOT / 'scripts/build-plugin.py'), '--verify'],
                   cwd=ROOT, check=True)
    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    source_dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT))
    output.mkdir(parents=True)
    for name in ['npm', 'packages', 'environment']:
        (output / name).mkdir()
    env = {key: value for key, value in os.environ.items()
           if key in {'PATH', 'SystemRoot', 'WINDIR', 'TMPDIR', 'TEMP', 'TMP'}}
    env.update(HOME=str(output / 'environment'), XDG_CONFIG_HOME=str(output / 'environment/config'),
               XDG_CACHE_HOME=str(output / 'environment/cache'),
               npm_config_cache=str(output / 'environment/npm-cache'),
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT='0', GIT_AUTHOR_DATE='2000-01-01T00:00:00Z',
               GIT_COMMITTER_DATE='2000-01-01T00:00:00Z')
    manifest = {'product': builder.PRODUCT, 'version': builder.VERSION,
                'status': 'Prepared locally; not published', 'source_commit': source_commit,
                'source_dirty': source_dirty, 'platforms': {}, 'npm': {},
                'repository_url': args.repository_url, 'npm_scope': args.npm_scope}
    write_json(output / 'release.json', {**manifest, 'status': 'In Progress'})
    try:
        for host in ['pi', 'opencode']:
            source = output / 'packages' / host
            files = builder.read_tree(ROOT / 'dist' / host / builder.PRODUCT)
            package = json.loads(files['package.json'][0])
            if args.npm_scope:
                old_package = dict(package)
                old_lock = json.loads(files['package-lock.json'][0]) if 'package-lock.json' in files else None
                package['name'] = '@' + args.npm_scope + '/program-design-' + host
                package['repository'] = {'type': 'git', 'url': args.repository_url,
                                         'directory': 'dist/' + host + '/program-design'}
                files['package.json'] = ((json.dumps(package, indent=2) + '\n').encode(), 0o644)
                if 'package-lock.json' in files:
                    lock = json.loads(files['package-lock.json'][0])
                    lock['name'] = package['name']
                    lock['packages']['']['name'] = package['name']
                    files['package-lock.json'] = ((json.dumps(lock, indent=2) + '\n').encode(), 0o644)
                if host == 'opencode':
                    # JS is compiled from the reviewed inputs; npm publication
                    # identity is a later JSON-only transformation. Keep both
                    # bindings instead of claiming the renamed manifest was
                    # the original compiler input.
                    build = json.loads(files['BUILD.json'][0])
                    changes = {
                        'package.json.name': {'before': old_package['name'], 'after': package['name']},
                        'package.json.repository': {'before': old_package.get('repository'),
                                                    'after': package['repository']},
                        'package-lock.json.name': {'before': old_lock['name'], 'after': package['name']},
                        'package-lock.json.packages[""].name': {
                            'before': old_lock['packages']['']['name'], 'after': package['name']}}
                    build['identity_transform'] = changes
                    build['identity_transform_sha256'] = builder.sha(
                        json.dumps(changes, sort_keys=True, separators=(',', ':')).encode())
                    build['packaging_inputs'] = builder.inventory(builder.opencode_inputs(files))
                    build['packaging_source_sha256'] = builder.tree_digest(builder.opencode_inputs(files))
                    files['BUILD.json'] = ((json.dumps(build, indent=2, sort_keys=True) + '\n').encode(), 0o644)
            builder.write_tree(files, source)
            manifest['npm'][host] = npm_archive(builder, source, output / 'npm', env)
        for host in ['gemini', 'hermes']:
            files = builder.read_tree(ROOT / 'dist' / host / builder.PRODUCT)
            manifest['platforms'][host] = git_tree(builder, host, files, output, previous, env)
        manifest['skill_pairs'] = {}
        for host in ['opencode', 'hermes']:
            files = builder.read_tree(ROOT / 'dist' / host / builder.PRODUCT / 'skills/project-docs')
            manifest['skill_pairs'][host] = {
                'source_commit': source_commit, 'source_dirty': source_dirty,
                'path': 'dist/' + host + '/program-design/skills/project-docs',
                'sha256': builder.tree_digest(files), 'files': builder.inventory(files),
                'runtime': (manifest['npm']['opencode']['name'] + '@' + builder.VERSION
                            if host == 'opencode' else manifest['platforms']['hermes']['commit'])}
        write_json(output / 'release.json', manifest)
        print(json.dumps({'output': str(output), 'status': manifest['status']}))
    except Exception as error:
        write_json(output / 'release.json', {**manifest, 'status': 'Failed', 'error': str(error)})
        raise


if __name__ == '__main__':
    main()
