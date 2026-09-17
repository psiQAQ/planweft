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
const CAPTURE_COMPLETENESS = new Set(['complete', 'truncated', 'unknown']);
const ARTIFACT_ORIGINS = new Set(['controlled_capture', 'imported', 'reported', 'derived']);
const INTEGRITY_STATES = new Set(['verified', 'unknown', 'corrupt', 'missing']);
const EXECUTION_COLLECTION_METHODS = new Set(['controlled_capture', 'imported', 'reported', 'unknown']);
const FRESHNESS_STATES = new Set(['fresh', 'stale', 'unknown']);
const STORE_CAPABILITIES = Object.freeze({artifacts: true, receipts: true, records: true, checkpoints: false, remote_reducer: false});

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
    flushFile(temporary);
    fs.renameSync(temporary, file);
    flushDirectory(path.dirname(file));
  } catch (error) {
    try { fs.rmSync(temporary, {force: true}); } catch {}
    fail(`Cannot write ${file}: ${error.message}`, EXIT_CODES.IO);
  }
}

function flushFile(file) {
  const descriptor = fs.openSync(file, 'r');
  try { fs.fsyncSync(descriptor); } finally { fs.closeSync(descriptor); }
}

function flushDirectory(directory) {
  try {
    const descriptor = fs.openSync(directory, 'r');
    try { fs.fsyncSync(descriptor); } finally { fs.closeSync(descriptor); }
  } catch (error) {
    if (process.platform !== 'win32') throw error;
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

function withinOrEqual(root, candidate) {
  const relative = path.relative(root, candidate);
  return !relative || (relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative));
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
  let planningRoot = null;
  for (let ancestor = path.dirname(resolved); ancestor !== path.dirname(ancestor); ancestor = path.dirname(ancestor)) {
    if (path.basename(ancestor) === '.planning') {
      planningRoot = ancestor;
      break;
    }
  }
  if (planningRoot && path.dirname(resolved) !== planningRoot) {
    fail('selected plan must be a direct child of .planning', EXIT_CODES.INPUT);
  }
  const projectRoot = planningRoot ? path.dirname(planningRoot) : resolved;
  const project = realDirectory(projectRoot, 'authorized project');
  const authorized = realDirectory(cwd, 'command working directory');
  if (!withinOrEqual(authorized, project)) fail('selected plan is outside the authorized project', EXIT_CODES.INPUT);
  return {planDir: resolved, projectRoot: project, planId: planningRoot ? path.basename(resolved) : 'legacy-root'};
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

function rejectSymlinkPath(root, candidate, label) {
  const resolvedRoot = realDirectory(root, 'authorized project');
  let current = path.resolve(candidate);
  while (withinOrEqual(resolvedRoot, current) && current !== resolvedRoot) {
    try {
      if (fs.lstatSync(current).isSymbolicLink()) fail(`${label} contains an unsupported symlink component`, EXIT_CODES.INPUT);
    } catch (error) {
      if (error.code !== 'ENOENT') fail(`${label} cannot be inspected: ${error.message}`, EXIT_CODES.INPUT);
    }
    current = path.dirname(current);
  }
}

function loadStore(info, {required = true} = {}) {
  const storeDir = path.join(info.planDir, STORE_NAME);
  const storeFile = path.join(storeDir, 'store.json');
  if (!fs.existsSync(storeFile)) {
    if (required) fail('state store is not initialized; run state init explicitly', EXIT_CODES.EVIDENCE);
    return {storeDir, store: null, damaged: fs.existsSync(storeDir), reason: fs.existsSync(storeDir) ? 'store_json_missing' : 'store_missing'};
  }
  let storeStat;
  let fileStat;
  try {
    storeStat = fs.lstatSync(storeDir);
    fileStat = fs.lstatSync(storeFile);
  } catch (error) { fail(`state store cannot be inspected: ${error.message}`, EXIT_CODES.EVIDENCE); }
  if (storeStat.isSymbolicLink() || !storeStat.isDirectory() || fileStat.isSymbolicLink() || !fileStat.isFile()) {
    fail('state store layout is unsafe', EXIT_CODES.EVIDENCE);
  }
  const gitignore = path.join(storeDir, '.gitignore');
  try {
    const gitignoreStat = fs.lstatSync(gitignore);
    if (gitignoreStat.isSymbolicLink() || !gitignoreStat.isFile() || fs.readFileSync(gitignore, 'utf8') !== '*\n!.gitignore\n') {
      fail('state store ignore file is invalid', EXIT_CODES.EVIDENCE);
    }
  } catch (error) {
    if (error instanceof StateError) throw error;
    fail(`state store ignore file is invalid: ${error.message}`, EXIT_CODES.EVIDENCE);
  }
  const store = readJSON(storeFile, 'store.json');
  assertKeys(store, new Set(['schema_version', 'store_id', 'plan_id', 'created_at', 'capabilities', 'storage_budget_bytes']), 'store.json');
  if (store.schema_version !== STORE_SCHEMA || typeof store.store_id !== 'string' || !store.store_id ||
      typeof store.plan_id !== 'string' || store.plan_id !== info.planId) {
    fail('state store binding or schema is invalid', EXIT_CODES.EVIDENCE);
  }
  assertKeys(store.capabilities, new Set(Object.keys(STORE_CAPABILITIES)), 'store capabilities');
  for (const [key, expected] of Object.entries(STORE_CAPABILITIES)) {
    if (store.capabilities[key] !== expected) fail(`store capability ${key} is invalid`, EXIT_CODES.EVIDENCE);
  }
  if (store.storage_budget_bytes !== null && (!Number.isSafeInteger(store.storage_budget_bytes) || store.storage_budget_bytes < 0)) {
    fail('storage_budget_bytes is invalid', EXIT_CODES.EVIDENCE);
  }
  return {storeDir, store, damaged: false, reason: null};
}

function ensureStoreDirectories(storeDir) {
  for (const directory of ['artifacts/sha256', 'receipts', 'transactions']) {
    const target = path.join(storeDir, directory);
    if (fs.existsSync(target)) {
      const stat = fs.lstatSync(target);
      if (stat.isSymbolicLink() || !stat.isDirectory()) fail(`state directory is unsafe: ${directory}`, EXIT_CODES.EVIDENCE);
    } else {
      fs.mkdirSync(target, {recursive: true, mode: 0o700});
    }
  }
}

export function initStore(planDir, {cwd = process.cwd(), storageBudgetBytes = null} = {}) {
  const info = planInfo(planDir, cwd);
  if (storageBudgetBytes !== null && (!Number.isSafeInteger(storageBudgetBytes) || storageBudgetBytes < 0)) {
    fail('storage_budget_bytes is invalid', EXIT_CODES.INPUT);
  }
  const target = path.join(info.planDir, STORE_NAME);
  if (fs.existsSync(target)) {
    const loaded = loadStore(info);
    ensureStoreDirectories(loaded.storeDir);
    return {created: false, ...info, ...loaded};
  }
  fs.mkdirSync(target, {mode: 0o700});
  ensureStoreDirectories(target);
  const gitignore = path.join(target, '.gitignore');
  fs.writeFileSync(gitignore, '*\n!.gitignore\n', {mode: 0o600, flag: 'wx'});
  flushFile(gitignore);
  const store = {
    schema_version: STORE_SCHEMA,
    store_id: crypto.randomUUID(),
    plan_id: info.planId,
    created_at: now(),
    capabilities: {...STORE_CAPABILITIES},
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
  flushFile(destination);
  const measured = {sha256: hash.digest('hex'), bytes};
  const confirmed = await hashFile(destination);
  if (confirmed.sha256 !== measured.sha256 || confirmed.bytes !== measured.bytes) {
    fail('staged artifact changed before publication', EXIT_CODES.EVIDENCE);
  }
  return measured;
}

function artifactDestination(storeDir, digest) {
  return path.join(storeDir, 'artifacts', 'sha256', digest.slice(0, 2), digest);
}

async function archiveArtifact(info, loaded, entry, temporaryRoot) {
  assertKeys(entry, new Set(['path', 'media_type', 'encoding', 'capture_completeness', 'origin', 'derived_from']), 'artifact input');
  if (typeof entry.path !== 'string' || !entry.path) fail('artifact path is required', EXIT_CODES.INPUT);
  if (typeof entry.media_type !== 'string' || !entry.media_type) fail('artifact media_type is required', EXIT_CODES.INPUT);
  if (entry.encoding !== null && entry.encoding !== undefined && typeof entry.encoding !== 'string') fail('artifact encoding is invalid', EXIT_CODES.INPUT);
  if (!CAPTURE_COMPLETENESS.has(entry.capture_completeness)) fail('artifact capture_completeness is invalid', EXIT_CODES.INPUT);
  if (!ARTIFACT_ORIGINS.has(entry.origin)) fail('artifact origin is invalid', EXIT_CODES.INPUT);
  if (entry.derived_from !== undefined && (!Array.isArray(entry.derived_from) || entry.derived_from.some(item => !isHash(item)))) {
    fail('artifact derived_from is invalid', EXIT_CODES.INPUT);
  }
  const sourceCandidate = path.resolve(info.projectRoot, entry.path);
  let source;
  try {
    rejectSymlinkPath(info.projectRoot, sourceCandidate, 'artifact source');
    const stat = fs.lstatSync(sourceCandidate);
    if (stat.isSymbolicLink() || !stat.isFile()) fail(`artifact source is not a regular file: ${entry.path}`, EXIT_CODES.INPUT);
    source = inside(info.projectRoot, sourceCandidate, 'artifact source');
    if (withinOrEqual(loaded.storeDir, source.absolute)) fail('artifact source cannot be inside the task state store', EXIT_CODES.INPUT);
  } catch (error) {
    if (error instanceof StateError) throw error;
    fail(`artifact source cannot be read: ${error.message}`, EXIT_CODES.INPUT);
  }
  const staged = path.join(temporaryRoot, crypto.randomUUID() + '.artifact');
  const measured = await archiveFile(source.absolute, staged);
  const destination = artifactDestination(loaded.storeDir, measured.sha256);
  rejectSymlinkPath(loaded.storeDir, destination, 'artifact object');
  fs.mkdirSync(path.dirname(destination), {recursive: true, mode: 0o700});
  if (fs.existsSync(destination)) {
    const existing = await hashFile(destination);
    if (existing.sha256 !== measured.sha256 || existing.bytes !== measured.bytes) {
      fail(`artifact object is corrupted for ${measured.sha256}`, EXIT_CODES.EVIDENCE);
    }
    fs.rmSync(staged, {force: true});
  } else {
    const budget = loaded.store.storage_budget_bytes;
    if (budget !== null && storageUsage(loaded.storeDir) + measured.bytes > budget) {
      fail(`artifact exceeds storage budget of ${budget} bytes`, EXIT_CODES.IO);
    }
    fs.renameSync(staged, destination);
    flushDirectory(path.dirname(destination));
  }
  return {
    path: posix(path.relative(info.projectRoot, source.absolute)),
    sha256: measured.sha256,
    bytes: measured.bytes,
    media_type: entry.media_type,
    encoding: entry.encoding ?? null,
    capture_completeness: entry.capture_completeness,
    origin: entry.origin,
    integrity: 'verified',
    derived_from: entry.derived_from || [],
  };
}

async function hashFile(file) {
  const hash = crypto.createHash('sha256');
  let bytes = 0;
  for await (const chunk of fs.createReadStream(file)) { hash.update(chunk); bytes += chunk.length; }
  return {sha256: hash.digest('hex'), bytes};
}

function storageUsage(storeDir) {
  const root = path.join(storeDir, 'artifacts');
  let total = 0;
  if (!fs.existsSync(root)) return total;
  const visit = directory => {
    for (const entry of fs.readdirSync(directory, {withFileTypes: true})) {
      const target = path.join(directory, entry.name);
      if (entry.isDirectory()) visit(target);
      else if (entry.isFile()) total += fs.statSync(target).size;
    }
  };
  visit(root);
  return total;
}

function hashFileSync(file) {
  const hash = crypto.createHash('sha256');
  let bytes = 0;
  const descriptor = fs.openSync(file, 'r');
  try {
    const buffer = Buffer.alloc(1024 * 1024);
    let read;
    do {
      read = fs.readSync(descriptor, buffer, 0, buffer.length, null);
      if (read) { hash.update(buffer.subarray(0, read)); bytes += read; }
    } while (read);
  } finally { fs.closeSync(descriptor); }
  return {sha256: hash.digest('hex'), bytes};
}

function readInput(info, inputPath, cwd) {
  if (typeof inputPath !== 'string' || !inputPath) fail('--input is required', EXIT_CODES.INPUT);
  const candidate = path.resolve(cwd, inputPath);
  try {
    rejectSymlinkPath(info.projectRoot, candidate, 'record input');
    if (fs.lstatSync(candidate).isSymbolicLink()) fail('record input cannot be a symlink', EXIT_CODES.INPUT);
  } catch (error) {
    if (error.code !== 'ENOENT') fail(`record input cannot be read: ${error.message}`, EXIT_CODES.INPUT);
  }
  const source = inside(info.projectRoot, candidate, 'record input');
  if (withinOrEqual(info.planDir, source.absolute)) fail('record input cannot be inside the selected plan', EXIT_CODES.INPUT);
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

function validateExecution(execution, label = 'execution') {
  if (execution === undefined || execution === null) return;
  assertKeys(execution, new Set(['argv', 'command', 'cwd', 'started_at', 'ended_at', 'exit_code', 'signal', 'timeout', 'collection_method']), label);
  if (execution.argv !== undefined && (!Array.isArray(execution.argv) || execution.argv.some(item => typeof item !== 'string'))) fail(`${label}.argv is invalid`, EXIT_CODES.INPUT);
  if (execution.command !== undefined && execution.command !== null && typeof execution.command !== 'string') fail(`${label}.command is invalid`, EXIT_CODES.INPUT);
  if (execution.argv === undefined && execution.command === undefined) fail(`${label} must include argv or command`, EXIT_CODES.INPUT);
  for (const field of ['cwd', 'started_at', 'ended_at', 'signal']) {
    if (execution[field] !== undefined && execution[field] !== null && typeof execution[field] !== 'string') fail(`${label}.${field} is invalid`, EXIT_CODES.INPUT);
  }
  if (execution.exit_code !== undefined && execution.exit_code !== null && !Number.isInteger(execution.exit_code)) fail(`${label}.exit_code is invalid`, EXIT_CODES.INPUT);
  if (execution.timeout !== undefined && execution.timeout !== null && typeof execution.timeout !== 'boolean') fail(`${label}.timeout is invalid`, EXIT_CODES.INPUT);
  if (!EXECUTION_COLLECTION_METHODS.has(execution.collection_method)) fail(`${label}.collection_method is invalid`, EXIT_CODES.INPUT);
}

function validateCriteria(criteria, label = 'criteria') {
  if (criteria === undefined || criteria === null) return;
  assertKeys(criteria, new Set(['covered', 'not_covered']), label);
  for (const field of ['covered', 'not_covered']) {
    if (!Array.isArray(criteria[field]) || criteria[field].some(item => typeof item !== 'string' || !item)) fail(`${label}.${field} is invalid`, EXIT_CODES.INPUT);
  }
}

function validateFreshness(freshness, label = 'freshness') {
  if (freshness === undefined || freshness === null) return;
  assertKeys(freshness, new Set(['status', 'reason', 'checked_at', 'subject_sha256']), label);
  if (!FRESHNESS_STATES.has(freshness.status) || typeof freshness.reason !== 'string' || !freshness.reason) fail(`${label} is invalid`, EXIT_CODES.INPUT);
  if (freshness.checked_at !== null && freshness.checked_at !== undefined && typeof freshness.checked_at !== 'string') fail(`${label}.checked_at is invalid`, EXIT_CODES.INPUT);
  if (freshness.subject_sha256 !== null && freshness.subject_sha256 !== undefined && !isHash(freshness.subject_sha256)) fail(`${label}.subject_sha256 is invalid`, EXIT_CODES.INPUT);
}

function validateRecordInput(input) {
  assertKeys(input, new Set(['idempotency_key', 'execution', 'subject', 'observed_result', 'interpretation', 'criteria', 'freshness', 'artifacts', 'excerpts', 'markdown', 'supersedes']), 'record input');
  if (typeof input.idempotency_key !== 'string' || !input.idempotency_key) fail('idempotency_key is required', EXIT_CODES.INPUT);
  if (input.observed_result !== undefined && !['Passed', 'Failed', 'Inconclusive', 'Not Run'].includes(input.observed_result)) {
    fail('observed_result is invalid', EXIT_CODES.INPUT);
  }
  validateExecution(input.execution);
  validateCriteria(input.criteria);
  validateFreshness(input.freshness);
  if (input.supersedes !== undefined && input.supersedes !== null && (!Array.isArray(input.supersedes) || input.supersedes.some(item => typeof item !== 'string' || !/^[0-9a-f]{32}$/.test(item)))) {
    fail('supersedes is invalid', EXIT_CODES.INPUT);
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
      excerpt.start_byte < 0 || excerpt.end_byte < excerpt.start_byte || excerpt.end_byte - excerpt.start_byte > MAX_RECALL_BYTES ||
      !Array.isArray(excerpt.lines) || excerpt.lines.some(line => !Number.isInteger(line) || line < 1) || typeof excerpt.quote !== 'string') {
    fail('excerpt range or quote is invalid', EXIT_CODES.INPUT);
  }
  if (!artifacts.some(artifact => artifact.sha256 === excerpt.artifact_sha256)) fail('excerpt references an unknown artifact', EXIT_CODES.INPUT);
}

async function verifyExcerptAgainstArtifact(storeDir, excerpt) {
  const file = artifactDestination(storeDir, excerpt.artifact_sha256);
  const length = excerpt.end_byte - excerpt.start_byte;
  const handle = await fs.promises.open(file, 'r');
  try {
    const buffer = Buffer.alloc(length);
    const read = await handle.read(buffer, 0, length, excerpt.start_byte);
    const quoted = Buffer.from(excerpt.quote, 'utf8');
    if (read.bytesRead !== length || quoted.length !== read.bytesRead || !buffer.subarray(0, read.bytesRead).equals(quoted)) {
      fail('excerpt quote does not match artifact bytes', EXIT_CODES.INPUT);
    }
  } finally { await handle.close(); }
}

function receiptPath(storeDir, receiptId) { return path.join(storeDir, 'receipts', `${receiptId}.json`); }

function acquireLock(storeDir, operationId) {
  const lock = path.join(storeDir, '.write-lock');
  let created = false;
  try {
    fs.mkdirSync(lock);
    created = true;
    writeJSON(path.join(lock, 'owner.json'), {operation_id: operationId, pid: process.pid, acquired_at: now()});
    return lock;
  } catch (error) {
    if (created) {
      try { fs.rmSync(lock, {recursive: true, force: true}); } catch {}
    }
    if (error.code === 'EEXIST') fail('another state write owns the store lock', EXIT_CODES.CONFLICT);
    fail(`cannot acquire state lock: ${error.message}`, EXIT_CODES.IO);
  }
}

function releaseLock(lock) {
  if (lock) fs.rmSync(lock, {recursive: true, force: true});
}

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
  let lock = null;
  let journalPublished = false;
  let receiptFile = null;
  try {
    lock = acquireLock(loaded.storeDir, transactionId);
    const artifacts = [];
    for (const entry of request.artifacts) artifacts.push(await archiveArtifact(info, loaded, entry, temporaryRoot));
    const excerpts = request.excerpts || [];
    for (const excerpt of excerpts) {
      validateExcerpt(excerpt, artifacts);
      await verifyExcerptAgainstArtifact(loaded.storeDir, excerpt);
    }
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
      freshness: request.freshness ?? {status: 'unknown', reason: 'freshness was not assessed', checked_at: null, subject_sha256: null},
      supersedes: request.supersedes ?? [],
    };
    receiptFile = receiptPath(loaded.storeDir, receiptId);
    if (fs.existsSync(receiptFile)) fail('receipt id collision with different content', EXIT_CODES.CONFLICT);
    writeJSON(receiptFile, receipt);
    const journal = {
      schema_version: 1,
      transaction_id: transactionId,
      status: 'receipt_published',
      store_id: loaded.store.store_id,
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
      flushFile(temporary);
      fs.renameSync(temporary, markdownTarget);
      flushDirectory(path.dirname(markdownTarget));
      if (sha256(fs.readFileSync(markdownTarget)) !== journal.target.after_sha256) {
        fail('markdown target changed or failed to persist after write', EXIT_CODES.EVIDENCE, {path: request.markdown.path});
      }
      journal.status = 'committed';
    } else {
      writeJSON(path.join(transactionDir, 'journal.json'), journal);
      journalPublished = true;
      journal.status = 'committed';
    }
    writeJSON(path.join(transactionDir, 'journal.json'), journal);
    return {idempotent: false, receipt_id: receiptId, transaction_id: transactionId, receipt};
  } finally {
    releaseLock(lock);
    fs.rmSync(temporaryRoot, {recursive: true, force: true});
    if (!journalPublished) {
      fs.rmSync(transactionDir, {recursive: true, force: true});
      if (receiptFile) fs.rmSync(receiptFile, {force: true});
    }
  }
}

async function validateReceipt(info, loaded, receipt) {
  const structureIssues = [];
  const sourceIssues = [];
  const allowed = new Set(['schema_version', 'receipt_id', 'store_id', 'plan_id', 'recorded_at', 'producer', 'operation_id', 'idempotency_key', 'input_sha256', 'execution', 'subject', 'artifacts', 'excerpts', 'observed_result', 'interpretation', 'criteria', 'freshness', 'supersedes']);
  try { assertKeys(receipt, allowed, 'receipt'); } catch (error) { structureIssues.push(error.message); }
  if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt)) {
    return {valid: false, structure_check: false, source_check: false, execution_evidence: 'unknown', criteria_check: 'unknown', freshness_check: 'unknown', observed_result: 'Inconclusive', structure_issues: structureIssues, source_issues: [], issues: structureIssues};
  }
  if (receipt.schema_version !== RECEIPT_SCHEMA) structureIssues.push('unsupported schema_version');
  if (typeof receipt.receipt_id !== 'string' || !/^[0-9a-f]{32}$/.test(receipt.receipt_id)) structureIssues.push('receipt id invalid');
  if (receipt.store_id !== loaded.store.store_id || receipt.plan_id !== info.planId) structureIssues.push('store or plan binding mismatch');
  if (!isHash(receipt.input_sha256)) structureIssues.push('input_sha256 is invalid');
  if (!Array.isArray(receipt.artifacts) || !receipt.artifacts.length) structureIssues.push('artifacts missing');
  if (!Array.isArray(receipt.excerpts)) structureIssues.push('excerpts missing');
  if (!['Passed', 'Failed', 'Inconclusive', 'Not Run'].includes(receipt.observed_result)) structureIssues.push('observed_result is invalid');
  try { validateExecution(receipt.execution, 'receipt.execution'); } catch (error) { structureIssues.push(error.message); }
  try { validateCriteria(receipt.criteria, 'receipt.criteria'); } catch (error) { structureIssues.push(error.message); }
  try { validateFreshness(receipt.freshness, 'receipt.freshness'); } catch (error) { structureIssues.push(error.message); }
  if (receipt.criteria === null || receipt.criteria === undefined) structureIssues.push('criteria declaration is missing');
  if (receipt.freshness === null || receipt.freshness === undefined) structureIssues.push('freshness declaration is missing');
  if (!Array.isArray(receipt.supersedes) || receipt.supersedes.some(item => typeof item !== 'string' || !/^[0-9a-f]{32}$/.test(item))) structureIssues.push('supersedes is invalid');

  for (const artifact of Array.isArray(receipt.artifacts) ? receipt.artifacts : []) {
    try { assertKeys(artifact, new Set(['path', 'sha256', 'bytes', 'media_type', 'encoding', 'capture_completeness', 'origin', 'integrity', 'derived_from']), 'receipt artifact'); }
    catch (error) { structureIssues.push(error.message); continue; }
    if (typeof artifact.path !== 'string' || path.isAbsolute(artifact.path) || artifact.path.includes('\\')) structureIssues.push('artifact path is not relative');
    if (!isHash(artifact.sha256) || !Number.isSafeInteger(artifact.bytes) || artifact.bytes < 0 || typeof artifact.media_type !== 'string' || !artifact.media_type ||
        (artifact.encoding !== null && typeof artifact.encoding !== 'string') || !CAPTURE_COMPLETENESS.has(artifact.capture_completeness) ||
        !ARTIFACT_ORIGINS.has(artifact.origin) || !INTEGRITY_STATES.has(artifact.integrity) || !Array.isArray(artifact.derived_from) || artifact.derived_from.some(item => !isHash(item))) {
      structureIssues.push('artifact metadata invalid');
      continue;
    }
    const file = artifactDestination(loaded.storeDir, artifact.sha256);
    rejectSymlinkPath(loaded.storeDir, file, 'artifact object');
    let stat;
    try { stat = fs.lstatSync(file); } catch { sourceIssues.push(`artifact missing: ${artifact.sha256}`); continue; }
    if (stat.isSymbolicLink() || !stat.isFile()) { sourceIssues.push(`artifact object is unsafe: ${artifact.sha256}`); continue; }
    const measured = await hashFile(file);
    if (measured.sha256 !== artifact.sha256 || measured.bytes !== artifact.bytes) sourceIssues.push(`artifact hash mismatch: ${artifact.sha256}`);
  }
  for (const excerpt of Array.isArray(receipt.excerpts) ? receipt.excerpts : []) {
    const artifact = (Array.isArray(receipt.artifacts) ? receipt.artifacts : []).find(item => item && excerpt && item.sha256 === excerpt.artifact_sha256);
    try { validateExcerpt(excerpt, Array.isArray(receipt.artifacts) ? receipt.artifacts : []); } catch (error) { structureIssues.push(error.message); continue; }
    if (!artifact) continue;
    const file = artifactDestination(loaded.storeDir, artifact.sha256);
    if (!fs.existsSync(file)) continue;
    try { await verifyExcerptAgainstArtifact(loaded.storeDir, excerpt); }
    catch (error) { sourceIssues.push(error.message); }
  }
  const executionEvidence = receipt.execution ? 'reported' : 'unknown';
  const criteriaCheck = receipt.criteria && Array.isArray(receipt.criteria.covered) && Array.isArray(receipt.criteria.not_covered) &&
    (receipt.criteria.covered.length || receipt.criteria.not_covered.length) ? 'declared' : 'unknown';
  const freshnessCheck = receipt.freshness?.status || 'unknown';
  return {
    valid: structureIssues.length === 0 && sourceIssues.length === 0,
    structure_check: structureIssues.length === 0,
    source_check: sourceIssues.length === 0,
    execution_evidence: executionEvidence,
    criteria_check: criteriaCheck,
    freshness_check: freshnessCheck,
    observed_result: receipt.observed_result || 'Inconclusive',
    structure_issues: structureIssues,
    source_issues: sourceIssues,
    issues: [...structureIssues, ...sourceIssues],
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
  rejectSymlinkPath(loaded.storeDir, file, 'artifact object');
  const stat = fs.lstatSync(file);
  if (stat.isSymbolicLink() || !stat.isFile()) fail(`artifact object is unsafe: ${digest}`, EXIT_CODES.EVIDENCE);
  const before = await hashFile(file);
  if (before.sha256 !== digest) fail(`artifact hash mismatch: ${digest}`, EXIT_CODES.EVIDENCE);
  if (startByte > before.bytes || startByte + length > before.bytes) fail('recall range exceeds artifact bytes', EXIT_CODES.EVIDENCE);
  const handle = await fs.promises.open(file, 'r');
  try {
    const buffer = Buffer.alloc(length);
    const read = await handle.read(buffer, 0, length, startByte);
    const data = buffer.subarray(0, read.bytesRead);
    const after = await hashFile(file);
    if (after.sha256 !== digest || after.bytes !== before.bytes) fail(`artifact changed during recall: ${digest}`, EXIT_CODES.EVIDENCE);
    return asJSON ? {artifact_sha256: digest, start_byte: startByte, length: data.length, encoding: 'base64', data: data.toString('base64')} : data;
  } finally { await handle.close(); }
}

function processIsAlive(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  try { process.kill(pid, 0); return true; } catch (error) { return error.code === 'EPERM'; }
}

function inspectLock(storeDir) {
  const lock = path.join(storeDir, '.write-lock');
  if (!fs.existsSync(lock)) return {status: 'absent', stale: false, owner: null};
  let stat;
  try { stat = fs.lstatSync(lock); } catch (error) { return {status: 'invalid', stale: true, owner: null, issue: error.message}; }
  if (stat.isSymbolicLink() || !stat.isDirectory()) return {status: 'invalid', stale: true, owner: null, issue: 'write lock is not a regular directory'};
  const ownerFile = path.join(lock, 'owner.json');
  if (!fs.existsSync(ownerFile)) return {status: 'present', stale: true, owner: null, issue: 'owner metadata is missing'};
  try {
    const owner = readJSON(ownerFile, 'write lock owner');
    const stale = !processIsAlive(owner.pid);
    return {status: 'present', stale, owner, ...(stale ? {issue: 'owner process is not alive'} : {})};
  } catch (error) { return {status: 'invalid', stale: true, owner: null, issue: error.message}; }
}

export async function doctor(planDir, {cwd = process.cwd()} = {}) {
  const info = planInfo(planDir, cwd);
  let loaded;
  try { loaded = loadStore(info, {required: false}); }
  catch (error) {
    return {status: 'damaged', reason: error.message, plan_id: info.planId, writes: false, read_mode: 'read-only', write_mode: 'disabled', exit_code: error.code || EXIT_CODES.EVIDENCE};
  }
  if (!loaded.store) {
    return {status: loaded.damaged ? 'damaged' : 'disabled', reason: loaded.reason, plan_id: info.planId, writes: false, read_mode: 'read-only', write_mode: 'disabled', exit_code: loaded.damaged ? EXIT_CODES.EVIDENCE : EXIT_CODES.OK};
  }
  const receiptIds = receiptFiles(loaded.storeDir).map(file => path.basename(file, '.json'));
  const receiptIssues = [];
  const missingReferences = [];
  const damagedReferences = [];
  const staleEvidence = [];
  let localArtifactCount = 0;
  for (const file of receiptFiles(loaded.storeDir)) {
    const receiptId = path.basename(file, '.json');
    try {
      const receipt = readJSON(file, `receipt ${receiptId}`);
      const verification = await validateReceipt(info, loaded, receipt);
      localArtifactCount += Array.isArray(receipt.artifacts) ? receipt.artifacts.length : 0;
      if (!verification.valid) {
        receiptIssues.push({receipt_id: receiptId, issues: verification.issues});
        for (const issue of verification.source_issues) {
          if (issue.includes('missing')) missingReferences.push({receipt_id: receiptId, issue});
          else damagedReferences.push({receipt_id: receiptId, issue});
        }
      }
      if (verification.freshness_check !== 'fresh') staleEvidence.push({receipt_id: receiptId, status: verification.freshness_check});
    } catch (error) { receiptIssues.push({receipt_id: receiptId, issues: [error.message]}); }
  }
  const transactions = [];
  const transactionRoot = path.join(loaded.storeDir, 'transactions');
  if (fs.existsSync(transactionRoot)) {
    for (const id of fs.readdirSync(transactionRoot)) {
      const journalFile = path.join(transactionRoot, id, 'journal.json');
      if (!fs.existsSync(journalFile)) continue;
      try {
        const journal = readJSON(journalFile, `transaction ${id}`);
        if (journal.status !== 'committed') transactions.push(journal);
      } catch (error) { transactions.push({transaction_id: id, status: 'invalid', issue: error.message}); }
    }
  }
  const writeLock = inspectLock(loaded.storeDir);
  const localOnly = {status: 'local-only', reason: 'P0 store has no remote sharing or reducer', artifact_count: localArtifactCount};
  const problems = [...receiptIssues, ...damagedReferences, ...(writeLock.status === 'invalid' ? [writeLock.issue] : [])];
  return {
    status: problems.length ? 'degraded' : 'ready',
    plan_id: info.planId,
    store_id: loaded.store.store_id,
    schema_version: loaded.store.schema_version,
    capabilities: loaded.store.capabilities,
    storage_budget_bytes: loaded.store.storage_budget_bytes,
    storage_used_bytes: storageUsage(loaded.storeDir),
    read_mode: 'read-only',
    write_mode: 'disabled',
    receipts: receiptIds.length,
    incomplete_transactions: transactions,
    missing_references: missingReferences,
    damaged_references: damagedReferences,
    stale_evidence: staleEvidence,
    local_only: localOnly,
    write_lock: writeLock,
    writes: false,
    exit_code: problems.length ? EXIT_CODES.EVIDENCE : EXIT_CODES.OK,
  };
}

export function recoverTransaction(planDir, {cwd = process.cwd(), transactionId, dryRun = false, apply = false} = {}) {
  const info = planInfo(planDir, cwd);
  const loaded = loadStore(info);
  if (typeof transactionId !== 'string' || !/^[0-9a-f-]{36}$/.test(transactionId)) fail('transaction id is invalid', EXIT_CODES.INPUT);
  const directory = path.join(loaded.storeDir, 'transactions', transactionId);
  const journalFile = path.join(directory, 'journal.json');
  if (!fs.existsSync(journalFile)) fail(`transaction is missing: ${transactionId}`, EXIT_CODES.EVIDENCE);
  const journal = readJSON(journalFile, `transaction ${transactionId}`);
  try { assertKeys(journal, new Set(['schema_version', 'transaction_id', 'status', 'store_id', 'receipt_id', 'plan_id', 'target']), 'transaction journal'); }
  catch (error) { fail(error.message, EXIT_CODES.EVIDENCE); }
  if (journal.schema_version !== 1 || journal.transaction_id !== transactionId || journal.store_id !== loaded.store.store_id || journal.plan_id !== info.planId ||
      (typeof journal.receipt_id !== 'string' && journal.receipt_id !== null)) {
    fail('transaction journal binding or schema is invalid', EXIT_CODES.EVIDENCE);
  }
  if (journal.receipt_id) {
    const receiptFile = receiptPath(loaded.storeDir, journal.receipt_id);
    if (!fs.existsSync(receiptFile)) fail('transaction receipt is missing', EXIT_CODES.EVIDENCE);
    const receipt = readJSON(receiptFile, `receipt ${journal.receipt_id}`);
    if (receipt.store_id !== loaded.store.store_id || receipt.plan_id !== info.planId || receipt.operation_id !== transactionId) {
      fail('transaction receipt binding is invalid', EXIT_CODES.EVIDENCE);
    }
  }
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
  const afterMeasured = hashFileSync(afterFile);
  if (afterMeasured.sha256 !== journal.target.after_sha256) fail('transaction recovery payload hash mismatch', EXIT_CODES.EVIDENCE);
  const current = sha256(fs.readFileSync(target));
  const state = current === journal.target.before_sha256 ? 'before' : current === journal.target.after_sha256 ? 'after' : 'other';
  const action = state === 'before' ? 'apply_after' : state === 'after' ? 'mark_committed' : 'manual_conflict';
  if (dryRun || !apply) return {transaction_id: transactionId, state, action, dry_run: true, writes: false};
  if (state === 'other') fail('transaction target has unrelated edits; manual recovery required', EXIT_CODES.CONFLICT);
  const lock = acquireLock(loaded.storeDir, transactionId);
  let finalState = state;
  let wrote = false;
  try {
    const lockedCurrent = sha256(fs.readFileSync(target));
    finalState = lockedCurrent === journal.target.before_sha256 ? 'before' : lockedCurrent === journal.target.after_sha256 ? 'after' : 'other';
    if (finalState === 'other') {
      fail('transaction target changed while acquiring recovery lock', EXIT_CODES.CONFLICT);
    }
    const lockedPayload = hashFileSync(afterFile);
    if (lockedPayload.sha256 !== journal.target.after_sha256) fail('transaction recovery payload changed during recovery', EXIT_CODES.EVIDENCE);
    if (finalState === 'before') {
      const after = fs.readFileSync(afterFile);
      const temporary = `${target}.${process.pid}.${crypto.randomBytes(6).toString('hex')}.tmp`;
      fs.writeFileSync(temporary, after, {mode: fs.statSync(target).mode & 0o777, flag: 'wx'});
      try {
        flushFile(temporary);
        fs.renameSync(temporary, target);
        flushDirectory(path.dirname(target));
      } finally { fs.rmSync(temporary, {force: true}); }
      if (sha256(fs.readFileSync(target)) !== journal.target.after_sha256) fail('recovered target hash mismatch', EXIT_CODES.EVIDENCE);
      wrote = true;
    }
    journal.status = 'committed';
    writeJSON(journalFile, journal);
  } finally {
    releaseLock(lock);
  }
  return {transaction_id: transactionId, state: finalState, action: finalState === 'before' ? 'apply_after' : 'mark_committed', dry_run: false, writes: wrote};
}

export function summarizeReceipt(receipt) {
  return {receipt_id: receipt.receipt_id, observed_result: receipt.observed_result, artifacts: receipt.artifacts.map(item => ({sha256: item.sha256, bytes: item.bytes})), criteria: receipt.criteria};
}
