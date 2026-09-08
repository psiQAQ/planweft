#!/usr/bin/env python3
"""Offline installation contracts for the platform ZIPs; no host or network use.

Run: python3 -m unittest discover -s tests -p 'test_pwf_installation.py' -v
"""
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
INSTALL_SURFACES = {
    'codex': ['.codex-plugin/plugin.json', '.agents/plugins/marketplace.json',
              'hooks/codex-hooks.json', '.codex/hooks/run_sh.py',
              'skills/project-docs/SKILL.md'],
    'claude': ['.claude-plugin/plugin.json', '.claude-plugin/marketplace.json',
               'hooks/hooks.json', 'hooks/claude-hook.sh', 'commands/pd-plan.md',
               'skills/project-docs/SKILL.md'],
    'pi': ['package.json', 'SKILL.md', 'extensions/program-design/index.ts'],
    'opencode': ['.opencode/packages/opencode-program-design/package.json',
                 '.opencode/packages/opencode-program-design/package-lock.json',
                 '.opencode/packages/opencode-program-design/src/index.ts',
                 '.opencode/plugins/program-design.ts',
                 '.opencode/commands/pd-pwf.md',
                 '.opencode/commands/pd-pwf-status.md',
                 '.opencode/skills/project-docs/SKILL.md'],
    'hermes': ['.hermes/plugins/program-design/plugin.yaml',
               '.hermes/plugins/program-design/__init__.py',
               '.hermes/skills/project-docs/SKILL.md'],
    'cursor': ['.cursor/hooks.json', '.cursor/hooks.windows.json',
               '.cursor/skills/project-docs/SKILL.md'],
    'gemini': ['.gemini/settings.json', '.gemini/skills/project-docs/SKILL.md'],
    'copilot': ['.github/hooks/program-design.json',
                '.github/hooks/scripts/session-start.sh',
                '.github/hooks/scripts/session-start.ps1',
                'skills/project-docs/SKILL.md'],
    'mastracode': ['.mastracode/hooks.json',
                   '.mastracode/skills/project-docs/SKILL.md'],
    'kiro': ['.kiro/skills/project-docs/SKILL.md',
             '.kiro/skills/project-docs/assets/scripts/bootstrap.sh',
             '.kiro/skills/project-docs/assets/scripts/bootstrap.ps1'],
    'continue': ['.continue/skills/project-docs/SKILL.md',
                 '.continue/prompts/pd-plan.prompt'],
    'factory': ['.factory/skills/project-docs/SKILL.md'],
    'codebuddy': ['.codebuddy/skills/project-docs/SKILL.md'],
    'agents': ['.agents/skills/project-docs/SKILL.md'],
}


def package_files(host):
    with zipfile.ZipFile(DIST / f'program-design-0.2.0-{host}.zip') as archive:
        return {name.removeprefix('program-design/'): archive.read(name)
                for name in archive.namelist()}


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
            'invented GitHub repository': re.compile(r'OthmanAdi/program-design'),
            'unpublished OpenCode npm registration': re.compile(
                r'["\']plugin["\']\s*:\s*\[[^\]]*["\']opencode-program-design["\']'),
            'unpublished npm installation': re.compile(
                r'\b(?:pi\s+install\s+npm:|npm\s+(?:install|add|i)\s+)'
                r'(?:opencode-)?program-design(?:\s|@|$)'),
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
        catalog = json.loads(codex['.agents/plugins/marketplace.json'])
        self.assertEqual(catalog['plugins'][0]['source'], {'source': 'local', 'path': './'})
        claude = package_files('claude')
        catalog = json.loads(claude['.claude-plugin/marketplace.json'])
        self.assertEqual(catalog['name'], 'program-design')
        self.assertEqual(catalog['plugins'][0]['source'], './')
        self.assertEqual(json.loads(claude['.claude-plugin/plugin.json'])['name'],
                         catalog['plugins'][0]['name'])

        pi = package_files('pi')
        package = json.loads(pi['package.json'])
        self.assertEqual(package['name'], 'program-design')
        self.assertEqual(package['pi']['skills'], ['SKILL.md'])
        self.assertEqual(package['pi']['extensions'], ['extensions/program-design/index.ts'])
        for name in package['pi']['skills'] + package['pi']['extensions']:
            self.assertIn(name, pi)
        self.assertFalse(any(name.startswith('.pi/') for name in pi),
                         'Pi installs the unpacked package root directly')

    def test_opencode_loader_matches_the_documented_local_build(self):
        files = package_files('opencode')
        prefix = '.opencode/packages/opencode-program-design/'
        package = json.loads(files[prefix + 'package.json'])
        config = json.loads(files[prefix + 'tsconfig.json'])
        options = config['compilerOptions']
        self.assertEqual(package['scripts']['build'], 'tsc -p tsconfig.json')
        self.assertFalse(options.get('noEmit', False))
        self.assertFalse(options.get('emitDeclarationOnly', False))
        self.assertEqual(package['type'], 'module')
        source = PurePosixPath('src/index.ts')
        self.assertIn(prefix + str(source), files)
        self.assertIn('PlanningWithFiles', files[prefix + str(source)].decode())
        output = (PurePosixPath(options['outDir']) /
                  source.relative_to(options['rootDir'])).with_suffix('.js')
        self.assertEqual(str(output), 'dist/index.js')
        self.assertIn(options['rootDir'], config['include'])
        self.assertEqual(package['main'], str(output))
        self.assertEqual(package['exports']['.']['import'], './' + str(output))
        entry = '.opencode/plugins/program-design.ts'
        match = re.search(r'export\s*\{\s*PlanningWithFiles\s*\}\s*from\s*["\']([^"\']+)',
                          files[entry].decode())
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1),
                         '../packages/opencode-program-design/dist/index.js')
        target = posixpath.normpath(str(PurePosixPath(entry).parent / match.group(1)))
        self.assertEqual(target, prefix + str(output))
        for name in [prefix + 'README.md', 'INSTALL.md']:
            with self.subTest(document=name):
                self.assertRegex(files[name].decode(),
                                 r'npm ci --ignore-scripts\s*\n\s*npm run build')

    @unittest.skipUnless(shutil.which('bash') and shutil.which('sh'),
                         'Gemini command protocol test requires POSIX shells')
    def test_gemini_disabled_commands_work_in_chinese_and_space_project_path(self):
        with tempfile.TemporaryDirectory(prefix='pd-gemini-install-') as temporary:
            root = Path(temporary)
            project = root / '中文项目 有空格'
            project.mkdir()
            with zipfile.ZipFile(DIST / 'program-design-0.2.0-gemini.zip') as archive:
                for member in archive.infolist():
                    relative = member.filename.removeprefix('program-design/')
                    if not relative.startswith('.gemini/'):
                        continue
                    path = project / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(archive.read(member))
                    # Restore exactly what the package ships. Adding execution
                    # bits here would conceal an installation defect in hooks
                    # whose configuration executes non-executable files directly.
                    path.chmod((member.external_attr >> 16) & 0o777)
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
            settings = json.loads((project / '.gemini/settings.json').read_text())
            commands = [(event, hook['command'])
                        for event, groups in settings['hooks'].items()
                        for group in groups for hook in group['hooks']]
            self.assertEqual({event for event, _ in commands},
                             {'SessionStart', 'BeforeTool', 'AfterTool',
                              'BeforeModel', 'SessionEnd'})
            self.assertEqual(len(commands), 5)
            before = snapshot(project)
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
            self.assertEqual(snapshot(private_cache), {},
                             'disabled Gemini hooks must not create private cache')


if __name__ == '__main__':
    unittest.main()
