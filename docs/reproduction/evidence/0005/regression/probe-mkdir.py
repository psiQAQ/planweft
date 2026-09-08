#!/usr/bin/env python3
"""Check that two plain mkdir processes cannot both create the same directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mkdir', required=True, help='Executable to test, for example /usr/bin/gnumkdir')
    parser.add_argument('--rounds', type=int, default=100)
    parser.add_argument('--output', required=True, type=Path, help='New evidence directory; never overwritten')
    args = parser.parse_args()
    executable = shutil.which(args.mkdir)
    if not executable or args.rounds < 1:
        parser.error('--mkdir must be executable and --rounds must be positive')
    output = args.output.absolute()
    if output.exists():
        parser.error('--output must not exist')
    (output / 'cases').mkdir(parents=True)
    version = subprocess.run([executable, '--version'], capture_output=True, text=True)
    cases = []
    for index in range(args.rounds):
        directory = output / 'cases' / str(index)
        command = [executable, str(directory)]
        processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for _ in range(2)]
        captured = [process.communicate() for process in processes]
        cases.append({'case': index, 'command': command,
                      'returncodes': [process.returncode for process in processes],
                      'outputs': [{'stdout': stdout, 'stderr': stderr} for stdout, stderr in captured]})
    summary = {
        'executable': executable, 'resolved_executable': str(Path(executable).resolve()),
        'sha256': hashlib.sha256(Path(executable).read_bytes()).hexdigest(),
        'version_stdout': version.stdout, 'version_stderr': version.stderr,
        'rounds': args.rounds,
        'both_succeeded': sum(case['returncodes'] == [0, 0] for case in cases),
        'unexpected_outcomes': sum(sorted(case['returncodes']) != [0, 1] for case in cases),
        'cases': cases,
    }
    summary['status'] = 'Passed' if summary['unexpected_outcomes'] == 0 else 'Failed'
    (output / 'results.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in summary.items() if key != 'cases'}, indent=2))
    return int(summary['status'] != 'Passed')


if __name__ == '__main__':
    raise SystemExit(main())
