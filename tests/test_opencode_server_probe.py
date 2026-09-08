"""No-model HTTP/SSE lifecycle tests for the native server collector."""
import importlib.util
import io
import json
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('pw_oc_probe',Path(__file__).with_name('opencode_server_probe.py'))
probe=importlib.util.module_from_spec(spec);sys.modules[spec.name]=probe;spec.loader.exec_module(probe)


def message(mid,role,parent=None,text='STOP_PROBE'):
    info={'id':mid,'sessionID':'ses_test','role':role,'time':{'created':1}}
    if role=='assistant': info.update(parentID=parent,time={'created':1,'completed':2})
    parts=[{'type':'text','text':text,'messageID':mid,'sessionID':'ses_test','time':{'end':2}}]
    if role=='assistant':
        parts=[{'type':'step-start','messageID':mid,'sessionID':'ses_test'},*parts,
               {'type':'step-finish','reason':'stop','messageID':mid,'sessionID':'ses_test'}]
    return {'info':info,'parts':parts}


def completed(m): return {'type':'message.updated','properties':{'info':m['info']}}
IDLE={'type':'session.status','properties':{'sessionID':'ses_test','status':{'type':'idle'}}}


class NativeFixture:
    def __init__(self,scenario):
        self.scenario=scenario;self.events=queue.Queue();self.messages=[];self.posts=[]
        self.stopped=threading.Event();self.connected=False;self.returncode=None
        self.stdout=io.StringIO('opencode server listening on http://127.0.0.1:4096\n')
        self.stderr=io.StringIO('')
    def respond(self,prompt):
        if self.scenario=='hang': return
        self.messages=[message('msg_u1','user',text=prompt),message('msg_a1','assistant','msg_u1')]
        self.events.put(completed(self.messages[-1]));self.events.put(IDLE)
        if self.scenario=='delayed':
            time.sleep(.4)
            self.messages += [message('msg_u2','user',text="[planweft] Gated plan incomplete: phase 'Probe' is in_progress (0/1 complete, gate block 1/20). Finish or update the plan, then stop."),message('msg_a2','assistant','msg_u2')]
            self.events.put(completed(self.messages[-1]));self.events.put(IDLE)
        elif self.scenario=='permission': self.events.put({'type':'permission.asked','properties':{'sessionID':'ses_test'}})
        elif self.scenario=='error': self.events.put({'type':'session.error','properties':{'sessionID':'ses_test','error':{'message':'second turn failed'}}})
        elif self.scenario=='disconnect': self.events.put(None)
        elif self.scenario=='tool': self.events.put({'type':'message.part.updated','properties':{'part':{'sessionID':'ses_test','type':'tool'}}})
    def poll(self): return self.returncode
    def terminate(self):
        self.returncode=0;self.stopped.set();self.events.put(None)
    def kill(self): self.terminate()
    def wait(self,timeout=None): return self.returncode


class FakeResponse(io.BytesIO):
    def __init__(self,data,status=200): super().__init__(json.dumps(data).encode() if data is not None else b'');self.status=status
    def getheader(self,name,default=''): return default


class FakeStream:
    status=200
    def __init__(self,fixture): self.fixture=fixture;self.lines=queue.Queue();self.first=True
    def getheader(self,name,default=''): return 'text/event-stream'
    def readline(self,size):
        if self.first:
            self.first=False;self.fixture.connected=True
            self.lines.put(b'\n')
            return b'data: {"type":"server.connected","properties":{}}\n'
        if not self.lines.empty(): return self.lines.get()
        event=self.fixture.events.get()
        if event is None: return b''
        self.lines.put(b'\n')
        return ('data: '+json.dumps(event)+'\n').encode()


class FakeConnection:
    def __init__(self,fixture,*args,**kwargs): self.fixture=fixture
    def request(self,method,path,body=None,headers=None): self.method=method;self.path=path;self.body=body
    def getresponse(self):
        if self.path=='/event': return FakeStream(self.fixture)
        if self.method=='GET': return FakeResponse(self.fixture.messages if self.path.endswith('/message') else {})
        body=json.loads(self.body);self.fixture.posts.append((self.path,body,self.fixture.connected))
        if self.path=='/session': return FakeResponse({'id':'ses_test'})
        threading.Thread(target=self.fixture.respond,args=(body['parts'][0]['text'],),daemon=True).start()
        return FakeResponse(None,204)
    def close(self): pass


