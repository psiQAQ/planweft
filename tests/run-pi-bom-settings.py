#!/usr/bin/env python3
"""Exact-package Pi BOM/CRLF native-settings regression; no models or credentials.

Use run-fixture-containers.py --scenario pi-bom-settings for locked, bounded
containers. Run the same entry against old and repaired archives; a known old
failure remains Failed, including when cleanup succeeds.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[1]
SCENARIO='pi_bom_settings_native_compatibility'
ASSERTIONS={'exact_installed_content','native_source_unchanged','settings_bom_crlf_preserved',
            'doctor_success','update_dry_run_success','owned_duplicate_rejected',
            'foreign_registration_rejected','owned_remove_complete'}


def load_fixture():
    spec=importlib.util.spec_from_file_location('installer_fixture',Path(__file__).with_name('run-installer-lifecycle.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def digest(path):
    result=hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b''):result.update(chunk)
    return result.hexdigest()


def snapshot(root):
    if not root.exists():return {}
    result={}
    for path in ([root] if root.is_file() else sorted(root.rglob('*'))):
        name='.' if path==root else str(path.relative_to(root))
        if path.is_symlink():result[name]={'symlink':os.readlink(path)}
        elif path.is_file():result[name]={'sha256':digest(path),'mode':path.stat().st_mode&0o777}
        elif path.is_dir():result[name]={'directory':True}
    return result


def bom_crlf(data):
    # Preserve the native JSON text, changing encoding/line endings only.
    text=data.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n')
    return b'\xef\xbb\xbf'+text.replace('\n','\r\n').encode('utf-8')


def parse_args(argv):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',choices=['pi'],required=True)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    if args.output.is_symlink():parser.error('Output must not be a symlink')
    args.output=args.output.resolve();args.archive=args.archive.resolve()
    if args.output.exists() or args.output==ROOT or ROOT in args.output.parents:
        parser.error('Output must be new and outside checkout')
    if any(c in str(args.output)+str(args.archive) for c in [',','\n','\r']):
        parser.error('Unsupported mount path')
    try:
        if not re.fullmatch('[a-f0-9]{64}',args.sha256) or digest(args.archive)!=args.sha256:
            raise ValueError('Archive SHA-256 mismatch')
        args.package=load_fixture().validate_archive(args.archive)
        if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?',args.package['version']):
            raise ValueError('Invalid package version')
        with tarfile.open(args.archive) as archive:
            for name in ['package/bin/planweft.mjs','package/dist/pi/planweft/SKILL.md']:
                if not archive.getmember(name).isfile():raise ValueError('Missing package entry: '+name)
    except (OSError,ValueError,KeyError,tarfile.TarError) as error:parser.error(str(error))
    return args


def main(argv=None):
    args=parse_args(argv)  # Validate everything before directories or native calls.
    out=args.output;out.mkdir(parents=True)
    home=out/'profile';home.mkdir();project=out/'项目 with spaces';project.mkdir()
    temporary=out/'tmp';temporary.mkdir()
    protected={name:b'approved project bytes\r\n' for name in
               ['task_plan.md','findings.md','progress.md','requirements.md']}
    for name,data in protected.items():(project/name).write_bytes(data)
    env={key:value for key,value in os.environ.items()
         if key.lower() in {'path','http_proxy','https_proxy','all_proxy','no_proxy'}}
    env.update(HOME=str(home),USERPROFILE=str(home),PI_CODING_AGENT_DIR=str(home/'.pi/agent'),
               XDG_CONFIG_HOME=str(home/'.config'),XDG_DATA_HOME=str(home/'.local/share'),
               XDG_CACHE_HOME=str(home/'.cache'),npm_config_cache=str(out/'npm-cache'),
               npm_config_userconfig=os.devnull,TMPDIR=str(temporary),PLANNING_DISABLED='1')
    report={'status':'In Progress','host':'pi','version':args.package['version'],
            'input_archive_sha256':args.sha256,'scenario':SCENARIO,'model_sessions':'Not Run',
            'credentials_mounted':False,'steps':[],'assertions':{key:False for key in sorted(ASSERTIONS)}}
    def save(): (out/'summary.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    def run(label,command,required=False):
        try:
            p=subprocess.run(command,cwd=project,env=env,input='y\ny\ny\n',text=True,
                             capture_output=True,timeout=180)
        except subprocess.TimeoutExpired as error:
            def text(value):return value.decode(errors='replace') if isinstance(value,bytes) else value or ''
            (out/(label+'.log')).write_text(text(error.stdout)+text(error.stderr))
            report['steps'].append({'step':label,'argv':command,'error':'TimeoutExpired'});save();raise
        (out/(label+'.log')).write_text(p.stdout+p.stderr)
        report['steps'].append({'step':label,'argv':command,'exit_code':p.returncode});save()
        if required and p.returncode:raise RuntimeError(label+' failed')
        return p
    def check(label,command,reject=False):
        before={'project':snapshot(project),'global_settings':snapshot(home/'.pi/agent/settings.json'),
                'global_store':snapshot(home/'.local/share/planweft')}
        observed=run(label,command)
        after={'project':snapshot(project),'global_settings':snapshot(home/'.pi/agent/settings.json'),
               'global_store':snapshot(home/'.local/share/planweft')}
        (out/(label+'-state.json')).write_text(json.dumps({'before':before,'after':after},indent=2))
        accepted=(observed.returncode!=0 and 'Another planning registration' in observed.stdout+observed.stderr
                  if reject else observed.returncode==0)
        return accepted and before==after
    save();settings=project/'.pi/settings.json';original=None;cli=None;installed=False
    try:
        source=out/'source';source.mkdir()
        with tarfile.open(args.archive) as archive:archive.extractall(source)
        package=source/'package';cli=['node',str(package/'bin/planweft.mjs')]
        run('native-version',['pi','--version'],True)
        run('project-install',cli+['add','-a','pi','--project','--approve-pi-project','--source',str(args.archive)],True)
        installed=True
        state=project/'.planweft/installations.json';rec=json.loads(state.read_text())['agents']['pi']
        if rec['status']!='installed' or rec['version']!=args.package['version']:raise RuntimeError('Receipt identity differs')
        actual=Path(rec['packageRoot']);expected=(project/'.planweft/versions'/args.package['version']/'node_modules/planweft').resolve()
        if actual.resolve()!=expected:raise RuntimeError('Package root not owned by this fixture')
        expected_source=actual/'dist/pi/planweft'
        if Path(rec['nativeSource']).resolve()!=expected_source.resolve():raise RuntimeError('Native source differs')
        checked=0
        for p in package.rglob('*'):
            if not p.is_file():continue
            target=actual/p.relative_to(package)
            if not target.is_file() or digest(target)!=digest(p) or bool(target.stat().st_mode&0o111)!=bool(p.stat().st_mode&0o111):
                raise RuntimeError('Installed bytes/mode differ: '+str(p.relative_to(package)))
            checked+=1
        report['assertions']['exact_installed_content']=True
        report['installed_content']={'files_checked':checked,'native_source':rec['nativeSource']}
        original=settings.read_bytes();baseline=json.loads(original.decode('utf-8-sig'))
        entries=baseline.get('packages',[])
        if len(entries)!=1:raise RuntimeError('Expected exactly one native project package')
        native_before=run('native-list-before',['pi','list','--approve'],True)
        bom=bom_crlf(original);settings.write_bytes(bom)
        (out/'settings-native.bin').write_bytes(original);(out/'settings-bom-crlf.bin').write_bytes(bom)
        native_after=run('native-list-bom-crlf',['pi','list','--approve'])
        report['assertions']['native_source_unchanged']=(native_after.returncode==0 and
            native_before.stdout.count(rec['nativeSource'])==1 and native_after.stdout.count(rec['nativeSource'])==1)
        report['assertions']['doctor_success']=check('owned-doctor',cli+['doctor','-a','pi','--project'])
        report['assertions']['update_dry_run_success']=check('owned-update-preflight',cli+['update','-a','pi','--project','--dry-run'])
        report['assertions']['settings_bom_crlf_preserved']=settings.read_bytes()==bom
        # Controls alter only this fixture's settings; no duplicate runtime is
        # loaded. Both doctor and dry-run must reject explicitly without writes.
        def reject_control(label,file,body):
            prior=file.read_bytes() if file.exists() else None
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_bytes(bom_crlf(json.dumps(body,indent=2).encode()))
            try:
                doctor=check(label+'-doctor',cli+['doctor','-a','pi','--project'],True)
                update=check(label+'-update',cli+['update','-a','pi','--project','--dry-run'],True)
                return doctor and update
            finally:
                if prior is None:file.unlink()
                else:file.write_bytes(prior)
        report['assertions']['owned_duplicate_rejected']=reject_control('owned-duplicate',settings,{**baseline,'packages':[entries[0],entries[0]]})
        report['assertions']['foreign_registration_rejected']=reject_control('foreign-scope',home/'.pi/agent/settings.json',{'packages':[rec['nativeSource']]})
        save()
    except (Exception,KeyboardInterrupt) as error:
        report['error']=type(error).__name__+': '+str(error)
    finally:
        # Restore only the bytes created by this fixture, even on the expected
        # old-package doctor failure. Cleanup never turns a failed probe green.
        restored=True
        if original is not None:
            try:settings.write_bytes(original)
            except OSError as error:
                restored=False;report['cleanup_error']='Restore failed: '+type(error).__name__
        if installed and cli is not None and restored:
            try:
                removed=run('owned-remove',cli+['remove','-a','pi','--project','--approve-pi-project'])
                state=project/'.planweft/installations.json'
                remaining=json.loads(state.read_text())['agents'] if state.exists() else {}
                native=run('native-list-after-remove',['pi','list','--approve'])
                report['assertions']['owned_remove_complete']=(removed.returncode==0 and not remaining and
                    native.returncode==0 and rec['nativeSource'] not in native.stdout)
            except (Exception,KeyboardInterrupt) as error:report['cleanup_error']=type(error).__name__+': '+str(error)
        report['project_records_unchanged']=all((project/n).is_file() and not (project/n).is_symlink()
            and (project/n).read_bytes()==data for n,data in protected.items())
        report['status']='Passed' if (all(report['assertions'].values()) and report['project_records_unchanged']
                                     and 'error' not in report and 'cleanup_error' not in report) else 'Failed'
        save()
    return 0 if report['status']=='Passed' else 1


if __name__=='__main__':raise SystemExit(main())
