"""Bounded native OpenCode server observation, not a native settled protocol.

Only one initial prompt is submitted. The installed plugin must originate any
follow-up. Raw evidence is returned to the caller for its credential redactor;
this module does not print or persist it. The private server's ephemeral HTTP
password is removed before returning evidence.
"""
from dataclasses import dataclass
import base64
import http.client
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import threading
import time
import uuid

QUIET_SECONDS = 5.0
SOURCES = [
    {'version':'1.18.22','url':'https://github.com/anomalyco/opencode/blob/v1.18.22/packages/opencode/src/cli/cmd/run.ts#L747-L826','fact':'Noninteractive run ends its event loop on the first idle status.'},
    {'version':'1.18.22','url':'https://github.com/anomalyco/opencode/blob/v1.18.22/packages/opencode/src/plugin/index.ts#L236-L244','fact':'Native event callbacks are invoked without awaiting their promises.'},
    {'version':'1.18.22','url':'https://github.com/anomalyco/opencode/blob/v1.18.22/packages/opencode/src/session/status.ts#L35-L43','fact':'Status idle is published before session.idle; the status map then removes the session.'},
    {'version':'1.18.22','url':'https://github.com/anomalyco/opencode/blob/v1.18.22/packages/opencode/src/cli/cmd/serve.ts#L11-L20','fact':'The standalone server remains running independently of a single session.'},
    {'version':'1.18.16','url':'https://github.com/anomalyco/opencode/blob/v1.18.16/packages/sdk/js/src/gen/sdk.gen.ts#L567-L608','fact':'V1 messages and prompt_async endpoints; prompt_async returns before model completion.'},
]


@dataclass
class ProbeResult:
    returncode: int
    stdout: str
    stderr: str
    evidence: dict


def sse_events(response):
    """Strict non-reconnecting SSE parser; split reads and multiline data work."""
    data=[]; size=0
    while True:
        line=response.readline(1024*1024+1)
        if not line:
            if data: raise ValueError('SSE ended inside an event')
            return
        if len(line)>1024*1024: raise ValueError('SSE line too large')
        line=line.decode('utf-8').rstrip('\r\n')
        if not line:
            if data:
                yield json.loads('\n'.join(data)); data=[]; size=0
            continue
        if line.startswith('data:'):
            piece=line[5:].removeprefix(' '); data.append(piece); size+=len(piece)
            if size>1024*1024: raise ValueError('SSE event too large')


def session_of(event):
    props=event.get('properties',{})
    return props.get('sessionID') or props.get('info',{}).get('sessionID') or props.get('part',{}).get('sessionID')


