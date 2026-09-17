import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pipeline } from 'node:stream/promises';
import { Transform } from 'node:stream';

export const EXIT_CODES = Object.freeze({
  OK: 0,
  INPUT: 2,
  CONFLICT: 3,
  EVIDENCE: 4,
  IO: 5,
});

const STORE_SCHEMA = 1;
const RECEIPT_SCHEMA = 1;
const STORE_NAME = '.planweft-state';
const PLAN_FILES = ['task_plan.md', 'findings.md', 'progress.md'];
const RECORD_FILES = new Set(PLAN_FILES);
const MAX_RECALL_BYTES = 8 * 1024 * 1024;

export class StateError extends Error {
  constructor(message, code = EXIT_CODES.IO, details = undefined) {
    super(message);
    this.name = 'StateError';
    this.code = code;
    this.details = details;
  }
}

const fail = (message, code, details) => { throw new StateError(message, code, details); };
const sha256 = value => crypto.createHash('sha256').update(value).digest('hex');
const now = () => new Date().toISOString();
const posix = value => value.split(path.sep).join('/');
const isHash = value => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);

function readJSON(file, label) {
  let raw;
  try { raw = fs.readFileSync(file, 'utf8'); } catch (error) {
    if (error.code === 'ENOENT') fail(`${label} is missing`, EXIT_CODES.EVIDENCE);
    fail(`Cannot read ${label}: ${error.message}`, EXIT_CODES.IO);
  }
  try { return JSON.parse(raw); } catch (error) {
    fail(`${label} is invalid JSON: ${error.message}`, EXIT_CODES.EVIDENCE);
  }
}

function writeJSON(file, value, mode = 0o600) {
  fs.mkdirSync(path.dirname(file), {recursive: true, mode: 0o700});
  const temporary = `${file}.${process.pid}.${crypto.randomBytes(6).toString('hex')}.tmp`;
  try {
    fs.writeFileSync(temporary, JSON.stringify(value, null, 2) + '\n', {flag: 'wx', mode});
    fs.renameSync(temporary, file);
  } catch (error) {
    try { fs.rmSync(temporary, {force: true}); } catch {}
    fail(`Cannot write ${file}: ${error.message}`, EXIT_CODES.IO);
  }
}

function assertKeys(value, allowed, label) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) fail(`${label} must be an object`, EXIT_CODES.INPUT);
  const unknown = Object.keys(value).filter(key => !allowed.has(key));
  if (unknown.length) fail(`${label} contains unknown fields: ${unknown.join(', ')}`, EXIT_CODES.INPUT);
}

function realDirectory(directory, label) {
  let resolved;
  try { resolved = fs.realpathSync(directory); } catch (error) {
    fail(`${label} is not an existing directory: ${error.message}`, EXIT_CODES.INPUT);
  }
  if (!fs.statSync(resolved).isDirectory()) fail(`${label} is not a directory`, EXIT_CODES.INPUT);
  return resolved;
}

function planInfo(planDir, cwd = process.cwd()) {
  const requested = path.resolve(cwd, planDir || '.');
  const resolved = realDirectory(requested, 'plan directory');
  for (const file of PLAN_FILES) {
    const candidate = path.join(resolved, file);
    if (!fs.existsSync(candidate) || !fs.statSync(candidate).isFile()) {
      fail(`selected plan is missing ${file}`, EXIT_CODES.INPUT);
    }
  }
  const parent = path.dirname(resolved);
  if (path.basename(parent) === '.planning' && path.dirname(resolved) !== parent) {
    fail('selected plan must be a direct child of .planning', EXIT_CODES.INPUT);
  }
  const projectRoot = path.basename(parent) === '.planning' ? path.dirname(parent) : resolved;
  const project = realDirectory(projectRoot, 'authorized project');
  const planId = path.basename(resolved);
  return {planDir: resolved, projectRoot: project, planId: planId === path.basename(project) ? 'legacy-root' : planId};
}

