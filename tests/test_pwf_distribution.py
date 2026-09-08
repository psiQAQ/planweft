#!/usr/bin/env python3
"""Offline distribution contracts exercised against packaged runtime scripts.

Run: python3 -m unittest discover -s tests -p 'test_pwf_distribution.py' -v
These are artifact/protocol checks, not claims of real host or model execution.
"""
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VERSION = json.loads((ROOT / 'package.json').read_text())['version']
DIST = ROOT / 'dist'
PLUGIN = DIST / 'codex/planweft'
COMMIT = '0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7'
HOSTS = {'codex', 'claude', 'pi', 'opencode', 'hermes', 'cursor', 'gemini',
         'copilot', 'mastracode', 'kiro', 'continue', 'factory', 'codebuddy', 'agents', 'dsh'}


def package_contents(host):
    root = DIST / host / 'planweft'
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


def copy_build_inputs(root):
    for source in ['scripts', 'overlays', 'vendor']:
        shutil.copytree(ROOT / source, root / source,
                        ignore=shutil.ignore_patterns('__pycache__'))


def snapshot(directory):
    """Include directory creation, file bytes and modes, but not timestamps."""
    return {str(path.relative_to(directory)):
            (path.stat().st_mode, path.read_bytes() if path.is_file() else None)
            for path in directory.rglob('*')}


def assert_snapshots_equal(test, actual, expected, message='snapshot differs'):
    # Comparing megabytes of file bodies through unittest's dictionary formatter
    # creates an enormous diff. File paths identify actionable drift directly.
    changed = sorted(name for name in actual.keys() | expected.keys()
                     if actual.get(name) != expected.get(name))
    test.assertEqual(changed, [], message)


def distribution_snapshot(directory):
    """The release contract hashes files and execution bits, independently of umask."""
    return {path.relative_to(directory).as_posix(): {
        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'executable': bool(path.stat().st_mode & 0o111)}
        for path in directory.rglob('*') if path.is_file()}


def frontmatter(body):
    return body.split('---', 2)[1] if body.startswith('---\n') else ''


