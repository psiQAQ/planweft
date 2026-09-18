# 0.7.0 offline ablation

`node tests/state-p1-ablation.test.mjs` passed with four deterministic local variants. The fixture recorded active-document bytes, local helper calls, recall calls, reducer facts, wall time, and the unavailable dimensions explicitly.

| Variant | Active bytes before → after | Saved bytes | Local tool calls | Recall calls | Reducer facts | Tokens | Cost |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| P0 | 3277 → 3277 | 0 | 0 | 0 | 0 | Not Run | Not Run |
| P0+checkpoint | 3277 → 2803 | 474 | 1 | 0 | 0 | Not Run | Not Run |
| P0+reducer | 3277 → 3277 | 0 | 1 | 0 | 4 | Not Run | Not Run |
| P0+checkpoint+reducer | 3277 → 2803 | 474 | 2 | 0 | 2 | Not Run | Not Run |

The fixture measures local deterministic work only; it is not a model quality or token/cost experiment.
