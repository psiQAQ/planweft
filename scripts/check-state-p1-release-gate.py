#!/usr/bin/env python3
"""Validate deterministic P1 release evidence for PlanWeft 0.7.0."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r'0\.7\.0')
NOT_RUN_REASON = 'outside 0.7.0 deterministic P1 release scope'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_policy(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    expected = {'schema_version', 'version', 'required_prepublication', 'required_promotion', 'not_run'}
    if set(value) != expected or value['schema_version'] != 1 or VERSION_RE.fullmatch(value['version']) is None:
        raise ValueError('Unsupported 0.7.0 P1 release policy')
    for key in ('required_prepublication', 'required_promotion', 'not_run'):
        items = value[key]
        if (not isinstance(items, list) or len(items) != len(set(items)) or
                any(not isinstance(item, str) or not item for item in items)):
            raise ValueError('Invalid policy list: ' + key)
    if not value['required_prepublication'] or set(value['required_prepublication']) & set(value['required_promotion']):
        raise ValueError('Release checks overlap or are empty')
    if set(value['not_run']) & (set(value['required_prepublication']) | set(value['required_promotion'])):
        raise ValueError('Not-run checks overlap required checks')
    return value


def safe_attachment(root, evidence_path, record, label):
    if (not isinstance(record, dict) or set(record) != {'status', 'evidence', 'sha256'} or
            record['status'] != 'Passed' or not isinstance(record['evidence'], str) or
            not re.fullmatch(r'[A-Za-z0-9_./-]+', record['evidence']) or
            not re.fullmatch(r'[0-9a-f]{64}', record['sha256'])):
        raise ValueError('Invalid Passed record: ' + label)
    target = (evidence_path.parent / record['evidence']).resolve()
    if target == evidence_path.resolve() or not target.is_file() or root not in target.parents:
        raise ValueError('Evidence attachment escapes its root: ' + label)
    if digest(target) != record['sha256']:
        raise ValueError('Evidence attachment digest differs: ' + label)
    return target


def validate_archive(archive, version):
    if not archive.is_file():
        raise ValueError('Package archive is missing')
    with tarfile.open(archive, 'r:gz') as packed:
        names = packed.getnames()
        package_names = [name for name in names if name == 'package/package.json']
        if package_names != ['package/package.json']:
            raise ValueError('Archive must contain exactly one package/package.json')
        package = json.load(packed.extractfile('package/package.json'))
        if package.get('name') != 'planweft' or package.get('version') != version:
            raise ValueError('Archive package identity differs')
        required = {'package/bin/planweft.mjs', 'package/lib/state/core.mjs',
                    'package/lib/state/cli.mjs', 'package/dist/manifest.json'}
        if not required <= set(names):
            raise ValueError('Archive is missing P1 runtime files')
        for name in names:
            if not name.startswith('package/') or '\\' in name or '/./' in name or '/../' in name or name.endswith('/'):
                raise ValueError('Unsafe archive member: ' + name)
            if '.planweft-state/' in name:
                raise ValueError('Task-side state must not be packaged')


def validate(policy_path, evidence_path, archive, promotion):
    policy = load_policy(policy_path)
    if policy_path.name != 'support-policy-0.7.0.json' or evidence_path.parent.name != policy['version']:
        raise ValueError('Policy/evidence path does not bind 0.7.0')
    evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
    expected = {'schema_version', 'version', 'policy_sha256', 'package_sha256', 'release_blocking', 'checks'}
    if set(evidence) != expected or evidence['schema_version'] != 1 or evidence['version'] != policy['version']:
        raise ValueError('Evidence identity differs')
    if evidence['policy_sha256'] != digest(policy_path) or evidence['package_sha256'] != digest(archive):
        raise ValueError('Evidence policy/package digest differs')
    validate_archive(archive, policy['version'])
    required = list(policy['required_prepublication'])
    if promotion:
        required += policy['required_promotion']
    expected_checks = set(required + policy['not_run'])
    if set(evidence['checks']) != expected_checks:
        raise ValueError('Evidence check set differs')
    root = evidence_path.parent.resolve()
    blocking = []
    for name in required:
        record = evidence['checks'][name]
        if not isinstance(record, dict) or record.get('status') != 'Passed':
            blocking.append(name)
            continue
        safe_attachment(root, evidence_path, record, name)
    for name in policy['not_run']:
        if evidence['checks'][name] != {'status': 'Not Run', 'reason': NOT_RUN_REASON}:
            raise ValueError('Non-blocking runtime record differs: ' + name)
    if not isinstance(evidence['release_blocking'], bool) or evidence['release_blocking'] != bool(blocking):
        raise ValueError('release_blocking differs')
    if blocking:
        raise ValueError('Release is blocked by: ' + ', '.join(blocking))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, default=ROOT / 'release/support-policy-0.7.0.json')
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--promotion', action='store_true')
    args = parser.parse_args()
    try:
        validate(args.policy.resolve(), args.evidence.resolve(), args.archive.resolve(), args.promotion)
    except (OSError, ValueError, json.JSONDecodeError, tarfile.TarError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print('P1 release gate: Passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
