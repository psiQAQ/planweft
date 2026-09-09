"""Offline runner protocol tests; fake native subprocesses are not Pi evidence."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('pi_bom_runner',Path(__file__).with_name('run-pi-bom-settings.py'))
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


def archive(root):
    target=root/'package.tgz'
    files={'package/package.json':b'{"name":"planweft","version":"0.4.0-rc.11"}',
           'package/bin/planweft.mjs':b'// offline fixture only\n',
           'package/dist/pi/planweft/SKILL.md':b'# fixture\n'}
    with tarfile.open(target,'w:gz') as tar:
        for name,data in files.items():
            item=tarfile.TarInfo(name);item.size=len(data);item.mode=0o755 if name.endswith('.mjs') else 0o644
            tar.addfile(item,io.BytesIO(data))
    return ['--host','pi','--archive',str(target),'--sha256',runner.digest(target),'--output',str(root/'run')]


class PiBomRunnerTest(unittest.TestCase):
    def test_argument_rejection_precedes_directory_or_native_effects(self):
        for case in ['sha','host','existing','symlink','unsafe_archive','version','unknown']:
            with self.subTest(case=case),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);args=archive(root);out=root/'run'
                if case=='sha':args+=['--sha256','0'*64]
                if case=='host':args+=['--host','claude']
                if case=='existing':out.mkdir()
                if case=='symlink':out.symlink_to(root/'missing',target_is_directory=True)
                if case=='unknown':args+=['--token','unacceptable']
                if case=='unsafe_archive':
                    target=root/'unsafe.tgz'
                    with tarfile.open(target,'w:gz') as tar:
                        item=tarfile.TarInfo('package/../escape');item.size=1;tar.addfile(item,io.BytesIO(b'x'))
                    args+=['--archive',str(target),'--sha256',runner.digest(target)]
                if case=='version':
                    target=root/'bad-version.tgz'
                    with tarfile.open(target,'w:gz') as tar:
                        data=b'{"name":"planweft","version":"../../escape"}'
                        item=tarfile.TarInfo('package/package.json');item.size=len(data);tar.addfile(item,io.BytesIO(data))
                    args+=['--archive',str(target),'--sha256',runner.digest(target)]
                with patch.object(runner.subprocess,'run') as native,contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):
                    runner.main(args)
                native.assert_not_called()
                self.assertFalse((out/'summary.json').exists())
                if case not in ['existing','symlink']:self.assertFalse(out.exists())

    def test_bom_conversion_changes_only_encoding_and_line_endings(self):
        native=b'{\n  "packages": ["../owned"]\n}\n'
        converted=runner.bom_crlf(native)
        self.assertTrue(converted.startswith(b'\xef\xbb\xbf'))
        self.assertEqual(converted.count(b'\xef\xbb\xbf'),1)
        self.assertNotIn(b'\n',converted.replace(b'\r\n',b''))
        self.assertEqual(json.loads(converted.decode('utf-8-sig')),json.loads(native))
        self.assertEqual(runner.bom_crlf(converted),converted)

    def fake_native(self,mode):
        def native(command,*,cwd,env,**kwargs):
            project=Path(cwd);out=project.parent;home=Path(env['HOME']);settings=project/'.pi/settings.json'
            state=project/'.planweft/installations.json';foreign=home/'.pi/agent/settings.json'
            source=project/'.planweft/versions/0.4.0-rc.11/node_modules/planweft/dist/pi/planweft'
            self.assertNotIn('OPENAI_API_KEY',env);self.assertEqual(env['PLANNING_DISABLED'],'1')
            self.assertEqual(kwargs['timeout'],180)
            rc=0;text=''
            if command[:2]==['pi','--version']:text='0.84.3\n'
            elif command[:2]==['pi','list']:
                data=json.loads(settings.read_bytes().decode('utf-8-sig')) if settings.exists() else {}
                if data.get('packages') and mode!='missing-native-source':text=str(source)+'\n'
            elif command[0]=='node':
                action=command[2]
                if action=='add':
                    shutil.copytree(out/'source/package',source.parents[2])
                    state.parent.mkdir(parents=True,exist_ok=True)
                    state.write_text(json.dumps({'agents':{'pi':{'status':'installed','version':'0.4.0-rc.11',
                        'nativeSource':str(source),'packageRoot':str(source.parents[2])}}}))
                    settings.parent.mkdir();settings.write_text(json.dumps({'packages':[os.path.relpath(source,settings.parent)]},indent=2)+'\n')
                elif action in ['doctor','update']:
                    data=json.loads(settings.read_bytes().decode('utf-8-sig'))
                    duplicated=len(data['packages'])>1 or foreign.exists()
                    if duplicated and mode!='allow-duplicate':rc=1;text='Another planning registration may be active'
                    elif mode=='old-parser':rc=1;text='Unexpected token BOM in JSON'
                    elif mode=='timeout' and action=='doctor':raise subprocess.TimeoutExpired(command,180,output='retained failure')
                    elif mode=='write-on-read':settings.write_bytes(settings.read_bytes()+b' ')
                elif action=='remove':
                    self.assertIn('--approve-pi-project',command)
                    if mode=='remove-failure':rc=1;text='cannot remove'
                    else:
                        state.write_text('{"agents":{}}');settings.write_text('{"packages":[]}')
                    if mode=='changed-record':(project/'requirements.md').write_bytes(b'wrong')
                else:self.fail('Unexpected action '+action)
            else:self.fail('Unexpected native call '+str(command))
            return subprocess.CompletedProcess(command,rc,text,'')
        return native

    def test_native_protocol_retains_old_failure_and_protects_bytes(self):
        for mode in ['fixed','old-parser','missing-native-source','allow-duplicate','write-on-read','timeout','remove-failure','changed-record']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);args=archive(root)
                with patch.dict(os.environ,{'OPENAI_API_KEY':'must-not-propagate'}),patch.object(runner.subprocess,'run',side_effect=self.fake_native(mode)):
                    result=runner.main(args)
                report=json.loads((root/'run/summary.json').read_text())
                self.assertEqual(result,0 if mode=='fixed' else 1)
                self.assertEqual(report['status'],'Passed' if mode=='fixed' else 'Failed')
                self.assertEqual(report['scenario'],runner.SCENARIO)
                self.assertEqual(set(report['assertions']),runner.ASSERTIONS)
                self.assertEqual(report['input_archive_sha256'],args[args.index('--sha256')+1])
                self.assertTrue(any(s['step']=='owned-remove' for s in report['steps']))
                if mode=='old-parser':
                    self.assertFalse(report['assertions']['doctor_success'])
                    self.assertTrue(report['assertions']['owned_remove_complete'])
                    self.assertIn('BOM',(root/'run/owned-doctor.log').read_text())
                if mode=='timeout':self.assertEqual(report['error'].split(':')[0],'TimeoutExpired')
                if mode!='changed-record':self.assertTrue(report['project_records_unchanged'])
                if mode=='fixed':
                    self.assertEqual((root/'run/settings-native.bin').read_bytes().decode(),
                        (root/'run/settings-bom-crlf.bin').read_bytes().decode('utf-8-sig').replace('\r\n','\n'))

    def test_restore_failure_is_reported_without_continuing_native_removal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);args=archive(root)
            settings=root/'run/项目 with spaces/.pi/settings.json'
            write=Path.write_bytes
            def fail_restore(path,data):
                if path==settings and data.startswith(b'{'):
                    raise OSError('synthetic restore failure')
                return write(path,data)
            with patch.object(runner.subprocess,'run',side_effect=self.fake_native('fixed')), \
                 patch.object(Path,'write_bytes',fail_restore):
                self.assertEqual(runner.main(args),1)
            report=json.loads((root/'run/summary.json').read_text())
            self.assertEqual(report['cleanup_error'],'Restore failed: OSError')
            self.assertFalse(report['assertions']['owned_remove_complete'])
            self.assertNotIn('owned-remove',[s['step'] for s in report['steps']])


if __name__=='__main__':unittest.main()