class OpenCodeServerProbeTest(unittest.TestCase):
    def run_fake(self,scenario,case='gated-continuation',accelerate=False):
        fixture=NativeFixture(scenario)
        actual_time=time
        clock=SimpleNamespace(monotonic=(lambda:actual_time.monotonic()*40),sleep=actual_time.sleep) if accelerate else actual_time
        try:
            with tempfile.TemporaryDirectory() as project, patch.object(probe.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'1.18.22\n','')), patch.object(probe.subprocess,'Popen',return_value=fixture), patch.object(probe,'QUIET_SECONDS',.08), patch.object(probe,'time',clock), patch.object(probe.http.client,'HTTPConnection',side_effect=lambda *a,**kw:FakeConnection(fixture,*a,**kw)):
                result=probe.run_probe('release/fake','INITIAL',30,project,project,case)
            return result,fixture
        finally:
            if fixture.poll() is None: fixture.terminate()
    def test_delayed_native_followup_survives_first_idle(self):
        result,fixture=self.run_fake('delayed')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.evidence['plugin_followups'],1)
        self.assertEqual(result.evidence['assistant_ids'],['msg_a1','msg_a2'])
        self.assertGreaterEqual(result.evidence['seconds'],.4)
        self.assertEqual(sum(path.endswith('/prompt_async') for path,_,_ in fixture.posts),1)
        self.assertTrue(all(ready for _,_,ready in fixture.posts))
        self.assertFalse(result.evidence['native_settled_available'])
        self.assertEqual([json.loads(l)['type'] for l in result.stdout.splitlines()].count('step_finish'),2)
    def test_default_stopping_observes_one_reply_then_window(self):
        result,_=self.run_fake('single','stopping')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.evidence['plugin_followups'],0)
        self.assertGreaterEqual(result.evidence['observed_quiet_seconds'],.08)
    def test_permission_error_and_stream_loss_fail(self):
        for scenario in ['permission','error','disconnect','tool']:
            with self.subTest(scenario=scenario):
                result,_=self.run_fake(scenario)
                self.assertEqual(result.returncode,1)
                self.assertEqual(result.evidence['result'],'Failed')
    def test_timeout_without_native_followup_fails(self):
        result,fixture=self.run_fake('hang',accelerate=True)
        self.assertEqual(result.returncode,1)
        self.assertIn('timeout',result.stderr.lower())
        self.assertEqual(sum(path.endswith('/prompt_async') for path,_,_ in fixture.posts),1)
    def test_message_parent_and_idle_binding(self):
        users=[message('msg_u1','user',text='INITIAL'),message('msg_u2','user',text='[planweft] Gated plan incomplete: reason')]
        assistants=[message('msg_a1','assistant','msg_u1'),message('msg_a2','assistant','msg_u2')]
        events=[completed(assistants[0]),IDLE,completed(assistants[1]),IDLE]
        def inspect(): return probe.inspect_completion(users+assistants,events,'ses_test','gated-continuation',{},'INITIAL')[0]
        self.assertTrue(inspect())
        assistants[1]['info']['parentID']='msg_unrelated';self.assertFalse(inspect())
        assistants[1]['info']['parentID']='msg_u2';events.pop();self.assertFalse(inspect())
    def test_sse_multiline_crlf_and_truncation(self):
        response=io.BytesIO(b': heartbeat\r\ndata: {"type":\r\ndata: "server.connected"}\r\n\r\n')
        self.assertEqual(list(probe.sse_events(response)),[{'type':'server.connected'}])
        with self.assertRaises(ValueError): list(probe.sse_events(io.BytesIO(b'data: {"type":"partial"}\n')))
    def test_validation_precedes_processes(self):
        with patch.object(probe.subprocess,'run') as command:
            with self.assertRaises(ValueError):probe.run_probe('bad','x',30,'.','.', 'stopping')
            command.assert_not_called()


if __name__=='__main__': unittest.main()
