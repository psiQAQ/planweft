import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {Installer, parse} from '../lib/installer.mjs';

function fixture(t) {
  const root = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), 'planweft 中文 '));
  t.after(() => fs.rmSync(root, {recursive:true, force:true}));
  const home = path.join(root, 'home'), project = path.join(root, 'project with spaces');
  fs.mkdirSync(home); fs.mkdirSync(project);
  fs.writeFileSync(path.join(project,'task_plan.md'), 'approved task\r\n');
  fs.mkdirSync(path.join(project,'docs')); fs.writeFileSync(path.join(project,'docs/spec.md'),'approved requirements');
  const packages = {};
  for (const [version, files] of [['0.4.0-rc.1', {'SKILL.md':'A', 'removed.txt':'old', 'changed.txt':'A'}],['0.4.0-rc.2', {'SKILL.md':'B', 'added.txt':'new', 'changed.txt':'B'}]]) {
    const p = path.join(root,version); fs.mkdirSync(p);
    fs.writeFileSync(path.join(p,'package.json'),JSON.stringify({name:'planweft',version}));
    const skill = path.join(p,'dist/opencode/planweft/skills/project-docs'); fs.mkdirSync(skill,{recursive:true});
    for (const [name, content] of Object.entries(files)) fs.writeFileSync(path.join(skill,name),content);
    for (const host of ['claude','codex']) {
      const platform = path.join(p,`dist/${host}/planweft`); fs.mkdirSync(platform,{recursive:true}); fs.writeFileSync(path.join(platform,'version.txt'),version);
      const cat = path.join(p,host==='claude'?'.claude-plugin/marketplace.json':'.agents/plugins/marketplace.json'); fs.mkdirSync(path.dirname(cat),{recursive:true});
      fs.writeFileSync(cat,JSON.stringify({name:'planweft',plugins:[{name:'planweft',source:`./dist/${host}/planweft`}]}));
    }
    packages[version]=p;
  }
  const calls=[];
  const create=(argv, version='0.4.0-rc.1', extra={}) => {
    const packageRoot=packages[version];
    const run=(argv) => {
      calls.push(argv);
      if (extra.fail?.(argv)) throw Error('injected native failure');
      if(argv[0]==='npm') {
        const prefix=argv[argv.indexOf('--prefix')+1];
        fs.mkdirSync(path.join(prefix,'node_modules'),{recursive:true});
        fs.cpSync(packageRoot,path.join(prefix,'node_modules/planweft'),{recursive:true});
        fs.writeFileSync(path.join(prefix,'package-lock.json'),'{}');
      }
    };
    return new Installer(parse(argv),{cwd:extra.cwd||project,env:{HOME:home,PATH:process.env.PATH},packageRoot,run,log:()=>{}});
  };
  return {root,home,project,packages,calls,create};
}

