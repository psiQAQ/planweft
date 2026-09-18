import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';

const ROOT = path.resolve(new URL('..', import.meta.url).pathname);
const BIN = path.join(ROOT, 'bin/planweft.mjs');

function digest(data) { return crypto.createHash('sha256').update(data).digest('hex'); }

function fixture(t) {
  const root = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), 'planweft-p1-'));
  const project = path.join(root, 'project');
  const plan = path.join(project, '.planning', 'p1-plan');
  fs.mkdirSync(plan, {recursive: true});
  fs.writeFileSync(path.join(plan, 'task_plan.md'), [
    '# Task Plan',
    '',
    '## Goal',
    '',
    'Keep the authorization and constraints in the active document.',
    '',
    '## Phases',
    '',
    '### Phase 1: Completed implementation',
    '- [x] artifact evidence',
    '- [x] recovery evidence',
    '- **Status:** complete',
    '',
    '### Phase 2: Pending validation',
    '- [ ] independent cold read',
    '- **Status:** pending',
    '',
    '## Constraints',
    '',
    'Do not execute command strings or discard unresolved work.',
    '',
  ].join('\n'));
  fs.writeFileSync(path.join(plan, 'findings.md'), '# Findings\n\nKeep this file byte-identical.\n');
  fs.writeFileSync(path.join(plan, 'progress.md'), '# Progress\n\nKeep this file byte-identical.\n');
  fs.writeFileSync(path.join(project, 'results.log'), '3 passed\n1 failed\n2 skipped\nFAIL test-bad\n');
  fs.writeFileSync(path.join(project, 'record.json'), '{}');
  t.after(() => fs.rmSync(root, {recursive: true, force: true}));
  const run = (args, extraEnv = {}) => {
    const result = spawnSync(process.execPath, [BIN, 'state', ...args], {
      cwd: project,
      env: {...process.env, PLAN_ID: 'p1-plan', ...extraEnv},
      encoding: 'utf8',
    });
    let json = null;
    try { json = result.stdout ? JSON.parse(result.stdout) : null; } catch {}
    return {...result, json};
  };
  return {root, project, plan, run};
}

function recordResult(f) {
  const data = fs.readFileSync(path.join(f.project, 'results.log'));
  const input = {
    idempotency_key: 'p1-results',
    execution: {command: 'echo never-run', exit_code: 0, collection_method: 'reported'},
    subject: {phase: 'S15'},
    observed_result: 'Failed',
    interpretation: 'The failure remains an observed result; no root cause is inferred.',
    criteria: {covered: ['quote'], not_covered: ['real agent']},
    freshness: {status: 'unknown', reason: 'fixture freshness is not assessed', checked_at: null, subject_sha256: null},
    artifacts: [{path: 'results.log', media_type: 'text/plain', encoding: 'utf-8', capture_completeness: 'complete', origin: 'imported'}],
    excerpts: [],
  };
  const inputPath = path.join(f.project, 'record.json');
  fs.writeFileSync(inputPath, JSON.stringify(input));
  const recorded = f.run(['record', '--input', 'record.json', '--json']);
  assert.equal(recorded.status, 0, recorded.stderr);
  return digest(data);
}

test('checkpoint dry-run preserves the prelude and phase status, then applies recoverably', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const before = fs.readFileSync(path.join(f.plan, 'task_plan.md'));
  const dryRun = f.run(['checkpoint', '--dry-run']);
  assert.equal(dryRun.status, 0, dryRun.stderr);
  assert.equal(dryRun.json.writes, false);
  assert.equal(dryRun.json.archived_phases.length, 1);
  assert.equal(fs.existsSync(path.join(f.plan, '.planweft-state', 'checkpoints')), true);
  assert.equal(fs.readdirSync(path.join(f.plan, '.planweft-state', 'checkpoints')).length, 0);

  const applied = f.run(['checkpoint', '--apply']);
  assert.equal(applied.status, 0, applied.stderr);
  assert.equal(applied.json.writes, true);
  const checkpointId = applied.json.checkpoint_id;
  const after = fs.readFileSync(path.join(f.plan, 'task_plan.md'), 'utf8');
  assert.equal(after.includes('### Phase 1: Completed implementation'), true);
  assert.equal(after.includes('**Status:** complete'), true);
  assert.equal(after.includes('### Phase 2: Pending validation'), true);
  assert.equal(after.includes('**Status:** pending'), true);
  assert.equal(after.includes('- checkpoint:'), true);
  assert.equal(after.includes('Keep the authorization and constraints'), true);
  assert.equal(after.includes('Do not execute command strings'), true);
  assert.notEqual(after, before.toString('utf8'));

  const manifestPath = path.join(f.plan, '.planweft-state', 'checkpoints', checkpointId, 'manifest.json');
  const manifest = JSON.parse(fs.readFileSync(manifestPath));
  assert.equal(manifest.status, 'applied');
  assert.equal(fs.existsSync(path.join(f.plan, '.planweft-state', 'checkpoints', checkpointId, 'before', 'task_plan.md')), true);
  assert.equal(fs.existsSync(path.join(f.plan, '.planweft-state', 'checkpoints', checkpointId, 'after', 'task_plan.md')), true);

  manifest.status = 'applying';
  delete manifest.applied_at;
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  fs.writeFileSync(path.join(f.plan, 'task_plan.md'), fs.readFileSync(path.join(f.plan, '.planweft-state', 'checkpoints', checkpointId, 'before', 'task_plan.md')));
  const resumed = f.run(['checkpoint', '--checkpoint', checkpointId, '--apply']);
  assert.equal(resumed.status, 0, resumed.stderr);
  assert.equal(resumed.json.writes, true);
  assert.equal(JSON.parse(fs.readFileSync(manifestPath)).status, 'applied');
  const repeated = f.run(['checkpoint', '--checkpoint', checkpointId, '--apply']);
  assert.equal(repeated.status, 0, repeated.stderr);
  assert.equal(repeated.json.writes, false);
});

