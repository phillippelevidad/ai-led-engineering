# Engineering Standards: AI-Native Development Playbook

**Status:** Active · **Audience:** All contributors — human and agent · **Source of truth:** This document is the canonical, human-facing standard. The repo's `AGENTS.md`/`CLAUDE.md` files are its _compiled, tightened subset_. When they conflict, this document wins and the agent files MUST be corrected.

---

## How to read this document

Requirement levels follow RFC 2119: **MUST** / **MUST NOT** are non-negotiable and SHOULD be machine-enforced; **SHOULD** / **SHOULD NOT** are strong defaults that require a documented reason to violate; **MAY** is discretionary.

Every load-bearing rule carries an **Enforced by** tag. The governing principle of this entire playbook: _a rule without enforcement is a suggestion, and agents do not obey suggestions reliably._ If a rule cannot be enforced by a deterministic gate, it MUST be enforced by a named human in review, or it does not belong here.

The three-line test for any rule's existence: **Would removing it cause a predictable mistake? Can a tool or a named reviewer catch the violation? Is it true for nearly every task?** If not all three, cut it.

---

## 0. Prime Directives

These supersede everything below.

| #   | Directive                                                                                                                                                                                    | Rationale                                                                        |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| P1  | **Optimize for context, not for elegance.** Every structural choice MUST minimize the tokens an agent needs to load to make a correct change.                                                | Context is the master constraint; quality degrades long before the window fills. |
| P2  | **Determinism is delegated to tooling.** The model is non-deterministic; correctness guarantees MUST live in types, lint, architecture tests, and CI — never in the agent's good intentions. | Agents read failures and self-correct; they do not reliably self-police.         |
| P3  | **Explicit beats clever, always.** Verbosity, duplication, and boring code are now _assets_. Abstraction is a cost paid in context.                                                          | Confirmed reversal of the pre-AI default.                                        |
| P4  | **The human is accountable for merged code, regardless of author.** "The agent wrote it" is not a defense.                                                                                   | Provenance does not transfer responsibility.                                     |
| P5  | **The bottleneck is review, not authorship.** Invest disproportionately in guardrails that make review cheap and bad code expensive to merge.                                                | Generation is now near-free; verification is the scarce resource.                |

---

## 1. Architecture

### 1.1 Default architecture

**MUST:** New services start as a **modular monolith** with clean internal bounded-context boundaries.

- **Enforced by:** Architecture review at service creation; `dependency-cruiser` thereafter.
- **Default:** Modular monolith. **Exception → extract a service** only when a module shows a _concrete_ independent-scaling need, a separate compliance/data-residency boundary, or genuine team-autonomy pressure. "We might need to scale it someday" is not a trigger.
- **Anti-pattern:** Monolith → microservices directly. The only sanctioned path is **monolith → modular monolith → selective extraction.**

**Why this is the AI-native default:** a single coherent codebase gives the agent a complete in-code semantic map. Microservices fragment that map across repos and hide contracts inside network calls the agent cannot see and will violate.

### 1.2 Module boundaries

- **MUST:** Each module maps to exactly one business capability (bounded context).
- **MUST:** Modules communicate only through an explicit public interface (`/public`) or domain events. No deep imports into another module's internals.
- **MUST NOT:** Cross-module database access — no shared foreign keys, no cross-module joins. Read another module's data through its service API.
- **SHOULD:** Prefix tables per module (`orders_*`, `vendors_*`) to keep modules independently reasoned-about and cleanly extractable.
- **SHOULD:** Use domain events (e.g. NestJS `EventEmitter2`/`@OnEvent`) for cross-module reactions rather than synchronous call chains.
- **Enforced by:** `dependency-cruiser` (imports), migration review (schema), DB linting (FK constraints).

**Trigger — boundaries are wrong if:** a single feature repeatedly forces edits across >1 bounded context. Re-draw the boundary; do not paper over it with a shared helper.

---

## 2. Repository Structure

### 2.1 Slicing

- **MUST:** Slice **vertically by feature/domain**, not horizontally by technical layer.
- **MUST NOT:** Group-by-layer at the top level (`/controllers`, `/services`, `/repositories` as siblings). This scatters every feature across the tree and forces the agent into token-expensive directory-hopping and monolithic-file reads.
- **Enforced by:** `dependency-cruiser` rules + review.

### 2.2 Monorepo

- **SHOULD (default):** **Monorepo.** Keep frontend, backend, and shared contracts in one repository so agents see end-to-end types and API definitions in one place.
- **Exception:** Split only when build times, access control, or org structure make a single repo untenable — and accept that you are trading away agent context to do so.

