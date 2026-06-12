# AI-Oriented ADR Template

This is the durable artifact the whole skill exists to produce: an Architecture Decision Record written to
be **executable organizational memory**. A future AI agent — with no prior context, in a fresh window —
must be able to read one of these and generate conformant code from it alone. That requirement drives every
part of the format below: machine-parseable frontmatter, canonical *and* rejected code exemplars, file-glob
scope, and an unambiguous directive block.

Fill the template literally. Keep the prose reasoning for humans; keep the directive block terse for agents.
One ADR governs **one concept**. Number them sequentially within the org's `/docs/adr` convention.

---

```markdown
---
id: ADR-0042
title: Canonical <concept> pattern
status: accepted            # proposed | accepted | superseded-by:ADR-XXXX | deprecated
date: 2026-06-12
scope:                      # file globs this ADR governs — agents match against these
  - "src/modules/**/infrastructure/*.repository.ts"
concept: repository-access-pattern
supersedes: []              # prior ADR ids this replaces
enforced_by:                # how conformance is checked; "review" if no automated gate
  - dependency-cruiser:no-orm-repo-in-service
  - eslint:custom/repository-return-type
convergence:
  canonical_count: 14       # files already conformant at time of writing
  deviating_count: 25       # files needing migration
  strategy: migrate-on-touch
---

## Context

<Why this decision exists. The concept being governed, the divergence that was found, and the frequencies
that drove the choice. State the scores or the headline numbers — "Variant B (custom repository over
dataSource.query) scored highest on prevalence among new modules and AI-legibility." Two short paragraphs
maximum. This is the "why" that stops a future agent from re-litigating the decision.>

## Decision

<The single canonical pattern, stated in one sentence, then shown in code. The code exemplar is
non-negotiable — agents pattern-match on it.>

### Canonical form

\```typescript
// THE default. Generate new code in exactly this shape.
export class OrderRepository {
  constructor(private readonly dataSource: DataSource) {}

  async findById(orderId: string): Promise<Order | null> {
    const rows = await this.dataSource.query(
      `select * from orders_order where id = $1 limit 1`,
      [orderId],
    );
    return rows[0] ? toOrder(rows[0]) : null;
  }
}
\```

### Rejected alternatives

<Show each losing variant briefly, with a one-line reason it lost. Agents need the counter-examples to
recognize and avoid drift, not just the positive example.>

\```typescript
// REJECTED: ORM Repository<T> injected straight into services.
// Reason: leaks ORM rows into the domain; produces N+1; scattered across service files (low AI-legibility).
\```

## Agent directives

> The machine-facing contract. A code-generating or refactoring agent treats this block as authoritative.

- **ALWAYS** return mapped domain entities from repositories, never raw ORM rows.
- **ALWAYS** write data access as a `*.repository.ts` class taking `DataSource` and using `dataSource.query` with lowercase SQL and positional parameters.
- **PREFERRED** one query method per use-case need; duplicate a query rather than build a generic query builder.
- **NEVER** inject `Repository<T>` or the ORM data-mapper directly into a service or use-case.
- **NEVER** perform cross-module joins; read another module's data through its public service.
- **FORBIDDEN** string-interpolating values into SQL; always parameterize.

## Migration

<Ordered convergence path. Which files change, in what order, and the rule for new code vs. existing code.>

- New code: conform immediately.
- Existing code: migrate the <N> deviating files on next touch; no big-bang rewrite.
- Priority files (security-sensitive / high-traffic): <list>.

## Enforcement

<How a violation is caught. Name the deterministic gate if one exists; if conformance is review-only, say
so plainly — an unenforced ADR is a suggestion, and agents drift from suggestions.>
```

---

## Notes on filling the template

- **The `scope` globs are load-bearing.** They let an agent (or an enforcement tool) determine *which* files
  this ADR applies to without guessing. Make them precise.
- **The directive verbs are a closed set:** ALWAYS, NEVER, PREFERRED, FORBIDDEN. Do not introduce softer
  words ("try to", "consider") in this block — ambiguity here defeats the purpose. Put nuance in the prose
  sections, certainty in the directives.
- **Keep ALWAYS/NEVER for hard rules and PREFERRED for the default-with-exceptions case.** FORBIDDEN is
  reserved for things that are actively dangerous (injection, secret exposure, authZ bypass), distinct from
  merely-NEVER stylistic prohibitions — the stronger word signals to both humans and agents that this is a
  safety boundary, not a convention.
- **If an ADR supersedes another, set `supersedes` and flip the old one's `status` to
  `superseded-by:<id>`.** Stale, contradictory ADRs are worse than none — they reintroduce the ambiguity the
  skill is meant to remove.
