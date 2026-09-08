#!/usr/bin/env python3
"""Candidates may ship to next; stable packages need matching acceptance evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]

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
    evidence = json.loads(args.evidence.read_text())
    if evidence.get('version') != package['version'] or evidence.get('npm_sha256') != hashlib.sha256(args.archive.read_bytes()).hexdigest():
        parser.error('Stable evidence does not identify this exact npm artifact')
    for host in ['codex', 'claude', 'pi', 'opencode']:
        for check in ['native_lifecycle', 'model_maintenance', 'cold_read'] + (['remote_lifecycle'] if args.promotion else []):
            record = evidence.get('core', {}).get(host, {}).get(check, {})
            if record.get('status') != 'Passed' or not record.get('evidence'):
                parser.error('Stable gate missing: ' + host + '/' + check)
    print('Stable pre-publication gates passed; remote smoke still precedes latest promotion')

if __name__ == '__main__': main()
