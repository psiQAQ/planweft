"""Bounded same-process Claude stream-json reminder *collection*, not a gate.

PostToolUse empty-output/debug correlation has not been established on the
pinned CLI. A complete collection therefore returns status=Not Run, never
Passed for reminder delivery/deduplication. Only collection_status may Passed.
No authentication is read here; the caller supplies an already isolated host.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import stat
import shutil
import subprocess
import tempfile
import time
import uuid

PREFIX='claude-reminder-'
FILES={'stdout':'native.stdout.jsonl','stderr':'native.stderr','debug':'hooks.log',
       'sent':'sent.jsonl','trace':'trace-observation.json','report':'observation.json'}
DEFAULT_LIMITS={'stdout':16*1024**2,'stderr':8*1024**2,'debug':8*1024**2,'line':1024**2,'total':48*1024**2}
TRACE_LIMIT=16*1024**2
TRACE_METADATA_LIMIT=256*1024
RESOURCES=['.claude-plugin/plugin.json','hooks/hooks.json','hooks/claude-hook.sh',
           'scripts/inject-plan.py','scripts/inject-plan.sh']


class ObservationGap(RuntimeError):
    """The pinned native protocol did not provide required observation data."""


def hashed(data):return hashlib.sha256(data).hexdigest()


def file_hash(path):
    result=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(65536),b''):result.update(chunk)
    return result.hexdigest()


def targets(work,label):
    return [(work/f'reminder-{label.lower()}-{index}.txt',f'{label}-{index}\n') for index in [1,2]]


def prompt(work,label):
    first,second=targets(work,label)
    return (f'这是已授权的原生提醒采集回合 {label}。仅通过两次独立、串行 Write 新建文件：'
            f'先写 {first[0]}，内容为 {json.dumps(first[1])}；收到成功工具结果后再写 {second[0]}，'
            f'内容为 {json.dumps(second[1])}。不要合并或并发调用，不使用 Read/Edit/Bash 或其他工具。'
            '除此之外不读写任何项目文件，不修改完成态计划，不手动调用 hooks，不读写宿主设置、'
            '凭据、历史或私有缓存，不清理 marker。工具失败即报告失败，不绕过或重试。'
            f'两次均成功后只回复 DONE_{label}。')


class Protocol:
    """Incremental actual tool pairing; never count debug strings as delivery."""
    def __init__(self,work,model,version,native_root):
        self.model=model;self.version=version
        self.native_root=str(native_root)
        self.work=work;self.sequence=0;self.session=None;self.current=None
        self.sent=[];self.rows=[];self.pending=None;self.tool_ids=set();self.turns=[]
        self.echoes=[];self.hooks=[];self.initializations={};self.init_metadata=None;self.finished=False
        self.answer_after_tools=False;self.commands={};self.command_events=[]

    def send(self,label,debug_offset):
        if (label not in ['A','B'] or len(self.sent)!=(0 if label=='A' else 1)
                or self.current is not None or (label=='B' and len(self.turns)!=1)):
            raise ValueError('Cannot queue B before successful A completion')
        request={'type':'user','uuid':str(uuid.uuid4()),'message':{'role':'user','content':prompt(self.work,label)},
                 'parent_tool_use_id':None}
        if self.session:request['session_id']=self.session
        row={'label':label,'request':request,'sent_after_stdout_sequence':self.sequence,
             'debug_native_bytes_at_send':debug_offset,
             'debug_offset_scope':'Private native file size before redaction, not an exported-byte offset or delivery correlation'}
        self.sent.append(row);self.current=label;self.answer_after_tools=False
        return row

    def accept(self,event):
        self.sequence+=1
        if not isinstance(event,dict):raise ValueError('Native event is not an object')
        if event.get('parent_tool_use_id') is not None:raise ValueError('Nested agent activity is outside this probe')
        session=event.get('session_id')
        if session:
            if self.session and self.session!=session:raise ValueError('Session identity changed')
            self.session=session
        kind=event.get('type');subtype=event.get('subtype','')
        if kind=='command_lifecycle':
            selected=[r for r in self.sent if r['request']['uuid']==event.get('command_uuid')]
            if len(selected)!=1 or not session:raise ObservationGap('Command lifecycle is not bound to a sent user request')
            label=selected[0]['label'];state=event.get('state');previous=self.commands.get(label)
            if state!={None:'queued','queued':'started','started':'completed'}.get(previous):
                raise ValueError('Repeated, incomplete or reordered command lifecycle')
            if state=='started' and (label!=self.current or (label=='B' and self.commands.get('A')!='completed')):
                raise ValueError('Command started outside its serial user turn')
            if state=='completed' and not any(t['label']==label for t in self.turns):
                raise ValueError('Command completed before successful result')
            self.commands[label]=state
            self.command_events.append({'label':label,'command_uuid':event['command_uuid'],'state':state,'sequence':self.sequence})
            return
        if kind=='system':
            if 'compact' in subtype.lower() or any(x in str(event.get('hook_event','')).lower() for x in ['compact','clear','resume']):
                raise ValueError('Compaction/reset cannot prove user-turn rearm')
            if subtype=='init':
                # Pinned Claude resends identical init metadata for each
                # stdin user request, without restarting SessionStart.
                if (self.current is None or self.current in self.initializations or self.pending is not None
                        or any(r['turn']==self.current for r in self.rows)):
                    raise ValueError('Repeated/late native initialization within a user turn')
                if self.commands.get(self.current)!='started':
                    raise ObservationGap('Initialization lacks native started request binding')
                required={'cwd':str,'model':str,'permissionMode':str,'claude_code_version':str,
                          'tools':list,'mcp_servers':list,'plugins':list,'skills':list}
                if any(not isinstance(event.get(k),kind) for k,kind in required.items()):
                    raise ObservationGap('Native initialization metadata is incomplete')
                if (event['cwd']!=str(self.work) or event['model']!=self.model
                        or event['permissionMode']!='acceptEdits' or event['claude_code_version']!='2.1.241'
                        or 'Write' not in event['tools'] or event['mcp_servers']):
                    raise ValueError('Native initial model, scope or capabilities differ')
                plugins=event['plugins']
                if (len(plugins)!=1 or not isinstance(plugins[0],dict)
                        or plugins[0].get('name')!='planweft' or plugins[0].get('version')!=self.version
                        or plugins[0].get('path')!=self.native_root
                        or event['skills'].count('planweft:project-docs')!=1):
                    raise ValueError('Native plugin/Skill identity differs or is duplicated')
                metadata={k:v for k,v in event.items() if k!='uuid'}
                if self.init_metadata is not None and metadata!=self.init_metadata:
                    raise ValueError('Native initialization metadata changed between user turns')
                self.init_metadata=metadata
                self.initializations[self.current]={'sequence':self.sequence,'session_id':self.session}
            if subtype in ['hook_started','hook_response']:
                if event.get('hook_event')=='SessionStart' and (self.rows or len(self.sent)>1):
                    raise ValueError('SessionStart after initial activity')
                if len(self.hooks)>=32:raise ObservationGap('Hook metadata budget exceeded; inspect retained raw stream')
                self.hooks.append({'sequence':self.sequence,'subtype':subtype,
                    **{k:event.get(k) for k in ['hook_id','hook_name','hook_event','exit_code','outcome']}})
            return
        if kind in ['assistant','user','result'] and not session:
            raise ObservationGap('Native message lacks session binding')
        if kind=='assistant':
            if self.current is None:raise ValueError('Assistant activity outside an active user turn')
            for block in event.get('message',{}).get('content',[]):
                if block.get('type')=='tool_use':
                    expected=targets(self.work,self.current)
                    count=sum(row['turn']==self.current for row in self.rows)
                    if (block.get('name')!='Write' or self.pending is not None or count>=2
                            or len(self.rows)>=4 or not block.get('id') or block['id'] in self.tool_ids):
                        raise ValueError('Unexpected, concurrent, duplicate or excess native tool call')
                    params=block.get('input',{})
                    if params.get('file_path')!=str(expected[count][0]) or params.get('content')!=expected[count][1]:
                        raise ValueError('Write target/content differs from this synthetic turn')
                    self.tool_ids.add(block['id'])
                    self.pending={'turn':self.current,'tool_id':block['id'],'path':params['file_path'],
                                  'content':params['content'],'call_sequence':self.sequence}
                elif block.get('type')=='text' and block.get('text'):
                    if self.pending is None and sum(row['turn']==self.current for row in self.rows)==2:
                        self.answer_after_tools=True
            return
        if kind=='user':
            blocks=event.get('message',{}).get('content',[])
            results=[b for b in blocks if isinstance(b,dict) and b.get('type')=='tool_result'] if isinstance(blocks,list) else []
            if results:
                if len(results)!=1 or self.pending is None:raise ValueError('Unpaired/combined native tool results')
                result=results[0]
                if result.get('tool_use_id')!=self.pending['tool_id']:raise ValueError('Tool result id differs')
                if result.get('is_error') is True:raise ValueError('Native Write failed')
                native=event.get('tool_use_result')
                if not isinstance(native,dict) or not all(native.get(key)==self.pending[value] for key,value in [('filePath','path'),('content','content')]):
                    raise ObservationGap('Native successful Write metadata unavailable or unbound')
                if native.get('type') not in ['create','update']:raise ObservationGap('Unrecognized native Write outcome')
                path=Path(self.pending['path'])
                if path.is_symlink() or not path.is_file() or path.read_bytes()!=self.pending['content'].encode():
                    raise ValueError('Native Write result does not match actual synthetic file')
                self.rows.append({**self.pending,'result_sequence':self.sequence,'native_type':native['type'],
                                  'file_sha256':hashed(path.read_bytes())})
                self.pending=None
            elif event.get('isReplay') is True:
                candidates=[r for r in self.sent if r['request']['uuid']==event.get('uuid')]
                if len(candidates)!=1 or event.get('message')!=candidates[0]['request']['message']:
                    raise ObservationGap('Native input replay UUID/content did not bind sent journal')
                self.echoes.append({'label':candidates[0]['label'],'sequence':self.sequence,'uuid':event['uuid']})
            # Skill/system synthetic user messages are kept verbatim in the raw
            # stream. They are not counted as input echoes or successful tools.
            return
        if kind=='result':
            if (self.current is None or subtype!='success' or event.get('is_error') is not False
                    or not self.session or self.pending is not None
                    or sum(row['turn']==self.current for row in self.rows)!=2):
                raise ValueError('Failed, incomplete or duplicate native user result')
            if self.current not in self.initializations:raise ObservationGap('No native initialization metadata for user turn')
            if not self.answer_after_tools:raise ObservationGap('No actual assistant response after the two successful Writes')
            self.turns.append({'label':self.current,'result_sequence':self.sequence,'session_id':self.session,
                               'uuid':event.get('uuid'),'subtype':subtype})
            self.current=None;self.finished=len(self.turns)==2
        elif kind=='error':raise ValueError('Native error event')


def stop_owned(process,grace=1):
    """The child creates its own session/group; signal only that recorded group."""
    if process is None:return {'started':False}
    result={'pid':process.pid,'signals':[]}
    try:
        if process.stdin and not process.stdin.closed:process.stdin.close()
    except (OSError,BrokenPipeError):pass
    if process.poll() is None:
        try:process.wait(timeout=grace)
        except subprocess.TimeoutExpired:pass
    # Also terminate any remaining members of the created group when its
    # leader exited early. Never use a name-based kill or the caller's group.
    if process.pid==os.getpgrp():raise RuntimeError('Refusing to signal caller process group')
    for sig in [signal.SIGTERM,signal.SIGKILL]:
        try:os.killpg(process.pid,sig);result['signals'].append(sig.name)
        except ProcessLookupError:break
        if process.poll() is None:
            try:process.wait(timeout=grace)
            except subprocess.TimeoutExpired:continue
    process.wait(timeout=grace)
    result['exit_code']=process.returncode
    return result


def clean_private_tree(directory,parent,identity):
    """Delete only the exact private directory created by this invocation."""
    if directory.parent!=parent or not shutil.rmtree.avoids_symlink_attacks:
        raise OSError('Safe private directory cleanup unavailable')
    fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        current=os.stat(directory.name,dir_fd=fd,follow_symlinks=False)
        if not stat.S_ISDIR(current.st_mode) or (current.st_dev,current.st_ino,current.st_uid)!=identity:
            raise OSError('Private debug directory identity changed')
        shutil.rmtree(directory.name,dir_fd=fd)
        try:os.stat(directory.name,dir_fd=fd,follow_symlinks=False)
        except FileNotFoundError:return
        raise OSError('Private debug directory remains')
    finally:os.close(fd)


def validate(model,work,out,package,native_root,plan_dir,private_dir,timeout,limits):
    if not isinstance(model,str) or not model or len(model)>256 or any(c in model for c in '\n\r\0'):raise ValueError('Invalid model')
    if type(timeout) not in [int,float] or not 0<timeout<=600:raise ValueError('Timeout must be positive and <=600 seconds')
    if set(limits)!=set(DEFAULT_LIMITS) or any(type(v) is not int or not 128<=v<=DEFAULT_LIMITS[k] for k,v in limits.items()):
        raise ValueError('Invalid bounded output limits')
    if limits['total']<128*1024:raise ValueError('Total budget must reserve 64 KiB for evidence metadata')
    if not private_dir.is_dir() or private_dir==out or out in private_dir.parents or private_dir==work or work in private_dir.parents:
        raise ValueError('Private debug parent must exist outside project/evidence')
    if not work.is_dir() or not package.is_dir() or not native_root.is_dir():raise ValueError('Missing isolated project/package/native root')
    if plan_dir!=work and work not in plan_dir.parents:raise ValueError('Plan must belong to the authorized project')
    if out==work or work in out.parents:raise ValueError('Evidence must stay outside the project')
    if out.is_symlink():raise ValueError('Evidence directory must not be a symlink')
    for suffix in FILES.values():
        p=out/(PREFIX+suffix)
        if p.exists() or p.is_symlink():raise ValueError('Probe evidence output must be new')
    protected={}
    for name in ['task_plan.md','findings.md','progress.md']:
        p=plan_dir/name
        if p.is_symlink() or not p.is_file() or p.stat().st_size>512*1024:raise ValueError('Missing/unsafe planning record')
        protected[p]=p.read_bytes()
    statuses=re.findall(r'^\s*-?\s*\*\*Status:\*\*\s*(\w+)\s*$',protected[plan_dir/'task_plan.md'].decode(),re.M)
    if not statuses or any(status!='complete' for status in statuses):raise ValueError('Fixture plan must already be complete')
    for label in ['A','B']:
        if any(p.exists() or p.is_symlink() for p,_ in targets(work,label)):raise ValueError('Synthetic Write targets must not exist')
    resources={}
    for relative in RESOURCES:
        expected=package/'dist/claude/planweft'/relative;actual=native_root/relative
        if not actual.is_file() or actual.read_bytes()!=expected.read_bytes():raise ValueError('Installed Claude hook resource differs: '+relative)
        resources[relative]=hashed(actual.read_bytes())
    manifest=json.loads((native_root/'hooks/hooks.json').read_text())
    handlers=manifest.get('hooks',{}).get('PostToolUse',[])
    if (len(handlers)!=1 or handlers[0].get('matcher')!='Write|Edit'
            or len(handlers[0].get('hooks',[]))!=1):raise ValueError('Expected one package-owned Write/Edit dispatcher')
    return protected,resources



def native_executable_identity():
    """Bind executables in the caller's fixed, read-only image, not basenames."""
    host=shutil.which('claude')
    if not host or not Path(host).is_absolute():raise ValueError('Missing native Claude executable')
    allowed={'shell':[], 'python':[]}
    hashes={host:file_hash(Path(host))}
    for category,names in [('shell',['sh','dash','bash']),('python',['python3','python'])]:
        for name in names:
            located=shutil.which(name)
            if not located or not Path(located).is_absolute():continue
            executable=Path(located)
            # Native launchers may use /bin while PATH lists /usr/bin. Only
            # include aliases proven to refer to the same installed file.
            candidates=[executable,executable.resolve(strict=True)]
            for directory in ['/bin','/usr/bin','/usr/local/bin']:
                alias=Path(directory)/name
                if alias.is_file() and alias.samefile(executable):candidates.append(alias)
            for candidate in candidates:
                value=str(candidate)
                if value not in allowed[category]:
                    allowed[category].append(value);hashes[value]=file_hash(candidate)
    if not all(allowed.values()):raise ValueError('Missing fixed-image hook interpreter')
    return host,allowed,hashes


