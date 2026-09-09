"""Public-input validation and byte ownership; no Docker, credentials or models."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import contextlib
import io

spec=importlib.util.spec_from_file_location('pw_review_feedback',Path(__file__).with_name('run-review-feedback.py'))
feedback=importlib.util.module_from_spec(spec);spec.loader.exec_module(feedback)


class ReviewFeedbackTest(unittest.TestCase):
    def fixture(self,root):
        source=root/'original';source.mkdir()
        files={k:'protected:'+k+'\n' for k in feedback.PROTECTED}
        files.update({'notes/work.md':'# Old work\n','.planning/task/task_plan.md':'# Task\nCurrent phase stale\n','.planning/task/progress.md':'# Actual records\n'})
        archive=root/'archive.tgz';archive.write_bytes(b'synthetic archive only; no native execution')
        assessment={'status':'Passed','controller':{'host':'pi','version':'0.4.0-rc.4','npm_sha256':feedback.digest(archive),'exact_artifact':'Passed','offline_tests':'Passed','independent_bytes':'Passed'},'assertions':{k:True for k in ['approved_requirement_preserved','user_edit_preserved','tests_passed','fixed_bom']}}
        after=source/'after.json';after.write_text(json.dumps(files))
        original=source/'assessment.json';original.write_text(json.dumps(assessment))
        review={'schema_version':1,'host':'pi','npm_sha256':feedback.digest(archive),'source_after_sha256':feedback.digest(after),'source_assessment_sha256':feedback.digest(original),'original_semantic_status':'Failed','original_scope':'Fix export encoding and maintain accurate documentation.','allowed_documents':['.planning/task/task_plan.md'],
                'findings':[{'id':'R1','file':'.planning/task/task_plan.md','observation':'Current Phase contradicts completed phases.','correction':'Reconcile with existing phase completion evidence.','evidence':['Prior final tests Passed; no new test execution authorized.']}]}
        path=root/'review.json';path.write_text(json.dumps(review))
        args=argparse.Namespace(after=after,after_sha256=feedback.digest(after),review=path,review_sha256=feedback.digest(path),original_assessment=original,assessment_sha256=feedback.digest(original),archive=archive,archive_sha256=feedback.digest(archive),host='pi',output=root/'new-run')
        return args,files,review
    def rewrite_review(self,args,value):
        args.review.write_text(json.dumps(value));args.review_sha256=feedback.digest(args.review)
    def test_valid_review_preserves_original_automatic_pass_and_semantic_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            args,files,review=self.fixture(Path(temporary))
            result=feedback.validate_inputs(args)
            self.assertEqual(result[0],files);self.assertEqual(result[2]['status'],'Passed')
            self.assertEqual(result[1]['original_semantic_status'],'Failed')
            self.assertFalse(args.output.exists())
    def test_unsafe_snapshot_and_modified_digests_rejected(self):
        for name in ['../escape','/absolute','.git/config','.pi/settings.json','node_modules/x','sessions/history.json','auth.json','native-events.jsonl']:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as temporary:
                args,files,review=self.fixture(Path(temporary));files[name]='forbidden'
                args.after.write_text(json.dumps(files));args.after_sha256=feedback.digest(args.after)
                review['source_after_sha256']=args.after_sha256;self.rewrite_review(args,review)
                with self.assertRaises(ValueError):feedback.validate_inputs(args)
                self.assertFalse(args.output.exists())
        with tempfile.TemporaryDirectory() as temporary:
            args,_,_=self.fixture(Path(temporary));args.after.write_text('{}')
            with self.assertRaises(ValueError):feedback.validate_inputs(args)
    def test_review_cannot_expand_to_code_requirements_or_new_files(self):
        for filename in ['export_text.py','tests/test_export_text.py','notes/contract.md','user-note.txt','README.md','new.md']:
            with self.subTest(filename=filename),tempfile.TemporaryDirectory() as temporary:
                args,_,review=self.fixture(Path(temporary));review['allowed_documents']=[filename];review['findings'][0]['file']=filename;self.rewrite_review(args,review)
                with self.assertRaises(ValueError):feedback.validate_inputs(args)
    def test_no_old_chat_schema_or_host_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            args,_,review=self.fixture(Path(temporary));review['transcript']='old chat';self.rewrite_review(args,review)
            with self.assertRaises(ValueError):feedback.validate_inputs(args)
            del review['transcript'];review['host']='dsh';self.rewrite_review(args,review)
            with self.assertRaises(ValueError):feedback.validate_inputs(args)
    def test_protected_bytes_and_cold_snapshot_are_exact(self):
        with tempfile.TemporaryDirectory() as temporary:
            args,files,review=self.fixture(Path(temporary));work=Path(temporary)/'work';feedback.materialize(work,files)
            for name,value in files.items():self.assertEqual((work/name).read_bytes(),value.encode())
            corrected=dict(files);corrected['.planning/task/task_plan.md']='fixed historical state\n'
            self.assertTrue(all(feedback.protected_result(files,corrected,review['allowed_documents']).values()))
            corrected['user-note.txt']+='changed'
            self.assertFalse(feedback.protected_result(files,corrected,review['allowed_documents'])['protected_bytes_preserved'])
            self.assertFalse(feedback.protected_result(files,files,review['allowed_documents'])['only_allowed_records_changed'])
    def test_original_run_output_rejected_and_parse_precedes_auth_or_docker(self):
        with tempfile.TemporaryDirectory() as temporary:
            args,_,_=self.fixture(Path(temporary));args.output=args.after.parent/'new'
            with self.assertRaises(ValueError):feedback.validate_inputs(args)
            argv=['--after',str(args.after),'--after-sha256','invalid','--review',str(args.review),'--review-sha256',args.review_sha256,'--original-assessment',str(args.original_assessment),'--assessment-sha256',args.assessment_sha256,'--archive',str(args.archive),'--archive-sha256',args.archive_sha256,'--host','pi','--direct-provider-config','/never-read-auth','--output',str(args.output)]
            with patch.object(feedback,'load_module') as load,patch.object(feedback.subprocess,'check_output') as docker:
                with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):feedback.main(argv)
                load.assert_not_called();docker.assert_not_called()
            self.assertFalse(args.output.exists())

    def _owner_chain(self,residual=False,cleanup_error=None):
        with tempfile.TemporaryDirectory() as temporary:
            args,files,review=self.fixture(Path(temporary))
            args.files=files;args.review_data=review;args.assessment_data=feedback.read_json(args.original_assessment)
            args.image='sha256:'+'a'*64;args.package={'version':'0.4.0-rc.4'};args.model='fake';args.timeout=30;args.direct_provider_config=Path('/not-read')
            snapshots=lambda fixture,root:{str(p.relative_to(root)):p.read_text() for p in root.rglob('*') if p.is_file()}
            fixture=SimpleNamespace(PROMPTS={'cold-reader':'Read only the project files and identify remaining work.'},BOUNDARY=' No history or cache access.')
            runner=SimpleNamespace(load_fixture_module=lambda:fixture,credentials=lambda *a:{'api_key':'FAKE_TEST_SECRET'},project_snapshot=snapshots,model_text=lambda host,text:{'final':text,'errors':[],'tool_calls':[]},
                                   resource_preflight=lambda path:{'checked':True},cleanup_finished_case=lambda *a:{'status':'Passed'})
            payloads=[]
            def run(command,**kwargs):
                if command[1:3]==['rm','-f']:
                    if cleanup_error=='rm': raise feedback.subprocess.CalledProcessError(1,command,stderr='FAKE_TEST_SECRET')
                    return SimpleNamespace(returncode=0)
                payload=json.loads(kwargs['input']);payloads.append(payload)
                for limit in ['--cpus=2','--memory=3g','--memory-swap=3g','--pids-limit=256','/tmp:mode=1777,size=512m']:
                    self.assertIn(limit,command)
                stage=args.output/payload['case'];raw=stage/'raw'
                if payload['case']=='review-correction': (stage/'project/.planning/task/task_plan.md').write_text('Corrected Current Phase based on prior evidence.\n')
                (raw/'model.stdout').write_text('Owner response' if payload['case']=='review-correction' else 'Independent file-only cold read')
                feedback.write_json(raw/'controller.json',{'status':'Passed','npm_sha256':args.archive_sha256})
                return SimpleNamespace(returncode=0)
            cleanup_calls=0
            def check(command,**kwargs):
                nonlocal cleanup_calls
                if command[1:3]==['image','inspect']: return args.image+'\n'
                if len(payloads)==2:
                    cleanup_calls+=1
                    if (cleanup_error=='ps' and cleanup_calls==1) or (cleanup_error=='recheck' and cleanup_calls==2) or (cleanup_error=='final' and cleanup_calls==3):
                        raise feedback.subprocess.CalledProcessError(1,command,stderr='FAKE_TEST_SECRET')
                    if cleanup_error=='rm' and '--filter' in command: return 'OWN_CONTAINER\n'
                if residual and '--filter' in command: return 'OWN_CONTAINER_STILL_PRESENT\n'
                return ''
            with patch.object(feedback,'parse_args',return_value=args),patch.object(feedback,'load_module',return_value=runner),patch.object(feedback.subprocess,'check_output',side_effect=check),patch.object(feedback.subprocess,'run',side_effect=run):
                self.assertEqual(feedback.main([]),1 if residual or cleanup_error else 0)
            report=feedback.read_json(args.output/'summary.json')
            self.assertEqual(report['status'],'Failed' if residual or cleanup_error else 'Awaiting independent semantic review')
            if cleanup_error:
                self.assertEqual(report['cleanup']['status'],'Failed')
                self.assertEqual(report['cleanup']['error_kind'],'CalledProcessError')
            else: self.assertEqual(bool(report['cleanup']['remaining_own_containers']),residual)
            self.assertTrue(report['original_results_unchanged'])
            self.assertEqual(set(report['original_input_verification']),{'after','assessment','review'})
            self.assertEqual(report['snapshot_assertion_scope']['coverage'],'project_snapshot text entries only')
            self.assertIn('executable bits',report['snapshot_assertion_scope']['excluded'])
            for stage in report['stages'].values(): self.assertEqual(stage['snapshot_assertion_scope'],report['snapshot_assertion_scope'])
            self.assertEqual(report['original_semantic_status'],'Failed')
            self.assertEqual(report['resource_preflight'],{'checked':True})
            self.assertEqual([p['case'] for p in payloads],['review-correction','cold-reader'])
            self.assertIn('Current Phase contradicts',payloads[0]['prompt'])
            self.assertNotIn('Current Phase contradicts',payloads[1]['prompt'])
            self.assertEqual(feedback.read_json(args.output/'review-correction/after.json'),feedback.read_json(args.output/'cold-reader/before.json'))
            self.assertEqual(feedback.read_json(args.output/'cold-reader/before.json'),feedback.read_json(args.output/'cold-reader/after.json'))
            self.assertEqual(feedback.digest(args.output/'original-after.json'),args.after_sha256)
            self.assertEqual(feedback.digest(args.after),args.after_sha256)
            self.assertNotIn('FAKE_TEST_SECRET',(args.output/'summary.json').read_text())

    def test_owner_cold_reader_chain_keeps_feedback_out_of_cold_prompt(self):
        self._owner_chain()

    def test_resource_shortage_stops_before_auth_docker_or_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            args,_,_=self.fixture(Path(temporary))
            from unittest.mock import Mock
            runner=SimpleNamespace(load_fixture_module=lambda:None,
                resource_preflight=Mock(side_effect=RuntimeError('Resource preflight')),
                credentials=Mock())
            with patch.object(feedback,'parse_args',return_value=args),patch.object(feedback,'load_module',return_value=runner), \
                 patch.object(feedback.subprocess,'check_output') as docker:
                with self.assertRaisesRegex(RuntimeError,'Resource preflight'):feedback.main([])
            runner.credentials.assert_not_called();docker.assert_not_called()
            self.assertFalse(args.output.exists())

    def test_exception_cleanup_removes_only_proven_unreferenced_cache(self):
        runner_impl=feedback.load_module('pw_cleanup_real',Path(__file__).with_name('run-five-agent-release.py'))
        for failure in ['timeout','invalid-controller']:
            with self.subTest(failure=failure),tempfile.TemporaryDirectory() as temporary:
                args,files,review=self.fixture(Path(temporary))
                args.files=files;args.review_data=review;args.assessment_data=feedback.read_json(args.original_assessment)
                args.image='sha256:'+'a'*64;args.package={'version':'0.4.0-rc.4'}
                args.model='fake';args.timeout=30;args.direct_provider_config=Path('/not-read')
                calls=[]
                def cleanup(project,name):
                    calls.append(name)
                    return {'status':'Passed','removed_unreferenced_versions':runner_impl.clean_completed_store(project)}
                runner=SimpleNamespace(load_fixture_module=lambda:SimpleNamespace(BOUNDARY=''),
                    resource_preflight=lambda path:{'checked':True},credentials=lambda *a:{},
                    project_snapshot=lambda fixture,root:{str(p.relative_to(root)):p.read_text() for p in root.rglob('*') if p.is_file()},
                    cleanup_finished_case=cleanup)
                def run(command,**kwargs):
                    stage=args.output/'review-correction';store=stage/'project/.planweft'
                    (store/'versions/rc').mkdir(parents=True)
                    (store/'versions/rc/cache').write_text('rebuildable')
                    (store/'installations.json').write_text('{"agents":{}}')
                    if failure=='timeout': raise feedback.subprocess.TimeoutExpired(command,30)
                    (stage/'raw/controller.json').write_text('{invalid')
                    return SimpleNamespace(returncode=0)
                with patch.object(feedback,'parse_args',return_value=args),patch.object(feedback,'load_module',return_value=runner), \
                     patch.object(feedback.subprocess,'check_output',side_effect=lambda c,**k:args.image+'\n' if c[1:3]==['image','inspect'] else ''), \
                     patch.object(feedback.subprocess,'run',side_effect=run):
                    self.assertEqual(feedback.main([]),1)
                self.assertEqual(len(calls),1)
                self.assertFalse((args.output/'review-correction/project/.planweft/versions').exists())
                self.assertTrue((args.output/'review-correction/project/.planweft/installations.json').is_file())
                report=feedback.read_json(args.output/'summary.json')
                self.assertEqual(report['status'],'Failed')
                self.assertTrue(report['cleanup']['stage_caches']['review-correction']['removed_unreferenced_versions'])

    def test_cleanup_rechecks_own_container_residue(self):
        self._owner_chain(residual=True)

    def test_cleanup_errors_still_save_failed_summary_and_verify_originals(self):
        for step in ['ps','rm','recheck','final']:
            with self.subTest(step=step): self._owner_chain(cleanup_error=step)

    def test_dsh_uses_native_events_and_requires_completed_turn(self):
        runner=feedback.load_module('pw_feedback_native_parser',feedback.ROOT/'tests/run-five-agent-release.py')
        assistant={'type':'assistant/message','data':{'message':{'content':[{'type':'text','text':'Native final answer'}]}}}
        completed={'type':'turn/end','data':{'reason':{'kind':'completed'}}}
        failed={'type':'turn/end','data':{'reason':{'kind':'error'}}}
        cases=[('missing',None,False,False,True),('plain',['Plain non-JSON output'],False,False,True),
               ('answer-only',[assistant],True,False,True),('completed',[assistant,completed],True,True,True),
               ('error',[assistant,failed],True,False,False)]
        for name,events,answer,ended,no_errors in cases:
            with self.subTest(name=name),tempfile.TemporaryDirectory() as temporary:
                raw=Path(temporary)
                # Even structured events on stdout cannot stand in for DSH's
                # absent native stream (nor can its ordinary human output).
                (raw/'model.stdout').write_text('Human final answer\n'+json.dumps(assistant)+'\n'+json.dumps(completed))
                if events is not None:
                    (raw/'native-events.jsonl').write_text('\n'.join(e if isinstance(e,str) else json.dumps(e) for e in events))
                trace,checks=feedback.model_trace(runner,'dsh',raw)
                self.assertEqual(checks,{'model_answer_present':answer,'no_model_errors':no_errors,'native_turn_completed':ended})
                self.assertEqual(trace['final'],'Native final answer' if answer else '')
                self.assertEqual(all(checks.values()),name=='completed')

    def test_model_and_time_budget_validated_before_input_auth_or_docker(self):
        with tempfile.TemporaryDirectory() as temporary:
            args,_,_=self.fixture(Path(temporary))
            argv=['--after',str(args.after),'--after-sha256',args.after_sha256,'--review',str(args.review),'--review-sha256',args.review_sha256,'--original-assessment',str(args.original_assessment),'--assessment-sha256',args.assessment_sha256,'--archive',str(args.archive),'--archive-sha256',args.archive_sha256,'--host','pi','--direct-provider-config','/never-read-auth','--output',str(args.output)]
            for extra in [['--model',''],['--model','bad model'],['--model','bad\nmodel'],['--timeout','601']]:
                with self.subTest(extra=extra),patch.object(feedback,'validate_inputs') as inputs,patch.object(feedback,'load_module') as load,contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):feedback.main(argv+extra)
                    inputs.assert_not_called();load.assert_not_called()


if __name__=='__main__':unittest.main()
