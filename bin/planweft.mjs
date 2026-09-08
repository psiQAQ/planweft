#!/usr/bin/env node
import { Installer, parse } from '../lib/installer.mjs';
try { process.exitCode = await new Installer(parse(process.argv.slice(2))).execute(); }
catch (error) { console.error(`PlanWeft: ${error.message}`); process.exitCode = 1; }
