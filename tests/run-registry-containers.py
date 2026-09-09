#!/usr/bin/env python3
"""Serial, bounded native registry acceptance in locked containers; no model/auth inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlsplit
import uuid

ROOT = Path(__file__).resolve().parents[1]
HOSTS = ('codex', 'claude', 'pi', 'opencode', 'dsh')
PROXIES = ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY',
           'http_proxy', 'https_proxy', 'all_proxy', 'no_proxy')
GIB = 1024 ** 3


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def resource_preflight(output):
    existing = output
    while not existing.exists(): existing = existing.parent
    disk = shutil.disk_usage(existing).free
    info = Path('/proc/meminfo').read_text()
    match = re.search(r'^MemAvailable:\s+(\d+)\s+kB$', info, re.M)
    if match is None: raise RuntimeError('Resource preflight: Linux MemAvailable is unavailable')
    memory = int(match[1]) * 1024
    if memory < 4 * GIB or disk < 8 * GIB:
        raise RuntimeError('Resource preflight: require 4 GiB available RAM and 8 GiB free disk')
    return {'available_memory_bytes': memory, 'free_disk_bytes': disk}


def docker_output(argv):
    result = subprocess.run(['docker', *argv], capture_output=True, text=True, timeout=30)
    if result.returncode: raise RuntimeError('Docker inspection failed')
    return result.stdout.strip()


def cleanup_container(name, token):
    """Never remove a different run's container, even if its name collides."""
    try:
        query = ['ps', '-aq', '--filter', 'name=^/' + name + '$']
        if not docker_output(query): return {'status': 'Passed', 'container_removed': True}
        owner = docker_output(['inspect', '--type', 'container', '--format',
                               '{{index .Config.Labels "planweft.registry-run"}}', name])
        if owner != token:
            return {'status': 'Failed', 'container_removed': False, 'reason': 'ownership label differs'}
        removed = subprocess.run(['docker', 'rm', '-f', name], capture_output=True, text=True, timeout=30)
        remaining = docker_output(query)
        if remaining:
            return {'status': 'Failed', 'container_removed': False, 'reason': 'container remains',
                    'remove_exit_code': removed.returncode}
        return {'status': 'Passed', 'container_removed': True, 'remove_exit_code': removed.returncode}
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        return {'status': 'Failed', 'container_removed': False, 'reason': 'cleanup cannot be verified'}


