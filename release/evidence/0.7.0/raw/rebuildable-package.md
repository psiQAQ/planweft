# 0.7.0 rebuildable package

The package was rebuilt from the repository source with the builder and packed with npm. The builder reported 15 host packages and zero generated differences on the subsequent `--verify` run.

Commands:

```text
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
npm pack --pack-destination <temporary-directory> --json
```

Candidate archive: `planweft-0.7.0.tgz`

- bytes: `6682632`
- SHA-256: `a0461b75bc3e263fae444711ae68044361b5493fd00b52e58649d71cb83b7a73`
- archive identity: `planweft@0.7.0`
- generated outputs are builder-owned; `dist/**` was not hand-edited.
