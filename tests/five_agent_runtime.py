"""Inside-container adapter for the real five-host release runner.

Credentials arrive only over stdin and stay in container memory/tmpfs. This
module never reads the laboratory's MemoryProxy config or identity headers.
"""
import hashlib
import importlib.util
import ctypes
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import struct
import tarfile
import tempfile
import threading
import time
import uuid

OUT = Path('/results')
WORK = Path('/workspace')
HOME = Path('/home/agent')
SECRETS = []
REDACTIONS = 0


def watch_gate_reads():
    """Observe only two synthetic gate files during a Linux model invocation.

    IN_ACCESS distinguishes a read from merely exiting without running Stop.
    This carries no PID attribution; use only in isolated no-tool scenarios.
    """
    libc=ctypes.CDLL(None,use_errno=True)
    libc.inotify_init1.argtypes=[ctypes.c_int];libc.inotify_init1.restype=ctypes.c_int
    libc.inotify_add_watch.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_uint32]
    libc.inotify_add_watch.restype=ctypes.c_int
    fd=libc.inotify_init1(os.O_NONBLOCK|os.O_CLOEXEC)
    if fd<0: raise OSError(ctypes.get_errno(),'Cannot initialize gate read observation')
    watches={}
    try:
        for name in ['.stop_blocks','.gate_last_ledger']:
            wd=libc.inotify_add_watch(fd,os.fsencode(WORK/name),0x1)
            if wd<0: raise OSError(ctypes.get_errno(),'Cannot watch gate counter')
            watches[wd]=name
    except Exception:
        os.close(fd);raise
    return fd,watches


def finish_gate_reads(watch):
    fd,watches=watch;events=[];overflow=False
    try:
        while True:
            try: data=os.read(fd,65536)
            except BlockingIOError: break
            if not data: break
            offset=0
            while offset<len(data):
                wd,mask,cookie,size=struct.unpack_from('iIII',data,offset);offset+=16+size
                overflow |= bool(mask&0x4000)
                if mask&0x1: events.append({'file':watches.get(wd),'event':'IN_ACCESS'})
    finally: os.close(fd)
    return {'kind':'Linux inotify during isolated no-tool model invocation','events':events,'overflow':overflow,'pid_attribution':False}


def safe_text(text):
    global REDACTIONS
    for value in SECRETS:
        REDACTIONS += text.count(value)
        text = text.replace(value, '[REDACTED_CREDENTIAL]')
    return text


def secret_values(value):
    if isinstance(value,dict):
        return [s for child in value.values() for s in secret_values(child)]
    if isinstance(value,list):
        return [s for child in value for s in secret_values(child)]
    return [value] if isinstance(value,str) and len(value)>=16 and not value.startswith('https://') else []


