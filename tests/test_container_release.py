"""Release runner boundaries: invalid inputs cannot create state or access Docker."""
import importlib.util
import hashlib
import io
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


class ContainerReleaseTest(unittest.TestCase):
    def test_mixed_scenario_payload_does_not_forward_auth_to_installation(self):
        from types import SimpleNamespace
        runner=module('pw_case_auth','tests/run-five-agent-release.py')
        runtime=module('pw_case_auth_runtime','tests/five_agent_runtime.py')
        args=SimpleNamespace(codex_model='test-codex',model='test-model',timeout=600,trace_gate_processes=False)
        secret={'api_key':'synthetic-never-forward'}
        for host, case in [('codex','preflight'),('claude','lifecycle'),('pi','package-approval')]:
            payload=runner.scenario_payload(args,host,case,'synthetic',secret)
            self.assertNotIn('synthetic-never-forward',json.dumps(payload))
            # Reject callers bypassing the outer runner before even creating
            # HOME or invoking the credential preparation function.
            with patch.object(runtime,'setup_environment') as setup,patch.object(runtime,'prepare_model') as prepare:
                with self.assertRaisesRegex(ValueError,'No-model scenario'):
                    runtime.controller({**payload,'secret':secret})
                setup.assert_not_called();prepare.assert_not_called()
        self.assertEqual(runner.scenario_payload(args,'codex','maintenance','synthetic',secret)['secret'],secret)
        self.assertEqual(secret,{'api_key':'synthetic-never-forward'})

    def test_claude_collection_never_satisfies_release_gate(self):
        runner=module('pw_claude_collection','tests/run-five-agent-release.py')
        for success in [True,False]:
            result=runner.reminder_collection_assessment({'collection_completed':success,'no_errors':True})
            self.assertEqual(result['status'],'Not Run' if success else 'Failed')
            self.assertEqual(result['reminder_deduplication'],'Not Run')
            self.assertTrue(result['diagnostic_only'])
        with patch.object(runner,'resource_preflight') as resources,patch.object(Path,'is_file') as files:
            with self.assertRaises(SystemExit):
                runner.parse_args(['--host','codex','--cases','reminder-collection',
                                   '--archive','absent.tgz','--output','absent'])
            resources.assert_not_called();files.assert_not_called()

    def test_codex_projection_omits_provider_and_unknown_registration_fields(self):
        runtime=module('pw_codex_projection','tests/five_agent_runtime.py')
        with tempfile.TemporaryDirectory() as temporary:
            config=Path(temporary)/'config.toml'
            raw=b'model="synthetic-model"\n[marketplaces.owned]\nsource="/synthetic/registry"\nsource_type="local"\nextra="omit"\n[plugins."planweft@owned"]\nenabled=true\nextra="omit"\n[model_providers.synthetic]\napi_key="never-export"\n'
            config.write_bytes(raw)
            self.assertEqual(runtime.codex_registration_projection(config), {
                'config_sha256':hashlib.sha256(raw).hexdigest(),
                'marketplaces':{'owned':{'source':'/synthetic/registry','source_type':'local'}},
                'plugins':{'planweft@owned':{'enabled':True}}})
            self.assertEqual(config.read_bytes(),raw)
            config.write_text('[marketplaces.owned]\nsource="a"\nsource="b"\n')
            with self.assertRaises(ValueError): runtime.codex_registration_projection(config)

    def test_regression_effectiveness_uses_behavior_not_method_count(self):
        runtime=module('pw_regression_effectiveness','tests/five_agent_runtime.py')
        fixture=module('pw_regression_fixture','tests/run-pwf-smoke.py')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'tests').mkdir()
            (root/'export_text.py').write_text(fixture.BASE['export_text.py'].replace('utf-8-sig','utf-8'))
            tests=root/'tests/test_export.py'
            tests.write_text('import unittest\nimport tempfile\nfrom pathlib import Path\nfrom export_text import write_export\n'
                             'class Test(unittest.TestCase):\n'
                             ' def test_bytes(self):\n'
                             '  with tempfile.TemporaryDirectory() as d:\n'
                             '   p=Path(d)/"中文 file";write_export("示例\\n",p);self.assertEqual(p.read_bytes(),"示例\\n".encode())\n')
            def check():
                fixed=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,text=True,capture_output=True)
                return runtime.regression_effectiveness(root,fixed)
            self.assertEqual(check()['status'],'Passed')
            self.assertEqual(hashlib.sha256(fixture.BASE['export_text.py'].encode()).hexdigest(),check()['original_module_sha256'])
            for content in ['import unittest\nclass Test(unittest.TestCase):\n def test_noop(self): pass\n',
                            'raise ImportError("missing dependency")\n',
                            'import unittest\nclass Test(unittest.TestCase):\n def test_bad(self): self.fail("always fails")\n']:
                tests.write_text(content)
                shutil.rmtree(root/'tests/__pycache__',ignore_errors=True)
                self.assertEqual(check()['status'],'Failed')

    def test_codex_js_wrapper_allows_only_one_literal_native_command(self):
        runtime=module('pw_codex_js_deny','tests/five_agent_runtime.py')
        source='const r = await tools.exec_command({"cmd":"python3 /workspace/write-probe.py","workdir":"/workspace","yield_time_ms":10000,"max_output_tokens":2000});\ntext(JSON.stringify(r));\n'
        self.assertEqual(runtime.single_exec_command(source)['cmd'],'python3 /workspace/write-probe.py')
        for bad in [source+'text("rejected: PW_NATIVE_DENY");',source.replace('text(JSON.stringify(r))','text("rejected: PW_NATIVE_DENY")'),
                    source.replace('python3 /workspace/write-probe.py',"printf 'python3 /workspace/write-probe.py rejected: PW_NATIVE_DENY'; false"),
                    source.replace('"workdir":"/workspace"','"workdir":"/other"')]:
            self.assertIsNone(runtime.single_exec_command(bad))
        call={'type':'response_item','payload':{'type':'custom_tool_call','name':'exec','input':source,'call_id':'one'}}
        result={'type':'response_item','payload':{'type':'custom_tool_call_output','call_id':'one','output':[{'type':'input_text','text':'exec_command failed: Rejected(command rejected: PW_NATIVE_DENY)'}]}}
        records='\n'.join(map(json.dumps,[call,result]))
        self.assertEqual(len(runtime.codex_denial_records(records)),1)

    def test_codex_rollout_denial_requires_matched_native_call_and_output(self):
        runtime=module('pw_codex_rollout_deny','tests/five_agent_runtime.py')
        call={'type':'response_item','payload':{'type':'function_call','name':'exec_command','call_id':'one',
              'arguments':json.dumps({'cmd':'python3 /workspace/write-probe.py'})}}
        result={'type':'response_item','payload':{'type':'function_call_output','call_id':'one',
                'output':'python3 /workspace/write-probe.py rejected: PW_NATIVE_DENY'}}
        def parse(values): return runtime.codex_denial_records('\n'.join(json.dumps(v) for v in values))
        self.assertEqual(len(parse([call,result])),1)
        self.assertEqual(parse([result]),[])
        self.assertEqual(parse([call,{**result,'type':'event_msg'}]),[])
        result['payload']['call_id']='other'
        self.assertEqual(parse([call,result]),[])

    def test_native_rule_denial_ignores_model_claims_and_ask_rejection(self):
        runtime=module('pw_native_rule_deny','tests/five_agent_runtime.py')
        command='python3 /workspace/write-probe.py'
        call={'type':'assistant','message':{'content':[{'type':'tool_use','name':'Bash','id':'one','input':{'command':command}}]}}
        result={'type':'result','permission_denials':[{'tool_name':'Bash','tool_use_id':'one','tool_input':{'command':command}}]}
        text=json.dumps(call)+'\n'+json.dumps(result)
        self.assertFalse(runtime.native_rule_denial('claude',text))
        reason={'type':'system','subtype':'permission_denied','tool_use_id':'one',
                'decision_reason_type':'rule','decision_reason':'Bash('+command+') deny'}
        self.assertTrue(runtime.native_rule_denial('claude',text+'\n'+json.dumps(reason)))
        for kind in ['mode','classifier','asyncAgent']:
            self.assertFalse(runtime.native_rule_denial('claude',text+'\n'+json.dumps({**reason,'decision_reason_type':kind})))
        self.assertFalse(runtime.native_rule_denial('claude',json.dumps(result)))
        part={'type':'tool_use','part':{'tool':'bash','state':{'status':'error','input':{'command':command},
              'error':'The user has specified a rule which prevents this call '+command+' deny'}}}
        self.assertTrue(runtime.native_rule_denial('opencode',json.dumps(part)))
        part['part']['state']['error']='The user rejected permission to use this specific tool call.'
        self.assertFalse(runtime.native_rule_denial('opencode',json.dumps(part)))

    def test_dsh_denial_binds_structured_error_to_actual_write_call(self):
        runtime=module('pw_dsh_deny','tests/five_agent_runtime.py')
        call={'type':'tool/call','data':{'callId':'one','name':'write','arguments':json.dumps({'file_path':'/workspace/protected.txt'})}}
        result={'type':'tool/result','data':{'error':{'code':'FS_SANDBOX_DENIED'},
                   'message':{'source':{'callId':'one'},'content':[{'type':'tool-result','isError':True,'content':[{'text':'denied under read-only mode'}]}]}}}
        def check(value): return runtime.native_dsh_denial(json.dumps(call)+'\n'+json.dumps(value))
        self.assertTrue(check(result))
        for code in ['FS_NOT_OBSERVED','PermissionError']:
            self.assertFalse(check({**result,'data':{**result['data'],'error':{'code':code}}}))
        result['data']['message']['source']['callId']='other'
        self.assertFalse(check(result))

    def test_resource_headroom_is_checked_without_creating_output(self):
        from types import SimpleNamespace
        runner=module('pw_headroom','tests/run-five-agent-release.py')
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/'absent'
            for ram,storage,passes in [(3,20,False),(8,7,False),(6,12,True)]:
                with patch.object(runner.shutil,'disk_usage',return_value=SimpleNamespace(free=storage*1024**3)), \
                     patch.object(Path,'read_text',return_value=f'MemAvailable: {ram*1024**2} kB\n'):
                    if passes: self.assertEqual(runner.resource_preflight(output)['available_memory_bytes'],ram*1024**3)
                    else:
                        with self.assertRaisesRegex(RuntimeError,'Resource preflight'): runner.resource_preflight(output)
                self.assertFalse(output.exists())

    def test_cache_cleanup_preserves_owned_records_and_referenced_versions(self):
        runner=module('pw_cache_cleanup','tests/run-five-agent-release.py')
        with tempfile.TemporaryDirectory() as temporary:
            project=Path(temporary);store=project/'.planweft';versions=store/'versions'
            versions.mkdir(parents=True);(versions/'cache.bin').write_bytes(b'cache')
            (project/'progress.md').write_text('test evidence')
            receipt=store/'installations.json';receipt.write_text('{"agents":{"pi":{"version":"old"}}}')
            self.assertFalse(runner.clean_completed_store(project));self.assertTrue(versions.exists())
            receipt.write_text('{"agents":{}}')
            self.assertTrue(runner.clean_completed_store(project));self.assertFalse(versions.exists())
            self.assertTrue(receipt.exists());self.assertEqual((project/'progress.md').read_text(),'test evidence')
            versions.symlink_to(project,target_is_directory=True)
            self.assertFalse(runner.clean_completed_store(project));self.assertTrue((project/'progress.md').exists())

    def test_failed_removal_never_cleans_a_possibly_live_store(self):
        runner=module('pw_live_cache','tests/run-five-agent-release.py')
        for outcome in ['still-running-id\n',subprocess.CalledProcessError(1,['docker','ps'])]:
            with patch.object(runner.subprocess,'check_output',side_effect=outcome if isinstance(outcome,Exception) else None,
                              return_value=outcome), patch.object(runner,'clean_completed_store') as clean:
                self.assertEqual(runner.cleanup_finished_case(Path('/unused'),'owned-case')['status'],'Failed')
                clean.assert_not_called()
        with patch.object(runner.subprocess,'check_output',return_value=''), \
             patch.object(runner,'clean_completed_store',return_value=True) as clean:
            self.assertEqual(runner.cleanup_finished_case(Path('/unused'),'owned-case')['status'],'Passed')
            clean.assert_called_once()

    def test_project_snapshot_prunes_stores_before_reading_and_keeps_nested_docs(self):
        runner=module('pw_snapshot_runner','tests/run-five-agent-release.py')
        fixture=module('pw_snapshot_fixture','tests/run-pwf-smoke.py')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            excluded={'.planweft','.pi','.opencode','.claude','opencode.json'}
            for name in excluded-{'opencode.json'}:
                (root/name/'cache').mkdir(parents=True)
                (root/name/'cache/large.bin').write_bytes(b'not project evidence')
            (root/'opencode.json').write_text('{}')
            (root/'notes/.planweft').mkdir(parents=True)
            (root/'notes/.planweft/design.md').write_text('Nested documentation stays visible.\n')
            (root/'task_plan.md').write_bytes(b'Current plan\r\n')
            (root/'result.bin').write_bytes(b'\xff')
            # Establish the former filtered result on small files, then make
            # any excluded read fail: equivalence alone would miss the OOM risk.
            expected={p:v for p,v in fixture.snapshot(root).items() if p.split('/')[0] not in excluded}
            original=Path.read_bytes
            def bounded_read(path):
                self.assertNotIn(path.relative_to(root).parts[0],excluded)
                return original(path)
            with patch.object(Path,'read_bytes',bounded_read):
                self.assertEqual(runner.project_snapshot(fixture,root),expected)
            self.assertIn('notes/.planweft/design.md',expected)
            self.assertEqual(expected['task_plan.md'],'Current plan\r\n')

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
