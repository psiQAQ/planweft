#!/usr/bin/env python3
"""Validate the scoped static/logic release evidence for PlanWeft 0.5.x.

This intentionally does not interpret the frozen 0.4.0 schema-3 policy.  It
rejects self-declared success and requires every applicable versioned policy
item to have a Passed evidence record.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    value = json.loads(path.read_text())
    expected = {'schema_version', 'version', 'required_prepublication',
                'required_promotion', 'not_run'}
    if set(value) != expected or value['schema_version'] != 1 or value['version'] != '0.5.0':
        raise ValueError('Unsupported 0.5 release policy')
    for key in ('required_prepublication', 'required_promotion', 'not_run'):
        items = value[key]
        if (not isinstance(items, list) or (key != 'not_run' and not items)
                or len(items) != len(set(items)) or any(
                not isinstance(item, str) or not item for item in items)):
            raise ValueError('Invalid policy list: ' + key)
    if set(value['required_prepublication']) & set(value['required_promotion']):
        raise ValueError('A release check cannot belong to both phases')
    return value


def read_attachment(evidence_path, record, label):
    """Read a hash-bound, non-self-referential attachment below evidence root."""
    if (not isinstance(record, dict) or not isinstance(record.get('evidence'), str)
            or not isinstance(record.get('sha256'), str)):
        raise ValueError('Evidence attachment missing: ' + label)
    relative = Path(record['evidence'])
    root = evidence_path.parent.resolve()
    attachment = (root / relative).resolve()
    if (relative.is_absolute() or not relative.parts or '..' in relative.parts
            or attachment == evidence_path.resolve() or root not in attachment.parents):
        raise ValueError('Evidence must remain below its evidence file: ' + label)
    if not attachment.is_file():
        raise ValueError('Evidence attachment missing: ' + label)
    if digest(attachment) != record['sha256']:
        raise ValueError('Evidence attachment digest differs: ' + label)


def validate_archive_identity(archive, version):
    """Require an npm-style PlanWeft archive, not arbitrary matching bytes."""
    with tarfile.open(archive, mode='r:gz') as packed:
        members = [member for member in packed.getmembers()
                   if member.isfile() and member.name == 'package/package.json']
        if len(members) != 1:
            raise ValueError('Archive package manifest differs')
        stream = packed.extractfile(members[0])
        if stream is None:
            raise ValueError('Archive package manifest differs')
        manifest = json.loads(stream.read())
    if (not isinstance(manifest, dict) or manifest.get('name') != 'planweft'
            or manifest.get('version') != version):
        raise ValueError('Archive package identity differs')


def validate(policy, evidence, promotion, evidence_path, archive):
    expected = {'schema_version', 'version', 'policy_sha256', 'package_sha256',
                'release_blocking', 'checks'}
    if set(evidence) != expected or evidence['schema_version'] != 1 or evidence['version'] != policy['version']:
        raise ValueError('Evidence identity differs')
    if evidence['policy_sha256'] != policy['_sha256']:
        raise ValueError('Evidence policy binding differs')
    if not archive.is_file() or evidence['package_sha256'] != digest(archive):
        raise ValueError('Evidence package digest differs')
    validate_archive_identity(archive, policy['version'])
    required = list(policy['required_prepublication'])
    if promotion:
        required += policy['required_promotion']
    expected_checks = set(required) | set(policy['not_run'])
    if set(evidence['checks']) != expected_checks:
        raise ValueError('Evidence check set differs')
    blocking = []
    for name in required:
        record = evidence['checks'][name]
        if not isinstance(record, dict) or set(record) != {'status', 'evidence', 'sha256'}:
            raise ValueError('Required record shape differs: ' + name)
        if record['status'] != 'Passed':
            blocking.append(name)
            continue
        read_attachment(evidence_path, record, name)
    for name in policy['not_run']:
        record = evidence['checks'][name]
        if record != {'status': 'Not Run', 'reason': 'outside 0.5.0 static/logic validation scope'}:
            raise ValueError('Excluded runtime record differs: ' + name)
    if evidence['release_blocking'] != bool(blocking):
        raise ValueError('release_blocking differs')
    if blocking:
        raise ValueError('Release is blocked by: ' + ', '.join(blocking))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, default=ROOT / 'release/support-policy-0.5.json')
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True,
                        help='local npm archive whose SHA-256 the evidence binds')
    parser.add_argument('--promotion', action='store_true')
    args = parser.parse_args()
    try:
        policy = load(args.policy)
        policy['_sha256'] = digest(args.policy)
        validate(policy, json.loads(args.evidence.read_text()), args.promotion,
                 args.evidence, args.archive)
    except (OSError, ValueError, json.JSONDecodeError, tarfile.TarError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
