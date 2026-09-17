#!/usr/bin/env node

try {
  const argv = process.argv.slice(2);
  if (argv[0] === 'state') {
    const {main} = await import('../lib/state/cli.mjs');
    process.exitCode = await main(argv.slice(1));
  } else {
    const {Installer, parse} = await import('../lib/installer.mjs');
    process.exitCode = await new Installer(parse(argv)).execute();
  }
} catch (error) {
  console.error(`PlanWeft: ${error.message}`);
  process.exitCode = 1;
}
