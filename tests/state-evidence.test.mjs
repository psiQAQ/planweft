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
    execution: {command: 'touch SHOULD_NOT_BE_EXECUTED', exit_code: 0, collection_method: 'reported'},
    subject: {phase: 'S01'},
    observed_result: 'Passed',
    interpretation: 'The command string is recorded as data only.',
    criteria: {covered: ['artifact'], not_covered: ['real agent']},
    freshness: {status: 'unknown', reason: 'fixture does not assess source freshness', checked_at: null, subject_sha256: null},
    artifacts: [{path: 'artifact.txt', media_type: 'text/plain', encoding: 'utf-8', capture_completeness: 'complete', origin: 'imported'}],
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
  assert.equal(verified.json.structure_check, true);
  assert.equal(verified.json.source_check, true);
  assert.equal(verified.json.execution_evidence, 'reported');
  assert.equal(verified.json.criteria_check, 'declared');
  assert.equal(verified.json.freshness_check, 'unknown');
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
  const recalledTampered = f.run(['recall', '--artifact', artifactSha, '--start-byte', '0', '--length', '8', '--json']);
  assert.equal(recalledTampered.status, 4);
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
  const linkInput = recordInput(f, 's03-symlink', {artifacts: [{path: 'outside-link', media_type: 'text/plain', encoding: 'utf-8', capture_completeness: 'complete', origin: 'imported'}], excerpts: []});
  const linkFailure = f.run(['record', '--input', linkInput, '--json']);
  assert.equal(linkFailure.status, 2);
  const escapeInput = recordInput(f, 's03-escape', {artifacts: [{path: '../outside.txt', media_type: 'text/plain', encoding: 'utf-8', capture_completeness: 'complete', origin: 'imported'}], excerpts: []});
  const escapeFailure = f.run(['record', '--input', escapeInput, '--json']);
  assert.equal(escapeFailure.status, 2);
  const inputEscape = path.join(f.root, 'outside-input.json');
  fs.writeFileSync(inputEscape, '{}');
  const inputFailure = f.run(['record', '--input', '../outside-input.json', '--json']);
  assert.equal(inputFailure.status, 2);
});

test('concurrent workers are excluded by an active owner lock', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const lock = path.join(f.plan, '.planweft-state', '.write-lock');
  fs.mkdirSync(lock);
  fs.writeFileSync(path.join(lock, 'owner.json'), JSON.stringify({operation_id: 'active-worker', pid: process.pid, acquired_at: new Date().toISOString()}));
  const input = recordInput(f, 'worker-conflict');
  const result = f.run(['record', '--input', input, '--json']);
  assert.equal(result.status, 3);
  fs.rmSync(lock, {recursive: true});
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

test('record rejects unsupported provenance and validates excerpts before publishing', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const invalidCapture = recordInput(f, 'schema-invalid-capture', {
    artifacts: [{path: 'artifact.txt', media_type: 'text/plain', encoding: 'utf-8', capture_completeness: 'complete-ish', origin: 'imported'}],
    excerpts: [],
  });
  assert.equal(f.run(['record', '--input', invalidCapture, '--json']).status, 2);
  const invalidExecution = recordInput(f, 'schema-invalid-execution', {execution: {command: 'echo data', exit_code: 0}, excerpts: []});
  assert.equal(f.run(['record', '--input', invalidExecution, '--json']).status, 2);
  const wrongQuote = recordInput(f, 'quote-mismatch', {excerpts: [{artifact_sha256: digest(fs.readFileSync(path.join(f.project, 'artifact.txt'))), start_byte: 0, end_byte: 6, lines: [1], quote: 'wrong\n'}]});
  assert.equal(f.run(['record', '--input', wrongQuote, '--json']).status, 2);
});

test('plan binding rejects nested and outside candidates', t => {
  const f = fixture(t);
  const nested = path.join(f.project, '.planning', 'group', 'nested-plan');
  fs.mkdirSync(nested, {recursive: true});
  for (const file of ['task_plan.md', 'findings.md', 'progress.md']) fs.writeFileSync(path.join(nested, file), '# nested\n');
  assert.equal(f.run(['init', '--plan-dir', '.planning/group/nested-plan', '--json']).status, 2);
  const outsideProject = path.join(f.root, 'outside-project');
  const outsidePlan = path.join(outsideProject, '.planning', 'outside');
  fs.mkdirSync(outsidePlan, {recursive: true});
  for (const file of ['task_plan.md', 'findings.md', 'progress.md']) fs.writeFileSync(path.join(outsidePlan, file), '# outside\n');
  assert.equal(f.run(['init', '--plan-dir', '../outside-project/.planning/outside', '--json']).status, 2);
});

