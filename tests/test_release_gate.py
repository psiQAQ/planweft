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

    def test_stable_requires_exact_artifact_and_all_four_hosts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); a=self.archive(root,'0.4.0'); evidence=root/'acceptance.json'
            self.assertNotEqual(self.check(a,evidence).returncode,0)
            record={'version':'0.4.0','npm_sha256':hashlib.sha256(a.read_bytes()).hexdigest(),'core':{}}
            for host in ['codex','claude','pi','opencode']:
                record['core'][host]={c:{'status':'Passed','evidence':'reviewed-fixture'} for c in ['native_lifecycle','model_maintenance','cold_read']}
            evidence.write_text(json.dumps(record)); self.assertEqual(self.check(a,evidence).returncode,0)
            self.assertNotEqual(self.check(a,evidence,'--promotion').returncode,0)
            for host in record['core']: record['core'][host]['remote_lifecycle']={'status':'Passed','evidence':'reviewed-fixture'}
            evidence.write_text(json.dumps(record)); self.assertEqual(self.check(a,evidence,'--promotion').returncode,0)
            record['npm_sha256']='wrong'; evidence.write_text(json.dumps(record)); self.assertNotEqual(self.check(a,evidence).returncode,0)
