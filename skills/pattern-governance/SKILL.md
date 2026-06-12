---
name: pattern-governance
description: >-
  Governs engineering patterns across a codebase: discovers recurring patterns, identifies competing or
  divergent implementations of the same concept, detects architectural drift, and decides which single
  pattern should become the canonical default. Produces a pattern-governance report plus ready-to-adopt,
  AI-oriented ADRs with explicit ALWAYS / NEVER / PREFERRED / FORBIDDEN directives that future AI agents
  follow when generating, modifying, or refactoring code. Use whenever the user wants to standardize,
  canonicalize, converge, or de-duplicate how something is implemented — e.g. "what should the canonical
  NestJS module structure be", "find the standard pattern for our repositories/DTOs/mappers", "detect
  pattern drift", "reduce inconsistency in how we do X", or "turn our tribal conventions into an ADR".
  Operates on a whole repo, a bounded area, a module, a file set, or a pasted code slice. This is PATTERN
  GOVERNANCE — it decides the default; it is NOT code review, bug-finding, or quality assessment.
---

# Pattern Governance

## What this skill is for

This skill converts emergent, undocumented code patterns into explicit, machine-consumable standards. The
deliverable is **organizational memory**: ADRs and agent-directives that make future AI-generated code
predictable, because every agent that touches the codebase converges on the same defaults instead of
re-inventing a local one.

The governing question is never *"what is the best possible implementation?"* It is:

> **"What implementation should become the default implementation for *this* codebase?"**

Those are different questions and they routinely have different answers. The theoretically optimal pattern
that appears in one file loses to the slightly-less-elegant pattern that appears in forty, because the cost
the skill is minimizing is **ambiguity**, not inefficiency. An AI agent generating code against a codebase
with one clear default produces correct, reviewable output; an agent generating against five competing
defaults guesses, and guessing is where drift, bugs, and review burden come from.

### Priority order (apply when criteria conflict)

1. **Convergence over innovation** — pick a default and eliminate forks; do not invent a sixth way.
2. **Standards over preferences** — an enforced rule beats any individual's taste.
3. **Predictability over cleverness** — boring and uniform beats locally-optimal and surprising.
4. **AI readability over architectural novelty** — favor patterns an agent parses with minimal context.
5. **Existing successful patterns over greenfield redesign** — bless what already works; redesign only when no existing variant is acceptable.

### Out of scope — do not do these

This skill governs *which pattern wins*. It does **not** assess code quality, hunt for bugs, audit
security, or rate performance, except in the one narrow case where a *prevailing* pattern is itself harmful
(see "The convergence safety valve" below). If the user wants review, say so and stop — do not silently
turn a governance pass into a critique. Conflating the two produces reports nobody can act on.

---

## Workflow

Execute these phases in order. Phases 1–2 are evidence-gathering and **must precede** any recommendation —
frequencies and divergences are *counted from the code*, never estimated from memory. Hallucinated
frequencies are the single fastest way to destroy this skill's credibility, so ground every number in a
tool result (see `references/counting-recipes.md` and `scripts/inventory.py`).

### Phase 0 — Resolve scope and concept

Two things must be pinned before analysis: **the scope** (where to look) and **the concept** (what to
govern). Infer both from the request; confirm only if genuinely ambiguous (one question, not an interview).

| Scope type | What to load |
|---|---|
| Whole repository | Module/package roots; run `scripts/inventory.py` over the source root |
| Bounded area | The directory subtree for that area (e.g. `src/modules/payments*`) |
| Single module | That module's directory |
| File set | Exactly the listed files |
| Pasted code slice | Only the provided text — state that frequency analysis is limited to what was shown |

The **concept** is the unit of governance: "controller structure", "repository access pattern", "DTO +
validation", "mapper convention", "cross-module dependency boundary", "test layout", "error shape", "file
naming". A single request often bundles several concepts (the canonical NestJS example bundles ~10).
**Govern each concept separately** — each gets its own inventory, its own decision, and its own ADR. Do not
average across concepts into one mushy recommendation.

### Phase 1 — Inventory

Enumerate **every** implementation of the concept within scope. For each variant, record: a stable label,
representative file path(s), a minimal code exemplar, and the raw count. Use deterministic tooling for
anything mechanically countable (file suffixes, directory shapes, import edges, decorator usage) —
`scripts/inventory.py` produces this structural census as JSON. Use semantic reading only for what tooling
cannot see (e.g. "does this repository return domain entities or ORM rows?").

Produce the **Pattern Inventory** and **Frequency Analysis** sections (template:
`references/governance-report-template.md`).

### Phase 2 — Divergence analysis

