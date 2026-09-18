# 0.7.0 rebuildable package

The package was rebuilt from the repository source with the builder and packed with the pinned GitHub runner toolchain (Node 24.20.0/npm 11.11.0). The builder reported 15 host packages and zero generated differences on the subsequent `--verify` run.

Commands:

```text
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
npm pack --pack-destination <temporary-directory> --json
```

Candidate archive: `planweft-0.7.0.tgz` from candidate workflow `35294402236`

- bytes: `6707526`
- SHA-256: `ddbdc57572341aa912885102b36f8c0e13ea4e07312930380e74fbe790445745`
- archive identity: `planweft@0.7.0`
- generated outputs are builder-owned; `dist/**` was not hand-edited.
