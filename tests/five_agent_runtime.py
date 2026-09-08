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
import shutil
import subprocess
import struct
import tarfile
import tempfile
import threading
import time

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
    checked = 0
    for name, expected in manifest['files'].items():
        for base in {native, expected_root}:
            p = base/name
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected['sha256']:
                raise RuntimeError('Installed content differs: '+name)
            if bool(p.stat().st_mode & 0o111) != expected['executable']:
                raise RuntimeError('Installed executable bit differs: '+name)
        checked += 1
    save('installed-content', {'status':'Passed','files_checked':checked,'native_root':str(native),
                              'package_root':str(root),'version':record['version']})
    return root


def model_command(host, model, prompt, case):
    if host == 'codex':
        command = ['codex','exec','--ephemeral','--json','--skip-git-repo-check',
            '--sandbox','danger-full-access','--model',model,'--disable','memories',
            '--disable','multi_agent','--cd',str(WORK)]
        if case == 'cold-reader':
            command += ['--disable', 'plugins']
        # This separate lane is explicitly not normal persisted trust acceptance.
        if case not in {'untrusted','cold-reader','readonly','simple'}:
            command += ['--dangerously-bypass-hook-trust']
        return command+['-'], prompt
    if host == 'claude':
        command=['claude','-p','--no-session-persistence','--permission-mode','acceptEdits',
                '--allowedTools','Read,Edit,Write,Bash,Glob,Grep,Skill',
                '--model',model,'--output-format','stream-json','--verbose']
        if case in {'stopping','gated-continuation','gate-cap','gate-stall','gate-cap-disabled','gate-stall-disabled'}:
            command+=['--debug','hooks','--debug-file','/tmp/planweft-native-hooks.log']
        return command, prompt
    if host == 'pi':
        return ['pi','--print','--no-session','--approve','--provider','release',
                '--model',model,'--mode','json',prompt], None
    if host == 'opencode':
        return ['opencode','run','--auto','--format','json','--model','release/'+model,prompt], None
    return ['dsh','--profile','headless',prompt], None


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


def controller(payload):
    global SECRETS
    SECRETS=secret_values(payload.get('secret',{}))
    setup_environment()
    host, case = payload['host'], payload['case']
    result = {'host':host,'case':case,'status':'Failed','model_session':'Not Run'}
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
            install('doctor')
            native_load(host,root)
            result['exact_artifact'] = 'Passed'
        if case not in {'preflight','lifecycle'}:
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
            command, data = model_command(host,payload['model'],prompt,case)
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
                'transport':'native server SSE; finite quiet window' if server_probe else 'native CLI',
                'codex_hook_trust':'invocation bypass' if '--dangerously-bypass-hook-trust' in command else 'normal',
                'planning_disabled':os.environ.get('PLANNING_DISABLED')=='1'})
            if host=='pi': save('pi-mode',{'configured':os.environ.get('PWF_MODE','auto'),
                'default_deepseek_behavior':'cache-safe reminder; full plan content requires parity'})
            gate_watch=watch_gate_reads() if case in {'gate-cap','gate-stall','gate-cap-disabled','gate-stall-disabled'} else None
            try:
                if host=='pi' and case in {'context','recovery','continuation-limit','stopping'}:
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
            if host=='claude' and Path('/tmp/planweft-native-hooks.log').is_file():
                (OUT/'native-hooks.log').write_text(safe_text(Path('/tmp/planweft-native-hooks.log').read_text()))
            result['model_session'] = 'Passed' if process.returncode == 0 else 'Failed'
            if process.returncode:
                raise RuntimeError('Real model process failed')
            if case == 'maintenance':
                tests = run('offline-tests',['python3','-m','unittest','discover','-s','tests','-v'],required=False)
                import re
                count=re.search(r'Ran (\d+) tests?',tests.stderr+tests.stdout)
                result['offline_tests'] = 'Passed' if tests.returncode==0 and count and int(count.group(1))>=2 else 'Failed'
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
