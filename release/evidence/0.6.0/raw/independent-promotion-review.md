# 0.6.0 deterministic promotion review

This is an independent file/registry/packaging review of the promotion boundary. It intentionally does not call a second Agent/model and does not claim real Agent, model, token, or cost validation.

| Review item | Result |
| --- | --- |
| P0 evidence policy and pre-publication attachments | Passed |
| Candidate workflow `35242327786` and source `master@5c23fa3` | Passed |
| Archive identity, bytes, SHA-256, SHA-512 integrity, and npm metadata | Passed |
| `next=0.6.0` while stable `latest=0.5.1` remained protected before promotion | Passed |
| Isolated install and state command readback from the public tarball | Passed |
| Real Agent/model regression and tokens/cost | Not Run by explicit scope |

Decision: the deterministic P0 artifact is eligible for stable npm promotion. This review is limited to source, generated artifacts, offline evidence, registry metadata, and package installation; it does not extend the support claim beyond that boundary.

## Post-promotion follow-up

The subsequent public readback reports `latest=0.6.0` and `next=0.6.0`, with the same archive identity, integrity, registry signatures, and SLSA provenance. The detailed result is attached as `stable-promotion-readback.md`. This follow-up does not rewrite the pre-promotion state; the earlier failed `E401` attempt remains in its separate historical attachment.
