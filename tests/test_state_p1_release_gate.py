"""Offline contract tests for the deterministic 0.7.0 P1 release gate."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/check-state-p1-release-gate.py'
POLICY = ROOT / 'release/support-policy-0.7.0.json'


class StateP1ReleaseGateTest(unittest.TestCase):
    def archive(self, root):
        archive = root / 'planweft-0.7.0.tgz'
        with tarfile.open(archive, 'w:gz') as packed:
            files = {
                'package/package.json': json.dumps({'name': 'planweft', 'version': '0.7.0'}).encode(),
                'package/dist/manifest.json': b'{}',
                'package/bin/planweft.mjs': b'#!/usr/bin/env node\n',
                'package/lib/state/core.mjs': b'export {};\n',
                'package/lib/state/cli.mjs': b'export {};\n',
            }
            for name, data in files.items():
                info = tarfile.TarInfo(name)
                info.size = len(data)
                packed.addfile(info, io.BytesIO(data))
        return archive

    def make_evidence(self, root, promotion=False):
        root = Path(root)
        evidence_root = root / 'release' / 'evidence' / '0.7.0'
        raw = evidence_root / 'raw'
        raw.mkdir(parents=True, exist_ok=True)
        policy = json.loads(POLICY.read_text())
        names = list(policy['required_prepublication'])
        if promotion:
            names += policy['required_promotion']
        checks = {}
        for name in names:
            path = raw / (name + '.txt')
            path.write_text('passed ' + name + '\n')
            checks[name] = {'status': 'Passed', 'evidence': 'raw/' + path.name,
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        checks.update({name: {'status': 'Not Run',
                              'reason': 'outside 0.7.0 deterministic P1 release scope'}
                       for name in policy['not_run']})
        archive = self.archive(root)
        evidence = evidence_root / ('promotion.json' if promotion else 'prepublication.json')
        evidence.write_text(json.dumps({
            'schema_version': 1, 'version': '0.7.0',
            'policy_sha256': hashlib.sha256(POLICY.read_bytes()).hexdigest(),
            'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
            'release_blocking': False, 'checks': checks,
        }))
        return evidence, archive

    def check(self, evidence, archive, promotion=False):
        return subprocess.run([
            sys.executable, str(SCRIPT), '--policy', str(POLICY),
            '--evidence', str(evidence), '--archive', str(archive),
            *(['--promotion'] if promotion else []),
        ], capture_output=True, text=True)

    def test_prepublication_and_promotion_are_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence, archive = self.make_evidence(directory)
            self.assertEqual(self.check(evidence, archive).returncode, 0)
            self.assertNotEqual(self.check(evidence, archive, True).returncode, 0)
            evidence, archive = self.make_evidence(directory, True)
            self.assertEqual(self.check(evidence, archive, True).returncode, 0)

    def test_status_digest_path_and_archive_identity_are_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence, archive = self.make_evidence(directory)
            payload = json.loads(evidence.read_text())
            payload['checks']['offline_ablation']['sha256'] = '0' * 64
            evidence.write_text(json.dumps(payload))
            self.assertNotEqual(self.check(evidence, archive).returncode, 0)
            evidence, archive = self.make_evidence(directory)
            payload = json.loads(evidence.read_text())
            payload['checks']['offline_ablation']['evidence'] = '../outside.txt'
            evidence.write_text(json.dumps(payload))
            self.assertNotEqual(self.check(evidence, archive).returncode, 0)
            evidence, archive = self.make_evidence(directory)
            archive.write_bytes(b'tampered')
            self.assertNotEqual(self.check(evidence, archive).returncode, 0)

    def test_not_run_is_explicit_and_nonblocking_only(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence, archive = self.make_evidence(directory)
            payload = json.loads(evidence.read_text())
            payload['checks']['real_agent_model']['status'] = 'Passed'
            payload['checks']['real_agent_model']['evidence'] = 'raw/real-agent-model.txt'
            payload['checks']['real_agent_model']['sha256'] = '0' * 64
            evidence.write_text(json.dumps(payload))
            self.assertNotEqual(self.check(evidence, archive).returncode, 0)


if __name__ == '__main__':
    unittest.main()