function inside(root, candidate, label) {
  const resolved = realDirectory(root, 'authorized project');
  let target;
  try { target = fs.realpathSync(candidate); } catch (error) {
    fail(`${label} does not exist: ${error.message}`, EXIT_CODES.INPUT);
  }
  const relative = path.relative(resolved, target);
  if (!relative || relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    fail(`${label} escapes the authorized project`, EXIT_CODES.INPUT);
  }
  return {absolute: target, relative: posix(relative)};
}

function loadStore(info, {required = true} = {}) {
  const storeDir = path.join(info.planDir, STORE_NAME);
  const storeFile = path.join(storeDir, 'store.json');
  if (!fs.existsSync(storeFile)) {
    if (required) fail('state store is not initialized; run state init explicitly', EXIT_CODES.EVIDENCE);
    return {storeDir, store: null};
  }
  const store = readJSON(storeFile, 'store.json');
  assertKeys(store, new Set(['schema_version', 'store_id', 'plan_id', 'created_at', 'capabilities', 'storage_budget_bytes']), 'store.json');
  if (store.schema_version !== STORE_SCHEMA || typeof store.store_id !== 'string' || !store.store_id ||
      typeof store.plan_id !== 'string' || store.plan_id !== info.planId) {
    fail('state store binding or schema is invalid', EXIT_CODES.EVIDENCE);
  }
  return {storeDir, store};
}

function ensureStoreDirectories(storeDir) {
  for (const directory of ['artifacts/sha256', 'receipts', 'transactions']) {
    fs.mkdirSync(path.join(storeDir, directory), {recursive: true, mode: 0o700});
  }
}

export function initStore(planDir, {cwd = process.cwd(), storageBudgetBytes = null} = {}) {
  const info = planInfo(planDir, cwd);
  const target = path.join(info.planDir, STORE_NAME);
  if (fs.existsSync(target)) {
    const loaded = loadStore(info);
    ensureStoreDirectories(loaded.storeDir);
    return {created: false, ...info, ...loaded};
  }
  fs.mkdirSync(target, {mode: 0o700});
  ensureStoreDirectories(target);
  fs.writeFileSync(path.join(target, '.gitignore'), '*\n!.gitignore\n', {mode: 0o600, flag: 'wx'});
  const store = {
    schema_version: STORE_SCHEMA,
    store_id: crypto.randomUUID(),
    plan_id: info.planId,
    created_at: now(),
    capabilities: {artifacts: true, receipts: true, records: true, checkpoints: false, remote_reducer: false},
    storage_budget_bytes: storageBudgetBytes,
  };
  writeJSON(path.join(target, 'store.json'), store);
  return {created: true, ...info, storeDir: target, store};
}

async function archiveFile(source, destination) {
  const hash = crypto.createHash('sha256');
  let bytes = 0;
  const meter = new Transform({transform(chunk, encoding, callback) {
    hash.update(chunk);
    bytes += chunk.length;
    callback(null, chunk);
  }});
  fs.mkdirSync(path.dirname(destination), {recursive: true, mode: 0o700});
  await pipeline(fs.createReadStream(source), meter, fs.createWriteStream(destination, {flags: 'wx', mode: 0o600}));
  return {sha256: hash.digest('hex'), bytes};
}

function artifactDestination(storeDir, digest) {
  return path.join(storeDir, 'artifacts', 'sha256', digest.slice(0, 2), digest);
}