def save(name, value):
    (OUT / (name + '.json')).write_text(safe_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n'))


def run(name, argv, *, input_data=None, timeout=240, required=True):
    started = time.monotonic()
    result = subprocess.run(argv, cwd=WORK, input=input_data, text=True, capture_output=True, timeout=timeout)
    (OUT / (name + '.stdout')).write_text(safe_text(result.stdout))
    (OUT / (name + '.stderr')).write_text(safe_text(result.stderr))
    save(name, {'argv': argv, 'exit_code': result.returncode, 'seconds': time.monotonic() - started})
    if required and result.returncode:
        raise RuntimeError(name + ' failed')
    return result


def unittest_observation(process):
    output=process.stderr+process.stdout
    count=re.search(r'^Ran (\d+) tests? in ',output,re.M)
    failure=re.search(r'^FAILED \(failures=(\d+)\)\s*$',output,re.M)
    return {'tests':int(count.group(1)) if count else 0,
            'passed':process.returncode==0 and bool(re.search(r'^OK\s*$',output,re.M)),
            'assertion_failures':int(failure.group(1)) if failure and process.returncode!=0 else 0}


def regression_effectiveness(work, fixed):
    """A meaningful regression detects the original BOM bug, regardless of method count.

    Run the identical test bytes against the exact synthetic original module in
    a separate directory. Import errors, skipped-only suites and unrelated test
    crashes cannot count as reproducing the defect. Never mutate owner files.
    """
    original='from pathlib import Path\n\n\ndef write_export(text, target):\n    Path(target).write_text(text, encoding="utf-8-sig")\n'
    with tempfile.TemporaryDirectory(prefix='pw-regression-') as temporary:
        project=Path(temporary)
        shutil.copytree(work/'tests',project/'tests',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        (project/'export_text.py').write_text(original)
        baseline=subprocess.run(['python3','-m','unittest','discover','-s','tests','-v'],
                                cwd=project,text=True,capture_output=True,timeout=60)
    current=unittest_observation(fixed);old=unittest_observation(baseline)
    return {'status':'Passed' if current['passed'] and current['tests']>0 and
            old['tests']==current['tests'] and old['assertion_failures']>0 and
            'AssertionError' in baseline.stderr else 'Failed',
            'scope':'identical generated tests against the fixed module and the synthetic original BOM module',
            'original_module_sha256':hashlib.sha256(original.encode()).hexdigest(),
            'fixed':current,'original':old,'original_exit_code':baseline.returncode,
            'original_stdout':baseline.stdout,'original_stderr':baseline.stderr}


def setup_environment():
    os.environ.update(HOME=str(HOME), USERPROFILE=str(HOME), XDG_CONFIG_HOME=str(HOME/'.config'),
        XDG_DATA_HOME=str(HOME/'.local/share'), XDG_CACHE_HOME=str(HOME/'.cache'),
        CODEX_HOME=str(HOME/'.codex'), CLAUDE_CONFIG_DIR=str(HOME/'.claude'),
        PI_CODING_AGENT_DIR=str(HOME/'.pi/agent'), DSH_HOME=str(HOME/'.dsh'),
        npm_config_userconfig='/dev/null', npm_config_cache=str(HOME/'.npm'),
        npm_config_registry='https://registry.npmjs.org', PYTHONDONTWRITEBYTECODE='1')
    for name in ['.codex', '.claude', '.pi/agent', '.config/opencode', '.dsh']:
        (HOME/name).mkdir(parents=True, exist_ok=True)


def prepare_model(host, secret, model):
    if host == 'codex':
        file = HOME/'.codex/auth.json'
        file.write_text(json.dumps(secret['auth']))
        file.chmod(0o600)
        return
    key, url = secret['api_key'], secret['base_url']
    os.environ['PLANWEFT_MODEL_KEY'] = key
    if host == 'claude':
        # The proxy stores an API endpoint including /v1; Anthropic's native
        # client appends /v1 itself (DeepSeek's documented base is /anthropic).
        url = url.rstrip('/').removesuffix('/v1')
        os.environ.update(ANTHROPIC_AUTH_TOKEN=key, ANTHROPIC_BASE_URL=url,
            ANTHROPIC_MODEL=model, ANTHROPIC_DEFAULT_OPUS_MODEL=model,
            ANTHROPIC_DEFAULT_SONNET_MODEL=model, ANTHROPIC_DEFAULT_HAIKU_MODEL=model,
            CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1')
    elif host == 'pi':
        config = {'providers': {'release': {'baseUrl': url, 'api': 'openai-completions',
            'apiKey': '$PLANWEFT_MODEL_KEY', 'authHeader': True,
            'compat': {'supportsDeveloperRole': False, 'supportsReasoningEffort': True},
            'models': [{'id': model, 'name': model, 'reasoning': True, 'input': ['text'],
                        'contextWindow': 1048576, 'maxTokens': 65536}]}}}
        (HOME/'.pi/agent/models.json').write_text(json.dumps(config))
    elif host == 'opencode':
        config = {'$schema': 'https://opencode.ai/config.json', 'model': 'release/'+model,
            'small_model': 'release/'+model, 'autoupdate': False, 'share': 'disabled',
            'provider': {'release': {'npm':'@ai-sdk/openai-compatible',
                'options': {'baseURL':url,'apiKey':'{env:PLANWEFT_MODEL_KEY}'},
                'models':{model:{'limit':{'context':1048576,'output':65536}}}}}}
        (HOME/'.config/opencode/opencode.json').write_text(json.dumps(config))
    elif host == 'dsh':
        # JSON scalar quoting is also valid YAML; no credential is written here.
        text = '- id: agent-default-model\n  config:\n    provider: release\n    model: '+json.dumps(model)+'\n'
        text += '- id: llm-pi-ai\n  config:\n    providers:\n      release:\n'
        text += '        apiKeyEnv: PLANWEFT_MODEL_KEY\n        api: openai-completions\n'
        text += '        baseURL: '+json.dumps(url)+'\n'
        text += '        compat:\n          thinkingFormat: deepseek\n          supportsDeveloperRole: false\n          maxTokensField: max_tokens\n'
        text += '        models:\n          - id: '+json.dumps(model)+'\n            name: DeepSeek\n            contextWindow: 1048576\n            maxTokens: 65536\n'
        # Preserve real native events for verification; this affects local log
        # encoding only. No observer extension or synthetic event carrier.
        text += '- id: session-persistence-jsonl\n  config:\n    root: /home/agent/.dsh/sessions\n    compression: none\n'
        (HOME/'.dsh/cordis.patch.yml').write_text(text)


def native_load(host, package_root):
    if host == 'codex':
        return run('native-load', ['codex', 'plugin', 'list', '--json']).stdout
    if host == 'claude':
        return run('native-load', ['claude', 'plugin', 'list', '--json']).stdout
    if host == 'pi':
        # EOF after the RPC request is sufficient; no model is selected or called.
        text=run('native-load', ['pi', '--mode', 'rpc', '--no-session', '--approve'],
                   input_data='{"id":"pw","type":"get_commands"}\n', timeout=30).stdout
        events=[json.loads(line) for line in text.splitlines() if line.startswith('{')]
        reply=next((e for e in events if e.get('id')=='pw'),{})
        if not reply.get('success') or sum(c.get('name')=='pw-plan-status' for c in reply.get('data',{}).get('commands',[]))!=1:
            raise RuntimeError('Pi did not discover exactly one PlanWeft Extension')
        return text
    if host == 'opencode':
        result = run('native-load', ['opencode', 'debug', 'agent', 'build']).stdout
        tools = json.loads(result).get('tools', {})
        if not all(tools.get(key) for key in ['pw_init', 'pw_status', 'pw_check']):
            raise RuntimeError('OpenCode tools missing')
        run('native-skills', ['opencode', 'debug', 'skill'])
        return result
    profile=HOME/'.dsh/profiles/headless'
    manifest=json.loads((profile/'package.json').read_text())
    if manifest.get('dsh',{}).get('profile',{}).get('bundles',[]).count('planweft')!=1 or (profile/'node_modules/planweft').resolve()!=package_root:
        raise RuntimeError('DSH did not select the exact native bundle once')
    text=run('native-load', ['dsh', '--profile', 'headless', '--dump-config']).stdout
    if 'planweft/dsh' not in text and '/dist/dsh/planweft/index.mjs' not in text:
        raise RuntimeError('DSH native bundle did not compose')
    run('native-boot', ['dsh', '--profile', 'headless', '--help'])
    return text


def verify_files(host, package, record):
    root = Path(record['packageRoot'])
    for expected in package.rglob('*'):
        if not expected.is_file(): continue
        relative=expected.relative_to(package)
        actual=root/relative
        if not actual.is_file() or actual.read_bytes()!=expected.read_bytes():
            raise RuntimeError('Persistent npm package differs from exact archive: '+str(relative))
    manifest = json.loads((package/'dist/manifest.json').read_text())['platforms'][host]
    expected_root = root/'dist'/host/'planweft'
    native = expected_root
    if host in {'codex', 'claude'}:
        suffix = '.codex-plugin/plugin.json' if host == 'codex' else '.claude-plugin/plugin.json'
        caches = list((HOME/('.codex/plugins/cache' if host == 'codex' else '.claude/plugins/cache')).rglob(suffix))
        matches = [p.parent.parent for p in caches if json.loads(p.read_text()).get('name') == 'planweft']
        if len(matches) != 1:
            raise RuntimeError('Expected exactly one native plugin cache')
        native = matches[0]
    cache = native
    if host == 'claude':
        # Claude's local marketplace loads its source payload directly, even
        # when install also created a version cache. Bind the executed source,
        # while independently retaining the cache-content check below.
        registry = WORK/'.planweft/registries/claude'
        catalog = registry/'.claude-plugin/marketplace.json'
        data = json.loads(catalog.read_text())
        if (catalog.resolve() != catalog.absolute() or data.get('name') != record.get('catalog')
                or len(data.get('plugins', [])) != 1
                or data['plugins'][0].get('name') != 'planweft'
                or data['plugins'][0].get('source') != './payload'):
            raise RuntimeError('Claude managed marketplace source differs')
        native = registry/'payload'
        if native.resolve() != native.absolute():
            raise RuntimeError('Claude managed source must not traverse symlinks')
    checked = 0
    for name, expected in manifest['files'].items():
        for base in {native, cache, expected_root}:
            p = base/name
            if host == 'claude' and p.resolve() != p.absolute():
                raise RuntimeError('Claude resource must not traverse symlinks: '+name)
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected['sha256']:
                raise RuntimeError('Installed content differs: '+name)
            if bool(p.stat().st_mode & 0o111) != expected['executable']:
                raise RuntimeError('Installed executable bit differs: '+name)
        checked += 1
    save('installed-content', {'status':'Passed','files_checked':checked,'native_root':str(native),
                              'cache_root':str(cache),'package_root':str(root),'version':record['version']})
    return root


def model_command(host, model, prompt, case):
    if host == 'codex':
        command = ['codex','exec',*([] if case=='permission-denial' else ['--ephemeral']),
            '--json','--skip-git-repo-check',
            '--sandbox','danger-full-access','--model',model,'--disable','memories',
            '--disable','multi_agent','--cd',str(WORK)]
        if case == 'cold-reader':
            command += ['--disable', 'plugins']
        # This separate lane is explicitly not normal persisted trust acceptance.
        if case not in {'untrusted','cold-reader','readonly','simple','persisted-trust','reminder-dedup'}:
            command += ['--dangerously-bypass-hook-trust']
        return command+['-'], prompt
    if host == 'claude':
        command=['claude','-p','--no-session-persistence','--permission-mode','acceptEdits',
                '--allowedTools','Read,Edit,Write,Bash,Glob,Grep,Skill',
                '--model',model,'--output-format','stream-json','--verbose']
        if case in {'stopping','gated-continuation','gate-cap','gate-stall','gate-cap-disabled','gate-stall-disabled'}:
            command+=['--debug','hooks','--debug-file','/tmp/planweft-native-hooks.log']
        if case=='permission-denial':
            command+=['--disallowedTools','Bash(python3 /workspace/write-probe.py)']
        return command, prompt
    if host == 'pi':
        return ['pi','--print','--no-session','--approve','--provider','release',
                '--model',model,'--mode','json',prompt], None
    if host == 'opencode':
        return ['opencode','run',*([] if case=='permission-denial' else ['--auto']),
                '--format','json','--model','release/'+model,prompt], None
    return ['dsh','--profile','headless',prompt], None


def codex_denial_records(text):
    """Project the native rollout's matched call/result; exec JSON omits denial.

    This is the new synthetic container session, never the user's chat history.
    Unrelated messages and arguments are excluded from the exported evidence.
    """
    calls={};matched=[]
    for index,line in enumerate(text.splitlines()):
        try: event=json.loads(line)
        except ValueError: continue
        if event.get('type')!='response_item': continue
        item=event.get('payload',{})
        args=None
        if item.get('type')=='custom_tool_call' and item.get('name')=='exec':
            args=single_exec_command(item.get('input',''))
        elif item.get('type')=='function_call' and item.get('name','').split('.')[-1] in {'exec_command','shell_command','shell'}:
            try: args=json.loads(item.get('arguments','{}'))
            except (ValueError,TypeError): continue
        if args and args.get('cmd',args.get('command'))=='python3 /workspace/write-probe.py':
            calls[item.get('call_id')]={'record':index,'item':item}
        if item.get('type') in {'function_call_output','custom_tool_call_output'} and item.get('call_id') in calls:
            output=item.get('output','')
            if isinstance(output,list):
                output='\n'.join(c.get('text','') for c in output if isinstance(c,dict) and c.get('type')=='input_text')
            if isinstance(output,str) and 'rejected' in output.lower() and 'PW_NATIVE_DENY' in output:
                matched.append({'call':calls[item['call_id']], 'result':{'record':index,'item':item}})
    return matched


def single_exec_command(source):
    """Recognize only one literal tool call and optional printing of its result.

    Codex 0.149.1 may expose exec as a JavaScript tool. Never execute or accept
    arbitrary JS while proving permission denial: extra statements, expressions,
    interpolated values and synthesized error messages fail this bounded grammar.
    """
    match=re.fullmatch(r'\s*const\s+([A-Za-z_$][\w$]*)\s*=\s*await\s+tools\.exec_command\((\{.*\})\);\s*text\((?:JSON\.stringify\(\1\)|\1)\);?\s*',source,re.S)
    literal=match[2] if match else None
    if literal is None:
        match=re.fullmatch(r'\s*text\(await\s+tools\.exec_command\((\{.*\})\)\);?\s*',source,re.S)
        if match: literal=match[1]
    if literal is None: return None
    try: args=json.loads(literal)
    except ValueError: return None
    if set(args)-{'cmd','workdir','yield_time_ms','max_output_tokens'}: return None
    if args.get('cmd')!='python3 /workspace/write-probe.py' or args.get('workdir','/workspace')!='/workspace': return None
    return args


def codex_tool_records(text):
    """Retain bounded native tool records for diagnosing a failed matcher."""
    records=[];size=0
    for index,line in enumerate(text.splitlines()):
        try: event=json.loads(line)
        except ValueError: continue
        item=event.get('payload',{})
        if event.get('type')=='response_item' and item.get('type') in {
                'function_call','function_call_output','custom_tool_call','custom_tool_call_output'}:
            size+=len(line.encode())
            if size>256*1024: raise RuntimeError('Synthetic native permission tool records exceeded bound')
            records.append({'record':index,'item':item})
    return records


def native_dsh_denial(text):
    """Bind the native filesystem error to the attempted protected-file write."""
    calls={}
    for line in text.splitlines():
        try: event=json.loads(line)
        except ValueError: continue
        data=event.get('data',{})
        if event.get('type')=='tool/call':
            try: args=json.loads(data.get('arguments','{}'))
            except (ValueError,TypeError): continue
            calls[data.get('callId')]=(data.get('name'),args.get('file_path'))
        if event.get('type')=='tool/result':
            message=data.get('message',{})
            call=message.get('source',{}).get('callId')
            if (calls.get(call)==('write','/workspace/protected.txt')
                    and data.get('error',{}).get('code')=='FS_SANDBOX_DENIED'
                    and 'read-only' in json.dumps(message)):
                return True
    return False


def native_rule_denial(host,text):
    """Match host-generated denied tool records, never natural-language claims."""
    calls=set();rule_denials=set()
    for line in text.splitlines():
        try: event=json.loads(line)
        except ValueError: continue
        if host=='claude':
            for block in event.get('message',{}).get('content',[]):
                if (block.get('type')=='tool_use' and block.get('name')=='Bash'
                        and block.get('input',{}).get('command')=='python3 /workspace/write-probe.py'):
                    calls.add(block.get('id'))
            # The summary list alone does not distinguish a rule from an ask,
            # mode or classifier rejection. Bind the native reason event too.
            if (event.get('type')=='system' and event.get('subtype')=='permission_denied'
                    and event.get('decision_reason_type')=='rule'
                    and 'python3 /workspace/write-probe.py' in json.dumps(event.get('decision_reason'))):
                rule_denials.add(event.get('tool_use_id'))
        elif host=='opencode' and event.get('type')=='tool_use':
            part=event.get('part',{});state=part.get('state',{})
            if (part.get('tool')=='bash' and state.get('status')=='error'
                    and state.get('input',{}).get('command')=='python3 /workspace/write-probe.py'
                    and 'The user has specified a rule which prevents' in state.get('error','')
                    and 'python3 /workspace/write-probe.py' in state.get('error','')
                    and 'deny' in state.get('error','')):
                return True
    return bool(calls & rule_denials) if host=='claude' else False


def codex_trusted_model(model,prompt,timeout):
    """Native trust UI between three complete, independent app-server sessions."""
    from codex_trust_probe import trust_hooks
    from codex_context_probe import run_probe
    deadline=time.monotonic()+timeout
    native=Path(json.loads((OUT/'installed-content.json').read_text())['native_root'])
    package=Path('/tmp/unpacked/package');sessions=[]
    def remaining():
        value=int(deadline-time.monotonic())
        if value<1: raise TimeoutError('Persisted trust scenario exceeded deadline')
        return value
    def invoke(name,expected,forbidden=None):
        process,observed=run_probe(model,WORK,OUT/name,package,native,remaining(),safe_text,
            prompt=prompt,expected_token=expected,forbidden_token=forbidden)
        sessions.append({'name':name,**observed})
        save('native-trust-sessions',{'sessions':sessions,'scope':'Fresh processes/threads, no resume or session history'})
        if process.returncode or observed.get('status')!='Passed':
            raise RuntimeError('Native context attribution failed: '+name)
        return process,observed
    original=re.search(r'PW_RECOVERY_[a-f0-9]+',(WORK/'task_plan.md').read_text())[0]
    _,before=invoke('context-before-trust',None,original)
    ui=trust_hooks(model,WORK,OUT/'native-trust-ui.log',min(90,remaining()),sanitize=safe_text)
    _,after=invoke('context-after-trust',original)
    fresh='PW_RECOVERY_'+uuid.uuid4().hex
    plan=WORK/'task_plan.md';plan.write_text(plan.read_text().replace(original,fresh))
    process,recovered=invoke('context-fresh-session',fresh,original)
    distinct_threads=len({s['thread_id'] for s in sessions})==3
    distinct_processes=len({s['native_pid'] for s in sessions})==3
    observations={'ui':ui,'before_no_context':before['answer']=='NO_CONTEXT',
                  'after_context':after['answer']==original,'fresh_context':recovered['answer']==fresh,
                  'no_tool_reads':all(s.get('no_model_tool_calls') is True for s in sessions),
                  'no_tool_reads_scope':'No model-initiated tools; native hooks read project files',
                  'distinct_threads':distinct_threads,'distinct_processes':distinct_processes,
                  'sessions':sessions,'new_owner_token':fresh,'history_available':False,'trust_bypass':False}
    save('native-trust',observations)
    (OUT/'model.stdout').write_text(safe_text(process.stdout))
    (OUT/'model.stderr').write_text(safe_text(process.stderr))
    metadata={'argv':process.args,'exit_code':process.returncode,'fresh_session':True,
              'case':'persisted-trust','codex_hook_trust':'normal','plugin_installed':True,
              'stdout_format':'Explicit context_probe_projection; complete native protocol retained for each session',
              'transport':'three independent app-server processes with full EOF drain',
              'external_memory':'Codex direct authentication; memories disabled; no session history'}
    save('model',metadata);save('model-invocation',metadata)
    return process,observations


def pi_project_approval():
    observed={}
    for name,flag in [('unapproved','--no-approve'),('approved','--approve')]:
        output=run('native-project-'+name,['pi','--mode','rpc','--no-session',flag],
                   input_data='{"id":"approval-probe","type":"get_commands"}\n',timeout=30).stdout
        events=[json.loads(line) for line in output.splitlines() if line.startswith('{')]
        reply=next((e for e in events if e.get('id')=='approval-probe'),{})
        if not reply.get('success'): raise RuntimeError('Pi project approval query failed')
        observed[name]=[{'name':c.get('name'),'source':c.get('source')} for c in reply.get('data',{}).get('commands',[])
                        if c.get('name','').startswith('pw-') or 'project-docs' in c.get('name','')]
    passed=(observed['unapproved']==[]
            and observed['approved'].count({'name':'pw-plan-status','source':'extension'})==1
            and observed['approved'].count({'name':'skill:project-docs','source':'skill'})==1)
    save('native-project-approval',{'status':'Passed' if passed else 'Failed','commands':observed,
                                   'scope':'explicit per-invocation project resource trust; not a tool sandbox',
                                   'model_calls':False,'global_or_cli_extensions':False})
    return passed


def pi_model(model, prompt, timeout, *, activate=True):
    """Keep native follow-ups until Pi 0.84.3 settles, then verify idle state."""
    command=['pi','--mode','rpc','--no-session','--approve','--provider','release','--model',model]
    messages=[]; inbox=queue.Queue(); started=time.monotonic(); deadline=started+timeout
    counts={'agent_start':0,'agent_end':0,'agent_settled':0}
    state=None; completion='Failed'; failure=None; model_error=False; forced=False
    with tempfile.TemporaryFile(mode='w+') as errors:
        proc=subprocess.Popen(command,cwd=WORK,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True)
        def read():
            for line in proc.stdout:
                inbox.put(line)
            inbox.put(None)
        reader=threading.Thread(target=read,daemon=True);reader.start()
        def send(value):
            proc.stdin.write(json.dumps(value)+'\n');proc.stdin.flush()
        def record(line):
            nonlocal model_error
            messages.append(line)
            try: value=json.loads(line)
            except ValueError: return {}
            if not isinstance(value,dict): return {}
            kind=value.get('type')
            if kind in counts: counts[kind]+=1
            if kind=='agent_end':
                model_error |= any(m.get('role')=='assistant' and m.get('stopReason') in {'error','aborted'}
                                   for m in value.get('messages',[]) if isinstance(m,dict))
            return value
        def event():
            remaining=deadline-time.monotonic()
            if remaining<=0: raise TimeoutError('Pi RPC did not settle before deadline')
            try: line=inbox.get(timeout=remaining)
            except queue.Empty: raise TimeoutError('Pi RPC did not settle before deadline') from None
            if line is None: raise RuntimeError('Pi RPC closed before verified completion')
            return record(line)
        def until(predicate):
            while True:
                value=event()
                if predicate(value): return value
        try:
            if activate:
                send({'id':'activate','type':'prompt','message':'/pw-plan-execute'})
                activation=until(lambda x:x.get('id')=='activate')
                if activation.get('success') is not True: raise RuntimeError('Pi explicit activation failed')
            send({'id':'task','type':'prompt','message':prompt})
            until(lambda x:x.get('type')=='agent_settled' and counts['agent_end']>0 and counts['agent_start']>0)
            settled_starts=counts['agent_start']
            send({'id':'settled-state','type':'get_state'})
            response=until(lambda x:x.get('id')=='settled-state')
            state=response.get('data')
            if response.get('success') is not True or not isinstance(state,dict) or not (
                    state.get('isStreaming') is False and state.get('isCompacting') is False
                    and type(state.get('pendingMessageCount')) is int and state['pendingMessageCount']==0):
                raise RuntimeError('Pi settled event did not confirm idle state')
            if counts['agent_start']!=settled_starts:
                raise RuntimeError('Pi restarted before verified shutdown')
            # stdin EOF is the native RPC shutdown signal, only after settled.
            proc.stdin.close()
            proc.wait(timeout=min(5,max(0.1,deadline-time.monotonic())))
            reader.join(timeout=1)
            if reader.is_alive(): raise RuntimeError('Pi stdout did not reach EOF')
            while not inbox.empty():
                line=inbox.get_nowait()
                if line is not None: record(line)
            if counts['agent_start']!=settled_starts:
                raise RuntimeError('Pi restarted during shutdown')
            if proc.returncode!=0: raise RuntimeError('Pi RPC exited nonzero')
            if model_error: raise RuntimeError('Pi model error in collected turns')
            completion='settled and idle; native EOF shutdown'
        except Exception as error:
            failure=str(error)
        finally:
            if proc.poll() is None:
                forced=True;proc.terminate()
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired: proc.kill();proc.wait(timeout=5)
            if not proc.stdin.closed: proc.stdin.close()
            reader.join(timeout=1)
            while not inbox.empty():
                line=inbox.get_nowait()
                if line is not None: record(line)
            (OUT/'model.stdout').write_text(safe_text(''.join(messages)))
            errors.seek(0);(OUT/'model.stderr').write_text(safe_text(errors.read()))
            proc.stdout.close()
    returncode=0 if failure is None and not forced and not model_error else 1
    save('model',{'argv':command,'exit_code':returncode,'process_exit_code':proc.returncode,
                  'seconds':time.monotonic()-started,'completion':completion,'failure':failure,
                  'forced_termination':forced,'event_counts':counts,'final_state':state,
                  'activation':'native /pw-plan-execute in same fresh RPC session' if activate else 'not requested; passive session'})
    return subprocess.CompletedProcess(command,returncode)


def codex_registration_projection(config):
    """Retain native registration evidence without copying provider settings."""
    import tomllib
    data = config.read_bytes()
    parsed = tomllib.loads(data.decode('utf-8'))
    return {'config_sha256': hashlib.sha256(data).hexdigest(),
            'marketplaces': {name: {key: value for key, value in entry.items()
                                   if key in {'source', 'source_type'}}
                             for name, entry in parsed.get('marketplaces', {}).items()},
            'plugins': {name: {key: value for key, value in entry.items() if key == 'enabled'}
                        for name, entry in parsed.get('plugins', {}).items()}}


def controller(payload):
    global SECRETS
    if payload['case'] in {'preflight','lifecycle','package-approval'} and payload.get('secret'):
        raise ValueError('No-model scenario must not receive credentials')
    SECRETS=secret_values(payload.get('secret',{}))
    setup_environment()
    host, case = payload['host'], payload['case']
    result = {'host':host,'case':case,'status':'Failed','model_session':'Not Run'}
    if payload.get('probe_scope'): result['probe_scope']=payload['probe_scope']
    try:
        versions = {}
        for command in [[host if host != 'claude' else 'claude','--version'], ['node','--version'],['python3','--version']]:
            versions[command[0]] = run('version-'+command[0], command).stdout.strip()
        result['versions'] = versions
        package = Path('/tmp/unpacked/package')
        with tarfile.open('/input/package.tgz') as archive:
            # Debian's Python 3.11 predates extraction filters. Accept only
            # package-local regular files/directories, never links or devices.
            for item in archive:
                path = Path(item.name)
                if path.is_absolute() or '..' in path.parts or path.parts[0] != 'package' or not (item.isfile() or item.isdir()):
                    raise ValueError('Unsafe package archive member')
            archive.extractall(package.parent)
        manifest = json.loads((package/'package.json').read_text())
        result.update(version=manifest['version'], npm_sha256=hashlib.sha256(Path('/input/package.tgz').read_bytes()).hexdigest())
        secret = payload.pop('secret', None)
        if secret:
            prepare_model(host, secret, payload['model'])
        os.environ['PLANNING_DISABLED'] = '1'
        cli = ['node',str(package/'bin/planweft.mjs')]
        scope = ['--global'] if host in {'codex','dsh'} else ['--approve-pi-project'] if host=='pi' else []
        def install(action):
            command = cli+[action,'-a',host,*scope]
            if action in {'add','update'}:
                command += ['--source','/input/package.tgz']
            return run('installer-'+action,command,input_data='y\ny\ny\n')
        if case != 'cold-reader':
            install('add')
            state = HOME/'.local/share/planweft' if host in {'codex','dsh'} else WORK/'.planweft'
            record = json.loads((state/'installations.json').read_text())['agents'][host]
            root = verify_files(host,package,record)
            # Continue from the verified persistent npm installation, which
            # includes declared runtime dependencies. The initial clean add
            # bootstraps that store from the unmodified exact tarball.
            cli = ['node', str(root/'bin/planweft.mjs')]
            if host == 'codex' and case in {'preflight', 'lifecycle'}:
                # These cases never inject authentication. Capture before
                # doctor so an installation failure does not lose its cause
                # when the isolated HOME tmpfs is removed.
                save('native-registration', codex_registration_projection(HOME/'.codex/config.toml'))
                run('native-marketplace-list', ['codex', 'plugin', 'marketplace', 'list', '--json'])
            install('doctor')
            native_load(host,root)
            result['exact_artifact'] = 'Passed'
        if case=='package-approval': result['native_package_approval']=pi_project_approval()
        if case not in {'preflight','lifecycle','package-approval'}:
            if not secret:
                raise RuntimeError('No isolated model authentication')
            if case not in {'readonly','simple','cold-reader','conflict','evidence-gap','gate-cap-disabled','gate-stall-disabled'}:
                os.environ.pop('PLANNING_DISABLED',None)
            if host=='pi' and case in {'context','recovery','continuation-limit','stopping'}:
                # DeepSeek defaults to cache-safe reminders, which deliberately
                # omit plan contents. This full-content probe explicitly tests
                # the supported parity mode without changing product defaults.
                os.environ['PWF_MODE']='auto' if case=='stopping' else 'parity'
            if case in {'gated-continuation','gate-cap','gate-stall','gate-cap-disabled','gate-stall-disabled'}:
                os.environ['PWF_GATE_CAP']='1' if case.startswith('gate-cap') else '20'
            prompt = payload['prompt']
            if case=='permission-denial':
                # Byte-identical script in a separate disposable directory:
                # a broken writer or unwritable filesystem cannot fake denial.
                with tempfile.TemporaryDirectory(prefix='pw-write-control-') as directory:
                    control=Path(directory)
                    shutil.copyfile(WORK/'write-probe.py',control/'write-probe.py')
                    shutil.copyfile(WORK/'protected.txt',control/'protected.txt')
                    run('native-write-control',['python3',str(control/'write-probe.py')])
                    result['synthetic_writer_works']=(control/'protected.txt').read_text()=='UNEXPECTED_WRITE\n'
                    if not result['synthetic_writer_works']: raise RuntimeError('Synthetic write control failed')
            if host=='opencode' and case=='permission-denial':
                config=HOME/'.config/opencode/opencode.json'
                selected=json.loads(config.read_text())
                selected['permission']={'bash':{'*':'allow','python3 /workspace/write-probe.py':'deny'}}
                config.write_text(json.dumps(selected))
                save('native-policy',{'mechanism':'OpenCode explicit bash deny','rules':selected['permission']})
            if host=='dsh' and case=='permission-denial':
                os.environ['DSH_PERMISSION_MODE']='read-only'
                patch=HOME/'.dsh/cordis.patch.yml'
                patch.write_text(patch.read_text()+'- id: approval\n  config:\n    policy: never\n'
                                 +'- id: permission\n  config:\n    defaultPreset: read-only\n    presets:\n      read-only:\n        sandbox: read-only\n        approval: never\n')
                save('native-policy',{'mechanism':'DSH fs-sandbox','mode':'read-only','approval_policy':'never',
                                      'scope':'native filesystem provider; not an OS shell sandbox'})
                run('native-denial-policy-boot',['dsh','--profile','headless','--help'])
            if host=='codex' and case=='permission-denial':
                rules=HOME/'.codex/rules';rules.mkdir(parents=True,exist_ok=True)
                rule=rules/'planweft-denial.rules'
                rule.write_text('prefix_rule(pattern=["python3", "/workspace/write-probe.py"], decision="forbidden", justification="PW_NATIVE_DENY: leave the sentinel unchanged")\n')
                policy=run('native-policy-check',['codex','execpolicy','check','--rules',str(rule),
                           '--','python3','/workspace/write-probe.py'])
                result['native_policy_loaded']=json.loads(policy.stdout).get('decision')=='forbidden'
                if not result['native_policy_loaded']: raise RuntimeError('Native execpolicy did not forbid the synthetic command')
            command, data = model_command(host,payload['model'],prompt,case)
            if host=='codex' and case in {'reminder-dedup','persisted-trust'}:
                command=['codex','--disable','memories','--disable','multi_agent','app-server']
            server_probe=host=='opencode' and case in {'stopping','gated-continuation','gate-cap','gate-stall','gate-cap-disabled','gate-stall-disabled'}
            if server_probe:
                command=['opencode','serve','--hostname','127.0.0.1','--port','0']
            traced=payload.get('trace_gate_processes',False)
            if traced:
                run('version-strace',['strace','--version'])
                spec=importlib.util.spec_from_file_location('gate_process_trace',Path(__file__).with_name('gate_process_trace.py'))
                tracer=importlib.util.module_from_spec(spec);spec.loader.exec_module(tracer)
                expected_gate_hash=hashlib.sha256((package/'dist'/host/'planweft/scripts/check-complete.sh').read_bytes()).hexdigest()
                command=['strace','-f','--decode-pids=comm','-s','4096','-e','trace='+tracer.TRACE_SYSCALLS,'-e','raw=read','-o','/tmp/planweft-gate.trace','--',*command]
            save('model-invocation',{'argv':command,'fresh_session':True,'case':case,
                'plugin_installed':case!='cold-reader','external_memory':'direct-provider; no MemoryProxy or identity headers',
                'transport':('three fresh native app-server probes; individual journals; stop after failure'
                             if host=='codex' and case=='persisted-trust'
                             else 'native server SSE; finite quiet window' if server_probe else 'native CLI'),
                'codex_hook_trust':'invocation bypass' if '--dangerously-bypass-hook-trust' in command else 'normal',
                'planning_disabled':os.environ.get('PLANNING_DISABLED')=='1'})
            if host=='pi': save('pi-mode',{'configured':os.environ.get('PWF_MODE','auto'),
                'default_deepseek_behavior':'cache-safe reminder; full plan content requires parity',
                'probe_scope':payload.get('probe_scope')})
            gate_watch=watch_gate_reads() if case in {'gate-cap','gate-stall','gate-cap-disabled','gate-stall-disabled'} else None
            try:
                if host=='codex' and case=='reminder-dedup':
                    from codex_reminder_probe import run_probe
                    native=Path(json.loads((OUT/'installed-content.json').read_text())['native_root'])
                    process,observation=run_probe(payload['model'],WORK,OUT,package,native,payload['timeout'],safe_text)
                    result['native_reminder_deduplication']=observation.get('status')=='Passed'
                    (OUT/'model.stdout').write_text(safe_text(process.stdout))
                    (OUT/'model.stderr').write_text(safe_text(process.stderr))
                    save('model',{'argv':command,'exit_code':process.returncode,
                        'stdout_format':'Agent messages projected from native app-server; full notifications in reminder-protocol.jsonl',
                        'completion':'two native turns in one thread; harness closes server afterward'})
                elif host=='claude' and case=='reminder-collection':
                    from claude_reminder_probe import run_probe
                    if payload.get('trace_reminder_processes'):run('version-strace',['strace','--version'])
                    native=Path(json.loads((OUT/'installed-content.json').read_text())['native_root'])
                    process,observation=run_probe(payload['model'],WORK,OUT,package,native,payload['timeout'],safe_text,
                        plan_dir=WORK,private_dir=Path('/tmp'),trace_hooks=payload.get('trace_reminder_processes',False))
                    save('model-invocation',{'argv':process.args,'fresh_session':True,'case':case,
                        'plugin_installed':True,'external_memory':'direct-provider; no MemoryProxy or identity headers',
                        'transport':'native stream-json; same process two serial turns',
                        'planning_disabled':os.environ.get('PLANNING_DISABLED')=='1','diagnostic_only':True})
                    result.update(reminder_collection=observation.get('collection_status'),
                        reminder_deduplication='Not Run',diagnostic_only=True)
                    for stream,suffix in [('stdout','native.stdout.jsonl'),('stderr','native.stderr')]:
                        source=OUT/('claude-reminder-'+suffix)
                        if source.is_file(): (OUT/('model.'+stream)).write_bytes(source.read_bytes())
                    save('model',{'argv':process.args,'exit_code':process.returncode,
                        'completion':'Diagnostic collection only; not reminder gate acceptance'})
                elif host=='codex' and case=='persisted-trust':
                    process,trust=codex_trusted_model(payload['model'],prompt,payload['timeout'])
                    result['native_persisted_trust']=all(trust[k] for k in ['before_no_context','after_context','fresh_context','no_tool_reads','distinct_threads','distinct_processes'])
                    result['trust_recovery_token']=trust['new_owner_token']
                elif host=='pi' and case in {'context','recovery','continuation-limit','stopping'}:
                    process=pi_model(payload['model'],prompt,payload['timeout'],activate=case!='stopping')
                elif server_probe:
                    spec=importlib.util.spec_from_file_location('opencode_server_probe',Path(__file__).with_name('opencode_server_probe.py'))
                    probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
                    process=probe.run_probe('release/'+payload['model'],prompt,payload['timeout'],WORK,OUT,case)
                    save('native-server-observation',process.evidence)
                    (OUT/'model.stdout').write_text(safe_text(process.stdout))
                    (OUT/'model.stderr').write_text(safe_text(process.stderr))
                    save('model',{'argv':command,'exit_code':process.returncode,
                        'completion':'finite native SSE/message observation; harness shuts down server',
                        'seconds':process.evidence['seconds'],'stdout_format':'projection of native stored message parts; original messages/SSE in native-server-observation.json'})
                else:
                    process = run('model',command,input_data=data,timeout=payload['timeout'],required=False)
            finally:
                if gate_watch:
                    observed=finish_gate_reads(gate_watch);save('native-gate-reads',observed)
                    observed_files={e['file'] for e in observed['events']}
                    result['any_gate_counter_access']=bool(observed_files) or observed['overflow']
                    result['gate_counters_read']=not observed['overflow'] and observed_files=={'.stop_blocks','.gate_last_ledger'}
                if traced and Path('/tmp/planweft-gate.trace').is_file():
                    raw=Path('/tmp/planweft-gate.trace').read_text()
                    attributed=tracer.attributed_gate_reads(raw,expected_gate_hash);save('native-gate-processes',attributed)
                    # Keep raw argv private in container tmpfs. Only the
                    # allowlisted process/counter projection and source digest
                    # are exported; credentials are never an output argument.
                    result['gate_trace_complete']=attributed['trace_complete']
                    result['attributed_gate_reads']=attributed['trace_complete'] and attributed['attributed_files']==['.gate_last_ledger','.stop_blocks']
                    result['any_attributed_gate_reads']=bool(attributed['attributed_files'])
            if host=='dsh':
                logs=list((HOME/'.dsh/sessions').rglob('*.jsonl'))
                content='\n'.join(p.read_text() for p in sorted(logs))
                (OUT/'native-events.jsonl').write_text(safe_text(content))
                result['native_session_logs']=len(logs)
                if case=='permission-denial':
                    result['native_permission_denied']=native_dsh_denial(content)
                    result['native_policy_loaded']=result['native_permission_denied']
            if host=='claude' and Path('/tmp/planweft-native-hooks.log').is_file():
                (OUT/'native-hooks.log').write_text(safe_text(Path('/tmp/planweft-native-hooks.log').read_text()))
            result['model_session'] = 'Passed' if process.returncode == 0 else 'Failed'
            if host=='codex' and case=='permission-denial':
                rollouts=[]
                for path in (HOME/'.codex/sessions').rglob('*.jsonl'):
                    text=path.read_text();records=codex_denial_records(text)
                    rollouts.append({'source_sha256':hashlib.sha256(text.encode()).hexdigest(),
                                     'source_bytes':len(text.encode()),'matched_native_records':records,
                                     'native_tool_records':codex_tool_records(text)})
                save('native-permission-rollout',{'kind':'new isolated synthetic session call/result projection',
                                                  'sources':rollouts})
                result['native_permission_denied']=any(r['matched_native_records'] for r in rollouts)
            if host in {'claude','opencode'} and case=='permission-denial':
                result['native_permission_denied']=native_rule_denial(host,process.stdout)
                result['native_policy_loaded']=result['native_permission_denied']
            if process.returncode:
                raise RuntimeError('Real model process failed')
            if case == 'maintenance':
                tests = run('offline-tests',['python3','-m','unittest','discover','-s','tests','-v'],required=False)
                effectiveness=regression_effectiveness(WORK,tests)
                save('regression-effectiveness',effectiveness)
                result['offline_tests']=effectiveness['status']
                check='''from pathlib import Path
import tempfile
from export_text import write_export
with tempfile.TemporaryDirectory() as temporary:
    for text in ["", "示例", "line\\nnext"]:
        path=Path(temporary)/"中文 with space.txt"
        write_export(text,path)
        assert path.read_bytes()==text.encode("utf-8"), "Export bytes violate approved contract"
print("Independent byte checks Passed")
'''
                actual=run('independent-byte-checks',['python3','-c',check],required=False)
                result['independent_bytes']='Passed' if actual.returncode==0 else 'Failed'
        if case == 'lifecycle':
            install('update')
            verify_files(host,package,record)
        if case != 'cold-reader':
            install('remove')
            if host in json.loads((state/'installations.json').read_text()).get('agents',{}):
                raise RuntimeError('Installer registration survived removal')
            if host in {'codex','claude'}:
                listing=run('native-removed',[host,'plugin','list','--json']).stdout
                if 'planweft' in listing: raise RuntimeError('Native registration survived removal')
            elif host=='pi':
                if 'planweft' in run('native-removed',['pi','list','--approve']).stdout:
                    raise RuntimeError('Pi registration survived removal')
            elif host=='dsh':
                profile=json.loads((HOME/'.dsh/profiles/headless/package.json').read_text())
                if 'planweft' in profile.get('dsh',{}).get('profile',{}).get('bundles',[]):
                    raise RuntimeError('DSH bundle survived removal')
            elif (WORK/'.opencode/plugins/planweft.ts').exists() or (WORK/'.opencode/skills/project-docs').exists():
                raise RuntimeError('OpenCode loader/Skill survived removal')
            result['uninstall'] = 'Passed'
        result['status'] = 'Passed'
    except Exception as error:
        result['error'] = str(error)
    finally:
        result['credential_redactions']=REDACTIONS
        if REDACTIONS:
            result['status']='Failed';result['error']='Credential appeared in native output; redacted; requires safety review'
        save('controller', result)
    return 0 if result['status']=='Passed' else 1
