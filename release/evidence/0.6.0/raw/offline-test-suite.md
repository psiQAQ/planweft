# 0.6.0 deterministic offline test evidence

Passed commands on the release source:

- `python3 scripts/build-plugin.py --verify`: 15 hosts, shared state, mirror, manifest, marketplaces and public docs; zero differences.
- `npm test`: 124 passed, 1 skipped.
- `python3 -m unittest discover -s tests -p 'test_*.py'`: 362 tests, 1 skipped, `OK`.
- `python3 -m unittest tests.test_public_docs tests.test_state_evidence tests.test_state_release_gate`: Passed.
- `git diff --check`: Passed.
- `node --test tests/state-evidence.test.mjs`: 12 passed.

The one initial workflow-contract failure was corrected by updating the test to cover both the historical 0.5.x path and the new 0.6.0 gate; the final full run is the 362-test result above.