def run_probe(model,work,out,package,native_root,timeout,sanitize,*,plan_dir,private_dir,limits=None,trace_hooks=False):
    """Return (CompletedProcess, evidence); rc0 means collection, NOT dedup Passed.

    Caller supplies existing isolated host auth/config; this function neither
    reads auth nor installs/enables plugins. ``out`` is a results directory;
    every claude-reminder-* output must be new. All native logs are bounded and
    sanitized, including the CLI-created debug file. Environment is inherited
    with only verbose debug level added; no model route or trust change.
    ``private_dir`` must be a caller-owned isolated tmpfs/private directory.
    Native debug is created there and sanitized into out only after shutdown.
    """
    work=Path(work).resolve();out_input=Path(out);out=out_input.resolve()
    if out_input.is_symlink():raise ValueError('Evidence directory must not be a symlink')
    package=Path(package).resolve();native_root=Path(native_root).resolve();plan_dir=Path(plan_dir).resolve();private_dir=Path(private_dir).resolve()
    limits={**DEFAULT_LIMITS} if limits is None else dict(limits)
    if not callable(sanitize):raise ValueError('sanitize callback required')
    if type(trace_hooks) is not bool:raise ValueError('trace_hooks must be boolean')
    protected,resources=validate(model,work,out,package,native_root,plan_dir,private_dir,timeout,limits)
    executable_identity=native_executable_identity() if trace_hooks else None
    out.mkdir(parents=True,exist_ok=True)
    paths={key:out/(PREFIX+name) for key,name in FILES.items()}
    command=['claude','-p','--no-session-persistence','--permission-mode','acceptEdits',
             '--allowedTools','Read,Edit,Write,Bash,Glob,Grep,Skill','--model',model,
             '--output-format','stream-json','--verbose','--input-format','stream-json',
             '--replay-user-messages']
    version=json.loads((native_root/'.claude-plugin/plugin.json').read_text())['version']
    protocol=Protocol(work,model,version,native_root);process=None;deadline=time.monotonic()+timeout
    evidence={'status':'Not Run','collection_status':'In Progress','reminder_deduplication':'Not Run',
              'reason':'Pinned Claude PostToolUse empty-output/handler-to-tool debug correlation remains unvalidated; raw collection only.',
              'command':command,'timeout_seconds':timeout,'output_limits':limits,'resource_sha256':resources,
              'native_root':str(native_root),
              'plan_before_sha256':{str(p.relative_to(work)):hashed(v) for p,v in protected.items()},
              'diagnostic_only':True,'same_process':True,'model_route_changed':False,'trust_changed':False,
              'private_process_trace_requested':trace_hooks}
    if executable_identity:
        evidence['executable_sha256']=executable_identity[2]
    privacy_errors=[]
    def redact(text):
        try:
            value=sanitize(text)
            if not isinstance(value,str):raise TypeError('Redactor must return text')
            return value
        except Exception as error:
            privacy_errors.append(type(error).__name__)
            return '[redaction failed; content omitted]\n'
    sizes={'stdout':0,'stderr':0};buffers={'stdout':b'','stderr':b''};handles={};truncated=[];debug_parent=None;debug_path=None;debug_identity=None;debug_parent_fd=None;debug_fd=None;debug_file_identity=None
    trace_fd=None;trace_path=None;trace_identity=None
    def checked_private_size(descriptor,path,identity):
        if descriptor is None or debug_parent_fd is None:raise OSError('Private descriptor missing')
        directory=debug_parent.lstat()
        if (not stat.S_ISDIR(directory.st_mode)
                or (directory.st_dev,directory.st_ino,directory.st_uid)!=debug_identity):
            raise OSError('Private debug directory identity changed')
        named=os.stat(path.name,dir_fd=debug_parent_fd,follow_symlinks=False)
        opened=os.fstat(descriptor)
        if (not stat.S_ISREG(named.st_mode) or not stat.S_ISREG(opened.st_mode)
                or (named.st_dev,named.st_ino,named.st_uid)!=identity
                or (opened.st_dev,opened.st_ino,opened.st_uid)!=identity):
            raise OSError('Private file identity changed')
        return opened.st_size
    def checked_debug_size():return checked_private_size(debug_fd,debug_path,debug_file_identity)
    def debug_size():
        size=checked_debug_size()
        if size>limits['debug']:raise RuntimeError('Bounded debug output exceeded')
        trace_size=checked_private_size(trace_fd,trace_path,trace_identity) if trace_fd is not None else 0
        if trace_size>TRACE_LIMIT:raise RuntimeError('Bounded private process trace exceeded')
        if size+trace_size+sum(sizes.values())>limits['total']-65536:raise RuntimeError('Total native output budget exceeded')
        return size
    def write_log(key,text):
        value=redact(text);count=len(value.encode())
        cap=limits[key] if key in ['stdout','stderr'] else 16384
        used=sum(os.fstat(h.fileno()).st_size for h in handles.values() if not h.closed)
        if os.fstat(handles[key].fileno()).st_size+count>cap or used+count>limits['total']-65536:
            raise RuntimeError('Sanitized native output budget exceeded')
        handles[key].write(value);handles[key].flush()
        if privacy_errors:raise RuntimeError('Native output redaction failed')
    def unchanged():
        try:return all(p.is_file() and not p.is_symlink() and p.read_bytes()==v for p,v in protected.items())
        except OSError:return False
    def send(label):
        row=protocol.send(label,debug_size())
        write_log('sent',json.dumps(row,ensure_ascii=False)+'\n')
        process.stdin.write((json.dumps(row['request'],ensure_ascii=False)+'\n').encode());process.stdin.flush()
    def lines(key,chunk):
        sizes[key]+=len(chunk)
        debug_size()
        if sizes[key]>limits[key]:
            remaining=max(0,limits[key]-(sizes[key]-len(chunk)));chunk=chunk[:remaining]
            truncated.append(key)
        buffers[key]+=chunk
        while b'\n' in buffers[key]:
            raw,buffers[key]=buffers[key].split(b'\n',1)
            if len(raw)>limits['line']:raise RuntimeError('Bounded native line exceeded')
            text=raw.decode('utf-8',errors='strict' if key=='stdout' else 'replace')
            write_log(key,text+'\n')
            if key=='stdout':protocol.accept(json.loads(text))
        if len(buffers[key])>limits['line']:raise RuntimeError('Bounded native line exceeded')
        if truncated:raise RuntimeError('Bounded native '+key+' output exceeded')
    def export_private_trace():
        from claude_hook_trace import analyze_trace
        debug_size()
        with os.fdopen(os.dup(trace_fd),'rb') as source:
            source.seek(0);raw=source.read(TRACE_LIMIT+1)
        if not raw or not raw.endswith(b'\n') or len(raw)>TRACE_LIMIT:
            raise RuntimeError('Incomplete/bounded private process trace; nothing exported')
        text=raw.decode('utf-8',errors='strict')
        # The existing caller knows the injected secrets. A
        # redaction change is a failure, not a sanitized pass.
        if redact(text)!=text or privacy_errors:
            raise RuntimeError('Private trace required redaction; nothing exported')
        observed=analyze_trace(text,native_root,resources,max_bytes=TRACE_LIMIT,
                               expected_host_executable=executable_identity[0],allowed_interpreters=executable_identity[1])
        rendered_trace=json.dumps(observed,ensure_ascii=False,indent=2)+'\n'
        # The frozen seven-hook native preflight already needs about 47 KiB
        # to retain every script read and EOF. Keep a separate bounded budget
        # instead of dropping provenance to fit the short summary limit.
        already_written=sum(path.stat().st_size for key,path in paths.items()
                            if key not in ['trace','report'] and path.exists() and not path.is_symlink())
        metadata_budget=max(0,min(TRACE_METADATA_LIMIT,limits['total']-65536-already_written))
        if len(rendered_trace.encode())>metadata_budget:
            raise RuntimeError('Trace observation metadata budget exceeded')
        with paths['trace'].open('x',encoding='utf-8') as target:
            target.write(redact(rendered_trace))
        evidence['hook_process_observation_complete']=observed.get('observation_complete') is True
        # Complete output attribution alone is not delivery or
        # dedup acceptance; native tool/context pairing remains.
        del raw,text,observed,rendered_trace
    try:
        for key in ['stdout','stderr','sent']:handles[key]=paths[key].open('x',encoding='utf-8')
        debug_parent=Path(tempfile.mkdtemp(prefix='planweft-claude-reminder-',dir=private_dir))
        created=debug_parent.stat();debug_identity=(created.st_dev,created.st_ino,created.st_uid)
        debug_parent_fd=os.open(debug_parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        debug_path=debug_parent/'native-debug.log'
        debug_fd=os.open(debug_path.name,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=debug_parent_fd)
        created_file=os.fstat(debug_fd);debug_file_identity=(created_file.st_dev,created_file.st_ino,created_file.st_uid)
        command+=['--debug-file',str(debug_path)]
        if trace_hooks:
            from claude_hook_trace import TRACE_SYSCALLS,RAW_SYSCALLS
            trace_path=debug_parent/'native-process.trace'
            trace_fd=os.open(trace_path.name,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=debug_parent_fd)
            trace_stat=os.fstat(trace_fd);trace_identity=(trace_stat.st_dev,trace_stat.st_ino,trace_stat.st_uid)
            # raw=... records counts/pointers, never data buffers. Do not add
            # strace read=/write= dumps; argv is private execution identity.
            command=['strace','-f','-ttt','--decode-pids=comm','-s','4096',
                     '-e','trace='+TRACE_SYSCALLS,'-e','raw='+RAW_SYSCALLS,
                     '-o',str(trace_path),'--',*command]
            evidence['command']=command
        process=subprocess.Popen(command,cwd=work,env={**os.environ,'CLAUDE_CODE_DEBUG_LOG_LEVEL':'verbose'},
                                 stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        send('A');streams={process.stdout:'stdout',process.stderr:'stderr'};stdin_closed=False
        while streams:
            if time.monotonic()>=deadline:raise TimeoutError('Claude reminder collection exceeded deadline')
            debug_size()
            ready,_,_=select.select(list(streams),[],[],min(.1,max(0,deadline-time.monotonic())))
            for stream in ready:
                data=os.read(stream.fileno(),65536)
                if not data:
                    key=streams.pop(stream)
                    if buffers[key]:
                        if key=='stdout':
                            buffers[key]=b''
                            write_log(key,'[incomplete native JSONL record omitted]\n')
                            raise ValueError('Truncated native JSONL record')
                        buffers[key]=b''
                        write_log(key,'[incomplete native stderr tail omitted]\n')
                        raise ValueError('Incomplete native stderr tail')
                    continue
                lines(streams[stream],data)
            # Process every record already returned in the current read batch.
            # Never queue B before A result AND both actual Writes are verified.
            if len(protocol.turns)==1 and len(protocol.sent)==1:
                if not unchanged():raise ValueError('Completed source plan records changed before B')
                send('B')
            if protocol.finished and not stdin_closed:
                process.stdin.close();stdin_closed=True
        process.wait(timeout=max(.01,deadline-time.monotonic()))
        if process.returncode!=0 or not protocol.finished:raise ValueError('Early/nonzero Claude process exit or missing result')
        if protocol.commands!={'A':'completed','B':'completed'}:raise ObservationGap('Missing complete native command lifecycles')
        if not unchanged():
            raise ValueError('Completed source plan records changed')
        if not debug_size():raise ObservationGap('Native debug file is empty; cannot declare collection complete')
        evidence['collection_status']='Passed'
    except ObservationGap as error:
        evidence.update(collection_status='Not Run',error=type(error).__name__+': '+str(error))
    except (Exception,KeyboardInterrupt) as error:
        evidence.update(status='Failed',collection_status='Failed',error=type(error).__name__+': '+str(error))
    finally:
        try:evidence['process_cleanup']=stop_owned(process)
        except (OSError,RuntimeError,subprocess.SubprocessError) as error:
            evidence.update(status='Failed',collection_status='Failed',cleanup_error=type(error).__name__)
        finally:
            if process:
                for stream in [process.stdin,process.stdout,process.stderr]:
                    if stream and not stream.closed:
                        try:stream.close()
                        except OSError as error:
                            evidence.update(status='Failed',collection_status='Failed',pipe_cleanup_error=type(error).__name__)
            for key,handle in handles.items():
                try:
                    if key in buffers and buffers[key]:
                        # An aborted tail may split a credential/header. Retain
                        # the complete earlier records, never an unsafe prefix.
                        write_log(key,'[aborted native tail omitted]\n')
                except Exception as error:
                    evidence.update(status='Failed',collection_status='Failed',log_export_error=type(error).__name__)
                finally:handle.close()
            if debug_path is not None:
                if trace_fd is not None:
                    try:export_private_trace()
                    except (Exception,KeyboardInterrupt) as error:
                        evidence.update(status='Failed',collection_status='Failed',
                                        trace_export_error=type(error).__name__,hook_process_observation_complete=False)
                try:
                    # Bounded incremental export; no raw debug copy in results.
                    # Reserve metadata space inside the aggregate 48 MiB cap.
                    used=sum(p.stat().st_size for key,p in paths.items() if key not in ['debug','report'] and p.exists())
                    budget=max(0,min(limits['debug'],limits['total']-65536-used))
                    raw_size=checked_debug_size()
                    with os.fdopen(os.dup(debug_fd),'rb') as source,paths['debug'].open('x',encoding='utf-8') as target:
                        source.seek(0)
                        remaining=budget;written=0
                        while remaining>0:
                            raw=source.readline(min(limits['line']+1,remaining))
                            if not raw:break
                            remaining-=len(raw)
                            if not raw.endswith(b'\n'):
                                raise RuntimeError('Incomplete native debug line omitted')
                            if len(raw)>limits['line']:
                                raise RuntimeError('Bounded debug line exceeded; unsafe partial line not exported')
                            safe=redact(raw.decode(errors='replace'))
                            written+=len(safe.encode())
                            if written>budget:raise RuntimeError('Sanitized debug output budget exceeded')
                            target.write(safe)
                    if raw_size>budget:
                        truncated.append('debug')
                        evidence.update(status='Failed',collection_status='Failed',error='Bounded debug/total output exceeded')
                except (Exception,KeyboardInterrupt) as error:
                    evidence.update(status='Failed',collection_status='Failed',debug_export_error=type(error).__name__+': '+str(error))
                finally:
                    for descriptor in [trace_fd,debug_fd,debug_parent_fd]:
                        if descriptor is not None:os.close(descriptor)
                    try:
                        # The CLI can create additional private diagnostic
                        # files here. This random directory belongs only to
                        # this probe; never traverse an exchanged root/link.
                        clean_private_tree(debug_parent,private_dir,debug_identity)
                        evidence['private_debug_removed']=not debug_parent.exists()
                        if trace_hooks:evidence['private_trace_removed']=not debug_parent.exists()
                    except OSError as error:
                        evidence.update(status='Failed',collection_status='Failed',private_debug_removed=False,
                                        cleanup_error='Private debug cleanup: '+type(error).__name__)
            evidence.update(session_id=protocol.session,sent=protocol.sent,turns=protocol.turns,
                native_writes=protocol.rows,input_echoes=protocol.echoes,stream_hook_events=protocol.hooks,
                initializations=protocol.initializations,command_lifecycle=protocol.command_events,
                stdout_records=protocol.sequence,bytes_received=sizes,truncated_streams=sorted(set(truncated)),
                plan_unchanged=unchanged())
            if not evidence['plan_unchanged']:evidence.update(status='Failed',collection_status='Failed')
            evidence['artifacts']={key:{'file':p.name,'sha256':file_hash(p),'bytes':p.stat().st_size}
                                  for key,p in paths.items() if key!='report' and not p.is_symlink() and p.is_file()}
            if privacy_errors:
                evidence.update(status='Failed',collection_status='Failed',redaction_errors=privacy_errors)
            rendered=redact(json.dumps(evidence,ensure_ascii=False,indent=2))+'\n'
            if privacy_errors:
                evidence.update(status='Failed',collection_status='Failed',redaction_errors=privacy_errors)
                rendered=json.dumps({'status':'Failed','collection_status':'Failed',
                    'error':'Redaction failed; content omitted','private_debug_removed':evidence.get('private_debug_removed')})+'\n'
            if len(rendered.encode())>32768:
                evidence={'status':'Failed','collection_status':'Failed','error':'Metadata budget exceeded',
                          'private_debug_removed':evidence.get('private_debug_removed')}
                rendered=json.dumps({'status':'Failed','collection_status':'Failed',
                    'error':'Metadata budget exceeded; variable content omitted'})+'\n'
            with paths['report'].open('x',encoding='utf-8') as target:target.write(rendered)
    return subprocess.CompletedProcess(command,0 if evidence['collection_status']=='Passed' else 1),evidence
