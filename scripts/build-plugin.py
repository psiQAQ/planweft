#!/usr/bin/env python3
"""Generate self-contained platform distributions from the pinned PWF archive.

Only this builder and overlays are maintained. No network access or upstream
scripts run during generation. --verify compares bytes and executable modes.
"""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'vendor/planning-with-files'
OVERLAY = ROOT / 'overlays/planweft'
VERSION = '0.4.0-rc.2'
PRODUCT = 'planweft'
SKILL = 'project-docs'
DESCRIPTION = ('Persistent file planning and task-relevant project documentation. '
               'Use for multi-step implementation, documented work and handoffs; '
               'maintain requirements, decisions and observed evidence as needed. '
               'Reading, diagnosis and host plan mode remain read-only. '
               'No project opt-in is required; respect applicable project rules. '
               'Hooks inject selected project context; session history access is explicit. '
               'Optional host-aware continuation; no network upload path.')
UPSTREAM_URL = 'https://github.com/OthmanAdi/planning-with-files'
COMMANDS = ['plan', 'start', 'status', 'pwf', 'pwf-status', 'plan-status',
            'plan-attest', 'plan-doctor', 'plan-execute', 'plan-goal', 'plan-loop',
            'plan-ar', 'plan-de', 'plan-es', 'plan-zh', 'plan-zht']
HOSTS = ['codex', 'claude', 'pi', 'opencode', 'hermes', 'cursor', 'gemini',
         'copilot', 'mastracode', 'kiro', 'continue', 'factory', 'codebuddy', 'agents', 'dsh']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_upstream():
    manifest = json.loads((VENDOR / 'upstream.json').read_text())
    packed = (VENDOR / manifest['archive']).read_bytes()
    if sha(packed) != manifest['sha256']:
        raise ValueError('upstream archive digest mismatch')
    inventory = json.loads((VENDOR / 'inventory.json').read_text())
    result = {}
    with tarfile.open(fileobj=io.BytesIO(packed), mode='r:gz') as archive:
        for entry in archive:
            if entry.isdir():
                continue
            path = PurePosixPath(entry.name)
            if not entry.isfile() or path.is_absolute() or '..' in path.parts:
                raise ValueError('unsafe upstream archive member: ' + entry.name)
            data = archive.extractfile(entry).read()
            expected = inventory[entry.name]
            if sha(data) != expected['sha256'] or oct(entry.mode) != expected['mode']:
                raise ValueError('upstream inventory mismatch: ' + entry.name)
            if entry.name in result:
                raise ValueError('duplicate upstream member: ' + entry.name)
            result[entry.name] = (data, entry.mode)
    if set(result) != set(inventory) or len(result) != manifest['file_count']:
        raise ValueError('incomplete upstream archive')
    return result, manifest


def command_name(name):
    return 'pw-' + name


def map_path(path):
    path = path.replace('planning-with-files', PRODUCT)
    path = path.replace('skills/planweft', 'skills/' + SKILL)
    path = path.replace('skills/i18n/planweft-', 'skills/i18n/' + SKILL + '-')
    if path == '.continue/prompts/planweft.prompt':
        return '.continue/prompts/pw-plan.prompt'
    parts = path.split('/')
    if 'commands' in parts or 'prompts' in parts:
        if parts[-1].endswith('.md') and parts[-1][:-3] in COMMANDS:
            parts[-1] = command_name(parts[-1][:-3]) + '.md'
    return '/'.join(parts)


def identity_text(text):
    # Source citations are provenance, not executable fallback locations.
    text = text.replace(UPSTREAM_URL, '__PW_UPSTREAM_URL__')
    text = text.replace('planning-with-files:planning-with-files', PRODUCT + ':' + SKILL)
    text = text.replace('planning-with-files', PRODUCT)
    text = text.replace('skills/planweft', 'skills/' + SKILL)
    text = text.replace('skills/i18n/planweft-', 'skills/i18n/' + SKILL + '-')
    text = re.sub(r'planweft-(ar|de|es|zh|zht)(?=[\"\'/\\])', r'project-docs-\1', text)
    text = re.sub(r'(skills\\+)planweft', r'\g<1>project-docs', text)
    # pathlib, path.join and PowerShell build skill paths from separate tokens.
    text = re.sub(r'([\"\']skills[\"\']\s*[/,]\s*[\"\'])planweft', r'\g<1>project-docs', text)
    text = re.sub(r'(SKILL_DIR_NAME\s*=\s*[\"\'])planweft', r'\g<1>project-docs', text)
    text = text.replace('path.join(base, "planweft")', 'path.join(base, "project-docs")')
    text = text.replace('planning_with_files', 'planweft')
    text = text.replace('pwf_init', 'pw_init').replace('pwf_status', 'pw_status').replace('pwf_check', 'pw_check')
    # Config keys, PWF_* env vars, PLAN_ID and disk state remain compatible.
    for name in sorted(COMMANDS, key=len, reverse=True):
        mapped = command_name(name)
        text = re.sub(r'(?<![\w./-])/' + re.escape(name) + r'(?![\w./-])', '/' + mapped, text)
        text = text.replace('commands/' + name + '.md', 'commands/' + mapped + '.md')
        text = re.sub(r'(registerCommand\(\s*[\"\'])' + re.escape(name) + r'([\"\'])', r'\g<1>' + mapped + r'\2', text)
        text = re.sub(r'(name\s*=\s*[\"\'])' + re.escape(name) + r'([\"\'])', r'\g<1>' + mapped + r'\2', text)
        text = re.sub(r'([\"\'])' + re.escape(name) + r'\.md([\"\'])', r'\g<1>' + mapped + r'.md\2', text)
        if '-' in name or name == 'pwf':
            text = re.sub(r'([\"\'])' + re.escape(name) + r'([\"\'])', r'\g<1>' + mapped + r'\2', text)
    # These are skill-identity comparisons, not plugin names or state keys.
    text = text.replace('CANONICAL = "planweft"', 'CANONICAL = "project-docs"')
    text = text.replace('skill_md.parent.name != "planweft"', 'skill_md.parent.name != "project-docs"')
    return text.replace('__PW_UPSTREAM_URL__', UPSTREAM_URL)


