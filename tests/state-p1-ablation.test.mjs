import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import {
  checkpointState,
  initStore,
  recordState,
  reduceArtifact,
  verifyReducedQuotes,
} from '../overlays/planweft/state/core.mjs';

const planId = '2026-09-17-sol-pi-state-management-implementation';

function planText() {
  return [
    `# Plan ${planId}`,
    '',
    '## Goal',
    '',
    'Run the deterministic P1 offline ablation fixture.',
    '',
    '### Phase 1: completed implementation',
    '',
    ...Array.from({ length: 24 }, (_, index) => `- completed detail ${index + 1}`),
    '- **Status:** complete',
    '',
    '### Phase 2: pending publication',
    '',
    '- **Status:** pending',
    '- constraint: real Agent/model and tokens/cost remain Not Run',
    '',
  ].join('\n');
}

async function makeFixture(root) {
  const planDir = path.join(root, '.planning', planId);
  await (await import('node:fs/promises')).mkdir(planDir, { recursive: true });
  const content = planText();
  await writeFile(path.join(planDir, 'task_plan.md'), content);
  await writeFile(path.join(planDir, 'findings.md'), `${content}\n${content}`);
  await writeFile(path.join(planDir, 'progress.md'), content);
  const store = await initStore(planDir, { cwd: root });
  return { planDir, store };
}

async function measureVariant(name, configure) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'planweft-p1-ablation-'));
  const started = process.hrtime.bigint();
  try {
    const { planDir, store } = await makeFixture(root);
    const before = await Promise.all(
      ['task_plan.md', 'findings.md', 'progress.md'].map(async (file) => {
        const data = await readFile(path.join(planDir, file));
        return data.byteLength;
      }),
    );
    const result = await configure({ root, planDir, store, activeBytes: before.reduce((sum, value) => sum + value, 0) });
    const after = await Promise.all(
      ['task_plan.md', 'findings.md', 'progress.md'].map(async (file) => {
        const data = await readFile(path.join(planDir, file));
        return data.byteLength;
      }),
    );
    return {
      name,
      active_document_bytes_before: before.reduce((sum, value) => sum + value, 0),
      active_document_bytes_after: after.reduce((sum, value) => sum + value, 0),
      saved_bytes: before.reduce((sum, value) => sum + value, 0) - after.reduce((sum, value) => sum + value, 0),
      tool_calls: result.toolCalls,
      recall_calls: result.recallCalls,
      reducer_facts: result.reducerFacts,
      wall_time_ms: Number(process.hrtime.bigint() - started) / 1_000_000,
      tokens: 'Not Run',
      cost: 'Not Run',
    };
  } finally {
    await rm(root, { recursive: true, force: true });
  }
}

test('P1 four-way offline ablation is deterministic and records measurable local evidence', async () => {
  const variants = [];
  variants.push(await measureVariant('P0', async () => ({ toolCalls: 0, recallCalls: 0, reducerFacts: 0 })));
  variants.push(await measureVariant('P0+checkpoint', async ({ root, planDir }) => {
    const result = await checkpointState(planDir, { cwd: root, apply: true, dryRun: false });
    assert.equal(result.status, 'applied');
    return { toolCalls: 1, recallCalls: 0, reducerFacts: 0 };
  }));
  variants.push(await measureVariant('P0+reducer', async ({ root, planDir }) => {
    await writeFile(path.join(root, 'result.log'), '3 passed\n1 failed\n2 skipped\nFAIL test_two\n');
    const inputPath = path.join(root, 'record.json');
    await writeFile(inputPath, JSON.stringify({
      idempotency_key: 'reducer-fixture',
      execution: {command: 'offline-fixture', collection_method: 'reported'},
      subject: {phase: 'P1'},
      observed_result: 'Failed',
      interpretation: null,
      criteria: {covered: ['offline reducer'], not_covered: ['real agent']},
      freshness: {status: 'unknown', reason: 'fixture', checked_at: null, subject_sha256: null},
      artifacts: [{path: 'result.log', media_type: 'text/plain', encoding: 'utf-8', capture_completeness: 'complete', origin: 'imported'}],
      excerpts: [],
    }));
    const recorded = await recordState(planDir, { cwd: root, inputPath });
    const reduced = reduceArtifact(planDir, { cwd: root, digest: recorded.receipt.artifacts[0].sha256 });
    assert.equal((await verifyReducedQuotes(planDir, { cwd: root, reduction: reduced })).valid, true);
    return { toolCalls: 1, recallCalls: 0, reducerFacts: reduced.facts.length };
  }));
  variants.push(await measureVariant('P0+checkpoint+reducer', async ({ root, planDir }) => {
    const checkpoint = await checkpointState(planDir, { cwd: root, apply: true, dryRun: false });
    assert.equal(checkpoint.status, 'applied');
    await writeFile(path.join(root, 'result.log'), '2 passed\nFAIL test_two\n');
    const inputPath = path.join(root, 'record.json');
    await writeFile(inputPath, JSON.stringify({
      idempotency_key: 'both-fixture',
      execution: {command: 'offline-fixture', collection_method: 'reported'},
      subject: {phase: 'P1'},
      observed_result: 'Failed',
      interpretation: null,
      criteria: {covered: ['offline reducer'], not_covered: ['real agent']},
      freshness: {status: 'unknown', reason: 'fixture', checked_at: null, subject_sha256: null},
      artifacts: [{path: 'result.log', media_type: 'text/plain', encoding: 'utf-8', capture_completeness: 'complete', origin: 'imported'}],
      excerpts: [],
    }));
    const recorded = await recordState(planDir, { cwd: root, inputPath });
    const reduced = reduceArtifact(planDir, { cwd: root, digest: recorded.receipt.artifacts[0].sha256 });
    assert.equal((await verifyReducedQuotes(planDir, { cwd: root, reduction: reduced })).valid, true);
    return { toolCalls: 2, recallCalls: 0, reducerFacts: reduced.facts.length };
  }));

  const base = variants[0];
  assert.ok(variants[1].saved_bytes > 0);
  assert.equal(variants[2].active_document_bytes_after, base.active_document_bytes_after);
  assert.ok(variants[2].reducer_facts > 0);
  assert.ok(variants[3].saved_bytes > 0);
  assert.ok(variants[3].reducer_facts > 0);
  assert.deepEqual(variants.map(({ name, tool_calls, reducer_facts, tokens, cost }) => ({ name, tool_calls, reducer_facts, tokens, cost })), [
    { name: 'P0', tool_calls: 0, reducer_facts: 0, tokens: 'Not Run', cost: 'Not Run' },
    { name: 'P0+checkpoint', tool_calls: 1, reducer_facts: 0, tokens: 'Not Run', cost: 'Not Run' },
    { name: 'P0+reducer', tool_calls: 1, reducer_facts: 4, tokens: 'Not Run', cost: 'Not Run' },
    { name: 'P0+checkpoint+reducer', tool_calls: 2, reducer_facts: 2, tokens: 'Not Run', cost: 'Not Run' },
  ]);
  console.log(JSON.stringify({ schema: 1, planId, variants }));
});