async function archiveArtifact(info, loaded, entry, temporaryRoot) {
  assertKeys(entry, new Set(['path', 'media_type', 'encoding', 'capture_completeness', 'origin']), 'artifact input');
  if (typeof entry.path !== 'string' || !entry.path) fail('artifact path is required', EXIT_CODES.INPUT);
  const sourceCandidate = path.resolve(info.projectRoot, entry.path);
  let source;
  try {
    const stat = fs.lstatSync(sourceCandidate);
    if (stat.isSymbolicLink() || !stat.isFile()) fail(`artifact source is not a regular file: ${entry.path}`, EXIT_CODES.INPUT);
    source = inside(info.projectRoot, sourceCandidate, 'artifact source');
  } catch (error) {
    if (error instanceof StateError) throw error;
    fail(`artifact source cannot be read: ${error.message}`, EXIT_CODES.INPUT);
  }
  const staged = path.join(temporaryRoot, crypto.randomUUID() + '.artifact');
  const measured = await archiveFile(source.absolute, staged);
  const destination = artifactDestination(loaded.storeDir, measured.sha256);
  fs.mkdirSync(path.dirname(destination), {recursive: true, mode: 0o700});
  if (fs.existsSync(destination)) {
    const existing = await hashFile(destination);
    if (existing.sha256 !== measured.sha256 || existing.bytes !== measured.bytes) {
      fail(`artifact object is corrupted for ${measured.sha256}`, EXIT_CODES.EVIDENCE);
    }
    fs.rmSync(staged, {force: true});
  } else {
    fs.renameSync(staged, destination);
  }
  return {
    path: posix(path.relative(info.projectRoot, source.absolute)),
    sha256: measured.sha256,
    bytes: measured.bytes,
    media_type: entry.media_type || 'application/octet-stream',
    encoding: entry.encoding ?? null,
    capture_completeness: entry.capture_completeness || 'complete',
    origin: entry.origin || 'imported',
  };
}

async function hashFile(file) {
  const hash = crypto.createHash('sha256');
  let bytes = 0;
  for await (const chunk of fs.createReadStream(file)) { hash.update(chunk); bytes += chunk.length; }
  return {sha256: hash.digest('hex'), bytes};
}

function readInput(info, inputPath, cwd) {
  if (typeof inputPath !== 'string' || !inputPath) fail('--input is required', EXIT_CODES.INPUT);
  const candidate = path.resolve(cwd, inputPath);
  const source = inside(info.projectRoot, candidate, 'record input');
  return {path: source.absolute, raw: fs.readFileSync(source.absolute)};
}

function receiptFiles(storeDir) {
  const directory = path.join(storeDir, 'receipts');
  if (!fs.existsSync(directory)) return [];
  return fs.readdirSync(directory).filter(name => name.endsWith('.json')).sort().map(name => path.join(directory, name));
}

function findIdempotent(storeDir, key) {
  for (const file of receiptFiles(storeDir)) {
    const receipt = readJSON(file, `receipt ${path.basename(file)}`);
    if (receipt.idempotency_key === key) return receipt;
  }
  return null;
}

function validateRecordInput(input) {
  assertKeys(input, new Set(['idempotency_key', 'execution', 'subject', 'observed_result', 'interpretation', 'criteria', 'artifacts', 'excerpts', 'markdown']), 'record input');
  if (typeof input.idempotency_key !== 'string' || !input.idempotency_key) fail('idempotency_key is required', EXIT_CODES.INPUT);
  if (input.observed_result !== undefined && !['Passed', 'Failed', 'Inconclusive', 'Not Run'].includes(input.observed_result)) {
    fail('observed_result is invalid', EXIT_CODES.INPUT);
  }
  if (!Array.isArray(input.artifacts) || input.artifacts.length === 0) fail('record input must contain at least one artifact', EXIT_CODES.INPUT);
  if (input.excerpts !== undefined && !Array.isArray(input.excerpts)) fail('excerpts must be an array', EXIT_CODES.INPUT);
  if (input.markdown !== undefined) {
    assertKeys(input.markdown, new Set(['path', 'entry', 'expected_sha256']), 'markdown input');
    if (typeof input.markdown.path !== 'string' || !RECORD_FILES.has(path.basename(input.markdown.path)) ||
        path.dirname(input.markdown.path) !== '.') fail('markdown path must be one selected plan file', EXIT_CODES.INPUT);
    if (typeof input.markdown.entry !== 'string' || !input.markdown.entry) fail('markdown entry is required', EXIT_CODES.INPUT);
    if (!isHash(input.markdown.expected_sha256)) fail('markdown expected_sha256 is required', EXIT_CODES.INPUT);
  }
}

