import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {
  EXIT_CODES,
  StateError,
  checkpointState,
  doctor,
  initStore,
  recallArtifact,
  recordState,
  recoverTransaction,
  reduceArtifact,
  verifyReceipt,
  verifyQuoteInput,
  upgradeStore,
} from './core.mjs';

const HELP = `PlanWeft task evidence state

Usage:
  planweft state init [--plan-dir DIR] [--storage-budget-bytes N]
  planweft state upgrade [--plan-dir DIR]
  planweft state record --input FILE [--plan-dir DIR]
  planweft state verify --receipt ID [--plan-dir DIR]
  planweft state recall --artifact SHA256 --start-byte N --length N [--plan-dir DIR] [--json]
  planweft state doctor [--plan-dir DIR]
  planweft state recover --transaction ID --dry-run [--plan-dir DIR]
  planweft state checkpoint [--plan-dir DIR] [--dry-run|--apply] [--checkpoint ID] [--json]
  planweft state reduce --artifact SHA256 [--plan-dir DIR] [--json]
  planweft state quote-verify --input FILE [--plan-dir DIR] [--json]

The selected plan defaults to .planning/$PLAN_ID when PLAN_ID is set. State
records are disabled when PLANNING_DISABLED=1. record accepts data only and
never executes a command string from its input.
`;

function valueFor(args, name, {required = false} = {}) {
  const index = args.findIndex(arg => arg === name || arg.startsWith(`${name}=`));
  if (index < 0) {
    if (required) throw new StateError(`${name} is required`, EXIT_CODES.INPUT);
    return undefined;
  }
  const arg = args[index];
  if (arg.includes('=')) return arg.slice(arg.indexOf('=') + 1);
  if (!args[index + 1] || args[index + 1].startsWith('--')) {
    throw new StateError(`${name} requires a value`, EXIT_CODES.INPUT);
  }
  return args[index + 1];
}

function has(args, name) {
  return args.includes(name) || args.some(arg => arg.startsWith(`${name}=`));
}

function rejectUnknown(args, allowed) {
  for (const arg of args) {
    if (!arg.startsWith('--')) continue;
    const name = arg.split('=', 1)[0];
    if (!allowed.has(name)) throw new StateError(`unknown option: ${name}`, EXIT_CODES.INPUT);
  }
}

function integerValue(args, name, {required = false, defaultValue} = {}) {
  const raw = valueFor(args, name, {required});
  if (raw === undefined) return defaultValue;
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new StateError(`${name} must be a non-negative integer`, EXIT_CODES.INPUT);
  }
  return value;
}

function selectedPlanDir(args, env) {
  const explicit = valueFor(args, '--plan-dir');
  if (explicit || env.PLAN_DIR) return explicit || env.PLAN_DIR;
  if (env.PLAN_ID) {
    if (!/^[^/\\]+$/.test(env.PLAN_ID) || env.PLAN_ID === '.' || env.PLAN_ID === '..') {
      throw new StateError('PLAN_ID must be one safe .planning directory name', EXIT_CODES.INPUT);
    }
    return path.join('.planning', env.PLAN_ID);
  }
  return '.';
}

function disabledResult(action, env) {
  return {
    action,
    status: 'disabled',
    reason: 'PLANNING_DISABLED=1',
    writes: false,
    exit_code: EXIT_CODES.OK,
    ...(env.PLAN_ID ? {plan_id: env.PLAN_ID} : {}),
  };
}

function emit(value, {json, stdout}) {
  if (Buffer.isBuffer(value)) {
    stdout.write(value);
    return;
  }
  stdout.write(json ? JSON.stringify(value, null, 2) + '\n' : format(value) + '\n');
}

function format(value) {
  if (value && typeof value === 'object') {
    if (value.created !== undefined) return value.created ? `Initialized state store for ${value.plan_id}` : `State store already initialized for ${value.plan_id}`;
    if (value.idempotent) return `Reused receipt ${value.receipt_id}`;
    if (value.receipt_id) return `Recorded receipt ${value.receipt_id}`;
    if (value.status === 'disabled') return `State disabled (${value.reason})`;
    if (value.valid !== undefined) return value.valid ? `Receipt ${value.receipt_id} verified` : `Receipt ${value.receipt_id} failed verification`;
  }
  return JSON.stringify(value);
}