def enhance_skill(text, path):
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:
        raise ValueError('unsupported skill frontmatter: ' + path)
    front, body = text[4:].split('\n---\n', 1)
    language = re.search(r'/i18n/(project-docs-[^/]+)/', path)
    name = language.group(1) if language else SKILL
    front = re.sub(r'^name:.*$', 'name: ' + name, front, flags=re.M)
    description = re.search(r'^description:\s*(.*)$', front, re.M).group(1)
    if description.startswith('"'):
        description = json.loads(description)
    else:
        description = description.strip("'")
    description += ' Automatic matching adds project docs and evidence maintenance; read-only and plan mode do not write records.'
    front = re.sub(r'^description:.*$', lambda _: 'description: ' + json.dumps(description, ensure_ascii=False), front, flags=re.M)
    front = re.sub(r'^(\s+version:) .+$', r'\1 "' + VERSION + '"', front, flags=re.M)
    if language and 'disable-model-invocation:' not in front:
        front += '\ndisable-model-invocation: true'
    workflow = (OVERLAY / 'workflow.md').read_text()
    # Installed skills need their own sibling helper, irrespective of host.
    # Preserve all consent options while removing another host's assumed path.
    def portable_catchup(match):
        block = match.group(0)
        if 'session-catchup.py' not in block or '.claude' not in block:
            return block
        return ('Locate the absolute directory containing the installed `SKILL.md` you just read. '
                'Run its sibling `scripts/session-catchup.py --metadata <absolute-project-directory>` '
                'with an available Python 3 interpreter only when metadata was explicitly requested. '
                'Use `--replay` only when bounded transcript replay was explicitly authorized. '
                'Resolve that same installed helper on Windows; do not assume another host\'s installation path.\n')
    body = re.sub(r'```[^\n]*\n.*?```', portable_catchup, body, flags=re.S)
    return '---\n' + front + '\n---\n\n' + workflow.rstrip() + '\n\n' + body.lstrip()