test('doctor reports integrity, stale lock, budget and damaged schema without writing', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const input = recordInput(f, 'doctor-integrity');
  const recorded = f.run(['record', '--input', input, '--json']);
  assert.equal(recorded.status, 0);
  const receiptFile = path.join(f.plan, '.planweft-state', 'receipts', `${recorded.json.receipt_id}.json`);
  const artifactSha = digest(fs.readFileSync(path.join(f.project, 'artifact.txt')));
  const object = path.join(f.plan, '.planweft-state', 'artifacts', 'sha256', artifactSha.slice(0, 2), artifactSha);
  fs.writeFileSync(object, 'damaged');
  fs.mkdirSync(path.join(f.plan, '.planweft-state', '.write-lock'));
  const doctor = f.run(['doctor', '--json']);
  assert.equal(doctor.status, 4);
  assert.equal(doctor.json.status, 'degraded');
  assert.equal(doctor.json.damaged_references.length >= 1, true);
  assert.equal(doctor.json.write_lock.stale, true);
  assert.equal(fs.existsSync(receiptFile), true);
  fs.rmSync(path.join(f.plan, '.planweft-state', '.write-lock'), {recursive: true});
  const storeFile = path.join(f.plan, '.planweft-state', 'store.json');
  const originalStore = fs.readFileSync(storeFile);
  fs.writeFileSync(storeFile, JSON.stringify({...JSON.parse(originalStore), schema_version: 99}));
  const damaged = f.run(['doctor', '--json']);
  assert.equal(damaged.status, 4);
  assert.equal(damaged.json.status, 'damaged');
  fs.writeFileSync(storeFile, originalStore);

  const budgetFixture = fixture(t);
  assert.equal(budgetFixture.run(['init', '--storage-budget-bytes', '1']).status, 0);
  const budgetInput = recordInput(budgetFixture, 'budget-limit');
  assert.equal(budgetFixture.run(['record', '--input', budgetInput, '--json']).status, 5);
});

test('CRLF, binary, empty and large artifacts round-trip byte-for-byte', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const files = {
    'crlf.txt': Buffer.from('one\r\ntwo\r\n', 'utf8'),
    'binary.bin': Buffer.from([0, 1, 2, 10, 13, 255]),
    'empty.bin': Buffer.alloc(0),
    'large.bin': Buffer.alloc(256 * 1024, 0x5a),
  };
  const artifacts = [];
  for (const [name, data] of Object.entries(files)) {
    fs.writeFileSync(path.join(f.project, name), data);
    artifacts.push({path: name, media_type: name.endsWith('.txt') ? 'text/plain' : 'application/octet-stream', encoding: name.endsWith('.txt') ? 'utf-8' : null, capture_completeness: 'complete', origin: 'imported'});
  }
  const input = recordInput(f, 'formats', {artifacts, excerpts: []});
  const recorded = f.run(['record', '--input', input, '--json']);
  assert.equal(recorded.status, 0, recorded.stderr);
  for (const [name, data] of Object.entries(files)) {
    const sha = digest(data);
    const recalled = f.run(['recall', '--artifact', sha, '--start-byte', '0', '--length', String(data.length), '--json']);
    assert.equal(recalled.status, 0, `${name}: ${recalled.stderr}`);
    assert.deepEqual(Buffer.from(recalled.json.data, 'base64'), data, name);
  }
});

