# Governance Report Template

The exact output skeleton for a pattern-governance pass. Follow this section order. Scale length to scope
(a four-file pass is short; a whole-repo pass is long) but never drop a section — a short pass still ends in
an ADR and a directive block.

The report has two readers. Humans skim sections 1–7 and approve; agents consume sections 8–9 verbatim.
Write accordingly: reasoning in prose, decisions in code exemplars, machine contract in imperative directives.

---

```markdown
# Pattern Governance Report: <concept(s)> in <scope>

## 1. Scope & concepts governed
- **Scope analyzed:** <repo / area / module / file set / slice — with paths>
- **Concepts governed:** <list — each gets its own decision and ADR below>
- **Deliberately excluded:** <what was out of scope, and why — e.g. "frontend modules; this pass is backend only">
- **Evidence basis:** <tools/commands run, e.g. "scripts/inventory.py over src/modules + ripgrep counts"; or "limited to the pasted slice — frequencies are illustrative, not codebase-wide">

> One block below per concept. Repeat sections 2–8 for each concept governed.

---

## Concept: <name>

### 2. Pattern inventory
| Variant | Label | Exemplar path | Minimal example |
|---|---|---|---|
| A | <name> | <path> | <1–5 line snippet> |
| B | <name> | <path> | <snippet> |

### 3. Frequency analysis
| Variant | Count | Share | Where it lives |
|---|---|---|---|
| A | 22 | 56% | older modules; one author |
| B | 14 | 36% | all modules created in the last quarter |
| C | 3 | 8% | one abandoned experiment |
*All counts grounded in: <tool output reference>.*

### 4. Divergence analysis
<The competing clusters in plain language, plus the drift signal: is this splintering or consolidating?
Which direction is new code moving? Was there a prior standard the newest code already ignores?>

### 5. Standardization recommendation
**Canonical default: Variant <X>.**
<Rationale tied to the rubric — name the signals that drove it, especially prevalence/recency/AI-legibility.
If prevalence was overridden for harm, say so here and show the evidence.>

### 6. Anti-pattern detection
| Deprecated variant | Why | Replaced by |
|---|---|---|
| C | <reason> | X |

### 7. Migration / refactoring recommendations
- **New code:** conform to X immediately.
- **Existing code:** <ordered path — migrate-on-touch vs. scheduled; priority files first>.
- **Risk notes:** <anything that could half-migrate the codebase into a more confusing state>.

### 8. ADR
<Inline the completed AI-oriented ADR for this concept — see references/adr-template.md. This is the durable
artifact; it must stand alone.>

---

## 9. Consolidated AI-agent instructions
> Aggregated ALWAYS / NEVER / PREFERRED / FORBIDDEN across all concepts in this pass. This block is what a
> future agent loads as authoritative guidance. Keep it terse and unambiguous.

**ALWAYS**
- <directive>

**NEVER**
- <directive>

**PREFERRED**
- <directive>

**FORBIDDEN**
- <directive>

## 10. Open decisions (if any)
<Ties that were broken arbitrarily, or concepts that need a human call before an ADR can be finalized. Empty
is good — the goal is to leave nothing ambiguous.>
```

---

## Filling guidance

- **Numbers must trace to evidence.** Every count in section 3 should be reproducible from a command in the
  evidence basis. If you could not count something deterministically (semantic patterns), say "estimated by
  reading N files" rather than presenting a false precision.
- **One concept, one decision, one ADR.** Resist merging concepts to save space — a future agent looking up
  "repository pattern" should find one ADR, not a paragraph buried in a combined document.
- **Section 9 is the payload.** If a reader only consumes one part, it is this. It must be correct and
  self-consistent across concepts — contradictory directives (ALWAYS X in one concept, NEVER X in another)
  are a defect to catch before output.
