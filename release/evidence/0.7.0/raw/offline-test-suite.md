# 0.7.0 offline test suite

Passed on the P1 branch after generated outputs were rebuilt:

```text
python3 scripts/build-plugin.py --verify       Passed
npm test                                       Passed
python3 -m unittest discover -s tests -p 'test_*.py'  Passed
python3 -m unittest tests.test_state_p1_release_gate tests.test_state_evidence  Passed
git diff --check                               Passed
```

The Python discovery result was `Ran 365 tests in 138.318s`, `OK (skipped=1)`. The npm suite passed installer, DSH hook, P0 state, P1 state, and P1 ablation tests. The single skipped Python case is the existing Windows-only Pi path.