test('checkpoint blocks on incomplete transactions and reducer quotes are byte-verifiable', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const transactions = path.join(f.plan, '.planweft-state', 'transactions', 'pending-transaction');
  fs.mkdirSync(transactions, {recursive: true});
  const store = JSON.parse(fs.readFileSync(path.join(f.plan, '.planweft-state', 'store.json')));
  fs.writeFileSync(path.join(transactions, 'journal.json'), JSON.stringify({
    schema_version: 1, transaction_id: 'pending-transaction', status: 'receipt_published',
    store_id: store.store_id, plan_id: store.plan_id, receipt_id: null, target: null,
  }));
  const blocked = f.run(['checkpoint', '--dry-run']);
  assert.equal(blocked.status, 3);
  fs.rmSync(transactions, {recursive: true});
  const artifactSha = recordResult(f);
  const reduced = f.run(['reduce', '--artifact', artifactSha]);
  assert.equal(reduced.status, 0, reduced.stderr);
  assert.equal(reduced.json.status, 'reduced');
  assert.equal(reduced.json.facts.some(fact => fact.field === 'passed_count' && fact.value === 3), true);
  assert.equal(reduced.json.facts.some(fact => fact.kind === 'failure'), true);
  assert.equal(reduced.json.facts.some(fact => fact.field === 'skipped_count' && fact.value === 2), true);
  assert.equal(reduced.json.interpretation.length, 0);
  fs.writeFileSync(path.join(f.project, 'reduced.json'), JSON.stringify(reduced.json));
  const verified = f.run(['quote-verify', '--input', 'reduced.json']);
  assert.equal(verified.status, 0, verified.stderr);
  assert.equal(verified.json.valid, true);
  assert.equal(verified.json.checked_quotes, reduced.json.facts.length);
  const tampered = {...reduced.json, facts: reduced.json.facts.map((fact, index) => index ? fact : {...fact, quote: {...fact.quote, quote: 'tampered'}})};
  fs.writeFileSync(path.join(f.project, 'reduced.json'), JSON.stringify(tampered));
  assert.equal(f.run(['quote-verify', '--input', 'reduced.json']).status, 2);
});

test('schema 1 stores are read-only until explicit upgrade with a verified backup', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const storePath = path.join(f.plan, '.planweft-state', 'store.json');
  const store = JSON.parse(fs.readFileSync(storePath));
  store.schema_version = 1;
  store.capabilities = {artifacts: true, receipts: true, records: true, checkpoints: false, remote_reducer: false};
  fs.writeFileSync(storePath, JSON.stringify(store, null, 2) + '\n');
  const data = fs.readFileSync(path.join(f.project, 'results.log'));
  const input = {
    idempotency_key: 'legacy-record', artifacts: [{path: 'results.log', media_type: 'text/plain', encoding: 'utf-8', capture_completeness: 'complete', origin: 'imported'}],
    excerpts: [], observed_result: 'Passed', criteria: {covered: ['artifact'], not_covered: []},
    freshness: {status: 'unknown', reason: 'not assessed', checked_at: null, subject_sha256: null},
  };
  fs.writeFileSync(path.join(f.project, 'record.json'), JSON.stringify(input));
  assert.equal(f.run(['record', '--input', 'record.json', '--json']).status, 4);
  const upgraded = f.run(['upgrade', '--json']);
  assert.equal(upgraded.status, 0, upgraded.stderr);
  assert.equal(upgraded.json.upgraded, true);
  assert.equal(JSON.parse(fs.readFileSync(storePath)).schema_version, 2);
  const migration = path.join(f.plan, '.planweft-state', 'migrations', upgraded.json.migration_id);
  assert.equal(fs.existsSync(path.join(migration, 'store.before.json')), true);
  assert.equal(digest(fs.readFileSync(path.join(migration, 'store.before.json'))), digest(Buffer.from(JSON.stringify({...store, schema_version: 1, capabilities: {artifacts: true, receipts: true, records: true, checkpoints: false, remote_reducer: false}}, null, 2) + '\n')));
  const recorded = f.run(['record', '--input', 'record.json', '--json']);
  assert.equal(recorded.status, 0, recorded.stderr);
  assert.equal(data.length > 0, true);
});
