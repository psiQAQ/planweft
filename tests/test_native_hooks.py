#!/usr/bin/env python3
"""Native hook contracts against built packages; no host install or model calls."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {
    'cursor': ('sessionStart', 'postToolUse', 'additional_context'),
    'copilot': ('sessionStart', 'postToolUse', 'additionalContext'),
    'gemini': ('BeforeAgent', 'AfterTool', 'hookSpecificOutput'),
}


def snapshot(root):
    return {p.relative_to(root).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(),
            p.stat().st_mode & 0o777) for p in root.rglob('*') if p.is_file()}


class NativeHookTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='pw-native-hook-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.project = self.root / '项目 工作目录'
        self.project.mkdir()
        self.home = self.root / 'isolated-home'
        self.home.mkdir()
        self.packages = {}
        for host in HOSTS:
            package = self.root / '独立 插件缓存' / host
            shutil.copytree(ROOT / 'dist' / host / 'planweft', package)
            self.packages[host] = package
        self.env = {'PATH': os.environ.get('PATH', ''), 'HOME': str(self.home),
                    'XDG_CACHE_HOME': str(self.root / 'runtime-cache'),
                    'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1',
                    'PWF_TRUSTED_PYTHON': sys.executable}

    def plan(self, handoff=None):
        path = self.project / 'task_plan.md'
        text = ('# Task Plan: NATIVE_PROJECT_MARKER\n\n## Goal\n'
                'Verify the installed package against this project.\n\n'
                '### Phase 1: Runtime\n- **Status:** in_progress\n')
        if handoff is not None:
            text += ('\n## Documentation Handoff\n\n<!-- planweft-docs-status: '
                     + handoff + ' -->\n'
                     '- Documents considered: docs/README.md\n'
                     '- Rationale / evidence: native hook fixture\n'
                     '- Next action: continue verification\n')
        path.write_text(text)
        return path

    def hook(self, host, event, payload=None, env=None):
        package = self.packages[host]
        data = {'cwd': str(self.project), 'conversation_id': 'pw-native-session',
                'session_id': 'pw-native-session', 'sessionId': 'pw-native-session'}
        data.update(payload or {})
        result = subprocess.run([sys.executable, '-I', '-B', str(package / 'hooks/native-hook.py'),
                                 host, event], input=json.dumps(data), text=True,
                                capture_output=True, cwd=package,
                                env={**self.env, **(env or {})}, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, '')
        return json.loads(result.stdout)

    def stop(self, host, **extra):
        event = 'stop' if host == 'cursor' else 'agentStop'
        return self.hook(host, event, {'status': 'completed', 'loop_count': 0,
                                     'stopReason': 'end_turn', **extra})

    def attest(self):
        result = subprocess.run(['sh', str(self.packages['cursor'] / 'scripts/attest-plan.sh')],
                                cwd=self.project, env=self.env, text=True,
                                capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_native_context_uses_project_payload_and_leaves_packages_unchanged(self):
        self.plan()
        project_before = snapshot(self.project)
        for host, (start, after, field) in HOSTS.items():
            with self.subTest(host=host):
                package_before = snapshot(self.packages[host])
                for event in [start, after]:
                    output = self.hook(host, event, {'toolName': 'edit', 'tool_name': 'Write'})
                    self.assertEqual(set(output), {field})
                    self.assertIn('NATIVE_PROJECT_MARKER', str(output))
                    self.assertIn('===BEGIN-PWF-DATA', str(output))
                    self.assertNotIn('permissionDecision', str(output))
                self.assertIn('document handoff', str(output))
                self.assertEqual(snapshot(self.packages[host]), package_before)
        self.assertEqual(snapshot(self.project), project_before)

    def test_missing_plan_optout_modes_and_bad_roots_are_quiet(self):
        for host, (start, _, _) in HOSTS.items():
            self.assertEqual(self.hook(host, start), {})
        self.plan()
        before = snapshot(self.project)
        for host, (start, _, _) in HOSTS.items():
            with self.subTest(host=host):
                self.assertEqual(self.hook(host, start, env={'PLANNING_DISABLED': '1'}), {})
                for mode in ['plan', 'ask', 'readonly', 'read-only']:
                    self.assertEqual(self.hook(host, start, {'mode': mode}), {})
                for cwd in ['relative', str(self.packages[host]), str(self.root / 'missing')]:
                    self.assertEqual(self.hook(host, start, {'cwd': cwd}), {})
        self.assertEqual(snapshot(self.project), before)

    def test_post_write_reminder_only_reports_pending_document_handoff(self):
        self.plan('complete')
        for host, (_, after, field) in HOSTS.items():
            output = self.hook(host, after, {'toolName': 'edit', 'tool_name': 'Write'})
            self.assertNotIn('document handoff', str(output))
            self.assertEqual(set(output), {field})
        self.plan('not_required')
        for host, (_, after, _) in HOSTS.items():
            self.assertNotIn('document handoff', str(self.hook(host, after, {'toolName': 'edit'})))
        self.plan('unknown')
        for host, (_, after, _) in HOSTS.items():
            self.assertIn('document handoff', str(self.hook(host, after, {'toolName': 'edit'})))

    def test_cursor_workspace_roots_and_gemini_compression_use_native_fields(self):
        self.plan()
        output = self.hook('cursor', 'sessionStart',
                           {'cwd': None, 'workspace_roots': [str(self.project)]})
        self.assertIn('NATIVE_PROJECT_MARKER', output['additional_context'])
        self.assertEqual(self.hook('cursor', 'sessionStart', {'cwd': None,
            'workspace_roots': [str(self.project), str(self.root)]}), {})
        output = self.hook('gemini', 'PreCompress')
        self.assertEqual(set(output), {'systemMessage'})
        self.assertIn('PreCompact', output['systemMessage'])

    @unittest.skipUnless(shutil.which('sh'), 'the upstream gated continuation needs sh')
    def test_continuation_requires_existing_gate_policy_and_accepted_plan(self):
        plan = self.plan()
        for host in ['cursor', 'copilot']:
            with self.subTest(host=host):
                self.assertEqual(self.stop(host), {}, 'advisory is the default')
                self.assertFalse((self.project / '.stop_blocks').exists())
        (self.project / '.mode').write_text('gate\n')
        for host in ['cursor', 'copilot']:
            self.assertEqual(self.stop(host), {}, 'gated mode inherits the upstream attestation rule')
            self.assertFalse((self.project / '.stop_blocks').exists())
        self.attest()
        for host in ['cursor', 'copilot']:
            with self.subTest(host=host):
                for marker in ['.stop_blocks', '.gate_last_ledger']:
                    (self.project / marker).unlink(missing_ok=True)
                output = self.stop(host)
                if host == 'cursor':
                    self.assertEqual(set(output), {'followup_message'})
                else:
                    self.assertEqual(output['decision'], 'block')
                    self.assertEqual(set(output), {'decision', 'reason'})
                self.assertIn('documentation handoff pending', str(output))
                self.assertEqual(self.stop(host, stop_hook_active=True), {})
                self.assertEqual(self.stop(host), {}, 'a stalled ledger does not repeatedly continue')
        plan.write_text(plan.read_text() + '\nUNATTESTED_PLAN_CHANGE\n')
        # Remove the stall markers, so refusal proves tamper checking rather
        # than accidentally passing because the earlier gate reached its cap.
        for marker in ['.stop_blocks', '.gate_last_ledger']:
            (self.project / marker).unlink(missing_ok=True)
        for host in ['cursor', 'copilot']:
            self.assertEqual(self.stop(host), {})
            self.assertFalse((self.project / '.stop_blocks').exists())

    @unittest.skipUnless(shutil.which('sh'), 'the upstream gated continuation needs sh')
    def test_completed_handoff_keeps_the_original_gate_reason(self):
        self.plan('complete')
        (self.project / '.mode').write_text('gate\n')
        self.attest()
        for host in ['cursor', 'copilot']:
            for marker in ['.stop_blocks', '.gate_last_ledger']:
                (self.project / marker).unlink(missing_ok=True)
            output = self.stop(host)
            self.assertIn('Gated plan incomplete', str(output))
            self.assertNotIn('documentation handoff pending', str(output))

    @unittest.skipUnless(shutil.which('sh'), 'the upstream gated continuation needs sh')
    def test_gate_respects_host_status_loop_mode_and_explicit_plan_binding(self):
        self.plan()
        (self.project / '.mode').write_text('gate\n')
        self.attest()
        for status in ['aborted', 'error']:
            self.assertEqual(self.stop('cursor', status=status), {})
        for count in [-1, 3, 100, '0', True]:
            self.assertEqual(self.stop('cursor', loop_count=count), {})
        for host in ['cursor', 'copilot']:
            self.assertEqual(self.stop(host, mode='readonly'), {})
            self.assertEqual(self.hook(host, 'stop' if host == 'cursor' else 'agentStop',
                {'status': 'completed', 'loop_count': 0}, env={'PLAN_ID': 'does-not-exist'}), {})
        self.assertFalse((self.project / '.stop_blocks').exists())


if __name__ == '__main__':
    unittest.main()
