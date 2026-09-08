#!/usr/bin/env python3
"""Translate the existing PWF runtime output into native hook responses.

Sources: cursor.com/docs/hooks; docs.github.com/en/copilot/reference/hooks-reference;
geminicli.com/docs/hooks/reference/. The native events differ: prompt-submit and
pre-tool events are not portable model-context injection surfaces.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN_ROOT / 'scripts'
REMINDER = ('[planweft] Update progress.md with observed work. If a phase is complete, '
            'update the selected task_plan.md. Read-only requests do not write records.')


def project_directory(host, payload):
    """Resolve the host workspace independently of the plugin's launch cwd."""
    candidate = payload.get('cwd')
    if candidate is None and host == 'cursor':
        roots = payload.get('workspace_roots')
        if isinstance(roots, list) and len(roots) == 1:
            candidate = roots[0]
        elif isinstance(roots, list) and len(roots) > 1:
            return None
    if candidate is None:
        candidate = os.environ.get({'cursor': 'CURSOR_PROJECT_DIR',
                                    'copilot': 'COPILOT_PROJECT_DIR',
                                    'gemini': 'GEMINI_PROJECT_DIR'}[host])
    if candidate is None:
        candidate = os.getcwd()
    if not isinstance(candidate, str) or not candidate or not Path(candidate).is_absolute():
        return None
    root = Path(candidate)
    if not root.is_dir():
        return None
    root = root.resolve()
    # A plugin cache can never become the implicit project receiving gate state.
    if root == PLUGIN_ROOT or PLUGIN_ROOT in root.parents:
        return None
    return root


def runtime_environment(payload, cwd):
    env = dict(os.environ)
    env.pop('PWF_SESSION_ID', None)
    session = payload.get('session_id') or payload.get('sessionId') or payload.get('conversation_id')
    if isinstance(session, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', session):
        env['PWF_SESSION_ID'] = session
    env['PWF_SHELL_PWD'] = str(cwd)
    env['PWF_TRUSTED_PYTHON'] = sys.executable
    return env


def run(command, cwd, env, stdin=''):
    try:
        result = subprocess.run(command, input=stdin, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True, encoding='utf-8',
                                errors='replace', cwd=cwd, env=env, timeout=7, check=False)
        return result.stdout.strip() if result.returncode == 0 else ''
    except (OSError, subprocess.TimeoutExpired):
        return ''


def context(kind, cwd, env):
    # The packaged Python twin preserves upstream selection, framing and
    # attestation rules. -I excludes project modules; -B keeps the cache clean.
    return run([sys.executable, '-I', '-B', str(SCRIPTS / 'inject-plan.py'),
                '--context=' + kind], cwd, env)


def gate(payload, cwd, env):
    if payload.get('stop_hook_active') is True:
        return {}
    if context('native-gate', cwd, env) != 'PWF_NATIVE_GATE_ACCEPTED_V1':
        return {}
    shell = shutil.which('sh')
    if not shell:
        return {}
    output = run([shell, str(SCRIPTS / 'gate-stop.sh')], cwd, env,
                 json.dumps({'stop_hook_active': False}))
    try:
        decision = json.loads(output)
    except ValueError:
        return {}
    if isinstance(decision, dict) and decision.get('decision') == 'block' and isinstance(decision.get('reason'), str):
        return {'decision': 'block', 'reason': decision['reason']}
    return {}


def handle(host, event, payload):
    if host not in {'cursor', 'copilot', 'gemini'} or not isinstance(payload, dict):
        return {}
    if os.environ.get('PLANNING_DISABLED') == '1':
        return {}
    # Only concrete host mode fields qualify here. Natural-language intent is
    # handled by the Skill; this hook never guesses from user prompt text.
    if any(str(payload.get(key, '')).lower() in {'plan', 'ask', 'readonly', 'read-only'}
           for key in ['permission_mode', 'mode', 'composer_mode']):
        return {}
    cwd = project_directory(host, payload)
    if cwd is None:
        return {}
    env = runtime_environment(payload, cwd)
    if event in {'stop', 'agentStop'}:
        if host == 'cursor':
            count = payload.get('loop_count', 0)
            if payload.get('status') != 'completed' or type(count) is not int or not 0 <= count < 3:
                return {}
        decision = gate(payload, cwd, env)
        if host == 'cursor':
            return {'followup_message': decision['reason']} if decision else {}
        return decision
    start = event in {'sessionStart', 'SessionStart', 'BeforeAgent'}
    after = event in {'postToolUse', 'AfterTool'}
    if not start and not after and event != 'PreCompress':
        return {}
    if event == 'PreCompress':
        message = context('precompact', cwd, env)
        return {'systemMessage': message} if message else {}
    message = context('userprompt' if start else 'pretool', cwd, env)
    if not message:
        return {}
    if after:
        tool = payload.get('tool_name') or payload.get('toolName') or ''
        if isinstance(tool, str) and tool.lower() in {'write', 'edit', 'create', 'apply_patch', 'write_file', 'replace', 'edit_file'}:
            message += '\n' + REMINDER
    if host == 'cursor':
        return {'additional_context': message}
    if host == 'copilot':
        return {'additionalContext': message}
    return {'hookSpecificOutput': {'hookEventName': event, 'additionalContext': message}}


def main():
    try:
        payload = json.load(sys.stdin)
        result = handle(sys.argv[1], sys.argv[2], payload)
    except (ValueError, OSError, IndexError, TypeError):
        result = {}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