def local_install_text(text, path):
    """Replace inherited release instructions with the derivative's local routes.

    Product renaming cannot imply that upstream publishes our GitHub/npm names.
    Keep provenance URLs while making instructions in installed Skills usable.
    """
    if path.endswith('/SKILL.md'):
        text = text.replace(
            '`/plugin marketplace add OthmanAdi/planweft` then `/plugin install`',
            '`/plugin marketplace add <absolute-claude-package-root>` then '
            '`/plugin install planweft@planweft`')
        text = text.replace(
            '`npx skills add OthmanAdi/planweft` (or ClawHub)',
            'Copy the complete packaged `skills/project-docs/` to '
            '`.claude/skills/project-docs/` (project) or `~/.claude/skills/project-docs/` (user)')
        text = text.replace(
            'Install it with `hermes plugins install '
            'OthmanAdi/planweft/.hermes/plugins/planweft`, then '
            '`hermes plugins enable planweft`. Full guide: docs/hermes.md in the repository.',
            'From the Hermes platform directory, copy the complete plugin root and '
            'its `skills/project-docs/` into `plugins/planweft/` and '
            '`skills/project-docs/` under the same `HERMES_HOME`. Then run '
            '`hermes plugins enable planweft` and restart Hermes. '
            'This derivative is installed from the local package.')
        text = text.replace(
            'add `"plugin": ["opencode-planweft"]` to `opencode.json`.',
            'copy the complete OpenCode platform directory into a local package and '
            'register its precompiled `dist/index.js` through a local loader; '
            'run `npm ci --omit=dev --ignore-scripts` for runtime dependencies in that local '
            'package directory. The shipped entry loads its compiled `dist/index.js`.')
        text = text.replace(
            '`npx skills add OthmanAdi/planweft --skill planweft -g` '
            'installs this skill to `~/.agents/skills/project-docs/`, one of the '
            'paths OpenCode reads natively. Full guide: docs/opencode.md.',
            'Copy the platform package complete `skills/project-docs/` directory to '
            'your project\'s `.opencode/skills/project-docs/`. For user scope, '
            'install the same packages/plugins/skills layout under '
            '`~/.config/opencode/`. Keep the local package\'s `node_modules/`. '
            'The unified npm package is planweft; use its version-matched installer after publication.')
        text = text.replace(
            '`~/.agents/skills/project-docs/templates/` after `npx skills add -g`',
            '`.opencode/skills/project-docs/templates/` after a project copy')
    if path == '.opencode/packages/opencode-planweft/README.md':
        text = text.replace('[planweft](' + UPSTREAM_URL + ')',
                            'PlanWeft, derived from [planning-with-files](' + UPSTREAM_URL + ')')
        text = re.sub(r'(?<=## Install\n).*?(?=\n## What the plugin does)',
                      lambda _: '\n' + (OVERLAY / 'install/opencode.md').read_text() + '\n',
                      text, flags=re.S)
        text = text.replace('`pwf.md` and `pwf-status.md`', '`pw-pwf.md` and `pw-pwf-status.md`')
        text = text.replace("from the repository's `.opencode/commands/`",
                            "from the OpenCode platform package's `commands/`")
        text = text.replace('Full guide: [docs/opencode.md]', 'Upstream implementation reference: [docs/opencode.md]')
    return text


