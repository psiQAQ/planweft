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
import shutil


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/check-document-release-gate.py'
POLICY = ROOT / 'release/support-policy-0.5.1.json'
LEGACY_POLICY = ROOT / 'release/support-policy-0.5.json'


class DocumentReleaseGateTest(unittest.TestCase):
    @staticmethod
    def write_archive(path, version, name='planweft', manifest=None):
        payload = json.dumps({'name': name, 'version': version} if manifest is None else manifest).encode()
        with tarfile.open(path, mode='w:gz') as packed:
            member = tarfile.TarInfo('package/package.json')
            member.size = len(payload)
            packed.addfile(member, io.BytesIO(payload))

    def make_evidence(self, directory, promotion=False, policy_path=POLICY):
        directory = Path(directory)
        policy = json.loads(policy_path.read_text())
        version = policy['version']
        evidence_root = directory / 'release' / 'evidence' / version
        evidence_root.mkdir(parents=True, exist_ok=True)
        archive = directory / ('planweft-' + version + '.tgz')
        self.write_archive(archive, version)
        required = list(policy['required_prepublication'])
        if promotion:
            required += policy['required_promotion']
        checks = {}
        for name in required:
            attachment = evidence_root / 'raw' / (name + '.txt')
            attachment.parent.mkdir(exist_ok=True)
            attachment.write_text('observed ' + name + '\n')
            checks[name] = {'status': 'Passed', 'evidence': str(attachment.relative_to(evidence_root)),
                            'sha256': hashlib.sha256(attachment.read_bytes()).hexdigest()}
        checks.update({name: {'status': 'Not Run',
                              'reason': 'outside ' + version + ' static/logic validation scope'}
                       for name in policy['not_run']})
        evidence = {'schema_version': 1, 'version': version,
                    'policy_sha256': hashlib.sha256(policy_path.read_bytes()).hexdigest(),
                    'package_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                    'release_blocking': False, 'checks': checks}
        path = evidence_root / 'evidence.json'
        path.write_text(json.dumps(evidence))
        return evidence, path, archive

    def check(self, evidence_path, archive, promotion=False, policy_path=POLICY):
        return subprocess.run([sys.executable, str(SCRIPT), '--policy', str(policy_path),
                               '--evidence', str(evidence_path),
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
            self.write_archive(archive, '0.5.1')
            evidence['checks']['hook_logic']['sha256'] = '0' * 64
            path.write_text(json.dumps(evidence))
            self.assertNotEqual(self.check(path, archive).returncode, 0)
            evidence, path, archive = self.make_evidence(directory)
            evidence['checks']['hook_logic']['evidence'] = '../outside.txt'
            path.write_text(json.dumps(evidence))
            self.assertNotEqual(self.check(path, archive).returncode, 0)
            evidence, path, archive = self.make_evidence(directory)
            self.write_archive(archive, '0.5.1', name='other-package')
            evidence['package_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
            path.write_text(json.dumps(evidence))
            self.assertNotEqual(self.check(path, archive).returncode, 0)
            evidence, path, archive = self.make_evidence(directory)
            self.write_archive(archive, '0.5.1', manifest=[])
            evidence['package_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
            path.write_text(json.dumps(evidence))
            self.assertNotEqual(self.check(path, archive).returncode, 0)

    def test_patch_policy_requires_exact_supported_version_and_identity(self):
        with tempfile.TemporaryDirectory(prefix='pw-document-release-') as directory:
            directory = Path(directory)
            for version, accepted in [('0.5.2', True), ('0.5.01', False), ('0.5.1-rc.1', False),
                                      ('0.4.1', False), ('0.6.0', False)]:
                with self.subTest(version=version):
                    policy = json.loads(POLICY.read_text())
                    policy['version'] = version
                    policy_path = directory / 'release' / ('support-policy-' + version + '.json')
                    policy_path.parent.mkdir(exist_ok=True)
                    policy_path.write_text(json.dumps(policy))
                    _, path, archive = self.make_evidence(directory / version.replace('/', '_'),
                                                            policy_path=policy_path)
                    result = self.check(path, archive, policy_path=policy_path)
                    if accepted:
                        self.assertEqual(result.returncode, 0, result.stderr)
                    else:
                        self.assertNotEqual(result.returncode, 0)
        with tempfile.TemporaryDirectory(prefix='pw-document-release-') as directory:
            evidence, path, archive = self.make_evidence(directory)
            evidence['version'] = '0.5.0'
            path.write_text(json.dumps(evidence))
            self.assertNotEqual(self.check(path, archive).returncode, 0)
            evidence, path, archive = self.make_evidence(directory)
            self.write_archive(archive, '0.5.0')
            evidence['package_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
            path.write_text(json.dumps(evidence))
            self.assertNotEqual(self.check(path, archive).returncode, 0)

    def test_policy_and_evidence_paths_are_version_bound(self):
        with tempfile.TemporaryDirectory(prefix='pw-document-release-') as directory:
            directory = Path(directory)
            evidence, path, archive = self.make_evidence(directory)
            wrong_policy = directory / 'release' / 'support-policy-0.5.2.json'
            wrong_policy.parent.mkdir(exist_ok=True)
            wrong_policy.write_bytes(POLICY.read_bytes())
            self.assertNotEqual(self.check(path, archive, policy_path=wrong_policy).returncode, 0)
            wrong_root = directory / 'release' / 'evidence' / '0.5.2'
            shutil.copytree(path.parent, wrong_root)
            self.assertNotEqual(self.check(wrong_root / path.name, archive).returncode, 0)

    def test_frozen_0_5_0_policy_keeps_its_historic_filename_only(self):
        with tempfile.TemporaryDirectory(prefix='pw-document-release-') as directory:
            directory = Path(directory)
            _, path, archive = self.make_evidence(directory, policy_path=LEGACY_POLICY)
            result = self.check(path, archive, policy_path=LEGACY_POLICY)
            self.assertEqual(result.returncode, 0, result.stderr)
            renamed = directory / 'release' / 'support-policy-0.5.0.json'
            renamed.parent.mkdir(exist_ok=True)
            renamed.write_bytes(LEGACY_POLICY.read_bytes())
            self.assertNotEqual(self.check(path, archive, policy_path=renamed).returncode, 0)

    def test_publish_workflow_resolves_policy_and_evidence_from_checked_version(self):
        workflow = (ROOT / '.github/workflows/publish.yml').read_text()
        self.assertIn("grep -Eq '^0\\.5\\.(0|[1-9][0-9]*)$'", workflow)
        self.assertIn('POLICY="release/support-policy-$VERSION.json"', workflow)
        self.assertIn('EVIDENCE="release/evidence/$VERSION/prepublication.json"', workflow)
        self.assertIn('--policy "$POLICY" --evidence "$EVIDENCE" --archive "$ARCHIVE"', workflow)


if __name__ == '__main__':
    unittest.main()