function validateExcerpt(excerpt, artifacts) {
  assertKeys(excerpt, new Set(['artifact_sha256', 'start_byte', 'end_byte', 'lines', 'quote']), 'excerpt');
  if (!isHash(excerpt.artifact_sha256) || !Number.isInteger(excerpt.start_byte) || !Number.isInteger(excerpt.end_byte) ||
      excerpt.start_byte < 0 || excerpt.end_byte < excerpt.start_byte || typeof excerpt.quote !== 'string') {
    fail('excerpt range or quote is invalid', EXIT_CODES.INPUT);
  }
  if (!artifacts.some(artifact => artifact.sha256 === excerpt.artifact_sha256)) fail('excerpt references an unknown artifact', EXIT_CODES.INPUT);
}

function receiptPath(storeDir, receiptId) { return path.join(storeDir, 'receipts', `${receiptId}.json`); }

export async function recordState(planDir, {cwd = process.cwd(), inputPath} = {}) {
  const info = planInfo(planDir, cwd);
  const loaded = loadStore(info);
  const input = readInput(info, inputPath, cwd);
  let request;
  try { request = JSON.parse(input.raw.toString('utf8')); } catch (error) { fail(`record input is invalid JSON: ${error.message}`, EXIT_CODES.INPUT); }
  validateRecordInput(request);
  const inputDigest = sha256(input.raw);
  const existing = findIdempotent(loaded.storeDir, request.idempotency_key);
  if (existing) {
    if (existing.input_sha256 !== inputDigest) fail('idempotency key conflicts with an existing receipt', EXIT_CODES.CONFLICT, {receipt_id: existing.receipt_id});
    return {idempotent: true, receipt_id: existing.receipt_id, receipt: existing};
  }
  const transactionId = crypto.randomUUID();
  const transactionDir = path.join(loaded.storeDir, 'transactions', transactionId);
  const temporaryRoot = path.join(transactionDir, 'staging');
  fs.mkdirSync(temporaryRoot, {recursive: true, mode: 0o700});
  const lock = path.join(loaded.storeDir, '.write-lock');
  let journalPublished = false;
  let receiptFile = null;
  try {
    fs.mkdirSync(lock);
  } catch (error) {
    fs.rmSync(transactionDir, {recursive: true, force: true});
    if (error.code === 'EEXIST') fail('another state write owns the store lock', EXIT_CODES.CONFLICT);
    fail(`cannot acquire state lock: ${error.message}`, EXIT_CODES.IO);
  }
  try {
    const artifacts = [];
    for (const entry of request.artifacts) artifacts.push(await archiveArtifact(info, loaded, entry, temporaryRoot));
    const excerpts = request.excerpts || [];
    for (const excerpt of excerpts) validateExcerpt(excerpt, artifacts);
    let markdownTarget = null;
    let markdownAfter = null;
    let markdownBeforeSha = null;
    if (request.markdown) {
      markdownTarget = path.join(info.planDir, request.markdown.path);
      const before = fs.readFileSync(markdownTarget);
      markdownBeforeSha = sha256(before);
      if (markdownBeforeSha !== request.markdown.expected_sha256) {
        fail('markdown target changed before write', EXIT_CODES.CONFLICT, {path: request.markdown.path});
      }
      const entry = request.markdown.entry.endsWith('\n') ? request.markdown.entry : `${request.markdown.entry}\n`;
      markdownAfter = Buffer.concat([before, Buffer.from(`${before.length && !before.toString().endsWith('\n') ? '\n' : ''}${entry}`)]);
      fs.writeFileSync(path.join(transactionDir, 'after.bin'), markdownAfter, {mode: 0o600, flag: 'wx'});
    }
    const receiptId = sha256(`${loaded.store.store_id}\n${request.idempotency_key}\n${inputDigest}`).slice(0, 32);
    const receipt = {
      schema_version: RECEIPT_SCHEMA,
      receipt_id: receiptId,
      store_id: loaded.store.store_id,
      plan_id: info.planId,
      recorded_at: now(),
      producer: {kind: 'planweft-state-helper', version: '0.6.0-dev'},
      operation_id: transactionId,
      idempotency_key: request.idempotency_key,
      input_sha256: inputDigest,
      execution: request.execution ?? null,
      subject: request.subject ?? null,
      artifacts,
      excerpts,
      observed_result: request.observed_result || 'Inconclusive',
      interpretation: request.interpretation ?? null,
      criteria: request.criteria ?? {covered: [], not_covered: []},
    };
    receiptFile = receiptPath(loaded.storeDir, receiptId);
    if (fs.existsSync(receiptFile)) fail('receipt id collision with different content', EXIT_CODES.CONFLICT);
    writeJSON(receiptFile, receipt);
    const journal = {
      schema_version: 1,
      transaction_id: transactionId,
      status: 'receipt_published',
      receipt_id: receiptId,
      plan_id: info.planId,
      target: null,
    };
    if (request.markdown) {
      journal.target = {path: request.markdown.path, before_sha256: markdownBeforeSha, after_sha256: sha256(markdownAfter), after_file: 'after.bin'};
      writeJSON(path.join(transactionDir, 'journal.json'), journal);
      journalPublished = true;
      const currentBeforeWrite = sha256(fs.readFileSync(markdownTarget));
      if (currentBeforeWrite !== markdownBeforeSha) {
        fail('markdown target changed after journal publication', EXIT_CODES.CONFLICT, {path: request.markdown.path});
      }
      const temporary = `${markdownTarget}.${process.pid}.${crypto.randomBytes(6).toString('hex')}.tmp`;
      fs.writeFileSync(temporary, markdownAfter, {mode: fs.statSync(markdownTarget).mode & 0o777, flag: 'wx'});
      fs.renameSync(temporary, markdownTarget);
      journal.status = 'committed';
    } else {
      writeJSON(path.join(transactionDir, 'journal.json'), journal);
      journalPublished = true;
      journal.status = 'committed';
    }
    writeJSON(path.join(transactionDir, 'journal.json'), journal);
    return {idempotent: false, receipt_id: receiptId, transaction_id: transactionId, receipt};
  } finally {
    fs.rmSync(lock, {recursive: true, force: true});
    fs.rmSync(temporaryRoot, {recursive: true, force: true});
    if (!journalPublished) {
      fs.rmSync(transactionDir, {recursive: true, force: true});
      if (receiptFile) fs.rmSync(receiptFile, {force: true});
    }
  }
}

