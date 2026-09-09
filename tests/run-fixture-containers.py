#!/usr/bin/env python3
"""Bounded A/B payload-delta fixtures; modified fixtures are not release archives.

Reuse the registry runner's input/resource/ownership rules. No credentials or
model configuration are accepted. A failed host stops the remaining sequence.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT=Path(__file__).resolve().parents[1]


def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tests'/name)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


registry=module('run-registry-containers.py')
isolation=module('run-project-isolation.py')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',choices=registry.HOSTS,action='append',required=True)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--timeout',type=int,default=600)
    given=parser.parse_args(argv)
    archive=given.archive.resolve()
    if ',' in str(archive):parser.error('Archive mount path cannot contain a comma')
    try:version=isolation.inspect_archive(archive,given.sha256)
    except (OSError,ValueError,KeyError,isolation.tarfile.TarError) as error:parser.error(str(error))
    args=registry.parse_args(['--version',version,'--sha256',given.sha256,
        '--output',str(given.output),'--timeout',str(given.timeout),
        *[x for host in given.host for x in ['--host',host]]])
    resources=registry.resource_preflight(args.output)
    for image in args.images.values():
        if registry.docker_output(['image','inspect',image,'--format','{{.Id}}'])!=image:
            raise RuntimeError('Locked image identity mismatch')
    args.output.mkdir(parents=True)
    frozen=args.output/'frozen';frozen.mkdir()
    worker=(ROOT/'tests/run-installer-lifecycle.py').read_bytes()
    (frozen/'run-installer-lifecycle.py').write_bytes(worker)
    (frozen/'run-fixture-containers.py').write_bytes(Path(__file__).read_bytes())
    (frozen/'run-registry-containers.py').write_bytes(Path(registry.__file__).read_bytes())
    (frozen/'run-project-isolation.py').write_bytes(Path(isolation.__file__).read_bytes())
    (frozen/'container-images.json').write_bytes(args.lock_bytes)
    report={'status':'In Progress','input_version':version,'input_archive_sha256':given.sha256,
        'scope':'Locally modified A/B fixtures, not exact release payload acceptance',
        'model_sessions':'Not Run','credentials_mounted':False,'resource_preflight':resources,
        'worker_sha256':hashlib.sha256(worker).hexdigest(),
        'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'hosts':{host:{'status':'Not Run'} for host in args.host}}
    registry.save(args.output/'summary.json',report)
    for host in args.host:
        try:resources=registry.resource_preflight(args.output)
        except (OSError,RuntimeError) as error:
            report['status']='Failed'
            report['hosts'][host]={'status':'Not Run','reason':type(error).__name__}
            registry.save(args.output/'summary.json',report)
            return 1
        case=args.output/host;case.mkdir()
        token=uuid.uuid4().hex;name='planweft-fixture-'+token
        result={'status':'Failed','image':args.images[host],'resource_preflight':resources}
        command=['docker','run','--name',name,'--label','planweft.registry-run='+token,
            '--read-only','--user',f'{os.getuid()}:{os.getgid()}','--cap-drop=ALL',
            '--security-opt=no-new-privileges','--cpus=2','--memory=3g','--memory-swap=3g',
            '--pids-limit=256','--network=host','--tmpfs','/tmp:mode=1777,size=512m',
            '--mount',f'type=bind,src={frozen},dst=/source/tests,readonly',
            '--mount',f'type=bind,src={archive},dst=/input/package.tgz,readonly',
            '--mount',f'type=bind,src={case},dst=/results',
            *[x for key in args.proxies for x in ['-e',key]],'--entrypoint','python3',
            args.images[host],'/source/tests/run-installer-lifecycle.py','--host',host,
            '--archive','/input/package.tgz','--output','/results/run']
        try:
            with (case/'container.stdout').open('w') as stdout,(case/'container.stderr').open('w') as stderr:
                completed=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=args.timeout)
            result['exit_code']=completed.returncode
            raw=(case/'run/summary.json').read_bytes();observed=json.loads(raw)
            result['raw_summary_sha256']=hashlib.sha256(raw).hexdigest()
            if (completed.returncode==0 and observed.get('status')=='Passed'
                    and observed.get('host')==host and observed.get('project_records_unchanged') is True
                    and observed.get('input_archive_sha256')==given.sha256
                    and set(observed.get('fixture_archives',{}))=={'A','B'}):result['status']='Passed'
        except (OSError,ValueError,subprocess.SubprocessError,KeyboardInterrupt) as error:
            result['error']=type(error).__name__
        finally:
            result['cleanup']=registry.cleanup_container(name,token)
            if result['cleanup']['status']!='Passed':result['status']='Failed'
            try:result['npm_cache']=registry.clear_success_cache(case,result['status']=='Passed',result['cleanup'])
            except OSError:
                result['npm_cache']={'status':'Failed','reason':'cleanup failed'};result['status']='Failed'
            registry.save(case/'container.json',result)
            report['hosts'][host]=result
            report['status']='Failed' if result['status']!='Passed' else 'In Progress'
            registry.save(args.output/'summary.json',report)
        if result['status']!='Passed':return 1
    report['status']='Passed';registry.save(args.output/'summary.json',report)
    return 0


if __name__=='__main__':raise SystemExit(main())
