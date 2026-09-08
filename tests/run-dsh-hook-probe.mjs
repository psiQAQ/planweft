// Real published DSH bridge + real hook subprocesses, with an explicit event
// carrier and shell-service fixture. This is a protocol probe, not a model run.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
const [packageRoot, output, sdkModules] = process.argv.slice(2);
if (!packageRoot || !output || fs.existsSync(output)) throw Error('Provide installed package root and new output directory');
const root=path.resolve(packageRoot),out=path.resolve(output);
if(out===root || out.startsWith(root+path.sep)) throw Error('Keep test output outside installed package');
const adapter=await import(pathToFileURL(path.join(root,'dist/dsh/planweft/index.mjs')).href);
fs.mkdirSync(out,{recursive:true});
const env={PATH:process.env.PATH,HOME:path.join(out,'home'),XDG_CACHE_HOME:path.join(out,'cache'),LANG:'C.UTF-8',PYTHONDONTWRITEBYTECODE:'1',PWF_FAST_PATH:process.env.PWF_FAST_PATH||'1'};
const handlers=new Map(),events=[],runs=[],warnings=[],plugins=[];
const modules=path.resolve(sdkModules || path.join(root,'node_modules'));
const {Context}=await import(pathToFileURL(path.join(modules,'@deepseek-ai/cordis/lib/index.js')).href);
const ctx=new Context();
// Observe native registrations without replacing bound Context methods,
// which would accidentally erase their private service scope.
ctx.on('internal/listener',(name,fn)=>{
  if(['agent/session-start','agent/pre-step','tools/pre-execute','tools/post-execute','agent/turn-stopping'].includes(name)) handlers.set(name,fn);
});
ctx.on('internal/plugin',fiber=>plugins.push({name:fiber.name,get config(){return fiber.config;},fiber}));
ctx.provide('sessionProjections',{stateOf:()=>({lastTurn:1})});
const skillControl=new AbortController();
ctx.provide('skills',{registerProvider:factory=>factory({signal:skillControl.signal,invalidate(){}})});
let shell={resolve:r=>r,run:async r=>{
  const result=spawnSync('sh',['-c',r.command],{cwd:r.workdir,env:{...env,...r.env},input:r.stdin,encoding:'utf8',timeout:r.timeoutMs});
  runs.push({cwd:r.workdir,event:JSON.parse(r.stdin).hook_event_name,exit:result.status,stdout:result.stdout,stderr:result.stderr});
  return {exitCode:result.status,stdout:{text:result.stdout||''},stderr:{text:result.stderr||''}};
}};
const fibers=[];
if(sdkModules) {
  const load=name=>import(pathToFileURL(path.resolve(sdkModules,name,'lib/index.js')).href);
  const {Context}=await load('@deepseek-ai/cordis');
  const runtime=new Context();
  for(const name of ['@deepseek-ai/dsh-subprocess-local','@deepseek-ai/dsh-sandbox-local']) {
    const plugin=(await load(name)).default, fiber=runtime.plugin(plugin,{});await fiber.await();fibers.push(fiber);
  }
  runtime.provide('sandboxPolicy',{defaultMode:'workspace-write',resolve:()=>({mode:'workspace-write',workspaceRoot:out})});
  const fiber=runtime.plugin((await load('@deepseek-ai/dsh-bash-sandbox')).default,{});await fiber.await();fibers.push(fiber);
  shell={resolve:r=>runtime.shell.resolve({...r,sandboxPolicy:{mode:'workspace-write',workspaceRoot:r.workdir},env:{...env,...r.env}}),run:async spec=>{
    const result=await runtime.shell.run(spec);
    runs.push({cwd:spec.workdir,event:JSON.parse(spec.stdin).hook_event_name,exit:result.exitCode,stdout:result.stdout.text,stderr:result.stderr.text,sandbox:result.sandbox});
    return result;
  }};
}
ctx.provide('shell',shell);
const adapterFiber=ctx.plugin(adapter,{});await adapterFiber.await();
for(const plugin of plugins) await plugin.fiber.await();
// Actual dependency readiness is part of this probe. Direct apply() calls
// cannot detect an installed bridge stranded in an inactive private scope.
for(let i=0;i<100 && !handlers.has('agent/pre-step');i++) await new Promise(r=>setTimeout(r,10));
assert.ok(handlers.has('agent/pre-step'),'native Cordis bridge never activated: '+JSON.stringify(plugins.map(p=>({name:p.name,state:p.fiber.state})))+'; '+warnings.join('; '));
assert.equal(plugins.find(p=>p.name==='hooks-claude-code')?.fiber.state,2);
assert.equal(plugins.filter(p=>p.name==='hooks-claude-code').length,1);
const hook=plugins.find(p=>p.name==='hooks-claude-code');assert.ok(!('projectDir' in hook.config));
assert.ok(path.isAbsolute(hook.config.configPath));
const signal=new AbortController().signal;
try {
  for(const id of ['A','B']) {
    const cwd=path.join(out,'项目 '+id);fs.mkdirSync(cwd);
    const plan='# Task Plan: DSH_MARKER_'+id+'\n\n## Goal\nTest project isolation.\n\n### Phase 1: Runtime\n- **Status:** in_progress\n';
    fs.writeFileSync(path.join(cwd,'task_plan.md'),plan);
    const injected=[],steered=[];
    const agent={session:{header:{id:'pw-dsh-'+id,cwd},append:(type,data)=>events.push({type,data})},inject:m=>injected.push(m),steer:m=>steered.push(m)};
    const messages=[{content:[{type:'text',text:'Continue the approved maintenance task.'}]}];
    const run=()=>handlers.get('agent/pre-step')({agent,messages,turn:1,signal},async()=>({kind:'enter',messages}));
    const first=await run();assert.ok(JSON.stringify(first).includes('DSH_MARKER_'+id));
    assert.ok(!JSON.stringify(first).includes('DSH_MARKER_'+(id==='A'?'B':'A')));
    const second=await run();assert.ok(JSON.stringify(second).includes('DSH_MARKER_'+id)); // PWF refreshes each prompt.
    const post=()=>handlers.get('tools/post-execute')({agent,name:'write',arguments:{},callId:'write-1',signal},{content:[{type:'text',text:'ok'}]},async()=>({kind:'pass',additionalContexts:[{content:[{type:'text',text:'other plugin context'}]}]}));
    const postFirst=await post();assert.equal(postFirst.additionalContexts.length,2);
    const postSecond=await post();assert.equal(postSecond.additionalContexts.length,1);
    assert.ok(JSON.stringify(postSecond).includes('other plugin context'));
    await run();assert.equal((await post()).additionalContexts.length,2);
    // A downstream permission denial remains unchanged.
    const denied=await handlers.get('tools/pre-execute')({agent,name:'read',arguments:{},callId:'read-1',signal},async()=>({kind:'deny',reason:'fixture-policy'}));
    assert.deepEqual(denied,{kind:'deny',reason:'fixture-policy'});
    await handlers.get('agent/turn-stopping')({agent,turn:1,signal});assert.equal(steered.length,0);
    assert.equal(fs.readFileSync(path.join(cwd,'task_plan.md'),'utf8'),plan);
    // Recovery in a fresh session uses project files only.
    agent.session.header.id+='-fresh';handlers.get('agent/session-start')({agent,source:'resume'});
    for(let i=0;i<100 && !injected.length;i++) await new Promise(r=>setTimeout(r,20));
    assert.ok(JSON.stringify(injected).includes('DSH_MARKER_'+id));
    // Gate counters and stall state remain in the selected plan, even when
    // the host recreates its temporary filesystem for every hook invocation.
    fs.writeFileSync(path.join(cwd,'.mode'),'autonomous gate\n');
    fs.writeFileSync(path.join(cwd,'.plan-attestation'),createHash('sha256').update(plan).digest('hex')+'\n');
    env.PWF_GATE_CAP='2';
    const stop=()=>handlers.get('agent/turn-stopping')({agent,turn:1,signal});
    await stop();assert.equal(steered.length,1);
    await stop();assert.equal(steered.length,1); // no new ledger observation: release stop
    fs.writeFileSync(path.join(cwd,'ledger-owner.jsonl'),'{"observation":"advanced"}\n');
    await stop();assert.equal(steered.length,2);
    fs.appendFileSync(path.join(cwd,'ledger-owner.jsonl'),'{"observation":"advanced again"}\n');
    await stop();assert.equal(steered.length,2); // cap reached
    assert.equal(fs.readFileSync(path.join(cwd,'.stop_blocks'),'utf8').trim(),'2');
    assert.equal(fs.readFileSync(path.join(cwd,'task_plan.md'),'utf8'),plan);
  }
  const empty=path.join(out,'empty');fs.mkdirSync(empty);
  const agent={session:{header:{id:'empty',cwd:empty},append(){}}};
  const messages=[{content:[{type:'text',text:'Read-only diagnosis.'}]}];
  const unplanned=()=>handlers.get('agent/pre-step')({agent,messages,turn:1,signal},async()=>({kind:'enter',messages}));
  assert.ok(JSON.stringify(await unplanned()).includes('project-docs'));
  assert.deepEqual(fs.readdirSync(empty),[]);
  fs.symlinkSync('missing',path.join(empty,'.planning'));
  assert.ok(!JSON.stringify(await unplanned()).includes('first load the installed'));
  const previous=process.env.PLANNING_DISABLED;process.env.PLANNING_DISABLED='1';
  const disabled=[];adapter.apply({plugin:p=>disabled.push(p.name)});
  if(previous===undefined)delete process.env.PLANNING_DISABLED;else process.env.PLANNING_DISABLED=previous;
  assert.ok(!disabled.includes('hooks-claude-code'));
  assert.ok(runs.every(r=>r.exit===0));
  assert.ok(warnings.every(w=>w.includes('Stop hook emitted a systemMessage'))); // Explicit official bridge limitation.
  fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify({status:'Passed',kind:sdkModules?'protocol fixture with real DSH bridge and sandbox':'protocol fixture with real DSH bridge and subprocesses',fastPath:env.PWF_FAST_PATH,nativeCordisReadiness:true,projectIsolation:true,promptRefresh:true,postToolDedup:true,recovery:true,defaultStop:true,gatedCap:true,gatedStall:true,unplannedReadOnly:true,brokenStatePreserved:true,stopSystemMessage:'not surfaced by DSH',permissionPreserved:true,disabled:true},null,2));
  console.log('Passed');
} finally {
  skillControl.abort();
  await adapterFiber.dispose();
  for(const fiber of fibers.reverse())await fiber.dispose();
  fs.writeFileSync(path.join(out,'trace.json'),JSON.stringify({events,runs,warnings},null,2));
}