def clear_success_cache(case, passed, cleanup):
    cache = case / 'run/npm-cache'
    if not passed or cleanup.get('container_removed') is not True:
        return {'status': 'preserved', 'reason': 'failed or unverified case'}
    if cache.is_symlink() or (case / 'run').is_symlink():
        return {'status': 'preserved', 'reason': 'unexpected cache link'}
    if not cache.exists(): return {'status': 'absent'}
    if not cache.is_dir(): return {'status': 'preserved', 'reason': 'unexpected cache type'}
    size = sum(p.stat().st_size for p in cache.rglob('*') if p.is_file() and not p.is_symlink())
    shutil.rmtree(cache)
    return {'status': 'removed', 'path': 'run/npm-cache', 'bytes': size}


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=HOSTS, action='append')
    parser.add_argument('--version', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--previous-version')
    parser.add_argument('--previous-sha256')
    parser.add_argument('--image-lock', type=Path, default=ROOT / 'tests/container-images.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=600)
    args = parser.parse_args(argv)
    args.host = list(dict.fromkeys(args.host or HOSTS))
    version_pattern = r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?'
    digest_pattern = r'[a-f0-9]{64}'
    if not re.fullmatch(version_pattern, args.version): parser.error('Invalid version')
    if not re.fullmatch(digest_pattern, args.sha256): parser.error('Invalid SHA-256')
    if bool(args.previous_version) != bool(args.previous_sha256): parser.error('Previous version and SHA must be paired')
    if args.previous_version and (not re.fullmatch(version_pattern, args.previous_version)
            or not re.fullmatch(digest_pattern, args.previous_sha256) or args.previous_version == args.version):
        parser.error('Invalid previous version or SHA-256')
    if not 1 <= args.timeout <= 600: parser.error('Timeout must be 1..600 seconds')
    if args.output.is_symlink(): parser.error('Output must not be a symlink')
    args.output = args.output.resolve()
    if args.output.exists() or args.output == ROOT or ROOT in args.output.parents:
        parser.error('Output must be new and outside checkout')
    if any(c in str(args.output) for c in [',', '\n', '\r']): parser.error('Unsupported Docker mount path')
    try:
        lock_bytes = args.image_lock.read_bytes()
        lock = json.loads(lock_bytes)
        if lock.get('schema_version') != 1: raise ValueError('Invalid image lock schema')
        args.images = {host: lock['hosts'][host]['image'] for host in args.host}
        if any(not isinstance(image, str) or not re.fullmatch(r'sha256:[a-f0-9]{64}', image)
               for image in args.images.values()): raise ValueError('Image locks must be full SHA-256 IDs')
        args.lock_bytes = lock_bytes
        args.runner_bytes = (ROOT / 'tests/run-registry-smoke.py').read_bytes()
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        parser.error('Invalid local runner or image lock: ' + type(error).__name__)
    args.proxies = {}
    for key in PROXIES:
        if key not in os.environ: continue
        value = os.environ[key]
        if key.lower() != 'no_proxy' and value:
            try:
                parsed = urlsplit(value)
                if parsed.scheme not in {'http', 'https', 'socks5', 'socks5h'} or not parsed.hostname or parsed.username or parsed.password:
                    raise ValueError()
            except ValueError: parser.error('Only credential-free proxy URLs are supported')
        args.proxies[key] = value
    return args


def main(argv=None):
    args = parse_args(argv)
    # All validation and headroom checks precede directory creation or Docker access.
    resources = resource_preflight(args.output)
    for image in args.images.values():
        if docker_output(['image', 'inspect', image, '--format', '{{.Id}}']) != image:
            raise RuntimeError('Locked image identity mismatch')
    args.output.mkdir(parents=True)
    frozen = args.output / 'frozen'; frozen.mkdir()
    (frozen / 'run-registry-smoke.py').write_bytes(args.runner_bytes)
    (frozen / 'container-images.json').write_bytes(args.lock_bytes)
    wrapper = Path(__file__).read_bytes()
    (frozen / 'run-registry-containers.py').write_bytes(wrapper)
    report = {'status': 'In Progress', 'version': args.version, 'npm_sha256': args.sha256,
              'previous_version': args.previous_version, 'previous_npm_sha256': args.previous_sha256,
              'runner_sha256': hashlib.sha256(args.runner_bytes).hexdigest(),
              'wrapper_sha256': hashlib.sha256(wrapper).hexdigest(),
              'image_lock_sha256': hashlib.sha256(args.lock_bytes).hexdigest(),
              'model_sessions': 'Not Run', 'credentials_mounted': False,
              'resource_preflight': resources, 'limits': {'cpus': 2, 'memory': '3g',
                  'memory_swap_total': '3g', 'pids': 256, 'tmpfs': '512m', 'timeout_seconds': args.timeout},
              'hosts': {host: {'status': 'Not Run'} for host in args.host}}
    save(args.output / 'summary.json', report)
    for host in args.host:
        try: resources = resource_preflight(args.output)
        except (OSError, RuntimeError):
            report['hosts'][host] = {'status': 'Not Run', 'reason': 'resource preflight failed'}
            report['status'] = 'Failed'; break
        case = args.output / host; case.mkdir(); (case / 'tmp').mkdir()
        token = uuid.uuid4().hex
        name = 'planweft-registry-' + host + '-' + token
        result = {'status': 'Failed', 'image': args.images[host], 'resource_preflight': resources,
                  'exit_code': None, 'runner_sha256': report['runner_sha256']}
        command = ['docker', 'run', '--name', name, '--label', 'planweft.registry-run=' + token,
                   '--read-only', '--user', f'{os.getuid()}:{os.getgid()}', '--cap-drop=ALL',
                   '--security-opt=no-new-privileges', '--cpus=2', '--memory=3g', '--memory-swap=3g',
                   '--pids-limit=256', '--network=host', '--tmpfs', '/tmp:mode=1777,size=512m',
                   '--mount', f'type=bind,src={frozen},dst=/source/tests,readonly',
                   '--mount', f'type=bind,src={case},dst=/results', '--workdir', '/results',
                   '-e', 'TMPDIR=/results/tmp', '-e', 'PYTHONDONTWRITEBYTECODE=1',
                   *[x for key in args.proxies for x in ['-e', key]], '--entrypoint', 'python3',
                   args.images[host], '/source/tests/run-registry-smoke.py', '--host', host,
                   '--version', args.version, '--sha256', args.sha256, '--output', '/results/run']
        if args.previous_version:
            command += ['--previous-version', args.previous_version, '--previous-sha256', args.previous_sha256]
        interrupted = False
        try:
            with (case / 'container.stdout').open('w') as stdout, (case / 'container.stderr').open('w') as stderr:
                proc = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=args.timeout)
            result['exit_code'] = proc.returncode
            raw = (case / 'run/summary.json').read_bytes()
            observed = json.loads(raw)
            result['raw_summary_sha256'] = hashlib.sha256(raw).hexdigest()
            if (proc.returncode == 0 and observed.get('status') == 'Passed'
                    and observed.get('version') == args.version and observed.get('npm_sha256') == args.sha256
                    and observed.get('previous_version') == args.previous_version
                    and observed.get('previous_npm_sha256') == args.previous_sha256
                    and observed.get('runner_sha256') == report['runner_sha256']):
                result['status'] = 'Passed'
            else: result['reason'] = 'worker failed or evidence binding differs'
        except KeyboardInterrupt:
            interrupted = True; result['reason'] = 'interrupted'
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            result['reason'] = type(error).__name__
        finally:
            result['cleanup'] = cleanup_container(name, token)
            if result['cleanup']['status'] != 'Passed': result['status'] = 'Failed'
            try: result['npm_cache'] = clear_success_cache(case, result['status'] == 'Passed', result['cleanup'])
            except OSError:
                result['npm_cache'] = {'status': 'Failed', 'reason': 'cache cleanup failed'}
                result['status'] = 'Failed'
            save(case / 'container.json', result)
            report['hosts'][host] = result
            save(args.output / 'summary.json', report)
        if interrupted or result['status'] != 'Passed':
            report['status'] = 'Failed'; break
    else: report['status'] = 'Passed'
    save(args.output / 'summary.json', report)
    return 0 if report['status'] == 'Passed' else 1


if __name__ == '__main__': raise SystemExit(main())
