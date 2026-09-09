"""Codex 0.149.1 native two-turn reminder observation, separate from Stop traces.

Protocol: rust-v0.149.1, app-server-protocol/src/protocol/v2/hook.rs.
Completed context entries are also passed to model context by core/tools/registry;
require a subsequent assistant response and normal turn completion as well.
"""
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time

REMINDER='[planweft] Update progress.md with what you just did. If a phase is now complete, update task_plan.md status.'


def assess(events, thread, turns, source, turn_requests):
    if len(turns)!=2 or len(set(turns))!=2:raise ValueError('Need two distinct turns')
    starts={};ends={};edits={turn:set() for turn in turns};answers={turn:[] for turn in turns}
    activity_started=False
    completed={};begun={};rows={turn:[] for turn in turns};resets={turn:[] for turn in turns};startup={}
    for i,e in enumerate(events):
        method=e.get('method');p=e.get('params',{})
        if method in {'error','session/closed'}:raise ValueError('Native session error/closure')
        if method and ('compact' in method.lower()):raise ValueError('Compaction invalidates the uninterrupted two-turn probe')
        if method in {'item/started','item/completed'} and p.get('item',{}).get('type') in {
                'fileChange','commandExecution','mcpToolCall','dynamicToolCall','webSearch'}:
            activity_started=True
        if method not in {'hook/started','hook/completed','item/completed','turn/started','turn/completed'}:continue
        if p.get('threadId')!=thread:raise ValueError('Foreign or absent thread binding')
        turn=p.get('turnId') or p.get('turn',{}).get('id')
        if method.startswith('hook/'):
            run=p.get('run',{})
            if run.get('eventName') in {'userPromptSubmit','preToolUse','postToolUse'}:activity_started=True
            if 'compact' in run.get('eventName','').lower():raise ValueError('Compaction hook resets cannot prove user-turn reset')
            if run.get('eventName')=='sessionStart':
                # 0.149.1 emits the initial turn/started before SessionStart.
                # Allow its one initial lifecycle only before any user reset or
                # tool, never as a reset between the two turns.
                if (turn not in {None,turns[0]} or activity_started
                        or len(begun)>1 or run.get('sourcePath')!=source):
                    raise ValueError('SessionStart between user turns')
                if (not run.get('id') or run.get('startedAt') is None or any(run.get(k)!=v for k,v in
                        {'handlerType':'command','executionMode':'sync','source':'plugin','scope':'thread'}.items())):
                    raise ValueError('Invalid initial SessionStart identity')
                if method in startup:raise ValueError('Repeated initial SessionStart')
                if method=='hook/started' and run.get('status')!='running':
                    raise ValueError('Initial SessionStart was not running')
                if method=='hook/completed':
                    prior=startup.get('hook/started')
                    if (prior is None or run.get('status')!='completed' or run.get('completedAt') is None
                            or any(prior[1].get(k)!=run.get(k) for k in
                                   ('id','eventName','sourcePath','source','handlerType','executionMode','scope','startedAt'))):
                        raise ValueError('Incomplete initial SessionStart')
                startup[method]=(i,run)
                continue
            if run.get('eventName') not in {'postToolUse','userPromptSubmit'}:continue
            if turn not in turns or run.get('sourcePath')!=source:raise ValueError('Unbound PostToolUse source/turn')
            if any(run.get(k)!=v for k,v in {'handlerType':'command','executionMode':'sync','source':'plugin','scope':'turn'}.items()):
                raise ValueError('Unexpected native handler identity or execution mode')
            key=(thread,turn,run.get('id'))
            if not key[2]:raise ValueError('Missing hook run id')
            target=starts if method=='hook/started' else ends
            if key in target:raise ValueError('Duplicate hook lifecycle notification')
            if method=='hook/started' and run.get('status')!='running':raise ValueError('Native hook start was not running')
            target[key]=(i,run)
            if method=='hook/completed':
                if key not in starts or run.get('status')!='completed' or run.get('completedAt') is None:
                    raise ValueError('Hook was not started and completed successfully')
                if any(starts[key][1].get(k)!=run.get(k) for k in
                       ('eventName','sourcePath','source','handlerType','executionMode','scope','startedAt')):
                    raise ValueError('Hook identity changed between start and completion')
                entries=run.get('entries')
                if not isinstance(entries,list):raise ValueError('Missing output entries')
                if any(x.get('kind') in {'error','stop','feedback'} for x in entries):raise ValueError('Hook error/control output')
                if run['eventName']=='userPromptSubmit':
                    resets[turn].append({'start_index':starts[key][0],'end_index':i})
                    continue
                context=[x.get('text','').strip() for x in entries if x.get('kind')=='context']
                if any(x!=REMINDER for x in context):raise ValueError('Unexpected model context')
                rows[turn].append({'id':key[2],'start_index':starts[key][0],
                    'end_index':i,'contexts':len(context)})
        elif turn not in turns:raise ValueError('Foreign user turn')
        elif method=='turn/started':
            if turn in begun:raise ValueError('Duplicate turn start')
            begun[turn]=i
        elif method=='turn/completed':
            if turn in completed or p.get('turn',{}).get('status')!='completed':raise ValueError('Incomplete/duplicate turn')
            completed[turn]=i
        elif method=='item/completed':
            item=p.get('item',{})
            if item.get('type')=='contextCompaction':raise ValueError('Compaction resets cannot prove user-turn reset')
            if item.get('type')=='fileChange':
                if item.get('status')!='completed' or not item.get('id'):raise ValueError('Failed native edit')
                edits[turn].add(item['id'])
            elif item.get('type')=='agentMessage' and item.get('text'):answers[turn].append((i,item['text']))
    if set(starts)!=set(ends):raise ValueError('Unfinished hook calls')
    if startup and set(startup)!={'hook/started','hook/completed'}:raise ValueError('Unfinished initial SessionStart')
    if set(begun)!=set(turns) or set(completed)!=set(turns):raise ValueError('Missing turn boundary')
    if completed[turns[0]]>=begun[turns[1]]:raise ValueError('Turns overlap')
    if (len(turn_requests)!=2 or len({r.get('request_id') for r in turn_requests})!=2
            or [r.get('turn_id') for r in turn_requests]!=turns
            or any(r.get('thread_id')!=thread for r in turn_requests)):
        raise ValueError('User request provenance differs')
    for i,(turn,request) in enumerate(zip(turns,turn_requests)):
        count=request.get('sent_after_event_count')
        if not isinstance(count,int) or not 0<=count<=begun[turn] or (i and count<=completed[turns[i-1]]):
            raise ValueError('User turn was sent before the previous turn completed')
    for turn in turns:
        selected=sorted(rows[turn],key=lambda r:r['start_index'])
        if len(selected)<2 or len(edits[turn])<2:raise ValueError('Need at least two actual native edits and hooks per turn')
        bindings=[[tool for tool in edits[turn] if r['id'].endswith(':'+tool)] for r in selected]
        if (any(len(b)!=1 for b in bindings) or len(bindings)!=len(edits[turn])
                or {b[0] for b in bindings if b}!=edits[turn]):
            raise ValueError('Hook calls do not bind native edit ids')
        if len(resets[turn])!=1 or not begun[turn]<resets[turn][0]['start_index']<resets[turn][0]['end_index']<selected[0]['start_index']:
            raise ValueError('Missing native UserPromptSubmit reset before tools')
        if [r['contexts'] for r in selected]!=[1]+[0]*(len(selected)-1):raise ValueError('Reminder was not first-only within the turn')
        for first,second in zip(selected,selected[1:]):
            if first['end_index']>=second['start_index']:raise ValueError('Concurrent hook calls are not the serial probe')
        if any(not begun[turn]<r['start_index']<r['end_index']<completed[turn] for r in selected):
            raise ValueError('Hook outside its user turn')
        if not any(selected[-1]['end_index']<i<completed[turn] for i,_ in answers[turn]):
            raise ValueError('No subsequent model response after context processing')
    return {'status':'Passed','thread_id':thread,'turn_ids':turns,'turns':rows,
            'scope':'Native first-only PostToolUse context plus subsequent model continuation; no model paraphrase counting'}