### 2.3 Naming and colocation

- **MUST:** Suffix-based, predictable file names: `*.use-case.ts`, `*.repository.ts`, `*.controller.ts`, `*.public-service.ts`, `*.event.ts`. Predictable suffixes are what makes architecture _enforceable_ by tooling.
- **MUST:** Colocate tests with the code they test (`thing.ts` + `thing.test.ts` in the same directory).
- **SHOULD:** One responsibility per file; one use-case per file.
- **MUST NOT:** Maintain a hand-written directory-map / project-tree document. It goes stale within a week and then actively misleads. Let agents explore the filesystem.

### 2.4 Canonical module template (stack-specific: NestJS)

This is the mandated shape for every backend module. Swap framework specifics for other stacks; keep the structure.

```
src/modules/<context>/
├── domain/            # entities, value objects, domain errors — NO framework imports
├── use-cases/         # one use-case per file
├── infrastructure/    # controllers, repositories (TypeORM/Prisma), DTOs
├── public/            # the module's public interface + implementation
├── adapters/          # the ONLY place permitted to import another module's /public
├── <context>.module.ts
├── <context>.test.ts  # (colocated per unit)
└── AGENTS.md          # module-scoped agent instructions
```

- **MUST:** `domain/` imports no framework code (no NestJS decorators in domain).
- **MUST:** Only `adapters/` may import other modules' `public/`. The consuming module defines its _own_ local interface for what it needs.
- **Enforced by:** `dependency-cruiser` with these named rules: `no-framework-in-domain`, `no-framework-in-use-cases`, `domain-isolation`, `no-cross-module-imports`, `adapters-only-import-public`, `no-circular-deps`.

---

## 3. Coding Conventions

### 3.1 The reversal table

| Old default (now an anti-pattern)     | New default                                                             | Why                                                                      |
| ------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| DRY / abstract on first repetition    | **Tolerate duplication; abstract only on the third, stable occurrence** | Premature abstraction forces multi-file context loads and hides behavior |
| Deep inheritance hierarchies          | **Composition, flat structures**                                        | Invisible behavior the agent gets wrong                                  |
| Implicit conventions, framework magic | **Explicit, visible wiring**                                            | Agents reason about what they can see                                    |
| Brevity / dense idioms                | **Verbose, boring, linear**                                             | "AI loves patterns; don't confuse it"                                    |
| Inferred types                        | **Explicit types everywhere**                                           | Types are deterministic guardrails for both agent and compiler           |

### 3.2 Hard requirements

- **MUST:** TypeScript `strict` mode on. No implicit `any`. Explicit return types on exported functions.
- **MUST:** Named exports only. No default exports.
- **MUST:** Descriptive, unambiguous names. `userId`, not `id` or `u`. No abbreviations. No magic numbers/strings — name them.
- **MUST:** A single, consistent error shape/class across the codebase.
- **SHOULD:** Repository pattern for all data access. Prefer custom SQL via `dataSource.query` over ORM patterns that produce N+1 queries.
- **SHOULD NOT:** Introduce bi-directional entity relationships in data models.
- **SHOULD:** Comments explain **why**, never **what**. The "what" is the code's job.
- **Enforced by:** `tsconfig` strict, ESLint (custom rules for named-exports, no-magic-numbers), review.

### 3.3 Over-engineering guard

- **MUST NOT:** Add files, abstractions, config options, or "flexibility" not required by the current task. Modern models default to over-building; instructions MUST explicitly constrain them to the minimal solution.
- **Enforced by:** Review (reviewer instructed to flag only gaps affecting correctness or stated requirements) + a standing `AGENTS.md` rule: _"Implement the minimum that satisfies the spec. Do not add speculative generality."_

---

## 4. Documentation & Context-as-Code

### 4.1 Two audiences, two systems

- Human docs (README, prose ADRs, design notes) stay human-facing.
- Agent docs (`AGENTS.md`, `CLAUDE.md`, skills) are machine-optimized, curated, and version-controlled _with_ the code.

### 4.2 The agent instruction files

- **MUST:** A root `AGENTS.md` (target **<100 lines**, hard ceiling 300) plus nested per-module `AGENTS.md`. Symlink or `@`-reference `CLAUDE.md` to stay tool-agnostic.
- **MUST:** Root file contains only repo-wide, universal, undiscoverable-from-code information: stack/versions, build/test/lint commands, the module-boundary rule, the three-tier permission list (§4.4), the canonical error shape, and a Mermaid ER diagram of the data model.
- **MUST NOT:** Bloat these files. Past ~150–200 instructions, the agent begins _ignoring_ real rules. Information earns a place only if it is **both** undiscoverable from code **and** universal to nearly every task.
- **SHOULD:** Keep personal/local preferences in a gitignored `CLAUDE.local.md`.
- **Trigger — add a rule when:** the same review comment or the same architecture violation recurs. Every recurring correction is evidence the agent lacked a written rule; convert it into one (and, where possible, into a deterministic check).

