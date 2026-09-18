# 0.7.0 isolated install

The exact local candidate archive was installed into a new temporary prefix with scripts disabled:

```text
npm install --ignore-scripts --no-audit --no-fund --prefix <temporary-prefix> planweft-0.7.0.tgz
node <temporary-prefix>/node_modules/planweft/bin/planweft.mjs state --help
node -p "require('<temporary-prefix>/node_modules/planweft/package.json').version"
```

Observed:

- installed version: `0.7.0`;
- state help exposed `init`, `upgrade`, `record`, `verify`, `recall`, `doctor`, `recover`, `checkpoint`, `reduce`, and `quote-verify`;
- the package did not contain task-side `.planweft-state/` data;
- npm emitted an existing local Node 22.22.1/`ini@7.0.0` engine warning but installation completed successfully. CI uses the pinned Node 24.20.0/npm 11.11.0 toolchain.
