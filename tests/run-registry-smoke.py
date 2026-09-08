#!/usr/bin/env python3
"""Verify published npm bytes, persistent CLI installs and direct Pi/OpenCode npm entries.

Uses isolated profiles without personal model credentials. Paired published versions
verify real A -> B -> A -> B -> remove; one version proves idempotence only.
Fresh model sessions and Git marketplace routes remain separate acceptance lanes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[1]

def extract_package(archive, output):
    # The fixed host images include Python 3.11, before extraction filters.
    with tarfile.open(archive) as tar:
        for member in tar:
            name=Path(member.name)
            if name.is_absolute() or '..' in name.parts or not name.parts or name.parts[0]!='package' or not (member.isfile() or member.isdir()):
                raise ValueError('Unsafe package archive member')
        tar.extractall(output)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version', required=True)
    p.add_argument('--sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cli-dir', type=Path, action='append', default=[])
    p.add_argument('--with-dsh', action='store_true', help='Compatibility alias; DSH is now required by default')
    p.add_argument('--host', choices=['codex','claude','pi','opencode','dsh'], action='append')
    p.add_argument('--previous-version', help='Published version used for real upgrade and rollback')
    p.add_argument('--previous-sha256')
    args = p.parse_args()
    import re
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[\w.-]+)?', args.version): p.error('Invalid version')
    if not re.fullmatch('[a-f0-9]{64}', args.sha256): p.error('Invalid digest')
    if bool(args.previous_version) != bool(args.previous_sha256): p.error('Previous version and SHA must be paired')
    if args.previous_version and (not re.fullmatch(r'\d+\.\d+\.\d+(?:-[\w.-]+)?', args.previous_version) or not re.fullmatch('[a-f0-9]{64}', args.previous_sha256) or args.previous_version==args.version): p.error('Invalid previous version or digest')
    hosts=list(dict.fromkeys(args.host or ['codex','claude','pi','opencode','dsh']))
    out = args.output.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents: p.error('Output must be new and outside checkout')
    out.mkdir(parents=True)
    profile = out / 'profile'; profile.mkdir()
    env = {k:v for k,v in os.environ.items() if k.lower() in {'path','systemroot','windir','https_proxy','http_proxy','all_proxy','no_proxy'}}
    env.update(HOME=str(profile), USERPROFILE=str(profile), XDG_CONFIG_HOME=str(profile/'.config'),
               XDG_DATA_HOME=str(profile/'.local/share'), XDG_CACHE_HOME=str(profile/'.cache'),
               DSH_HOME=str(profile/'.dsh'), CODEX_HOME=str(profile/'.codex'), CLAUDE_CONFIG_DIR=str(profile/'.claude'),
               PI_CODING_AGENT_DIR=str(profile/'.pi/agent'), PLANNING_DISABLED='1',
               npm_config_userconfig=os.devnull, npm_config_cache=str(out/'npm-cache'),
               npm_config_prefix=str(profile/'npm-prefix'), npm_config_registry='https://registry.npmjs.org',
               PATH=os.pathsep.join([*map(str,args.cli_dir),env['PATH']]))
    summary = {'version':args.version, 'npm_sha256':args.sha256, 'status':'In Progress', 'steps':[],
               'remote_cross_version_lifecycle':'Pending' if args.previous_version else 'Not Run: one published candidate', 'model_sessions':'Not Run','runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    def save(): (out/'summary.json').write_text(json.dumps(summary,indent=2))
    def run(label,argv,cwd=out,input_data='y\ny\ny\n',timeout=240):
        r=subprocess.run(argv,cwd=cwd,env=env,input=input_data,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
        (out/(label+'.log')).write_text(r.stdout+r.stderr)
        summary['steps'].append({'step':label,'argv':argv,'exit_code':r.returncode});save()
        if r.returncode: raise RuntimeError(label+' failed')
        return r.stdout
    try:
        packed=json.loads(run('download',['npm','pack','planweft@'+args.version,'--ignore-scripts','--json']))[0]
        archive=out/packed['filename']
        if hashlib.sha256(archive.read_bytes()).hexdigest()!=args.sha256: raise RuntimeError('Remote artifact digest differs')
        run('npx-help',['npm','exec','--yes','--package=planweft@'+args.version,'--','planweft','--help'])
        extract_package(archive,out)
        cli=out/'package/bin/planweft.mjs'
        previous_cli=None
        if args.previous_version:
            old=out/'previous';old.mkdir()
            previous=json.loads(run('download-previous',['npm','pack','planweft@'+args.previous_version,'--ignore-scripts','--json'],old))[0]
            previous_archive=old/previous['filename']
            if hashlib.sha256(previous_archive.read_bytes()).hexdigest()!=args.previous_sha256: raise RuntimeError('Previous remote artifact digest differs')
            extract_package(previous_archive,old)
            previous_cli=old/'package/bin/planweft.mjs'
        packages={args.version:out/'package'}
        if previous_cli: packages[args.previous_version]=previous_cli.parent.parent
        for host in hosts:
            project=out/('项目 '+host);project.mkdir()
            protected={name:(name+' approved\r\n').encode() for name in ['task_plan.md','findings.md','progress.md','requirements.md']}
            for name,data in protected.items(): (project/name).write_bytes(data)
            flags=['--global'] if host in ['codex','dsh'] else ['--approve-pi-project'] if host=='pi' else []
            def invoke(action,executable=cli,label=None):
                return run(host+'-'+(label or action),['node',str(executable),action,'-a',host,*flags],project)
            invoke('add',previous_cli or cli)
            state_dir=profile/'.local/share/planweft' if host in ['codex','dsh'] else project/'.planweft'
            state=json.loads((state_dir/'installations.json').read_text())
            persistent=Path(state['agents'][host]['packageRoot'])/'bin/planweft.mjs'
            # The managed runtime must survive deletion of the test's disposable npx cache.
            disposable=out/'npm-cache/_npx'
            if disposable.exists(): shutil.rmtree(disposable)
            invoke('doctor',persistent)
            def verify_version(version,label):
                state=json.loads((state_dir/'installations.json').read_text())
                rec=state['agents'][host]
                root=Path(rec['packageRoot'])
                if rec['version']!=version: raise RuntimeError('Installed version differs')
                expected_package=packages[version]
                manifest=json.loads((expected_package/'dist/manifest.json').read_text())['platforms'][host]
                for source in expected_package.rglob('*'):
                    if source.is_file():
                        actual=root/source.relative_to(expected_package)
                        if not actual.is_file() or actual.read_bytes()!=source.read_bytes(): raise RuntimeError('Persistent package differs from downloaded archive')
                native=root/'dist'/host/'planweft'
                if host in ['codex','claude']:
                    suffix='.codex-plugin/plugin.json' if host=='codex' else '.claude-plugin/plugin.json'
                    candidates=[p.parent.parent for p in (profile/('.codex/plugins/cache' if host=='codex' else '.claude/plugins/cache')).rglob(suffix) if json.loads(p.read_text()).get('version')==version]
                    if len(candidates)!=1: raise RuntimeError('Native cache does not identify selected version')
                    native=candidates[0]
                for name,expected in manifest['files'].items():
                    installed=native/name
                    if not installed.is_file() or hashlib.sha256(installed.read_bytes()).hexdigest()!=expected['sha256'] or bool(installed.stat().st_mode & 0o111)!=expected['executable']:
                        raise RuntimeError('Remote installed content differs: '+name)
                for other_version,other_package in packages.items():
                    old_manifest=json.loads((other_package/'dist/manifest.json').read_text())['platforms'][host]
                    for removed in set(old_manifest['files'])-set(manifest['files']):
                        if (native/removed).exists(): raise RuntimeError('Removed platform file survived update')
                if host=='dsh':
                    prof=profile/'.dsh/profiles/headless'
                    data=json.loads((prof/'package.json').read_text())
                    if data['dsh']['profile']['bundles'].count('planweft')!=1 or (prof/'node_modules/planweft').resolve()!=root:
                        raise RuntimeError('DSH did not select downloaded version')
                    run(host+'-compose-'+label,['dsh','--profile','headless','--dump-config'],project)
                    run(host+'-boot-'+label,['dsh','--profile','headless','--help'],project)
                elif host=='pi':
                    if str(root/'dist/pi/planweft') not in run(host+'-list-'+label,['pi','list','--approve'],project):
                        raise RuntimeError('Pi did not select downloaded version')
                elif host=='opencode':
                    loaded=json.loads(run(host+'-load-'+label,['opencode','debug','agent','build'],project))
                    if not all(loaded.get('tools',{}).get(n) for n in ['pw_init','pw_status','pw_check']): raise RuntimeError('OpenCode runtime failed to load')
                summary['steps'].append({'step':host+'-verify-'+label,'version':version,'files_checked':len(manifest['files'])});save()
            verify_version(args.previous_version or args.version,'initial')
            invoke('update',cli,'upgrade');verify_version(args.version,'upgrade')
            if previous_cli:
                invoke('update',previous_cli,'rollback');verify_version(args.previous_version,'rollback')
                invoke('update',cli,'reupgrade');verify_version(args.version,'reupgrade')
            invoke('remove')
            if host in json.loads((state_dir/'installations.json').read_text()).get('agents',{}): raise RuntimeError('Installer registration survived removal')
            if host in ['codex','claude'] and 'planweft' in run(host+'-removed',[host,'plugin','list','--json'],project): raise RuntimeError('Native registration survived removal')
            if host=='pi' and 'planweft' in run(host+'-removed',['pi','list','--approve'],project): raise RuntimeError('Pi registration survived removal')
            if host=='dsh' and 'planweft' in json.loads((profile/'.dsh/profiles/headless/package.json').read_text()).get('dsh',{}).get('profile',{}).get('bundles',[]): raise RuntimeError('DSH registration survived removal')
            if host=='opencode' and ((project/'.opencode/plugins/planweft.ts').exists() or (project/'.opencode/skills/project-docs').exists()): raise RuntimeError('OpenCode components survived removal')
            if any((project/n).read_bytes()!=data for n,data in protected.items()): raise RuntimeError('Project records changed')
        if 'pi' in hosts:
            direct_pi=out/'native-pi';direct_pi.mkdir()
            run('pi-npm-install',['pi','install','npm:planweft@'+args.version,'--local','--approve'],direct_pi)
            run('pi-npm-list',['pi','list','--approve'],direct_pi)
            proc=subprocess.Popen(['pi','--mode','rpc','--no-session','--approve'],cwd=direct_pi,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try: stdout,stderr=proc.communicate('{"id":"pw","type":"get_commands"}\n',timeout=20)
            except subprocess.TimeoutExpired:
                proc.terminate()
                try: stdout,stderr=proc.communicate(timeout=5)
                except subprocess.TimeoutExpired: proc.kill();stdout,stderr=proc.communicate()
            (out/'pi-npm-rpc.log').write_text(stdout+stderr)
            replies=[json.loads(line) for line in stdout.splitlines() if line.startswith('{')]
            reply=next((r for r in replies if r.get('id')=='pw'),{})
            commands=reply.get('data',{}).get('commands',[])
            if not reply.get('success') or sum(c.get('name')=='pw-plan-status' for c in commands)!=1: raise RuntimeError('Pi root npm Extension did not load once')
            summary['steps'].append({'step':'pi-root-npm-load','status':'Passed'});save()
            run('pi-npm-remove',['pi','remove','npm:planweft@'+args.version,'--local','--approve'],direct_pi)
        if 'opencode' in hosts:
            direct_oc=out/'native-opencode';direct_oc.mkdir()
            (direct_oc/'opencode.json').write_text(json.dumps({'plugin':['planweft@'+args.version]}))
            run('opencode-pair',['node',str(cli),'add','-a','opencode','--skill-only'],direct_oc)
            agent=json.loads(run('opencode-npm-load',['opencode','debug','agent','build'],direct_oc))
            if not all(agent.get('tools',{}).get(n) is True for n in ['pw_init','pw_status','pw_check']): raise RuntimeError('OpenCode root npm tools not loaded')
            run('opencode-npm-skills',['opencode','debug','skill'],direct_oc)
            run('opencode-unpair',['node',str(cli),'remove','-a','opencode'],direct_oc)
        if 'dsh' in hosts:
            run('dsh-npm-install',['dsh','plugin','--profile','headless','add','planweft@'+args.version])
            composed=run('dsh-npm-compose',['dsh','--profile','headless','--dump-config'])
            if 'planweft/dsh' not in composed and '/dist/dsh/planweft/index.mjs' not in composed: raise RuntimeError('DSH npm bundle did not compose')
            run('dsh-npm-boot',['dsh','--profile','headless','--help'])
            run('dsh-npm-remove',['dsh','plugin','--profile','headless','remove','planweft'])
        if args.previous_version: summary['remote_cross_version_lifecycle']='Passed'
        summary['status']='Passed'
    except Exception as error:
        summary['status']='Failed';summary['error']=str(error)
    save();print(json.dumps({'status':summary['status'],'output':str(out)}))
    if summary['status']!='Passed': raise SystemExit(1)

if __name__=='__main__': main()
