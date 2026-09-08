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
    fs.cpSync(path.join(p,'dist/opencode/planweft'),path.join(p,'dist/dsh/planweft'),{recursive:true});
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
      if(argv[0]==='dsh') {
        const profile=argv[argv.indexOf('--profile')+1],dir=path.join(home,'.dsh/profiles',profile);
        fs.mkdirSync(dir,{recursive:true});const file=path.join(dir,'package.json');
        const manifest=fs.existsSync(file)?JSON.parse(fs.readFileSync(file)):{dependencies:{},dsh:{profile:{bundles:['@deepseek-ai/dsh-base']}}};
        if(argv.includes('add')) {manifest.dependencies.planweft=argv.at(-1);if(!manifest.dsh.profile.bundles.includes('planweft'))manifest.dsh.profile.bundles.push('planweft');}
        else if(argv.includes('remove')) {delete manifest.dependencies.planweft;manifest.dsh.profile.bundles=manifest.dsh.profile.bundles.filter(n=>n!=='planweft');}
        if(extra.failDshAfterPersist && argv.includes('add')) manifest.dependencies.planweft='link:'+path.relative(dir,argv.at(-1).slice(5));
        fs.writeFileSync(file,JSON.stringify(manifest));
        if(extra.failDshAfterPersist && argv.includes('add')) throw Error('failure after native persistence');
      }
      if(argv[0]==='npm') {
        const prefix=argv[argv.indexOf('--prefix')+1];
        fs.mkdirSync(path.join(prefix,'node_modules'),{recursive:true});
        fs.cpSync(packageRoot,path.join(prefix,'node_modules/planweft'),{recursive:true});
        fs.writeFileSync(path.join(prefix,'package-lock.json'),'{}');
      }
    };
    return new Installer(parse(argv),{cwd:extra.cwd||project,env:{HOME:home,PATH:process.env.PATH,...extra.env},packageRoot,run,log:()=>{}});
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


test('DSH skill lifecycle follows nearest Git root and protects user records', async t => {
  const f=fixture(t);fs.mkdirSync(path.join(f.project,'.git'));
  const nested=path.join(f.project,'nested');fs.mkdirSync(nested);
  await assert.rejects(f.create(['add','-a','dsh','--skill-only'],undefined,{cwd:nested}).execute(),/Git root/);
  const run=(action,version='0.4.0-rc.1') => f.create([action,'-a','dsh','--skill-only','--copy'],version).execute();
  await run('add');
  const skill=path.join(f.project,'.dsh/skills/project-docs');
  assert.equal(fs.readFileSync(path.join(skill,'SKILL.md'),'utf8'),'A');
  await run('update','0.4.0-rc.2');assert.equal(fs.existsSync(path.join(skill,'removed.txt')),false);
  await run('update');assert.equal(fs.existsSync(path.join(skill,'added.txt')),false);
  fs.writeFileSync(path.join(skill,'SKILL.md'),'user edit');
  await assert.rejects(run('remove'),/User changes preserved/);
  fs.writeFileSync(path.join(skill,'SKILL.md'),'A');await run('remove');
  assert.equal(fs.existsSync(skill),false);
  assert.equal(fs.readFileSync(path.join(f.project,'task_plan.md'),'utf8'),'approved task\r\n');
});

test('DSH global skill uses DSH_HOME and unsupported full integration fails before writes', async t => {
  const f=fixture(t),dshHome=path.join(f.root,'custom-dsh');
  await assert.rejects(f.create(['add','-a','dsh']).execute(),/--skill-only/);
  assert.equal(fs.existsSync(path.join(f.project,'.planweft')),false);
  await f.create(['add','-a','dsh','--global','--skill-only','--copy'],undefined,{env:{DSH_HOME:dshHome}}).execute();
  assert.equal(fs.existsSync(path.join(dshHome,'skills/project-docs/SKILL.md')),true);
  await f.create(['remove','-a','dsh','--global'],undefined,{env:{DSH_HOME:dshHome}}).execute();
});

test('DSH home follows native whitespace and tilde expansion', t => {
  const f=fixture(t);
  for (const [value,expected] of [['  ',path.join(f.home,'.dsh')],['~',f.home],['~/dsh custom',path.join(f.home,'dsh custom')],['~\\dsh',path.join(f.home,'dsh')]]) {
    assert.equal(f.create(['add','-a','dsh','--global','--skill-only'],undefined,{env:{DSH_HOME:value}}).hostRoot('dsh'),expected);
  }
});