async function validateReceipt(info, loaded, receipt) {
  const issues = [];
  try {
    assertKeys(receipt, new Set(['schema_version', 'receipt_id', 'store_id', 'plan_id', 'recorded_at', 'producer', 'operation_id', 'idempotency_key', 'input_sha256', 'execution', 'subject', 'artifacts', 'excerpts', 'observed_result', 'interpretation', 'criteria', 'supersedes']), 'receipt');
    if (receipt.schema_version !== RECEIPT_SCHEMA) issues.push('unsupported schema_version');
    if (typeof receipt.receipt_id !== 'string' || !/^[0-9a-f]{32}$/.test(receipt.receipt_id)) issues.push('receipt id invalid');
    if (receipt.store_id !== loaded.store.store_id || receipt.plan_id !== info.planId) issues.push('store or plan binding mismatch');
    if (!Array.isArray(receipt.artifacts) || !receipt.artifacts.length) issues.push('artifacts missing');
    for (const artifact of receipt.artifacts || []) {
      if (!isHash(artifact.sha256) || !Number.isInteger(artifact.bytes)) { issues.push('artifact metadata invalid'); continue; }
      const file = artifactDestination(loaded.storeDir, artifact.sha256);
      if (!fs.existsSync(file)) { issues.push(`artifact missing: ${artifact.sha256}`); continue; }
      const measured = await hashFile(file);
      if (measured.sha256 !== artifact.sha256 || measured.bytes !== artifact.bytes) issues.push(`artifact hash mismatch: ${artifact.sha256}`);
    }
    for (const excerpt of receipt.excerpts || []) {
      const artifact = (receipt.artifacts || []).find(item => item.sha256 === excerpt.artifact_sha256);
      if (!artifact || !Number.isInteger(excerpt.start_byte) || !Number.isInteger(excerpt.end_byte) || excerpt.end_byte < excerpt.start_byte) {
        issues.push('excerpt metadata invalid'); continue;
      }
      const file = artifactDestination(loaded.storeDir, artifact.sha256);
      if (!fs.existsSync(file)) continue;
      const length = excerpt.end_byte - excerpt.start_byte;
      if (length > MAX_RECALL_BYTES) { issues.push('excerpt exceeds recall budget'); continue; }
      const handle = await fs.promises.open(file, 'r');
      try {
        const buffer = Buffer.alloc(length);
        const read = await handle.read(buffer, 0, length, excerpt.start_byte);
        const quoted = Buffer.from(excerpt.quote, 'utf8');
        if (read.bytesRead !== length || quoted.length !== read.bytesRead || !buffer.subarray(0, read.bytesRead).equals(quoted)) {
          issues.push('excerpt quote mismatch');
        }
      } finally { await handle.close(); }
    }
  } catch (error) {
    issues.push(error instanceof StateError ? error.message : error.message);
  }
  return {
    valid: issues.length === 0,
    structure_check: issues.length === 0,
    source_check: issues.length === 0,
    execution_evidence: receipt.execution ? 'reported' : 'unknown',
    criteria_check: receipt.criteria ? 'declared' : 'unknown',
    observed_result: receipt.observed_result || 'Inconclusive',
    issues,
  };
}

