#!/usr/bin/env python3
"""Verify published npm bytes, persistent CLI installs and direct Pi/OpenCode npm entries.

Uses isolated profiles without personal model credentials. A single published version
can verify reinstall/update idempotence, not remote cross-version upgrade/rollback.
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

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version', required=True)
    p.add_argument('--sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--cli-dir', type=Path, action='append', default=[])
    args = p.parse_args()
    import re
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[\w.-]+)?', args.version): p.error('Invalid version')
    if not re.fullmatch('[a-f0-9]{64}', args.sha256): p.error('Invalid digest')
    out = args.output.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents: p.error('Output must be new and outside checkout')
    out.mkdir(parents=True)
    profile = out / 'profile'; profile.mkdir()
    env = {k:v for k,v in os.environ.items() if k.lower() in {'path','systemroot','windir','https_proxy','http_proxy','all_proxy','no_proxy'}}
    env.update(HOME=str(profile), USERPROFILE=str(profile), XDG_CONFIG_HOME=str(profile/'.config'),
               XDG_DATA_HOME=str(profile/'.local/share'), XDG_CACHE_HOME=str(profile/'.cache'),
               CODEX_HOME=str(profile/'.codex'), CLAUDE_CONFIG_DIR=str(profile/'.claude'),
               PI_CODING_AGENT_DIR=str(profile/'.pi/agent'), PLANNING_DISABLED='1',
               npm_config_userconfig=os.devnull, npm_config_cache=str(out/'npm-cache'),
               npm_config_prefix=str(profile/'npm-prefix'), npm_config_registry='https://registry.npmjs.org',
               PATH=os.pathsep.join([*map(str,args.cli_dir),env['PATH']]))
    summary = {'version':args.version, 'npm_sha256':args.sha256, 'status':'In Progress', 'steps':[],
               'remote_cross_version_lifecycle':'Not Run: one published candidate', 'model_sessions':'Not Run'}
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
        with tarfile.open(archive) as tar: tar.extractall(out,filter='data')
        cli=out/'package/bin/planweft.mjs'
        for host in ['codex','claude','pi','opencode']:
            project=out/('项目 '+host);project.mkdir()
            protected={name:(name+' approved\r\n').encode() for name in ['task_plan.md','findings.md','progress.md','requirements.md']}
            for name,data in protected.items(): (project/name).write_bytes(data)
            flags=['--global'] if host=='codex' else ['--approve-pi-project'] if host=='pi' else []
            def invoke(action,executable=cli):
                return run(host+'-'+action,['node',str(executable),action,'-a',host,*flags],project)
            invoke('add')
            state_dir=profile/'.local/share/planweft' if host=='codex' else project/'.planweft'
            state=json.loads((state_dir/'installations.json').read_text())
            persistent=Path(state['agents'][host]['packageRoot'])/'bin/planweft.mjs'
            # The managed runtime must survive deletion of the test's disposable npx cache.
            disposable=out/'npm-cache/_npx'
            if disposable.exists(): shutil.rmtree(disposable)
            invoke('doctor',persistent)
            invoke('update');invoke('remove')
            if any((project/n).read_bytes()!=data for n,data in protected.items()): raise RuntimeError('Project records changed')
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
        direct_oc=out/'native-opencode';direct_oc.mkdir()
        (direct_oc/'opencode.json').write_text(json.dumps({'plugin':['planweft@'+args.version]}))
        run('opencode-pair',['node',str(cli),'add','-a','opencode','--skill-only'],direct_oc)
        agent=json.loads(run('opencode-npm-load',['opencode','debug','agent','build'],direct_oc))
        if not all(agent.get('tools',{}).get(n) is True for n in ['pw_init','pw_status','pw_check']): raise RuntimeError('OpenCode root npm tools not loaded')
        run('opencode-npm-skills',['opencode','debug','skill'],direct_oc)
        run('opencode-unpair',['node',str(cli),'remove','-a','opencode'],direct_oc)
        summary['status']='Passed'
    except Exception as error:
        summary['status']='Failed';summary['error']=str(error)
    save();print(json.dumps({'status':summary['status'],'output':str(out)}))
    if summary['status']!='Passed': raise SystemExit(1)

if __name__=='__main__': main()
