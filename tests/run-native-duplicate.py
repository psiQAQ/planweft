#!/usr/bin/env python3
"""Observe cross-scope preflight after a real native user installation.

This proves prevention of a second registration, not execution-time hook dedup.
No models or credentials are used. Run through run-fixture-containers.py.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tarfile


def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',choices=['pi','opencode'],required=True)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    fixture=load('run-installer-lifecycle.py')
    package=fixture.validate_archive(args.archive)
    out=args.output.resolve()
    if out.exists():parser.error('Output must be new')
    out.mkdir(parents=True)
    home=out/'profile';home.mkdir()
    project=out/'项目 with spaces';project.mkdir()
    temporary=out/'tmp';temporary.mkdir()
    protected={name:b'approved project bytes\r\n' for name in
               ['task_plan.md','findings.md','progress.md','requirements.md']}
    for name,data in protected.items():(project/name).write_bytes(data)
    env={key:value for key,value in os.environ.items()
         if key.lower() in {'path','http_proxy','https_proxy','all_proxy','no_proxy'}}
    env.update(HOME=str(home),USERPROFILE=str(home),PI_CODING_AGENT_DIR=str(home/'.pi/agent'),
               XDG_CONFIG_HOME=str(home/'.config'),XDG_DATA_HOME=str(home/'.local/share'),
               XDG_CACHE_HOME=str(home/'.cache'),npm_config_cache=str(out/'npm-cache'),
               npm_config_userconfig='/dev/null',TMPDIR=str(temporary),PLANNING_DISABLED='1')
    report={'status':'In Progress','host':args.host,'version':package['version'],
            'input_archive_sha256':hashlib.sha256(args.archive.read_bytes()).hexdigest(),
            'scenario':'prevention_of_second_native_registration',
            'model_sessions':'Not Run','execution_time_deduplication':'Not Run',
            'steps':[]}
    def save(): (out/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    def snapshot(root):
        # Native logs/caches can change on discovery; snapshot only registration
        # files and owned component trees specified by the caller.
        if not root.exists():return {}
        result={}
        for p in ([root] if root.is_file() else sorted(root.rglob('*'))):
            key='.' if p==root else str(p.relative_to(root))
            if p.is_symlink():result[key]={'link':os.readlink(p)}
            elif p.is_file():result[key]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        return result
    def run(label,argv,required=True):
        try:
            p=subprocess.run(argv,cwd=project,env=env,input='y\ny\ny\n',text=True,
                             capture_output=True,timeout=180)
        except subprocess.TimeoutExpired as error:
            def text(v):return v.decode(errors='replace') if isinstance(v,bytes) else v or ''
            (out/(label+'.log')).write_text(text(error.stdout)+text(error.stderr));raise
        (out/(label+'.log')).write_text(p.stdout+p.stderr)
        report['steps'].append({'step':label,'argv':argv,'exit_code':p.returncode});save()
        if required and p.returncode:raise RuntimeError(label+' failed')
        return p
    save()
    try:
        source=out/'source';source.mkdir()
        with tarfile.open(args.archive) as archive:archive.extractall(source)
        cli=['node',str(source/'package/bin/planweft.mjs')]
        run('version',[args.host,'--version'])
        run('global-install',cli+['add','-a',args.host,'--global','--source',str(args.archive)])
        state=home/'.local/share/planweft/installations.json'
        rec=json.loads(state.read_text())['agents'][args.host]
        if rec['status']!='installed' or rec['version']!=package['version']:raise RuntimeError('Global receipt differs')
        def discover(label):
            if args.host=='pi':
                native=run(label,['pi','list','--approve']).stdout
                if rec['nativeSource'] not in native:raise RuntimeError('Native Pi source missing')
            else:
                native=json.loads(run(label,['opencode','debug','agent','build']).stdout)
                if not all(native.get('tools',{}).get(key) for key in ['pw_init','pw_status','pw_check']):
                    raise RuntimeError('Native OpenCode tools missing')
                skills=json.loads(run(label+'-skills',['opencode','debug','skill']).stdout)
                if len([s for s in skills if s.get('name')=='project-docs'])!=1:
                    raise RuntimeError('Native main Skill not unique')
        discover('native-before')
        roots=[state,home/'.pi/agent/settings.json'] if args.host=='pi' else [state,home/'.config/opencode']
        before={str(p):snapshot(p) for p in roots}
        project_before=snapshot(project)
        (out/'before.json').write_text(json.dumps({'registrations':before,'project':project_before},indent=2))
        # Dry-run exercises exactly the preflight used before any package-store
        # write. A failed negative control never creates a second live runtime.
        rejected=run('second-project-preflight',cli+['add','-a',args.host,'--project','--dry-run'],False)
        after={str(p):snapshot(p) for p in roots}
        (out/'after.json').write_text(json.dumps({'registrations':after,'project':snapshot(project)},indent=2))
        if rejected.returncode==0 or 'Another planning' not in rejected.stdout+rejected.stderr:
            raise RuntimeError('Second registration preflight was not rejected')
        if before!=after or project_before!=snapshot(project):raise RuntimeError('Rejected preflight changed state')
        discover('native-after')
        run('owned-doctor',cli+['doctor','-a',args.host,'--global'])
        run('owned-update-preflight',cli+['update','-a',args.host,'--global','--dry-run'])
        run('global-remove',cli+['remove','-a',args.host,'--global'])
        if json.loads(state.read_text())['agents']:raise RuntimeError('Owned installation record remains')
        report['status']='Passed'
    except (Exception,KeyboardInterrupt) as error:
        report['status']='Failed';report['error']=type(error).__name__+': '+str(error)
    finally:
        report['project_records_unchanged']=all((project/n).is_file() and not (project/n).is_symlink()
            and (project/n).read_bytes()==data for n,data in protected.items())
        if not report['project_records_unchanged']:report['status']='Failed'
        save()
    return 0 if report['status']=='Passed' else 1


if __name__=='__main__':raise SystemExit(main())
