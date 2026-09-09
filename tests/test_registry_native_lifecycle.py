"""Offline contracts for remote native lanes, not actual-host acceptance evidence."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('run-registry-smoke.py')
spec = importlib.util.spec_from_file_location('registry_native', SCRIPT)
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
OLD, NEW = '0.4.0-rc.7', '0.4.0'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) if not isinstance(value, str) else value)


def commands(root, version):
    return [{'name': name, 'source': kind, 'sourceInfo': {
        'source': 'npm:planweft@' + version, 'baseDir': str(root),
        'path': str(root / 'dist/pi/planweft' / suffix)}}
        for name, kind, suffix in [('pw-plan-status', 'extension', 'extensions/planweft/index.ts'),
                                   ('skill:project-docs', 'skill', 'SKILL.md')]]


class NativeFixture:
    """Explicit fake CLI: only exercises runner sequencing and assertion failures."""
    def __init__(self, root):
        self.out = root / 'run'; self.out.mkdir()
        self.profile = self.out / 'profile'; self.profile.mkdir()
        self.packages = {}
        self.calls = []
        for version in [OLD, NEW]:
            package = root / version
            write(package / 'package.json', {'name': 'planweft', 'version': version})
            write(package / 'bin/planweft.mjs', version)
            write(package / 'dist/pi/planweft/SKILL.md', version)
            write(package / 'dist/pi/planweft/extensions/planweft/index.ts', version)
            write(package / 'dist/opencode/planweft/skills/project-docs/SKILL.md', version)
            write(package / 'dist/dsh/planweft/skills/project-docs/SKILL.md', version)
            write(package / 'dist/dsh/planweft/index.mjs', version)
            self.packages[version] = package

    def install(self, version, target):
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(self.packages[version], target)

    def rpc(self, project, env, log):
        root = project / '.pi/npm/node_modules/planweft'
        if not root.exists(): return []
        return commands(root, json.loads((root / 'package.json').read_text())['version'])

    def run(self, label, argv, cwd):
        self.calls.append((label, argv))
        if argv[0] == 'pi':
            root = cwd / '.pi/npm/node_modules/planweft'
            if argv[1] == 'install':
                self.install(argv[2].split('@')[-1], root)
                write(cwd / '.pi/settings.json', {'packages': [argv[2]]})
            elif argv[1] == 'remove':
                shutil.rmtree(root); write(cwd / '.pi/settings.json', {'packages': []})
            return (cwd / '.pi/settings.json').read_text()
        if argv[0] == 'node':
            package = Path(argv[1]).parent.parent
            skill = cwd / '.opencode/skills/project-docs'
            if skill.exists(): shutil.rmtree(skill)
            if argv[2] != 'remove':
                shutil.copytree(package / 'dist/opencode/planweft/skills/project-docs', skill)
            return ''
        if argv[0] == 'opencode':
            data = json.loads((cwd / 'opencode.json').read_text())
            sources = [x for x in data['plugin'] if x.startswith('planweft@')]
            if argv[2] == 'agent':
                if sources:
                    version = sources[0].split('@')[-1]
                    cache = self.profile / '.cache/opencode/packages' / ('planweft@' + version)
                    self.install(version, cache / 'node_modules/planweft')
                    write(cache / 'package.json', {'dependencies': {'planweft': version}})
                return json.dumps({'tools': {x: True for x in ['pw_init', 'pw_status', 'pw_check']} if sources else {'bash': True}})
            skill = cwd / '.opencode/skills/project-docs/SKILL.md'
            return json.dumps([{'name': 'project-docs', 'location': str(skill)}] if skill.exists() else [])
        if argv[0] == 'dsh':
            prof = self.profile / '.dsh/profiles/headless'
            root = prof / 'node_modules/planweft'
            if argv[1] == 'plugin':
                if argv[4] == 'add':
                    version = argv[5].split('@')[-1]; self.install(version, root)
                    write(prof / 'package.json', {'dependencies': {'planweft': version}, 'dsh': {'profile': {'bundles': ['base', 'planweft']}}})
                else:
                    shutil.rmtree(root)
                    write(prof / 'package.json', {'dependencies': {}, 'dsh': {'profile': {'bundles': ['base']}}})
            if argv[-1] == '--dump-config':
                return '- id: planweft\n  name: ' + (root / 'dist/dsh/planweft/index.mjs').as_uri() + '\n' if root.exists() else '- id: base\n'
            return ''
        raise AssertionError(argv)


class RegistryNativeTests(unittest.TestCase):
    def test_three_native_channels_execute_the_real_version_sequence(self):
        for host in ['pi', 'opencode', 'dsh']:
            with self.subTest(host=host), tempfile.TemporaryDirectory() as temporary:
                f = NativeFixture(Path(temporary))
                with patch.object(runner, 'pi_commands', side_effect=f.rpc):
                    result = runner.direct_npm_lifecycle(host, NEW, OLD, f.packages, f.out, f.profile, {}, f.run)
                self.assertEqual([x.get('version') for x in result['steps']], [OLD, NEW, OLD, NEW, None])
                self.assertEqual(result['scope'], 'cross-version')
                self.assertEqual(result['model_sessions'], 'Not Run')
                self.assertNotIn(temporary, json.dumps(result))
                if host == 'opencode':
                    selected = [Path(argv[1]).parent.parent.name for _, argv in f.calls if argv[0] == 'node' and argv[2] != 'remove']
                    self.assertEqual(selected, [OLD, NEW, OLD, NEW])
                    self.assertTrue(any(label.endswith('remove-load') for label, _ in f.calls))
                    self.assertTrue(any(label.endswith('remove-skills') for label, _ in f.calls))
                else:
                    selected = [argv[2] if host == 'pi' else argv[5] for _, argv in f.calls
                                if (argv[:2] == ['pi', 'install'] if host == 'pi' else argv[:2] == ['dsh', 'plugin'] and argv[4] == 'add')]
                    self.assertEqual([x.split('@')[-1] for x in selected], [OLD, NEW, OLD, NEW])

    def test_single_version_is_not_reported_as_an_upgrade(self):
        self.assertEqual(runner.native_version_steps(NEW), [('install', NEW)])
        with tempfile.TemporaryDirectory() as temporary:
            f = NativeFixture(Path(temporary))
            result = runner.direct_npm_lifecycle('opencode', NEW, None, f.packages, f.out, f.profile, {}, f.run)
            self.assertEqual(result['scope'], 'single-version-install-remove')
            self.assertEqual([x['step'] for x in result['steps']], ['install', 'remove'])

    def test_opencode_removal_preserves_other_configuration_and_plugins(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / 'opencode.json'
            before = {'plugin': ['other-plugin@1', 'planweft@' + OLD, 'file:///other.js'],
                      'permission': {'bash': 'deny'}, 'model': 'example/test'}
            write(config, before)
            runner.set_opencode_source(config, OLD, NEW)
            self.assertEqual(json.loads(config.read_text())['plugin'], ['other-plugin@1', 'planweft@' + NEW, 'file:///other.js'])
            runner.set_opencode_source(config, NEW, None)
            before['plugin'].remove('planweft@' + OLD)
            self.assertEqual(json.loads(config.read_text()), before)

    def test_opencode_canonical_schema_normalization_keeps_strict_comparison(self):
        # The fixed host adds $schema on reading/writing config. Previously this
        # alone failed the final equality check despite a successful uninstall.
        for unrelated_change in [False, True]:
            with self.subTest(unrelated_change=unrelated_change), tempfile.TemporaryDirectory() as temporary:
                f = NativeFixture(Path(temporary)); observed = []
                def run(label, argv, cwd):
                    if argv[0] == 'opencode':
                        config = cwd / 'opencode.json'
                        data = json.loads(config.read_text())
                        observed.append(data.get('$schema'))
                        data.setdefault('$schema', 'https://opencode.ai/config.json')
                        if unrelated_change: data['share'] = 'auto'
                        write(config, data)
                    return f.run(label, argv, cwd)
                if unrelated_change:
                    with self.assertRaisesRegex(RuntimeError, 'Unrelated OpenCode configuration changed'):
                        runner.direct_npm_lifecycle('opencode', NEW, None, f.packages, f.out, f.profile, {}, run)
                else:
                    result = runner.direct_npm_lifecycle('opencode', NEW, None, f.packages, f.out, f.profile, {}, run)
                    self.assertEqual(result['status'], 'Passed')
                self.assertTrue(observed)
                self.assertEqual(set(observed), {'https://opencode.ai/config.json'})

    def test_opencode_old_unpair_only_bug_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'survived native removal'):
            runner.verify_opencode_discovery({'tools': {'pw_init': True}}, [])
        with self.assertRaisesRegex(RuntimeError, 'survived native removal'):
            runner.verify_opencode_discovery({'tools': {}}, [{'name': 'project-docs'}])
        runner.verify_opencode_discovery({'tools': {'bash': True}}, [])

    def test_direct_uninstall_rejects_a_dangling_skill_link_without_deleting_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            f = NativeFixture(Path(temporary))
            def run(label, argv, cwd):
                output = f.run(label, argv, cwd)
                if argv[0] == 'node' and argv[2] == 'remove':
                    link = cwd / '.opencode/skills/project-docs'
                    try: link.symlink_to(cwd / 'removed-package', target_is_directory=True)
                    except (OSError, NotImplementedError): self.skipTest('Symlink creation is unavailable')
                return output
            with self.assertRaisesRegex(RuntimeError, 'components survived removal'):
                runner.direct_npm_lifecycle('opencode', NEW, None, f.packages, f.out, f.profile, {}, run)
            project = f.out / 'native-opencode'
            link = project / '.opencode/skills/project-docs'
            self.assertTrue(link.is_symlink()); self.assertFalse(link.exists())
            config = json.loads((project / 'opencode.json').read_text())
            self.assertEqual(config['permission'], {'bash': 'ask'})
            self.assertIs(config['autoupdate'], False)

    def test_managed_uninstall_rejects_dangling_skill_and_loader_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            config = project / 'opencode.json'; write(config, {'permission': {'bash': 'deny'}, 'plugin': ['other']})
            before = config.read_bytes()
            for relative in ['.opencode/skills/project-docs', '.opencode/plugins/planweft.ts']:
                with self.subTest(relative=relative):
                    link = project / relative; link.parent.mkdir(parents=True, exist_ok=True)
                    try: link.symlink_to(project / 'removed-package')
                    except (OSError, NotImplementedError): self.skipTest('Symlink creation is unavailable')
                    with self.assertRaisesRegex(RuntimeError, 'components survived removal'):
                        runner.verify_opencode_removed(project, managed=True)
                    self.assertTrue(link.is_symlink()); self.assertFalse(link.exists())
                    self.assertEqual(config.read_bytes(), before)
                    link.unlink()
            runner.verify_opencode_removed(project, managed=True)

    def test_opencode_exact_layout_selects_versions_without_old_cache_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            f = NativeFixture(Path(temporary)); config = f.out / 'opencode.json'
            old_layout = f.profile / '.cache/opencode/node_modules/planweft'
            f.install(NEW, old_layout)
            roots = {}
            for version in [OLD, NEW]:
                cache = f.profile / '.cache/opencode/packages' / ('planweft@' + version)
                roots[version] = cache / 'node_modules/planweft'
                f.install(version, roots[version])
                write(cache / 'package.json', {'dependencies': {'planweft': version}})
                write(config, {'plugin': ['planweft@' + version]})
                self.assertEqual(runner.opencode_package_root(f.profile, config, version), roots[version])
            # A retained old version and even a matching unversioned package
            # cannot stand in for the missing selected per-version installation.
            shutil.rmtree(roots[NEW]); write(config, {'plugin': ['planweft@' + NEW]})
            with self.assertRaisesRegex(RuntimeError, 'selected version cache is missing'):
                runner.opencode_package_root(f.profile, config, NEW)

    def test_opencode_cache_rejects_duplicate_or_wrong_version_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            f = NativeFixture(Path(temporary)); config = f.out / 'opencode.json'
            cache = f.profile / '.cache/opencode/packages' / ('planweft@' + NEW)
            root = cache / 'node_modules/planweft'
            f.install(NEW, root); write(cache / 'package.json', {'dependencies': {'planweft': NEW}})
            for entries in [[], ['planweft@' + OLD], ['planweft@' + NEW] * 2,
                            ['planweft@' + NEW, 'planweft@' + OLD]]:
                write(config, {'plugin': entries})
                with self.subTest(entries=entries), self.assertRaisesRegex(RuntimeError, 'source is missing, ambiguous'):
                    runner.opencode_package_root(f.profile, config, NEW)
            write(config, {'plugin': ['planweft@' + NEW]})
            write(cache / 'package.json', {'dependencies': {'planweft': OLD}})
            with self.assertRaisesRegex(RuntimeError, 'requested version'):
                runner.opencode_package_root(f.profile, config, NEW)
            write(cache / 'package.json', {'dependencies': {'planweft': NEW}})
            f.install(OLD, root)
            with self.assertRaisesRegex(RuntimeError, 'requested version'):
                runner.opencode_package_root(f.profile, config, NEW)

    def test_conflicting_opencode_registration_does_not_modify_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Path(temporary) / 'opencode.json'
            for entries in [['planweft@' + NEW], ['planweft@' + OLD] * 2, ['planweft']]:
                write(config, {'plugin': entries}); before = config.read_bytes()
                with self.assertRaises(RuntimeError): runner.set_opencode_source(config, OLD, NEW)
                self.assertEqual(config.read_bytes(), before)

    def test_pi_requires_version_matched_unique_skill_and_extension(self):
        root = Path('/synthetic/package')
        runner.verify_pi_commands(commands(root, NEW), NEW, root)
        bad = [commands(root, OLD), commands(root, NEW) * 2, commands(root, NEW)[:1]]
        for items in bad:
            with self.subTest(items=items), self.assertRaises(RuntimeError): runner.verify_pi_commands(items, NEW, root)
        with self.assertRaises(RuntimeError): runner.verify_pi_commands(commands(root, NEW), None, None)

    def test_package_and_skill_mismatches_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            f = NativeFixture(Path(temporary)); actual = Path(temporary) / 'actual'
            f.install(OLD, actual)
            with self.assertRaises(RuntimeError): runner.verify_native_package(actual, f.packages[NEW])
            with self.assertRaises(RuntimeError):
                runner.verify_skill_tree(actual / 'dist/opencode/planweft/skills', f.packages[NEW] / 'dist/opencode/planweft/skills')
            f.install(NEW, actual)
            write(actual / 'dist/opencode/planweft/removed.txt', 'stale')
            with self.assertRaisesRegex(RuntimeError, 'Removed distribution files'):
                runner.verify_native_package(actual, f.packages[NEW])


if __name__ == '__main__': unittest.main()
