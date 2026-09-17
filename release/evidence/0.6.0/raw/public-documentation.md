# 0.6.0 public documentation evidence

The bilingual README and installation pages identify `0.6.0`. The host page links the versioned `support-policy-0.6.0.json` and states that deterministic P0 evidence does not prove real host/model behavior. The changelog and release guide describe the state commands, evidence boundary, and `Not Run` limits.

Result: `python3 -m unittest tests.test_public_docs` — 12 passed; `python3 scripts/build-plugin.py --verify` — public-docs differences 0.
