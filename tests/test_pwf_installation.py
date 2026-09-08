#!/usr/bin/env python3
"""Offline installation contracts for the native platform directories; no host or network use.

Run: python3 -m unittest discover -s tests -p 'test_pwf_installation.py' -v
"""
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
INSTALL_SURFACES = {
    'codex': ['.codex-plugin/plugin.json', 'hooks/codex-hooks.json',
              '.codex/hooks/run_sh.py', 'skills/project-docs/SKILL.md'],
    'claude': ['.claude-plugin/plugin.json', 'hooks/hooks.json',
               'hooks/claude-hook.sh', 'commands/pw-plan.md', 'skills/project-docs/SKILL.md'],
    'pi': ['package.json', 'SKILL.md', 'extensions/planweft/index.ts'],
    'opencode': ['package.json', 'package-lock.json', 'src/index.ts', 'dist/index.js',
                 'commands/pw-pwf.md', 'commands/pw-pwf-status.md',
                 'skills/project-docs/SKILL.md'],
    'hermes': ['plugin.yaml', '__init__.py', 'skills/project-docs/SKILL.md'],
    'cursor': ['.cursor-plugin/plugin.json', 'hooks/hooks.json', 'skills/project-docs/SKILL.md'],
    'gemini': ['gemini-extension.json', 'hooks/hooks.json', 'skills/project-docs/SKILL.md'],
    'copilot': ['plugin.json', 'hooks.json', 'skills/project-docs/SKILL.md'],
    'mastracode': ['.mastracode/hooks.json', '.mastracode/skills/project-docs/SKILL.md'],
    'kiro': ['plugin.json', 'skills/project-docs/SKILL.md',
             'skills/project-docs/assets/scripts/bootstrap.sh',
             'skills/project-docs/assets/scripts/bootstrap.ps1'],
    'continue': ['.continue/skills/project-docs/SKILL.md', '.continue/prompts/pw-plan.prompt'],
    'factory': ['.factory-plugin/plugin.json', 'skills/project-docs/SKILL.md'],
    'codebuddy': ['.codebuddy-plugin/plugin.json', 'skills/project-docs/SKILL.md'],
    'agents': ['.agents/skills/project-docs/SKILL.md'],
}


def package_files(host):
    root = DIST / host / 'planweft'
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


def snapshot(directory):
    """Capture project content and modes, including newly created directories."""
    return {path.relative_to(directory).as_posix():
            (path.stat().st_mode, path.read_bytes() if path.is_file() else None)
            for path in directory.rglob('*')}