### 4.3 Specs and decision records

- **MUST (for any non-trivial feature):** Spec-Driven Development. Workflow is **spec → plan → tasks → implement**. The spec is the durable artifact; code is its expression. Review the spec and plan, not merely the diff.
- **MUST:** Record architecturally-significant decisions as ADRs (MADR format, `/docs/adr`). ADRs encode the _why_ so agents reuse decisions rather than regenerate or contradict them.
- **SHOULD:** Have the agent draft an ADR whenever it makes an architectural change.
- **Exception:** Trivial changes (≤ ~10 lines, no new dependency, no schema/contract change) MAY skip the spec.

### 4.4 Permission tiers (MUST appear in root `AGENTS.md`)

| Tier          | Examples                                                                                                            |
| ------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Always**    | Run tests before commit; run lint; follow module boundaries                                                         |
| **Ask first** | Modify DB schema; add a dependency; change CI; alter a public contract                                              |
| **Never**     | Commit secrets; edit `node_modules` or generated files; disable a failing gate to make CI green; bypass auth checks |

---

## 5. Testing

- **MUST:** Tests are _boringly explicit_ — linear setup/execute/verify, minimal logic, self-contained. **Prefer duplication over shared test abstraction.** Assert business outcomes, not implementation details.
- **MUST:** Every endpoint touching payments, vendor data, or PII has an explicit **behavioral authorization test**. These are precisely the checks agents skip and precisely where vibe-coded breaches happen.
- **SHOULD:** Agents write the tests, including edge cases; merge is gated on tests passing.
- **MUST NOT:** Treat raw coverage % as the goal. Gate on _behavior covered_, not lines hit.
- **Enforced by:** CI test gate (stop-hook style: the agent keeps fixing until green); review for auth-path presence.

---

## 6. Human Oversight & CI Gates

### 6.1 The evidence that mandates this section

Treat AI-generated code as a security and stability liability to be _contained_, not trusted. The empirical basis: ~45% of AI-generated samples introduce a known vulnerability even at >95% syntactic correctness; security degrades further across iterations; and large-scale field data shows AI raises throughput while degrading delivery stability absent strong controls. These are not reasons to avoid agents — they are reasons the gates below are **mandatory, not optional**.

### 6.2 The required gate stack (every PR, in order)

```
typecheck → lint → dependency-cruiser (architecture) → unit + behavioral tests
         → SAST + secret scan → AI review agent → human approval
```

- **MUST:** Static analysis (SAST) and secret scanning on every PR. Static analysis is deterministic and independently verifies non-deterministic output.
- **MUST:** Any critical / security / production-safety finding **blocks merge** (request-changes), with a documented human "break glass" override for the rare false positive.
- **MUST:** Human approval before merge. Non-negotiable, regardless of code author.
- **SHOULD:** Scale review intensity to risk — trivial diffs get a light pass; >100-line or security-sensitive changes get full multi-dimension review (security, correctness, performance, boundaries).
- **SHOULD:** Use **fresh-context or cross-model adversarial review** — a reviewer that did not just write the code (different window, ideally different model) is less biased toward it.

### 6.3 The agent work-loop standard

- **MUST:** Start from a clean git state. Commit frequently (checkpoints).
- **SHOULD:** **Revert over repair.** When a trajectory goes bad, reset to the last good checkpoint rather than fighting it in-context — starting over has a higher success rate than patching a polluted context.
- **Trigger — stop and reset when:** the agent has failed the same gate twice, or planning a single change consumes >~40% of context (your module is too big — slice it).

---

## 7. Context Management

- **MUST:** Persist durable knowledge as version-controlled, high-signal, curated files (ADRs, `AGENTS.md`, skills, specs) — **never** raw logs and **never** secrets.
- **SHOULD:** Design modules so a feature fits in a small context budget. Quality degrades past ~40% utilization; this is the deepest justification for vertical slices and small files.
- **SHOULD:** Prefer just-in-time retrieval (file paths, queries, search) over pre-loading "just in case." Extra context is often counterproductive.
- **SHOULD:** Use `/clear` between unrelated tasks and `/compact` within a long task; keep a `PLAN.md` scratchpad that survives context resets.

