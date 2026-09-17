import test from 'node:test';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';

const ROOT = path.resolve(new URL('..', import.meta.url).pathname);
const BIN = path.join(ROOT, 'bin/planweft.mjs');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), 'planweft-state-'));
  const project = path.join(root, 'project');
  const plan = path.join(project, '.planning', 'state-plan');
  fs.mkdirSync(plan, {recursive: true});
  fs.writeFileSync(path.join(plan, 'task_plan.md'), '# Task\n');
  fs.writeFileSync(path.join(plan, 'findings.md'), '# Findings\n');
  fs.writeFileSync(path.join(plan, 'progress.md'), '# Progress\n');
  fs.writeFileSync(path.join(project, 'artifact.txt'), 'alpha\nbeta\n');
  fs.writeFileSync(path.join(root, 'outside.txt'), 'outside\n');
  t.after(() => fs.rmSync(root, {recursive: true, force: true}));
  const run = (args, extraEnv = {}) => {
    const result = spawnSync(process.execPath, [BIN, 'state', ...args], {
      cwd: project,
      env: {...process.env, PLAN_ID: 'state-plan', ...extraEnv},
      encoding: 'utf8',
    });
    let json = null;
    try { json = result.stdout ? JSON.parse(result.stdout) : null; } catch {}
    return {...result, json};
  };
  return {root, project, plan, run};
}

function digest(data) { return crypto.createHash('sha256').update(data).digest('hex'); }

function recordInput(f, idempotencyKey, extra = {}) {
  const data = fs.readFileSync(path.join(f.project, 'artifact.txt'));
  const input = {
    idempotency_key: idempotencyKey,
    execution: {command: 'touch SHOULD_NOT_BE_EXECUTED', exit_code: 0},
    subject: {phase: 'S01'},
    observed_result: 'Passed',
    interpretation: 'The command string is recorded as data only.',
    criteria: {freshness: 'separate', covered: ['artifact'], not_covered: ['real agent']},
    artifacts: [{path: 'artifact.txt', media_type: 'text/plain', encoding: 'utf-8', origin: 'fixture'}],
    excerpts: [{artifact_sha256: digest(data), start_byte: 0, end_byte: 6, lines: [1], quote: 'alpha\n'}],
    ...extra,
  };
  const file = path.join(f.project, `${idempotencyKey}.json`);
  fs.writeFileSync(file, JSON.stringify(input));
  return file;
}

test('state init is explicit, isolated from installer state, and disabled mode is read-only', t => {
  const f = fixture(t);
  const unsafePlan = f.run(['init', '--json'], {PLAN_ID: '../escape'});
  assert.equal(unsafePlan.status, 2);
  const disabled = f.run(['init', '--json'], {PLANNING_DISABLED: '1'});
  assert.equal(disabled.status, 0);
  assert.equal(disabled.json.writes, false);
  assert.equal(fs.existsSync(path.join(f.plan, '.planweft-state')), false);
  const initialized = f.run(['init', '--json']);
  assert.equal(initialized.status, 0);
  assert.equal(initialized.json.created, true);
  assert.equal(fs.existsSync(path.join(f.plan, '.planweft-state/store.json')), true);
  assert.equal(fs.existsSync(path.join(f.plan, '.planweft')), false);
  const doctor = f.run(['doctor']);
  assert.equal(doctor.status, 0);
  assert.equal(doctor.json.status, 'ready');
  assert.equal(doctor.json.writes, false);
});

test('record stores streamed content, verifies excerpts, recalls bytes and remains idempotent', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const input = recordInput(f, 's02-record');
  const recorded = f.run(['record', '--input', input, '--json']);
  assert.equal(recorded.status, 0, recorded.stderr);
  assert.equal(recorded.json.idempotent, false);
  const receiptId = recorded.json.receipt_id;
  const artifactSha = digest(fs.readFileSync(path.join(f.project, 'artifact.txt')));
  const verified = f.run(['verify', '--receipt', receiptId]);
  assert.equal(verified.status, 0, `${verified.stderr}\n${verified.stdout}`);
  assert.equal(verified.json.valid, true);
  assert.equal(verified.json.observed_result, 'Passed');
  const recalled = f.run(['recall', '--artifact', artifactSha, '--start-byte', '0', '--length', '6', '--json']);
  assert.equal(recalled.status, 0);
  assert.equal(Buffer.from(recalled.json.data, 'base64').toString(), 'alpha\n');
  const repeated = f.run(['record', '--input', input, '--json']);
  assert.equal(repeated.status, 0);
  assert.equal(repeated.json.idempotent, true);
  assert.equal(repeated.json.receipt_id, receiptId);
  assert.equal(fs.existsSync(path.join(f.project, 'SHOULD_NOT_BE_EXECUTED')), false);
});

