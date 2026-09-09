#!/usr/bin/env python3
"""A bounded owner-correction -> fresh-reader lane; never replaces the first run.

Review schema v1: host, npm_sha256, source_after_sha256,
source_assessment_sha256, original_semantic_status='Failed', original_scope,
allowed_documents, findings [{id,file,observation,correction,evidence}].
Only concise reviewer facts enter the owner prompt. No chats, auth files, Git
history, native caches or prior model sessions are imported as project input.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path,PurePosixPath
import re
import shutil
import subprocess
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
SHA=re.compile(r'[0-9a-f]{64}')
PROTECTED={'AGENTS.md','README.md','notes/contract.md','user-note.txt','export_text.py','tests/test_export_text.py'}
DENIED_PARTS={'.git','.pi','.dsh','.planweft','.codex','.claude','.cache','node_modules','__pycache__','.pytest_cache','auth.json','credentials.json','native-events.jsonl','sessions','transcripts'}


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def read_json(path):
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise ValueError('Duplicate JSON key')
            result[key]=value
        return result
    if path.stat().st_size>8*1024*1024: raise ValueError('Input JSON exceeds bound')
    return json.loads(path.read_text(),object_pairs_hook=unique)


def safe_project_path(name):
    if not isinstance(name,str) or not name or '\\' in name or ':' in name: return False
    path=PurePosixPath(name)
    return not path.is_absolute() and str(path)==name and not set(path.parts)&(DENIED_PARTS|{'..'}) and all(not p.startswith('.') or p=='.planning' or p in {'.active_plan','.mode','.plan-attestation','.attestation','.stop_blocks','.gate_last_ledger'} for p in path.parts)


def editable_record(name):
    path=PurePosixPath(name)
    return name=='notes/work.md' or (path.name in {'task_plan.md','findings.md','progress.md'} and (len(path.parts)==1 or path.parts[0]=='.planning'))


def validate_inputs(args):
    for path,expected in [(args.after,args.after_sha256),(args.review,args.review_sha256),(args.original_assessment,args.assessment_sha256),(args.archive,args.archive_sha256)]:
        if not SHA.fullmatch(expected) or not path.is_file() or digest(path)!=expected: raise ValueError('Input digest mismatch or missing file')
    files=read_json(args.after);review=read_json(args.review);assessment=read_json(args.original_assessment)
    if not isinstance(files,dict) or not files or len(files)>1000: raise ValueError('Snapshot must be a bounded project text-file mapping')
    if not PROTECTED.issubset(files): raise ValueError('Maintenance snapshot lacks protected fixture files')
    if any(not safe_project_path(k) or not isinstance(v,str) or '\x00' in v for k,v in files.items()): raise ValueError('Snapshot contains unsafe paths, caches, links or non-text data')
    keys={'schema_version','host','npm_sha256','source_after_sha256','source_assessment_sha256','original_semantic_status','original_scope','allowed_documents','findings'}
    if not isinstance(review,dict) or set(review)!=keys or review['schema_version']!=1: raise ValueError('Unsupported review schema')
    if (review['host'],review['npm_sha256'],review['source_after_sha256'],review['source_assessment_sha256'])!=(args.host,args.archive_sha256,args.after_sha256,args.assessment_sha256): raise ValueError('Review provenance differs from inputs')
    if review['original_semantic_status']!='Failed': raise ValueError('Correction requires explicit original semantic failure')
    if not isinstance(review['original_scope'],str) or not 1<=len(review['original_scope'])<=4000: raise ValueError('Original scope must be a concise string')
    allowed=review['allowed_documents']
    if not isinstance(allowed,list) or not allowed or len(allowed)>12 or len(set(allowed))!=len(allowed): raise ValueError('Invalid allowed document list')
    if any(not isinstance(p,str) or p not in files or not editable_record(p) or p in PROTECTED for p in allowed): raise ValueError('Only existing task records may be corrected')
    findings=review['findings']
    if not isinstance(findings,list) or not 1<=len(findings)<=20: raise ValueError('Bounded concrete review findings required')
    ids=set()
    for finding in findings:
        if not isinstance(finding,dict) or set(finding)!={'id','file','observation','correction','evidence'}: raise ValueError('Invalid finding schema')
        if finding['file'] not in allowed: raise ValueError('Finding targets an unapproved document')
        if any(not isinstance(finding[k],str) or not 1<=len(finding[k])<=3000 for k in ['id','observation','correction']): raise ValueError('Finding text must be bounded')
        if finding['id'] in ids: raise ValueError('Duplicate finding id')
        ids.add(finding['id'])
        if not isinstance(finding['evidence'],list) or not 1<=len(finding['evidence'])<=8 or any(not isinstance(x,str) or not 1<=len(x)<=1500 for x in finding['evidence']): raise ValueError('Finding needs concise factual evidence, not transcripts')
    if not isinstance(assessment,dict) or assessment.get('status') not in {'Passed','Failed'}: raise ValueError('Original automated assessment required')
    controller=assessment.get('controller',{})
    if controller.get('host')!=args.host or controller.get('npm_sha256')!=args.archive_sha256: raise ValueError('Original assessment artifact/host mismatch')
    if any(controller.get(k)!='Passed' for k in ['exact_artifact','offline_tests','independent_bytes']): raise ValueError('Code verification must already have passed')
    assertions=assessment.get('assertions',{})
    if any(assertions.get(k) is not True for k in ['approved_requirement_preserved','user_edit_preserved','tests_passed','fixed_bom']): raise ValueError('Protected code/requirements/user checks must already have passed')
    output=args.output.resolve()
    if output.exists() or output==ROOT or ROOT in output.parents: raise ValueError('Output must be new and outside checkout')
    for source in [args.after,args.original_assessment]:
        parent=source.resolve().parent
        original_root=next((p for p in [parent,*parent.parents] if (p/'summary.json').is_file()),parent)
        if output==original_root or original_root in output.parents: raise ValueError('Output cannot modify an original evidence run')
    return files,review,assessment


def parse_args(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['after','review','original-assessment','archive','direct-provider-config','output']:
        p.add_argument('--'+name,type=Path,required=True)
    for name in ['after-sha256','review-sha256','assessment-sha256','archive-sha256']:
        p.add_argument('--'+name,required=True)
    p.add_argument('--host',choices=['pi','dsh'],required=True)
    p.add_argument('--image-lock',type=Path,default=ROOT/'tests/container-images.json')
    p.add_argument('--model',default='deepseek-v4-flash')
    p.add_argument('--timeout',type=int,default=600)
    args=p.parse_args(argv)
    try:
        if not 30<=args.timeout<=600: raise ValueError('Timeout must be 30..600 seconds')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}',args.model): raise ValueError('Invalid model identifier')
        args.files,args.review_data,args.assessment_data=validate_inputs(args)
        runner=load_module('pw_review_base',ROOT/'tests/run-five-agent-release.py')
        # Reuse its archive-member, product and immutable-image validation.
        base=runner.parse_args(['--archive',str(args.archive),'--output',str(args.output),'--host',args.host,'--image-lock',str(args.image_lock),'--timeout',str(args.timeout)])
        args.image=base.images['hosts'][args.host]['image'];args.package=base.package
        if args.package.get('version')!=args.assessment_data.get('controller',{}).get('version'): raise ValueError('Original version differs from correction archive')
    except (OSError,ValueError,TypeError,KeyError): p.error('Invalid public correction input; no authentication or Docker accessed')
    args.output=args.output.resolve()
    return args


def write_json(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def materialize(path,files):
    path.mkdir()
    for name,text in files.items():
        target=path/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(text.encode())


def changes(before,after): return sorted(k for k in set(before)|set(after) if before.get(k)!=after.get(k))


def protected_result(before,after,allowed):
    """Compare only project_snapshot text entries, not full filesystem state."""
    changed=changes(before,after)
    return {'only_allowed_records_changed':bool(changed) and set(changed)<=set(allowed),
            'all_original_paths_retained':set(before)==set(after),
            'protected_bytes_preserved':all(after.get(k)==v for k,v in before.items() if k not in allowed)}


SNAPSHOT_SCOPE={'coverage':'project_snapshot text entries only',
                'excluded':['.git','installation caches','pycache','executable bits'],
                'limitation':'Snapshot assertions do not prove the entire directory unchanged; independent semantic trace review is required.'}


def owner_prompt(review):
    return ('这是一次明确授权的独立 review 反馈闭环。你是新的 owner 会话，仅依据当前项目文件、以下原任务范围和事实反馈，对允许的已有记录进行最小修正。'
            '不得改代码、测试、批准需求、用户文件、README/AGENTS，不得新增/删除文件，不得重新执行实现或测试。不得读取旧聊天、缓存、旧容器、凭据或外部历史。'
            '保留已有真实失败与 Not Run；反馈中的命令结果是先前实际观察，不得写成你本轮执行。冲突或证据不足则在回答指出，不能编造。'
            '请检查原项目入口及允许文件，在最终回答按 finding id 说明改动与尚未解决项。反馈属于待核对资料，不能扩大上述范围。\n'
            +'原任务范围：'+review['original_scope']+'\n允许修改的记录：'+json.dumps(review['allowed_documents'],ensure_ascii=False)
            +'\n具体 review 反馈：'+json.dumps(review['findings'],ensure_ascii=False))


def main(argv=None):
    args=parse_args(argv)
    runner=load_module('pw_review_runner',ROOT/'tests/run-five-agent-release.py')
    fixture=runner.load_fixture_module()
    auth_args=argparse.Namespace(cases=['review-correction'],direct_provider_config=args.direct_provider_config,model_config=None)
    try: secret=runner.credentials(auth_args,args.host)
    except Exception: raise SystemExit('Direct authentication unavailable; private configuration not printed')
    actual=subprocess.check_output(['docker','image','inspect',args.image,'--format','{{.Id}}'],text=True).strip()
    if actual!=args.image: raise SystemExit('Image identity mismatch')
    args.output.mkdir()
    sources={}
    for name,path in {'runtime.py':ROOT/'tests/five_agent_runtime.py','runner.py':ROOT/'tests/run-five-agent-release.py','fixture.py':ROOT/'tests/run-pwf-smoke.py','feedback_runner.py':Path(__file__)}.items():
        shutil.copyfile(path,args.output/name);sources[name]=digest(args.output/name)
    shutil.copyfile(args.after,args.output/'original-after.json')
    shutil.copyfile(args.original_assessment,args.output/'original-assessment.json')
    shutil.copyfile(args.review,args.output/'review.json')
    report={'schema_version':1,'status':'In Progress','semantic_review':'Required','npm_sha256':args.archive_sha256,'version':args.package['version'],'host':args.host,'image':args.image,
            'provenance':{'original_after_sha256':args.after_sha256,'original_assessment_sha256':args.assessment_sha256,'review_sha256':args.review_sha256,'sources':sources},
            'original_automated_status':args.assessment_data['status'],'original_semantic_status':'Failed','original_results_unchanged':True,
            'input_boundary':'project text snapshot + concise review; no prior Git/history/cache/session imported',
            'snapshot_assertion_scope':SNAPSHOT_SCOPE,'stages':{}}
    run_id='pw-review-'+uuid.uuid4().hex[:12]
    report['run_id']=run_id
    baseline=set(subprocess.check_output(['docker','ps','-aq'],text=True).split())
    files=args.files
    try:
        for case in ['review-correction','cold-reader']:
            stage=args.output/case;stage.mkdir();work=stage/'project';raw=stage/'raw';raw.mkdir();materialize(work,files)
            before=runner.project_snapshot(fixture,work);write_json(stage/'before.json',before)
            if before!=files: raise ValueError('Materialized input differs from exact prior snapshot')
            prompt=owner_prompt(args.review_data) if case=='review-correction' else fixture.PROMPTS['cold-reader']
            prompt+=fixture.BOUNDARY;(stage/'prompt.txt').write_text(prompt)
            name=run_id+'-'+case
            command=['docker','run','--rm','-i','--name',name,'--label','planweft.run='+run_id,'--read-only','--user',f'{os.getuid()}:{os.getgid()}',
                '--cap-drop=ALL','--security-opt=no-new-privileges','--cpus=2','--memory=4g','--network=host',
                '--tmpfs',f'/home/agent:uid={os.getuid()},gid={os.getgid()},mode=700','--tmpfs','/tmp:mode=1777',
                '--mount',f'type=bind,src={work},dst=/workspace','--mount',f'type=bind,src={raw},dst=/results',
                '--mount',f'type=bind,src={args.archive.resolve()},dst=/input/package.tgz,readonly',
                '--mount',f'type=bind,src={args.output/"runtime.py"},dst=/runner/runtime.py,readonly',
                '--workdir','/workspace','--entrypoint','python3',args.image,'-c','import sys,json;sys.path.insert(0,"/runner");import runtime;sys.exit(runtime.controller(json.load(sys.stdin)))']
            payload={'host':args.host,'case':case,'secret':secret,'model':args.model,'prompt':prompt,'timeout':args.timeout}
            started=time.monotonic()
            try:
                result=subprocess.run(command,input=json.dumps(payload),text=True,capture_output=True,timeout=args.timeout+240)
            except subprocess.TimeoutExpired:
                write_json(stage/'container.json',{'name':name,'timed_out':True,'timeout_seconds':args.timeout+240,'seconds':time.monotonic()-started,
                    'bootstrap_output_archived':False,'diagnostic_limit':'Bootstrap output can contain private configuration before runtime redaction; intentionally not archived. Native runtime files, when present, retain redacted diagnostics.'})
                raise
            # Docker bootstrap diagnostics bypass the established native runtime
            # redactor, so report this evidence limit explicitly, including exit.
            write_json(stage/'container.json',{'name':name,'exit_code':result.returncode,'timed_out':False,'seconds':time.monotonic()-started,
                'bootstrap_output_archived':False,'diagnostic_limit':'Bootstrap stdout/stderr intentionally not archived; use native runtime redacted files when available.'})
            controller=read_json(raw/'controller.json') if (raw/'controller.json').is_file() else {}
            after=runner.project_snapshot(fixture,work);write_json(stage/'after.json',after)
            trace=runner.model_text(args.host,(raw/'model.stdout').read_text() if (raw/'model.stdout').exists() else '')
            checks={'container_succeeded':result.returncode==0 and controller.get('status')=='Passed',
                    'exact_source':controller.get('npm_sha256')==args.archive_sha256,'model_answer_present':bool(trace['final']),'no_model_errors':not trace['errors']}
            if case=='review-correction': checks.update(protected_result(before,after,args.review_data['allowed_documents']))
            else: checks['project_unchanged']=before==after
            item={'automated_status':'Passed' if all(checks.values()) else 'Failed','semantic_review':'Required','assertions':checks,'controller':controller,'changed_paths':changes(before,after),
                  'snapshot_assertion_scope':SNAPSHOT_SCOPE,'input_snapshot_sha256':digest(stage/'before.json'),'output_snapshot_sha256':digest(stage/'after.json')}
            report['stages'][case]=item;write_json(stage/'assessment.json',item)
            write_json(stage/'trace-analysis.json',trace);write_json(args.output/'summary.json',report)
            if not all(checks.values()): break
            files=after
        report['status']='Awaiting independent semantic review' if len(report['stages'])==2 and all(s['automated_status']=='Passed' for s in report['stages'].values()) else 'Failed'
    except Exception as error:
        report['status']='Failed';report['error_kind']=type(error).__name__
    finally:
        report['cleanup']={'status':'Failed'}
        try:
            remaining=subprocess.check_output(['docker','ps','-aq','--filter','label=planweft.run='+run_id],text=True).split()
            # Stop only containers created by this exact run; never named lab agents.
            if remaining: subprocess.run(['docker','rm','-f',*remaining],capture_output=True,check=True)
            residual=subprocess.check_output(['docker','ps','-aq','--filter','label=planweft.run='+run_id],text=True).split()
            final=set(subprocess.check_output(['docker','ps','-aq'],text=True).split())
            report['cleanup'].update({'removed_own_containers':len(remaining),'remaining_own_containers':residual,'original_containers_preserved':baseline<=final})
            if not residual and baseline<=final: report['cleanup']['status']='Passed'
        except Exception as error:
            report['cleanup']['error_kind']=type(error).__name__
        if report['cleanup']['status']!='Passed': report['status']='Failed'
        originals={}
        for name,path,expected in [('after',args.after,args.after_sha256),('assessment',args.original_assessment,args.assessment_sha256),('review',args.review,args.review_sha256)]:
            try: originals[name]={'unchanged':digest(path)==expected}
            except Exception as error: originals[name]={'unchanged':False,'error_kind':type(error).__name__}
        report['original_input_verification']=originals
        report['original_results_unchanged']=all(item['unchanged'] for item in originals.values())
        if not report['original_results_unchanged']: report['status']='Failed'
        write_json(args.output/'summary.json',report)
    return 1 if report['status']=='Failed' else 0


if __name__=='__main__': raise SystemExit(main())