def transform(upstream, enhanced=True):
    """Transform the complete tree, including tests for the migration regression."""
    result = {}
    for source, (raw, mode) in upstream.items():
        target = map_path(source)
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            result[target] = (raw, mode)
            continue
        if PurePosixPath(source).name != 'LICENSE':
            text = identity_text(text)
        if target.endswith('.md'):
            text = local_install_text(text, target)
        if enhanced and source.endswith('/SKILL.md'):
            text = enhance_skill(text, target)
        # Local, source-reviewed adapter patches. Keep event payloads and the
        # upstream state protocol; only remove implicit cwd imports/opt-out gaps.
        if '/hooks/' in '/' + target and target.endswith('.sh'):
            text = re.sub(r'(\$[A-Z_]*PYTHON[A-Z_]*"?)(\s+)(?=-c\b|-(?=\s|$))',
                          r'\1\2-I ', text)
        if target.startswith('.gemini/hooks/') and target.endswith('.sh') and 'PLANNING_DISABLED' not in text:
            first, rest = text.split('\n', 1)
            text = first + '\n[ "${PLANNING_DISABLED:-}" = "1" ] && { echo \'{}\'; exit 0; }\n' + rest
        if target == '.mastracode/hooks.json':
            payload = json.loads(text)
            for handlers in payload.values():
                for handler in handlers:
                    handler['command'] = '[ "${PLANNING_DISABLED:-}" = "1" ] && exit 0; ' + handler['command']
            text = json.dumps(payload, indent=2) + '\n'
        if target == '.gemini/settings.json':
            payload = json.loads(text)
            for groups in payload['hooks'].values():
                for group in groups:
                    for hook in group['hooks']:
                        command = hook['command']
                        if not re.fullmatch(r'\$GEMINI_PROJECT_DIR/\.gemini/hooks/[\w-]+\.sh', command):
                            raise ValueError('Gemini command changed; review its shell quoting')
                        # Upstream ships these scripts as 0664. Use their Bash
                        # interpreter explicitly instead of relying on +x.
                        hook['command'] = 'bash "' + command + '"'
            text = json.dumps(payload, indent=2) + '\n'
        if target.endswith('/scripts/plan-doctor.sh') or target == 'scripts/plan-doctor.sh':
            text = text.replace("echo '=== plan-doctor done ==='", (OVERLAY / 'doctor-overlap.sh').read_text() + "\necho '=== plan-doctor done ==='")
        if enhanced and '/templates/' in '/' + target:
            stem = PurePosixPath(target).stem
            if stem in ('analytics_task_plan', 'task_plan_autonomous'):
                stem = 'task_plan'
            if stem == 'analytics_findings':
                stem = 'findings'
            extra = OVERLAY / 'templates' / (stem + '.append.md')
            if extra.is_file():
                text = text.rstrip() + '\n\n' + extra.read_text().rstrip() + '\n'
        if source.endswith('/package.json') or source.endswith('/package-lock.json'):
            payload = json.loads(text)
            if source.endswith('/package.json'):
                payload['version'] = VERSION
                payload['description'] = DESCRIPTION
                if 'private' not in payload:
                    # These are local artifacts; do not advertise upstream as
                    # the publisher/support endpoint of a modified package.
                    for field in ['repository', 'homepage', 'bugs']:
                        payload.pop(field, None)
                payload['author'] = 'PlanWeft contributors; derived from Ahmad Adi / PWF'
            else:
                payload['version'] = VERSION
                root_package = payload.get('packages', {}).get('')
                if root_package is not None:
                    root_package['version'] = VERSION
            text = json.dumps(payload, indent=2) + '\n'
        if target.endswith('/plugin.json'):
            try:
                payload = json.loads(text)
                payload.update(name=PRODUCT, version=VERSION, description=DESCRIPTION)
                payload.pop('repository', None)
                payload['author'] = {'name': 'PlanWeft contributors'}
                text = json.dumps(payload, indent=2) + '\n'
            except json.JSONDecodeError:
                pass
        if target == '.hermes/plugins/planweft/plugin.yaml':
            text = re.sub(r'^version:.*$', 'version: ' + VERSION, text, flags=re.M)
        if target == '.claude-plugin/marketplace.json':
            payload = json.loads(text)
            payload['owner'] = {'name': 'PlanWeft contributors'}
            payload['description'] = DESCRIPTION
            for entry in payload['plugins']:
                entry.update(name=PRODUCT, version=VERSION, description=DESCRIPTION)
            text = json.dumps(payload, indent=2) + '\n'
        if target == '.hermes/plugins/planweft/__init__.py':
            text = text.replace('name="planweft",\n', 'name="project-docs",\n')
            text = text.replace('("pwf", "pwf-status", "plan-status")',
                                '("pw-pwf", "pw-pwf-status", "pw-plan-status")')
        if target == 'tests/test_hermes_first_class.py':
            # Upstream only releases numeric versions; our candidate is an exact
            # semver prerelease. Assert this release's value rather than accepting
            # arbitrary malformed versions or changing the original baseline.
            text = text.replace(r'r"(?m)^version: \d+\.\d+\.\d+$"',
                                'r"(?m)^version: ' + re.escape(VERSION) + '$"')
            text = text.replace('"planweft", ctx.skills', '"project-docs", ctx.skills')
            text = text.replace('ctx.skills["planweft"]', 'ctx.skills["project-docs"]')
            if enhanced:
                # Upstream test_hermes_first_class.py:763 assumed this bundle
                # lacked inject-plan.sh. Self-contained Skills now include it.
                # Prove the existing bundled fallback, then remove the bundle
                # from the fixture rather than weakening the no-script contract.
                missing_script_assertion = (
                    '            self.assertEqual({}, run("pre_llm_call"), '
                    '"no scripts found must stay a silent no-op")')
                if text.count(missing_script_assertion) != 1:
                    raise ValueError('Hermes no-script fixture changed; review the upstream test adaptation')
                isolated_bridge = (
                    '            self.assertIn("context", run("pre_llm_call"), '
                    '"an invalid explicit root still permits the bundled fallback")\n'
                    '            bundled_bridge = bridge\n'
                    '            bridge = root / "uninstalled" / "plugins" / "planweft" / "shell_hook.py"\n'
                    '            bridge.parent.mkdir(parents=True)\n'
                    '            shutil.copyfile(bundled_bridge, bridge)\n')
                text = text.replace(missing_script_assertion, isolated_bridge + missing_script_assertion)
        if target == 'tests/test_codex_plugin_operations.py':
            text = text.replace('["planweft"], sorted(path.name for path in skill_dirs)',
                                '["project-docs"], sorted(path.name for path in skill_dirs)')
        if target == 'CITATION.cff':
            text = re.sub(r'^version:.*$', 'version: ' + VERSION, text, flags=re.M)
        if target == '.opencode/packages/opencode-planweft/src/core.ts':
            text = re.sub(r'export const VERSION = "[^"]+"', 'export const VERSION = "' + VERSION + '"', text)
        if ('/commands/' in '/' + target or '/prompts/' in '/' + target) and target.endswith(('.md', '.prompt')):
            if text.startswith('---\n'):
                front, body = text[4:].split('\n---\n', 1)
                if target.endswith('.prompt'):
                    front = re.sub(r'^name:.*$', 'name: pw-plan', front, flags=re.M)
                if 'disable-model-invocation:' not in front:
                    front += '\ndisable-model-invocation: true'
                text = '---\n' + front + '\n---\n\n' + (
                    'Follow project-docs scope rules: read-only requests and host plan mode do not '
                    'initialize or update project files. Resolve the task-owned plan first; '
                    'never create a competing root plan.\n\n') + body.lstrip()
        result[target] = (text.encode('utf-8'), mode)
    if enhanced:
        data, mode = result['LICENSE']
        result['LICENSE'] = (data.replace(b'Permission is hereby granted', b'Copyright (c) 2026 PlanWeft contributors\n\nPermission is hereby granted', 1), mode)
        canonical = 'skills/project-docs/'
        for name in list(result):
            if name.endswith('/SKILL.md'):
                base = str(PurePosixPath(name).parent)
                result[base + '/references/evidence.md'] = ((OVERLAY / 'references/evidence.md').read_bytes(), 0o644)
                result[base + '/references/controls.md'] = ((OVERLAY / 'references/controls.md').read_bytes(), 0o644)
                # A standalone install copies the skill folder, not its repo.
                # Fill absent assets only; native/localized assets remain intact.
                for asset, value in list(result.items()):
                    if asset.startswith(canonical) and not asset.endswith('/SKILL.md'):
                        suffix = asset[len(canonical):]
                        if suffix.startswith(('scripts/', 'templates/')) or suffix in ('reference.md', 'examples.md'):
                            result.setdefault(base + '/' + suffix, value)
                result[base + '/LICENSE'] = result['LICENSE']
    return result


