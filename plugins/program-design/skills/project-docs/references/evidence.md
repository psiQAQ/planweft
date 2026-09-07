# Evidence and ordinary records

Read for a new or substantially changed design, or when a task needs an evidence record. Follow project conventions first.

| Record | Minimum useful content |
| --- | --- |
| Specification | Problem, desired behavior, boundaries and observable acceptance criteria |
| Plan | Goal, completed work, next action, blockers and evidence links |
| ADR | Significant choice, alternatives, reasons, consequences and decision status |
| Reproduction | Environment, steps, expected result, observed result and verification limits |

Use a single existing record when sufficient. An ADR is for a meaningful choice, not every edit. Keep historical observations dated; append later corrections rather than rewriting past results.

## Cite designs

Use the existing reference ledger. If a substantive design has no place for its basis, create `docs/design-references.md`: one row per affected design file, with problem/design point, requirement or source and exact location, borrowed idea and local difference, related verification/decision and review status. Shared sources can support multiple rows.

Explicit user requirements are valid sources. Third-party files point to upstream; generated files point to their generator. Review reports cite actual review evidence without creating circular review requirements.

Compare relevant precedents and the simplest adequate alternative for important choices. Open the actual section or implementation; link counts, popularity and reachability do not prove support. Local references retain attribution, original link, access date, license and scope. Save a short summary unless the license permits full reproduction or translation.

## Search before a new mechanism

Search official documentation, projects and concrete implementations for mechanisms not covered by existing evidence. Record actual date, queries, scope and close matches. Add useful precedent to the local reference collection and cite it.

If no adequate precedent is found, use the existing innovation record or create `docs/innovations.md`. State "not found in this search", why new design remains necessary, minimum validation and an exit condition. Do not claim originality or create placeholders. If search is unavailable, record Not Run and leave evidence-dependent decisions pending; never invent search results.

## Independent evidence review

For new or substantially changed designs, citations or innovation entries, delegate a bounded review to a separate agent when available. Ask it to open sources and check whether they support the design; pinned commit/file agreement; distinctions between inspiration, upstream implementation and local validation; simpler alternatives; and search/validation/exit conditions for unsupported candidates.

Save scope, inspected revision or workspace state, findings and disposition in existing review records (default `docs/reviews`). The main agent checks and resolves findings; only re-review affected parts. Fresh-reader comprehension differs from source audit. Without delegation, record independent review Not Run and continue work that does not depend on approval. Self-review is not independent review.
