import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createInterface } from 'node:readline/promises';

export const HOSTS = ['codex', 'claude', 'pi', 'opencode', 'hermes', 'cursor', 'gemini', 'copilot', 'mastracode', 'kiro', 'continue', 'factory', 'codebuddy', 'agents'];
const catalogs = {codex: '.agents/plugins/marketplace.json', claude: '.claude-plugin/marketplace.json', cursor: '.cursor-plugin/marketplace.json', copilot: '.github/plugin/marketplace.json', factory: '.factory-plugin/marketplace.json', codebuddy: '.codebuddy-plugin/marketplace.json'};
const executables = {factory: 'droid', claude: 'claude', codebuddy: 'codebuddy', copilot: 'copilot', codex: 'codex'};
const hash = value => crypto.createHash('sha256').update(value).digest('hex');
const json = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const exists = file => { try { fs.lstatSync(file); return true; } catch (e) { if (e.code === 'ENOENT') return false; throw e; } };
function noLinks(file) {
  for (let p = path.resolve(file); ; p = path.dirname(p)) {
    if (exists(p) && fs.lstatSync(p).isSymbolicLink()) throw Error(`Symlink in managed parent: ${p}`);
    if (p === path.dirname(p)) break;
  }
}
function writeJSON(file, value) {
  noLinks(file); fs.mkdirSync(path.dirname(file), {recursive: true});
  const tmp = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(value, null, 2) + '\n', {flag: 'wx', mode: 0o600});
  fs.renameSync(tmp, file);
}
export function inventory(root, allowInternalLinks = false) {
  const result = {};
  function walk(dir) {
    for (const name of fs.readdirSync(dir).sort()) {
      const p = path.join(dir, name), st = fs.lstatSync(p);
      if (st.isSymbolicLink()) {
        const relative = path.relative(root, fs.realpathSync(p));
        if (!allowInternalLinks || relative.startsWith('..') || path.isAbsolute(relative)) throw Error(`Unexpected link inside owned copy: ${p}`);
        result[path.relative(root, p).split(path.sep).join('/')] = {link: fs.readlinkSync(p)}; continue;
      }
      if (st.isDirectory()) walk(p);
      else if (st.isFile()) result[path.relative(root, p).split(path.sep).join('/')] = {sha256: hash(fs.readFileSync(p)), executable: !!(st.mode & 0o111)};
      else throw Error(`Unsupported file type: ${p}`);
    }
  }
  if (fs.statSync(root).isFile()) return {file: hash(fs.readFileSync(root))};
  walk(root); return result;
}
const digest = root => hash(JSON.stringify(inventory(root)));
const modulesDigest = root => hash(JSON.stringify(inventory(root, true)));
export function parse(argv) {
  const [action = 'help', ...args] = argv;
  if (!['add', 'update', 'remove', 'list', 'doctor', 'help', '--help', '-h'].includes(action)) throw Error(`Unknown command: ${action}`);
  const o = {action, agents: [], scope: 'project', method: 'auto', skillOnly: false, dryRun: false};
  const seen = new Set();
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (['-a', '--agent', '--source'].includes(a)) {
      const v = args[++i]; if (!v || v.startsWith('-')) throw Error(`Missing value for ${a}`);
      if (a === '--source') { if (o.source) throw Error('Duplicate --source'); o.source = path.resolve(v); }
      else { if (!HOSTS.includes(v)) throw Error(`Unknown agent: ${v}`); if (o.agents.includes(v)) throw Error(`Duplicate agent: ${v}`); o.agents.push(v); }
    } else if (['--global', '-g', '--project'].includes(a)) {
      const scope = a === '--project' ? 'project' : 'global';
      if (seen.has('scope') && o.scope !== scope) throw Error('Choose --project or --global');
      seen.add('scope'); o.scope = scope;
    } else if (['--copy', '--symlink'].includes(a)) {
      const method = a.slice(2); if (seen.has('method') && o.method !== method) throw Error('Choose --copy or --symlink');
      seen.add('method'); o.method = method;
    } else if (a === '--skill-only') { o.skillOnly = true; seen.add('skillOnly'); }
    else if (a === '--dry-run') o.dryRun = true;
    else if (a === '--approve-pi-project') o.approvePiProject = true;
    else if (a === '--help' || a === '-h') o.action = 'help';
    else throw Error(`Unknown option: ${a}`);
  }
  o.explicit = [...seen];
  if (o.source && !['add', 'update'].includes(action)) throw Error('--source is only for add/update');
  return o;
}
export function command(argv, {cwd, env}) {
  // npm's Windows .cmd shim requires a shell. Invoke its JS entry instead.
  if (process.platform === 'win32' && argv[0] === 'npm') {
    const cli = env.npm_execpath?.endsWith('npm-cli.js') ? env.npm_execpath : path.join(path.dirname(process.execPath), 'node_modules/npm/bin/npm-cli.js');
    argv = [process.execPath, cli, ...argv.slice(1)];
  }
  const p = spawnSync(argv[0], argv.slice(1), {cwd, env, stdio: 'inherit', shell: false});
  if (p.error) throw p.error;
  if (p.status !== 0) throw Error(`${argv[0]} ${argv.slice(1, 3).join(' ')} failed (${p.status ?? p.signal})`);
}
export class Installer {
  constructor(options, {cwd = process.cwd(), env = process.env, packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..'), run = command, log = console.log} = {}) {
    this.o = options; this.cwd = fs.realpathSync(cwd); this.env = env; this.packageRoot = packageRoot; this.run = run; this.log = log;
    this.pkg = json(path.join(packageRoot, 'package.json'));
    if (this.pkg.name !== 'planweft' || !/^\d+\.\d+\.\d+(?:-[\w.-]+)?$/.test(this.pkg.version)) throw Error('Invalid PlanWeft package identity');
    this.home = env.HOME || env.USERPROFILE || os.homedir();
    const userData = env.PLANWEFT_HOME || path.join(env.XDG_DATA_HOME || (process.platform === 'win32' ? env.LOCALAPPDATA || path.join(this.home, 'AppData/Local') : path.join(this.home, '.local/share')), 'planweft');
    this.base = path.resolve(options.scope === 'global' ? userData : path.join(this.cwd, '.planweft'));
    this.statePath = path.join(this.base, 'installations.json');
    noLinks(this.statePath);
    this.state = exists(this.statePath) ? json(this.statePath) : {schema: 1, scope: options.scope, project: options.scope === 'project' ? this.cwd : null, agents: {}};
    if (this.state.schema !== 1 || this.state.scope !== options.scope || this.state.project !== (options.scope === 'project' ? this.cwd : null)) throw Error('Installation scope mismatch');
  }
  exec(argv) { this.run(argv, {cwd: this.cwd, env: this.env}); }
  save() { writeJSON(this.statePath, this.state); }
  hostRoot(host) {
    const user = this.o.scope === 'global', root = user ? this.home : this.cwd;
    const dirs = {codex: user ? this.env.CODEX_HOME || path.join(root, '.codex') : path.join(root, '.agents'), claude: user ? this.env.CLAUDE_CONFIG_DIR || path.join(root, '.claude') : path.join(root, '.claude'), pi: user ? this.env.PI_CODING_AGENT_DIR || path.join(root, '.pi/agent') : path.join(root, '.pi'), opencode: user ? path.join(this.env.XDG_CONFIG_HOME || path.join(root, '.config'), 'opencode') : path.join(root, '.opencode'), copilot: path.join(root, '.copilot'), factory: path.join(root, '.factory'), mastracode: path.join(root, '.mastracode'), agents: path.join(root, '.agents'), hermes: user ? this.env.HERMES_HOME || path.join(root, '.hermes') : path.join(root, '.hermes')};
    return path.resolve(dirs[host] || path.join(root, `.${host}`));
  }
  catalog(host) { return `planweft-cli-${host}-${hash(this.base).slice(0, 16)}`; }
  resolveOptions(host) {
    const old = this.state.agents[host];
    return {skillOnly: this.o.explicit.includes('skillOnly') ? this.o.skillOnly : old?.skillOnly ?? this.o.skillOnly, method: this.o.explicit.includes('method') ? this.o.method : old?.requestedMethod ?? this.o.method};
  }
  components(host, root, opt) {
    const out = this.hostRoot(host), skill = path.join(out, 'skills/project-docs');
    if (opt.skillOnly || ['agents', 'continue'].includes(host)) return [{source: path.join(root, 'dist/opencode/planweft/skills/project-docs'), target: skill}];
    if (host === 'opencode') return [{source: path.join(root, 'dist/opencode/planweft/skills/project-docs'), target: skill}, {text: `// Managed by PlanWeft; update through its installer.\nexport { PlanningWithFiles } from ${JSON.stringify(pathToFileURL(path.join(root, 'dist/opencode/planweft/dist/index.js')).href)};\n`, target: path.join(out, 'plugins/planweft.ts')}];
    return [];
  }
  assertOwned(item) {
    noLinks(path.dirname(item.target));
    if (!exists(item.target)) throw Error(`Owned component missing: ${item.target}`);
    const st = fs.lstatSync(item.target);
    if (item.method === 'symlink') {
      if (!st.isSymbolicLink() || path.resolve(path.dirname(item.target), fs.readlinkSync(item.target)) !== item.source) throw Error(`Link changed by user: ${item.target}`);
      if (!exists(item.source) || digest(item.source) !== item.sha256) throw Error(`Linked resource changed: ${item.source}`);
    } else if (st.isSymbolicLink() || digest(item.target) !== item.sha256) throw Error(`User changes preserved: ${item.target}`);
  }
  assertRecord(host, rec) {
    // Lock files are local data, not authority to delete arbitrary paths.
    const allowed = new Set(this.components(host, rec.packageRoot, rec).map(x => x.target));
    for (const item of rec.components || []) {
      if (!allowed.has(item.target)) throw Error('Unexpected managed target in installation record');
      if (!(item.removing && !exists(item.target))) this.assertOwned(item);
    }
    this.checkStore(rec.packageRoot);
    if (!path.resolve(rec.packageRoot).startsWith(path.join(this.base, 'versions') + path.sep)) throw Error('Unexpected package location');
  }
  checkStore(root) {
    const target = path.resolve(root, '../..');
    if (!target.startsWith(path.join(this.base, 'versions') + path.sep)) throw Error('Unexpected package location');
    noLinks(target);
    const receipt = json(path.join(target, 'receipt.json'));
    if (modulesDigest(path.join(target, 'node_modules')) !== receipt.modulesSha256 || hash(fs.readFileSync(path.join(target, 'package-lock.json'))) !== receipt.lockSha256) throw Error('Stored package integrity mismatch');
  }
  detectDuplicates(host, old) {
    const root = this.hostRoot(host);
    for (const name of ['planning-with-files', 'program-design']) {
      for (const sub of ['skills', 'plugins']) if (exists(path.join(root, sub, name))) throw Error(`Other planning installation detected: ${path.join(root, sub, name)}`);
    }
    // Read known native registration surfaces without editing foreign settings.
    const checks = host === 'pi' ? [path.join(root, 'settings.json')] : host === 'opencode' ? [path.join(root, 'opencode.json'), path.join(root, 'opencode.jsonc'), path.join(this.cwd, 'opencode.json'), path.join(this.cwd, 'opencode.jsonc')] : host === 'claude' ? [path.join(root, 'settings.json'), path.join(this.env.CLAUDE_CONFIG_DIR || path.join(this.home, '.claude'), 'plugins/installed_plugins.json')] : host === 'codex' ? [path.join(root, 'config.toml')] : [];
    for (const file of checks) {
      if (!exists(file)) continue;
      let text = fs.readFileSync(file, 'utf8');
      if (host === 'claude' && path.basename(file) === 'installed_plugins.json') {
        const native = JSON.parse(text);
        text = JSON.stringify(Object.fromEntries(Object.entries(native.plugins || {}).filter(([id, records]) =>
          id !== old?.nativeId && records.some(r => r.scope === 'user' || !r.projectPath || path.resolve(r.projectPath) === this.cwd))));
      }
      if (old?.nativeId) text = text.split(old.nativeId).join('');
      if (old?.nativeSource) text = text.split(old.nativeSource).join('');
      text = text.split(`${old?.catalog || this.catalog(host)}`).join('');
      if (/planning-with-files|program-design|npm:planweft|["']planweft@|planweft-cli-/.test(text)) throw Error(`Another planning registration may be active in ${file}; inspect it before installing`);
    }
  }
  preflight(host) {
    const old = this.state.agents[host], opt = this.resolveOptions(host);
    if (old) {
      this.assertRecord(host, old);
      if (old.skillOnly !== opt.skillOnly) throw Error('Remove the existing installation before switching full/skill-only mode');
      if (host === 'gemini' && !opt.skillOnly) throw Error('Gemini currently requires remove then add to replace its native source');
    }
    this.detectDuplicates(host, old);
    if (!opt.skillOnly && this.o.scope === 'project' && ['codex', 'copilot', 'gemini', 'hermes'].includes(host)) throw Error(`${host} full plugin installation has no supported project scope; select --global or --skill-only`);
    if (!opt.skillOnly && host === 'hermes') throw Error('Hermes full install is blocked by the default scanner; use --skill-only or inspect INSTALL. No scanner bypass is provided.');
    for (const c of this.components(host, this.packageRoot, opt)) {
      noLinks(path.dirname(c.target));
      if (exists(c.target) && !(old?.components || []).some(x => x.target === c.target)) throw Error(`Foreign target preserved: ${c.target}`);
    }
    return opt;
  }
  ensurePackage() {
    const target = path.join(this.base, 'versions', this.pkg.version), root = path.join(target, 'node_modules/planweft');
    noLinks(target);
    if (exists(target)) {
      const receipt = json(path.join(target, 'receipt.json'));
      if (receipt.version !== this.pkg.version || modulesDigest(path.join(target, 'node_modules')) !== receipt.modulesSha256 || hash(fs.readFileSync(path.join(target, 'package-lock.json'))) !== receipt.lockSha256) throw Error('Stored package integrity mismatch');
      return root;
    }
    fs.mkdirSync(path.dirname(target), {recursive: true});
    const staging = fs.mkdtempSync(path.join(path.dirname(target), '.install-'));
    try {
      const source = this.o.source || `planweft@${this.pkg.version}`;
      if (this.o.source && (!fs.statSync(source).isFile() || !source.endsWith('.tgz'))) throw Error('--source must be a local npm .tgz archive');
      this.exec(['npm', 'install', '--prefix', staging, '--ignore-scripts', '--omit=dev', '--no-audit', '--no-fund', '--package-lock=true', '--registry=https://registry.npmjs.org', source]);
      const unpacked = path.join(staging, 'node_modules/planweft'), pkg = json(path.join(unpacked, 'package.json'));
      if (pkg.name !== this.pkg.name || pkg.version !== this.pkg.version) throw Error('Installed archive identity/version differs from this CLI');
      const receipt = {version: pkg.version, source, modulesSha256: modulesDigest(path.join(staging, 'node_modules')), lockSha256: hash(fs.readFileSync(path.join(staging, 'package-lock.json')))};
      writeJSON(path.join(staging, 'receipt.json'), receipt);
      fs.renameSync(staging, target); return root;
    } catch (e) { fs.rmSync(staging, {recursive: true, force: true}); throw e; }
  }
  place(c, method) {
    fs.mkdirSync(path.dirname(c.target), {recursive: true});
    if (c.text !== undefined) { fs.writeFileSync(c.target, c.text, {flag: 'wx'}); return {...c, method: 'copy', sha256: digest(c.target)}; }
    if (method !== 'copy') {
      try {
        fs.symlinkSync(process.platform === 'win32' ? c.source : path.relative(path.dirname(c.target), c.source), c.target, process.platform === 'win32' ? 'junction' : 'dir');
        return {...c, method: 'symlink', sha256: digest(c.source)};
      } catch (e) { if (method === 'symlink') throw e; this.log(`Link unavailable; copying ${c.target}: ${e.code}`); }
    }
    const staging = fs.mkdtempSync(path.join(path.dirname(c.target), '.planweft-component-'));
    try {
      const item = path.join(staging, 'item');
      fs.cpSync(c.source, item, {recursive: true, errorOnExist: true, force: false});
      const sha256 = digest(item);
      if (exists(c.target)) throw Error(`Foreign target appeared during copy: ${c.target}`);
      fs.renameSync(item, c.target); return {...c, method: 'copy', sha256};
    } finally { fs.rmSync(staging, {recursive: true, force: true}); }
  }
  step(rec, name, fn) {
    rec.steps[name] = 'in-progress'; this.save();
    try { fn(); rec.steps[name] = 'done'; this.save(); }
    catch (e) { rec.steps[name] = 'failed'; rec.error = e.message; this.save(); throw e; }
  }
  piScope() { return this.o.scope === 'project' ? ['-l', ...(this.o.approvePiProject ? ['--approve'] : [])] : []; }
  native(host, rec, old) {
    if (rec.skillOnly || ['agents', 'continue', 'opencode'].includes(host)) return;
    if (host === 'pi') {
      rec.nativeSource = path.join(rec.packageRoot, 'dist/pi/planweft'); this.save();
      if (old?.nativeSource && old.nativeSource !== rec.nativeSource) this.step(rec, 'remove-old-native', () => this.exec(['pi', 'remove', ...this.piScope(), old.nativeSource]));
      try { this.step(rec, 'native-install', () => this.exec(['pi', 'install', ...this.piScope(), rec.nativeSource])); }
      catch (error) {
        if (old?.nativeSource && rec.steps['remove-old-native'] === 'done') {
          this.step(rec, 'native-restore', () => this.exec(['pi', 'install', ...this.piScope(), old.nativeSource]));
          rec.nativeSource = old.nativeSource; rec.actualVersion = old.version; this.save();
        }
        throw error;
      }
      return;
    }
    if (host === 'gemini') {
      rec.nativeSource = path.join(rec.packageRoot, 'dist/gemini/planweft'); this.save();
      if (old) throw Error('Gemini CLI-managed replacement requires remove then add; project records are preserved');
      this.step(rec, 'native-install', () => this.exec(['gemini', 'extensions', 'install', rec.nativeSource])); return;
    }
    const cli = executables[host];
    if (!cli) { rec.status = 'manual'; rec.instructions = path.join(rec.packageRoot, `dist/${host}/planweft/INSTALL.md`); this.save(); return; }
    rec.catalog = this.catalog(host); rec.nativeId = `planweft@${rec.catalog}`;
    const registry = path.join(this.base, 'registries', host);
    noLinks(registry);
    const catalogFile = path.join(registry, catalogs[host]);
    let payload = json(path.join(rec.packageRoot, catalogs[host]));
    payload.name = rec.catalog;
    // Native managers receive an ordinary self-contained directory, not an
    // escaping source path or a symlink that may be rejected by their verifier.
    if (exists(catalogFile) && (!old?.registrySha256 || hash(fs.readFileSync(catalogFile)) !== old.registrySha256)) throw Error('Foreign or user-modified CLI marketplace preserved');
    const payloadDir = path.join(registry, 'payload');
    if (exists(payloadDir) && (!old?.payloadSha256 || digest(payloadDir) !== old.payloadSha256)) throw Error('User-modified marketplace payload preserved');
    fs.mkdirSync(registry, {recursive: true});
    const staging = fs.mkdtempSync(path.join(registry, '.payload-'));
    const backup = path.join(registry, '.payload-backup');
    if (exists(backup)) { fs.rmdirSync(staging); throw Error('Interrupted registry replacement requires inspection of .payload-backup'); }
    try {
      fs.cpSync(path.join(rec.packageRoot, `dist/${host}/planweft`), staging, {recursive: true});
      payload.plugins = payload.plugins.filter(x => x.name === 'planweft');
      payload.plugins[0].source = host === 'codex' ? {source: 'local', path: './payload'} : './payload';
      if (exists(payloadDir)) fs.renameSync(payloadDir, backup);
      fs.renameSync(staging, payloadDir);
      writeJSON(catalogFile, payload);
      rec.registrySha256 = hash(fs.readFileSync(catalogFile)); rec.payloadSha256 = digest(payloadDir); this.save();
      if (exists(backup)) fs.rmSync(backup, {recursive: true});
    } catch (error) {
      fs.rmSync(staging, {recursive: true, force: true});
      if (exists(backup)) { fs.rmSync(payloadDir, {recursive: true, force: true}); fs.renameSync(backup, payloadDir); }
      throw error;
    }
    if (!old?.steps?.['marketplace-add'] || old.steps['marketplace-add'] !== 'done') this.step(rec, 'marketplace-add', () => this.exec([cli, 'plugin', 'marketplace', 'add', registry]));
    else { rec.steps['marketplace-add'] = 'done'; this.step(rec, 'marketplace-update', () => this.exec([cli, 'plugin', 'marketplace', 'update', rec.catalog])); }
    const scope = ['claude', 'factory', 'codebuddy'].includes(host) ? ['--scope', this.o.scope === 'global' ? 'user' : 'project'] : [];
    this.step(rec, 'native-install', () => this.exec([cli, 'plugin', host === 'codex' ? 'add' : old?.steps?.['native-install'] === 'done' ? 'update' : 'install', rec.nativeId, ...scope]));
  }
  install(host, opt, root) {
    const old = this.state.agents[host];
    const rec = {...old, error: null, version: this.pkg.version, packageRoot: root, scope: this.o.scope, skillOnly: opt.skillOnly, requestedMethod: opt.method, status: 'installing', components: old?.components || [], steps: {...old?.steps}, previous: old?.previous || old || null};
    this.state.agents[host] = rec; this.save();
    try {
      this.native(host, rec, old);
      const backups = [];
      rec.components = [];
      try {
        for (const item of old?.components || []) {
          this.assertOwned(item); const backup = `${item.target}.planweft-backup-${process.pid}`;
          if (exists(backup)) throw Error(`Backup already exists: ${backup}`);
          fs.renameSync(item.target, backup); backups.push({item, backup});
        }
        for (const c of this.components(host, root, opt)) { rec.components.push(this.place(c, opt.method)); this.save(); }
      } catch (e) {
        rec.status = 'removing'; this.save();
    for (const c of [...rec.components]) {
      if (!(c.removing && !exists(c.target))) {
        this.assertOwned(c); c.removing = true; this.save();
        fs.rmSync(c.target, {recursive: true});
      }
      rec.components = rec.components.filter(item => item !== c); this.save();
    }
        rec.components = [];
        for (const {item, backup} of backups) fs.renameSync(backup, item.target);
        rec.components = old?.components || []; throw e;
      }
      for (const {backup} of backups) fs.rmSync(backup, {recursive: true});
      rec.status = rec.status === 'manual' ? 'manual' : 'installed'; rec.previous = null; this.save();
      this.log(`${host}: ${rec.status}, ${rec.version}, ${this.o.scope}${rec.instructions ? `; follow ${rec.instructions}` : ''}`);
    } catch (e) { rec.status = 'failed'; rec.error = e.message; this.save(); throw e; }
  }
  remove(host) {
    const rec = this.state.agents[host]; if (!rec) throw Error(`${host} is not managed in this scope`);
    this.assertRecord(host, rec);
    const registry = path.join(this.base, 'registries', host);
    const catalogFile = catalogs[host] ? path.join(registry, catalogs[host]) : null;
    const payloadDir = path.join(registry, 'payload');
    if (rec.registrySha256 && exists(catalogFile) && hash(fs.readFileSync(catalogFile)) !== rec.registrySha256) throw Error('User-modified CLI marketplace preserved');
    if (rec.payloadSha256 && exists(payloadDir) && digest(payloadDir) !== rec.payloadSha256) throw Error('User-modified marketplace payload preserved');
    const scope = this.o.scope === 'global' ? 'user' : 'project';
    if (['done', 'failed', 'in-progress'].includes(rec.steps['native-install'])) {
      const cli = executables[host];
      const args = host === 'pi' ? ['pi', 'remove', ...this.piScope(), rec.nativeSource] : host === 'gemini' ? ['gemini', 'extensions', 'uninstall', 'planweft'] : [cli, 'plugin', host === 'codex' ? 'remove' : 'uninstall', rec.nativeId, ...(['claude', 'factory', 'codebuddy'].includes(host) ? ['--scope', scope] : [])];
      this.step(rec, 'native-remove', () => this.exec(args)); rec.steps['native-install'] = 'removed'; this.save();
    }
    if (rec.steps['marketplace-add'] === 'done') { this.step(rec, 'marketplace-remove', () => this.exec([executables[host], 'plugin', 'marketplace', 'remove', rec.catalog])); rec.steps['marketplace-add'] = 'removed'; this.save(); }
    rec.status = 'removing'; this.save();
    for (const c of [...rec.components]) {
      if (!(c.removing && !exists(c.target))) {
        this.assertOwned(c); c.removing = true; this.save();
        fs.rmSync(c.target, {recursive: true});
      }
      rec.components = rec.components.filter(item => item !== c); this.save();
    }
    if (rec.payloadSha256 && exists(payloadDir)) fs.rmSync(payloadDir, {recursive: true});
    if (rec.registrySha256 && exists(catalogFile)) fs.unlinkSync(catalogFile);
    delete this.state.agents[host]; this.save(); this.log(`${host}: removed; version store retained for rollback`);
  }
  async execute() {
    const o = this.o;
    if (['help', '--help', '-h'].includes(o.action)) { this.log('planweft <add|update|remove|list|doctor> -a HOST [-a HOST] [--project|--global] [--skill-only] [--copy|--symlink] [--dry-run] [--source package.tgz] [--approve-pi-project]\nHosts: ' + HOSTS.join(', ') + '\nDefault: project scope, full native integration, symlink with reported copy fallback. Update uses this CLI version.'); return 0; }
    if (['list', 'doctor'].includes(o.action)) {
      let failures = 0;
      for (const [host, rec] of Object.entries(this.state.agents)) {
        if (o.agents.length && !o.agents.includes(host)) continue;
        this.log(`${host}: ${rec.status} ${rec.version} ${rec.scope}`);
        if (o.action === 'doctor') try { this.assertRecord(host, rec); this.detectDuplicates(host, rec); if (rec.status !== 'installed') throw Error(rec.error || 'Manual completion required'); } catch (e) { failures++; this.log(`${host}: ${e.message}`); }
      }
      return failures ? 1 : 0;
    }
    if (!o.agents.length) {
      if (!process.stdin.isTTY) throw Error('Specify -a/--agent in non-interactive use');
      const rl = createInterface({input: process.stdin, output: process.stdout});
      try { o.agents = (await rl.question(`Agents (${HOSTS.join(', ')}): `)).trim().split(/[ ,]+/); } finally { rl.close(); }
      if (!o.agents.length || o.agents.some(h => !HOSTS.includes(h)) || new Set(o.agents).size !== o.agents.length) throw Error('Invalid agent selection');
    }
    // Preflight every requested host before any installation side effect.
    const opts = {};
    for (const host of o.agents) {
      if (o.action === 'remove') { const rec = this.state.agents[host]; if (!rec) throw Error(`${host} is not managed`); this.assertRecord(host, rec); }
      else { if (o.action === 'update' && !this.state.agents[host]) throw Error(`${host} is not managed; use add`); opts[host] = this.preflight(host); }
    }
    if (o.dryRun) { this.log(JSON.stringify({action: o.action, version: this.pkg.version, agents: o.agents, scope: o.scope, base: this.base, options: opts}, null, 2)); return 0; }
    noLinks(this.base); fs.mkdirSync(this.base, {recursive: true});
    const lock = path.join(this.base, '.operation-lock');
    try { fs.mkdirSync(lock); } catch (e) { if (e.code === 'EEXIST') throw Error('Another operation or interrupted operation owns .operation-lock; inspect before removing it'); throw e; }
    let failures = 0;
    try {
      const root = o.action === 'remove' ? null : this.ensurePackage();
      for (const host of o.agents) try { if (o.action === 'remove') this.remove(host); else this.install(host, opts[host], root); } catch (e) { failures++; this.log(`${host}: FAILED: ${e.message}`); }
    } finally { fs.rmdirSync(lock); }
    return failures ? 1 : 0;
  }
}