def subset(tree, prefixes):
    return {p: v for p, v in tree.items() if any(p == x or p.startswith(x.rstrip('/') + '/') for x in prefixes)}


def distributions(tree, upstream, compiled=True):
    common = ['scripts', 'templates', 'skills']
    result = {}
    result['codex'] = subset(tree, ['.codex/hooks', 'hooks/codex-hooks.json', *common])
    # Codex selects exactly one main root; native hooks come from its manifest,
    # never from Claude's skill frontmatter or a migrated command skill.
    key = 'skills/project-docs/SKILL.md'
    _, body = result['codex'][key][0].decode()[4:].split('\n---\n', 1)
    result['codex'][key] = (('---\nname: project-docs\ndescription: ' + json.dumps(DESCRIPTION) + '\nmetadata:\n  version: "' + VERSION + '"\n---\n' + body).encode(), 0o644)
    result['codex']['skills/project-docs/agents/openai.yaml'] = (b'interface:\n  display_name: "Project Docs"\n  short_description: "Persistent planning, project documents and evidence"\npolicy:\n  allow_implicit_invocation: true\n', 0o644)
    for path in list(result['codex']):
        if path.startswith('skills/i18n/') and path.endswith('/SKILL.md'):
            # Codex discovers nested language variants. Its native policy is
            # agents/openai.yaml, not Claude's disable-model-invocation flag.
            policy_path = str(PurePosixPath(path).parent / 'agents/openai.yaml')
            result['codex'][policy_path] = (b'policy:\n  allow_implicit_invocation: false\n', 0o644)
    codex_manifest = {'name': PRODUCT, 'version': VERSION, 'description': DESCRIPTION,
                      'skills': './skills/', 'hooks': './hooks/codex-hooks.json',
                      'author': {'name': 'PlanWeft contributors'},
                      'interface': {'displayName': 'PlanWeft', 'category': 'Productivity',
                                    'shortDescription': 'Persistent planning and project documentation',
                                    'longDescription': DESCRIPTION, 'developerName': 'PlanWeft contributors',
                                    'capabilities': ['Read', 'Write'],
                                    'defaultPrompt': ['Use $project-docs to continue this project.']}}
    result['codex']['.codex-plugin/plugin.json'] = (json.dumps(codex_manifest, indent=2).encode() + b'\n', 0o644)
    local_catalog = {'name': 'planweft-local', 'plugins': [{
        'name': PRODUCT, 'source': {'source': 'local', 'path': './'},
        'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
        'category': 'Productivity'}]}
    result['codex']['.agents/plugins/marketplace.json'] = (json.dumps(local_catalog, indent=2).encode() + b'\n', 0o644)
    result['claude'] = subset(tree, ['.claude-plugin', 'hooks/hooks.json', 'hooks/claude-hook.sh', 'commands', *common])
    pi_prefix = '.pi/skills/project-docs/'
    result['pi'] = {p[len(pi_prefix):]: v for p, v in tree.items() if p.startswith(pi_prefix)}
    result['opencode'] = subset(tree, ['.opencode', *common])
    # The source tree keeps its development entry; installation loads the locked
    # local build, so users can copy the adapter without hand-writing a loader.
    result['opencode']['.opencode/plugins/planweft.ts'] = (
        b'// Local package: run npm ci --ignore-scripts and npm run build in its directory.\n'
        b'export { PlanningWithFiles } from "../packages/opencode-planweft/dist/index.js"\n',
        0o644)
    for host in HOSTS:
        if host in result:
            continue
        prefix = '.github/hooks' if host == 'copilot' else '.' + host
        result[host] = subset(tree, [prefix, *common])
    provenance = json.dumps({'product': PRODUCT, 'version': VERSION, 'upstream': upstream,
                            'changes': ['product identity mapping', 'project-docs workflow and evidence',
                                        'self-contained platform packaging'],
                            'update_policy': 'Pinned source plus reviewed overlays; no runtime fetch.'}, indent=2).encode() + b'\n'
    for host, files in result.items():
        # Tests/build tooling remain in the reproducible source tree, not runtime packages.
        for name in list(files):
            if '__tests__' in PurePosixPath(name).parts or name.endswith('.test.ts'):
                del files[name]
            elif name.startswith('scripts/') and PurePosixPath(name).name in {
                    'bump-version.py', 'sync-ide-folders.py', '_v240_update_hook_bodies.py', 'build-clawhub-upload.py'}:
                del files[name]
        files['LICENSE'] = tree['LICENSE']
        files['UPSTREAM.json'] = (provenance, 0o644)
        for path in list(files):
            if path.endswith('/SKILL.md') or path == 'SKILL.md':
                base = str(PurePosixPath(path).parent)
                prefix = '' if base == '.' else base + '/'
                files[prefix + 'LICENSE'] = tree['LICENSE']
                files[prefix + 'UPSTREAM.json'] = (provenance, 0o644)
        if host == 'hermes':
            for name in ['LICENSE', 'UPSTREAM.json']:
                files['.hermes/plugins/planweft/' + name] = files[name]
        for suffix in ['', '.en']:
            notice = ('> Package: **' + host + '**. Use this host\'s installation section.'
                      if suffix else '> 当前安装包：**' + host + '**。请选择本文对应宿主的安装章节。')
            for name, source in [('README' + suffix + '.md', OVERLAY / ('README' + suffix + '.md')),
                                 ('INSTALL' + suffix + '.md', OVERLAY / 'install' / ('INSTALL' + suffix + '.md'))]:
                # Keep the source language switch first; do not prepend a
                # second title or link to documents outside the installed pack.
                text = source.read_text()
                if name.startswith('README'):
                    # Overlay sources are also readable in the repository;
                    # their install/ links become flat within installed packs.
                    text = text.replace('](install/INSTALL.md)', '](INSTALL.md)')
                    text = text.replace('](install/INSTALL.en.md)', '](INSTALL.en.md)')
                navigation, _, body = text.partition('\n')
                files[name] = ((navigation + '\n\n' + notice + '\n\n' + body.lstrip()).encode(), 0o644)
        # npm only packs files declared in its allowlist: make attribution ship too.
        if host == 'pi':
            payload = json.loads(files['package.json'][0])
            payload['files'] = list(dict.fromkeys([*payload.get('files', []), 'LICENSE', 'UPSTREAM.json',
                                                  'README.en.md', 'INSTALL.md', 'INSTALL.en.md', 'references/']))
            files['package.json'] = (json.dumps(payload, indent=2).encode() + b'\n', 0o644)
        if host == 'opencode':
            prefix = '.opencode/packages/opencode-planweft/'
            for name in ['LICENSE', 'UPSTREAM.json']:
                files[prefix + name] = files[name]
            payload = json.loads(files[prefix + 'package.json'][0])
            payload['files'] = list(dict.fromkeys([*payload.get('files', []), 'LICENSE', 'UPSTREAM.json']))
            files[prefix + 'package.json'] = (json.dumps(payload, indent=2).encode() + b'\n', 0o644)
        result[host] = files
    spec = importlib.util.spec_from_file_location('pw_native_adapters', OVERLAY / 'native/adapters.py')
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    result = native.adapt(result, VERSION, DESCRIPTION)
    if compiled:
        attach_opencode_compiled(result['opencode'])
    return result