def inspect_completion(messages, events, session_id, case, status, prompt):
    """Require native message links and an idle after the last completed answer."""
    if not isinstance(messages,list) or not isinstance(status,dict): return False,{}
    relevant=[m for m in messages if m.get('info',{}).get('sessionID')==session_id]
    users=[m for m in relevant if m.get('info',{}).get('role')=='user']
    assistants=[m for m in relevant if m.get('info',{}).get('role')=='assistant']
    expected=2 if case=='gated-continuation' else 1
    if len(users)!=expected or len(assistants)!=expected: return False,{}
    initial=[m for m in users if any(p.get('type')=='text' and p.get('text')==prompt for p in m.get('parts',[]))]
    if len(initial)!=1: return False,{}
    ordered_users=[initial[0]]
    if expected==2:
        follow=[m for m in users if m is not initial[0] and any(p.get('type')=='text' and p.get('text','').startswith('[planweft] Gated plan incomplete:') for p in m.get('parts',[]))]
        if len(follow)!=1: return False,{}
        ordered_users+=follow
    ordered_assistants=[]
    for user in ordered_users:
        linked=[m for m in assistants if m['info'].get('parentID')==user['info'].get('id')]
        if len(linked)!=1: return False,{}
        message=linked[0]; info=message['info']
        if not info.get('time',{}).get('completed') or info.get('error'): return False,{}
        if any(p.get('type')=='tool' for p in message.get('parts',[])): return False,{}
        ordered_assistants.append(message)
    # REST completion alone cannot show that idle followed this answer. Bind to
    # the same completed message IDs in the uninterrupted native event stream.
    complete_positions={}; idle_positions=[]
    for index,event in enumerate(events):
        if session_of(event)!=session_id: continue
        props=event.get('properties',{})
        if event.get('type')=='message.updated':
            info=props.get('info',{})
            if info.get('role')=='assistant' and info.get('time',{}).get('completed'):
                complete_positions[info.get('id')]=index
        if event.get('type')=='session.status' and props.get('status',{}).get('type')=='idle': idle_positions.append(index)
    ids=[m['info'].get('id') for m in ordered_assistants]
    if any(i not in complete_positions for i in ids): return False,{}
    positions=[complete_positions[i] for i in ids]
    if positions!=sorted(positions) or len(set(positions))!=expected: return False,{}
    if not idle_positions or idle_positions[-1]<=positions[-1]: return False,{}
    if expected==2 and not any(positions[0]<i<positions[1] for i in idle_positions): return False,{}
    state=status.get(session_id,{'type':'idle'})
    if not isinstance(state,dict) or state.get('type')!='idle': return False,{}
    return True,{'user_ids':[m['info']['id'] for m in ordered_users],
                 'assistant_ids':ids,'idle_events':len(idle_positions),
                 'plugin_followups':expected-1,'completion':'idle observed; no native settled event'}


def cli_output(messages,session_id):
    """Project native stored parts into the existing CLI assessment schema."""
    rows=[]
    for message in messages:
        info=message.get('info',{})
        if info.get('sessionID')!=session_id or info.get('role')!='assistant': continue
        for part in message.get('parts',[]):
            kind={'step-start':'step_start','step-finish':'step_finish','text':'text','tool':'tool_use'}.get(part.get('type'))
            if kind: rows.append({'type':kind,'sessionID':session_id,'part':part})
    return ''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows)


