#!/usr/bin/env python3
"""Compare CI bytes to the reviewed archive before any npm write."""
import argparse
import hashlib
import json
import os
import re
import tarfile
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    args=parser.parse_args()
    expected=os.environ.get('EXPECTED_NPM_SHA256','')
    with tarfile.open(args.archive) as tar:
        package=json.load(tar.extractfile('package/package.json'))
    stable='-' not in package['version']
    if stable and not expected:
        parser.error('Stable publication requires the reviewed exact archive SHA-256')
    if expected and not re.fullmatch('[a-f0-9]{64}',expected):
        parser.error('Invalid expected archive digest')
    actual=hashlib.sha256(args.archive.read_bytes()).hexdigest()
    if expected and actual!=expected:
        parser.error('CI archive differs from reviewed bytes; do not replace the expected digest')
    print(json.dumps({'version':package['version'],'npm_sha256':actual,'reviewed_digest_matched':bool(expected)}))


if __name__=='__main__':main()
