#!/usr/bin/env python3
"""Candidates may ship to next; stable packages need matching acceptance evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
HOSTS = ('codex', 'claude', 'pi', 'opencode', 'dsh')
LOCAL_CHECKS = ('exact_artifact', 'native_lifecycle', 'skill_loading', 'context_injection',
                'recovery', 'stopping', 'permissions', 'model_maintenance', 'cold_read',
                'independent_review')
REMOTE_CHECKS = ('remote_lifecycle', 'remote_session', 'native_channels')
MODEL_CHECKS = ('context_injection', 'recovery', 'stopping', 'model_maintenance', 'cold_read', 'remote_session')


def read_attachment(root, record, label):
    if not isinstance(record, dict) or not isinstance(record.get('evidence'), str):
        raise ValueError('Evidence reference missing: ' + label)
    relative = Path(record['evidence'])
    attachment = (root / relative).resolve()
    if relative.is_absolute() or '..' in relative.parts or root not in attachment.parents:
        raise ValueError('Evidence must remain inside acceptance directory: ' + label)
    if not attachment.is_file():
        raise ValueError('Evidence attachment missing: ' + label)
    raw = attachment.read_bytes()
    if record.get('sha256') != hashlib.sha256(raw).hexdigest():
        raise ValueError('Evidence attachment digest differs: ' + label)
    return raw


def validate_evidence(archive, package, evidence_path, promotion=False):
    evidence = json.loads(evidence_path.read_text())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if evidence.get('schema_version') != 1:
        raise ValueError('Unsupported acceptance schema')
    if evidence.get('version') != package['version'] or evidence.get('npm_sha256') != digest:
        raise ValueError('Stable evidence does not identify this exact npm artifact')
    root = evidence_path.resolve().parent
    for host in HOSTS:
        observed_checks = {}
        for check in LOCAL_CHECKS + (REMOTE_CHECKS if promotion else ()):
            label = host + '/' + check
            record = evidence.get('core', {}).get(host, {}).get(check, {})
            if record.get('status') != 'Passed' or not isinstance(record.get('evidence'), str):
                raise ValueError('Stable gate missing: ' + label)
            observed = json.loads(read_attachment(root, record, label))
            expected = {'status': 'Passed', 'host': host, 'check': check,
                        'version': package['version'], 'npm_sha256': digest}
            if any(observed.get(k) != v for k, v in expected.items()):
                raise ValueError('Evidence attachment binding differs: ' + label)
            details = observed.get('observations')
            observed_checks[check] = details
            if not isinstance(details, dict) or not isinstance(details.get('artifacts'), list) or not details['artifacts']:
                raise ValueError('Evidence requires raw observation attachments: ' + label)
            for artifact in details['artifacts']:
                if artifact.get('evidence') == record['evidence']:
                    raise ValueError('Evidence cannot reference itself: ' + label)
                read_attachment(root, artifact, label + '/raw')
            if check in MODEL_CHECKS:
                required = ('image', 'cli_version', 'model', 'runner_sha256', 'session_id')
                if details.get('kind') != 'actual-host-model' or not all(isinstance(details.get(k), str) and details[k] for k in required):
                    raise ValueError('Actual host/model provenance missing: ' + label)
                if details.get('external_memory') is not False:
                    raise ValueError('External memory isolation missing: ' + label)
            if check == 'cold_read' and (details.get('history_available') is not False or details.get('plugin_available') is not False or not details.get('input_snapshot_sha256')):
                raise ValueError('Independent cold-read isolation missing: ' + label)
            if check == 'independent_review':
                reviewed = details.get('reviewed_sha256')
                required_checks = LOCAL_CHECKS + (REMOTE_CHECKS if promotion else ())
                current = {r['sha256'] for c,r in evidence['core'][host].items() if c != 'independent_review' and c in required_checks}
                if not details.get('reviewer') or not isinstance(reviewed,list) or not current.issubset(set(reviewed)):
                    raise ValueError('Independent review does not bind current local evidence: ' + label)
        reader, writer = observed_checks['cold_read'], observed_checks['model_maintenance']
        if reader['session_id'] == writer['session_id'] or reader['input_snapshot_sha256'] != writer.get('output_snapshot_sha256'):
            raise ValueError('Cold read must independently read the actual maintenance output: ' + host)
    return evidence

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, default=ROOT / 'release/acceptance.json')
    parser.add_argument('--promotion', action='store_true', help='Also require remote lifecycle evidence before latest')
    args = parser.parse_args()
    with tarfile.open(args.archive) as archive:
        package = json.load(archive.extractfile('package/package.json'))
    if package['name'] != 'planweft': parser.error('Unexpected package')
    if '-' in package['version']:
        if args.promotion: parser.error('Candidates cannot be promoted to latest')
        print('Candidate: next only; no stable acceptance claimed')
        return
    if not args.evidence.is_file(): parser.error('Stable acceptance evidence is missing')
    try:
        validate_evidence(args.archive, package, args.evidence, args.promotion)
    except (ValueError, OSError, TypeError, AttributeError) as error:
        parser.error(str(error))
    print('Five-host ' + ('promotion' if args.promotion else 'pre-publication') + ' gates passed')

if __name__ == '__main__': main()