def inventory(files):
    return {name: {'sha256': sha(data), 'executable': bool(mode & 0o111)}
            for name, (data, mode) in sorted(files.items())}


def public_installation_files():
    """Repository guides and installed guides share the same reviewed source."""
    result = {}
    for suffix in ['', '.en']:
        source = OVERLAY / 'install' / ('INSTALL' + suffix + '.md')
        text = source.read_text().replace('](INSTALL.md)', '](installation.md)')
        text = text.replace('](INSTALL.en.md)', '](installation.en.md)')
        navigation, _, body = text.partition('\n')
        context = ('Project overview: [中文](../README.md) / [English](../README.en.md) · '
                   'Cross-platform design: [中文](platforms.md) / [English](platforms.en.md)'
                   if suffix else '项目介绍：[中文](../README.md) / [English](../README.en.md) · '
                   '跨平台设计：[中文](platforms.md) / [English](platforms.en.md)')
        generated = '<!-- Generated from overlays/planweft/install/' + source.name + '; edit the source. -->'
        result['installation' + suffix + '.md'] = (
            (navigation + '\n\n' + context + '\n\n' + generated + '\n\n' + body.lstrip()).encode(), 0o644)
    return result


def tree_digest(files):
    return sha(json.dumps(inventory(files), sort_keys=True, separators=(',', ':')).encode())


