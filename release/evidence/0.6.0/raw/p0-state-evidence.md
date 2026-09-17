# 0.6.0 P0 state evidence

The Node fixture suite covers the fixed S01–S13 offline boundary: explicit initialization and disabled mode, streamed artifacts, quote verification, integrity and idempotency failures, owner locks, journal recovery, plan/path boundaries, doctor diagnostics, CRLF/binary/empty/large artifacts, ten fixed interruption seeds, moved projects, local-only evidence, and package replacement isolation.

The shared source is `overlays/planweft/state/`; generated copies are checked by `tests.test_state_evidence` and `build-plugin.py --verify`. The implementation does not execute command strings, replace host tools, enable a remote reducer, or change the default advisory Hook.

Result: `node --test tests/state-evidence.test.mjs` — 12 passed; generated-state Python checks — 2 passed.