export async function verifyReceipt(planDir, {cwd = process.cwd(), receiptId} = {}) {
  const info = planInfo(planDir, cwd);
  const loaded = loadStore(info);
  if (typeof receiptId !== 'string' || !/^[0-9a-f]{32}$/.test(receiptId)) fail('receipt id is invalid', EXIT_CODES.INPUT);
  const file = receiptPath(loaded.storeDir, receiptId);
  if (!fs.existsSync(file)) fail(`receipt is missing: ${receiptId}`, EXIT_CODES.EVIDENCE);
  const receipt = readJSON(file, `receipt ${receiptId}`);
  if (receipt.receipt_id !== receiptId) fail('receipt id does not match its filename', EXIT_CODES.EVIDENCE);
  const verification = await validateReceipt(info, loaded, receipt);
  return {receipt_id: receiptId, ...verification};
}

export async function recallArtifact(planDir, {cwd = process.cwd(), digest, startByte = 0, length, asJSON = false} = {}) {
  const info = planInfo(planDir, cwd);
  const loaded = loadStore(info);
  if (!isHash(digest)) fail('artifact SHA-256 is invalid', EXIT_CODES.INPUT);
  if (!Number.isInteger(startByte) || startByte < 0 || !Number.isInteger(length) || length < 0 || length > MAX_RECALL_BYTES) {
    fail(`recall range must be 0..${MAX_RECALL_BYTES} bytes`, EXIT_CODES.INPUT);
  }
  const file = artifactDestination(loaded.storeDir, digest);
  if (!fs.existsSync(file)) fail(`artifact is missing: ${digest}`, EXIT_CODES.EVIDENCE);
  const handle = await fs.promises.open(file, 'r');
  try {
    const buffer = Buffer.alloc(length);
    const read = await handle.read(buffer, 0, length, startByte);
    const data = buffer.subarray(0, read.bytesRead);
    return asJSON ? {artifact_sha256: digest, start_byte: startByte, length: data.length, encoding: 'base64', data: data.toString('base64')} : data;
  } finally { await handle.close(); }
}