test('integrity, idempotency, symlink and project-boundary failures keep their exit semantics', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const input = recordInput(f, 's03-integrity');
  const recorded = f.run(['record', '--input', input, '--json']);
  const receiptId = recorded.json.receipt_id;
  const artifactSha = digest(fs.readFileSync(path.join(f.project, 'artifact.txt')));
  const object = path.join(f.plan, '.planweft-state', 'artifacts', 'sha256', artifactSha.slice(0, 2), artifactSha);
  fs.writeFileSync(object, 'tampered');
  const failed = f.run(['verify', '--receipt', receiptId, '--json']);
  assert.equal(failed.status, 4);
  assert.equal(failed.json.valid, false);
  fs.writeFileSync(object, 'alpha\nbeta\n');
  const conflicting = recordInput(f, 's03-integrity', {observed_result: 'Failed'});
  const conflict = f.run(['record', '--input', conflicting, '--json']);
  assert.equal(conflict.status, 3);
  const transactionsBeforeLock = fs.readdirSync(path.join(f.plan, '.planweft-state', 'transactions'));
  fs.mkdirSync(path.join(f.plan, '.planweft-state', '.write-lock'));
  const lockedInput = recordInput(f, 's03-lock');
  const locked = f.run(['record', '--input', lockedInput, '--json']);
  assert.equal(locked.status, 3);
  fs.rmSync(path.join(f.plan, '.planweft-state', '.write-lock'), {recursive: true});
  assert.deepEqual(fs.readdirSync(path.join(f.plan, '.planweft-state', 'transactions')), transactionsBeforeLock);
  fs.writeFileSync(path.join(f.project, 'outside-link'), 'placeholder');
  fs.rmSync(path.join(f.project, 'outside-link'));
  fs.symlinkSync(path.join(f.root, 'outside.txt'), path.join(f.project, 'outside-link'));
  const linkInput = recordInput(f, 's03-symlink', {artifacts: [{path: 'outside-link', origin: 'fixture'}], excerpts: []});
  const linkFailure = f.run(['record', '--input', linkInput, '--json']);
  assert.equal(linkFailure.status, 2);
  const escapeInput = recordInput(f, 's03-escape', {artifacts: [{path: '../outside.txt', origin: 'fixture'}], excerpts: []});
  const escapeFailure = f.run(['record', '--input', escapeInput, '--json']);
  assert.equal(escapeFailure.status, 2);
  const inputEscape = path.join(f.root, 'outside-input.json');
  fs.writeFileSync(inputEscape, '{}');
  const inputFailure = f.run(['record', '--input', '../outside-input.json', '--json']);
  assert.equal(inputFailure.status, 2);
});

test('markdown writes use a journal and recover without overwriting unrelated edits', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const target = path.join(f.plan, 'progress.md');
  const before = fs.readFileSync(target);
  const expected = digest(before);
  const input = recordInput(f, 's13-journal', {
    markdown: {path: 'progress.md', expected_sha256: expected, entry: '- recorded evidence'},
  });
  const recorded = f.run(['record', '--input', input, '--json']);
  assert.equal(recorded.status, 0, recorded.stderr);
  const transaction = recorded.json.transaction_id;
  const journalFile = path.join(f.plan, '.planweft-state', 'transactions', transaction, 'journal.json');
  const journal = JSON.parse(fs.readFileSync(journalFile));
  journal.status = 'receipt_published';
  fs.writeFileSync(journalFile, JSON.stringify(journal, null, 2) + '\n');
  const doctor = f.run(['doctor']);
  assert.equal(doctor.status, 0);
  assert.equal(doctor.json.incomplete_transactions.length, 1);
  fs.writeFileSync(target, before);
  const dryRun = f.run(['recover', '--transaction', transaction, '--dry-run']);
  assert.equal(dryRun.status, 0);
  assert.equal(dryRun.json.action, 'apply_after');
  assert.equal(dryRun.json.writes, false);
  const applied = f.run(['recover', '--transaction', transaction, '--apply', '--json']);
  assert.equal(applied.status, 0, applied.stderr);
  assert.equal(applied.json.writes, true);
  assert.equal(fs.readFileSync(target, 'utf8').includes('- recorded evidence'), true);
  const committed = JSON.parse(fs.readFileSync(journalFile));
  assert.equal(committed.status, 'committed');
  assert.equal(journal.target.after_sha256, digest(fs.readFileSync(target)));
});
