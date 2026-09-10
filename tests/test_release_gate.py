"""Stable publishing is computed from schema 3 policy, never a self-asserted boolean."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('gate', ROOT / 'scripts/check-release-gate.py')
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class ReleaseGateTest(unittest.TestCase):
    def archive(self, root, version):
        path = root / (version + '.tgz')
        with tarfile.open(path, 'w:gz') as archive:
            data = json.dumps({'name': 'planweft', 'version': version}).encode()
            info = tarfile.TarInfo('package/package.json')
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        return path

    def check(self, archive, evidence, policy, *flags):
        return subprocess.run([
            sys.executable, str(ROOT / 'scripts/check-release-gate.py'),
            '--archive', str(archive), '--evidence', str(evidence),
            '--policy', str(policy), '--evidence-root', str(evidence.parent), *flags
        ], capture_output=True)

    def write(self, root, name, payload):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True))
        return {'evidence': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def complete(self, root, archive):
        policy = root / 'support-policy.json'
        policy.write_bytes((ROOT / 'release/support-policy.json').read_bytes())
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        record = {
            'schema_version': 3, 'version': '0.4.0', 'npm_sha256': digest,
            'support_policy_sha256': hashlib.sha256(policy.read_bytes()).hexdigest(),
            'release_blocking': False, 'core': {}, 'workflows': {},
            'independent_reviews': {}
        }
        raw = self.write(root, 'raw/trace.json', {'fixture': True})
        maintenance_raw = self.write(root, 'raw/maintenance.json', {'fixture': 'maintenance'})
        cold_raw = self.write(root, 'raw/cold-read.json', {'fixture': 'cold-read'})
        for host in gate.HOSTS:
            record['core'][host] = {}
            for check in gate.LOCAL_CHECKS + gate.REMOTE_CHECKS:
                rules = json.loads(policy.read_text())['core'][host][check]['scenarios']
                scenarios = {name: {'status': 'Passed', 'evidence_type': 'fresh',
                                    'artifacts': [raw]} for name in rules}
                details = {
                    'scenarios': scenarios, 'kind': 'actual-host-model',
                    'image': 'fixture-image', 'cli_version': 'fixture-cli',
                    'model': 'fixture-model', 'runner_sha256': 'fixture-runner',
                    'session_id': host + '-' + check, 'external_memory': False
                }
                payload = {'status': 'Passed', 'host': host, 'check': check,
                           'version': '0.4.0', 'npm_sha256': digest,
                           'observations': details}
                attestation = self.write(root, 'attestations/' + host + '-' + check + '.json', payload)
                record['core'][host][check] = {
                    'status': 'Passed', 'evidence_type': 'fresh', **attestation
                }
        for name, (host, mode, tier) in gate.WORKFLOWS.items():
            rules = json.loads(policy.read_text())['workflows'][name]['scenarios']
            scenarios = {
                scenario: {'status': 'Passed', 'evidence_type': 'fresh',
                           'artifacts': [maintenance_raw if scenario == 'maintenance'
                                         else cold_raw if scenario == 'independent_cold_read'
                                         else raw]}
                for scenario in rules
            }
            details = {
                'scenarios': scenarios, 'kind': 'actual-host-model',
                'image': 'fixture-image', 'cli_version': 'fixture-cli',
                'model': 'fixture-model', 'runner_sha256': 'fixture-runner',
                'session_id': name, 'external_memory': False,
                'adoption_mode': mode, 'classification': 'supported',
                'maintenance_session_id': name + '-writer',
                'cold_read_session_id': name + '-reader',
                'output_snapshot_sha256': 'fixture-snapshot',
                'input_snapshot_sha256': 'fixture-snapshot',
                'maintenance_evidence_sha256': maintenance_raw['sha256'],
                'cold_read_evidence_sha256': cold_raw['sha256'],
                'history_available': False, 'plugin_available': False,
                'skill_loading_evidence_sha256': record['core'][host]['skill_loading']['sha256'],
                'explicit_skill_read': mode == 'explicit'
            }
            payload = {'status': 'Passed', 'workflow': name, 'host': host,
                       'version': '0.4.0', 'npm_sha256': digest,
                       'observations': details}
            attestation = self.write(root, 'attestations/' + name + '.json', payload)
            record['workflows'][name] = {
                'status': 'Passed', 'evidence_type': 'fresh', **attestation
            }
        self.refresh_reviews(root, record, raw)
        evidence = root / 'acceptance.json'
        evidence.write_text(json.dumps(record, indent=2))
        return evidence, policy, record, raw

    def refresh_record(self, root, record, label, payload):
        path = root / record['evidence']
        path.write_text(json.dumps(payload, sort_keys=True))
        record['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()

    def refresh_reviews(self, root, record, raw):
        for phase in ('prepublication', 'promotion'):
            reviewed = {row[2] for row in gate.result_rows(record, phase)}
            result_digest = gate.result_set_digest(record, phase)
            details = {
                'scenarios': {'review': {'status': 'Passed', 'evidence_type': 'fresh',
                                         'artifacts': [raw]}},
                'reviewer': 'fixture-independent-reviewer',
                'reviewed_sha256': sorted(reviewed),
                'support_policy_sha256': record['support_policy_sha256'],
                'npm_sha256': record['npm_sha256'],
                'result_set_sha256': result_digest
            }
            if phase == 'promotion':
                details['prior_review_sha256'] = record['independent_reviews']['prepublication']['sha256']
            payload = {'status': 'Passed', 'check': 'independent_review',
                       'phase': phase, 'version': '0.4.0',
                       'npm_sha256': record['npm_sha256'], 'observations': details}
            attestation = self.write(root, 'attestations/review-' + phase + '.json', payload)
            record['independent_reviews'][phase] = {
                'status': 'Passed', 'evidence_type': 'fresh', **attestation
            }

    def test_candidate_cannot_be_promoted_to_latest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, '0.4.0-rc.1')
            policy = root / 'support-policy.json'
            policy.write_bytes((ROOT / 'release/support-policy.json').read_bytes())
            absent = root / 'absent.json'
            self.assertEqual(self.check(archive, absent, policy).returncode, 0)
            self.assertNotEqual(self.check(archive, absent, policy, '--promotion').returncode, 0)

    def test_complete_policy_bound_acceptance_passes_both_phases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, '0.4.0')
            evidence, policy, _, _ = self.complete(root, archive)
            self.assertEqual(self.check(archive, evidence, policy).returncode, 0)
            self.assertEqual(self.check(archive, evidence, policy, '--promotion').returncode, 0)

    def test_missing_policy_items_and_unsafe_attachments_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, '0.4.0')
            evidence, policy, complete, _ = self.complete(root, archive)
            changed_policy = json.loads(policy.read_text())
            changed_policy['core']['dsh'].pop('recovery')
            policy.write_text(json.dumps(changed_policy))
            self.assertNotEqual(self.check(archive, evidence, policy).returncode, 0)
            policy.write_bytes((ROOT / 'release/support-policy.json').read_bytes())
            for value in ('../outside.json', 'acceptance.json', 'support-policy.json'):
                changed = copy.deepcopy(complete)
                changed['core']['codex']['exact_artifact']['evidence'] = value
                evidence.write_text(json.dumps(changed))
                self.assertNotEqual(self.check(archive, evidence, policy).returncode, 0)

    def test_policy_cannot_downgrade_a_required_scenario(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, '0.4.0')
            evidence, policy, _, _ = self.complete(root, archive)
            changed = json.loads(policy.read_text())
            changed['core']['codex']['skill_loading']['scenarios']['actual_skill_read']['tier'] = 'experimental'
            policy.write_text(json.dumps(changed))
            result = self.check(archive, evidence, policy)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'weakens frozen contract', result.stderr)

    def test_aggregate_status_is_real_but_experimental_failure_does_not_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, '0.4.0')
            evidence, policy, record, raw = self.complete(root, archive)
            entry = record['core']['claude']['model_maintenance']
            payload = json.loads((root / entry['evidence']).read_text())
            scenario = payload['observations']['scenarios']['automatic_adoption']
            scenario.update(status='Failed', public_limit_id='LIMIT-CLAUDE-AUTO')
            payload['status'] = entry['status'] = 'Failed'
            self.refresh_record(root, entry, 'claude/model_maintenance', payload)
            self.refresh_reviews(root, record, raw)
            evidence.write_text(json.dumps(record))
            result = self.check(archive, evidence, policy)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload['status'] = entry['status'] = 'Passed'
            self.refresh_record(root, entry, 'claude/model_maintenance', payload)
            self.refresh_reviews(root, record, raw)
            evidence.write_text(json.dumps(record))
            result = self.check(archive, evidence, policy)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'Aggregate status differs', result.stderr)

    def test_required_failure_must_set_blocking_and_still_rejects_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, '0.4.0')
            evidence, policy, record, raw = self.complete(root, archive)
            entry = record['core']['codex']['skill_loading']
            payload = json.loads((root / entry['evidence']).read_text())
            payload['observations']['scenarios']['actual_skill_read']['status'] = 'Failed'
            payload['status'] = entry['status'] = 'Failed'
            self.refresh_record(root, entry, 'codex/skill_loading', payload)
            workflow = record['workflows']['codex_explicit_maintenance_cold_read']
            workflow_payload = json.loads((root / workflow['evidence']).read_text())
            workflow_payload['observations']['skill_loading_evidence_sha256'] = entry['sha256']
            self.refresh_record(root, workflow, 'workflows/codex_explicit_maintenance_cold_read',
                                workflow_payload)
            self.refresh_reviews(root, record, raw)
            evidence.write_text(json.dumps(record))
            mismatch = self.check(archive, evidence, policy)
            self.assertIn(b'release_blocking differs', mismatch.stderr)
            record['release_blocking'] = True
            evidence.write_text(json.dumps(record))
            blocked = self.check(archive, evidence, policy)
            self.assertIn(b'Release is blocked by: codex/skill_loading/actual_skill_read', blocked.stderr)

    def test_reuse_requires_full_binding_and_respects_nonreusable_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, '0.4.0')
            evidence, policy, record, raw = self.complete(root, archive)
            manifest_payload = {
                'schema_version': 1, 'source_version': '0.4.0-rc.15',
                'source_npm_sha256': '1' * 64, 'target_version': '0.4.0',
                'target_npm_sha256': record['npm_sha256'],
                'changed_files': [{'path': 'package.json', 'before_sha256': '2' * 64,
                                   'after_sha256': '3' * 64}],
                'affected_checks': [], 'reviewer': 'fixture-reviewer'
            }
            manifest = self.write(root, 'raw/manifest-diff.json', manifest_payload)
            entry = record['core']['codex']['recovery']
            payload = json.loads((root / entry['evidence']).read_text())
            scenario = payload['observations']['scenarios']['fresh_session_project_files']
            scenario['evidence_type'] = 'reused'
            scenario['reuse'] = {
                'source_version': '0.4.0-rc.15', 'source_npm_sha256': '1' * 64,
                'target_version': '0.4.0', 'target_npm_sha256': record['npm_sha256'],
                'manifest_diff': manifest, 'affected_checks': [],
                'reviewer': 'fixture-reviewer'
            }
            self.refresh_record(root, entry, 'codex/recovery', payload)
            self.refresh_reviews(root, record, raw)
            evidence.write_text(json.dumps(record))
            self.assertEqual(self.check(archive, evidence, policy).returncode, 0)
            forbidden = copy.deepcopy(record)
            item = forbidden['core']['codex']['exact_artifact']
            item_payload = json.loads((root / item['evidence']).read_text())
            archive_bytes = item_payload['observations']['scenarios']['archive_bytes']
            archive_bytes['evidence_type'] = 'reused'
            archive_bytes['reuse'] = dict(scenario['reuse'])
            self.refresh_record(root, item, 'codex/exact_artifact', item_payload)
            self.refresh_reviews(root, forbidden, raw)
            evidence.write_text(json.dumps(forbidden))
            self.assertIn(b'Non-reusable scenario', self.check(archive, evidence, policy).stderr)

    def test_evidence_based_not_run_is_preserved_without_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, '0.4.0')
            evidence, policy, record, raw = self.complete(root, archive)
            entry = record['workflows']['pi_explicit_maintenance_cold_read']
            payload = json.loads((root / entry['evidence']).read_text())
            for scenario in payload['observations']['scenarios'].values():
                scenario.clear()
                scenario.update(status='Not Run', evidence_type='fresh',
                                reason='Fixture records an unavailable model run')
            payload['observations']['classification'] = 'experimental'
            for key in ('maintenance_session_id', 'cold_read_session_id',
                        'output_snapshot_sha256', 'input_snapshot_sha256',
                        'explicit_skill_read', 'skill_loading_evidence_sha256'):
                payload['observations'].pop(key)
            payload['status'] = entry['status'] = 'Not Run'
            self.refresh_record(root, entry, 'workflows/pi_explicit_maintenance_cold_read', payload)
            self.refresh_reviews(root, record, raw)
            evidence.write_text(json.dumps(record))
            result = self.check(archive, evidence, policy)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_ci_cannot_publish_different_stable_bytes(self):
        import os
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = self.archive(root, '0.4.0')
            command = [sys.executable, str(ROOT / 'scripts/check-release-artifact.py'),
                       '--archive', str(archive)]
            for expected in ('', '0' * 64, 'not-a-digest'):
                result = subprocess.run(command, env={**os.environ, 'EXPECTED_NPM_SHA256': expected},
                                        capture_output=True)
                self.assertNotEqual(result.returncode, 0)
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            result = subprocess.run(command, env={**os.environ, 'EXPECTED_NPM_SHA256': digest},
                                    capture_output=True)
            self.assertEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
