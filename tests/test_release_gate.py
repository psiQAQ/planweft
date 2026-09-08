"""Stable publishing cannot be inferred from a version string or a candidate tag."""
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

class ReleaseGateTest(unittest.TestCase):
    def archive(self, root, version):
        p = root / (version + '.tgz')
        with tarfile.open(p, 'w:gz') as tar:
            data = json.dumps({'name': 'planweft', 'version': version}).encode()
            info = tarfile.TarInfo('package/package.json'); info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        return p

    def check(self, archive, evidence, *flags):
        return subprocess.run([sys.executable, str(ROOT / 'scripts/check-release-gate.py'),
            '--archive', str(archive), '--evidence', str(evidence), *flags], capture_output=True)

    def test_candidate_cannot_be_promoted_to_latest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); a=self.archive(root,'0.4.0-rc.1'); evidence=root/'absent.json'
            self.assertEqual(self.check(a,evidence).returncode,0)
            self.assertNotEqual(self.check(a,evidence,'--promotion').returncode,0)

    def complete(self, root, archive):
        import importlib.util
        spec = importlib.util.spec_from_file_location('gate', ROOT / 'scripts/check-release-gate.py')
        gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        record = {'schema_version': 1, 'version': '0.4.0', 'npm_sha256': digest, 'core': {}}
        (root/'trace.json').write_text('{"fixture":true}')
        raw={'evidence':'trace.json','sha256':hashlib.sha256((root/'trace.json').read_bytes()).hexdigest()}
        for host in gate.HOSTS:
            record['core'][host] = {}
            for check in tuple(c for c in gate.LOCAL_CHECKS + gate.REMOTE_CHECKS if c!='independent_review') + ('independent_review',):
                name = host + '-' + check + '.json'
                details={'artifacts':[raw], 'kind':'actual-host-model','image':'fixture-image', 'cli_version':'fixture-cli',
                    'model':'fixture-model','runner_sha256':'fixture-runner','session_id':host+'-'+check, 'external_memory':False,
                    'history_available':False,'plugin_available':False,'input_snapshot_sha256':'fixture-snapshot','output_snapshot_sha256':'fixture-snapshot',
                    'reviewer':'fixture-reviewer','reviewed_sha256':[r['sha256'] for r in record['core'][host].values()]}
                data = json.dumps({'status':'Passed','host':host,'check':check,'version':'0.4.0',
                    'npm_sha256':digest,'observations':details}).encode()
                (root/name).write_bytes(data)
                record['core'][host][check] = {'status':'Passed','evidence':name,'sha256':hashlib.sha256(data).hexdigest()}
        return record

    def test_five_hosts_and_exact_attachments_are_required(self):
        import copy
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); a=self.archive(root,'0.4.0'); evidence=root/'acceptance.json'
            complete=self.complete(root,a)
            evidence.write_text(json.dumps(complete))
            self.assertEqual(self.check(a,evidence,'--promotion').returncode,0)
            mutations = [
                lambda x: x['core'].pop('dsh'),
                lambda x: x['core']['pi'].pop('recovery'),
                lambda x: x['core']['claude']['cold_read'].update(status='Not Run'),
                lambda x: x.update(npm_sha256='wrong'),
                lambda x: x['core']['codex']['exact_artifact'].update(evidence='missing.json'),
                lambda x: x['core']['codex']['exact_artifact'].update(evidence='../outside.json'),
                lambda x: x['core']['codex']['exact_artifact'].update(sha256='wrong'),
                lambda x: x['core']['codex']['exact_artifact'].update(**x['core']['pi']['exact_artifact']),
            ]
            for mutate in mutations:
                changed=copy.deepcopy(complete); mutate(changed)
                evidence.write_text(json.dumps(changed))
                self.assertNotEqual(self.check(a,evidence).returncode,0)
            changed=copy.deepcopy(complete); changed['core']['dsh'].pop('remote_lifecycle')
            evidence.write_text(json.dumps(changed))
            self.assertEqual(self.check(a,evidence).returncode,0)
            self.assertNotEqual(self.check(a,evidence,'--promotion').returncode,0)
            evidence.write_text(json.dumps(complete))
            attachment=root/complete['core']['codex']['exact_artifact']['evidence']
            attachment.write_text(attachment.read_text()+' ')
            self.assertNotEqual(self.check(a,evidence).returncode,0)

    def test_ci_cannot_publish_different_stable_bytes(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); archive=self.archive(root,'0.4.0')
            command=[sys.executable,str(ROOT/'scripts/check-release-artifact.py'),'--archive',str(archive)]
            for expected in ['', '0'*64, 'not-a-digest']:
                result=subprocess.run(command,env={**os.environ,'EXPECTED_NPM_SHA256':expected},capture_output=True)
                self.assertNotEqual(result.returncode,0)
            digest=hashlib.sha256(archive.read_bytes()).hexdigest()
            result=subprocess.run(command,env={**os.environ,'EXPECTED_NPM_SHA256':digest},capture_output=True)
            self.assertEqual(result.returncode,0)
