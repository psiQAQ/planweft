#!/usr/bin/env python3
"""Reassess retained raw stopping evidence; never rewrites or reruns a model trial."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if not (args.run/'summary.json').is_file() or args.output.exists() or not args.output.parent.is_dir():
        parser.error('Require an existing run and a new output in an existing directory')
    spec=importlib.util.spec_from_file_location('pw_stop_runner',ROOT/'tests/run-five-agent-release.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    inputs={}
    def read(path,decode=True):
        raw=path.read_bytes();inputs[str(path.relative_to(args.run))]=hashlib.sha256(raw).hexdigest()
        return json.loads(raw) if decode else raw.decode()
    report=read(args.run/'summary.json')
    result={'kind':'Explicit post-hoc reassessment; no model rerun; original files unchanged',
        'version':report['version'],'npm_sha256':report['npm_sha256'],
        'analysis_source_sha256':hashlib.sha256((ROOT/'tests/run-five-agent-release.py').read_bytes()).hexdigest(),
        'original_runner_sha256':report['runner_sha256'],'hosts':{},'inputs_sha256':inputs}
    for host,original in report['hosts'].items():
        if host not in runner.HOSTS: parser.error('Unknown host')
        cases={};result['hosts'][host]=cases
        # Controls must be evaluated before their enabled counterparts.
        ordered=sorted(original,key=lambda c:(0 if c.endswith('-disabled') else 1,c))
        for case in ordered:
            if case not in runner.STOP_CASES: continue
            base=args.run/host/case
            before=read(base/'before.json');after=read(base/'after.json')
            old=read(base/'assessment.json');controller=read(base/'raw/controller.json')
            trace=runner.model_text(host,read(base/'raw'/('native-events.jsonl' if host=='dsh' else 'model.stdout'),False))
            rpc=read(base/'raw/model.json') if host=='pi' else {}
            observed=base/'raw/native-gate-reads.json'
            if observed.is_file():
                access=read(observed);files={e['file'] for e in access['events']}
                controller={**controller,'any_gate_counter_access':bool(files) or access['overflow'],
                            'gate_counters_read':not access['overflow'] and files=={'.stop_blocks','.gate_last_ledger'}}
            assertions={'original_container_succeeded':old['assertions'].get('container_succeeded') is True,
                        'model_succeeded':controller.get('model_session')=='Passed' and not trace['errors'],
                        'artifact_bound':controller.get('version')==report['version'] and controller.get('npm_sha256')==report['npm_sha256']}
            assertions.update(runner.stop_assertions(case,host,before,after,trace,controller,rpc,cases))
            cases[case]={'status':'Passed' if all(assertions.values()) else 'Failed','original_status':old['status'],
                'assertions':assertions,'controller':controller,'assistant_responses':trace['assistant_responses'],
                'native_stop_decisions':trace['native_stop_decisions']}
    result['status']='Passed' if result['hosts'] and all(cases and all(c['status']=='Passed' for c in cases.values()) for cases in result['hosts'].values()) else 'Failed'
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'kind':result['kind'],'output':str(args.output)}))
    return 0 if result['status']=='Passed' else 1

if __name__=='__main__':raise SystemExit(main())
