import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


probe = load('codex_stop_probe', 'codex_stop_probe.py')
context_tests = load('stop_context_fixtures', 'test_codex_context_probe.py')
PROMPT = 'Native stop experiment. Use no tools. Every answer must be STOP_PROBE.'


def fixture(work, native, case='stopping', disabled_hooks=True):
    thread, events = context_tests.fixture(work, native, None)
    events = events[:5]
    events[3]['params']['item']['content'][0]['text'] = PROMPT
    events[4]['params']['item']['content'][0]['text'] = PROMPT
    def event(method, **params):
        return {'method':method, 'params':{'threadId':'thread-1', 'turnId':'turn-1', **params}}
    def raw(ident, role, text, phase=None):
        item = {'id':ident, 'type':'message', 'role':role,
                'content':[{'type':'output_text' if role == 'assistant' else 'input_text', 'text':text}]}
        if phase: item['phase'] = phase
        return event('rawResponseItem/completed', item=item)
    def hook(ident, name, entries, status='completed'):
        run = {'id':ident,'eventName':name,'sourcePath':str(native/'hooks/codex-hooks.json'),
               'source':'plugin','handlerType':'command','executionMode':'sync',
               'scope':'thread' if name == 'sessionStart' else 'turn','status':'running','startedAt':1}
        events.extend([event('hook/started',run=run),event('hook/completed',run={**run,'status':status,'completedAt':2,'entries':entries})])
    disabled = case.endswith('-disabled')
    if not disabled or disabled_hooks:
        for ident, name in [('ss','sessionStart'),('ups','userPromptSubmit')]:
            entries = [] if disabled else [{'kind':'context','text':'[planweft] selected external-approval plan'}]
            hook(ident,name,entries)
            if entries: events.append(raw('d-'+ident,'developer',entries[0]['text']))
    count = 2 if case == 'gated-continuation' else 1
    for index in range(count):
        ident = 'answer-'+str(index)
        events.extend([event('item/started',item={'id':ident,'type':'agentMessage','phase':'final_answer'}),
                       raw(ident,'assistant','STOP_PROBE','final_answer'),
                       event('item/completed',item={'id':ident,'type':'agentMessage','phase':'final_answer','text':'STOP_PROBE'}),
                       event('rawResponse/completed',responseId='response-'+str(index))])
        blocked = count == 2 and index == 0
        entries = [{'kind':'feedback','text':'Plan awaits approval; continue within scope.'}] if blocked else [] if disabled else [{'kind':'warning','text':'Task in progress.'}]
        hook('stop-'+str(index),'stop',entries,'blocked' if blocked else 'completed')
        if blocked:
            hp = {'id':'hp','type':'hookPrompt','fragments':[{'hookRunId':'stop-0','text':entries[0]['text']}]}
            events.extend([event('item/started',item=hp),
                raw('hp','user','<hook_prompt hook_run_id="stop-0">Plan awaits approval; continue within scope.</hook_prompt>'),
                event('item/completed',item=hp)])
    events.append(event('turn/completed',turn={'id':'turn-1','status':'completed','error':None}))
    return thread, events


class StopProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='pw-stop-test-');self.root=Path(self.tmp.name)
        self.work=self.root/'work';self.work.mkdir();self.native=self.root/'native';self.package=self.root/'package'
        for root in (self.native,self.package/'dist/codex/planweft'):
            for name in ('hooks/codex-hooks.json','.codex/hooks/adapter.py','skills/project-docs/scripts/resolve.sh'):
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture\n')
        self.serial=0

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, events, case='stopping'):
        return probe.assess(events,'thread-1','turn-1',PROMPT,str(self.native/'hooks/codex-hooks.json'),case)

    def run_fake(self, case='stopping', mode='normal', mutate=None, limits=None, prefix=(), timeout=3):
        self.serial+=1;out=self.root/('out-'+str(self.serial))
        thread,events=fixture(self.work,self.native,case)
        if mutate: mutate(events)
        cfg={'mode':mode,'thread':thread,'events':events,'limit':8192,'child_pid':str(self.root/'child.pid')}
        native_popen=subprocess.Popen; commands=[]; processes=[]
        def spawn(command, **kwargs):
            commands.append(command)
            code=context_tests.FAKE
            if prefix:
                self.assertIn('preexec_fn',kwargs)
                code='import resource;assert resource.getrlimit(resource.RLIMIT_FSIZE)==(32768,32768)\n'+code
            process=native_popen([sys.executable,'-c',code,json.dumps(cfg)],**kwargs);processes.append(process);return process
        with mock.patch.dict(os.environ,{'PLANNING_DISABLED':'1' if case.endswith('-disabled') else '0'}), \
             mock.patch.object(probe.transport.subprocess,'Popen',side_effect=spawn):
            result, observation=probe.run_probe('synthetic-model',self.work,out,self.package,self.native,timeout,
                lambda s:s.replace('SECRET','[REDACTED]'),prompt=PROMPT,case=case,limits=limits,
                command_prefix=prefix,trace_limit=32768)
        self.assertTrue(all(p.poll() is not None for p in processes))
        self.assertTrue(observation['private_stderr_removed'])
        for p in out.iterdir(): self.assertNotIn('SECRET',p.read_text())
        return result,observation,commands,out

    def test_cases_use_native_complete_protocol_and_single_or_bound_followup(self):
        for case in sorted(probe.CASES):
            with self.subTest(case=case):
                result,observed,commands,out=self.run_fake(case)
                self.assertEqual(result.returncode,0,observed)
                self.assertTrue(observed['no_model_tool_calls'])
                self.assertEqual(case=='gated-continuation',observed['actual_followup'])
                self.assertFalse(observed['trust_bypass'])
                self.assertEqual(commands[0],['codex','--disable','memories','--disable','multi_agent','app-server'])
                journal=[json.loads(line) for line in (out/'stop-protocol.jsonl').read_text().splitlines()]
                sent=[r['message'] for r in journal if r['direction']=='sent']
                self.assertEqual([m['method'] for m in sent],['initialize','initialized','thread/start','turn/start'])
                self.assertEqual(len([m for m in sent if m['method']=='turn/start']),1)

    def test_disabled_accepts_empty_startup_hooks_but_not_context_or_missing_stop(self):
        for included in [True,False]:
            _,events=fixture(self.work,self.native,'gate-cap-disabled',disabled_hooks=included)
            self.assertEqual('Passed',self.check(events,'gate-cap-disabled')['status'])
        _,events=fixture(self.work,self.native,'gate-cap-disabled')
        event=next(e for e in events if e.get('method')=='hook/completed')
        event['params']['run']['entries']=[{'kind':'context','text':'unexpected'}]
        with self.assertRaises(ValueError):self.check(events,'gate-cap-disabled')
        _,events=fixture(self.work,self.native,'stopping')
        events=[e for e in events if not e.get('params',{}).get('run',{}).get('eventName')=='stop']
        with self.assertRaises(ValueError):self.check(events)

    def test_raw_and_high_level_tools_unknown_and_late_events_are_rejected(self):
        for kind in ['custom_tool_call','custom_tool_call_output','function_call','function_call_output',
                     'local_shell_call','web_search_call','unknown']:
            _,events=fixture(self.work,self.native)
            evil={'method':'rawResponseItem/completed','params':{'threadId':'thread-1','turnId':'turn-1','item':{'id':'tool','type':kind}}}
            for position in [5,len(events)]:
                with self.subTest(kind=kind,position=position):
                    mutated=copy.deepcopy(events);mutated.insert(position,evil)
                    with self.assertRaises(ValueError):self.check(mutated)
        for kind in ['commandExecution','mcpToolCall','fileChange','collabAgentToolCall','unknown']:
            _,events=fixture(self.work,self.native)
            events.insert(5,{'method':'item/started','params':{'threadId':'thread-1','turnId':'turn-1','item':{'id':'tool','type':kind}}})
            with self.assertRaises(ValueError):self.check(events)
        result,observed,_,_=self.run_fake(mode='late')
        self.assertNotEqual(result.returncode,0);self.assertEqual(observed['status'],'Failed')

    def test_two_messages_cannot_fake_continuation_or_reuse_response(self):
        for change in ['no-block','no-raw','wrong-run','wrong-text','duplicate-response','no-high','second-turn','assistant-instead','late-feedback']:
            _,events=fixture(self.work,self.native,'gated-continuation')
            if change=='no-block':
                for e in events:
                    r=e.get('params',{}).get('run',{})
                    if r.get('status')=='blocked':r['status']='completed';r['entries']=[]
            elif change=='no-raw':events=[e for e in events if not(e['method']=='rawResponseItem/completed' and e['params']['item']['id']=='hp')]
            elif change in {'wrong-run','wrong-text'}:
                e=next(e for e in events if e['method']=='rawResponseItem/completed' and e['params']['item']['id']=='hp')
                e['params']['item']['content'][0]['text']=e['params']['item']['content'][0]['text'].replace('stop-0','forged') if change=='wrong-run' else '<hook_prompt hook_run_id="stop-0">Other instruction</hook_prompt>'
            elif change=='duplicate-response':
                for e in events:
                    if e['method']=='rawResponse/completed':e['params']['responseId']='same'
            elif change=='no-high':events=[e for e in events if e.get('params',{}).get('item',{}).get('type')!='hookPrompt']
            elif change=='second-turn':events[-1]['params']['turn']['id']='turn-2'
            elif change=='assistant-instead':
                e=next(e for e in events if e['method']=='rawResponseItem/completed' and e['params']['item']['id']=='hp');e['params']['item']['role']='assistant'
            elif change=='late-feedback':
                moved=[e for e in events if e.get('params',{}).get('item',{}).get('id')=='hp']
                events=[e for e in events if e not in moved];events[-1:-1]=moved
            with self.subTest(change=change):
                with self.assertRaises(ValueError):self.check(events,'gated-continuation')

    def test_foreign_source_thread_lifecycle_and_xml_controls_fail_closed(self):
        for field,value in [('sourcePath','/foreign/hooks.json'),('source','config'),('executionMode','async'),('handlerType','mcpTool'),('status','failed')]:
            _,events=fixture(self.work,self.native)
            target=next(e for e in events if e['method']=='hook/completed');target['params']['run'][field]=value
            with self.subTest(field=field):
                with self.assertRaises(ValueError):self.check(events)
        for field in ['threadId','turnId']:
            _,events=fixture(self.work,self.native);events[5]['params'][field]='foreign'
            with self.assertRaises(ValueError):self.check(events)
        _,events=fixture(self.work,self.native,'gated-continuation')
        target=next(e for e in events if e['method']=='rawResponseItem/completed' and e['params']['item']['id']=='hp')
        target['params']['item']['content'][0]['text']='<!DOCTYPE hook_prompt [<!ENTITY x "secret">]><hook_prompt hook_run_id="stop-0">&x;</hook_prompt>'
        with self.assertRaises(ValueError):self.check(events,'gated-continuation')

    def test_same_text_hook_contexts_require_distinct_ordered_delivery(self):
        for change in ['missing', 'both-after-submit', 'duplicate']:
            _,events=fixture(self.work,self.native)
            first=next(e for e in events if e.get('params',{}).get('item',{}).get('id')=='d-ss')
            if change=='missing':events.remove(first)
            elif change=='both-after-submit':
                events.remove(first)
                later=next(i for i,e in enumerate(events) if e.get('params',{}).get('item',{}).get('id')=='d-ups')
                events.insert(later,first)
            else:
                extra=copy.deepcopy(first);extra['params']['item']['id']='duplicate-developer'
                events.insert(events.index(first)+1,extra)
            with self.subTest(change=change),self.assertRaises(ValueError):self.check(events)

    def test_eof_exit_limits_and_context_assessor_remain_strict(self):
        for mode in ['early','truncated','exit','stdout','stderr','timeout']:
            with self.subTest(mode=mode):
                result,observed,_,_=self.run_fake(mode=mode,limits={'stdout':4096,'stderr':4096} if mode in {'stdout','stderr'} else None,
                                                timeout=0.3 if mode=='timeout' else 3)
                self.assertNotEqual(result.returncode,0);self.assertEqual(observed['status'],'Failed')
        _,events=fixture(self.work,self.native,'gated-continuation')
        with self.assertRaises(ValueError):
            probe.transport.assess(events,'thread-1','turn-1',PROMPT,str(self.native/'hooks/codex-hooks.json'),None,None)

    def test_trace_prefix_wraps_actual_popen_and_child_file_limit(self):
        private=self.root/'private';private.mkdir(mode=0o700)
        prefix=probe.trace_prefix(private)
        result,observed,commands,_=self.run_fake(prefix=prefix)
        self.assertEqual(result.returncode,0,observed)
        self.assertEqual(commands[0][:len(prefix)],prefix)
        self.assertEqual(commands[0][len(prefix):],['codex','--disable','memories','--disable','multi_agent','app-server'])
        self.assertEqual(result.args,commands[0])
        self.assertFalse((private/'gate-private.strace').exists()) # Fake transport; no invented trace evidence.

    def test_invalid_prefix_case_scope_and_limits_fail_before_output_or_process(self):
        private=self.root/'private';private.mkdir(mode=0o700);good=probe.trace_prefix(private)
        variants=[['sh','-c','anything'],good[:-1]+['--dangerously-bypass-hook-trust'],
                  good[:8]+['read=all']+good[9:],good[:10]+[str(self.work/'gate-private.strace')]+good[11:]]
        for prefix in variants:
            with self.subTest(prefix=prefix),mock.patch.object(probe.transport.subprocess,'Popen') as spawn:
                with mock.patch.dict(os.environ,{'PLANNING_DISABLED':'0'}),self.assertRaises(ValueError):
                    probe.run_probe('synthetic',self.work,self.root/'never',self.package,self.native,3,lambda s:s,
                                    prompt=PROMPT,case='stopping',command_prefix=prefix)
                spawn.assert_not_called();self.assertFalse((self.root/'never').exists())
        with mock.patch.dict(os.environ,{'PLANNING_DISABLED':'1'}),self.assertRaises(ValueError):
            probe.run_probe('synthetic',self.work,self.root/'never',self.package,self.native,3,lambda s:s,prompt=PROMPT,case='stopping')


if __name__=='__main__':unittest.main()
