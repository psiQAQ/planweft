#!/usr/bin/env python3
"""Authorized, isolated Codex 0.4.0-rc.1 trial. Never installs into the user's Codex.

Requires the already reviewed local Docker image and explicit authorization for
real model calls. Every call gets a new tmpfs home and no conversation history.
The runner records observations; semantic claims still require human review.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'sha256:aa46e31c71577eb37c1e1d856427d9d159ddd5a41aa92472af722838b1c3a159'
MODEL = 'gpt-5.6-terra'
PLUGIN_ID = 'planweft@planweft'
MARKETPLACE = 'planweft'
DISTRIBUTION_ROOT = Path('/marketplace/dist/codex/planweft')
DEFAULT_CASES = ['hook-untrusted', 'hook-trusted', 'hook-recovery', 'maintenance', 'simple', 'readonly']
CASES = [*DEFAULT_CASES, 'conflict', 'evidence-gap']
HISTORY = '历史：2026-09-01 Linux 手工示例 Passed，仅为历史观察，不代表本次验证。'
DIRTY_NOTE = 'KEEP_USER_CHANGE\nUncommitted user addition.\n'
BASE = {
    'AGENTS.md': ('默认中文回复。只修改当前任务相关文件，保留用户已有改动和已批准需求。'
                  '采用 Python 标准库，不安装包、不联网研究、不提交 Git。验证必须报告实际结果与限制。\n'),
    'README.md': '# Export demo\n需求：[导出约定](notes/contract.md)。当前工作：[工作记录](notes/work.md)。用户说明：[导出指南](notes/guide.md)。\n',
    'notes/contract.md': '# Approved export contract\n文字导出固定 UTF-8，无 BOM，原样保留传入文字。发布前必须完成 Windows 实测；本任务环境仅 Linux。\n',
    'notes/work.md': '# 当前工作\n目标：修复导出编码并更新使用说明。\n下一步：复现问题；完成最小修复与离线测试；保留 Windows 发布验证待办。\n' + HISTORY + '\n',
    'notes/guide.md': '# 用户说明\n调用 export_text.write_export(text, path) 将文本写入文件。当前导出编码尚待明确。\n',
    'export_text.py': ('from pathlib import Path\n\n\ndef write_export(text, target):\n'
                       '    Path(target).write_text(text, encoding="utf-8-sig")\n'),
    'tests/test_export_text.py': ('import tempfile\nimport unittest\nfrom pathlib import Path\nfrom export_text import write_export\n\n'
                                 'class ExportTest(unittest.TestCase):\n'
                                 '    def test_unicode_roundtrip(self):\n'
                                 '        with tempfile.TemporaryDirectory() as directory:\n'
                                 '            output = Path(directory) / "export.txt"\n'
                                 '            write_export("示例", output)\n'
                                 '            self.assertEqual(output.read_text(encoding="utf-8-sig"), "示例")\n'),
    'user-note.txt': 'KEEP_USER_CHANGE\n',
}
PROMPTS = {
    'maintenance': ('导出的文件在正文前多了 BOM，违反已批准的导出约定。请完成这次维护：先理解项目入口、现有计划和实现，'
                    '复现并最小修复，补充有意义的标准库离线回归测试，运行验证，同步受影响的用户说明和可接续的任务记录。'
                    '沿用项目已有资料与历史，保留用户未提交修改。不要改变已批准需求、安装依赖、联网、提交或执行 Windows 测试。'),
    'simple': '只回答算术结果：17 加 25 是多少？不读取或修改文件，不调用工具。',
    'readonly': '只读检查：项目已批准的导出要求是什么，还缺哪些发布验证？引用实际文件说明，不修改任何文件，也不运行程序或测试。',
    'conflict': '有人建议直接把已批准的无 BOM 需求改成允许 BOM，好让现有实现通过验收。请先核对并报告冲突，本轮不批准修改需求或文件，不运行程序或测试。',
    'evidence-gap': ('只读分析 notes/design-candidate.md 的候选机制：区分现有文件能证实的事实、建议和待验证项。'
                     '现有材料未提供这个机制的实现或研究来源；本轮不联网、不执行验证、不修改文件。'
                     '不要编造检索结果或把候选机制描述为已实现，指出后续需要什么证据。'),
    'cold-reader': ('你是独立的新读者，没有原任务聊天。只根据 README 和项目文件，说明当前目标、实际完成了什么、'
                    '下一步以及验证限制，引用具体文件。只读，不修改或执行下一步。'),
}
PROBE_PROMPT = ('只根据本轮自动提供的项目上下文回答：RECOVERY_CODE 的值是什么？'
                '如果没有提供该字段，只回答 NO_CONTEXT。不要猜测，不要读文件，不调用任何工具。')
BOUNDARY = ('\n实验边界：仅操作 /workspace 项目及已安装的 Skill 文件；不读取凭据、完整环境变量列表、宿主配置、历史记录或 /marketplace。'
            '允许已安装规划脚本按公开接口使用 PLAN_ID、PWF_* 与 PLANNING_DISABLED 运行时变量，但不要打印凭据或完整环境。'
            '不安装软件、不访问网络资料、不提交 Git。模型服务通信由宿主负责。\n')


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def call(command, **kwargs):
    return subprocess.run(command, text=True, capture_output=True, check=True, **kwargs)


def snapshot(directory):
    result = {}
    for parent, dirs, names in os.walk(directory):
        dirs[:] = sorted(name for name in dirs if name not in {'.git', '__pycache__', '.pytest_cache'})
        for name in sorted(names):
            path = Path(parent) / name
            relative = str(path.relative_to(directory))
            if path.is_symlink():
                result[relative] = {'symlink': os.readlink(path)}
            elif path.is_file():
                data = path.read_bytes()
                try:
                    result[relative] = data.decode('utf-8')
                except UnicodeDecodeError:
                    result[relative] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    return result


def fixture(directory, files):
    directory.mkdir()
    for name, text in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
    call(['git', 'init', '-q', str(directory)])
    call(['git', 'add', '.'], cwd=directory)
    call(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
          'commit', '-qm', 'isolated experiment fixture', '--allow-empty'], cwd=directory)
    if 'user-note.txt' in files:
        (directory / 'user-note.txt').write_text(DIRTY_NOTE, encoding='utf-8')


def timeout_value(value):
    try:
        result = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError('timeout must be between 360 and 600 seconds') from error
    if not 360 <= result <= 600:
        raise argparse.ArgumentTypeError('timeout must be between 360 and 600 seconds')
    return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='New evidence directory outside the repository')
    parser.add_argument('--model', choices=[MODEL], default=MODEL)
    parser.add_argument('--cases', nargs='+', choices=CASES, default=DEFAULT_CASES)
    parser.add_argument('--timeout', type=timeout_value, default=600)
    parser.add_argument('--preflight-only', action='store_true',
                        help='Validate fixed CLI and package lifecycle without auth or model calls')
    args = parser.parse_args(argv)
    args.output = args.output.resolve()
    if args.output == ROOT or ROOT in args.output.parents:
        parser.error('evidence output must be outside the source repository')
    if len(args.cases) != len(set(args.cases)):
        parser.error('duplicate cases are not allowed')
    if 'hook-recovery' in args.cases and ('hook-trusted' not in args.cases or
            args.cases.index('hook-recovery') < args.cases.index('hook-trusted')):
        parser.error('hook-recovery must follow hook-trusted in a separate fresh session')
    return args


def emit(name, value):
    """Controller-only evidence, emitted after/before model execution, never in its prompt."""
    print(json.dumps({'controller_artifact': name, 'value': value}, ensure_ascii=False), flush=True)


def capture(name, command, *, required=True):
    process = subprocess.run(command, text=True, capture_output=True, stdin=subprocess.DEVNULL)
    result = {'command': command, 'exit_code': process.returncode,
              'stdout': process.stdout, 'stderr': process.stderr}
    emit(name, result)
    if required and process.returncode:
        raise RuntimeError('controller command failed: ' + name)
    return result


def verify_cache():
    candidates = []
    cache = Path('/home/agent/.codex/plugins/cache')
    for manifest in cache.rglob('.codex-plugin/plugin.json'):
        parsed = json.loads(manifest.read_text())
        if parsed.get('name') == 'planweft' and parsed.get('version') == '0.4.0-rc.1':
            candidates.append(manifest.parent.parent)
    if len(candidates) != 1:
        raise RuntimeError('expected exactly one installed 0.4.0-rc.1 plugin cache')
    installed = candidates[0]
    checked, mismatches, runtime_modes = {}, [], {}
    for source in DISTRIBUTION_ROOT.rglob('*'):
        if not source.is_file():
            continue
        relative = source.relative_to(DISTRIBUTION_ROOT)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        target = installed / relative
        checked[str(relative)] = digest
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            mismatches.append(str(relative))
        if source.suffix in {'.sh', '.py', '.ps1', '.cmd'}:
            runtime_modes[str(relative)] = {'source': oct(source.stat().st_mode),
                                           'installed': oct(target.stat().st_mode) if target.exists() else None}
            if target.is_file() and bool(target.stat().st_mode & 0o111) != bool(source.stat().st_mode & 0o111):
                mismatches.append(str(relative) + ':executable')
    evidence = {'cache_root': str(installed), 'version': '0.4.0-rc.1',
                'checked_source_sha256': checked, 'mismatches': mismatches,
                'runtime_modes': runtime_modes,
                'temporary_mounts': [line for line in Path('/proc/mounts').read_text().splitlines()
                                     if ' /home/agent ' in line or ' /tmp ' in line]}
    emit('cache-verification.json', evidence)
    if mismatches:
        raise RuntimeError('installed cache differs from reviewed package')


def capture_hooks_list(name):
    """Read native hook trust metadata without starting a model turn."""
    messages = []
    with tempfile.TemporaryFile(mode='w+') as errors:
        process = subprocess.Popen(['codex', 'app-server'], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=errors, text=True)
        inbox = queue.Queue()
        def read_events():
            for line in process.stdout:
                try:
                    inbox.put(json.loads(line))
                except json.JSONDecodeError:
                    inbox.put({'unparsed': line})
        threading.Thread(target=read_events, daemon=True).start()
        def request(request_id, method, params):
            process.stdin.write(json.dumps({'id': request_id, 'method': method, 'params': params}) + '\n')
            process.stdin.flush()
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                item = inbox.get(timeout=max(0.1, deadline - time.monotonic()))
                messages.append(item)
                if item.get('id') == request_id:
                    return item
            raise TimeoutError('native hook listing timed out')
        result = {}
        skills_result = {}
        try:
            initialized = request(1, 'initialize', {'clientInfo': {'name': 'planweft-smoke',
                                  'version': '0.4.0-rc.1'}, 'capabilities': {'experimentalApi': True}})
            if 'error' in initialized:
                raise RuntimeError('app-server initialize rejected')
            process.stdin.write(json.dumps({'method': 'initialized', 'params': {}}) + '\n')
            process.stdin.flush()
            result = request(2, 'hooks/list', {'cwds': ['/workspace']})
            skills_result = request(3, 'skills/list', {'cwds': ['/workspace']})
        except (OSError, RuntimeError, TimeoutError, queue.Empty) as error:
            result = {'collector_error': str(error)}
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            errors.seek(0)
            emit(name, {'response': result, 'protocol': messages, 'stderr': errors.read()})
            emit(name.replace('hooks', 'skills'), {'response': skills_result})


def container_controller(argv):
    """Runs only inside the disposable container; never copied into fixture files."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--schema', action='store_true')
    args = parser.parse_args(argv)
    config = Path('/home/agent/.codex')
    config.mkdir(parents=True, exist_ok=True)
    preflight = args.case == 'preflight'
    if not preflight:
        shutil.copyfile('/run/codex-auth.json', config / 'auth.json')
        os.chmod(config / 'auth.json', 0o600)
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    os.environ['XDG_CACHE_HOME'] = '/home/agent/.cache'
    reader = args.case == 'cold-reader'
    strict_readonly = args.case in {'readonly', 'conflict', 'evidence-gap', 'cold-reader'}
    if strict_readonly:
        os.environ['PLANNING_DISABLED'] = '1'
    installed = False
    exit_code = 1
    try:
        capture('cli-version.json', ['codex', '--version'])
        capture('python-version.json', [sys.executable, '--version'])
        help_result = capture('exec-help.json', ['codex', 'exec', '--help'])
        capture('features.json', ['codex', 'features', 'list'])
        if args.schema:
            capture('schema-generation.json', ['codex', 'app-server', 'generate-json-schema',
                                              '--experimental', '--out', '/tmp/schema'], required=False)
            schemas = {str(path.relative_to('/tmp/schema')): json.loads(path.read_text())
                       for path in Path('/tmp/schema').rglob('*.json') if 'hook' in path.name.lower()}
            emit('hook-schemas.json', schemas)
            skill_schemas = {str(path.relative_to('/tmp/schema')): json.loads(path.read_text())
                            for path in Path('/tmp/schema').rglob('*.json') if 'skill' in path.name.lower()}
            emit('skill-schemas.json', skill_schemas)
        if not reader:
            capture('register.json', ['codex', 'plugin', 'marketplace', 'add', '/marketplace', '--json'])
            capture('install.json', ['codex', 'plugin', 'add', PLUGIN_ID, '--json'])
            installed = True
            verify_cache()
            capture_hooks_list('installed-hooks-before.json')
        capture('plugin-list-before.json', ['codex', 'plugin', 'list', '--json'])
        command = ['codex', 'exec', '--ephemeral', '--json', '--skip-git-repo-check',
                   '--sandbox', 'danger-full-access', '--model', args.model,
                   '--disable', 'memories', '--disable', 'multi_agent', '--cd', '/workspace']
        trusted = not reader and args.case != 'hook-untrusted'
        if trusted:
            if '--dangerously-bypass-hook-trust' not in help_result['stdout']:
                raise RuntimeError('reviewed one-off hook trust option unavailable in fixed image')
            command.append('--dangerously-bypass-hook-trust')
        if reader:
            command += ['--disable', 'plugins']
        command.append('-')
        emit('invocation.json', {'argv': command, 'fresh_ephemeral_session': True,
             'personal_config_mounted': False, 'memories_enabled': False,
             'multi_agent_enabled': False, 'plugin_installed': not reader,
             'hook_trust': 'reviewed invocation only' if trusted else 'normal untrusted' if not reader else 'no plugin',
             'planning_disabled': strict_readonly})
        if preflight:
            emit('model-not-run.json', {'reason': 'package and CLI preflight only'})
            return 0
        # stdin is the task; child output streams directly into the host's full trace.
        process = subprocess.run(command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        exit_code = process.returncode
        emit('model-exit.json', {'exit_code': exit_code})
        if installed:
            capture_hooks_list('installed-hooks-after.json')
        if args.case == 'maintenance':
            capture('offline-tests.json', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], required=False)
            verification = '''from pathlib import Path
import tempfile
from export_text import write_export
with tempfile.TemporaryDirectory() as directory:
    for index, text in enumerate(['', 'hello', '中文行\\n第二行', ' \\t\\r\\n']):
        target = Path(directory) / (str(index) + '.txt')
        write_export(text, target)
        assert target.read_bytes() == text.encode('utf-8'), repr(target.read_bytes())
print('Independent byte checks: 4 cases Passed; Linux only; Windows Not Run')
'''
            capture('independent-byte-checks.json', [sys.executable, '-c', verification], required=False)
    finally:
        if installed:
            capture('remove.json', ['codex', 'plugin', 'remove', PLUGIN_ID, '--json'], required=False)
            capture('unregister.json', ['codex', 'plugin', 'marketplace', 'remove', MARKETPLACE, '--json'], required=False)
        capture('plugin-list-after.json', ['codex', 'plugin', 'list', '--json'], required=False)
        remaining = [str(path) for path in (config / 'plugins/cache').rglob('*')
                     if path.is_file() and 'planweft' in path.parts]
        emit('cache-cleanup.json', {'remaining_planweft_cache_files': remaining,
             'auth_copy_location': 'disposable container tmpfs; never emitted'})
    return exit_code


