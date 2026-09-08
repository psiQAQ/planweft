#!/usr/bin/env python3
"""Prepare one npm package and Git release trees. Never publishes or pushes.

The output must be a new directory outside this checkout. --previous-release
continues earlier generated Git branches without rewriting their history.
Remote installation coordinates are emitted only with an explicit repository
URL; they describe prepared artifacts, not a published release.
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
    spec = importlib.util.spec_from_file_location('pw_builder', ROOT / 'scripts/build-plugin.py')
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
    required = ['LICENSE', 'NOTICE', 'package.json', 'README.en.md', 'bin/planweft.mjs',
                'lib/installer.mjs', 'dist/manifest.json', 'docs/installation.md',
                'docs/installation.en.md', *builder.CATALOGS.values()]
    package = json.loads(files['package.json'][0])
    required += [*package['pi']['skills'], *package['pi']['extensions'],
                 package['exports']['.']['import'].removeprefix('./'),
                 package['exports']['.']['types'].removeprefix('./')]
    for path in required:
        if path not in files:
            raise ValueError('npm archive missing ' + path)
    # Check every platform, including nested lockfiles and hook execution bits;
    # the presence of Pi metadata must not bypass OpenCode completeness checks.
    manifest = json.loads(files['dist/manifest.json'][0])
    if package['name'] != 'planweft' or package['version'] != manifest['version']:
        raise ValueError('npm and distribution identities differ')
    for host, item in manifest['platforms'].items():
        for name, expected in item['files'].items():
            key = 'dist/' + item['path'] + '/' + name
            if key not in files or builder.sha(files[key][0]) != expected['sha256']:
                raise ValueError('npm platform file missing or changed: ' + key)
            if bool(files[key][1] & 0o111) != expected['executable']:
                raise ValueError('npm platform execution bit changed: ' + key)
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
        run(['git', '-c', 'user.name=PlanWeft build',
             '-c', 'user.email=build@planweft.invalid', 'commit', '--quiet',
             '--no-gpg-sign', '-m', 'Release planweft ' + builder.VERSION + ' for ' + host],
            destination, env)
    return {'branch': branch, 'commit': run(['git', 'rev-parse', 'HEAD'], destination, env),
            'tree_sha256': builder.tree_digest(files), 'directory': 'git/' + host}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--previous-release', type=Path)
    parser.add_argument('--repository-url')
    parser.add_argument('--release', action='store_true', help='Require clean tracked release inputs')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output == ROOT or ROOT in output.parents:
        parser.error('--output must be a NEW directory outside this checkout')
    if args.repository_url:
        parsed = urlparse(args.repository_url)
        if (parsed.scheme not in {'https', 'ssh'} or not parsed.hostname or parsed.password
                or (parsed.username and not (parsed.scheme == 'ssh' and parsed.username == 'git'))
                or parsed.query or parsed.fragment):
            parser.error('Use a credential-free HTTPS or ssh://git@host repository URL')
    previous = args.previous_release.resolve() if args.previous_release else None
    if previous and not (previous / 'release.json').is_file():
        parser.error('--previous-release must contain release.json')
    builder = builder_module()
    # Verify the exact directory outputs and source binding before copying.
    subprocess.run([os.sys.executable, str(ROOT / 'scripts/build-plugin.py'), '--verify'],
                   cwd=ROOT, check=True)
    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    source_dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT))
    if args.release and source_dirty:
        parser.error('--release requires a clean source checkout')
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
                'repository_url': args.repository_url, 'npm_package': 'planweft'}
    write_json(output / 'release.json', {**manifest, 'status': 'In Progress'})
    try:
        manifest['npm']['planweft'] = npm_archive(builder, ROOT, output / 'npm', env)
        for host in ['gemini', 'hermes']:
            files = builder.read_tree(ROOT / 'dist' / host / builder.PRODUCT)
            manifest['platforms'][host] = git_tree(builder, host, files, output, previous, env)
        manifest['skill_pairs'] = {}
        for host in ['opencode', 'hermes']:
            files = builder.read_tree(ROOT / 'dist' / host / builder.PRODUCT / 'skills/project-docs')
            manifest['skill_pairs'][host] = {
                'source_commit': source_commit, 'source_dirty': source_dirty,
                'path': 'dist/' + host + '/planweft/skills/project-docs',
                'sha256': builder.tree_digest(files), 'files': builder.inventory(files),
                'runtime': (manifest['npm']['planweft']['name'] + '@' + builder.VERSION
                            if host == 'opencode' else manifest['platforms']['hermes']['commit'])}
        write_json(output / 'release.json', manifest)
        print(json.dumps({'output': str(output), 'status': manifest['status']}))
    except Exception as error:
        write_json(output / 'release.json', {**manifest, 'status': 'Failed', 'error': str(error)})
        raise


if __name__ == '__main__':
    main()
