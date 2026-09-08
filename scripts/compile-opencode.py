#!/usr/bin/env python3
"""Rebuild the locked OpenCode V1 runtime; ordinary distribution builds stay offline.

--install permits npm ci in a disposable directory, never in the project.
Alternatively --node-modules uses an existing toolchain installed from the
package's lockfile. --check compiles again and compares without updating files.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    spec = importlib.util.spec_from_file_location('pw_builder', ROOT / 'scripts/build-plugin.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    return builder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--install', action='store_true')
    group.add_argument('--node-modules', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    builder = load_builder()
    original, upstream = builder.read_upstream()
    files = builder.distributions(builder.transform(original), upstream, compiled=False)['opencode']
    inputs = builder.opencode_inputs(files)
    with tempfile.TemporaryDirectory(prefix='pw-opencode-compile-') as directory:
        work = Path(directory)
        builder.write_tree(inputs, work)
        env = {**os.environ, 'npm_config_audit': 'false', 'npm_config_fund': 'false',
               'npm_config_cache': str(work / 'npm-cache')}
        if args.install:
            subprocess.run(['npm', 'ci', '--ignore-scripts', '--no-audit', '--no-fund'],
                           cwd=work, env=env, check=True)
        else:
            modules = args.node_modules.resolve()
            if not (modules / 'typescript/bin/tsc').is_file():
                parser.error('--node-modules must contain the locked TypeScript toolchain')
            (work / 'node_modules').symlink_to(modules, target_is_directory=True)
        subprocess.run(['node', str(work / 'node_modules/typescript/bin/tsc'), '-p', 'tsconfig.json'],
                       cwd=work, env=env, check=True)
        compiler = json.loads((work / 'node_modules/typescript/package.json').read_text())['version']
        lock = json.loads(inputs['package-lock.json'][0])
        expected = lock['packages']['node_modules/typescript']['version']
        if compiler != expected:
            raise ValueError('TypeScript version differs from package-lock.json')
        output = {'dist/' + name: (data, 0o644)
                  for name, (data, _) in builder.read_tree(work / 'dist').items()}
        if 'dist/index.js' not in output:
            raise ValueError('Compiler did not produce dist/index.js')
        manifest = {'source_sha256': builder.tree_digest(inputs), 'inputs': builder.inventory(inputs),
                    'compiler': 'typescript@' + compiler,
                    'command': 'tsc -p tsconfig.json', 'files': builder.inventory(output)}
        output['manifest.json'] = (json.dumps(manifest, indent=2, sort_keys=True).encode() + b'\n', 0o644)
        differences = builder.write_tree(output, ROOT / 'overlays/planweft/opencode-compiled', args.check)
        print(json.dumps({'check': args.check, 'differences': differences, 'compiler': manifest['compiler']}))
        if args.check and differences:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