class InstallationContractTest(unittest.TestCase):
    def test_installation_surfaces_do_not_advertise_unpublished_sources(self):
        # Local package names and upstream attribution URLs remain valid. These
        # patterns target instructions that would fetch nonexistent releases.
        forbidden = {
            'invented GitHub repository': re.compile(r'OthmanAdi/planweft'),
            'unpublished OpenCode npm registration': re.compile(
                r'["\']plugin["\']\s*:\s*\[[^\]]*["\']opencode-planweft["\']'),
            'unpublished npm installation': re.compile(
                r'\b(?:pi\s+install\s+npm:|npm\s+(?:install|add|i)\s+)'
                r'(?:opencode-)?planweft(?:\s|@|$)'),
            'unpublished-package instruction': re.compile(
                r'Users install the published package'),
        }
        problems = []
        for host in sorted(INSTALL_SURFACES):
            for name, content in package_files(host).items():
                if PurePosixPath(name).suffix not in {
                        '.md', '.prompt', '.json', '.yaml', '.yml', '.toml',
                        '.ts', '.js', '.sh', '.ps1', '.cmd', '.py'}:
                    continue
                text = content.decode('utf-8')
                for label, pattern in forbidden.items():
                    if match := pattern.search(text):
                        line = text.count('\n', 0, match.start()) + 1
                        problems.append(f'{host}:{name}:{line}: {label}')
        self.assertEqual(problems, [], '\n'.join(problems))

    def test_each_platform_has_its_documented_installation_entries(self):
        manifest = json.loads((DIST / 'manifest.json').read_text())
        self.assertEqual(set(manifest['platforms']), set(INSTALL_SURFACES))
        for host, entries in INSTALL_SURFACES.items():
            files = package_files(host)
            with self.subTest(host=host):
                for name in [*entries, 'INSTALL.md', 'LICENSE', 'UPSTREAM.json']:
                    self.assertIn(name, files, f'{host} is missing {name}')
                for name in entries:
                    if name.endswith('SKILL.md'):
                        base = str(PurePosixPath(name).parent)
                        prefix = '' if base == '.' else base + '/'
                        for dependency in ['scripts/init-session.sh',
                                           'scripts/check-complete.sh',
                                           'templates/task_plan.md',
                                           'references/evidence.md']:
                            self.assertIn(prefix + dependency, files)

        codex = package_files('codex')
        plugin = json.loads(codex['.codex-plugin/plugin.json'])
        self.assertIn(plugin['hooks'].removeprefix('./'), codex)
        pi = package_files('pi')
        package = json.loads(pi['package.json'])
        self.assertEqual(package['name'], 'planweft')
        self.assertEqual(package['pi']['skills'], ['SKILL.md'])
        self.assertEqual(package['pi']['extensions'], ['extensions/planweft/index.ts'])
        for name in package['pi']['skills'] + package['pi']['extensions']:
            self.assertIn(name, pi)
        self.assertFalse(any(name.startswith('.pi/') for name in pi),
                         'Pi installs the unpacked package root directly')

    def test_opencode_precompiled_entry_has_all_relative_runtime_modules(self):
        files = package_files('opencode')
        package = json.loads(files['package.json'])
        config = json.loads(files['tsconfig.json'])
        options = config['compilerOptions']
        self.assertEqual(package['type'], 'module')
        self.assertFalse(options.get('noEmit', False))
        self.assertFalse(options.get('emitDeclarationOnly', False))
        source = PurePosixPath('src/index.ts')
        self.assertIn('PlanningWithFiles', files[str(source)].decode())
        output = (PurePosixPath(options['outDir']) /
                  source.relative_to(options['rootDir'])).with_suffix('.js')
        self.assertEqual(str(output), 'dist/index.js')
        self.assertEqual(package['main'], str(output))
        self.assertEqual(package['exports']['.']['import'], './' + str(output))
        self.assertIn(str(output), files, 'npm entry must work without a user build step')
        self.assertTrue(any(path.rstrip('/') == 'dist' for path in package['files']))
        for name, data in files.items():
            if not name.startswith('dist/') or not name.endswith('.js'):
                continue
            for target in re.findall(r"(?:from|import)\s*['\"](\.[^'\"]+)['\"]", data.decode()):
                resolved = PurePosixPath(name).parent / target
                self.assertIn(str(resolved), files, f'{name} references missing runtime module {target}')

    @unittest.skipUnless(shutil.which('bash') and shutil.which('sh'),
                         'Gemini command protocol test requires POSIX shells')
    def test_gemini_disabled_commands_work_in_chinese_and_space_project_path(self):
        with tempfile.TemporaryDirectory(prefix='pw-gemini-install-') as temporary:
            root = Path(temporary)
            project = root / '中文项目 有空格'
            project.mkdir()
            extension = root / '扩展 安装目录' / 'planweft'
            shutil.copytree(DIST / 'gemini/planweft', extension)
            (project / 'task_plan.md').write_text(
                '# Existing plan\n\n### Phase 1\n- **Status:** in_progress\n')
            (project / 'progress.md').write_text('User-owned progress.\n')
            (project / 'findings.md').write_text('User-owned findings.\n')
            private_cache = root / 'private-cache'
            private_cache.mkdir()
            env = {key: value for key, value in os.environ.items()
                   if not key.startswith(('PWF_', 'GEMINI_'))
                   and key not in {'PLAN_ID', 'PLANNING_DISABLED'}}
            env.update(GEMINI_PROJECT_DIR=str(project), PLANNING_DISABLED='1',
                       XDG_CACHE_HOME=str(private_cache), PYTHONDONTWRITEBYTECODE='1')
            settings = json.loads((extension / 'hooks/hooks.json').read_text())
            commands = [(event, hook['command'].replace('${extensionPath}', str(extension)))
                        for event, groups in settings['hooks'].items()
                        for group in groups for hook in group['hooks']]
            self.assertEqual({event for event, _ in commands},
                             {'SessionStart', 'BeforeAgent', 'AfterTool', 'PreCompress'})
            self.assertEqual(len(commands), 4)
            before = snapshot(project)
            installed_before = snapshot(extension)
            for event, command in commands:
                with self.subTest(event=event):
                    result = subprocess.run(['sh', '-c', command], cwd=project,
                                            env=env, input='{}', text=True,
                                            capture_output=True, timeout=15)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(result.stderr, '')
                    self.assertEqual(json.loads(result.stdout), {})
                    self.assertEqual(snapshot(project), before,
                                     'a disabled hook must not change project files')
            self.assertEqual(snapshot(extension), installed_before)
            self.assertEqual(snapshot(private_cache), {},
                             'disabled Gemini hooks must not create private cache')


if __name__ == '__main__':
    unittest.main()
