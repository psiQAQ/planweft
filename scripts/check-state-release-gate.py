#!/usr/bin/env python3
"""Validate the deterministic P0 release evidence for PlanWeft 0.6.0."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tarfile


ROOT = Path(__file__).resolve().parents[1]
VERSION_RE = re.compile(r"0\.6\.0")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_policy(path):
    value = json.loads(path.read_text())
    expected = {'schema_version', 'version', 'required_prepublication',
                'required_promotion', 'not_run'}
    if (set(value) != expected or value['schema_version'] != 1
            or not isinstance(value['version'], str)
            or VERSION_RE.fullmatch(value['version']) is None):
        raise ValueError('Unsupported 0.6.0 release policy')
    for key in ('required_prepublication', 'required_promotion', 'not_run'):
        items = value[key]
        if (not isinstance(items, list) or (key != 'not_run' and not items)
                or len(items) != len(set(items)) or any(
                    not isinstance(item, str) or not item for item in items)):
            raise ValueError('Invalid policy list: ' + key)
    if (set(value['required_prepublication']) & set(value['required_promotion'])):
        raise ValueError('A release check cannot belong to both phases')
    return value


def read_attachment(evidence_path, record, label):
    if (not isinstance(record, dict) or set(record) != {'status', 'evidence', 'sha256'}
            or record.get('status') != 'Passed'
            or not isinstance(record.get('evidence'), str)
            or not isinstance(record.get('sha256'), str)):
        raise ValueError('Evidence attachment shape differs: ' + label)
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
    with tarfile.open(archive, mode='r:gz') as packed:
        names = {member.name for member in packed.getmembers() if member.isfile()}
        manifests = [member for member in packed.getmembers()
                     if member.isfile() and member.name == 'package/package.json']
        if len(manifests) != 1:
            raise ValueError('Archive package manifest differs')
        stream = packed.extractfile(manifests[0])
        if stream is None:
            raise ValueError('Archive package manifest differs')
        manifest = json.loads(stream.read())
    if manifest.get('name') != 'planweft' or manifest.get('version') != version:
        raise ValueError('Archive package identity differs')
    required = {
        'package/dist/manifest.json', 'package/bin/planweft.mjs',
        'package/lib/state/core.mjs', 'package/lib/state/cli.mjs',
    }
    if not required <= names:
        raise ValueError('Archive is missing required P0 state assets')


def validate(policy_path, evidence_path, archive, promotion):
    policy = load_policy(policy_path)
    policy_sha = digest(policy_path)
    evidence = json.loads(evidence_path.read_text())
    expected = {'schema_version', 'version', 'policy_sha256', 'package_sha256',
                'release_blocking', 'checks'}
    if (set(evidence) != expected or evidence['schema_version'] != 1
            or evidence['version'] != policy['version']
            or evidence['policy_sha256'] != policy_sha):
        raise ValueError('Evidence identity differs')
    if policy_path.name != 'support-policy-0.6.0.json':
        raise ValueError('Policy path does not bind 0.6.0')
    if evidence_path.parent.name != policy['version']:
        raise ValueError('Evidence path does not bind its version')
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
        if not isinstance(record, dict) or record.get('status') != 'Passed':
            blocking.append(name)
            continue
        read_attachment(evidence_path, record, name)
    not_run_reason = 'outside 0.6.0 deterministic P0 release scope'
    for name in policy['not_run']:
        record = evidence['checks'][name]
        if record != {'status': 'Not Run', 'reason': not_run_reason}:
            raise ValueError('Non-blocking runtime record differs: ' + name)
    if (not isinstance(evidence['release_blocking'], bool)
            or evidence['release_blocking'] != bool(blocking)):
        raise ValueError('release_blocking differs')
    if blocking:
        raise ValueError('Release is blocked by: ' + ', '.join(blocking))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, default=ROOT / 'release/support-policy-0.6.0.json')
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--promotion', action='store_true')
    args = parser.parse_args()
    try:
        validate(args.policy.resolve(), args.evidence.resolve(), args.archive.resolve(), args.promotion)
    except (OSError, ValueError, json.JSONDecodeError, tarfile.TarError, KeyError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
    print('Deterministic P0 ' + ('promotion' if args.promotion else 'pre-publication') + ' gate passed')


if __name__ == '__main__':
    main()
