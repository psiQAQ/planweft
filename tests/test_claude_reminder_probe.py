"""Offline fake-CLI/process tests. These are not real Claude hook evidence."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from claude_reminder_probe import DEFAULT_LIMITS,FILES,PREFIX,Protocol,run_probe,stop_owned

FAKE=r'''
import json,os,select,sys,time
from pathlib import Path
mode=sys.argv[1];debug=Path(sys.argv[2]);work=Path.cwd()
def emit(value): print(json.dumps(value),flush=True)
def event(kind,**fields): return {'type':kind,'session_id':'session',**fields}
for index,line in enumerate(sys.stdin):
    request=json.loads(line);label=['A','B'][index]
    if index==0:emit(event('system',subtype='init'))
    emit(event('user',message=request['message'],uuid=request['uuid'],isReplay=True))
    with debug.open('a') as f:
        if mode!='no-debug':f.write('SYNTHETIC_SECRET native hook diagnostic '+label+'\n')
    if mode=='debug-limit':
        with debug.open('a') as f:f.write('x'*10000+'\n')
        time.sleep(1)
    if mode=='stdout-limit':
        print('x'*10000,flush=True);time.sleep(1)
    if mode=='stderr-limit':
        print('x'*10000,file=sys.stderr,flush=True);time.sleep(1)
    if mode=='total-limit':
        with debug.open('a') as f:f.write(('x'*100+'\n')*500)
        print('y'*30000,file=sys.stderr,flush=True);time.sleep(1)
    if mode=='truncate':sys.stdout.write('{"type":');sys.stdout.flush();sys.exit(0)
    if mode=='hang':time.sleep(30)
    if mode=='early':sys.exit(0)
    if mode=='foreign-session' and index:emit({'type':'assistant','session_id':'foreign','message':{'content':[]}})
    if mode=='reset' and index:emit(event('system',subtype='init'))
    for number in [1,2]:
        path=work/f'reminder-{label.lower()}-{number}.txt';text=f'{label}-{number}\n';tool=label+str(number)
        call={'type':'tool_use','name':'Write','id':tool,'input':{'file_path':str(path),'content':text}}
        if mode=='bash':call['name']='Bash'
        if mode=='concurrent':emit(event('assistant',message={'content':[call,{**call,'id':'concurrent'}]}))
        else:emit(event('assistant',message={'content':[call]}))
        if mode=='failed-write':
            emit(event('user',message={'content':[{'type':'tool_result','tool_use_id':tool,'is_error':True}]}));sys.exit(0)
        path.write_text(text)
        result=event('user',message={'content':[{'type':'tool_result','tool_use_id':tool,'content':'successful'}]},
                     tool_use_result={'type':'create','filePath':str(path),'content':text})
        if mode=='unbound':result.pop('tool_use_result')
        emit(result)
        if mode=='one-write':break
    if mode=='changed-plan':(work/'task_plan.md').write_text('# changed\n')
    if index==0:
        # The fake child has finished its tools but not emitted result A yet.
        # A queued second request would invalidate the serial-input probe.
        if select.select([sys.stdin],[],[],.01)[0]:raise RuntimeError('B queued before A result')
    emit(event('assistant',message={'content':[{'type':'text','text':'DONE_'+label}]}))
    emit(event('result',subtype='success',is_error=False,uuid='result-'+label))
    if mode=='extra-result':emit(event('result',subtype='success',is_error=False))
'''


class ClaudeReminderTest(unittest.TestCase):
    def fixture(self,root):
        work=root/'project';out=root/'evidence';package=root/'package';native=root/'native';private=root/'private'
        for path in [work,package,native,private]:path.mkdir()
        (work/'task_plan.md').write_text('# Plan\n## Goal\nSynthetic complete plan\n### Phase 1\n- **Status:** complete\n')
        (work/'findings.md').write_text('# Findings\n');(work/'progress.md').write_text('# Progress\n')
        from claude_reminder_probe import RESOURCES
        for relative in RESOURCES:
            content=b'fixed resource\n'
            if relative=='hooks/hooks.json':content=json.dumps({'hooks':{'PostToolUse':[{'matcher':'Write|Edit','hooks':[{'type':'command','command':'owned'}]}]}}).encode()
            for base in [native,package/'dist/claude/planweft']:
                path=base/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
        script=root/'fake_cli.py';script.write_text(FAKE)
        return work,out,package,native,private,script

    def invoke(self,root,mode='normal',limits=None,timeout=3,sanitize=None):
        work,out,package,native,private,script=self.fixture(root)
        real=subprocess.Popen;spawned=[]
        def spawn(command,**kwargs):
            self.assertIn('--input-format',command);self.assertIn('--replay-user-messages',command)
            self.assertNotIn('--debug',command);self.assertEqual(kwargs['env']['CLAUDE_CODE_DEBUG_LOG_LEVEL'],'verbose')
            debug=Path(command[command.index('--debug-file')+1]);self.assertIn(private,debug.parents)
            self.assertNotIn(out,debug.parents);self.assertEqual(debug.parent.stat().st_mode&0o777,0o700)
            process=real([sys.executable,'-u',str(script),mode,str(debug)],**kwargs);spawned.append(process);return process
        with patch('claude_reminder_probe.subprocess.Popen',side_effect=spawn):
            completed,evidence=run_probe('synthetic-model',work,out,package,native,timeout,
                sanitize or (lambda s:s.replace('SYNTHETIC_SECRET','[REDACTED]')),plan_dir=work,private_dir=private,limits=limits)
        self.assertEqual(len(spawned),1);self.assertIsNotNone(spawned[0].poll())
        self.assertTrue(all(s.closed for s in [spawned[0].stdin,spawned[0].stdout,spawned[0].stderr]))
        self.assertEqual(list(private.iterdir()),[])
        for file in out.iterdir():self.assertNotIn('SYNTHETIC_SECRET',file.read_text())
        self.assertTrue(evidence['private_debug_removed'])
        return completed,evidence,out

    def test_same_process_serial_collection_does_not_claim_hook_passed(self):
        with tempfile.TemporaryDirectory() as temporary:
            result,evidence,out=self.invoke(Path(temporary))
            self.assertEqual(result.returncode,0)
            self.assertEqual(evidence['collection_status'],'Passed')
            self.assertEqual(evidence['status'],'Not Run')
            self.assertEqual(evidence['reminder_deduplication'],'Not Run')
            self.assertEqual(len(evidence['native_writes']),4)
            self.assertEqual([r['label'] for r in evidence['input_echoes']],['A','B'])
            self.assertGreaterEqual(evidence['sent'][1]['sent_after_stdout_sequence'],evidence['turns'][0]['result_sequence'])
            self.assertGreater(evidence['sent'][1]['debug_native_bytes_at_send'],0)
            self.assertEqual(evidence['sent'][1]['request']['session_id'],'session')
            self.assertIn('[REDACTED] native hook diagnostic',(out/(PREFIX+FILES['debug'])).read_text())
            self.assertTrue(evidence['plan_unchanged'])

    def test_protocol_rejects_early_queue_before_native_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            protocol=Protocol(Path(temporary));protocol.send('A',0)
            with self.assertRaises(ValueError):protocol.send('B',0)
            with self.assertRaises(ValueError):protocol.send('A',0)

    def test_failure_truncation_extra_tools_and_resets_never_pass(self):
        for mode in ['failed-write','truncate','early','concurrent','one-write','bash','foreign-session','reset','extra-result','changed-plan','unbound','no-debug']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temporary:
                result,evidence,_=self.invoke(Path(temporary),mode)
                self.assertNotEqual(result.returncode,0)
                self.assertNotEqual(evidence['collection_status'],'Passed')
                self.assertNotEqual(evidence['status'],'Passed')
                if mode in ['failed-write','truncate','early','concurrent','one-write','bash','unbound']:
                    self.assertEqual(len(evidence['sent']),1)
                if mode in ['unbound','no-debug']:self.assertEqual(evidence['status'],'Not Run')
                # Duplicate result can arrive after valid A triggered B; only
                # the eventual Failed verdict, not prediction of late data, is required.

    def test_channel_and_total_limits_keep_private_source_out_of_evidence(self):
        for channel in ['stdout','stderr','debug','total']:
            with self.subTest(channel=channel),tempfile.TemporaryDirectory() as temporary:
                limits=dict(DEFAULT_LIMITS)
                if channel=='total':limits.update(total=128*1024,line=65536)
                else:limits[channel]=1024;limits['line']=1024
                result,evidence,out=self.invoke(Path(temporary),channel+'-limit',limits)
                self.assertEqual(evidence['status'],'Failed');self.assertEqual(result.returncode,1)
                self.assertLess(sum(p.stat().st_size for p in out.iterdir()),limits['total'])

    def test_redaction_failure_or_expansion_never_leaks_or_passes(self):
        def failing(value):
            if 'native hook diagnostic' in value:raise RuntimeError('synthetic redactor failure')
            return value
        for redactor in [failing,lambda value:'x'*100000]:
            with self.subTest(redactor=redactor),tempfile.TemporaryDirectory() as temporary:
                result,evidence,out=self.invoke(Path(temporary),sanitize=redactor)
                self.assertEqual(result.returncode,1);self.assertEqual(evidence['status'],'Failed')
                self.assertLess(sum(p.stat().st_size for p in out.iterdir()),DEFAULT_LIMITS['total'])
                saved=json.loads((out/(PREFIX+FILES['report'])).read_text())
                self.assertEqual(saved['status'],'Failed')

    def test_timeout_stops_only_owned_group_and_closes_descriptors(self):
        real=subprocess.Popen
        other=real([sys.executable,'-c','import time; time.sleep(30)'],start_new_session=True)
        try:
            with tempfile.TemporaryDirectory() as temporary:
                result,evidence,_=self.invoke(Path(temporary),'hang',timeout=.2)
                self.assertEqual(evidence['status'],'Failed');self.assertIn('TimeoutError',evidence['error'])
                self.assertIn('SIGTERM',evidence['process_cleanup']['signals'])
                self.assertIsNone(other.poll())
        finally:
            os.killpg(other.pid,signal.SIGTERM);other.wait(timeout=2)

    def test_invalid_arguments_do_not_start_process_or_create_outputs(self):
        for mode in ['timeout','limits','existing-target','incomplete-plan','resource-drift','private-in-output','existing-log']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);work,out,package,native,private,_=self.fixture(root)
                timeout=3;limits=None
                if mode=='timeout':timeout=601
                if mode=='limits':limits={**DEFAULT_LIMITS,'stdout':0}
                if mode=='existing-target':(work/'reminder-a-1.txt').write_text('owned elsewhere')
                if mode=='incomplete-plan':(work/'task_plan.md').write_text('- **Status:** in_progress\n')
                if mode=='resource-drift':(native/'hooks/claude-hook.sh').write_text('changed')
                if mode=='private-in-output':out.mkdir();private=out
                if mode=='existing-log':out.mkdir();(out/(PREFIX+FILES['debug'])).write_text('preserve')
                with patch('claude_reminder_probe.subprocess.Popen') as spawn,self.assertRaises(ValueError):
                    run_probe('synthetic',work,out,package,native,timeout,lambda s:s,
                              plan_dir=work,private_dir=private,limits=limits)
                spawn.assert_not_called();self.assertFalse((out/(PREFIX+FILES['report'])).exists())

    def test_owned_group_cleanup_escalates_for_term_ignoring_child(self):
        process=subprocess.Popen([sys.executable,'-u','-c',
            'import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print("ready",flush=True);time.sleep(30)'],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,start_new_session=True)
        try:
            self.assertEqual(process.stdout.readline(),b'ready\n')
            evidence=stop_owned(process,grace=.05)
            self.assertIn('SIGKILL',evidence['signals']);self.assertIsNotNone(process.poll())
        finally:
            process.stdout.close()
            if process.poll() is None:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=2)


if __name__=='__main__':unittest.main()
