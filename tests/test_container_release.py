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
    def test_bad_arguments_have_no_output_side_effect(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);archive=root/'package.tgz';output=root/'absent'
            with tarfile.open(archive,'w:gz') as tar:
                data=json.dumps({'name':'planweft','version':'0.4.0-rc.1'}).encode()
                info=tarfile.TarInfo('package/package.json');info.size=len(data)
                tar.addfile(info,io.BytesIO(data))
            base=[sys.executable,str(ROOT/'tests/run-five-agent-release.py'),'--archive',str(archive),'--output',str(output)]
            for flags in [['--host','unknown'],['--host','codex','--timeout','0'],
                          ['--host','codex','--cases','cold-reader'],
                          ['--host','codex','--cases','cold-reader','maintenance'],['--host','codex','--image-lock',str(root/'missing')]]:
                with self.subTest(flags=flags):
                    result=subprocess.run(base+flags,capture_output=True)
                    self.assertEqual(result.returncode,2)
                    self.assertFalse(output.exists())

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
