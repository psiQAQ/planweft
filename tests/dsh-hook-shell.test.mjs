import test from 'node:test';
import assert from 'node:assert/strict';
import {hookShell} from '../overlays/planweft/native/dsh/hook-shell.mjs';

test('native hook facade preserves sandbox requests, session binding and per-turn reminders', async () => {
  const requests=[];
  const response={exitCode:0,stdout:{text:JSON.stringify({hookSpecificOutput:{hookEventName:'PostToolUse',additionalContext:'[planweft] Reminder',permissionDecision:'deny'},continue:false,reason:'keep policy'}),truncated:false},stderr:{text:'diagnostic'},sandbox:{mode:'workspace-write'}};
  const shell=hookShell({resolve:r=>({...r,sandboxPolicy:{mode:'workspace-write'}}),run:async r=>{requests.push(r);return structuredClone(response);}});
  const invoke=(event,session='session-A')=>shell.run(shell.resolve({command:'public hook',stdin:JSON.stringify({hook_event_name:event,session_id:session}),env:{CLAUDE_PROJECT_DIR:'/project'},workdir:'/project'}));
  const first=await invoke('PostToolUse');assert.deepEqual(first,response);
  const second=await invoke('PostToolUse');
  const parsed=JSON.parse(second.stdout.text);
  assert.equal(parsed.hookSpecificOutput.additionalContext,undefined);
  assert.equal(parsed.hookSpecificOutput.permissionDecision,'deny');
  assert.equal(parsed.continue,false);assert.equal(parsed.reason,'keep policy');
  assert.deepEqual(second.stderr,response.stderr);assert.deepEqual(second.sandbox,response.sandbox);
  assert.equal(second.stdout.truncated,false);
  assert.deepEqual(await invoke('PostToolUse','session-B'),response);
  await invoke('UserPromptSubmit');assert.deepEqual(await invoke('PostToolUse'),response);
  await invoke('SessionStart');assert.deepEqual(await invoke('PostToolUse'),response);
  assert.deepEqual(await invoke('Stop'),response);
  assert.equal(requests[0].env.PWF_SESSION_ID,'session-A');
  assert.equal(requests[0].env.CLAUDE_PROJECT_DIR,'/project');
  assert.deepEqual(requests[0].sandboxPolicy,{mode:'workspace-write'});
  assert.equal(requests[0].workdir,'/project');
  assert.equal(requests[0].stdin,JSON.stringify({hook_event_name:'PostToolUse',session_id:'session-A'}));
  const stop=' {"session_id":"session-A","hook_event_name":"Stop","stop_hook_active":true} \n';
  await shell.run(shell.resolve({stdin:stop}));
  assert.equal(requests.at(-1).stdin,stop);
  assert.equal(requests.at(-1).env.PWF_SESSION_ID,'session-A');
});

test('malformed output, failed hooks, other context and invalid session IDs pass through', async () => {
  for(const text of ['not JSON','null','[]','42','"plain"',JSON.stringify({hookSpecificOutput:{hookEventName:'PostToolUse',additionalContext:'other plugin'}})]) {
    const response={exitCode:0,stdout:{text},stderr:{text:''}};
    const shell=hookShell({resolve:r=>r,run:async()=>response});
    for(let i=0;i<2;i++) assert.equal(await shell.run({stdin:JSON.stringify({session_id:'A',hook_event_name:'PostToolUse'})}),response);
  }
  const response={exitCode:2,stdout:{text:'blocked'},stderr:{text:'permission denied'}};
  const shell=hookShell({resolve:r=>r,run:async()=>response});
  const request={stdin:'{"session_id":"../bad","hook_event_name":"Stop","stop_hook_active":true}',env:{EXISTING:'keep'}};
  assert.deepEqual(shell.resolve(request),request);
  assert.equal(await shell.run(request),response);
});

test('reminder state evicts old sessions at its bounded capacity', async () => {
  const response={exitCode:0,stdout:{text:JSON.stringify({hookSpecificOutput:{hookEventName:'PostToolUse',additionalContext:'[planweft] Reminder'}})}};
  const shell=hookShell({resolve:r=>r,run:async()=>structuredClone(response)});
  const invoke=id=>shell.run({stdin:JSON.stringify({session_id:id,hook_event_name:'PostToolUse'})});
  for(let i=0;i<1025;i++) assert.deepEqual(await invoke('s'+i),response);
  assert.equal(JSON.parse((await invoke('s1024')).stdout.text).hookSpecificOutput.additionalContext,undefined);
  assert.deepEqual(await invoke('s0'),response);
});
