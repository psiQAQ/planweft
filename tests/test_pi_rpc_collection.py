"""Real subprocess fixtures for native RPC follow-up collection; no model/network."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
FAKE=r'''
import json, select, sys, time
mode=sys.argv[1]
def emit(**value): print(json.dumps(value),flush=True)
assert json.loads(input())['id']=='activate'
emit(id='activate',success=True)
assert json.loads(input())['id']=='task'
emit(type='agent_start')
emit(type='agent_end',messages=[{'role':'assistant','stopReason':'stop'}])
if mode=='eof': sys.exit(0)
if mode=='timeout': time.sleep(10)
# Closing stdin after the first end would cancel the extension's continuation.
ready,_,_=select.select([sys.stdin],[],[],0.05)
if ready: sys.exit(7)
emit(type='agent_start')
emit(type='agent_end',messages=[{'role':'assistant','stopReason':'error' if mode=='model-error' else 'stop'}])
emit(type='agent_settled')
assert json.loads(input())['id']=='settled-state'
emit(id='settled-state',success=True,data={'isStreaming':False,'isCompacting':mode=='compacting','pendingMessageCount':1 if mode=='pending' else 0})
if mode=='restart': emit(type='agent_start')
for line in sys.stdin: pass
emit(type='shutdown_complete')
sys.exit(9 if mode=='exit-error' else 0)
'''

class PiRpcCollectionTest(unittest.TestCase):
    def trial(self,mode):
        spec=importlib.util.spec_from_file_location('pw_pi_runtime',ROOT/'tests/five_agent_runtime.py')
        runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);fake=root/'fake.py';fake.write_text(FAKE)
            runtime.WORK=runtime.OUT=root
            popen=subprocess.Popen
            def start(command,**kwargs):
                self.assertEqual(command[0],'pi')
                return popen([sys.executable,str(fake),mode],**kwargs)
            with patch.object(runtime.subprocess,'Popen',side_effect=start):
                result=runtime.pi_model('fixture','synthetic task',0.3 if mode=='timeout' else 3)
            return result,json.loads((root/'model.json').read_text()),(root/'model.stdout').read_text()

    def test_followup_is_collected_through_idle_and_eof(self):
        result,meta,raw=self.trial('ok')
        self.assertEqual(result.returncode,0)
        self.assertEqual(meta['event_counts'],{'agent_start':2,'agent_end':2,'agent_settled':1})
        self.assertFalse(meta['forced_termination'])
        self.assertIn('shutdown_complete',raw)
        self.assertEqual(meta['process_exit_code'],0)

    def test_incomplete_or_failed_followup_never_passes(self):
        for mode in ['model-error','timeout','eof','pending','compacting','restart','exit-error']:
            with self.subTest(mode=mode):
                result,meta,raw=self.trial(mode)
                self.assertNotEqual(result.returncode,0)
                self.assertTrue(meta['failure'] or meta['forced_termination'])
                self.assertIn('agent_end',raw)
                if mode=='model-error': self.assertIn('"stopReason": "error"',raw)
                if mode=='exit-error': self.assertEqual(meta['process_exit_code'],9)
                if mode=='timeout': self.assertTrue(meta['forced_termination'])

if __name__=='__main__': unittest.main()