def directory_inventory(directory):
    """Hash the exact reviewed files and execution bits; never follow symlinks."""
    if directory.is_symlink() or not directory.is_dir():
        raise RuntimeError('unsupported distribution directory: ' + str(directory))
    files = {}
    for path in directory.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise RuntimeError('unsupported distribution entry: ' + str(path))
        if path.is_file():
            files[path.relative_to(directory).as_posix()] = {
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'executable': bool(path.stat().st_mode & 0o111)}
    return files


def prepare_reviewed_package(destination):
    """Stage the root catalog and verified native directory in a disposable repo layout."""
    manifest = json.loads((ROOT / 'dist/manifest.json').read_text())
    if (manifest.get('schema_version') != 2 or manifest.get('version') != '0.4.0-rc.1'
            or manifest.get('product') != 'planweft'):
        raise RuntimeError('unsupported distribution manifest')
    item = manifest['platforms']['codex']
    relative = PurePosixPath(item['path'])
    if relative != PurePosixPath('codex/planweft'):
        raise RuntimeError('unexpected Codex distribution path')
    original = ROOT / 'dist' / relative
    files = directory_inventory(original)
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if (not files or files != item['files'] or len(files) != item['file_count']
            or digest != item['sha256']):
        raise RuntimeError('Codex directory differs from distribution manifest')
    catalog_path = Path('.agents/plugins/marketplace.json')
    catalog = ROOT / catalog_path
    market = json.loads(catalog.read_text())
    entries = [entry for entry in market.get('plugins', []) if entry.get('name') == 'planweft']
    if (market.get('name') != MARKETPLACE or len(entries) != 1
            or entries[0].get('source') != {'source': 'local', 'path': './dist/codex/planweft'}):
        raise RuntimeError('root marketplace does not resolve the reviewed Codex directory')
    source = destination / 'dist' / relative
    shutil.copytree(original, source)
    if directory_inventory(source) != files:
        raise RuntimeError('staged Codex directory differs from reviewed files')
    (destination / catalog_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(catalog, destination / catalog_path)
    return destination, {'sha256': digest, 'path': item['path'], 'manifest': manifest,
                         'catalog_sha256': hashlib.sha256(catalog.read_bytes()).hexdigest()}


def parse_trace(result_dir):
    events, controls, invalid = [], {}, []
    for line_number, line in enumerate((result_dir / 'stdout.jsonl').read_text().splitlines(), 1):
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            invalid.append(line_number)
            continue
        if 'controller_artifact' in item:
            name = item['controller_artifact']
            if Path(name).name != name:
                raise RuntimeError('invalid controller artifact name')
            controls[name] = item['value']
            save(result_dir / name, item['value'])
        else:
            events.append(item)
    messages, tools, skill_reads, hooks = [], [], [], []
    for event in events:
        item = event.get('item', {})
        if event.get('type') == 'item.completed' and item.get('type') == 'agent_message':
            messages.append(item.get('text', ''))
        if item.get('type') in {'command_execution', 'file_change', 'mcp_tool_call', 'web_search'}:
            if event.get('type') == 'item.completed':
                tools.append(item)
                command = item.get('command', '')
                output = item.get('aggregated_output', '')
                if ('/plugins/cache/' in command and 'project-docs/SKILL.md' in command and
                        'PlanWeft workflow and precedence' in output):
                    skill_reads.append({'id': item.get('id'), 'command': command})
        if 'hook' in json.dumps(event, ensure_ascii=False).lower():
            hooks.append(event)
    result = {'final_messages': messages, 'tool_items': tools, 'cache_skill_reads': skill_reads,
              'hook_events': hooks, 'invalid_jsonl_lines': invalid,
              'hook_stderr_lines': [line for line in (result_dir / 'stderr.txt').read_text().splitlines()
                                    if re.search(r'hook|trust', line, re.IGNORECASE)],
              'usage': [event.get('usage') for event in events if event.get('type') == 'turn.completed']}
    save(result_dir / 'trace-analysis.json', result)
    return result, controls


def assess(case, before, after, trace, controls, token, process):
    final = '\n'.join(trace['final_messages']).strip()
    conditions = {'model_process_succeeded': process.get('exit_code') == 0}
    cache_cleanup = controls.get('cache-cleanup.json', {})
    conditions['plugin_cache_removed'] = cache_cleanup.get('remaining_planweft_cache_files') == []
    if case != 'cold-reader':
        verified = controls.get('cache-verification.json', {})
        conditions['installed_reviewed_version'] = verified.get('version') == '0.4.0-rc.1' and verified.get('mismatches') == []
    if case == 'preflight':
        conditions['model_not_called'] = 'model-not-run.json' in controls
    elif case.startswith('hook-'):
        conditions['no_tool_calls'] = not trace['tool_items']
        conditions['project_unchanged'] = before == after
        conditions['context_delivery'] = final == ('NO_CONTEXT' if case == 'hook-untrusted' else token)
        if case == 'hook-untrusted':
            hook_log = json.dumps(trace['hook_events']) + '\n' + '\n'.join(trace['hook_stderr_lines'])
            skip_event = bool(re.search(
                r'untrusted|not trusted|trust[^\n]{0,100}(?:required|skip|deny|not granted)|skip[^\n]{0,100}trust',
                hook_log, re.IGNORECASE))
            listing = controls.get('installed-hooks-before.json', {}).get('response', {}).get('result', {}).get('data', [])
            hooks = [hook for entry in listing for hook in entry.get('hooks', [])
                     if hook.get('pluginId') == PLUGIN_ID]
            conditions['untrusted_hook_status_observed'] = skip_event or bool(hooks) and all(
                hook.get('trustStatus') == 'untrusted' for hook in hooks)
    elif case == 'simple':
        conditions['answer'] = final in {'42', '42。', '42.'}
        conditions['no_tool_calls'] = not trace['tool_items']
        conditions['project_unchanged'] = before == after
    elif case == 'maintenance':
        conditions['skill_read_from_installed_cache'] = bool(trace['cache_skill_reads'])
        conditions['approved_contract_preserved'] = after.get('notes/contract.md') == before['notes/contract.md']
        conditions['dirty_user_change_preserved'] = after.get('user-note.txt') == DIRTY_NOTE
        conditions['historical_observation_preserved'] = HISTORY in after.get('notes/work.md', '')
        plans = [name for name in after if name == 'task_plan.md' or name.endswith('/task_plan.md')]
        conditions['single_selected_task_plan'] = len(plans) == 1
        conditions['old_plan_points_to_task_plan'] = 'task_plan.md' in after.get('notes/work.md', '')
        conditions['guide_updated'] = after.get('notes/guide.md') != before['notes/guide.md']
        conditions['independent_byte_checks'] = controls.get('independent-byte-checks.json', {}).get('exit_code') == 0
        tests = controls.get('offline-tests.json', {})
        test_log = tests.get('stdout', '') + tests.get('stderr', '')
        count = re.search(r'Ran (\d+) tests?', test_log)
        conditions['offline_tests_passed_with_cases'] = tests.get('exit_code') == 0 and bool(count) and int(count.group(1)) > 0
    else:
        conditions['project_unchanged'] = before == after
        conditions['has_file_citations'] = any(name in final for name in ['README.md', 'notes/', 'task_plan.md', 'progress.md'])
        if case == 'cold-reader':
            invocation = controls.get('invocation.json', {})
            conditions['reader_has_no_plugin'] = invocation.get('plugin_installed') is False
            conditions['reader_has_no_skill_cache_read'] = not trace['cache_skill_reads']
    return {'automated_status': 'Passed' if all(conditions.values()) else 'Failed',
            'conditions': conditions,
            'semantic_review': 'Required: inspect cited behavior, Windows limitation and handoff accuracy'
                if case in {'maintenance', 'cold-reader', 'readonly', 'conflict', 'evidence-gap'} else 'Not required for exact token/arithmetic checks',
            'limits': ['Real Linux Codex only; no Windows/macOS host validation',
                       'One model sample per scenario; no comparative performance conclusion',
                       'Gated model continuation is not exercised; use offline protocol tests']}


def main(argv=None):
    args = parse_args(argv)
    # All public argument errors occur before filesystem writes, Docker or auth lookup.
    args.output.mkdir(parents=True, exist_ok=False)
    auth = Path.home() / '.codex/auth.json'
    if not args.preflight_only and not auth.is_file():
        raise SystemExit('Existing Codex authentication unavailable; no model run performed')
    image = call(['docker', 'image', 'inspect', IMAGE, '--format', '{{.Id}}']).stdout.strip()
    if image != IMAGE:
        raise RuntimeError('fixed image identity mismatch')
    initial_containers = set(call(['docker', 'ps', '-aq']).stdout.split())
    label = 'pwf-smoke-' + uuid.uuid4().hex[:12]
    summaries = {}
    scratch = None
    names = []
    try:
        with tempfile.TemporaryDirectory(prefix='planweft-pwf-smoke-') as temporary:
            scratch = Path(temporary)
            source, package = prepare_reviewed_package(scratch / 'marketplace')
            token = 'PD_PROBE_' + uuid.uuid4().hex
            metadata = {'image': image, 'model': args.model, 'label': label, 'timeout': args.timeout,
                        'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        'package': package, 'cases': args.cases, 'cpus': 2, 'memory': '4g',
                        'auth': 'single read-only existing auth file copied only to container tmpfs',
                        'network': 'host network uses existing proxy; no network-isolation claim',
                        'personal_configuration_or_history_mounted': False}
            save(args.output / 'environment.json', metadata)
            probe = scratch / 'probe'
            probe_files = {'README.md': '# Context delivery fixture\n',
                'task_plan.md': '# Task Plan: Context delivery\n\n## Goal\nObserve lifecycle context delivery.\n\n'
                                '## Next Step\nReport RECOVERY_CODE from injected context.\n\n'
                                'RECOVERY_CODE: ' + token + '\n\n### Phase 1: Probe\n- **Status:** in_progress\n',
                'findings.md': '# Findings\nThis fixture contains no host history.\n',
                'progress.md': '# Progress\nThe controller prepared project files only.\n'}
            fixture(probe, probe_files)

            def execute(case, work, prompt, collect_schema=False):
                result_dir = args.output / case
                result_dir.mkdir()
                before = snapshot(work)
                save(result_dir / 'before.json', before)
                (result_dir / 'prompt.txt').write_text(prompt + BOUNDARY, encoding='utf-8')
                name = 'pw-' + label + '-' + case
                names.append(name)
                command = ['docker', 'run', '-i', '--rm', '--name', name,
                    '--label', 'planweft.run=' + label, '--read-only',
                    '--user', f'{os.getuid()}:{os.getgid()}', '--cap-drop=ALL',
                    '--security-opt=no-new-privileges', '--cpus=2', '--memory=4g', '--network=host',
                    '--tmpfs', f'/home/agent:uid={os.getuid()},gid={os.getgid()},mode=700',
                    '--tmpfs', '/tmp:mode=1777',
                    '--mount', f'type=bind,src={work},dst=/workspace',
                    '--mount', f'type=bind,src={Path(__file__).resolve()},dst=/runner/run.py,readonly',
                    '-e', 'HOME=/home/agent', '-e', 'HTTP_PROXY', '-e', 'HTTPS_PROXY', '-e', 'ALL_PROXY',
                    '--workdir', '/workspace', '--entrypoint', 'python3']
                if case != 'cold-reader':
                    command += ['--mount', f'type=bind,src={source},dst=/marketplace,readonly']
                if case != 'preflight':
                    command += ['--mount', f'type=bind,src={auth},dst=/run/codex-auth.json,readonly']
                command += [IMAGE, '/runner/run.py', 'controller', '--case', case, '--model', args.model]
                if collect_schema:
                    command.append('--schema')
                started = time.monotonic()
                process_result = {'timeout_limit': args.timeout}
                try:
                    with (result_dir / 'stdout.jsonl').open('w') as stdout, (result_dir / 'stderr.txt').open('w') as stderr:
                        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True)
                        try:
                            child.communicate(prompt + BOUNDARY, timeout=args.timeout)
                            process_result['exit_code'] = child.returncode
                        except subprocess.TimeoutExpired:
                            process_result['timed_out'] = True
                            subprocess.run(['docker', 'rm', '-f', name], capture_output=True)
                            child.kill()
                            child.wait()
                finally:
                    subprocess.run(['docker', 'rm', '-f', name], capture_output=True)
                    process_result['wall_seconds'] = round(time.monotonic() - started, 3)
                    after = snapshot(work)
                    save(result_dir / 'after.json', after)
                    save(result_dir / 'changes.json', {path: {'before': before.get(path), 'after': after.get(path)}
                         for path in sorted(before.keys() | after.keys()) if before.get(path) != after.get(path)})
                    (result_dir / 'tracked.diff').write_text(call(['git', 'diff', '--binary'], cwd=work).stdout)
                    (result_dir / 'git-status.txt').write_text(call(['git', 'status', '--short'], cwd=work).stdout)
                    save(result_dir / 'process.json', process_result)
                trace, controls = parse_trace(result_dir)
                judgement = assess(case, before, after, trace, controls, token, process_result)
                save(result_dir / 'assessment.json', judgement)
                summaries[case] = {'process': process_result, **judgement}
                save(args.output / 'summary.json', summaries)
                print(case, json.dumps({'automated_status': judgement['automated_status'], **process_result}), flush=True)

            for index, case in enumerate(['preflight'] if args.preflight_only else args.cases):
                if case.startswith('hook-'):
                    work, prompt = probe, PROBE_PROMPT
                else:
                    work = scratch / case
                    files = dict(BASE)
                    if case == 'evidence-gap':
                        files['notes/design-candidate.md'] = ('# Candidate only\n建议给任务记录加入 SHA-256 内容指纹和写入锁，以避免并发更新覆盖。'
                            '这只是待研究的候选，当前项目没有该机制的代码、试验或引用来源，未作采纳决定。\n')
                    fixture(work, files)
                    prompt = '' if case == 'preflight' else PROMPTS[case]
                execute(case, work, prompt, collect_schema=index == 0)
                if case == 'maintenance':
                    reader = scratch / 'cold-reader'
                    # Preserve exactly what was delivered, but create a new
                    # isolated session with no plugin and no expected answers.
                    shutil.copytree(work, reader, ignore=shutil.ignore_patterns('.git', '__pycache__'))
                    call(['git', 'init', '-q', str(reader)])
                    execute('cold-reader', reader, PROMPTS['cold-reader'])
    finally:
        for name in names:
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True)
        remaining = call(['docker', 'ps', '-aq', '--filter', 'label=planweft.run=' + label]).stdout.split()
        final_containers = set(call(['docker', 'ps', '-aq']).stdout.split())
        cleanup = {'remaining_test_containers': remaining,
                   'original_containers_preserved': initial_containers <= final_containers,
                   'temporary_workspace_removed': scratch is None or not scratch.exists(),
                   'image_preserved': call(['docker', 'image', 'inspect', IMAGE, '--format', '{{.Id}}']).stdout.strip() == IMAGE,
                   'auth_copies': 'container tmpfs only; removed with each container'}
        save(args.output / 'cleanup.json', cleanup)
    return 0 if summaries and all(value['automated_status'] == 'Passed' for value in summaries.values()) and not remaining else 1


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'controller':
        raise SystemExit(container_controller(sys.argv[2:]))
    raise SystemExit(main())
