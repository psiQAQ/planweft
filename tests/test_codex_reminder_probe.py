"""Offline native-notification counterexamples, never actual model evidence."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from codex_reminder_probe import REMINDER,assess,run_probe

SOURCE='/owned/hooks/codex-hooks.json'


def fixture():
    events=[]
    for turn in ['A','B']:
        events.append({'method':'turn/started','params':{'threadId':'thread','turn':{'id':turn}}})
        # UserPromptSubmit has the same handler id across turns. Pair it with
        # thread+turn, and prove a native reset rather than a new SessionStart.
        reset={'id':'reset-handler','eventName':'userPromptSubmit','sourcePath':SOURCE,
               'status':'running','entries':[],'handlerType':'command',
               'executionMode':'sync','source':'plugin','scope':'turn'}
        params={'threadId':'thread','turnId':turn,'run':reset}
        events.append({'method':'hook/started','params':copy.deepcopy(params)})
        params['run'].update(status='completed',completedAt=1)
        events.append({'method':'hook/completed','params':copy.deepcopy(params)})
        for index in range(2):
            tool=turn+str(index)
            # Actual 0.149.1 publishes the successful fileChange before its
            # PostToolUse hook; the hook cannot prove the edit happened alone.
            events.append({'method':'item/completed','params':{'threadId':'thread','turnId':turn,
                'item':{'id':tool,'type':'fileChange','status':'completed'}}})
            run={'id':'handler:'+tool,'eventName':'postToolUse','sourcePath':SOURCE,
                 'status':'running','entries':[],'handlerType':'command',
                 'executionMode':'sync','source':'plugin','scope':'turn'}
            params={'threadId':'thread','turnId':turn,'run':run}
            events.append({'method':'hook/started','params':copy.deepcopy(params)})
            params['run'].update(status='completed',completedAt=1,
                entries=[{'kind':'context','text':REMINDER}] if index==0 else [])
            events.append({'method':'hook/completed','params':copy.deepcopy(params)})
        events.append({'method':'item/completed','params':{'threadId':'thread','turnId':turn,
            'item':{'id':'answer'+turn,'type':'agentMessage','text':'DONE_'+turn}}})
        events.append({'method':'turn/completed','params':{'threadId':'thread','turn':{'id':turn,'status':'completed'}}})
    return events


def initial_session_pair(turn='A'):
    run={'id':'session-start-handler','eventName':'sessionStart','sourcePath':SOURCE,
         'status':'running','entries':[],'handlerType':'command','executionMode':'sync',
         'source':'plugin','scope':'thread','startedAt':1,'completedAt':None}
    first={'method':'hook/started','params':{'threadId':'thread','turnId':turn,'run':run}}
    second=copy.deepcopy(first);second['method']='hook/completed'
    second['params']['run'].update(status='completed',completedAt=1)
    return [first,second]


class ReminderTest(unittest.TestCase):
    def requests(self,events):
        return [{'thread_id':'thread','turn_id':turn,'request_id':index+3,
                 'sent_after_event_count':next(i for i,e in enumerate(events)
                    if e.get('method')=='turn/started' and e['params']['turn']['id']==turn)}
                for index,turn in enumerate(['A','B'])]

    def check(self,events,requests=None):
        return assess(events,'thread',['A','B'],SOURCE,self.requests(events) if requests is None else requests)

    def test_two_serial_turns_have_one_context_each(self):
        self.assertEqual(self.check(fixture())['status'],'Passed')

    def test_real_initial_session_start_may_follow_first_turn_started(self):
        events=fixture();events[1:1]=initial_session_pair()
        self.assertEqual(self.check(events)['status'],'Passed')

    def test_initial_session_lifecycle_cannot_rearm_during_user_reset_or_tools(self):
        for mode in ['after-reset-start','after-pretool-start','after-tool-item','second-turn','repeat','unfinished','different-id']:
            events=fixture();pair=initial_session_pair()
            if mode=='after-reset-start':events[2:2]=pair
            elif mode=='after-pretool-start':
                pretool=copy.deepcopy(pair[0]);pretool['params']['run'].update(id='pretool-handler',eventName='preToolUse',scope='turn')
                events[1:1]=[pretool,*pair]
            elif mode=='after-tool-item':
                tool={'method':'item/started','params':{'threadId':'thread','turnId':'A',
                      'item':{'id':'A0','type':'fileChange','status':'inProgress'}}}
                events[1:1]=[tool,*pair]
            elif mode=='second-turn':
                index=next(i for i,e in enumerate(events) if e['method']=='turn/started' and e['params']['turn']['id']=='B')
                events[index+1:index+1]=initial_session_pair('B')
            elif mode=='repeat':events[1:1]=pair+copy.deepcopy(pair)
            elif mode=='unfinished':events[1:1]=pair[:1]
            else:
                pair[1]['params']['run']['id']='different';events[1:1]=pair
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.check(events)

    def test_initial_session_has_valid_complete_native_identity(self):
        for mode in ['missing-id','wrong-type','failed-start','missing-completed-at','identity-changed']:
            events=fixture();pair=initial_session_pair()
            if mode=='missing-id':
                for e in pair:e['params']['run'].pop('id')
            elif mode=='wrong-type':
                for e in pair:e['params']['run']['handlerType']='agent'
            elif mode=='failed-start':pair[0]['params']['run']['status']='failed'
            elif mode=='missing-completed-at':pair[1]['params']['run']['completedAt']=None
            else:pair[1]['params']['run']['scope']='turn'
            events[1:1]=pair
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.check(events)

    def test_missing_second_execution_cannot_fake_dedup(self):
        events=[e for e in fixture() if e.get('params',{}).get('run',{}).get('id')!='handler:A1']
        with self.assertRaises(ValueError):self.check(events)

    def test_missing_first_duplicate_or_late_context_is_rejected(self):
        for counts in [(0,0),(1,1),(0,1)]:
            events=fixture();completed=[e for e in events if e['method']=='hook/completed'
                and e['params']['run']['eventName']=='postToolUse']
            for e,count in zip(completed,counts):e['params']['run']['entries']=[{'kind':'context','text':REMINDER}]*count
            with self.subTest(counts=counts),self.assertRaises(ValueError):self.check(events)

    def test_output_is_context_not_user_warning_or_model_paraphrase(self):
        events=fixture()
        for e in events:
            for entry in e.get('params',{}).get('run',{}).get('entries',[]):entry['kind']='warning'
        with self.assertRaises(ValueError):self.check(events)

    def test_failed_missing_duplicate_or_truncated_completion_is_rejected(self):
        base=fixture();completion=next(i for i,e in enumerate(base) if e['method']=='hook/completed'
            and e['params']['run']['eventName']=='postToolUse')
        for mode in ['failed','missing','duplicate','truncated']:
            events=copy.deepcopy(base)
            if mode=='failed':events[completion]['params']['run']['status']='failed'
            if mode=='missing':events.pop(completion)
            if mode=='duplicate':events.insert(completion,copy.deepcopy(events[completion]))
            if mode=='truncated':events.pop()
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.check(events)

    def test_source_turn_and_tool_id_binding(self):
        for field,value in [('sourcePath','/foreign/hooks/codex-hooks.json'),('id','handler:unknown')]:
            events=fixture()
            for e in events:
                if e['method'].startswith('hook/'):e['params']['run'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.check(events)
        events=fixture();events[2]['params']['threadId']='different'
        with self.assertRaises(ValueError):self.check(events)

    def test_new_session_or_shell_modifications_cannot_fake_two_turn_edits(self):
        events=fixture();events.insert(9,{'method':'hook/started','params':{'threadId':'thread','turnId':None,
            'run':{'eventName':'sessionStart'}}})
        with self.assertRaises(ValueError):self.check(events)
        events=fixture()
        for e in events:
            item=e.get('params',{}).get('item',{})
            if item.get('type')=='fileChange':item['type']='commandExecution'
        with self.assertRaises(ValueError):self.check(events)

    def test_no_model_continuation_after_context_is_not_delivery(self):
        events=[e for e in fixture() if e.get('params',{}).get('item',{}).get('type')!='agentMessage']
        with self.assertRaises(ValueError):self.check(events)

    def test_two_hooks_for_one_edit_cannot_cover_missing_other_edit(self):
        events=fixture()
        for e in events:
            run=e.get('params',{}).get('run',{})
            if run.get('id')=='handler:A1':run['id']='second-handler:A0'
        with self.assertRaises(ValueError):self.check(events)

    def test_native_user_prompt_reset_is_required_for_each_turn(self):
        for mode in ['all-missing','second-missing','incomplete','failed','after-first-edit']:
            events=fixture()
            def reset(e):return e.get('params',{}).get('run',{}).get('eventName')=='userPromptSubmit'
            if mode=='all-missing':events=[e for e in events if not reset(e)]
            elif mode=='second-missing':events=[e for e in events if not (reset(e) and e['params']['turnId']=='B')]
            elif mode=='incomplete':events=[e for e in events if not (reset(e) and e['method']=='hook/completed')]
            elif mode=='failed':
                for e in events:
                    if reset(e) and e['method']=='hook/completed':e['params']['run']['status']='failed'
            else:
                pair=[e for e in events if reset(e) and e['params']['turnId']=='B']
                events=[e for e in events if e not in pair]
                index=next(i for i,e in enumerate(events) if e.get('params',{}).get('run',{}).get('id')=='handler:B1')
                events[index:index]=pair
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.check(events)

    def test_compaction_cannot_rearm_the_second_user_turn(self):
        for kind in ['item','hook']:
            events=fixture()
            index=next(i for i,e in enumerate(events) if e['method']=='turn/started' and e['params']['turn']['id']=='B')
            if kind=='item':event={'method':'item/completed','params':{'threadId':'thread','turnId':'A',
                'item':{'id':'compact','type':'contextCompaction'}}}
            else:event={'method':'hook/started','params':{'threadId':'thread','turnId':'A',
                'run':{'eventName':'preCompact','sourcePath':SOURCE}}}
            events.insert(index,event)
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.check(events)

    def test_native_handler_identity_and_mode_are_required(self):
        for field,value in [('handlerType','agent'),('executionMode','async'),('source','project'),('scope','thread')]:
            events=fixture()
            for e in events:
                run=e.get('params',{}).get('run',{})
                if run.get('eventName')=='postToolUse':run[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.check(events)

    def test_start_and_completed_event_identity_cannot_change(self):
        events=fixture()
        reset=next(e for e in events if e['method']=='hook/started'
                   and e['params']['run']['eventName']=='userPromptSubmit')
        reset['params']['run']['eventName']='postToolUse'
        with self.assertRaises(ValueError):self.check(events)

    def test_second_request_must_follow_observed_first_turn_completion(self):
        events=fixture()
        completed=next(i for i,e in enumerate(events) if e['method']=='turn/completed'
                       and e['params']['turn']['id']=='A')
        begun=next(i for i,e in enumerate(events) if e['method']=='turn/started'
                   and e['params']['turn']['id']=='B')
        for count in [0,completed, begun+1]:
            requests=self.requests(events);requests[1]['sent_after_event_count']=count
            with self.subTest(count=count),self.assertRaises(ValueError):self.check(events,requests)
        requests=self.requests(events);requests[1]['sent_after_event_count']=completed+1
        self.assertEqual(self.check(events,requests)['status'],'Passed')

    def test_request_evidence_is_complete_and_bound_to_thread_and_turn(self):
        events=fixture()
        variants=[[]]
        for key,value in [('thread_id','foreign'),('turn_id','A'),('request_id',3),
                          ('sent_after_event_count',-1)]:
            requests=self.requests(events);requests[1][key]=value;variants.append(requests)
        requests=self.requests(events);requests[0]['sent_after_event_count']=1;variants.append(requests)
        for requests in variants:
            with self.subTest(requests=requests),self.assertRaises(ValueError):self.check(events,requests)

    def test_collector_keeps_completion_received_before_turn_rpc_response(self):
        # A tiny local JSON-RPC peer, not Codex and not a model. Notifications
        # intentionally precede their request response in the same stdout batch.
        real_popen=subprocess.Popen
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);work=root/'work';out=root/'out';package=root/'package';native=root/'native'
            work.mkdir();out.mkdir()
            for name in ['hooks/codex-hooks.json','.codex/hooks/post_tool_use.py','.codex/hooks/post-tool-use.sh',
                         '.codex/hooks/codex_hook_adapter.py','.codex/hooks/user-prompt-submit.sh']:
                for base in [native,package/'dist/codex/planweft']:
                    target=base/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('owned fixture\n')
            events=fixture()
            for event in events:
                run=event.get('params',{}).get('run',{})
                if run:run['sourcePath']=str(native/'hooks/codex-hooks.json')
            script='''import json,sys
events=json.loads(sys.argv[1]);turn_index=0
for line in sys.stdin:
 request=json.loads(line);method=request.get('method')
 if 'id' not in request:continue
 if method=='initialize':result={}
 elif method=='thread/start':result={'thread':{'id':'thread'}}
 elif method=='turn/start':
  turn=['A','B'][turn_index];turn_index+=1
  for event in events:
   params=event['params']
   if (params.get('turnId') or params.get('turn',{}).get('id'))==turn:print(json.dumps(event))
  result={'turn':{'id':turn}}
 else:raise RuntimeError('Unexpected request')
 print(json.dumps({'id':request['id'],'result':result}),flush=True)
'''
            def start_peer(command,**kwargs):
                return real_popen([sys.executable,'-u','-c',script,json.dumps(events)],**kwargs)
            with patch('codex_trust_probe.trust_hooks',return_value={'stage':'verified-active'}),\
                 patch('codex_reminder_probe.subprocess.Popen',side_effect=start_peer):
                process,observation=run_probe('offline-fixture',work,out,package,native,3,lambda value:value)
            self.assertEqual(process.returncode,0,observation)
            self.assertEqual(observation['status'],'Passed')
            self.assertEqual(observation['native_exit_code'],0)
            journal=[json.loads(line) for line in (out/'reminder-protocol.jsonl').read_text().splitlines()]
            requests=[(i,row) for i,row in enumerate(journal) if row['direction']=='sent'
                      and row['message'].get('method')=='turn/start']
            first_completed=next(i for i,row in enumerate(journal) if row['direction']=='received'
                and row['message'].get('method')=='turn/completed'
                and row['message']['params']['turn']['id']=='A')
            self.assertLess(first_completed,requests[1][0])

    def test_non_codex_case_rejected_before_archive_or_output_access(self):
        runner=Path(__file__).with_name('run-five-agent-release.py')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);output=root/'never-created'
            result=subprocess.run([sys.executable,str(runner),'--host','claude',
                '--cases','reminder-dedup','--archive',str(root/'absent.tgz'),
                '--output',str(output)],capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,2)
            self.assertIn('supports Codex only',result.stderr)
            self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
