"""Release runner boundaries: invalid inputs cannot create state or access Docker."""
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


class ContainerReleaseTest(unittest.TestCase):
    def test_claude_stream_blocks_are_not_extra_model_responses(self):
        runner=module('pw_claude_responses','tests/run-five-agent-release.py')
        events=[{'type':'assistant','message':{'id':'one','content':[{'type':kind}]}} for kind in ['thinking','text']]
        parse=lambda:runner.model_text('claude','\n'.join(json.dumps(e) for e in events))
        self.assertEqual(parse()['assistant_responses'],1)
        events.append({'type':'assistant','message':{'id':'followup','content':[{'type':'text'}]}})
        self.assertEqual(parse()['assistant_responses'],2)

    @unittest.skipUnless(sys.platform=='linux','inotify observation is a Linux container lane')
    def test_gate_observer_distinguishes_read_from_no_hook(self):
        runtime=module('pw_gate_observer','tests/five_agent_runtime.py')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);runtime.WORK=root
            for name in ['.stop_blocks','.gate_last_ledger']: (root/name).write_text('1\n')
            watch=runtime.watch_gate_reads()
            (root/'unrelated.txt').write_text('fixture')
            empty=runtime.finish_gate_reads(watch)
            self.assertEqual(empty['events'],[])
            watch=runtime.watch_gate_reads()
            self.assertEqual((root/'.stop_blocks').read_text(),'1\n')
            read=runtime.finish_gate_reads(watch)
            self.assertFalse(read['overflow'])
            self.assertEqual(read['events'],[{'file':'.stop_blocks','event':'IN_ACCESS'}])

    def test_bad_arguments_have_no_output_side_effect(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);archive=root/'package.tgz';output=root/'absent'
            with tarfile.open(archive,'w:gz') as tar:
                data=json.dumps({'name':'planweft','version':'0.4.0-rc.1'}).encode()
                info=tarfile.TarInfo('package/package.json');info.size=len(data)
                tar.addfile(info,io.BytesIO(data))
            base=[sys.executable,str(ROOT/'tests/run-five-agent-release.py'),'--archive',str(archive),'--output',str(output)]
            for flags in [['--host','unknown'],['--host','codex','--timeout','0'],
                          ['--host','pi','--cases','gate-cap'],
                          ['--host','claude','--cases','gate-cap'],
                          ['--host','codex','--cases','continuation-limit'],
                          ['--host','codex','--cases','cold-reader'],
                          ['--host','codex','--cases','cold-reader','maintenance'],['--host','codex','--image-lock',str(root/'missing')]]:
                with self.subTest(flags=flags):
                    result=subprocess.run(base+flags,capture_output=True)
                    self.assertEqual(result.returncode,2)
                    self.assertFalse(output.exists())

    def test_stop_fixtures_separate_cap_from_stall(self):
        import hashlib
        runner=module('pw_stop_fixture','tests/run-five-agent-release.py')
        cap=runner.stop_fixture('gate-cap');stall=runner.stop_fixture('gate-stall')
        for files in [cap,stall,runner.stop_fixture('gated-continuation')]:
            self.assertIn('### Phase 1:',files['task_plan.md'])
            self.assertIn('**Status:** in_progress',files['task_plan.md'])
            self.assertEqual(files['.plan-attestation'].strip(),hashlib.sha256(files['task_plan.md'].encode()).hexdigest())
        self.assertEqual(cap['.stop_blocks'],stall['.stop_blocks'])
        self.assertEqual(cap['.gate_last_ledger'],'0\n')
        self.assertEqual(len(cap['ledger-owner.jsonl'].splitlines()),1)
        self.assertNotIn('ledger-owner.jsonl',stall)
        self.assertEqual(cap,runner.stop_fixture('gate-cap-disabled'))
        self.assertEqual(stall,runner.stop_fixture('gate-stall-disabled'))
        self.assertNotIn('.stop_blocks',runner.stop_fixture('gated-continuation'))
        for case in ['stopping','continuation-limit']:
            self.assertNotIn('.mode',runner.stop_fixture(case))

    def test_direct_provider_rejects_memory_configuration_and_nonofficial_routes(self):
        from types import SimpleNamespace
        runner=module('pw_direct_provider','tests/run-five-agent-release.py')
        with tempfile.TemporaryDirectory() as temporary:
            config=Path(temporary)/'provider.json'
            args=SimpleNamespace(cases=['context'],direct_provider_config=config,model_config=None)
            approved={'base_url':'https://api.deepseek.com/v1','api_key':'fixture-only-secret'}
            config.write_text(json.dumps(approved))
            self.assertEqual(runner.credentials(args,'pi'),approved)
            for rejected in [{**approved,'memory':{'enabled':True}},
                             {**approved,'base_url':'https://memory.example/v1'},
                             {**approved,'base_url':'https://api.deepseek.com/v1?gateway=example'},
                             {**approved,'base_url':'https://user@api.deepseek.com/v1'}]:
                config.write_text(json.dumps(rejected))
                with self.assertRaises(ValueError): runner.credentials(args,'dsh')

    def test_archive_symlink_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);archive=root/'package.tgz';output=root/'absent'
            with tarfile.open(archive,'w:gz') as tar:
                item=tarfile.TarInfo('package/escape');item.type=tarfile.SYMTYPE;item.linkname='/etc'
                tar.addfile(item)
            result=subprocess.run([sys.executable,str(ROOT/'tests/run-five-agent-release.py'),
                '--archive',str(archive),'--output',str(output),'--host','codex'],capture_output=True)
            self.assertEqual(result.returncode,2);self.assertFalse(output.exists())

    def test_history_sanitization_is_recursive_and_idempotent(self):
        sanitize=module('pw_sanitize','scripts/sanitize-release-history.py').sanitize
        content=b'/home/psi/workspace/example\r\nkeep original test result\n'
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode='w:gz') as tar:
            item=tarfile.TarInfo('trace.log');item.size=len(content);item.mode=0o755
            item.uid=1000;item.gid=1000;item.uname='private';item.gname='private'
            tar.addfile(item,io.BytesIO(content))
        cleaned=sanitize(buf.getvalue(),'evidence.tar.gz')
        self.assertEqual(cleaned,sanitize(cleaned,'evidence.tar.gz'))
        with tarfile.open(fileobj=io.BytesIO(cleaned)) as tar:
            item=tar.next();self.assertEqual(item.mode,0o755)
            self.assertEqual((item.uid,item.gid,item.uname,item.gname),(0,0,'',''))
            self.assertEqual(tar.extractfile(item).read(),content.replace(b'/home/psi/',b'/home/USER/'))

    def test_native_model_events_are_parsed_without_counting_user_prompt(self):
        runner=module('pw_runner','tests/run-five-agent-release.py')
        text='\n'.join(json.dumps(x) for x in [
            {'type':'message_end','message':{'role':'custom','content':'not an assistant answer'}},
            {'type':'message_end','message':{'role':'assistant','content':[{'type':'text','text':'answer'}, {'type':'toolCall','name':'read'}]}},
        ])
        result=runner.model_text('pi',text)
        self.assertEqual(result['final'],'answer');self.assertEqual(len(result['tool_calls']),1)

    def test_zero_exit_native_stream_can_still_report_model_failure(self):
        runner=module('pw_runner_error','tests/run-five-agent-release.py')
        line=json.dumps({'type':'message_end','message':{'role':'assistant','content':[],
            'stopReason':'error','errorMessage':'401: invalid fixture authentication'}})
        result=runner.model_text('pi',line)
        self.assertFalse(result['final']);self.assertTrue(result['errors'])

    def test_dsh_requires_actual_session_events_for_tool_observation(self):
        runner=module('pw_runner_dsh','tests/run-five-agent-release.py')
        self.assertFalse(runner.model_text('dsh','prose alone')['tool_observation_supported'])
        stream='\n'.join(json.dumps(e) for e in [
            {'type':'tool/call','data':{'name':'read','arguments':'fixture'}},
            {'type':'assistant/message','data':{'message':{'content':[{'type':'text','text':'42'}]}}},
            {'type':'turn/end','data':{'reason':{'kind':'completed'}}}])
        observed=runner.model_text('dsh',stream)
        self.assertTrue(observed['tool_observation_supported']);self.assertEqual(len(observed['tool_calls']),1)
        self.assertEqual(observed['final'],'42')


if __name__=='__main__': unittest.main()