test('DSH native profile installs updates rolls back and preserves foreign settings', async t => {
  const f=fixture(t),args=['-a','dsh','--global','--dsh-profile','web'];
  const run=(action,version) => f.create([action,...args],version).execute();
  assert.equal(await run('add'),0);
  const file=path.join(f.home,'.dsh/profiles/web/package.json');
  const manifest=JSON.parse(fs.readFileSync(file));manifest.other='keep';fs.writeFileSync(file,JSON.stringify(manifest));
  assert.equal(await run('update','0.4.0-rc.2'),0);
  assert.equal(await run('update'),0);
  await assert.rejects(f.create(['update','-a','dsh','--global','--dsh-profile','headless']).execute(),/(?:changing profile|differs from)/);
  assert.equal(await run('remove'),0);
  const after=JSON.parse(fs.readFileSync(file));assert.equal(after.other,'keep');assert.ok(!after.dependencies.planweft);
  assert.deepEqual(after.dsh.profile.bundles,['@deepseek-ai/dsh-base']);
});

test('DSH native ownership and failed update keep the previous profile source', async t => {
  const f=fixture(t),args=['-a','dsh','--global'];
  assert.equal(await f.create(['add',...args]).execute(),0);
  const file=path.join(f.home,'.dsh/profiles/headless/package.json'),before=fs.readFileSync(file,'utf8');
  assert.equal(await f.create(['update',...args],'0.4.0-rc.2',{fail:a=>a[0]==='dsh' && a.includes('add') && a.at(-1).includes('rc.2')}).execute(),1);
  assert.equal(fs.readFileSync(file,'utf8'),before);
  assert.equal(await f.create(['update',...args]).execute(),0);
  const manifest=JSON.parse(before);manifest.dependencies.planweft='npm:someone-else';fs.writeFileSync(file,JSON.stringify(manifest));
  await assert.rejects(f.create(['remove',...args]).execute(),/User-modified DSH/);
});

test('DSH profile argument and foreign source are rejected before installation', async t => {
  const f=fixture(t);
  for(const value of ['../web','desktop','web/x'])assert.throws(()=>parse(['add','-a','dsh','--dsh-profile',value]),/Invalid/);
  assert.throws(()=>parse(['add','-a','pi','--dsh-profile','web']),/requires/);
  const file=path.join(f.home,'.dsh/profiles/headless/package.json');fs.mkdirSync(path.dirname(file),{recursive:true});
  fs.writeFileSync(file,JSON.stringify({dependencies:{planweft:'0.3.0'}}));
  await assert.rejects(f.create(['add','-a','dsh','--global']).execute(),/Foreign DSH/);
  assert.equal(f.calls.length,0);
});


test('DSH partial native persistence accepts equivalent relative links for recovery', async t => {
  const f=fixture(t),args=['-a','dsh','--global'];
  assert.equal(await f.create(['add',...args],undefined,{failDshAfterPersist:true}).execute(),1);
  assert.equal(await f.create(['update',...args]).execute(),0);
  assert.equal(await f.create(['remove',...args]).execute(),0);
});

test('DSH explicit profile mismatch cannot remove or report another profile', async t => {
  const f=fixture(t),args=['-a','dsh','--global'];await f.create(['add',...args]).execute();
  const before=f.calls.length;
  for(const action of ['remove','doctor','list'])await assert.rejects(f.create([action,...args,'--dsh-profile','web']).execute(),/differs from/);
  assert.equal(f.calls.length,before);
});


test('DSH detects a second planning hook in a native user overlay before writes', async t => {
  const f=fixture(t),file=path.join(f.home,'.dsh/cordis.patch.yml');fs.mkdirSync(path.dirname(file),{recursive:true});
  fs.writeFileSync(file,'- insert:\n    - name: planweft/dsh\n');
  await assert.rejects(f.create(['add','-a','dsh','--global']).execute(),/Another planning hook/);
  assert.equal(f.calls.length,0);
});


test('DSH duplicate-hook hints ignore whole-line comments and skill-only operations', async t => {
  const f=fixture(t),file=path.join(f.home,'.dsh/cordis.patch.yml');fs.mkdirSync(path.dirname(file),{recursive:true});
  fs.writeFileSync(file,'# old program-design removed\n[]\n');
  assert.equal(await f.create(['add','-a','dsh','--global','--dry-run']).execute(),0);
  fs.writeFileSync(file,'- insert:\n    - name: planweft/dsh\n');
  assert.equal(await f.create(['add','-a','dsh','--global','--skill-only']).execute(),0);
});
