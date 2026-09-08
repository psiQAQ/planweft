"""Native package layouts, applied after the reviewed upstream transformation.

The builder owns distribution locations. This module only maps files inside each
package and never touches the filesystem outside this overlay directory.
"""
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
PRODUCT = 'planweft'
SKILL = 'project-docs'


def json_file(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode(), 0o644


def subset(files, prefixes):
    return {p: v for p, v in files.items()
            if any(p == x or p.startswith(x.rstrip('/') + '/') for x in prefixes)}


def flatten(files, prefix):
    return {p[len(prefix):]: v for p, v in files.items() if p.startswith(prefix)}


def metadata(version, description):
    return {'name': PRODUCT, 'version': version, 'description': description,
            'author': {'name': 'PlanWeft contributors'}, 'license': 'MIT'}


def portable_skills(files, version):
    """One native discovery root, without another host's executable frontmatter.

    Complete language resources travel with a standalone main Skill copy.
    GUIDE.md avoids rediscovery by hosts that recursively scan for SKILL.md;
    Claude and Codex keep their own language discovery policies and layouts.
    """
    result = {}
    for name, value in files.items():
        is_variant = name.startswith('skills/i18n/')
        target = (name.replace('skills/i18n/',
                               'skills/project-docs/references/language-variants/', 1)
                  if is_variant else name)
        if is_variant and target.endswith('/SKILL.md'):
            target = target.removesuffix('SKILL.md') + 'GUIDE.md'
        data, mode = value
        if name.endswith('/SKILL.md'):
            text = data.decode('utf-8')
            front, body = text[4:].split('\n---\n', 1)
            skill_name = re.search(r'^name:\s*(.+)$', front, re.M).group(1)
            description = re.search(r'^description:\s*(.+)$', front, re.M).group(1)
            header = '---\nname: ' + skill_name + '\ndescription: ' + description
            header += '\nmetadata:\n  version: "' + version + '"'
            if skill_name == SKILL:
                body = ('\nFor an explicitly requested language variant, read its instructions from '
                        '`references/language-variants/project-docs-<language>/GUIDE.md` relative to this '
                        'Skill directory (ar, de, es, zh, zht). These are supporting resources of '
                        'this single entry point. Resolve runtime assets from the installed Skill; '
                        'keep task records in the user project.\n' + body)
            data = (header + '\n---\n' + body).encode()
        result[target] = (data, mode)
    return result


def shared(files, version):
    return portable_skills(subset(files, ['skills', 'scripts', 'templates',
                                         'README.md', 'README.en.md', 'INSTALL.md', 'INSTALL.en.md',
                                         'LICENSE', 'UPSTREAM.json']), version)


def add_bridge(files):
    files['hooks/native-hook.py'] = ((HERE / 'native-hook.py').read_bytes(), 0o644)
    # The upstream "validate" mode returns before checking the attestation.
    # Native continuation needs an acceptance result after those checks, while
    # keeping upstream resolution and tamper handling as the one implementation.
    marker = '        progress = None\n        ledger_dir = None\n'
    acceptance = ('        if context == "native-gate":\n'
                  '            self.echo("PWF_NATIVE_GATE_ACCEPTED_V1")\n'
                  '            raise Bail()\n\n')
    for name, (data, mode) in list(files.items()):
        if name.endswith('/inject-plan.py'):
            text = data.decode()
            if text.count(marker) != 1:
                raise ValueError('native gate insertion point changed: ' + name)
            files[name] = (text.replace(marker, acceptance + marker).encode(), mode)


def cursor(files, version, description):
    result = shared(files, version)
    manifest = metadata(version, description)
    manifest.update(skills='./skills/', hooks='./hooks/hooks.json')
    result['.cursor-plugin/plugin.json'] = json_file(manifest)
    add_bridge(result)
    # beforeSubmitPrompt and preToolUse cannot inject model context. Use the
    # documented sessionStart/postToolUse response fields instead.
    hooks = {}
    for event in ['sessionStart', 'postToolUse', 'stop']:
        hook = {'command': 'python3 -I -B "${CURSOR_PLUGIN_ROOT}/hooks/native-hook.py" cursor ' + event,
                'timeout': 10}
        if event == 'stop':
            hook['loop_limit'] = 3
        hooks[event] = [hook]
    result['hooks/hooks.json'] = json_file({'version': 1, 'hooks': hooks})
    return result


def copilot(files, version, description):
    result = shared(files, version)
    manifest = metadata(version, description)
    manifest.update(skills='./skills/', hooks='./hooks.json')
    result['plugin.json'] = json_file(manifest)
    add_bridge(result)
    hooks = {}
    # Native command-hook userPromptSubmitted output is ignored. preToolUse
    # permission decisions are deliberately absent from this advisory plugin.
    for event in ['sessionStart', 'postToolUse', 'agentStop']:
        script = '"${PLUGIN_ROOT}/hooks/native-hook.py" copilot ' + event
        hooks[event] = [{'type': 'command', 'bash': 'python3 -I -B ' + script,
                         'powershell': 'python -I -B ' + script, 'timeoutSec': 10}]
    result['hooks.json'] = json_file({'version': 1, 'hooks': hooks})
    return result


def gemini(files, version, description):
    result = shared(files, version)
    result['gemini-extension.json'] = json_file({'name': PRODUCT, 'version': version,
                                                'description': description})
    add_bridge(result)
    hooks = {}
    for event in ['SessionStart', 'BeforeAgent', 'AfterTool', 'PreCompress']:
        hook = {'name': 'planweft-' + event.lower(), 'type': 'command',
                'command': 'python3 -I -B "${extensionPath}/hooks/native-hook.py" gemini ' + event,
                'timeout': 10000}
        hooks[event] = [{'hooks': [hook]}]
    result['hooks/hooks.json'] = json_file({'hooks': hooks})
    # Commands are Gemini TOML prompts, not renamed Claude Markdown commands.
    for name, action in [('pw-plan', 'Continue the authorized implementation using the installed project-docs skill.'),
                         ('pw-plan-status', 'Read the selected project plan and report its status without modifying files.')]:
        prompt = action + ' Resolve scripts and templates from the installed skill directory; keep task records in the project.'
        result['commands/' + name + '.toml'] = (
            ('description = ' + json.dumps(action) + '\nprompt = ' + json.dumps(prompt) + '\n').encode(), 0o644)
    return result


def hermes(files, version):
    result = shared(files, version)
    result.update(flatten(files, '.hermes/plugins/planweft/'))
    # The plugin's registered skill and runtime assets must resolve inside this
    # installation even when another host has a same-named skill installed.
    data, mode = result['paths.py']
    text = data.decode()
    start = text.index('def plugin_skill_dir()')
    end = text.index('\n\ndef normalize_cwd', start)
    text = text[:start] + '''def plugin_skill_dir() -> Path | None:
    """Only explicitly selected or bundled assets belong to this plugin."""
    explicit = resolve_explicit_skill_dir()
    if explicit is not None:
        return explicit
    bundled = PLUGIN_DIR / "skills" / SKILL_DIR_NAME
    return bundled if has_skill_assets(bundled) else None


def find_skill_dir(start: Path) -> Path:
    return plugin_skill_dir() or (PLUGIN_DIR / "skills" / SKILL_DIR_NAME)
''' + text[end:]
    start = text.index('def resolve_skill_dir(') if 'def resolve_skill_dir(' in text else -1
    if start >= 0:
        end = text.index('\n\nSKILL_ROOT', start)
        text = text[:start] + '''def resolve_skill_dir(project_dir: Path) -> Path:
    return plugin_skill_dir() or (PLUGIN_DIR / "skills" / SKILL_DIR_NAME)
''' + text[end:]
    result['paths.py'] = (text.encode(), mode)
    data, mode = result['shell_hook.py']
    text = data.decode()
    start = text.index('def _candidate_script_dirs()')
    end = text.index('\n\ndef _find_script', start)
    text = text[:start] + '''def _candidate_script_dirs() -> list[Path]:
    dirs: list[Path] = []
    explicit = os.environ.get("PLANNING_WITH_FILES_SKILL_ROOT", "").strip()
    if explicit:
        dirs.append(Path(explicit).expanduser() / "scripts")
    dirs.append(Path(__file__).resolve().parent / "skills" / "project-docs" / "scripts")
    return dirs
''' + text[end:]
    result['shell_hook.py'] = (text.encode(), mode)
    data, mode = result['plugin.yaml']
    result['plugin.yaml'] = (re.sub(r'^version:.*$', 'version: ' + version, data.decode(), flags=re.M).encode(), mode)
    return result


def opencode(files, version, description):
    result = shared(files, version)
    result.update({p: value for p, value in flatten(files, '.opencode/packages/opencode-planweft/').items()
                   if p != 'README.md'})
    result.update({'commands/' + p: v for p, v in flatten(files, '.opencode/commands/').items()})
    payload = json.loads(result['package.json'][0])
    payload.update(version=version, description=description)
    payload['files'] = ['dist/', 'skills/', 'commands/',
                        'README.md', 'README.en.md', 'INSTALL.md', 'INSTALL.en.md',
                        'BUILD.json', 'LICENSE', 'UPSTREAM.json']
    # Release compilation belongs to the builder. Consumers of the generated
    # npm package use the verified dist files without running lifecycle builds.
    payload['scripts'].pop('prepublishOnly', None)
    result['package.json'] = json_file(payload)
    lock = json.loads(result['package-lock.json'][0])
    lock['version'] = version
    lock.get('packages', {}).get('', {})['version'] = version
    result['package-lock.json'] = json_file(lock)
    data, mode = result['src/core.ts']
    text = data.decode().replace('import * as path from "node:path"',
                                 'import * as path from "node:path"\nimport { fileURLToPath } from "node:url"')
    text = re.sub(r'export const VERSION = "[^"]+"', 'export const VERSION = "' + version + '"', text)
    start = text.index('export function findSkillDir(')
    end = text.index('\n}\n', start) + 3
    text = text[:start] + '''export function findSkillDir(_root: string, env: Env): string | null {
  const explicit = (env.PLANNING_WITH_FILES_SKILL_ROOT ?? "").trim()
  const bundled = fileURLToPath(new URL("../skills/project-docs/", import.meta.url))
  const candidate = explicit || bundled
  return isRegularFile(path.join(candidate, "templates", "task_plan.md")) ? candidate : null
}
''' + text[end:]
    result['src/core.ts'] = (text.encode(), mode)
    result['install/loader-template.ts'] = (
        b'// Replace this file URL with the absolute path to the built package.\n'
        b'export { PlanningWithFiles } from "file:///ABSOLUTE/PATH/TO/planweft/dist/index.js"\n', 0o644)
    return result


def adapt(bundles, version, description):
    result = {host: dict(files) for host, files in bundles.items()}
    # Claude is already a complete native package. Its standalone catalog is
    # retained; the repository catalog (owned by the builder) points to it.
    claude = result['claude']
    manifest = json.loads(claude['.claude-plugin/plugin.json'][0])
    manifest.update(version=version, description=description)
    claude['.claude-plugin/plugin.json'] = json_file(manifest)
    catalog = json.loads(claude['.claude-plugin/marketplace.json'][0])
    for entry in catalog['plugins']:
        entry.pop('version', None)  # plugin.json is the one release version.
    claude['.claude-plugin/marketplace.json'] = json_file(catalog)
    # Use the documented command string form rather than relying on a host
    # interpreting Claude's upstream experimental separate args property.
    config = json.loads(claude['hooks/hooks.json'][0])
    for groups in config['hooks'].values():
        for group in groups:
            for hook in group['hooks']:
                args = hook.pop('args', [])
                if args:
                    hook['command'] += ' ' + ' '.join('"' + value + '"' for value in args)
    claude['hooks/hooks.json'] = json_file(config)
    result['cursor'] = cursor(result['cursor'], version, description)
    result['copilot'] = copilot(result['copilot'], version, description)
    result['gemini'] = gemini(result['gemini'], version, description)
    result['hermes'] = hermes(result['hermes'], version)
    result['opencode'] = opencode(result['opencode'], version, description)
    for host in ['factory', 'codebuddy']:
        files = shared(result[host], version)
        manifest = metadata(version, description)
        manifest['skills'] = './skills/'
        files['.' + host + '-plugin/plugin.json'] = json_file(manifest)
        result[host] = files
    kiro = result['kiro']
    result['kiro'] = shared(kiro, version)
    # Preserve Kiro's bootstrap/steering assets and its no-continuation Skill
    # contract while exposing them through the current Power package root.
    kiro_skills = {'skills/' + name: value
                   for name, value in flatten(kiro, '.kiro/skills/').items()}
    result['kiro'].update(portable_skills(kiro_skills, version))
    data, mode = result['kiro']['skills/project-docs/SKILL.md']
    text = data.decode()
    # Power caches are not project .kiro/skills directories. Shell variables
    # deliberately name the loaded Skill while cwd stays the user's project.
    intro = 'From the **workspace root**:'
    if text.count(intro) != 1:
        raise ValueError('Kiro bootstrap instruction anchor changed')
    text = text.replace(intro,
        'Keep the current working directory at the **target workspace root**. '
        'Set the variable below to the absolute directory containing this loaded '
        'SKILL.md (inside the installed Power, or a standalone Skill copy). '
        'Use that same variable for the later helper commands; do not change '
        'into the Power cache to run them. Project records remain under .kiro/plan '
        'and .kiro/steering in the target workspace.')
    prefix = '.kiro/skills/project-docs/assets/scripts/'
    for filename in ('bootstrap.sh', 'session-catchup.py', 'check-complete.sh'):
        text = text.replace(prefix + filename, '"$PD_KIRO_SKILL_ROOT/assets/scripts/' + filename + '"')
    # The Python helper has one command example in each shell.
    text = text.replace('python "$PD_KIRO_SKILL_ROOT/assets/scripts/session-catchup.py"',
                        'python "$PdKiroSkillRoot/assets/scripts/session-catchup.py"')
    for filename in ('bootstrap.ps1', 'check-complete.ps1'):
        text = text.replace(prefix + filename, '"$PdKiroSkillRoot/assets/scripts/' + filename + '"')
    text = text.replace('sh "$PD_KIRO_SKILL_ROOT/assets/scripts/bootstrap.sh"',
        'PD_KIRO_SKILL_ROOT="/absolute/path/to/installed/skills/project-docs"\n'
        'sh "$PD_KIRO_SKILL_ROOT/assets/scripts/bootstrap.sh"')
    text = text.replace('pwsh -ExecutionPolicy RemoteSigned -File "$PdKiroSkillRoot/assets/scripts/bootstrap.ps1"',
        '$PdKiroSkillRoot = "C:/absolute/path/to/installed/skills/project-docs"\n'
        'pwsh -ExecutionPolicy RemoteSigned -File "$PdKiroSkillRoot/assets/scripts/bootstrap.ps1"')
    result['kiro']['skills/project-docs/SKILL.md'] = (text.encode(), mode)
    manifest = metadata(version, description)
    manifest['$schema'] = 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'
    manifest['keywords'] = ['planning', 'project documentation', 'requirements', 'decisions', 'evidence', 'handoff']
    result['kiro']['plugin.json'] = json_file(manifest)
    return result