Cluster the variants. The output is a clear statement of *competing implementations of the same concept*:
"Repositories diverge three ways: (A) ORM-native `Repository<T>` injected directly into services — 22 files;
(B) custom repository class wrapping `dataSource.query` — 14 files; (C) static query helpers — 3 files."
Note **where** each cluster lives (newer modules? one author's modules? a since-abandoned experiment?) and
any **drift signal** — e.g. a pattern that was uniform six months ago and has since splintered, or a
documented standard that the newest code already ignores. Drift direction matters as much as drift presence.

### Phase 3 — Decide the canonical default

Apply the scoring rubric in `references/decision-rubric.md`. In brief, the canonical pattern is the variant
that maximizes a weighted blend of **prevalence, recency, centrality (lives in core/healthy modules),
AI-legibility, alignment with existing written standards, and low migration cost** — with prevalence and
recency weighted highest because convergence is the objective. Read the rubric for the full model, the
tie-breakers, and the two special cases (no clear winner; prevailing-but-harmful). State the decision as a
single named default with an explicit rationale tied to the scores, not to aesthetics.

### Phase 4 — Anti-pattern detection and deprecation

Identify variants that should be **refactored away** — both the losers of the convergence decision and any
genuine anti-patterns (cross-reference the organization's standards if available; otherwise flag patterns
that fragment, hide behavior, or are demonstrably harmful). For each, state what replaces it.

### Phase 5 — Migration / refactoring plan

Produce an ordered, low-risk convergence path: which deviating files change, in what order, and how to
sequence so the codebase is never half-migrated in a way that confuses agents. Favor **incremental
convergence** (new code uses the default immediately; existing code migrates on touch) over a risky
big-bang rewrite, unless the variant count is small and the change is mechanical.

### Phase 6 — Generate the authoritative artifacts

Emit the **AI-oriented ADR(s)** (`references/adr-template.md`) and the **explicit agent-instruction block**
(ALWAYS / NEVER / PREFERRED / FORBIDDEN). These are the durable executable memory — the parts a future
agent loads as authoritative guidance. They must be self-contained: a fresh agent with zero prior context
should be able to generate conformant code from the ADR alone.

---

## The convergence safety valve

Convergence is the default, but it is not blind obedience to the majority. Blessing the most common pattern
is correct **unless that pattern is genuinely harmful** — it leaks secrets, breaks authorization, corrupts
data, or is explicitly forbidden by the organization's standards. In that single case, do **not** canonicalize
it. Instead: name it as a deprecated anti-pattern, select the canonical default from the best *acceptable*
existing variant (or, only if none exists, propose the minimal greenfield pattern), and write the migration
plan as a remediation. Always state explicitly when you are overriding prevalence, and why — this is the one
place the skill is permitted to weigh quality, and it must show its work.

---

## Output contract

ALWAYS produce all of the following, in this order. Use `references/governance-report-template.md` as the
exact skeleton.

1. **Scope & concepts governed** — what was analyzed; what was deliberately excluded.
2. **Pattern inventory** — every variant, with exemplars and paths.
3. **Frequency analysis** — counts per variant, grounded in tool output.
4. **Divergence analysis** — the competing clusters and the drift signal.
5. **Standardization recommendation** — the single canonical default per concept, with rubric-based rationale.
6. **Anti-pattern detection** — what is deprecated and why.
7. **Migration / refactoring recommendations** — the ordered convergence path.
8. **Ready-to-adopt ADR(s)** — one per concept, in the AI-oriented template.
9. **Explicit AI-agent instructions** — the ALWAYS / NEVER / PREFERRED / FORBIDDEN block.

Output is for two readers at once. Humans skim the report and approve. Agents consume the ADR and the
directive block verbatim. Keep both legible: prose for the reasoning, code exemplars for the canonical and
rejected forms, and unambiguous imperative directives for the machine-facing parts.

If the scope was a small file set or a pasted slice, scale the output down proportionally but keep the same
section order — a governance pass over four files still ends in an ADR and a directive block, just shorter.

---

## Reference files

Load these as needed; do not inline them.

- `references/decision-rubric.md` — the weighted scoring model for selecting the canonical pattern, tie-breakers, and special-case handling. Read before Phase 3.
- `references/adr-template.md` — the AI-oriented ADR format (machine-parseable frontmatter + ALWAYS/NEVER/PREFERRED/FORBIDDEN). Read before Phase 6.
- `references/governance-report-template.md` — the exact output skeleton for the full report. Read before writing output.
- `references/counting-recipes.md` — ripgrep / AST recipes for grounding frequency analysis; what is mechanically countable vs. what needs semantic reading. Read during Phases 1–2.

## Bundled tooling

- `scripts/inventory.py` — deterministic structural census of a codebase: per-module directory shape, file-suffix histograms, naming-convention conformance, and cross-module import edges (flagging imports that bypass a module's public surface). Stdlib-only; run it to ground Phases 1–2 in real counts.

  ```bash
  python scripts/inventory.py <source-root> [--modules-subdir modules] \
      [--canonical-dirs domain,use-cases,infrastructure,public,adapters] \
      [--suffixes .use-case.ts,.service.ts,.repository.ts,.controller.ts,.dto.ts,.mapper.ts] \
      [--json out.json]
  ```

  Treat its numbers as authoritative for structure; treat its import-edge flags as high-recall but
  approximate (regex-based) — confirm flagged boundary violations by reading the file before reporting them.
