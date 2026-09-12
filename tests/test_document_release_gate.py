"""The 0.5 static/logic gate binds Passed claims to files and an npm archive."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tarfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/check-document-release-gate.py'
POLICY = ROOT / 'release/support-policy-0.5.json'


class DocumentReleaseGateTest(unittest.TestCase):
    @staticmethod
    def write_archive(path, name='planweft', manifest=None):
        payload = json.dumps({'name': name, 'version': '0.5.0'} if manifest is None else manifest).encode()
        with tarfile.open(path, mode='w:gz') as packed:
            member = tarfile.TarInfo('package/package.json')
            member.size = len(payload)
            packed.addfile(member, io.BytesIO(payload))

    def make_evidence(self, directory, promotion=False):
        directory = Path(directory)
        policy = json.loads(POLICY.read_text())
        archive = directory / 'planweft-0.5.0.tgz'
        self.write_archive(archive)
        required = list(policy['required_prepublication'])
        if promotion:
            required += policy['required_promotion']
        checks = {}
        for name in required:
            attachment = directory / 'raw' / (name + '.txt')
            attachment.parent.mkdir(exist_ok=True)
            attachment.write_text('observed ' + name + '\n')
            checks[name] = {'status': 'Passed', 'evidence': str(attachment.relative_to(directory)),
                            'sha256': hashlib.sha256(attachment.read_bytes()).hexdigest()}
        checks.update({name: {'status': 'Not Run',
                              'reason': 'outside 0.5.0 static/logic validation scope'}
                       for name in policy['not_run']})
        evidence = {'schema_version': 1, 'version': '0.5.0',
                    'policy_sha256': hashlib.sha256(POLICY.read_bytes()).hexdigest(),
                    'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                    'release_blocking': False, 'checks': checks}
        path = directory / 'evidence.json'
        path.write_text(json.dumps(evidence))
        return evidence, path, archive

    def check(self, evidence_path, archive, promotion=False):
        return subprocess.run([sys.executable, str(SCRIPT), '--evidence', str(evidence_path),
                               '--archive', str(archive),
                               *(['--promotion'] if promotion else [])],
                              capture_output=True, text=True)

    def test_prepublication_and_promotion_require_their_own_hash_bound_records(self):
        with tempfile.TemporaryDirectory(prefix='pw-document-release-') as directory:
            _, path, archive = self.make_evidence(directory)
            self.assertEqual(self.check(path, archive).returncode, 0)
            self.assertNotEqual(self.check(path, archive, promotion=True).returncode, 0)
        with tempfile.TemporaryDirectory(prefix='pw-document-release-') as directory:
            _, path, archive = self.make_evidence(directory, promotion=True)
            self.assertEqual(self.check(path, archive, promotion=True).returncode, 0)

    def test_required_status_and_check_set_cannot_be_forged(self):
        with tempfile.TemporaryDirectory(prefix='pw-document-release-') as directory:
            evidence, path, archive = self.make_evidence(directory)
            evidence['checks']['hook_logic']['status'] = 'Not Run'
            evidence['release_blocking'] = True
            path.write_text(json.dumps(evidence))
            self.assertNotEqual(self.check(path, archive).returncode, 0)
            evidence, path, archive = self.make_evidence(directory)
            evidence['checks']['unexpected_check'] = {'status': 'Passed'}
            path.write_text(json.dumps(evidence))
            self.assertNotEqual(self.check(path, archive).returncode, 0)
            for non_boolean in (0, 1):
                evidence, path, archive = self.make_evidence(directory)
                evidence['release_blocking'] = non_boolean
                path.write_text(json.dumps(evidence))
                self.assertNotEqual(self.check(path, archive).returncode, 0)

    def test_archive_and_attachment_digests_are_verified_inside_evidence_root(self):
        with tempfile.TemporaryDirectory(prefix='pw-document-release-') as directory:
            evidence, path, archive = self.make_evidence(directory)
            archive.write_bytes(b'tampered archive')
            self.assertNotEqual(self.check(path, archive).returncode, 0)
            self.write_archive(archive)
            evidence['checks']['hook_logic']['sha256'] = '0' * 64
            path.write_text(json.dumps(evidence))
            self.assertNotEqual(self.check(path, archive).returncode, 0)
            evidence, path, archive = self.make_evidence(directory)
            evidence['checks']['hook_logic']['evidence'] = '../outside.txt'
            path.write_text(json.dumps(evidence))
            self.assertNotEqual(self.check(path, archive).returncode, 0)
            evidence, path, archive = self.make_evidence(directory)
            self.write_archive(archive, name='other-package')
            evidence['package_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
            path.write_text(json.dumps(evidence))
            self.assertNotEqual(self.check(path, archive).returncode, 0)
            evidence, path, archive = self.make_evidence(directory)
            self.write_archive(archive, manifest=[])
            evidence['package_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
            path.write_text(json.dumps(evidence))
            self.assertNotEqual(self.check(path, archive).returncode, 0)


if __name__ == '__main__':
    unittest.main()
