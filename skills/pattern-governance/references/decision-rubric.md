# Decision Rubric: Selecting the Canonical Pattern

This is the analytical core of pattern governance. It answers one question per concept: **which existing
variant becomes the default, and why.** The output of applying this rubric is a single named winner plus a
defensible rationale — never a vague "consider standardizing."

## The scoring model

Score each candidate variant on six signals, 0–5. Multiply by the weights, sum. Highest total wins.

| Signal | Weight | 0 | 5 |
|---|---|---|---|
| **Prevalence** — share of in-scope implementations using this variant | ×3 | rare | dominant majority |
| **Recency** — is this what new code is being written in? | ×3 | only in old/abandoned code | the trend; newest modules use it |
| **Centrality** — does it live in core, healthy, high-traffic modules? | ×2 | only in peripheral/experimental code | in the most important modules |
| **AI-legibility** — can an agent reproduce it correctly with minimal context? | ×2 | requires loading many files / hidden magic | self-contained, explicit, one-file-readable |
| **Standards alignment** — does it match existing written standards/ADRs? | ×2 | contradicts them | already the documented intent |
| **Migration cost (inverse)** — how cheap is it to converge everything else onto this? | ×1 | requires rewriting most of the codebase | most code already conforms |

**Why prevalence and recency dominate (×3):** the objective is convergence. A pattern that is already
winning is the cheapest possible default — most code already conforms, the team already has muscle memory,
and agents have already been seeing it as the de-facto example. Recency is weighted equally because a
*rising* minority pattern that all new code adopts is often the right convergence target even before it
becomes the majority — standardizing on a declining pattern just guarantees a second migration later. When
prevalence and recency disagree (the common case is "old majority vs. new minority"), read the drift
direction: if the new pattern is deliberate and spreading, converge forward onto it; if it is accidental
sprawl, converge back onto the majority.

**Why AI-legibility is a first-class signal, not an afterthought:** this codebase's primary author is
increasingly an agent. A pattern that a human finds equivalent but an agent reproduces more reliably (explicit
over implicit, colocated over scattered, typed over inferred) is genuinely superior *for this purpose*, even
if it is marginally more verbose. Verbosity that buys predictability is a win here, not a cost.

## Tie-breakers (apply in order)

When two variants score within ~2 points:

1. **Prefer the more explicit / more AI-legible variant.** Predictability breaks ties.
2. **Prefer the one already closest to written standards.** Minimize the gap between code and documented intent.
3. **Prefer the lower migration cost.** Less churn, less half-migrated ambiguity.
4. **Prefer the one with better test coverage / lower churn.** A stable, tested variant is a safer default.
5. **If still tied, pick one and move on.** A coin-flip default that everyone follows beats a perfect default nobody converges on. State that the tie was arbitrary so the decision can be revisited cheaply — but *do* decide. Indecision is the failure mode this skill exists to eliminate.

## Special case A — no clear winner (high fragmentation, no dominant variant)

When implementations are scattered with no majority and no clear trend, the codebase has genuine pattern
debt. Do not crown a weak plurality by default. Instead:

1. Define the **minimal canonical pattern** by composing the best-scoring *attributes* across variants
   (e.g. variant A's file layout + variant B's error handling), staying as close as possible to existing
   code so it reads as "the obvious synthesis," not a greenfield invention.
2. Justify each composed attribute against the scoring signals.
3. Flag the high migration cost honestly and lean hard on incremental (migrate-on-touch) convergence.

This is the **only** sanctioned path to a near-greenfield default, and even here the bias is toward
recombining what exists over designing something new.

## Special case B — the prevailing pattern is harmful

If the dominant variant is genuinely harmful (leaks secrets, breaks authZ, corrupts data, or is explicitly
forbidden by org standards), prevalence is overridden. This is the one place the skill weighs quality:

1. Name the prevailing pattern as a **deprecated anti-pattern**, with the concrete harm stated.
2. Select the canonical default from the best-scoring *acceptable* variant. Only if none exists, define a
   minimal greenfield pattern per Special Case A.
3. Write the migration plan as a **remediation**, sequenced by risk (most-exposed code first).
4. State explicitly in the report that prevalence was overridden, and show the harm evidence. Never override
   silently — a convergence skill that quietly substitutes its taste for the team's prevailing practice has
   exceeded its mandate.

## What this rubric deliberately ignores

- **Personal taste / aesthetics.** Not a signal. "I prefer functional style" is not a reason.
- **Theoretical best practice from outside the codebase.** Relevant only as a tie-breaker via standards
  alignment, never as a primary driver. The default is chosen *from what exists here*.
- **Novelty / cleverness.** Actively penalized via AI-legibility. The interesting pattern is usually the
  wrong default.
