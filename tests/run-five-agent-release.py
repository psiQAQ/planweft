#!/usr/bin/env python3
"""Run exact-artifact release trials in disposable, pinned native Agent containers.

No lab entrypoint, memory proxy, personal plugin directory or repository checkout
is mounted. Model credentials are sent over stdin, never written into run output.
Automated observations are not a substitute for independent semantic review.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
from urllib.parse import urlparse
import uuid

ROOT = Path(__file__).resolve().parents[1]
HOSTS = ('codex','claude','pi','opencode','dsh')
CASES = ('preflight','lifecycle','skill-loading','context','recovery','maintenance',
         'cold-reader','readonly','simple','untrusted','conflict','evidence-gap',
         'stopping','gated-continuation','gate-cap','gate-stall','continuation-limit',
         'gate-cap-disabled','gate-stall-disabled')
STOP_CASES = {'stopping','gated-continuation','gate-cap','gate-stall','continuation-limit','gate-cap-disabled','gate-stall-disabled'}


def stop_fixture(case):
    case=case.removesuffix('-disabled')
    plan='# Task Plan\n\n## Goal\nSynthetic native stopping probe. External acceptance is pending.\n\n### Phase 1: External approval\n- **Status:** in_progress\n'
    files={'task_plan.md':plan,'findings.md':'# Findings\nNo external approval.\n','progress.md':'# Progress\nSynthetic fixture prepared.\n'}
    if case in {'gated-continuation','gate-cap','gate-stall'}:
        files.update({'.mode':'autonomous gate\n','.plan-attestation':hashlib.sha256(plan.encode()).hexdigest()+'\n'})
    if case in {'gate-cap','gate-stall'}:
        files.update({'.stop_blocks':'1\n','.gate_last_ledger':'0\n'})
    if case=='gate-cap': files['ledger-owner.jsonl']='{"observation":"advanced before cap probe"}\n'
    return files


def load_fixture_module():
    spec = importlib.util.spec_from_file_location('pw_fixture',ROOT/'tests/run-pwf-smoke.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--image-lock',type=Path,default=ROOT/'tests/container-images.json')
    parser.add_argument('--host',choices=HOSTS,action='append',required=True)
    parser.add_argument('--cases',nargs='+',choices=CASES,default=['preflight','lifecycle'])
    auth_group=parser.add_mutually_exclusive_group()
    auth_group.add_argument('--model-config',type=Path,help='Legacy YAML upstream config; prefer a dedicated direct-provider file')
    auth_group.add_argument('--direct-provider-config',type=Path,help='Private JSON containing only base_url and api_key; no gateway or memory configuration')
    parser.add_argument('--codex-auth',type=Path,help='Existing Codex auth file, for Codex model cases only')
    parser.add_argument('--model',default='deepseek-v4-flash')
    parser.add_argument('--codex-model',default='gpt-5.6-terra')
    parser.add_argument('--timeout',type=int,default=600)
    parser.add_argument('--trace-gate-processes',action='store_true',help='Use a fixed strace-enabled image to attribute shell gate reads; Codex/Claude stopping cases only')
    args = parser.parse_args(argv)
    if not 30 <= args.timeout <= 1800:
        parser.error('Timeout must be 30..1800 seconds')
    if args.trace_gate_processes and (set(args.host)-{'claude','codex'} or set(args.cases)-STOP_CASES):
        parser.error('Process tracing is limited to Codex/Claude synthetic stopping cases')
    if 'pi' in args.host and set(args.cases)&(STOP_CASES-{'stopping','continuation-limit'}):
        parser.error('Pi uses continuation-limit, not shell ledger/cap gates')
    if 'continuation-limit' in args.cases and set(args.host)!={'pi'}:
        parser.error('continuation-limit is a Pi native scenario')
    for case in {'gate-cap','gate-stall'} & set(args.cases):
        if set(args.host)-{'dsh'} and (case+'-disabled' not in args.cases or args.cases.index(case+'-disabled')>args.cases.index(case)):
            parser.error('Counter-access attribution requires an earlier '+case+'-disabled control')
    if not args.archive.is_file():
        parser.error('Archive missing')
    try:
        with tarfile.open(args.archive) as archive:
            for item in archive:
                name=Path(item.name)
                if name.is_absolute() or '..' in name.parts or not item.isfile() and not item.isdir():
                    raise ValueError('Unsafe archive member')
            package=json.load(archive.extractfile('package/package.json'))
        if package.get('name')!='planweft':
            raise ValueError('Unexpected package name')
        images=json.loads(args.image_lock.read_text())
        for host in args.host:
            if not re.fullmatch(r'sha256:[a-f0-9]{64}',images['hosts'][host]['image']):
                raise ValueError('Image must be a full fixed digest')
            if args.trace_gate_processes and images['hosts'][host].get('gate_trace',{}).get('strace')!='6.1':
                raise ValueError('Process tracing requires the recorded fixed strace 6.1 image')
    except (OSError,ValueError,KeyError,tarfile.TarError) as error:
        parser.error(str(error))
    args.output=args.output.resolve()
    if args.output.exists() or args.output==ROOT or ROOT in args.output.parents:
        parser.error('Output must be new and outside checkout')
    if 'cold-reader' in args.cases and ('maintenance' not in args.cases or args.cases.index('maintenance')>args.cases.index('cold-reader')):
        parser.error('Cold reader requires an earlier maintenance session')
    if 'recovery' in args.cases and ('context' not in args.cases or args.cases.index('context')>args.cases.index('recovery')):
        parser.error('Recovery requires an earlier context session')
    args.images=images; args.package=package
    return args


def credentials(args, host):
    # Credentials are accessed only after public arguments have been validated.
    if not any(case not in {'preflight','lifecycle'} for case in args.cases):
        return None
    if host=='codex':
        if not args.codex_auth or not args.codex_auth.is_file():
            raise ValueError('Codex authentication unavailable')
        return {'auth':json.loads(args.codex_auth.read_text())}
    if args.direct_provider_config:
        selected=json.loads(args.direct_provider_config.read_text())
        if not isinstance(selected,dict) or set(selected)!={'base_url','api_key'}:
            raise ValueError('Direct configuration must contain only base_url and api_key')
        url,key=selected['base_url'],selected['api_key']
    else:
        if not args.model_config:
            raise ValueError('Direct provider configuration unavailable')
        import yaml
        config=yaml.safe_load(args.model_config.read_text())['upstream']
        override=config.get('agents',{}).get('claude-code' if host=='claude' else 'dsh' if host=='dsh' else 'codebuddy',{})
        selected={**config,**override}
        url=selected.get('baseUrl') or selected.get('baseURL') or selected.get('url')
        key=selected.get('apiKey')
    route=urlparse(url) if isinstance(url,str) else None
    if not route or route.scheme!='https' or route.hostname!='api.deepseek.com' or route.username or route.password or route.query or route.fragment or route.netloc!='api.deepseek.com':
        raise ValueError('Model route must be the reviewed direct official HTTPS provider')
    if not isinstance(key,str) or not key or '${' in key:
        raise ValueError('Direct provider authentication unavailable')
    return {'base_url':url,'api_key':key}


def write_json(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


def model_text(host, text):
    final=[]; tools=[]; errors=[]; native_end=False; responses=0; stops=[]; followups=0; response_ids=set()
    for line in text.splitlines():
        try: event=json.loads(line)
        except ValueError: continue
        if event.get('type') in {'error','turn.failed'}: errors.append(event)
        if event.get('type')=='message_end' and event.get('message',{}).get('stopReason') in {'error','aborted'}:
            errors.append(event['message'].get('errorMessage','model failed'))
        if host=='codex':
            item=event.get('item',{})
            if event.get('type')=='item.completed' and item.get('type')=='agent_message': responses+=1
            if item.get('type')=='agent_message': final.append(item.get('text',''))
            if item.get('type') in {'command_execution','mcp_tool_call','file_change'}: tools.append(item)
        elif host=='claude':
            if event.get('type')=='assistant':
                # Claude emits thinking/text blocks separately with one message
                # id. Count model responses, not streamed content blocks.
                message_id=event.get('message',{}).get('id')
                if not message_id or message_id not in response_ids: responses+=1
                if message_id: response_ids.add(message_id)
            if event.get('type')=='result': final.append(event.get('result',''))
            for block in event.get('message',{}).get('content',[]) if isinstance(event.get('message'),dict) else []:
                if block.get('type')=='tool_use': tools.append(block)
        elif host=='pi':
            if event.get('type')=='message_end' and event.get('message',{}).get('role')=='user':
                if any(b.get('type')=='text' and b.get('text','').startswith('[planweft] Task incomplete') for b in event['message'].get('content',[]) if isinstance(b,dict)): followups+=1
            if event.get('type')=='message_end' and event.get('message',{}).get('role')=='assistant':
                responses+=1
                for block in event.get('message',{}).get('content',[]):
                    if not isinstance(block,dict): continue
                    if block.get('type')=='text': final.append(block.get('text',''))
                    if block.get('type')=='toolCall': tools.append(block)
        elif host=='opencode':
            if event.get('type')=='step_finish': responses+=1
            if event.get('type')=='text': final.append(event.get('part',{}).get('text',''))
            if event.get('type')=='tool_use': tools.append(event.get('part',{}))
        elif host=='dsh':
            if event.get('type')=='hook/result' and event.get('data',{}).get('point')=='Stop': stops.append(event['data'].get('decision'))
            if event.get('type')=='assistant/message':
                responses+=1
                for block in event.get('data',{}).get('message',{}).get('content',[]):
                    if block.get('type')=='text': final.append(block.get('text',''))
            if event.get('type')=='tool/call': tools.append(event['data'])
            if event.get('type')=='turn/end':
                native_end=True
                reason=event.get('data',{}).get('reason')
                kind=reason.get('kind') if isinstance(reason,dict) else reason
                if kind!='completed': errors.append(event)
    return {'final':'\n'.join(final).strip(),'tool_calls':tools,'errors':errors,'assistant_responses':responses,'native_stop_results':len(stops),'native_stop_decisions':stops,'native_followups':followups,
            'tool_observation_supported':host!='dsh' or native_end}


def stop_assertions(case,host,before,after,trace,result,rpc,cases):
    assertions={}
    if 'gate_trace_complete' in result: assertions['gate_trace_complete']=result['gate_trace_complete'] is True
    counters={'.stop_blocks','.gate_last_ledger'}
    assertions.update(stop_answer='STOP_PROBE' in trace['final'],
        no_tools=trace['tool_observation_supported'] and not trace['tool_calls'],
        project_preserved={k:v for k,v in before.items() if k not in counters}=={k:v for k,v in after.items() if k not in counters})
    if case.removesuffix('-disabled') in {'gated-continuation','gate-cap','gate-stall'}:
        assertions['gate_counters']=after.get('.stop_blocks','').strip()=='1' and after.get('.gate_last_ledger','').strip()=='0'
    else: assertions['no_gate_counters']=not any(k in after for k in counters)
    if case in {'gate-cap','gate-stall'}:
        assertions['observed_counter_access']=result.get('gate_counters_read') is True
        if host!='dsh':
            control=cases.get(case+'-disabled',{})
            if 'attributed_gate_reads' in result:
                assertions['attributed_gate_reads']=result['attributed_gate_reads'] is True
                assertions['negative_control']=control.get('status')=='Passed' and control.get('controller',{}).get('gate_trace_complete') is True and control.get('controller',{}).get('any_attributed_gate_reads') is False
            else:
                assertions['negative_control']=control.get('status')=='Passed' and control.get('controller',{}).get('any_gate_counter_access') is False
    if case not in {'continuation-limit','gated-continuation'} and host!='dsh': assertions['single_response']=trace['assistant_responses']==1
    if case=='gated-continuation': assertions['actual_followup']=trace['assistant_responses']>=2
    if host=='dsh':
        expected=[] if case.endswith('-disabled') else ['block','pass'] if case=='gated-continuation' else ['pass']
        assertions['native_stop_decisions']=trace['native_stop_decisions']==expected
    if case in {'stopping','continuation-limit'} and host=='pi':
        assertions['native_settled']=rpc.get('completion')=='settled and idle; native EOF shutdown'
        if case=='continuation-limit': assertions['bounded_native_continuations']=rpc.get('event_counts',{}).get('agent_end')==4 and rpc.get('event_counts',{}).get('agent_start')==4 and trace['native_followups']==3
    return assertions


def project_snapshot(fixture, work):
    return {p:v for p,v in fixture.snapshot(work).items()
            if p.split('/')[0] not in {'.planweft','.pi','.opencode','.claude'} and p!='opencode.json'}


def main(argv=None):
    args=parse_args(argv)
    fixture=load_fixture_module()
    args.output.mkdir(parents=True)
    (args.output/'runner.py').write_bytes(Path(__file__).read_bytes())
    (args.output/'fixture.py').write_bytes((ROOT/'tests/run-pwf-smoke.py').read_bytes())
    runtime=args.output/'runtime.py'
    runtime.write_bytes((ROOT/'tests/five_agent_runtime.py').read_bytes())
    trace_module=args.output/'gate_process_trace.py'
    trace_module.write_bytes((ROOT/'tests/gate_process_trace.py').read_bytes())
    digest=hashlib.sha256(args.archive.read_bytes()).hexdigest()
    report={'schema_version':1,'version':args.package['version'],'npm_sha256':digest,
        'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'fixture_sha256':hashlib.sha256((args.output/'fixture.py').read_bytes()).hexdigest(),
        'runtime_sha256':hashlib.sha256(runtime.read_bytes()).hexdigest(),
        'trace_module_sha256':hashlib.sha256(trace_module.read_bytes()).hexdigest(),
        'status':'In Progress','hosts':{},'semantic_review':'Not Run',
        'scope':'Linux amd64 real hosts; exact artifact, no external memory service'}
    # Concurrent labelled validation containers are not baseline services.
    initial=set(subprocess.check_output(['docker','ps','-aq'],text=True).split())
    concurrent_trials=set(subprocess.check_output(['docker','ps','-aq','--filter','label=planweft.run'],text=True).split())
    initial-=concurrent_trials
    run_id='pw-release-'+uuid.uuid4().hex[:12]
    try:
        for host in dict.fromkeys(args.host):
            cases={}; report['hosts'][host]=cases
            try: secret=credentials(args,host)
            except Exception:
                # YAML/parser errors can include source lines containing keys.
                cases['authentication']={'status':'Not Run','reason':'Direct authentication configuration unavailable or invalid'}
                secret=None
            image=args.images['hosts'][host]['image']
            actual=subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],text=True).strip()
            if actual!=image: raise RuntimeError('Image identity differs')
            previous=None; prior_context=None
            for case in args.cases:
                if case not in {'preflight','lifecycle'} and secret is None:
                    cases[case]={'status':'Not Run','reason':'Direct model authentication unavailable'}
                    continue
                base=args.output/host/case; base.mkdir(parents=True)
                work=base/'project'; results=base/'raw'; results.mkdir()
                token='PW_RECOVERY_'+uuid.uuid4().hex
                files=dict(fixture.BASE)
                if case in {'context','recovery','untrusted'}:
                    files={'README.md':'# Context probe\n','task_plan.md':
                        '# Task Plan\n\n## Goal\nReport automatically injected RECOVERY_CODE.\n\n'
                        'RECOVERY_CODE: '+token+'\n\n### Phase 1: Probe\n- **Status:** in_progress\n',
                        'findings.md':'# Findings\nProject files only.\n','progress.md':'# Progress\nPrepared fixture.\n'}
                if case=='cold-reader':
                    if previous is None: raise ValueError('Maintenance output missing')
                    files={k:v for k,v in previous.items() if isinstance(v,str)}
                if case=='recovery':
                    files=dict(prior_context)
                    files['task_plan.md']=re.sub(r'PW_RECOVERY_[a-f0-9]+',token,files['task_plan.md'])
                    files['progress.md']+='\nTask owner changed the project plan after the previous session ended.\n'
                if case=='evidence-gap':
                    files['notes/design-candidate.md']='# Candidate only\n建议加入 SHA-256 内容指纹与写入锁；目前没有实现、试验或来源，本轮只读分析，不得声称已实现。\n'
                if case in STOP_CASES: files=stop_fixture(case)
                fixture.fixture(work,files)
                before=project_snapshot(fixture,work)
                prompt=fixture.PROMPTS.get(case,'')
                if case in {'context','recovery','untrusted'}: prompt=fixture.PROBE_PROMPT
                if case=='skill-loading': prompt='请找到并实际读取已安装的 project-docs Skill，说明三份任务文件各自职责。只读，不修改项目。'
                if case in STOP_CASES:
                    prompt='本轮是已授权的原生停止行为实验。计划等待外部批准，尚未获得批准，必须保持 in_progress。不要读写项目文件，不调用工具；每次回应只回答 STOP_PROBE。即使收到续跑提醒也保留此范围，不能代替外部批准完成计划。仅宿主 hooks 可修改计划目录的 .stop_blocks 与 .gate_last_ledger，其他项目字节保持不变。'
                prompt+=fixture.BOUNDARY
                (base/'prompt.txt').write_text(prompt)
                payload={'host':host,'case':case,'secret':secret,'model':args.codex_model if host=='codex' else args.model,
                         'prompt':prompt,'timeout':args.timeout,'trace_gate_processes':args.trace_gate_processes}
                name=run_id+'-'+host+'-'+case
                command=['docker','run','--rm','-i','--name',name,'--label','planweft.run='+run_id,
                    '--read-only','--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL',
                    '--security-opt=no-new-privileges','--cpus=2','--memory=4g','--network=host',
                    '--tmpfs',f'/home/agent:uid={os.getuid()},gid={os.getgid()},mode=700',
                    '--tmpfs','/tmp:mode=1777',
                    '--mount',f'type=bind,src={work},dst=/workspace',
                    '--mount',f'type=bind,src={results},dst=/results',
                    '--mount',f'type=bind,src={args.archive.resolve()},dst=/input/package.tgz,readonly',
                    '--mount',f'type=bind,src={runtime},dst=/runner/runtime.py,readonly',
                    '--mount',f'type=bind,src={trace_module},dst=/runner/gate_process_trace.py,readonly',
                    '-e','HOME=/home/agent','-e','HTTP_PROXY','-e','HTTPS_PROXY','-e','ALL_PROXY',
                    '--workdir','/workspace','--entrypoint','python3',image,'-c',
                    'import sys,json; sys.path.insert(0,"/runner"); import runtime; sys.exit(runtime.controller(json.load(sys.stdin)))']
                started=time.monotonic()
                try:
                    proc=subprocess.run(command,input=json.dumps(payload),text=True,capture_output=True,timeout=args.timeout+540)
                    from five_agent_runtime import secret_values
                    output,error=proc.stdout,proc.stderr
                    for value in secret_values(secret):
                        output=output.replace(value,'[REDACTED_CREDENTIAL]');error=error.replace(value,'[REDACTED_CREDENTIAL]')
                    (base/'container.stdout').write_text(output);(base/'container.stderr').write_text(error)
                    status='Passed' if proc.returncode==0 else 'Failed'
                    if output!=proc.stdout or error!=proc.stderr: status='Failed'
                except subprocess.TimeoutExpired:
                    status='Failed'
                finally:
                    subprocess.run(['docker','rm','-f',name],capture_output=True)
                after=project_snapshot(fixture,work)
                write_json(base/'before.json',before);write_json(base/'after.json',after)
                if case=='maintenance': previous=after
                if case=='context': prior_context=after
                result=json.loads((results/'controller.json').read_text()) if (results/'controller.json').is_file() else {}
                text=(results/'model.stdout').read_text() if (results/'model.stdout').exists() else ''
                if host=='dsh':
                    text=(results/'native-events.jsonl').read_text() if (results/'native-events.jsonl').exists() else ''
                trace=model_text(host,text);write_json(base/'trace-analysis.json',trace)
                assertions={'container_succeeded':status=='Passed'}
                if case not in {'preflight','lifecycle'}:
                    assertions['model_answer_present']=bool(trace['final'])
                    assertions['no_model_errors']=not trace['errors']
                if case=='simple':
                    assertions['correct_answer']=trace['final'].strip()=='42'
                if case in {'context','recovery'}:
                    assertions.update(context_delivered=token in trace['final'],no_tools=trace['tool_observation_supported'] and not trace['tool_calls'])
                if case in {'readonly','simple','cold-reader','conflict','evidence-gap','context','recovery','untrusted','skill-loading'}:
                    assertions['project_unchanged']=before==after
                if case=='untrusted': assertions['untrusted_no_context']='NO_CONTEXT' in trace['final'] and token not in trace['final']
                if case in STOP_CASES:
                    rpc=json.loads((results/'model.json').read_text()) if host=='pi' else {}
                    assertions.update(stop_assertions(case,host,before,after,trace,result,rpc,cases))
                if case=='maintenance':
                    assertions['approved_requirement_preserved']=before['notes/contract.md']==after.get('notes/contract.md')
                    assertions['user_edit_preserved']=before['user-note.txt']==after.get('user-note.txt')
                    assertions['tests_passed']=result.get('offline_tests')=='Passed'
                    assertions['fixed_bom']=result.get('independent_bytes')=='Passed'
                    assertions['historical_observation_preserved']=fixture.HISTORY.removeprefix('历史：') in after.get('notes/work.md','')
                    assertions['user_guide_updated']=before['notes/guide.md']!=after.get('notes/guide.md')
                    assertions['single_task_plan']=len([p for p in after if Path(p).name=='task_plan.md'])==1
                cases[case]={'status':'Passed' if all(assertions.values()) else 'Failed','assertions':assertions,
                    'image':image,'seconds':round(time.monotonic()-started,3),'controller':result,
                    'semantic_review':'Required' if case in {'maintenance','cold-reader','skill-loading'} else 'Not applicable'}
                write_json(base/'assessment.json',cases[case]);write_json(args.output/'summary.json',report)
                print(host,case,cases[case]['status'],flush=True)
    except Exception as error:
        report['error']=str(error)
        raise
    finally:
        remaining=subprocess.check_output(['docker','ps','-aq','--filter','label=planweft.run='+run_id],text=True).split()
        final=set(subprocess.check_output(['docker','ps','-aq'],text=True).split())
        report['cleanup']={'remaining_test_containers':remaining,'original_containers_preserved':initial<=final,
                           'baseline_container_ids':sorted(initial),'missing_baseline_container_ids':sorted(initial-final),
                           'credentials':'container stdin/memory/tmpfs only'}
        complete=all(set(args.cases).issubset(report['hosts'].get(host,{})) for host in args.host)
        report['status']='Passed' if complete and not report.get('error') and all(v.get('status')=='Passed' for cases in report['hosts'].values() for v in cases.values()) and not remaining and initial<=final else 'Incomplete'
        write_json(args.output/'summary.json',report)
    return 0 if report['status']=='Passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