export async function main(argv = process.argv.slice(2), {
  cwd = process.cwd(),
  env = process.env,
  stdout = process.stdout,
  stderr = process.stderr,
} = {}) {
  const args = [...argv];
  const action = args.shift() || 'help';
  const json = has(args, '--json');
  if (action === 'help' || action === '--help' || has(args, '--help')) {
    stdout.write(HELP);
    return EXIT_CODES.OK;
  }

  try {
    const planDir = selectedPlanDir(args, env);
    let value;
    if (action === 'init') {
      rejectUnknown(args, new Set(['--plan-dir', '--storage-budget-bytes', '--json']));
      value = env.PLANNING_DISABLED === '1'
        ? disabledResult(action, env)
        : initStore(planDir, {cwd, storageBudgetBytes: integerValue(args, '--storage-budget-bytes', {defaultValue: null})});
    } else if (action === 'upgrade') {
      rejectUnknown(args, new Set(['--plan-dir', '--json']));
      value = env.PLANNING_DISABLED === '1' ? disabledResult(action, env) : upgradeStore(planDir, {cwd});
    } else if (action === 'record') {
      rejectUnknown(args, new Set(['--plan-dir', '--input', '--json']));
      value = env.PLANNING_DISABLED === '1'
        ? disabledResult(action, env)
        : await recordState(planDir, {cwd, inputPath: valueFor(args, '--input', {required: true})});
    } else if (action === 'verify') {
      rejectUnknown(args, new Set(['--plan-dir', '--receipt', '--json']));
      value = await verifyReceipt(planDir, {cwd, receiptId: valueFor(args, '--receipt', {required: true})});
    } else if (action === 'recall') {
      rejectUnknown(args, new Set(['--plan-dir', '--artifact', '--start-byte', '--length', '--json']));
      value = await recallArtifact(planDir, {
        cwd,
        digest: valueFor(args, '--artifact', {required: true}),
        startByte: integerValue(args, '--start-byte', {defaultValue: 0}),
        length: integerValue(args, '--length', {required: true}),
        asJSON: json,
      });
    } else if (action === 'doctor') {
      rejectUnknown(args, new Set(['--plan-dir', '--json']));
      value = env.PLANNING_DISABLED === '1'
        ? disabledResult(action, env)
        : await doctor(planDir, {cwd});
    } else if (action === 'recover') {
      rejectUnknown(args, new Set(['--plan-dir', '--transaction', '--dry-run', '--apply', '--json']));
      if (has(args, '--dry-run') && has(args, '--apply')) throw new StateError('--dry-run and --apply cannot be combined', EXIT_CODES.INPUT);
      const dryRun = has(args, '--dry-run') || !has(args, '--apply');
      value = recoverTransaction(planDir, {
        cwd,
        transactionId: valueFor(args, '--transaction', {required: true}),
        dryRun,
        apply: has(args, '--apply'),
      });
    } else if (action === 'checkpoint') {
      rejectUnknown(args, new Set(['--plan-dir', '--dry-run', '--apply', '--checkpoint', '--json']));
      if (has(args, '--dry-run') && has(args, '--apply')) throw new StateError('--dry-run and --apply cannot be combined', EXIT_CODES.INPUT);
      const apply = has(args, '--apply');
      value = env.PLANNING_DISABLED === '1'
        ? disabledResult(action, env)
        : checkpointState(planDir, {
          cwd,
          dryRun: !apply,
          apply,
          checkpointId: valueFor(args, '--checkpoint'),
        });
    } else if (action === 'reduce') {
      rejectUnknown(args, new Set(['--plan-dir', '--artifact', '--json']));
      value = reduceArtifact(planDir, {cwd, digest: valueFor(args, '--artifact', {required: true})});
    } else if (action === 'quote-verify') {
      rejectUnknown(args, new Set(['--plan-dir', '--input', '--json']));
      value = await verifyQuoteInput(planDir, {cwd, inputPath: valueFor(args, '--input', {required: true})});
    } else {
      throw new StateError(`unknown state action: ${action}`, EXIT_CODES.INPUT);
    }
    emit(value, {json: json || ['verify', 'doctor', 'recover', 'upgrade', 'checkpoint', 'reduce', 'quote-verify'].includes(action), stdout});
    if (value && value.valid === false) return EXIT_CODES.EVIDENCE;
    return value?.exit_code ?? EXIT_CODES.OK;
  } catch (error) {
    const code = error instanceof StateError ? error.code : EXIT_CODES.IO;
    const payload = {error: error.message, code};
    if (error instanceof StateError && error.details) payload.details = error.details;
    if (json) stderr.write(JSON.stringify(payload) + '\n');
    else stderr.write(`PlanWeft state: ${error.message}\n`);
    return code;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  process.exitCode = await main();
}
