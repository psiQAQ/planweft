#!/usr/bin/env python3
"""Observe real Codex hook delivery using a loopback Responses fixture, no model.

Only a fresh temporary profile is used. The HTTP fixture records synthetic
requests and returns a constant reply; this proves host delivery, not model
understanding, semantic maintenance quality or a real provider's behavior.
"""
import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import uuid

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cli', default=shutil.which('codex'))
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output == ROOT or ROOT in output.parents:
        parser.error('--output must be a NEW directory outside the repository')
    if not args.cli or not Path(args.cli).is_file():
        parser.error('--cli must be an installed Codex executable')
    lifecycle = module('pd_lifecycle_probe', 'tests/run-native-lifecycle.py')
    staging = module('pd_staging_probe', 'tests/run-pwf-smoke.py')
    output.mkdir(parents=True)
    runner = Path(__file__).read_bytes()
    (output / 'runner.py').write_bytes(runner)
    report = {'kind': 'Real Codex host with a local synthetic Responses provider',
              'real_model': 'Not Run: no authentication or paid calls',
              'runner_sha256': hashlib.sha256(runner).hexdigest(),
              'cases': {}, 'commands': [], 'status': 'In Progress'}
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *unused):
            pass

        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get('Content-Length', '0')))
            if self.headers.get('Content-Encoding') == 'zstd':
                from compression import zstd
                raw = zstd.decompress(raw)
            payload = json.loads(raw)
            requests.append(payload)
            item = {'id': 'msg_fixture', 'type': 'message', 'role': 'assistant',
                    'status': 'completed', 'content': [{'type': 'output_text', 'text': 'OK', 'annotations': []}]}
            response = {'id': 'resp_fixture', 'object': 'response', 'status': 'completed',
                        'output': [item], 'usage': {'input_tokens': 1, 'output_tokens': 1, 'total_tokens': 2}}
            events = [
                {'type': 'response.created', 'response': {**response, 'status': 'in_progress', 'output': []}},
                {'type': 'response.output_item.added', 'output_index': 0, 'item': {**item, 'status': 'in_progress', 'content': []}},
                {'type': 'response.content_part.added', 'item_id': item['id'], 'output_index': 0,
                 'content_index': 0, 'part': {'type': 'output_text', 'text': '', 'annotations': []}},
                {'type': 'response.output_text.delta', 'item_id': item['id'], 'output_index': 0,
                 'content_index': 0, 'delta': 'OK'},
                {'type': 'response.output_text.done', 'item_id': item['id'], 'output_index': 0,
                 'content_index': 0, 'text': 'OK'},
                {'type': 'response.output_item.done', 'output_index': 0, 'item': item},
                {'type': 'response.completed', 'response': response},
            ]
            body = ''.join('event: ' + item['type'] + '\ndata: ' + json.dumps(item) + '\n\n' for item in events).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = None
    try:
        with tempfile.TemporaryDirectory(prefix='pd-codex-host-probe-') as temporary:
            root = Path(temporary)
            profile, project = root / 'profile', root / '项目 with spaces'
            project.mkdir()
            env = lifecycle.isolated_environment(profile)
            source = root / 'marketplace'
            staging.prepare_reviewed_package(source)
            report['source_inventory'] = lifecycle.inventory(source / 'dist/codex/program-design')

            def call(label, argv, extra=None):
                try:
                    result = subprocess.run(argv, cwd=project, env={**env, **(extra or {})},
                                            input='', capture_output=True, text=True, timeout=60)
                except subprocess.TimeoutExpired as error:
                    def decoded(value):
                        return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
                    result = subprocess.CompletedProcess(argv, 124, decoded(error.stdout), decoded(error.stderr))
                (output / (label + '.stdout')).write_text(result.stdout)
                (output / (label + '.stderr')).write_text(result.stderr)
                report['commands'].append({'label': label, 'argv': argv, 'returncode': result.returncode})
                return result

            report['version'] = call('version', [args.cli, '--version']).stdout.strip()
            for label, argv in [
                ('marketplace-add', [args.cli, 'plugin', 'marketplace', 'add', str(source)]),
                ('plugin-add', [args.cli, 'plugin', 'add', 'program-design@program-design']),
            ]:
                if call(label, argv).returncode:
                    raise RuntimeError(label + ' failed')
            # The bypass below is limited to this invocation of these reviewed
            # bytes. It does not grant persistent trust in a personal profile.
            candidates = list((profile / '.codex').rglob('.codex-plugin/plugin.json'))
            installed = [p.parent.parent for p in candidates
                         if json.loads(p.read_text()).get('name') == 'program-design'
                         and 'cache' in p.parts]
            expected = lifecycle.inventory(source / 'dist/codex/program-design')
            if not installed or not any(lifecycle.inventory(path) == expected for path in installed):
                raise RuntimeError('Installed plugin bytes differ from the reviewed directory')
            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            config = ('model = "pd-fixture"\nmodel_provider = "local_fixture"\n'
                      'model_context_window = 128000\nmodel_max_output_tokens = 1024\n'
                      '[model_providers.local_fixture]\nname = "Local fixture"\n'
                      'base_url = "http://127.0.0.1:' + str(server.server_port) + '/v1"\n'
                      'wire_api = "responses"\nrequires_openai_auth = false\n'
                      'request_max_retries = 0\nstream_max_retries = 0\n')
            config_path = profile / '.codex/config.toml'
            # TOML keys appended after an existing plugin table would belong to
            # that table; put provider selection before all existing tables.
            config_path.write_text(config + '\n' + config_path.read_text())
            for case, trusted, disabled in [('untrusted', False, False), ('trusted', True, False),
                                             ('new-session-recovery', True, False), ('disabled', True, True)]:
                token = uuid.uuid4().hex
                (project / 'task_plan.md').write_text('# Probe\n\nRECOVERY_CODE: ' + token +
                                                     '\n\n### Phase 1\n- **Status:** in_progress\n')
                (project / 'findings.md').write_text('Synthetic project findings.\n')
                (project / 'progress.md').write_text('Existing project progress.\n')
                before = lifecycle.inventory(project)
                requests.clear()
                argv = [args.cli, 'exec', '--skip-git-repo-check', '--json', '--ephemeral',
                        '-C', str(project), '--sandbox', 'read-only']
                if trusted:
                    argv.append('--dangerously-bypass-hook-trust')
                argv.append('Reply OK. Do not use tools or read files.')
                result = call(case, argv, {'PLANNING_DISABLED': '1'} if disabled else {})
                if result.returncode == 124:
                    raise RuntimeError(case + ' timed out; partial stdout/stderr retained')
                delivered = token in json.dumps(requests)
                expected_delivery = trusted and not disabled
                lifecycle.save(output / (case + '.requests.json'), requests)
                report['cases'][case] = {
                    'returncode': result.returncode, 'request_count': len(requests),
                    'marker_delivered': delivered, 'expected_delivery': expected_delivery,
                    'project_unchanged': lifecycle.inventory(project) == before,
                    'passed': result.returncode == 0 and bool(requests) and delivered == expected_delivery
                              and lifecycle.inventory(project) == before}
            for label, argv in [
                ('plugin-remove', [args.cli, 'plugin', 'remove', 'program-design@program-design']),
                ('marketplace-remove', [args.cli, 'plugin', 'marketplace', 'remove', 'program-design']),
            ]:
                if call(label, argv).returncode:
                    raise RuntimeError(label + ' failed')
            report['status'] = 'Passed' if all(case['passed'] for case in report['cases'].values()) else 'Failed'
        report['temporary_profile_removed'] = not root.exists()
    except Exception as error:
        report.update(status='Failed', error=str(error))
    finally:
        if server:
            server.shutdown()
            server.server_close()
        lifecycle.save(output / 'summary.json', report)
    print(json.dumps({'status': report['status'], 'output': str(output)}))
    if report['status'] != 'Passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