class PackageContractTest(unittest.TestCase):
    def test_rebuild_is_deterministic_and_verify_detects_drift_without_writing(self):
        with tempfile.TemporaryDirectory(prefix='pw-build-contract-') as temporary:
            root = Path(temporary) / 'independent source'
            copy_build_inputs(root)
            command = [sys.executable, str(root / 'scripts/build-plugin.py')]
            env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
            first = subprocess.run(command, env=env, text=True, capture_output=True, timeout=90)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            expected = distribution_snapshot(root / 'dist')
            second = subprocess.run(command, env=env, text=True, capture_output=True, timeout=90)
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            assert_snapshots_equal(self, distribution_snapshot(root / 'dist'), expected)
            assert_snapshots_equal(self, distribution_snapshot(root / 'dist'), distribution_snapshot(DIST))
            checked = subprocess.run([*command, '--verify'], env=env,
                                     text=True, capture_output=True, timeout=90)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            assert_snapshots_equal(self, distribution_snapshot(root / 'dist'), expected)
            target = root / 'dist/codex/planweft/skills/project-docs/SKILL.md'
            original, mode = target.read_bytes(), target.stat().st_mode
            for change in ['content', 'missing', 'extra', 'executable', 'mirror', 'public-docs']:
                with self.subTest(change=change):
                    changed = target
                    if change == 'content':
                        changed.write_text('Intentional generated-file drift.\n')
                    elif change == 'missing':
                        changed.unlink()
                    elif change == 'extra':
                        changed = target.parent / 'unexpected.txt'
                        changed.write_text('Unexpected shipped file.\n')
                    elif change == 'executable':
                        changed.chmod(mode ^ 0o111)
                    elif change == 'public-docs':
                        changed = root / 'docs/installation.en.md'
                        document = changed.read_bytes()
                        changed.write_text('Generated installation-guide drift.\n')
                    else:
                        changed = root / 'plugins/planweft/skills/project-docs/SKILL.md'
                        changed.write_text('Compatibility mirror drift.\n')
                    before = snapshot(root)
                    checked = subprocess.run([*command, '--verify'], env=env,
                                             text=True, capture_output=True, timeout=90)
                    self.assertNotEqual(checked.returncode, 0, checked.stdout + checked.stderr)
                    self.assertIn(changed.name, checked.stdout + checked.stderr)
                    assert_snapshots_equal(self, snapshot(root), before, '--verify must not repair or write files')
                    if change == 'extra':
                        changed.unlink()
                    elif change == 'public-docs':
                        changed.write_bytes(document)
                    else:
                        changed.write_bytes(original)
                        changed.chmod(mode)
            assert_snapshots_equal(self, distribution_snapshot(root / 'dist'), expected)

    def test_platform_inventory_and_directory_integrity(self):
        manifest = json.loads((DIST / 'manifest.json').read_text())
        self.assertEqual(manifest['schema_version'], 2)
        self.assertEqual(manifest['product'], 'planweft')
        self.assertEqual(manifest['upstream_commit'], COMMIT)
        self.assertEqual(set(manifest['platforms']), HOSTS)
        self.assertEqual(manifest['version'], VERSION)
        self.assertEqual(list(DIST.rglob('*.zip')), [], 'old ZIPs must not remain distributable')
        self.assertEqual({path.name for path in DIST.iterdir() if path.is_dir()}, HOSTS)
        for host, item in manifest['platforms'].items():
            with self.subTest(host=host):
                self.assertEqual(item['path'], f'{host}/planweft')
                package = DIST / item['path']
                actual = {}
                for path in package.rglob('*'):
                    self.assertFalse(path.is_symlink(), str(path))
                    if path.is_file():
                        actual[path.relative_to(package).as_posix()] = {
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'executable': bool(path.stat().st_mode & 0o111)}
                self.assertEqual(actual, item['files'])
                self.assertEqual(len(actual), item['file_count'])
                encoded = json.dumps(actual, sort_keys=True, separators=(',', ':')).encode()
                self.assertEqual(hashlib.sha256(encoded).hexdigest(), item['sha256'])
        mirror = ROOT / 'plugins/planweft'
        mirrored_files = {path.relative_to(mirror).as_posix(): {
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'executable': bool(path.stat().st_mode & 0o111)}
            for path in mirror.rglob('*') if path.is_file()}
        self.assertEqual(mirrored_files, manifest['platforms']['codex']['files'],
                         'Codex compatibility mirror must match the primary bytes and execution bits')

    def test_every_bundle_retains_license_provenance_and_evidence(self):
        for host in sorted(HOSTS):
            with self.subTest(host=host):
                files = package_contents(host)
                license_text = files['LICENSE'].decode()
                self.assertIn('MIT License', license_text)
                self.assertIn('Copyright', license_text)
                provenance = json.loads(files['UPSTREAM.json'])
                self.assertEqual(provenance['upstream']['commit'], COMMIT)
                skills = [name for name in files if name.endswith('SKILL.md')]
                self.assertTrue(skills, 'a package must contain its own Skill')
                for name in skills:
                    with self.subTest(skill=name):
                        text = files[name].decode()
                        self.assertIn('(references/evidence.md)', text)
                        evidence = str(PurePosixPath(name).parent / 'references/evidence.md')
                        self.assertIn(evidence, files)
                        self.assertIn('Independent evidence review', files[evidence].decode())
                        parent = PurePosixPath(name).parent
                        self.assertEqual(files[str(parent / 'LICENSE')], files['LICENSE'])
                        self.assertEqual(files[str(parent / 'UPSTREAM.json')], files['UPSTREAM.json'])

    def test_codex_has_one_automatic_main_skill_and_its_own_hooks(self):
        manifest = json.loads((PLUGIN / '.codex-plugin/plugin.json').read_text())
        self.assertEqual(manifest['name'], 'planweft')
        self.assertEqual(manifest['version'], VERSION)
        skills_root = PLUGIN / manifest['skills']
        automatic = []
        for path in skills_root.rglob('SKILL.md'):
            front = frontmatter(path.read_text())
            policy = path.parent / 'agents/openai.yaml'
            self.assertTrue(policy.is_file(), 'every Codex entry has an explicit native invocation policy')
            if 'allow_implicit_invocation: true' in policy.read_text():
                automatic.append(path.relative_to(skills_root).as_posix())
            else:
                self.assertIn('allow_implicit_invocation: false', policy.read_text())
                self.assertIn('disable-model-invocation: true', front)
        self.assertEqual(automatic, ['project-docs/SKILL.md'])
        self.assertNotIn('hooks:', frontmatter((skills_root / automatic[0]).read_text()))
        self.assertIn('allow_implicit_invocation: true',
                      (skills_root / 'project-docs/agents/openai.yaml').read_text())
        self.assertTrue((PLUGIN / manifest['hooks']).is_file())
        self.assertFalse(any('migrated-command-skills' in str(path)
                             for path in PLUGIN.rglob('SKILL.md')))

    def test_codex_windows_dispatch_references_packaged_launcher(self):
        config = json.loads((PLUGIN / 'hooks/codex-hooks.json').read_text())
        for event, groups in config['hooks'].items():
            for group in groups:
                for hook in group['hooks']:
                    with self.subTest(event=event):
                        encoded = hook['commandWindows'].split('-EncodedCommand ', 1)[1]
                        decoded = base64.b64decode(encoded).decode('utf-16le')
                        paths = re.findall(r"'([^']+)'", decoded)
                        self.assertTrue(paths)
                        for path in paths:
                            self.assertTrue((PLUGIN / path.replace('\\', '/')).is_file(), path)
                        self.assertIn('$env:PLUGIN_ROOT', decoded)

    def test_runtime_and_skill_fallbacks_do_not_call_original_plugin(self):
        for host in sorted(HOSTS):
            files = package_contents(host)
            for name, content in files.items():
                path = PurePosixPath(name)
                if not (path.suffix in {'.sh', '.ps1', '.cmd', '.py', '.ts', '.js', '.json', '.yaml'}
                        or path.name == 'SKILL.md'):
                    continue
                if path.name in {'UPSTREAM.json', 'package-lock.json'}:
                    continue
                text = content.decode('utf-8')
                # An upstream source citation remains attribution; installation
                # paths and executable fallbacks must resolve this derivative.
                text = re.sub(r'https://github\.com/OthmanAdi/planning-with-files[^\s)\]"<>]*',
                              '<upstream-source>', text)
                if path.name == 'plan-doctor.sh':
                    # Legacy locations in the overlap inventory are inspected,
                    # not executable fallbacks. Exercise that distinction below.
                    text = re.sub(r'for PD_OLD_SURFACE in .*?\ndone\n', '', text, flags=re.S)
                with self.subTest(host=host, path=name):
                    self.assertTrue('planning-with-files' not in text,
                                    'original plugin identity remains in a runtime/install surface')
                    normalized = text.replace('\\\\', '\\')
                    stale = re.search(r'skills[/\\]planweft(?:[/\\]|["\'])', normalized)
                    self.assertIsNone(stale, 'skill fallback should name project-docs')
                    self.assertTrue('/home/psi/' not in text, 'personal workspace path leaked')
                    # This one literal is a runtime mktemp template inside the
                    # DSH sandbox, not the builder's scratch directory.
                    scratch_text = text
                    if host == 'dsh' and path == PurePosixPath('hooks/dsh-hook.sh'):
                        scratch_text = text.replace('mktemp -d /tmp/planweft-hook.XXXXXX', 'mktemp -d RUNTIME_CACHE')
                    self.assertTrue('/tmp/planweft-' not in scratch_text, 'build scratch path leaked')

    def test_auxiliary_command_files_are_namespaced_and_explicit(self):
        seen = 0
        for host in sorted(HOSTS):
            for name, content in package_contents(host).items():
                path = PurePosixPath(name)
                if path.suffix != '.md' or not {'commands', 'prompts'}.intersection(path.parts):
                    continue
                with self.subTest(host=host, path=name):
                    seen += 1
                    self.assertTrue(path.stem.startswith('pw-'), name)
                    text = content.decode()
                    if text.startswith('---\n'):
                        self.assertIn('disable-model-invocation: true', frontmatter(text))
        self.assertGreater(seen, 0)

    def test_pi_package_entries_and_registered_commands_are_local(self):
        files = package_contents('pi')
        package = json.loads(files['package.json'])
        self.assertEqual(package['name'], 'planweft')
        self.assertEqual(package['version'], VERSION)
        for path in package['pi']['skills'] + package['pi']['extensions']:
            self.assertIn(path, files)
        self.assertTrue({'LICENSE', 'UPSTREAM.json', 'references/'}.issubset(package['files']))
        source = '\n'.join(data.decode() for name, data in files.items() if name.endswith('.ts'))
        commands = re.findall(r'registerCommand\(\s*["\']([^"\']+)', source)
        self.assertTrue(commands)
        self.assertTrue(all(name.startswith('pw-') for name in commands), commands)
        self.assertIn('pw-plan-status', commands)
        self.assertNotIn('planning-with-files', source)

    def test_opencode_tools_are_namespaced_and_package_retains_attribution(self):
        files = package_contents('opencode')
        source = files['src/index.ts'].decode()
        names = re.findall(r'\b([A-Za-z_]\w*):\s*tool\(', source)
        self.assertEqual(set(names), {'pw_init', 'pw_status', 'pw_check'})
        package = json.loads(files['package.json'])
        self.assertEqual(package['name'], 'opencode-planweft')
        for path in ['LICENSE', 'UPSTREAM.json']:
            self.assertIn(path, package['files'])
            self.assertIn(path, files)