---

## 8. Tooling Standards

| Concern                  | Default                                                           | Notes                                                                                                                                 |
| ------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Agentic IDE / CLI        | Cursor + Claude Code                                              | Current frontier pairing                                                                                                              |
| Parallel work            | Git worktrees, isolated per agent                                 | Decompose by domain boundary; isolate DB/port/`node_modules` per worktree; never run parallel dependency changes (lockfile conflicts) |
| Architecture enforcement | `dependency-cruiser` (+ `tsarch` for naming/access as unit tests) | The literal teeth behind §1–§2                                                                                                        |
| Spec workflow            | GitHub Spec Kit or equivalent                                     | `specify → plan → tasks → implement`                                                                                                  |
| Quality gates            | SonarQube/Semgrep + secret scanner                                | Deterministic backstop                                                                                                                |
| Agent ↔ external systems | MCP servers (typed, bounded tools)                                | Namespace by domain; prefer search over list-all; cap response sizes; design the tool interface with UI-level care                    |

- **MUST NOT:** Disable, weaken, or bypass an enforcement tool to unblock a merge. If a gate is wrong, fix the gate in its own PR.

---

## 9. Anti-Pattern Registry (Prohibited)

| Anti-pattern                                             | Replace with                                               |
| -------------------------------------------------------- | ---------------------------------------------------------- |
| Horizontal/layer-first repo layout                       | Vertical feature slices (§2.1)                             |
| DRY-on-first-repetition                                  | Tolerated duplication; abstract on third stable use (§3.1) |
| Microservices by default                                 | Modular monolith (§1.1)                                    |
| Deep inheritance / framework magic / implicit convention | Explicit, visible, composed code (§3.1)                    |
| Hand-maintained directory-map docs                       | Filesystem exploration (§2.3)                              |
| Bloated `AGENTS.md` ("just in case" context)             | Tight, curated, undiscoverable-and-universal only (§4.2)   |
| Thick framework abstractions for orchestration/state     | Explicit, owned, testable code                             |
| Coverage-% as a target                                   | Behavior-covered, auth-path tests (§5)                     |
| Trusting AI output without SAST/review                   | Mandatory gate stack (§6.2)                                |
| Cross-module DB joins / shared FKs                       | Service-API access + per-module table prefixes (§1.2)      |

---

## 10. Migration Guidance (existing codebases)

Apply in this order; each stage is independently valuable and de-risks the next.

**Stage 0 — Foundations (do first, compounds forever)**

1. Adopt the canonical module template (§2.4) for all _new_ modules immediately; leave existing ones until touched.
2. Install `dependency-cruiser` in CI. Start in **warn** mode to surface existing violations without blocking, then flip to **error** module-by-module as you clean them.
3. Write the tight root `AGENTS.md` + permission tiers + ER diagram.
4. Turn on TS `strict` (incrementally per-module via path overrides if the codebase is large) and named-exports-only.
5. Write one **golden module** that obeys every rule. Point agents and humans at it as the reference.

**Stage 1 — Workflow & gates (weeks)** 6. Stand up the full CI gate stack (§6.2), block-on-critical with break-glass. 7. Adopt spec-driven workflow for anything non-trivial. 8. Add behavioral auth tests to every payment/PII/vendor-data endpoint — backfill the highest-risk endpoints first.

**Stage 2 — Scale (as agent share grows)** 9. Institutionalize the feedback loop: recurring review comment → `AGENTS.md` rule → deterministic check. 10. Introduce ADRs; have agents draft them on architectural change. 11. Parallelize via worktrees by domain boundary.

**Migration triggers — re-evaluate when:**

- Architecture violations or review comments cluster on one rule → that rule must become a deterministic gate.
- Change-fail rate / incidents-per-PR rises as AI share grows (the predicted failure mode) → tighten gates and _slow_ merge cadence **before** granting more autonomy.
- A module is repeatedly edited by features from another context → boundaries are wrong; re-draw before adding helpers.

---

## 11. Governance of this document

- **MUST:** Treat this playbook as code. Changes go through PR and review.
- **MUST:** When this document changes, update the compiled `AGENTS.md`/`CLAUDE.md` in the same PR. Drift between the two is a defect.
- **SHOULD:** Quarterly review against field outcomes (delivery stability, escaped defects, recurring review comments). Rules that never fire and rules that never catch anything are both candidates for deletion — a standards document that only grows is failing the §0 context test as surely as any bloated codebase.

_A standard nobody can enforce is folklore; a standard nobody can read is decoration. This one aims to be neither._
