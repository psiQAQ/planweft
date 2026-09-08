import path from 'node:path';
import {fileURLToPath} from 'node:url';
import * as filesystem from '@deepseek-ai/dsh-skill-filesystem';
import * as hooks from '@deepseek-ai/dsh-hooks-claude-code';
import {hookShell} from './hook-shell.mjs';

export const name = 'planweft';
export const inject = ['skills', ...hooks.inject];
const root = path.dirname(fileURLToPath(import.meta.url));

export function apply(ctx) {
  ctx.plugin(filesystem, {providerName: 'planweft', includeDefaultRoots: false,
    customSkillDirs: [path.join(root, 'skills')], watch: false});
  if (process.env.PLANNING_DISABLED === '1') return;
  // Package assets use absolute paths. Omit projectDir so each session keeps
  // its own workspace, including different projects in one web profile.
  const shell = ctx.shell;
  const scoped = ctx.isolate('shell');
  // The provider must own a fiber in this scope: outer-fiber activation does
  // not notify dependencies waiting on the isolated shell service.
  scoped.plugin({name: 'planweft-hook-runtime', apply(hookCtx) {
    hookCtx.provide('shell', hookShell(shell));
    hookCtx.plugin(hooks, {configPath: path.join(root, 'hooks/hooks.json'), pluginRoot: root});
  }});
}