def opencode_inputs(files):
    return {name: value for name, value in files.items()
            if name.startswith('src/') or name in {'package.json', 'package-lock.json', 'tsconfig.json'}}


def attach_opencode_compiled(files):
    """Keep ordinary builds offline, but refuse precompiled code from stale source."""
    root = OVERLAY / 'opencode-compiled'
    path = root / 'manifest.json'
    if not path.is_file():
        raise ValueError('OpenCode compiler output missing; run scripts/compile-opencode.py --install')
    manifest = json.loads(path.read_text())
    if manifest['source_sha256'] != tree_digest(opencode_inputs(files)):
        raise ValueError('OpenCode compiled source is stale; run scripts/compile-opencode.py --install')
    actual = {}
    for name, expected in manifest['files'].items():
        safe_name(name)
        source = root / name
        reject_symlinks(source)
        data = source.read_bytes()
        if sha(data) != expected['sha256']:
            raise ValueError('OpenCode compiled output digest mismatch: ' + name)
        actual[name] = (data, 0o755 if expected['executable'] else 0o644)
    extras = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()} - {'manifest.json'} - actual.keys()
    if extras:
        raise ValueError('Unexpected OpenCode compiler output: ' + ', '.join(sorted(extras)))
    if 'dist/index.js' not in actual:
        raise ValueError('OpenCode compiler output has no entrypoint')
    files.update(actual)
    files['BUILD.json'] = (path.read_bytes(), 0o644)


CATALOGS = {
    'codex': '.agents/plugins/marketplace.json',
    'claude': '.claude-plugin/marketplace.json',
    'cursor': '.cursor-plugin/marketplace.json',
    'copilot': '.github/plugin/marketplace.json',
    'factory': '.factory-plugin/marketplace.json',
    'codebuddy': '.codebuddy-plugin/marketplace.json',
}


def marketplace_files():
    """Each host discovers its own catalog; only our entry is builder-owned."""
    result = {}
    for host, name in CATALOGS.items():
        entry = {'name': PRODUCT, 'source': './dist/' + host + '/' + PRODUCT,
                 'description': DESCRIPTION, 'version': VERSION}
        if host == 'codex':
            entry = {'name': PRODUCT, 'source': {'source': 'local', 'path': entry['source']},
                     'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
                     'category': 'Productivity'}
            payload = {'name': PRODUCT, 'interface': {'displayName': 'PlanWeft'}, 'plugins': [entry]}
        else:
            payload = {'name': PRODUCT, 'owner': {'name': 'PlanWeft contributors'}, 'plugins': [entry]}
        path = ROOT / name
        reject_symlinks(path)
        if path.is_file():
            old = json.loads(path.read_text())
            if not isinstance(old.get('plugins'), list):
                raise ValueError('Invalid existing marketplace: ' + name)
            legacy = [item for item in old['plugins'] if item.get('name') == 'program-design']
            if legacy:
                ownership = json.loads((OVERLAY / 'legacy-0.3.json').read_text())
                if sha(path.read_bytes()) != ownership['catalogs'].get(name):
                    raise ValueError('Modified legacy marketplace preserved: ' + name)
                old['plugins'] = [item for item in old['plugins'] if item.get('name') != 'program-design']
            matches = [i for i, item in enumerate(old['plugins']) if item.get('name') == PRODUCT]
            if len(matches) > 1:
                raise ValueError('Duplicate planweft marketplace entries: ' + name)
            entries = old['plugins'][:]
            if matches:
                entries[matches[0]] = entry
            else:
                entries.append(entry)
            # Preserve unrelated metadata and plugin order, while migrating the
            # product catalog identity explicitly approved for this release.
            payload = {**old, **{key: value for key, value in payload.items() if key != 'plugins'}, 'plugins': entries}
            if host == 'codex':
                payload['interface'] = {**old.get('interface', {}), **payload['interface']}
        result[name] = (json.dumps(payload, indent=2, ensure_ascii=False).encode() + b'\n', 0o644)
    return result


def safe_name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or not path.parts:
        raise ValueError('Unsafe generated path: ' + name)


def reject_symlinks(path):
    for candidate in [path, *path.parents]:
        if candidate.is_symlink():
            raise ValueError('Refusing symlink in generated path: ' + str(candidate))


def write_tree(files, destination, verify=False):
    reject_symlinks(destination)
    for path in destination.rglob('*') if destination.exists() else []:
        if path.is_symlink():
            raise ValueError('Refusing symlink in generated tree: ' + str(path))
    existing = {str(p.relative_to(destination)): p for p in destination.rglob('*') if p.is_file()} if destination.exists() else {}
    differences = [p for p in existing if p not in files]
    differences.extend(write_files(files, destination, verify))
    if not verify:
        for name in existing.keys() - files.keys():
            existing[name].unlink()
        for path in sorted(destination.rglob('*'), reverse=True):
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
    return sorted(differences)