def run_probe(model, work, out, package, native_root, timeout, sanitize):
    from codex_trust_probe import trust_hooks
    deadline=time.monotonic()+timeout
    def remaining():
        value=deadline-time.monotonic()
        if value<=0:raise TimeoutError('Reminder probe exceeded deadline')
        return value
    trust=trust_hooks(model,work,out/'reminder-trust-ui.log',min(90,remaining()),sanitize=sanitize)
    command=['codex','--disable','memories','--disable','multi_agent','app-server']
    events=[];buffer=b'';pending=[];bytes_seen=0;process=None;thread=None;turns=[];turn_requests=[];evidence={'status':'Failed'}
    request_id=0
    with (out/'reminder-protocol.jsonl').open('w') as journal,(out/'reminder-native.stderr').open('w+') as errors:
        def log(direction,value):
            journal.write(sanitize(json.dumps({'direction':direction,'message':value},ensure_ascii=False))+'\n');journal.flush()
        def send(value):
            log('sent',value);process.stdin.write((json.dumps(value)+'\n').encode());process.stdin.flush()
        def receive():
            nonlocal buffer,bytes_seen
            while not pending:
                if os.fstat(errors.fileno()).st_size>8*1024**2:raise RuntimeError('Bounded native stderr exceeded')
                if process.poll() is not None:raise RuntimeError('Native app-server exited early')
                if not select.select([process.stdout],[],[],min(remaining(),1))[0]:continue
                chunk=os.read(process.stdout.fileno(),65536)
                if not chunk:raise RuntimeError('Truncated app-server output')
                bytes_seen+=len(chunk)
                if bytes_seen>16*1024**2:raise RuntimeError('Bounded native protocol output exceeded')
                buffer+=chunk
                while b'\n' in buffer:
                    line,buffer=buffer.split(b'\n',1)
                    value=json.loads(line);log('received',value);events.append(value);pending.append(value)
            value=pending.pop(0)
            if 'id' in value and 'method' in value:raise RuntimeError('Unexpected native permission/input request')
            return value
        def request(method,params):
            nonlocal request_id
            request_id+=1;ident=request_id;send({'id':ident,'method':method,'params':params})
            while True:
                value=receive()
                if value.get('id')==ident:
                    if 'error' in value:raise RuntimeError('Native '+method+' rejected')
                    return value['result']
        try:
            process=subprocess.Popen(command,cwd=work,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                     stderr=errors,start_new_session=True)
            request('initialize',{'clientInfo':{'name':'planweft-reminder-probe','version':'1'},
                                  'capabilities':{'experimentalApi':True}})
            send({'method':'initialized','params':{}})
            started=request('thread/start',{'model':model,'cwd':str(work),'approvalPolicy':'never',
                                             'sandbox':'danger-full-access','ephemeral':True,'experimentalRawEvents':True})
            thread=started['thread']['id']
            for label in ['A','B']:
                prompt=('这是原生提醒去重验收。请仅用两次独立、串行的 apply_patch 调用，先将 reminder-a.txt 全文改为 '
                    +label+'，收到工具结果后再将 reminder-b.txt 全文改为 '+label+'。不要合并调用，不用 shell；'
                    '每个文件为一行，保留结尾换行。'
                    '不读写其他文件、不修改完成态计划、不手动调用 hooks、不读取或清理宿主缓存。两次完成后只回复 DONE_'+label+'。')
                prompt+=' 这两个目标文件的现有全文均为 '+json.dumps(('initial' if label=='A' else 'A')+'\n')+'。工具失败时报告失败，不得声称完成。'
                sent={'thread_id':thread,'request_id':request_id+1,'sent_after_event_count':len(events)}
                turn=request('turn/start',{'threadId':thread,'input':[{'type':'text','text':prompt,'text_elements':[]}]})['turn']['id']
                turns.append(turn)
                sent['turn_id']=turn;turn_requests.append(sent)
                while not any(e.get('method')=='turn/completed' and e.get('params',{}).get('turn',{}).get('id')==turn for e in events):
                    value=receive()
            sources={e['params']['run']['sourcePath'] for e in events if e.get('method')=='hook/completed'
                     and e.get('params',{}).get('run',{}).get('eventName')=='postToolUse'}
            if len(sources)!=1:raise RuntimeError('Native hook configuration source not unique')
            source=Path(next(iter(sources)));relative=Path('hooks/codex-hooks.json')
            if source!=native_root/relative or not source.is_file():raise RuntimeError('Unexpected native hook manifest')
            native=source.parent.parent;expected=package/'dist/codex/planweft';bindings={}
            for name in [relative,Path('.codex/hooks/post_tool_use.py'),Path('.codex/hooks/post-tool-use.sh'),
                         Path('.codex/hooks/codex_hook_adapter.py'),Path('.codex/hooks/user-prompt-submit.sh')]:
                raw=(native/name).read_bytes()
                if raw!=(expected/name).read_bytes():raise RuntimeError('Installed hook resource bytes differ')
                bindings[str(name)]=hashlib.sha256(raw).hexdigest()
            evidence=assess(events,thread,turns,str(source),turn_requests)
            evidence.update(trust=trust,trust_bypass=False,source_path=str(source),resource_sha256=bindings,
                            protocol_revision='ff29a44391deccde0aba0f8390337d7f3c319ea4')
        except Exception as error:
            evidence.update(error=type(error).__name__+': '+str(error),thread_id=thread,turn_ids=turns)
        finally:
            try:
                if process is not None:
                    if process.poll() is None:
                        try:process.stdin.close()
                        except BrokenPipeError:pass
                        try:process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            try:os.killpg(process.pid,signal.SIGTERM)
                            except ProcessLookupError:pass
                            try:process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                try:os.killpg(process.pid,signal.SIGKILL)
                                except ProcessLookupError:pass
                                process.wait(timeout=5)
                    evidence['native_exit_code']=process.returncode
                    evidence['server_shutdown']='Harness closes its owned server after two turns'
            except (OSError,subprocess.SubprocessError) as error:
                evidence.update(status='Failed',cleanup_error=type(error).__name__)
            finally:
                if process is not None:
                    for stream in (process.stdin,process.stdout):
                        if stream is not None:
                            try:stream.close()
                            except OSError:pass
                errors.seek(0);stderr=errors.read(8*1024**2+1)
                if len(stderr)>8*1024**2:
                    stderr=stderr[:8*1024**2].rsplit('\n',1)[0]+'\n[stderr truncated at limit]\n'
                    evidence.update(status='Failed',stderr_truncated=True)
                stderr=sanitize(stderr);errors.seek(0);errors.truncate();errors.write(stderr)
                evidence['turn_requests']=turn_requests
                (out/'reminder-observation.json').write_text(sanitize(json.dumps(evidence,indent=2))+'\n')
    # Existing runner consumes an explicitly labeled projection, not fake hook
    # notifications. The complete app-server protocol remains in its own file.
    answers=[e['params']['item']['text'] for e in events if e.get('method')=='item/completed'
             and e.get('params',{}).get('item',{}).get('type')=='agentMessage']
    stdout='\n'.join(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':a}}) for a in answers)
    return subprocess.CompletedProcess(command,0 if evidence['status']=='Passed' else 1,stdout,stderr),evidence
