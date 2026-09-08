#!/usr/bin/env python3
"""Native directory lifecycle boundaries; no real host, registry or model calls."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_pwf_distribution import ROOT, assert_snapshots_equal, copy_build_inputs, snapshot


CATALOGS = {
    'codex': ('.agents/plugins/marketplace.json', '.codex-plugin/plugin.json'),
    'claude': ('.claude-plugin/marketplace.json', '.claude-plugin/plugin.json'),
    'cursor': ('.cursor-plugin/marketplace.json', '.cursor-plugin/plugin.json'),
    'copilot': ('.github/plugin/marketplace.json', 'plugin.json'),
    'factory': ('.factory-plugin/marketplace.json', '.factory-plugin/plugin.json'),
    'codebuddy': ('.codebuddy-plugin/marketplace.json', '.codebuddy-plugin/plugin.json'),
}


class NativeCatalogTest(unittest.TestCase):
    def test_catalogs_resolve_the_matching_native_plugin_directory(self):
        self.assertFalse((ROOT / 'marketplace.json').exists(),
                         'a shared fallback catalog would conflate incompatible host formats')
        for host, (relative, plugin_manifest) in CATALOGS.items():
            with self.subTest(host=host):
                catalog = json.loads((ROOT / relative).read_text())
                entries = [entry for entry in catalog['plugins'] if entry['name'] == 'program-design']
                self.assertEqual(len(entries), 1, 'registration must not duplicate the plugin')
                source = entries[0]['source']
                if host == 'codex':
                    self.assertEqual(source['source'], 'local')
                    source = source['path']
                self.assertIsInstance(source, str)
                resolved = (ROOT / source).resolve()
                self.assertEqual(resolved, ROOT / 'dist' / host / 'program-design')
                plugin = json.loads((resolved / plugin_manifest).read_text())
                self.assertEqual(plugin['name'], entries[0]['name'])
                self.assertEqual(plugin['version'], '0.3.0')

    def test_build_preserves_other_catalog_entries_and_verify_is_read_only(self):
        with tempfile.TemporaryDirectory(prefix='pd-catalog-contract-') as temporary:
            root = Path(temporary)
            copy_build_inputs(root)
            retained = {}
            for host, (relative, _) in CATALOGS.items():
                source = './retained-plugin'
                if host == 'codex':
                    source = {'source': 'local', 'path': source}
                entry = {'name': 'retained-plugin', 'source': source,
                         'description': 'Existing unrelated catalog entry'}
                retained[host] = entry
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps({'name': 'program-design-local',
                    'owner': {'name': 'Fixture'}, 'plugins': [entry]}) + '\n')
            command = [sys.executable, str(root / 'scripts/build-plugin.py')]
            env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
            built = subprocess.run(command, env=env, capture_output=True, text=True, timeout=90)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            for host, (relative, _) in CATALOGS.items():
                with self.subTest(host=host):
                    catalog = json.loads((root / relative).read_text())
                    self.assertIn(retained[host], catalog['plugins'])
                    self.assertEqual(sum(entry['name'] == 'program-design'
                                         for entry in catalog['plugins']), 1)
            before = snapshot(root)
            checked = subprocess.run([*command, '--verify'], env=env,
                                     capture_output=True, text=True, timeout=90)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            assert_snapshots_equal(self, snapshot(root), before)


class SmokeDirectoryBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('pd_native_smoke', ROOT / 'tests/run-pwf-smoke.py')
        cls.runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.runner)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='pd-smoke-directory-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'source'
        self.package = self.root / 'dist/codex/program-design'
        self.package.mkdir(parents=True)
        (self.package / 'LICENSE').write_text('Fixture license\n')
        script = self.package / 'hook.sh'
        script.write_text('#!/bin/sh\nexit 0\n')
        script.chmod(0o755)
        files = {path.name: {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'executable': bool(path.stat().st_mode & 0o111)}
                 for path in self.package.iterdir()}
        digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        self.item = {'path': 'codex/program-design', 'sha256': digest,
                     'file_count': len(files), 'files': files}
        self.manifest = {'schema_version': 2, 'product': 'program-design', 'version': '0.3.0',
                         'platforms': {'codex': self.item}}
        self.write_manifest()
        self.catalog = self.root / '.agents/plugins/marketplace.json'
        self.catalog.parent.mkdir(parents=True)
        self.catalog.write_text(json.dumps({'name': self.runner.MARKETPLACE, 'plugins': [{
            'name': 'program-design', 'source': {'source': 'local', 'path': './dist/codex/program-design'}}]}))
        self.destination = Path(temporary.name) / 'isolated marketplace 中文'
        root_patch = patch.object(self.runner, 'ROOT', self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)

    def write_manifest(self):
        (self.root / 'dist/manifest.json').write_text(json.dumps(self.manifest))

    def test_staging_keeps_reviewed_bytes_modes_and_root_catalog(self):
        before = snapshot(self.root)
        staged, evidence = self.runner.prepare_reviewed_package(self.destination)
        self.assertEqual(staged, self.destination)
        self.assertEqual(evidence['sha256'], self.item['sha256'])
        self.assertEqual(snapshot(self.destination / 'dist/codex/program-design'), snapshot(self.package))
        self.assertEqual((staged / '.agents/plugins/marketplace.json').read_bytes(), self.catalog.read_bytes())
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse((staged / 'plugins').exists(), 'the mirror must not become the tested artifact')

    def test_staging_rejects_drift_before_creating_any_installation_files(self):
        script = self.package / 'hook.sh'
        original, mode = script.read_bytes(), script.stat().st_mode
        for change in ['content', 'missing', 'extra', 'executable', 'symlink']:
            with self.subTest(change=change):
                extra = self.package / 'unexpected'
                if change == 'content':
                    script.write_text('unexpected content')
                elif change == 'missing':
                    script.unlink()
                elif change == 'extra':
                    extra.write_text('extra')
                elif change == 'executable':
                    script.chmod(0o644)
                else:
                    extra.symlink_to(script)
                with self.assertRaises(RuntimeError):
                    self.runner.prepare_reviewed_package(self.destination)
                self.assertFalse(self.destination.exists())
                if extra.exists() or extra.is_symlink():
                    extra.unlink()
                script.write_bytes(original)
                script.chmod(mode)

    def test_staging_rejects_a_catalog_or_manifest_pointing_elsewhere(self):
        self.item['path'] = '../plugins/program-design'
        self.write_manifest()
        with self.assertRaisesRegex(RuntimeError, 'distribution path'):
            self.runner.prepare_reviewed_package(self.destination)
        self.item['path'] = 'codex/program-design'
        self.write_manifest()
        catalog = json.loads(self.catalog.read_text())
        catalog['plugins'][0]['source']['path'] = './plugins/program-design'
        self.catalog.write_text(json.dumps(catalog))
        with self.assertRaisesRegex(RuntimeError, 'marketplace'):
            self.runner.prepare_reviewed_package(self.destination)
        self.assertFalse(self.destination.exists())


if __name__ == '__main__':
    unittest.main()