def write_files(files, destination, verify=False):
    """Write only named files; root catalogs must never prune the repository."""
    differences = []
    for name, (data, mode) in files.items():
        safe_name(name)
        path = destination / name
        reject_symlinks(path)
        if not path.is_file() or path.read_bytes() != data or bool(path.stat().st_mode & 0o111) != bool(mode & 0o111):
            differences.append(name)
            if not verify:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                path.chmod(mode)
    return sorted(differences)


def read_tree(directory):
    reject_symlinks(directory)
    result = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ValueError('Refusing symlink in source tree: ' + str(path))
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = (path.read_bytes(), path.stat().st_mode & 0o777)
    return result


def retired_archives():
    """Only an old manifest and matching bytes establish ownership of a ZIP."""
    path = ROOT / 'dist/manifest.json'
    if not path.is_file():
        return []
    old = json.loads(path.read_text())
    if old.get('product') != PRODUCT or old.get('schema_version', 1) != 1:
        return []
    version = old.get('version', '')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version):
        raise ValueError('Unrecognized legacy distribution version')
    result = []
    for host, item in old.get('platforms', {}).items():
        if host not in HOSTS or item.get('archive') != f'{PRODUCT}-{version}-{host}.zip':
            raise ValueError('Unrecognized legacy archive ownership')
        candidate = ROOT / 'dist' / item['archive']
        reject_symlinks(candidate)
        if candidate.exists():
            if sha(candidate.read_bytes()) != item.get('sha256'):
                raise ValueError('Modified legacy archive preserved: ' + candidate.name)
            result.append(candidate)
    return result



def legacy_directories():
    """Refuse to retire any 0.3 directory not matching its reviewed content hash."""
    record = json.loads((OVERLAY / 'legacy-0.3.json').read_text())
    candidates = [(ROOT / 'dist' / host / 'program-design', digest)
                  for host, digest in record['platforms'].items()]
    candidates.append((ROOT / 'plugins/program-design', record['platforms']['codex']))
    result = []
    for path, digest in candidates:
        reject_symlinks(path)
        if path.exists():
            if tree_digest(read_tree(path)) != digest:
                raise ValueError('Modified legacy directory preserved: ' + str(path))
            result.append(path)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Compare generated artifacts without changing them')
    parser.add_argument('--tree', type=Path, help='Write full transformed tree (including upstream tests) to a NEW directory')
    parser.add_argument('--identity-only', action='store_true', help='With --tree, omit workflow/template overlays')
    args = parser.parse_args()
    if args.identity_only and not args.tree:
        parser.error('--identity-only requires --tree')
    original, upstream = read_upstream()
    tree = transform(original, enhanced=not args.identity_only)
    if args.tree:
        if args.verify:
            parser.error('--tree cannot be combined with --verify')
        if args.tree.exists():
            parser.error('--tree destination must not exist')
        write_tree(tree, args.tree)
        print(json.dumps({'tree_files': len(tree), 'identity_only': args.identity_only}))
        return
    bundles = distributions(tree, upstream)
    retired = retired_archives()
    old_directories = legacy_directories()
    index = {'schema_version': 2, 'product': PRODUCT, 'version': VERSION,
             'upstream_commit': upstream['commit'], 'platforms': {}}
    catalogs = marketplace_files()
    differences = {'retired-directories': [str(p.relative_to(ROOT)) for p in old_directories]}
    for host, files in bundles.items():
        relative = host + '/' + PRODUCT
        index['platforms'][host] = {'path': relative, 'sha256': tree_digest(files),
                                   'file_count': len(files), 'files': inventory(files)}
        differences[host] = write_tree(files, ROOT / 'dist' / relative, args.verify)
    differences['codex-mirror'] = write_tree(bundles['codex'], ROOT / 'plugins/planweft', args.verify)
    manifest = {'manifest.json': (json.dumps(index, indent=2, sort_keys=True).encode() + b'\n', 0o644)}
    differences['manifest'] = write_files(manifest, ROOT / 'dist', args.verify)
    differences['marketplaces'] = write_files(catalogs, ROOT, args.verify)
    differences['public-docs'] = write_files(public_installation_files(), ROOT / 'docs', args.verify)
    # Only retire our previous named platform distributions, never vendor or
    # evidence archives, nor unrelated files placed next to generated outputs.
    differences['retired-archives'] = []
    for path in retired:
        differences['retired-archives'].append(path.name)
        if not args.verify:
            path.unlink()
    if not args.verify:
        for path in old_directories:
            shutil.rmtree(path)
    print(json.dumps({'platforms': len(bundles), 'differences': {k: len(v) for k, v in differences.items()},
                      'verified': args.verify and not any(differences.values())}, indent=2))
    if args.verify and any(differences.values()):
        for group, paths in differences.items():
            for path in paths[:30]:
                print(group + ': ' + path)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
