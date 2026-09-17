# 0.6.0 isolated package install evidence

- Local archive: `/tmp/planweft-release-0.6.0-20260917/npm/planweft-0.6.0.tgz`
- Installation: `npm install --ignore-scripts --no-audit --no-fund --prefix /tmp/planweft-isolated-0.6.0-20260917 <archive>`
- Readback: installed package reports `planweft@0.6.0`.
- CLI readback: `node .../node_modules/planweft/bin/planweft.mjs state --help` listed all six frozen state interfaces and the data-only command boundary.
- Result: Passed. No model, Agent session, or cost measurement was used.
