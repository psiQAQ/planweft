#!/usr/bin/env python3
"""Exercise Copilot/CodeBuddy local marketplace lifecycles in disposable profiles.

No model calls, authentication inheritance, global installations or remote writes.
Synthetic A/B fixtures demonstrate local native update behavior, not a published
Git repository or public marketplace update channel.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pd_native_lifecycle', HERE / 'run-native-lifecycle.py')
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
common.CATALOGS.update(copilot='.github/plugin/marketplace.json',
                       codebuddy='.codebuddy-plugin/marketplace.json')
common.MANIFESTS.update(copilot='plugin.json', codebuddy='.codebuddy-plugin/plugin.json')


class MarketplaceLifecycle(common.Lifecycle):
    def __init__(self, args, scratch):
        super().__init__(args, scratch)
        self.env.update(COPILOT_HOME=str(self.profile / '.copilot'),
                        CODEBUDDY_CONFIG_DIR=str(self.profile / '.codebuddy'),
                        CODEBUDDY_REMOTE_CONFIG_DISABLED='1',
                        CODEBUDDY_SKIP_BUILTIN_MARKETPLACE='1',
                        CODEBUDDY_DISABLE_ENTERPRISE_POLICY='1',
                        CODEBUDDY_DISABLE_IDE='1', CODEBUDDY_DISABLE_SHELL_SNAPSHOT='1',
                        CODEBUDDY_DISABLE_TRACE_COLLECTOR='1')
        self.summary['remote_channel'] = 'Not Run: local directory marketplace only'

    def scope(self):
        return ['--scope', 'user'] if self.args.host == 'codebuddy' else []

    def install(self, label, version):
        self.command(label, ['plugin', 'install', self.plugin_id, *self.scope()])
        self.installed = True

    def update(self):
        self.command('refresh-marketplace', ['plugin', 'marketplace', 'update', self.marketplace])
        self.command('update-to-B', ['plugin', 'update', self.plugin_id, *self.scope()])
        self.summary['update_route'] = 'native marketplace update and plugin update from a local directory'
        if self.args.host == 'copilot':
            self.summary['update_route'] += '; Copilot 1.0.83 loads local marketplace plugins live without copying'

    def list_installed(self, label):
        flags = ['--json'] if self.args.host == 'codebuddy' else []
        return self.command(label, ['plugin', 'list', *flags])

    def installed_path(self, version):
        if self.args.host == 'copilot':
            # Copilot 1.0.83 explicitly reports this as a live local plugin.
            # The native listing verifies registration; comparisons below check
            # the real directory that listing names, including removed assets.
            listing = self.list_installed('locate-' + version)
            if self.plugin_id not in listing['stdout'] or str(self.live) not in listing['stdout']:
                raise RuntimeError('Copilot did not list the registered live local source')
            self.summary['installation_storage'] = 'live local marketplace source; no copied plugin cache'
            return self.source
        cache = self.profile / '.codebuddy/plugins/cache'
        candidates = [p.parent.parent for p in cache.rglob(common.MANIFESTS[self.args.host])
                      if json.loads(p.read_text()).get('version') == version]
        if len(candidates) != 1:
            raise RuntimeError('expected one CodeBuddy installation for ' + version + ': ' + str(candidates))
        return candidates[0]

    def uninstall(self, label, version, required=True):
        self.command(label, ['plugin', 'uninstall', getattr(self, 'plugin_id', common.PRODUCT),
                             *self.scope()], required=required)
        self.installed = False

    def run(self):
        self.command('cli-version', ['--version'])
        for label, args in [('plugin-help', ['plugin', '--help']),
                            ('install-help', ['plugin', 'install', '--help']),
                            ('update-help', ['plugin', 'update', '--help']),
                            ('marketplace-help', ['plugin', 'marketplace', '--help'])]:
            self.command(label, args)
        manifest = json.loads((common.ROOT / 'dist/manifest.json').read_text())
        item = manifest['platforms'][self.args.host]
        original = common.ROOT / 'dist' / self.args.host / common.PRODUCT
        actual = common.inventory(original)
        digest = hashlib.sha256(json.dumps(actual, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if (manifest.get('schema_version') != 2 or manifest.get('version') != '0.3.0'
                or item['path'] != self.args.host + '/' + common.PRODUCT or actual != item['files']
                or len(actual) != item['file_count'] or digest != item['sha256']):
            raise RuntimeError('source distribution differs from the reviewed manifest')
        self.summary['source_sha256'] = digest
        fixtures, expected = {}, {}
        for version in ['0.3.0', '0.3.1']:
            fixtures[version] = self.scratch / ('fixture-' + version)
            expected[version] = common.fixture_version(original, fixtures[version], self.args.host, version)
            common.save(self.args.output / ('fixture-' + version + '.json'), expected[version])
        self.publish_local_fixture(fixtures['0.3.0'])
        self.command('register-marketplace', ['plugin', 'marketplace', 'add', str(self.live)])
        self.install('install-A', '0.3.0')
        self.verify('A', '0.3.0', expected['0.3.0'])
        self.publish_local_fixture(fixtures['0.3.1'])
        self.update()
        self.verify('B', '0.3.1', expected['0.3.1'], set(expected['0.3.0']) - set(expected['0.3.1']))
        self.uninstall('remove-before-rollback', '0.3.1')
        self.publish_local_fixture(fixtures['0.3.0'])
        self.command('refresh-for-rollback', ['plugin', 'marketplace', 'update', self.marketplace])
        self.install('rollback-to-A', '0.3.0')
        self.verify('rollback-A', '0.3.0', expected['0.3.0'], set(expected['0.3.1']) - set(expected['0.3.0']))
        self.uninstall('uninstall', '0.3.0')
        listing = self.list_installed('list-after-uninstall')
        if self.args.host == 'copilot':
            entries = [line for line in listing['stdout'].splitlines() if self.plugin_id in line]
            if not entries or any('(disabled)' not in line for line in entries):
                raise RuntimeError('Copilot local live plugin was not disabled by native uninstall')
            self.summary['uninstall_semantics'] = ('local live plugin uninstall disables discovery; '
                                                   'marketplace removal unregisters the local source')
            self.command('remove-live-marketplace', ['plugin', 'marketplace', 'remove', self.marketplace])
            del self.marketplace
            listing = self.list_installed('list-after-marketplace-removal')
        if self.plugin_id in listing['stdout']:
            raise RuntimeError('uninstalled plugin is still listed as registered')
        self.summary['checks']['uninstall'] = {'status': 'Passed',
            'remaining_profile_cache': sorted(p for p in common.inventory(self.profile)
                                               if common.PRODUCT in p and 'cache' in p)}
        self.summary['status'] = 'Passed'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=['copilot', 'codebuddy'], required=True)
    parser.add_argument('--cli', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=common.positive_timeout, default=45)
    args = parser.parse_args()
    args.cli = args.cli.expanduser().resolve()
    args.output = args.output.expanduser().resolve()
    if not args.cli.is_file() or not os.access(args.cli, os.X_OK):
        parser.error('--cli must be an already installed executable')
    if args.output == common.ROOT or common.ROOT in args.output.parents or args.output.exists():
        parser.error('--output must be a new evidence directory outside the repository')
    args.output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix='pd-marketplace-lifecycle-') as temporary:
        scratch = Path(temporary)
        lifecycle = MarketplaceLifecycle(args, scratch)
        try:
            lifecycle.run()
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            lifecycle.summary['error'] = str(error)
        finally:
            lifecycle.cleanup()
    lifecycle.summary['temporary_profile_removed'] = not scratch.exists()
    lifecycle.summary['cli'] = str(args.cli)
    lifecycle.summary['runner_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    common.save(args.output / 'summary.json', lifecycle.summary)
    print(json.dumps(lifecycle.summary, ensure_ascii=False), flush=True)
    return 0 if lifecycle.summary['status'] == 'Passed' else 1


if __name__ == '__main__':
    sys.exit(main())