export function doctor(planDir, {cwd = process.cwd()} = {}) {
  const info = planInfo(planDir, cwd);
  const loaded = loadStore(info, {required: false});
  if (!loaded.store) return {status: 'disabled', reason: 'store_missing', plan_id: info.planId, writes: false, exit_code: EXIT_CODES.OK};
  const receipts = receiptFiles(loaded.storeDir).map(file => path.basename(file, '.json'));
  const transactions = fs.existsSync(path.join(loaded.storeDir, 'transactions'))
    ? fs.readdirSync(path.join(loaded.storeDir, 'transactions')).filter(id => fs.existsSync(path.join(loaded.storeDir, 'transactions', id, 'journal.json'))).map(id => readJSON(path.join(loaded.storeDir, 'transactions', id, 'journal.json'), `transaction ${id}`)).filter(item => item.status !== 'committed')
    : [];
  return {status: 'ready', plan_id: info.planId, store_id: loaded.store.store_id, schema_version: loaded.store.schema_version, capabilities: loaded.store.capabilities, receipts: receipts.length, incomplete_transactions: transactions, writes: false, exit_code: 0};
}

export function recoverTransaction(planDir, {cwd = process.cwd(), transactionId, dryRun = false, apply = false} = {}) {
  const info = planInfo(planDir, cwd);
  const loaded = loadStore(info);
  if (typeof transactionId !== 'string' || !/^[0-9a-f-]{36}$/.test(transactionId)) fail('transaction id is invalid', EXIT_CODES.INPUT);
  const directory = path.join(loaded.storeDir, 'transactions', transactionId);
  const journalFile = path.join(directory, 'journal.json');
  if (!fs.existsSync(journalFile)) fail(`transaction is missing: ${transactionId}`, EXIT_CODES.EVIDENCE);
  const journal = readJSON(journalFile, `transaction ${transactionId}`);
  if (!journal.target) return {transaction_id: transactionId, status: journal.status, action: 'none', dry_run: dryRun};
  assertKeys(journal.target, new Set(['path', 'before_sha256', 'after_sha256', 'after_file']), 'transaction target');
  if (typeof journal.target.path !== 'string' || path.dirname(journal.target.path) !== '.' ||
      !RECORD_FILES.has(journal.target.path) || !isHash(journal.target.before_sha256) ||
      !isHash(journal.target.after_sha256) || journal.target.after_file !== 'after.bin') {
    fail('transaction target metadata is invalid', EXIT_CODES.EVIDENCE);
  }
  const target = path.resolve(info.planDir, journal.target.path);
  if (!fs.existsSync(target)) fail(`transaction target is missing: ${journal.target.path}`, EXIT_CODES.CONFLICT);
  if (fs.lstatSync(target).isSymbolicLink() || !fs.statSync(target).isFile()) {
    fail(`transaction target is not a regular file: ${journal.target.path}`, EXIT_CODES.CONFLICT);
  }
  const afterFile = path.join(directory, journal.target.after_file);
  if (!fs.existsSync(afterFile) || fs.lstatSync(afterFile).isSymbolicLink() || !fs.statSync(afterFile).isFile()) {
    fail('transaction recovery payload is missing or unsafe', EXIT_CODES.EVIDENCE);
  }
  const current = sha256(fs.readFileSync(target));
  const state = current === journal.target.before_sha256 ? 'before' : current === journal.target.after_sha256 ? 'after' : 'other';
  const action = state === 'before' ? 'apply_after' : state === 'after' ? 'mark_committed' : 'manual_conflict';
  if (dryRun || !apply) return {transaction_id: transactionId, state, action, dry_run: true, writes: false};
  if (state === 'other') fail('transaction target has unrelated edits; manual recovery required', EXIT_CODES.CONFLICT);
  if (state === 'before') {
    const after = fs.readFileSync(afterFile);
    const temporary = `${target}.${process.pid}.${crypto.randomBytes(6).toString('hex')}.tmp`;
    fs.writeFileSync(temporary, after, {mode: fs.statSync(target).mode & 0o777, flag: 'wx'});
    fs.renameSync(temporary, target);
  }
  journal.status = 'committed';
  writeJSON(journalFile, journal);
  return {transaction_id: transactionId, state, action, dry_run: false, writes: state === 'before'};
}

export function summarizeReceipt(receipt) {
  return {receipt_id: receipt.receipt_id, observed_result: receipt.observed_result, artifacts: receipt.artifacts.map(item => ({sha256: item.sha256, bytes: item.bytes})), criteria: receipt.criteria};
}
