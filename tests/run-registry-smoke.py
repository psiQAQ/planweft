#!/usr/bin/env python3
"""Verify published npm bytes, persistent CLI installs and direct Pi/OpenCode/DSH npm entries.

Uses isolated profiles without personal model credentials. Paired published versions
verify real A -> B -> A -> B -> remove; one version proves idempotence only.
Fresh model sessions and Git marketplace routes remain separate acceptance lanes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def native_version_steps(version, previous=None):
    return ([('install', previous), ('upgrade', version), ('rollback', previous),
             ('reupgrade', version)] if previous else [('install', version)])


def set_opencode_source(config, previous, version):
    """Change only the owned npm entry; an unexpected registration is a conflict."""
    data = json.loads(config.read_text())
    entries = data.get('plugin', [])
    if not isinstance(entries, list): raise RuntimeError('OpenCode plugin configuration is not a list')
    owned = [x for x in entries if isinstance(x, str) and (x == 'planweft' or x.startswith('planweft@'))]
    expected = ['planweft@' + previous] if previous else []
    if owned != expected: raise RuntimeError('OpenCode native source changed or duplicated')
    replacement = 'planweft@' + version if version else None
    if previous:
        updated = [replacement if x == expected[0] else x for x in entries]
        data['plugin'] = [x for x in updated if x is not None]
    else:
        data['plugin'] = entries + ([replacement] if replacement else [])
    config.write_text(json.dumps(data, indent=2) + '\n')


def verify_native_package(root, expected):
    """Bind native-resolved package bytes to the independently downloaded archive."""
    if not (root / 'package.json').is_file(): raise RuntimeError('Native npm package is missing')
    count = 0
    for source in expected.rglob('*'):
        if not source.is_file(): continue
        actual = root / source.relative_to(expected)
        if (not actual.is_file() or actual.read_bytes() != source.read_bytes()
                or bool(actual.stat().st_mode & 0o111) != bool(source.stat().st_mode & 0o111)):
            raise RuntimeError('Native npm package differs: ' + source.relative_to(expected).as_posix())
        count += 1
    expected_dist = {p.relative_to(expected / 'dist').as_posix()
                     for p in (expected / 'dist').rglob('*') if p.is_file()}
    actual_dist = {p.relative_to(root / 'dist').as_posix()
                   for p in (root / 'dist').rglob('*') if p.is_file()}
    if actual_dist != expected_dist:
        raise RuntimeError('Removed distribution files survived native version switch')
    return count


def verify_skill_tree(actual, expected):
    def inventory(root):
        return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in root.rglob('*') if p.is_file()}
    if not actual.is_dir() or inventory(actual) != inventory(expected):
        raise RuntimeError('Native Skill is missing, changed, or paired to another version')


def bootstrap_cli(version, archive, expected_sha256, expected_package, out, run):
    """Execute npm-installed CLI bytes, not a dependency-free tar extraction."""
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected_sha256:
        raise RuntimeError('CLI bootstrap archive digest differs')
    prefix=out/'cli-bootstrap'/version
    if prefix.exists(): raise RuntimeError('CLI bootstrap destination must be new')
    run('bootstrap-'+version, ['npm','install','--prefix',str(prefix),
        '--ignore-scripts','--omit=dev','--no-audit','--no-fund',
        '--registry=https://registry.npmjs.org',str(archive)], out)
    root=prefix/'node_modules/planweft'
    verify_native_package(root,expected_package)
    return root


def pi_commands(project, env, log):
    # RPC discovery invokes no model. EOF alone need not stop the Pi event loop.
    proc = subprocess.Popen(['pi', '--mode', 'rpc', '--no-session', '--approve'],
                            cwd=project, env=env, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    terminated = False
    try:
        stdout, stderr = proc.communicate('{"id":"pw","type":"get_commands"}\n', timeout=20)
    except subprocess.TimeoutExpired:
        terminated = True
        proc.terminate()
        try: stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill(); stdout, stderr = proc.communicate()
    finally:
        if proc.poll() is None:
            proc.kill(); proc.wait()
    log.write_text(stdout + stderr)
    if not terminated and proc.returncode != 0:
        raise RuntimeError('Pi native command discovery process failed')
    replies = [json.loads(line) for line in stdout.splitlines() if line.startswith('{')]
    matches = [x for x in replies if x.get('id') == 'pw']
    if len(matches) != 1 or not matches[0].get('success'):
        raise RuntimeError('Pi native command discovery failed')
    return matches[0].get('data', {}).get('commands', [])


def verify_pi_commands(commands, version, root):
    relevant = [c for c in commands if c.get('name', '').startswith('pw-')
                or c.get('name') == 'skill:project-docs']
    if version is None:
        if relevant: raise RuntimeError('Pi commands or Skill survived native removal')
        return
    for name, kind, suffix in [('pw-plan-status', 'extension', 'extensions/planweft/index.ts'),
                               ('skill:project-docs', 'skill', 'SKILL.md')]:
        selected = [c for c in relevant if c.get('name') == name]
        if len(selected) != 1: raise RuntimeError('Pi runtime or Skill did not load exactly once')
        item = selected[0]; info = item.get('sourceInfo', {})
        if (item.get('source') != kind or info.get('source') != 'npm:planweft@' + version
                or Path(info.get('baseDir', '')).resolve() != root.resolve()
                or Path(info.get('path', '')).resolve() != (root / 'dist/pi/planweft' / suffix).resolve()):
            raise RuntimeError('Pi runtime and Skill sources do not match the selected npm version')
    if len({c['name'] for c in relevant}) != len(relevant):
        raise RuntimeError('Pi commands loaded more than once')


def verify_opencode_discovery(agent, skills, skill=None):
    active = {k for k, enabled in agent.get('tools', {}).items() if k.startswith('pw_') and enabled}
    selected = [s for s in skills if s.get('name') == 'project-docs']
    if skill is None:
        if active or selected: raise RuntimeError('OpenCode npm tools or Skill survived native removal')
    elif (active != {'pw_init', 'pw_status', 'pw_check'} or len(selected) != 1
          or Path(selected[0].get('location', '')).resolve() != (skill / 'SKILL.md').resolve()):
        raise RuntimeError('OpenCode npm runtime or paired Skill did not load uniquely')


def verify_opencode_removed(project, *, managed=False):
    targets = [project / '.opencode/skills/project-docs']
    if managed: targets.append(project / '.opencode/plugins/planweft.ts')
    # exists() follows links: a stale link to a removed package is still an
    # installed component, even though its target no longer exists.
    if any(target.exists() or target.is_symlink() for target in targets):
        raise RuntimeError('OpenCode components survived removal')


def opencode_package_root(profile, config, version):
    """Resolve the pinned 1.18.22 layout, after actual native discovery succeeds.

    Retained versions and the former unversioned cache are not candidates. Cache
    presence is only a content check; the caller must also check native loading.
    """
    entries = json.loads(config.read_text()).get('plugin', [])
    if not isinstance(entries, list): raise RuntimeError('OpenCode plugin configuration is not a list')
    sources = [x for x in entries if isinstance(x, str) and (x == 'planweft' or x.startswith('planweft@'))]
    if sources != ['planweft@' + version]:
        raise RuntimeError('OpenCode npm source is missing, ambiguous, or selects another version')
    cache = profile / '.cache/opencode/packages' / ('planweft@' + version)
    root = cache / 'node_modules/planweft'
    if not (cache / 'package.json').is_file() or not (root / 'package.json').is_file():
        raise RuntimeError('OpenCode selected version cache is missing')
    resolved = json.loads((cache / 'package.json').read_text())
    installed = json.loads((root / 'package.json').read_text())
    if (resolved.get('dependencies', {}).get('planweft') != version
            or installed.get('name') != 'planweft' or installed.get('version') != version):
        raise RuntimeError('OpenCode selected cache does not contain the requested version')
    return root


def direct_npm_lifecycle(host, version, previous, packages, out, profile, env, run, cli_packages=None):
    """Native package manager/config operations; discovery only, never a model claim."""
    project = out / ('native-' + host); project.mkdir()
    protected = {n: (n + ' approved\r\n').encode() for n in
                 ['task_plan.md', 'findings.md', 'progress.md', 'requirements.md']}
    for name, data in protected.items(): (project / name).write_bytes(data)
    observations = []
    config = project / 'opencode.json'
    if host == 'opencode':
        # 1.18.22 adds this canonical schema during config normalization. Seed
        # it explicitly so the final full-object comparison still catches every
        # unrelated change (https://opencode.ai/docs/config/#schema).
        baseline = {'$schema': 'https://opencode.ai/config.json', 'autoupdate': False,
                    'share': 'disabled', 'permission': {'bash': 'ask'}, 'plugin': []}
        config.write_text(json.dumps(baseline) + '\n')
    current = None
    for label, selected in native_version_steps(version, previous):
        prefix = host + '-npm-' + label
        cli = (cli_packages or packages)[selected] / 'bin/planweft.mjs'
        source = ('npm:' if host == 'pi' else '') + 'planweft@' + selected
        if host == 'pi':
            run(prefix, ['pi', 'install', source, '--local', '--approve'], project)
            run(prefix + '-list', ['pi', 'list', '--approve'], project)
            settings = json.loads((project / '.pi/settings.json').read_text())
            sources = [x.get('source') if isinstance(x, dict) else x for x in settings.get('packages', [])]
            if [x for x in sources if isinstance(x, str) and x.startswith('npm:planweft')] != [source]:
                raise RuntimeError('Pi native registration differs from selected version')
            root = project / '.pi/npm/node_modules/planweft'
            verify_pi_commands(pi_commands(project, env, out / (prefix + '-rpc.log')), selected, root)
        elif host == 'opencode':
            set_opencode_source(config, current, selected)
            run(prefix + '-pair', ['node', str(cli), 'update' if current else 'add', '-a', 'opencode', '--skill-only'], project)
            agent = json.loads(run(prefix + '-load', ['opencode', 'debug', 'agent', 'build'], project))
            skills = json.loads(run(prefix + '-skills', ['opencode', 'debug', 'skill'], project))
            skill = project / '.opencode/skills/project-docs'
            verify_opencode_discovery(agent, skills, skill)
            verify_skill_tree(skill, packages[selected] / 'dist/opencode/planweft/skills/project-docs')
            # Locked OpenCode 1.18.22 uses a per-spec package directory. Bind it
            # to the unique config and the fresh discovery above, not old cache existence.
            root = opencode_package_root(profile, config, selected)
        else:
            # DSH 0.1.2-rc.1 forwards add/remove to pnpm and reconciles bundles
            # from installed declarations (CLI lib/plugin-*.js), not just names.
            run(prefix, ['dsh', 'plugin', '--profile', 'headless', 'add', source], project)
            prof = profile / '.dsh/profiles/headless'
            manifest = json.loads((prof / 'package.json').read_text())
            if manifest.get('dsh', {}).get('profile', {}).get('bundles', []).count('planweft') != 1:
                raise RuntimeError('DSH npm bundle is not uniquely registered')
            root = prof / 'node_modules/planweft'
            composed = run(prefix + '-compose', ['dsh', '--profile', 'headless', '--dump-config'], project)
            blocks = re.findall(r'^- id: planweft\s*\n(.*?)(?=^- id:|\Z)', composed, re.M | re.S)
            paths = re.findall(r'file://[^\s\'"<>]+', blocks[0]) if len(blocks) == 1 else []
            if len(paths) != 1 or Path(unquote(urlsplit(paths[0]).path)).resolve() != (root / 'dist/dsh/planweft/index.mjs').resolve():
                raise RuntimeError('DSH composed bundle does not identify selected npm package')
            run(prefix + '-boot', ['dsh', '--profile', 'headless', '--help'], project)
            # The bundle registers a filesystem provider rooted at this same package.
            # This binds Skill bytes, not model-time Skill discovery (a separate lane).
            verify_skill_tree(root / 'dist/dsh/planweft/skills', packages[selected] / 'dist/dsh/planweft/skills')
        checked = verify_native_package(root, packages[selected])
        observations.append({'step': label, 'version': selected, 'source': source,
                             'files_checked': checked, 'status': 'Passed'})
        current = selected
    prefix = host + '-npm-remove'
    if host == 'pi':
        run(prefix, ['pi', 'remove', 'npm:planweft@' + current, '--local', '--approve'], project)
        if 'planweft' in run(prefix + '-list', ['pi', 'list', '--approve'], project):
            raise RuntimeError('Pi native registration survived removal')
        verify_pi_commands(pi_commands(project, env, out / (prefix + '-rpc.log')), None, None)
    elif host == 'opencode':
        run(prefix + '-unpair', ['node', str(packages[current] / 'bin/planweft.mjs'), 'remove', '-a', 'opencode'], project)
        set_opencode_source(config, current, None)
        if json.loads(config.read_text()) != baseline: raise RuntimeError('Unrelated OpenCode configuration changed')
        agent = json.loads(run(prefix + '-load', ['opencode', 'debug', 'agent', 'build'], project))
        skills = json.loads(run(prefix + '-skills', ['opencode', 'debug', 'skill'], project))
        verify_opencode_discovery(agent, skills)
        verify_opencode_removed(project)
    else:
        run(prefix, ['dsh', 'plugin', '--profile', 'headless', 'remove', 'planweft'], project)
        manifest = json.loads((profile / '.dsh/profiles/headless/package.json').read_text())
        if ('planweft' in manifest.get('dependencies', {})
                or 'planweft' in manifest.get('dsh', {}).get('profile', {}).get('bundles', [])):
            raise RuntimeError('DSH native registration survived removal')
        composed = run(prefix + '-compose', ['dsh', '--profile', 'headless', '--dump-config'], project)
        if re.search(r'^- id: planweft\s*$', composed, re.M): raise RuntimeError('DSH bundle still composes after removal')
        run(prefix + '-boot', ['dsh', '--profile', 'headless', '--help'], project)
    if any((project / n).read_bytes() != data for n, data in protected.items()):
        raise RuntimeError('Native npm lifecycle changed project records')
    observations.append({'step': 'remove', 'status': 'Passed'})
    return {'status': 'Passed', 'scope': 'cross-version' if previous else 'single-version-install-remove',
            'model_sessions': 'Not Run', 'skill_verification': 'package-bound filesystem provider; model discovery separate' if host == 'dsh' else 'native discovery and package bytes',
            'steps': observations}

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
    temporary = out / 'tmp'; temporary.mkdir()
    env = {k:v for k,v in os.environ.items() if k.lower() in {'path','systemroot','windir','https_proxy','http_proxy','all_proxy','no_proxy'}}
    env.update(HOME=str(profile), USERPROFILE=str(profile), XDG_CONFIG_HOME=str(profile/'.config'),
               XDG_DATA_HOME=str(profile/'.local/share'), XDG_CACHE_HOME=str(profile/'.cache'),
               DSH_HOME=str(profile/'.dsh'), CODEX_HOME=str(profile/'.codex'), CLAUDE_CONFIG_DIR=str(profile/'.claude'),
               PI_CODING_AGENT_DIR=str(profile/'.pi/agent'), PLANNING_DISABLED='1',
               npm_config_userconfig=os.devnull, npm_config_cache=str(out/'npm-cache'),
               TMPDIR=str(temporary),
               npm_config_prefix=str(profile/'npm-prefix'), npm_config_registry='https://registry.npmjs.org',
               PATH=os.pathsep.join([*map(str,args.cli_dir),env['PATH']]))
    summary = {'version':args.version, 'npm_sha256':args.sha256, 'status':'In Progress', 'steps':[],
               'previous_version':args.previous_version, 'previous_npm_sha256':args.previous_sha256,
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
        packages={args.version:out/'package'}
        cli_packages={args.version:bootstrap_cli(args.version,archive,args.sha256,packages[args.version],out,run)}
        cli=cli_packages[args.version]/'bin/planweft.mjs'
        previous_cli=None
        if args.previous_version:
            old=out/'previous';old.mkdir()
            previous=json.loads(run('download-previous',['npm','pack','planweft@'+args.previous_version,'--ignore-scripts','--json'],old))[0]
            previous_archive=old/previous['filename']
            if hashlib.sha256(previous_archive.read_bytes()).hexdigest()!=args.previous_sha256: raise RuntimeError('Previous remote artifact digest differs')
            extract_package(previous_archive,old)
            packages[args.previous_version]=old/'package'
            cli_packages[args.previous_version]=bootstrap_cli(args.previous_version,previous_archive,args.previous_sha256,packages[args.previous_version],out,run)
            previous_cli=cli_packages[args.previous_version]/'bin/planweft.mjs'
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
            if host=='opencode': verify_opencode_removed(project, managed=True)
            if any((project/n).read_bytes()!=data for n,data in protected.items()): raise RuntimeError('Project records changed')
        summary['native_channels'] = {}
        for host in ['pi', 'opencode', 'dsh']:
            if host in hosts:
                summary['native_channels'][host] = {'status': 'In Progress', 'model_sessions': 'Not Run'}
                save()
                summary['native_channels'][host] = direct_npm_lifecycle(
                    host, args.version, args.previous_version, packages, out, profile, env, run, cli_packages)
                save()
        if args.previous_version: summary['remote_cross_version_lifecycle']='Passed'
        summary['status']='Passed'
    except Exception as error:
        summary['status']='Failed';summary['error']=str(error)
    save();print(json.dumps({'status':summary['status'],'output':str(out)}))
    if summary['status']!='Passed': raise SystemExit(1)

if __name__=='__main__': main()