test('arguments reject ambiguous scope/method and non-agent values', () => {
  for (const argv of [['add','--global','--project'],['add','--copy','--symlink'],['add','-a','unknown'],['add','--source'],['remove','--source','x.tgz']]) assert.throws(()=>parse(argv));
});
test('list, doctor and dry run do not create state or touch project documents', async t => {
  const f=fixture(t);
  for(const argv of [['list'],['doctor'],['add','-a','agents','--dry-run']]) assert.equal(await f.create(argv).execute(),0);
  assert.deepEqual(fs.readdirSync(f.project).sort(),['docs','task_plan.md']); assert.equal(f.calls.length,0);
});
test('unsupported native scope fails before any write', async t => {
  const f=fixture(t); await assert.rejects(f.create(['add','-a','codex']).execute(),/no supported project scope/);
  assert.equal(fs.existsSync(path.join(f.project,'.planweft')),false);
});
test('copied install updates added/changed/deleted files, rolls back and uninstalls', async t => {
  const f=fixture(t), target=path.join(f.project,'.agents/skills/project-docs');
  assert.equal(await f.create(['add','-a','agents','--copy']).execute(),0);
  assert.equal(fs.readFileSync(path.join(target,'changed.txt'),'utf8'),'A');
  assert.equal(await f.create(['update','-a','agents'],'0.4.0-rc.2').execute(),0);
  assert.equal(fs.existsSync(path.join(target,'removed.txt')),false); assert.equal(fs.readFileSync(path.join(target,'added.txt'),'utf8'),'new');
  assert.equal(await f.create(['update','-a','agents']).execute(),0);
  assert.equal(fs.existsSync(path.join(target,'added.txt')),false); assert.equal(fs.existsSync(path.join(target,'removed.txt')),true);
  assert.equal(await f.create(['remove','-a','agents']).execute(),0); assert.equal(fs.existsSync(target),false);
  assert.equal(fs.readFileSync(path.join(f.project,'task_plan.md'),'utf8'),'approved task\r\n');
  assert.equal(fs.readFileSync(path.join(f.project,'docs/spec.md'),'utf8'),'approved requirements');
});
test('user modifications block update and uninstall', async t => {
  const f=fixture(t); await f.create(['add','-a','agents','--copy']).execute();
  const target=path.join(f.project,'.agents/skills/project-docs/SKILL.md'); fs.writeFileSync(target,'user text');
  for(const action of ['update','remove']) await assert.rejects(f.create([action,'-a','agents'],'0.4.0-rc.2').execute(),/User changes preserved/);
  assert.equal(fs.readFileSync(target,'utf8'),'user text');
});
test('symlink points to persistent complete version and updates without mixed files', async t => {
  const f=fixture(t), target=path.join(f.project,'.agents/skills/project-docs');
  assert.equal(await f.create(['add','-a','agents','--symlink']).execute(),0);
  assert.equal(fs.lstatSync(target).isSymbolicLink(),true); const old=fs.realpathSync(target);
  assert.equal(await f.create(['update','-a','agents'],'0.4.0-rc.2').execute(),0);
  assert.notEqual(fs.realpathSync(target),old); assert.equal(fs.existsSync(old),true);
  assert.equal(fs.existsSync(path.join(target,'removed.txt')),false);
});
test('foreign destination and symlink parents are protected', async t => {
  const f=fixture(t), target=path.join(f.project,'.agents/skills/project-docs'); fs.mkdirSync(target,{recursive:true}); fs.writeFileSync(path.join(target,'mine'),'keep');
  await assert.rejects(f.create(['add','-a','agents']).execute(),/Foreign target/);
  fs.rmSync(path.join(f.project,'.agents'),{recursive:true});
  fs.symlinkSync(f.home,path.join(f.project,'.agents'),process.platform==='win32'?'junction':'dir');
  await assert.rejects(f.create(['add','-a','agents']).execute(),/Symlink in managed parent/);
});
test('two projects keep distinct native catalogs and versions', async t => {
  const f=fixture(t), b=path.join(f.root,'project B'); fs.mkdirSync(b);
  assert.equal(await f.create(['add','-a','claude']).execute(),0);
  assert.equal(await f.create(['add','-a','claude'],'0.4.0-rc.2',{cwd:b}).execute(),0);
  const astate=JSON.parse(fs.readFileSync(path.join(f.project,'.planweft/installations.json'))), bstate=JSON.parse(fs.readFileSync(path.join(b,'.planweft/installations.json')));
  assert.notEqual(astate.agents.claude.catalog,bstate.agents.claude.catalog);
  assert.equal(await f.create(['update','-a','claude'],'0.4.0-rc.2').execute(),0);
  assert.equal(await f.create(['remove','-a','claude']).execute(),0);
  assert.equal(JSON.parse(fs.readFileSync(path.join(b,'.planweft/installations.json'))).agents.claude.version,'0.4.0-rc.2');
});
test('native install failure remains failed, registration can be removed', async t => {
  const f=fixture(t);
  const code=await f.create(['add','-a','claude'],'0.4.0-rc.1',{fail:a=>a[0]==='claude'&&a[2]==='install'}).execute();
  assert.equal(code,1);
  const rec=JSON.parse(fs.readFileSync(path.join(f.project,'.planweft/installations.json'))).agents.claude;
  assert.equal(rec.status,'failed'); assert.equal(rec.steps['marketplace-add'],'done'); assert.equal(rec.steps['native-install'],'failed');
  assert.equal(await f.create(['remove','-a','claude']).execute(),0);
  assert.ok(f.calls.some(a=>a.join(' ').includes('marketplace remove')));
});
test('tampered stored version is rejected before reuse', async t => {
  const f=fixture(t); await f.create(['add','-a','agents','--copy']).execute();
  const p=path.join(f.project,'.planweft/versions/0.4.0-rc.1/node_modules/planweft/dist/opencode/planweft/skills/project-docs/SKILL.md'); fs.writeFileSync(p,'tampered');
  await assert.rejects(f.create(['update','-a','agents']).execute(),/integrity mismatch/);
});
test('multi-agent failure preserves independent success without success exit', async t => {
  const f=fixture(t); assert.equal(await f.create(['add','-a','agents','-a','claude'],'0.4.0-rc.1',{fail:a=>a[0]==='claude'}).execute(),1);
  const state=JSON.parse(fs.readFileSync(path.join(f.project,'.planweft/installations.json')));
  assert.equal(state.agents.agents.status,'installed'); assert.equal(state.agents.claude.status,'failed');
});
test('native remove allows reinstall and foreign catalog is never overwritten', async t => {
  const f=fixture(t); await f.create(['add','-a','claude']).execute(); await f.create(['remove','-a','claude']).execute();
  assert.equal(await f.create(['add','-a','claude']).execute(),0);
  await f.create(['remove','-a','claude']).execute();
  const cat=path.join(f.project,'.planweft/registries/claude/.claude-plugin/marketplace.json'); fs.writeFileSync(cat,'foreign');
  for (let i=0; i<2; i++) { assert.equal(await f.create(['add','-a','claude']).execute(),1); assert.equal(fs.readFileSync(cat,'utf8'),'foreign'); }
});
test('mode switching is rejected before losing active native registration', async t => {
  const f=fixture(t); await f.create(['add','-a','pi']).execute();
  const calls=f.calls.length;
  await assert.rejects(f.create(['add','-a','pi','--skill-only']).execute(),/before switching/);
  assert.equal(f.calls.length,calls);
  assert.equal(await f.create(['remove','-a','pi']).execute(),0); assert.ok(f.calls.some(a=>a[0]==='pi'&&a[1]==='remove'));
});
test('Claude other-project registration does not conflict, user scope does', async t => {
  const f=fixture(t), file=path.join(f.home,'.claude/plugins/installed_plugins.json'); fs.mkdirSync(path.dirname(file),{recursive:true});
  fs.writeFileSync(file,JSON.stringify({version:2,plugins:{'planweft@planweft-cli-claude-other':[{scope:'project',projectPath:path.join(f.root,'other-project')}]}}));
  assert.equal(await f.create(['add','-a','claude']).execute(),0);
  fs.writeFileSync(file,JSON.stringify({version:2,plugins:{'planweft@planweft':[{scope:'user'}]}}));
  await assert.rejects(f.create(['update','-a','claude']).execute(),/Another planning registration/);
});
test('Pi replacement failure attempts restoration and keeps failure evidence', async t => {
  const f=fixture(t); await f.create(['add','-a','pi']).execute();
  assert.equal(await f.create(['update','-a','pi'],'0.4.0-rc.2',{fail:a=>a[0]==='pi'&&a[1]==='install'&&a.at(-1).includes('rc.2')}).execute(),1);
  const rec=JSON.parse(fs.readFileSync(path.join(f.project,'.planweft/installations.json'))).agents.pi;
  assert.equal(rec.steps['native-restore'],'done'); assert.equal(rec.actualVersion,'0.4.0-rc.1');
  assert.equal(await f.create(['remove','-a','pi']).execute(),0);
});
test('component removal failure records progress and can be retried', async t => {
  const f=fixture(t); assert.equal(await f.create(['add','-a','opencode','--copy']).execute(),0);
  const rm=fs.rmSync;
  fs.rmSync=(target, options)=>{ if(target.endsWith('plugins/planweft.ts')) throw Error('injected EACCES'); return rm(target,options); };
  try { assert.equal(await f.create(['remove','-a','opencode']).execute(),1); } finally { fs.rmSync=rm; }
  assert.equal(await f.create(['remove','-a','opencode']).execute(),0);
});
test('partial copy failure restores the previous complete component', async t => {
  const f=fixture(t); await f.create(['add','-a','agents','--copy']).execute();
  // Pre-cache B, isolating the injected error to component copying.
  await f.create(['add','-a','continue','--copy'],'0.4.0-rc.2').execute();
  const cp=fs.cpSync;
  fs.cpSync=(source,target,options)=>{ if(target.includes('.planweft-component-')) { fs.mkdirSync(target,{recursive:true}); fs.writeFileSync(path.join(target,'partial'),'partial'); throw Error('injected ENOSPC'); } return cp(source,target,options); };
  try { assert.equal(await f.create(['update','-a','agents'],'0.4.0-rc.2').execute(),1); } finally { fs.cpSync=cp; }
  const target=path.join(f.project,'.agents/skills/project-docs'); assert.equal(fs.readFileSync(path.join(target,'SKILL.md'),'utf8'),'A'); assert.equal(fs.existsSync(path.join(target,'partial')),false);
  assert.equal(await f.create(['update','-a','agents'],'0.4.0-rc.2').execute(),0);
});
