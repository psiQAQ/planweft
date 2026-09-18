# REV-0022: SoL-Pi 0.7.0 promotion completion

## Scope

This is a deterministic post-promotion readback of the P1 release. It does not call a real Agent/model and does not claim tokens/cost measurement; those dimensions remain `Not Run` by explicit scope.

## Evidence

| Check | Result |
| --- | --- |
| Promotion workflow `35307560099` | Passed |
| `npm whoami` preflight | Passed |
| Candidate archive and P1 gate | Passed |
| Stable `dist-tag` mutation | Passed |
| Registry tags | `latest=0.7.0`, `next=0.7.0` |
| Registry archive identity | 6,707,526 bytes; SHA-256 `ddbdc57572341aa912885102b36f8c0e13ea4e07312930380e74fbe790445745` |
| Annotated tag and GitHub Release | Passed; `v0.7.0` remains non-draft and non-prerelease |
| Real Agent/model, tokens/cost, different-Agent continuation | Not Run |

The preceding `EOTP` attempts are retained unchanged as historical failure evidence. The final public state is recorded in [`stable-promotion-readback.md`](../../release/evidence/0.7.0/raw/stable-promotion-readback.md).

## Decision

Passed for the deterministic P1/R1 release boundary. The npm package, stable tags, source tag, and GitHub Release are publicly readable and match the reviewed release identity.