def run_probe(model,prompt,timeout,cwd,out,case):
    """Run an isolated server; return raw evidence for caller-side safe_text.

    `out` is accepted for caller symmetry; no evidence is written here. A
    successful result means the explicit finite observation window passed,
    never that the host exposed a settled/follow-up-queue-empty guarantee.
    """
    del out
    if case not in {'stopping','gated-continuation','gate-cap','gate-stall','gate-cap-disabled','gate-stall-disabled'}:
        raise ValueError('Server probe supports synthetic stopping cases only')
    if timeout<30 or timeout>1800: raise ValueError('Timeout must be 30..1800 seconds')
    if '/' not in model: raise ValueError('Model must be provider/model')
    cwd=Path(cwd)
    if not cwd.is_dir(): raise ValueError('Project directory is missing')
    provider,model_id=model.split('/',1)
    if not provider or not model_id: raise ValueError('Model must be provider/model')
    started=time.monotonic(); deadline=started+timeout
    password=uuid.uuid4().hex
    encoded=base64.b64encode(('opencode:'+password).encode()).decode()
    headers={'Authorization':'Basic '+encoded,'x-opencode-directory':str(cwd),'Content-Type':'application/json'}
    stop=threading.Event(); ready=threading.Event(); incoming=queue.Queue(); logs=queue.Queue()
    events=[]; messages=[]; status={}; status_samples=[]; submitted=0
    evidence={'protocol':'OpenCode V1 SSE and session API','sources':SOURCES,
              'quiet_window_seconds':QUIET_SECONDS,'native_settled_available':False}
    server=None; stream_thread=None; connection=None; session_id=None; failure=None
    streams=[]; log_lines=[]; total_log=0

    def request(method,path,body=None):
        remaining=deadline-time.monotonic()
        if remaining<=0: raise TimeoutError('Probe timeout')
        conn=http.client.HTTPConnection('127.0.0.1',port,timeout=min(15,remaining))
        try:
            conn.request(method,path,None if body is None else json.dumps(body).encode(),headers)
            response=conn.getresponse(); content=response.read(4*1024*1024+1)
            if len(content)>4*1024*1024: raise ValueError('HTTP evidence too large')
            if not 200<=response.status<300: raise ValueError('Native HTTP request failed: '+str(response.status))
            return json.loads(content) if content else None
        finally: conn.close()

    def drain(stream,label):
        try:
            for line in iter(stream.readline,''):
                logs.put((label,line))
        finally: stream.close()

    def collect_stream():
        nonlocal connection
        try:
            connection=http.client.HTTPConnection('127.0.0.1',port,timeout=max(30,timeout))
            connection.request('GET','/event',headers=headers)
            response=connection.getresponse()
            if response.status!=200 or 'text/event-stream' not in response.getheader('Content-Type',''):
                raise ValueError('Native SSE subscription failed')
            for event in sse_events(response):
                if not isinstance(event,dict): raise ValueError('Malformed native event')
                if event.get('type')=='server.connected': ready.set()
                incoming.put(('event',event))
                if stop.is_set(): return
            if not stop.is_set(): incoming.put(('error','Native SSE disconnected'))
        except Exception as error:
            if not stop.is_set(): incoming.put(('error',type(error).__name__+': '+str(error)))

    def drain_logs():
        nonlocal total_log
        while True:
            try: label,line=logs.get_nowait()
            except queue.Empty: return
            total_log+=len(line)
            if total_log>4*1024*1024: raise ValueError('Native server logs too large')
            log_lines.append({'stream':label,'text':line})

    try:
        version=subprocess.run(['opencode','--version'],cwd=cwd,text=True,capture_output=True,timeout=15)
        if version.returncode or version.stdout.strip()!='1.18.22': raise ValueError('Expected native OpenCode 1.18.22')
        evidence['host_version']=version.stdout.strip()
        environment=dict(os.environ,OPENCODE_SERVER_PASSWORD=password,OPENCODE_SERVER_USERNAME='opencode')
        server=subprocess.Popen(['opencode','serve','--hostname','127.0.0.1','--port','0'],cwd=cwd,env=environment,
                                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        for label,stream in [('stdout',server.stdout),('stderr',server.stderr)]:
            thread=threading.Thread(target=drain,args=(stream,label),daemon=True);thread.start();streams.append(thread)
        port=None
        while port is None:
            drain_logs()
            for item in log_lines:
                match=re.search(r'opencode server listening on http://127\.0\.0\.1:(\d+)',item['text'])
                if match: port=int(match[1])
            if server.poll() is not None: raise ValueError('Native server exited during startup')
            if time.monotonic()>min(deadline,started+30): raise TimeoutError('Native server startup timeout')
            if port is None: time.sleep(.05)
        stream_thread=threading.Thread(target=collect_stream,daemon=True);stream_thread.start()
        while not ready.wait(.05):
            if server.poll() is not None: raise ValueError('Native server exited before SSE readiness')
            if time.monotonic()>min(deadline,started+40): raise TimeoutError('Native SSE readiness timeout')
            if not incoming.empty():
                kind,value=incoming.get()
                if kind=='error': raise ValueError(value)
                events.append(value)
        created=request('POST','/session',{'title':'PlanWeft bounded stop probe'})
        session_id=created.get('id') if isinstance(created,dict) else None
        if not isinstance(session_id,str) or not re.fullmatch(r'ses_[A-Za-z0-9]+',session_id): raise ValueError('Native session creation failed')
        evidence['session_id']=session_id
        submitted+=1
        request('POST','/session/'+session_id+'/prompt_async',{'model':{'providerID':provider,'modelID':model_id},'parts':[{'type':'text','text':prompt}]})
        last_activity=time.monotonic(); candidate_since=None; last_check=0; event_bytes=0
        while True:
            now=time.monotonic()
            if now>=deadline: raise TimeoutError('No complete bounded observation before timeout')
            if server.poll() is not None: raise ValueError('Native server exited before observation completed')
            if not stream_thread.is_alive(): raise ValueError('Native SSE collector stopped')
            drain_logs()
            while True:
                try: kind,event=incoming.get_nowait()
                except queue.Empty: break
                if kind=='error': raise ValueError(event)
                events.append(event);event_bytes+=len(json.dumps(event))
                if event_bytes>32*1024*1024: raise ValueError('Native event evidence too large')
                sid=session_of(event);event_type=event.get('type','')
                if sid==session_id: last_activity=now
                if event_type in {'session.error','permission.asked','question.asked'} and sid in {None,session_id}:
                    raise ValueError('Native error or interaction request: '+event_type)
                if sid==session_id and event_type=='message.updated' and event.get('properties',{}).get('info',{}).get('error'):
                    raise ValueError('Native assistant message error')
                if sid==session_id and event_type=='message.part.updated' and event.get('properties',{}).get('part',{}).get('type')=='tool':
                    raise ValueError('Native tool call violates the no-tool stopping fixture')
                if event_type in {'server.instance.disposed','server.stopped'}: raise ValueError('Native instance disposed')
            if now-last_check>=.25:
                messages=request('GET','/session/'+session_id+'/message')
                status=request('GET','/session/status')
                last_check=now
                complete,details=inspect_completion(messages,events,session_id,case,status,prompt)
                status_samples.append({'elapsed':now-started,'status':status,'message_ids':[m.get('info',{}).get('id') for m in messages] if isinstance(messages,list) else [],'eligible':complete})
                if complete:
                    if candidate_since is None: candidate_since=now
                    if now-max(candidate_since,last_activity)>=QUIET_SECONDS:
                        # These are fresh HTTP snapshots after the quiet window;
                        # the server and uninterrupted SSE remain live throughout.
                        if incoming.empty() and server.poll() is None and stream_thread.is_alive():
                            evidence.update(details); evidence['observed_quiet_seconds']=now-max(candidate_since,last_activity)
                            break
                else: candidate_since=None
            time.sleep(.025)
    except Exception as error:
        failure=type(error).__name__+': '+str(error)
    finally:
        stop.set()
        if server is not None:
            try:
                alive=server.poll() is None
                evidence['server_alive_before_harness_shutdown']=alive
                if alive:
                    server.terminate()
                    try: server.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        server.kill();server.wait(timeout=5)
                        if failure is None: failure='Native server required forced shutdown'
                elif failure is None: failure='Native server exited before harness shutdown'
            except Exception as error:
                if failure is None: failure='Native server cleanup failed: '+type(error).__name__
            evidence['server_exit_code']=server.returncode
            evidence['server_shutdown']='harness initiated after observation or failure; not native model completion'
        if connection is not None: connection.close()
        if stream_thread is not None: stream_thread.join(timeout=2)
        for thread in streams: thread.join(timeout=2)
        evidence['collector_threads_closed']=not any(thread.is_alive() for thread in [*streams,*([stream_thread] if stream_thread else [])])
        if not evidence['collector_threads_closed'] and failure is None: failure='Native collector threads did not close'
        try: drain_logs()
        except Exception as error:
            if failure is None: failure=str(error)
    evidence.update(initial_prompts_submitted=submitted,native_events=events,messages=messages,status=status,
                    status_samples=status_samples,server_logs=log_lines,seconds=time.monotonic()-started,
                    result='Failed' if failure else 'Passed',failure=failure)
    # Protect the ephemeral local HTTP credential even before caller redaction.
    def redact(text): return text.replace(password,'[REDACTED_LOCAL_HTTP_AUTH]').replace(encoded,'[REDACTED_LOCAL_HTTP_AUTH]')
    evidence=json.loads(redact(json.dumps(evidence,ensure_ascii=False)))
    stdout=redact(cli_output(messages if isinstance(messages,list) else [],session_id))
    return ProbeResult(1 if failure else 0,stdout,redact(failure or ''),evidence)
