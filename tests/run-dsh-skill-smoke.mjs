// Native DSH provider discovery without a model or personal profile.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const [modules, output] = process.argv.slice(2);
if (!modules || !output) throw Error('Usage: node tests/run-dsh-skill-smoke.mjs ISOLATED_NODE_MODULES NEW_OUTPUT');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.resolve(output);
if (out === root || out.startsWith(root + path.sep) || fs.existsSync(out)) throw Error('Output must be new and outside checkout');
const load = name => import(pathToFileURL(path.resolve(modules, name, 'lib/index.js')).href);
const {Context} = await load('@deepseek-ai/cordis');
const registry = await load('@deepseek-ai/dsh-skill');
const provider = await load('@deepseek-ai/dsh-skill-filesystem');
fs.mkdirSync(out, {recursive:true});
const project = path.join(out, '项目 with spaces'); fs.mkdirSync(project);
fs.mkdirSync(path.join(project,'.git'));
const skill = path.join(project,'.dsh/skills/project-docs');
fs.cpSync(path.join(root,'dist/dsh/planweft/skills/project-docs'),skill,{recursive:true});
const ctx = new Context();
const registryFiber = await ctx.plugin(registry.default);
const providerFiber = await ctx.plugin(provider,{dshHome:path.join(out,'home'),agentsHome:path.join(out,'agents'),watch:false});
try {
  const rows = await ctx.skills.list({cwd:project});
  assert.equal(rows.filter(x => x.name === 'project-docs').length,1);
  const loaded = await ctx.skills.get('project-docs',{cwd:project});
  assert.equal(loaded.path,path.join(skill,'SKILL.md'));
  assert.ok(loaded.content.includes('task_plan.md'));
  assert.ok(fs.existsSync(path.join(skill,'scripts/init-session.sh')));
  assert.ok(fs.existsSync(path.join(skill,'LICENSE')));
  fs.appendFileSync(path.join(skill,'SKILL.md'),'\nDSH_BODY_REFRESH_PROBE\n');
  assert.ok((await ctx.skills.get('project-docs',{cwd:project})).content.includes('DSH_BODY_REFRESH_PROBE'));
  const result={status:'Passed',kind:'official provider runtime; not a model session',
    providerVersion:JSON.parse(fs.readFileSync(path.resolve(modules,'@deepseek-ai/dsh-skill-filesystem/package.json'))).version,
    uniqueSkill:true,packageResources:true,bodyRefresh:true};
  fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result));
} finally { await providerFiber.dispose(); await registryFiber.dispose(); }
