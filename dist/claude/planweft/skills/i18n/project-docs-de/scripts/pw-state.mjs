import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const candidates = [
  path.resolve(here, '../state/cli.mjs'),
  path.resolve(here, '../lib/state/cli.mjs'),
  path.resolve(here, '../skills/project-docs/state/cli.mjs'),
  path.resolve(here, '../../../state/cli.mjs'),
  path.resolve(here, '../../../lib/state/cli.mjs'),
];
const target = candidates.find(file => fs.existsSync(file));
if (!target) {
  console.error('PlanWeft state CLI is not present beside this helper. Reinstall the complete package.');
  process.exitCode = 5;
} else {
  const {main} = await import(pathToFileURL(target).href);
  process.exitCode = await main(process.argv.slice(2));
}