@unittest.skipUnless(shutil.which('bash') and shutil.which('sh'), 'POSIX runtime requires bash and sh')
class PackagedRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.installed = tempfile.TemporaryDirectory(prefix='pw-installed-')
        cls.addClassCleanup(cls.installed.cleanup)
        install_parent = Path(cls.installed.name) / '插件 安装目录'
        cls.plugin = install_parent / 'planweft'
        shutil.copytree(PLUGIN, cls.plugin)
        cls.gemini = install_parent / 'Gemini 独立扩展'
        shutil.copytree(DIST / 'gemini/planweft', cls.gemini)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='pw-protocol-')
        self.addCleanup(temporary.cleanup)
        self.temporary = Path(temporary.name)
        self.project = self.temporary / '项目 工作目录'
        self.project.mkdir()
        cache = self.temporary / 'private-cache'
        cache.mkdir()
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith('PWF_') and key not in {
                        'PLAN_ID', 'PLANNING_DISABLED', 'PYTHON_BIN',
                        'CLAUDE_PLUGIN_ROOT', 'CLAUDE_SKILL_DIR', 'PLUGIN_ROOT'}}
        self.env.update(XDG_CACHE_HOME=str(cache), PYTHONDONTWRITEBYTECODE='1',
                        PWF_TRUSTED_PYTHON=sys.executable, PLUGIN_ROOT=str(self.plugin),
                        CLAUDE_PLUGIN_ROOT=str(self.plugin))

    def run_script(self, name, *args, extra_env=None, payload='', cwd=None):
        path = self.plugin / name
        interpreter = sys.executable if path.suffix == '.py' else 'bash'
        result = subprocess.run([interpreter, str(path), *args], cwd=cwd or self.project,
                                env={**self.env, **(extra_env or {})}, input=payload,
                                text=True, capture_output=True, timeout=20)
        return result

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def assert_plan_frame(self, context):
        match = re.search(
            r'===BEGIN-PWF-DATA kind=plan nonce=(\w+) bytes=(\d+) sha256=([0-9a-f]{64}) '
            r'truncated=false===\n(.*?)\n===END-PWF-DATA kind=plan nonce=\1===',
            context, re.DOTALL)
        self.assertIsNotNone(match, 'plan must be bounded by matching nonce data markers')
        payload = match.group(4).encode()
        self.assertEqual(len(payload), int(match.group(2)))
        self.assertEqual(hashlib.sha256(payload).hexdigest(), match.group(3))

    def plan(self, title='PACKAGED_PLAN_MARKER'):
        path = self.project / 'task_plan.md'
        path.write_text(f'# Task Plan: {title}\n\n## Goal\nVerify packaged behavior.\n\n'
                        '## Next Step\nRun the contract.\n\n'
                        '### Phase 1: Runtime\n- **Status:** in_progress\n')
        return path

    def payload(self, event, **extra):
        return json.dumps({'cwd': str(self.project), 'session_id': 'pw-protocol-session',
                           'hook_event_name': event, **extra})

    def test_no_plan_hooks_are_silent_and_do_not_create_project_state(self):
        before = snapshot(self.project)
        for event in ['userprompt', 'pretool', 'posttool', 'precompact', 'stop']:
            with self.subTest(surface='skill', event=event):
                result = self.run_script('scripts/skill-hook.sh', '--event=' + event,
                                         payload=self.payload('UserPromptSubmit'))
                self.assertEqual(self.assert_ok(result), '')
        for script in ['session-start.sh', 'user-prompt-submit.sh', 'pre-compact.sh']:
            with self.subTest(surface='codex', event=script):
                result = self.run_script('.codex/hooks/run_sh.py', script,
                                         payload=self.payload('UserPromptSubmit'))
                self.assertEqual(self.assert_ok(result), '')
        self.assertEqual(self.assert_ok(self.run_script('.codex/hooks/stop.py',
                         payload=self.payload('Stop'))), '')
        self.assertEqual(snapshot(self.project), before)

    def test_default_initialization_is_advisory_and_preserves_existing_records(self):
        self.assert_ok(self.run_script('scripts/init-session.sh'))
        for name in ['task_plan.md', 'findings.md', 'progress.md']:
            self.assertTrue((self.project / name).is_file())
        self.assertFalse((self.project / '.mode').exists())
        self.assertFalse((self.project / '.plan-attestation').exists())
        (self.project / 'findings.md').write_text('User-authored findings must survive.\n')
        before = snapshot(self.project)
        self.assert_ok(self.run_script('scripts/init-session.sh'))
        self.assertEqual(snapshot(self.project), before)

    def test_named_initialization_resolves_its_plan_not_root(self):
        self.plan('ROOT_PLAN_MUST_NOT_LEAK')
        self.assert_ok(self.run_script('scripts/init-session.sh', 'Parallel verification'))
        pointer = (self.project / '.planning/.active_plan').read_text().strip()
        selected = self.project / '.planning' / pointer
        self.assertTrue((selected / 'task_plan.md').is_file())
        result = self.run_script('scripts/resolve-plan-dir.sh', extra_env={'PLAN_ID': pointer})
        self.assertEqual(Path(self.assert_ok(result).strip()).resolve(), selected.resolve())
        (selected / 'task_plan.md').write_text('# SELECTED_PLAN_MARKER\n')
        context = self.assert_ok(self.run_script('scripts/inject-plan.sh', '--context=userprompt',
                                                extra_env={'PLAN_ID': pointer}))
        self.assertIn('SELECTED_PLAN_MARKER', context)
        self.assertNotIn('ROOT_PLAN_MUST_NOT_LEAK', context)

    def test_wrong_explicit_selector_refuses_recovery_and_status_write(self):
        self.plan('ROOT_SECRET_MARKER')
        before = snapshot(self.project)
        wrong = {'PLAN_ID': 'does-not-exist'}
        result = self.run_script('scripts/resolve-plan-dir.sh', extra_env=wrong)
        # The resolver always exits zero for lifecycle compatibility; refusal
        # is an empty selected path, not a fallback or an exception.
        self.assertEqual(self.assert_ok(result), '')
        context = self.assert_ok(self.run_script('scripts/inject-plan.sh', '--context=userprompt',
                                                extra_env=wrong))
        self.assertNotIn('ROOT_SECRET_MARKER', context)
        self.assertIn('PLAN_ID', context)
        result = self.run_script('scripts/phase-status.sh', '1', 'complete', extra_env=wrong)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(snapshot(self.project), before)

    def test_attested_plan_injects_and_changed_bytes_are_refused(self):
        plan = self.plan()
        self.assert_ok(self.run_script('scripts/attest-plan.sh'))
        context = self.assert_ok(self.run_script('scripts/inject-plan.sh', '--context=userprompt'))
        self.assertIn('PACKAGED_PLAN_MARKER', context)
        self.assert_plan_frame(context)
        plan.write_text(plan.read_text().replace('PACKAGED_PLAN_MARKER', 'UNATTESTED_CONTENT_MARKER'))
        refused = self.assert_ok(self.run_script('scripts/inject-plan.sh', '--context=userprompt'))
        self.assertIn('PLAN TAMPERED', refused)
        self.assertNotIn('UNATTESTED_CONTENT_MARKER', refused)
        self.assertNotIn('Verify packaged behavior.', refused)

    def test_codex_dispatch_emits_native_context_from_unicode_install_path(self):
        self.plan('CODEX_NATIVE_CONTEXT_MARKER')
        result = self.run_script('.codex/hooks/run_sh.py', 'user-prompt-submit.sh',
                                 payload=self.payload('UserPromptSubmit'))
        response = json.loads(self.assert_ok(result))
        specific = response['hookSpecificOutput']
        self.assertEqual(specific['hookEventName'], 'UserPromptSubmit')
        self.assertIn('CODEX_NATIVE_CONTEXT_MARKER', specific['additionalContext'])
        self.assert_plan_frame(specific['additionalContext'])

    def test_disabled_hooks_do_not_mutate_existing_plan_or_write_new_project_files(self):
        self.assert_ok(self.run_script('scripts/init-session.sh', '--gated'))
        before = snapshot(self.project)
        disabled = {'PLANNING_DISABLED': '1'}
        for event in ['userprompt', 'pretool', 'posttool', 'precompact', 'stop']:
            with self.subTest(surface='skill', event=event):
                result = self.run_script('scripts/skill-hook.sh', '--event=' + event,
                                         extra_env=disabled, payload=self.payload('Stop'))
                self.assertEqual(self.assert_ok(result), '')
        for script, event in [('run_sh.py', 'UserPromptSubmit'), ('pre_tool_use.py', 'PreToolUse'),
                              ('post_tool_use.py', 'PostToolUse'), ('stop.py', 'Stop')]:
            with self.subTest(surface='codex', event=event):
                args = ['user-prompt-submit.sh'] if script == 'run_sh.py' else []
                result = self.run_script('.codex/hooks/' + script, *args, extra_env=disabled,
                                         payload=self.payload(event, tool_name='apply_patch'))
                self.assertEqual(self.assert_ok(result), '')
        self.assertEqual(snapshot(self.project), before)

    def test_repeated_posttool_nudges_are_deduplicated_per_turn(self):
        self.plan()
        request = self.payload('UserPromptSubmit')
        self.assert_ok(self.run_script('scripts/skill-hook.sh', '--event=userprompt', payload=request))
        first = self.assert_ok(self.run_script('scripts/skill-hook.sh', '--event=posttool', payload=request))
        repeated = self.assert_ok(self.run_script('scripts/skill-hook.sh', '--event=posttool', payload=request))
        self.assertTrue(first)
        self.assertEqual(repeated, '')
        self.assert_ok(self.run_script('scripts/skill-hook.sh', '--event=userprompt', payload=request))
        next_turn = self.assert_ok(self.run_script('scripts/skill-hook.sh', '--event=posttool', payload=request))
        self.assertTrue(next_turn)

    def test_doctor_reports_original_install_without_executing_it(self):
        home = self.temporary / 'home'
        old = home / '.claude/skills/planning-with-files/scripts'
        old.mkdir(parents=True)
        for helper in ['inject-plan.sh', 'check-complete.sh', 'resolve-plan-dir.sh']:
            (old / helper).write_text('#!/bin/sh\ntouch OLD_PLUGIN_EXECUTED\n')
        result = self.run_script('scripts/plan-doctor.sh', extra_env={'HOME': str(home)})
        self.assertIn('original PWF installation detected', self.assert_ok(result))
        self.assertIn('does not prove activation', result.stdout)
        self.assertFalse((self.project / 'OLD_PLUGIN_EXECUTED').exists())

    def test_mastracode_opt_out_suppresses_all_registered_reminders(self):
        self.plan()
        before = snapshot(self.project)
        mastra = json.loads(package_contents('mastracode')['.mastracode/hooks.json'])
        commands = [('mastracode:' + event, handler['command'], '')
                    for event, handlers in mastra.items() for handler in handlers]
        self.assertEqual(len(commands), 4)
        for name, command, expected in commands:
            with self.subTest(hook=name):
                result = subprocess.run(['bash', '-c', command], cwd=self.project,
                                        env={**self.env, 'PLANNING_DISABLED': '1'}, input='{}',
                                        text=True, capture_output=True, timeout=20)
                self.assertEqual(self.assert_ok(result).strip(), expected)
        self.assertEqual(snapshot(self.project), before)

    def test_gemini_native_hook_ignores_project_json_module(self):
        self.plan()
        # A normal project may contain json.py. Hooks must not import it while
        # escaping their own JSON protocol, even when PYTHONPATH names the cwd.
        (self.project / 'json.py').write_text(
            'from pathlib import Path\nPath("PROJECT_MODULE_EXECUTED").touch()\n'
            'raise RuntimeError("project json module imported by hook")\n')
        for event in ['SessionStart', 'BeforeAgent']:
            with self.subTest(event=event):
                result = subprocess.run([sys.executable, '-I', '-B',
                                         str(self.gemini / 'hooks/native-hook.py'), 'gemini', event],
                                        cwd=self.project, env={**self.env, 'PYTHONPATH': str(self.project)},
                                        input='{}', text=True, capture_output=True, timeout=20)
                message = json.loads(self.assert_ok(result))
                self.assertIn('PACKAGED_PLAN_MARKER',
                              message.get('hookSpecificOutput', {}).get('additionalContext', ''),
                              'enabled hook must still deliver its context')
                self.assertFalse((self.project / 'PROJECT_MODULE_EXECUTED').exists())

    def test_expanded_templates_keep_upstream_phase_semantics(self):
        vendor = ROOT / 'vendor/planning-with-files'
        manifest = json.loads((vendor / 'upstream.json').read_text())
        with tarfile.open(vendor / manifest['archive'], mode='r:gz') as source:
            for name in ['task_plan.md', 'task_plan_autonomous.md', 'analytics_task_plan.md']:
                with self.subTest(template=name):
                    original = source.extractfile('skills/planning-with-files/templates/' + name).read()
                    baseline = self.project / 'original.md'
                    baseline.write_bytes(original)
                    expanded = self.plugin / 'skills/project-docs/templates' / name
                    expected = self.assert_ok(self.run_script('scripts/check-complete.sh', str(baseline)))
                    actual = self.assert_ok(self.run_script('scripts/check-complete.sh', str(expanded)))
                    self.assertEqual(actual, expected)
                    self.assertTrue('## Scope and acceptance evidence' in expanded.read_text(),
                                    name + ' lacks its evidence extension')
                    plan = self.project / 'task_plan.md'
                    plan.write_bytes(expanded.read_bytes())
                    self.assert_ok(self.run_script('scripts/phase-status.sh', '1', 'complete'))
                    rewritten = plan.read_text()
                    self.assertIn('**Status:** complete', rewritten)
                    self.assertIn('## Handoff evidence', rewritten)


if __name__ == '__main__':
    unittest.main()