test('recovery rejects a tampered payload and uses fixed interruption seeds', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const target = path.join(f.plan, 'progress.md');
  const before = fs.readFileSync(target);
  const expected = digest(before);
  const first = recordInput(f, 'tampered-recovery', {markdown: {path: 'progress.md', expected_sha256: expected, entry: '- recovery'}});
  const recorded = f.run(['record', '--input', first, '--json']);
  assert.equal(recorded.status, 0);
  const transactionDir = path.join(f.plan, '.planweft-state', 'transactions', recorded.json.transaction_id);
  const journalFile = path.join(transactionDir, 'journal.json');
  const journal = JSON.parse(fs.readFileSync(journalFile));
  journal.status = 'receipt_published';
  fs.writeFileSync(journalFile, JSON.stringify(journal));
  fs.writeFileSync(target, before);
  const afterFile = path.join(transactionDir, 'after.bin');
  const afterPayload = fs.readFileSync(afterFile);
  fs.writeFileSync(afterFile, 'tampered payload');
  assert.equal(f.run(['recover', '--transaction', recorded.json.transaction_id, '--apply', '--json']).status, 4);
  fs.writeFileSync(afterFile, afterPayload);
  const lock = path.join(f.plan, '.planweft-state', '.write-lock');
  fs.mkdirSync(lock);
  assert.equal(f.run(['recover', '--transaction', recorded.json.transaction_id, '--apply', '--json']).status, 3);
  fs.rmSync(lock, {recursive: true});

  const seeds = [11, 23, 37, 41, 59, 67, 73, 89, 101, 127];
  for (const [index, seed] of seeds.entries()) {
    const current = fs.readFileSync(target);
    const input = recordInput(f, `seed-${seed}`, {
      markdown: {path: 'progress.md', expected_sha256: digest(current), entry: `- seed-${seed}`},
    });
    const result = f.run(['record', '--input', input, '--json']);
    assert.equal(result.status, 0, `seed ${seed}: ${result.stderr}`);
    const dir = path.join(f.plan, '.planweft-state', 'transactions', result.json.transaction_id);
    const file = path.join(dir, 'journal.json');
    const state = JSON.parse(fs.readFileSync(file));
    state.status = 'receipt_published';
    fs.writeFileSync(file, JSON.stringify(state));
    if (index % 2 === 0) fs.writeFileSync(target, current);
    const recovered = f.run(['recover', '--transaction', result.json.transaction_id, '--apply', '--json']);
    assert.equal(recovered.status, 0, `seed ${seed}: ${recovered.stderr}`);
    assert.equal(JSON.parse(fs.readFileSync(file)).status, 'committed');
  }
});

test('a moved project retains its store and missing local evidence stays explicit', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const input = recordInput(f, 'move-and-local-only');
  const recorded = f.run(['record', '--input', input, '--json']);
  assert.equal(recorded.status, 0);
  const storeFile = path.join(f.plan, '.planweft-state', 'store.json');
  const storeBefore = fs.readFileSync(storeFile);
  const moved = path.join(f.root, 'moved-project');
  fs.renameSync(f.project, moved);
  const movedPlan = path.join(moved, '.planning', 'state-plan');
  const movedVerify = spawnSync(process.execPath, [BIN, 'state', 'verify', '--receipt', recorded.json.receipt_id, '--json'], {
    cwd: moved,
    env: {...process.env, PLAN_ID: 'state-plan'},
    encoding: 'utf8',
  });
  assert.equal(movedVerify.status, 0, movedVerify.stderr);
  assert.deepEqual(fs.readFileSync(path.join(movedPlan, '.planweft-state', 'store.json')), storeBefore);
  const artifactSha = digest(fs.readFileSync(path.join(moved, 'artifact.txt')));
  fs.rmSync(path.join(movedPlan, '.planweft-state', 'artifacts', 'sha256', artifactSha.slice(0, 2), artifactSha));
  const doctor = spawnSync(process.execPath, [BIN, 'state', 'doctor', '--json'], {
    cwd: moved,
    env: {...process.env, PLAN_ID: 'state-plan'},
    encoding: 'utf8',
  });
  assert.equal(doctor.status, 4);
  const report = JSON.parse(doctor.stdout);
  assert.equal(report.local_only.status, 'local-only');
  assert.equal(report.missing_references.length, 1);
});

test('package replacement simulation does not touch task-side state', t => {
  const f = fixture(t);
  assert.equal(f.run(['init']).status, 0);
  const storeFile = path.join(f.plan, '.planweft-state', 'store.json');
  const before = fs.readFileSync(storeFile);
  const install = path.join(f.root, 'install');
  fs.cpSync(path.join(ROOT, 'dist', 'codex', 'planweft'), install, {recursive: true});
  fs.rmSync(install, {recursive: true});
  fs.cpSync(path.join(ROOT, 'dist', 'codex', 'planweft'), install, {recursive: true});
  assert.deepEqual(fs.readFileSync(storeFile), before);
  assert.equal(fs.existsSync(path.join(install, 'state', 'core.mjs')), true);
});
