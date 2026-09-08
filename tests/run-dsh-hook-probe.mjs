// Real published DSH bridge + real hook subprocesses, with an explicit event
// carrier and shell-service fixture. This is a protocol probe, not a model run.
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import assert from 'node:assert/strict';
const [packageRoot, output] = process.argv.slice(2);
if (!packageRoot || !output || fs.existsSync(output)) throw Error('Provide installed package root and new output directory');
const root=path.resolve(packageRoot),out=path.resolve(output);
if(out===root || out.startsWith(root+path.sep)) throw Error('Keep test output outside installed package');
const adapter=await import(pathToFileURL(path.join(root,'dist/dsh/planweft/index.mjs')).href);
fs.mkdirSync(out,{recursive:true});
const env={PATH:process.env.PATH,HOME:path.join(out,'home'),XDG_CACHE_HOME:path.join(out,'cache'),LANG:'C.UTF-8',PYTHONDONTWRITEBYTECODE:'1'};
const handlers=new Map(),events=[],runs=[],warnings=[],effects=[],plugins=[];
const ctx={logger:{warn:msg=>warnings.push(msg)},get:()=>undefined,
  sessionProjections:{stateOf:()=>({lastTurn:1})},
  on:(name,fn)=>handlers.set(name,fn),effect:fn=>effects.push(fn()),
  plugin:(plugin,config)=>{plugins.push({name:plugin.name,config});if(plugin.name==='hooks-claude-code')plugin.apply(ctx,config);},
  shell:{resolve:r=>r,run:async r=>{
    const result=spawnSync('sh',['-c',r.command],{cwd:r.workdir,env:{...env,...r.env},input:r.stdin,encoding:'utf8',timeout:r.timeoutMs});
    runs.push({cwd:r.workdir,event:JSON.parse(r.stdin).hook_event_name,exit:result.status,stdout:result.stdout,stderr:result.stderr});
    return {exitCode:result.status,stdout:{text:result.stdout||''},stderr:{text:result.stderr||''}};
  }}
};
adapter.apply(ctx);
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
    // A downstream permission denial remains unchanged.
    const denied=await handlers.get('tools/pre-execute')({agent,name:'read',arguments:{},callId:'read-1',signal},async()=>({kind:'deny',reason:'fixture-policy'}));
    assert.deepEqual(denied,{kind:'deny',reason:'fixture-policy'});
    await handlers.get('agent/turn-stopping')({agent,turn:1,signal});assert.equal(steered.length,0);
    assert.equal(fs.readFileSync(path.join(cwd,'task_plan.md'),'utf8'),plan);
    // Recovery in a fresh session uses project files only.
    agent.session.header.id+='-fresh';handlers.get('agent/session-start')({agent,source:'resume'});
    for(let i=0;i<100 && !injected.length;i++) await new Promise(r=>setTimeout(r,20));
    assert.ok(JSON.stringify(injected).includes('DSH_MARKER_'+id));
  }
  const previous=process.env.PLANNING_DISABLED;process.env.PLANNING_DISABLED='1';
  const disabled=[];adapter.apply({plugin:p=>disabled.push(p.name)});
  if(previous===undefined)delete process.env.PLANNING_DISABLED;else process.env.PLANNING_DISABLED=previous;
  assert.ok(!disabled.includes('hooks-claude-code'));
  assert.ok(runs.every(r=>r.exit===0));
  assert.ok(warnings.every(w=>w.includes('Stop hook emitted a systemMessage'))); // Explicit official bridge limitation.
  fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify({status:'Passed',kind:'protocol fixture with real DSH bridge and subprocesses',projectIsolation:true,promptRefresh:true,recovery:true,defaultStop:true,stopSystemMessage:'not surfaced by DSH',permissionPreserved:true,disabled:true},null,2));
  console.log('Passed');
} finally {
  for(const dispose of effects) if(typeof dispose==='function') await dispose();
  fs.writeFileSync(path.join(out,'trace.json'),JSON.stringify({events,runs,warnings},null,2));
}
