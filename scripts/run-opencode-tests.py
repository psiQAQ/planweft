#!/usr/bin/env python3
"""Compare pinned upstream and generated native OpenCode runtime in isolated trees.

Downloads only the locked test dependencies. Raw native results are retained
before the two deliberate local contract changes are applied to test fixtures.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output == ROOT or ROOT in output.parents:
        parser.error('--output must be new and outside the checkout')
    spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build-plugin.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    original, upstream = builder.read_upstream()
    transformed = builder.transform(original)
    native = builder.distributions(transformed, upstream, compiled=False)['opencode']
    trees = {}
    for name, source, prefix in [
        ('baseline', original, '.opencode/packages/opencode-planning-with-files/'),
        ('native', transformed, '.opencode/packages/opencode-planweft/'),
    ]:
        files = {p[len(prefix):]: value for p, value in source.items() if p.startswith(prefix)}
        if name == 'native':
            files.update(native)
        trees[name] = files
    output.mkdir(parents=True)
    summary = {'upstream': upstream['commit'], 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'inputs': {}, 'commands': [], 'expected_raw_native_failures': [
                   'Upstream no-plan silence is replaced by a conditional Skill reminder.',
                   'Native templates come from the installed package or explicit skill root, not project discovery.']}
    env = {**os.environ, 'npm_config_registry': 'https://registry.npmjs.org',
           'npm_config_cache': str(output / 'npm-cache')}
    for key in list(env):
        if key.startswith('PWF_') or key in {'PLAN_ID', 'PLANNING_DISABLED', 'PLANNING_WITH_FILES_SKILL_ROOT'}:
            del env[key]

    def run(name, command, cwd):
        with (output / (name + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=600)
        summary['commands'].append({'name': name, 'command': command, 'exit_code': result.returncode})
        (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(name, result.returncode, flush=True)
        return result.returncode

    failures = 0
    for name, files in trees.items():
        work = output / name
        builder.write_tree(files, work)
        summary['inputs'][name] = builder.inventory(files)
        if run(name + '-install', ['npm', 'ci', '--ignore-scripts', '--no-audit', '--no-fund'], work):
            failures += 1
            continue
        failures += bool(run(name + '-typecheck', ['npm', 'run', 'typecheck'], work))
        results = output / (name + '-raw.json')
        code = run(name + '-raw', ['npm', 'test', '--', '--reporter=default',
                                  '--reporter=json', '--outputFile=' + str(results)], work)
        if name == 'baseline':
            failures += bool(code)
            continue
        report = json.loads(results.read_text())
        failed = [test['title'] for suite in report['testResults']
                  for test in suite['assertionResults'] if test['status'] == 'failed']
        expected = ['injects nothing without a plan, when disabled, or for a broken pin; announces ambiguity',
                    'uses a real skill template when one is discoverable, and rejects unknown modes']
        raw_matches = sorted(failed) == sorted(expected) and report['numFailedTests'] == 2 and report['numPendingTests'] == 0 and code == 1
        summary['raw_native_expected_failure_set_matches'] = raw_matches
        summary['raw_native_failed_tests'] = failed
        failures += not raw_matches
        # These two intentional protocol differences remain visible in raw logs.
        plugin = work / '__tests__/plugin.test.ts'
        text = plugin.read_text()
        needle = 'expect(none.output.parts).toHaveLength(0)'
        if text.count(needle) != 1:
            raise ValueError('Review upstream no-plan test before adapting')
        plugin.write_text(text.replace(needle, 'expect(none.output.parts[0]?.text).toContain("project-docs")'))
        core = work / '__tests__/core.test.ts'
        text = core.read_text()
        needle = '    const legacy = initPlan(root, {}, env)'
        if text.count(needle) != 1:
            raise ValueError('Review upstream template fixture before adapting')
        core.write_text(text.replace(needle, '    env.PLANNING_WITH_FILES_SKILL_ROOT = path.dirname(skill)\n' + needle))
        (work / '__tests__/workflow.test.ts').write_bytes((ROOT / 'tests/opencode-workflow.test.ts').read_bytes())
        summary['adapted_tests'] = builder.inventory(builder.read_tree(work / '__tests__'))
        failures += bool(run(name + '-contracts', ['npm', 'test'], work))
    summary['status'] = 'Failed' if failures else 'Passed'
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
