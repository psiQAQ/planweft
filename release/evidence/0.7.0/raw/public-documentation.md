# 0.7.0 public documentation

Builder-generated public documentation and host mirrors describe the P1 commands:

```text
planweft state upgrade
planweft state checkpoint --dry-run
planweft state checkpoint --apply
planweft state reduce --artifact SHA256
planweft state quote-verify --input FILE
```

The documentation states that checkpoint preserves unresolved work, reducer output is source facts rather than interpretation, remote reducer is disabled, and real Agent/model and tokens/cost measurements are `Not Run`. `docs/design-references.md`, `docs/innovations.md`, SPEC-0009, ADR-0013, and the release policy record provenance and limits.
