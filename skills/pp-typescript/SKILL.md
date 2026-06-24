---
name: pp-typescript
description: >-
  House TypeScript authoring standards — naming, type constructs, file layout, error shapes, and test
  placement — for writing and editing .ts/.tsx code (including NestJS and Next.js). Apply this whenever you
  generate, modify, or refactor TypeScript so the output matches this codebase's conventions instead of
  generic defaults: new code conforms fully, edits align only the lines you touch, wider refactors happen
  only when explicitly requested. Use it even when the user doesn't name a "standard" — any prompt that
  produces or changes TypeScript (add a function/service/route, fix a bug in a .ts file, write a type,
  add tests, scaffold a module) is in scope. Covers strict typing, explicit return types, named exports,
  discriminated unions, branded ids, top-down file ordering, and colocated tests. This governs HOW
  TypeScript is written here; it is not a linter run, a code review, or a bug hunt.
---

# pp-typescript

House standards for authoring TypeScript here. Aim for craft, clarity, and contracts: code that reads
top-down, encodes guarantees in types, and looks like every other file so the next reader can predict it.

Requirement levels follow RFC 2119: **MUST** / **MUST NOT** are non-negotiable; **SHOULD** / **SHOULD NOT**
are strong defaults that need a documented reason to break; **MAY** is discretionary.

## Scope of application — read first

Authoring guidance, not a mandate to rewrite everything. Match enforcement to what you're doing:

- **New code** — follow these standards in full; every applicable rule.
- **Editing existing code ("on touch")** — align only the lines you change; preserve surrounding behavior
  and style. Don't reformat, rename, or restructure untouched lines. A bug fix is a bug fix, not a
  conformance pass.
- **Wider refactor** — refactor beyond the immediate change only when explicitly asked. Surprise refactors
  bury the real diff.

If nearby code breaks a rule but you're only touching adjacent lines, leave it — flag it if it matters,
don't expand scope. Predictable, minimal diffs beat local perfection; unrequested churn erodes trust.

## General rules

- **MUST:** Handle every async rejection; never fire-and-forget a promise — it fails silently, far from
  its cause.
- **MUST:** Keep automated checks green — typecheck, lint, tests on every change.
- **SHOULD:** One responsibility per function; extract when the intent blurs.
- **SHOULD:** Prefer flat code — guard early and return, avoid nesting.
- **SHOULD:** Keep modules orthogonal; minimize cross-import coupling so changes don't ripple.

## Naming

Names are the cheapest documentation. Spend on them.

- **MUST:** Constants are SCREAMING_SNAKE at module scope; name every magic literal.
- **MUST:** Use descriptive, unambiguous names — `userId`, not `id` or `u`; no abbreviations.
- **SHOULD:** Variables and functions are camelCase — nouns for values, verbs for actions, `is`/`has`/`can`
  for booleans.
- **SHOULD:** Classes and object interfaces are PascalCase nouns, no prefix.
- **SHOULD:** Contract interfaces (behavior ports) take an `I` prefix: `IDatabase`, `ILogger`.
- **SHOULD:** Union types are PascalCase, suffixed `Result`, `Error`, or `State`.
- **SHOULD:** Name for domain meaning. Code explains _what_; comments explain _why_.

## Type constructs

Encode contracts in types; let the compiler enforce what a comment or runtime check otherwise would.

- **MUST:** Strict mode on; no implicit `any`; fix type errors rather than suppressing them.
- **MUST:** Explicit return types on all exported functions — the signature is the contract callers read.
- **MUST:** Accept `unknown` at boundaries and narrow it; never cast without a stated reason.
- **MUST:** Export one canonical shape per concept; no duplicate definitions of the same thing.
- **MUST:** One consistent error shape or class across the codebase.
- **SHOULD:** `interface` for objects and classes; `type` for unions.
- **SHOULD:** Prefer a `const` object + `as const` + `satisfies` over `enum`.
- **SHOULD:** Validate at boundaries, assert invariants inside.
- **SHOULD:** Use discriminated unions for states, results, and the canonical error.
- **SHOULD:** Branded types for opaque ids, not plain `string`, so a `UserId` can't be passed where an
  `OrderId` is expected.
- **SHOULD:** "Good enough" types now; tighten when behavior stabilizes.
- **SHOULD:** Default to `const`; use `let` only when reassignment is genuinely necessary.

## File layout

Order files for **top-down reading**, not compiler define-before-use. Primary export first; helpers below
in call order.

- **MUST:** Named exports only. No default exports — they let import sites rename freely and hide intent.
- **SHOULD:** Classes — public methods first, private last, in call order.
- **SHOULD:** Modules — primary export first, helpers below in call order.
- **SHOULD:** Single-export files — the export first, then its unexported helpers.
- **SHOULD NOT:** Put helpers above the orchestrator or entry point.

```ts
// ✅ entry first — reads top-down
export function someCheck(input: RawInput): CheckResult {
  const parsed = parseData(input);
  return evaluate(parsed);
}

function parseData(input: RawInput): ParsedInput { ... }

// ❌ helper first — forces bottom-up reading
function parseData(input: RawInput): ParsedInput { ... }
export function someCheck(input: RawInput): CheckResult { ... }
```

## Testing (general guidance)

Test behavior worth protecting, not a coverage number. Aim to catch real regressions; avoid taxing
refactors.

- **MUST:** Behavioral authorization tests for any endpoint touching payments, vendor data, or PII.
- **MUST:** Colocate unit tests with source — `thing.ts` beside `thing.test.ts`.
- **SHOULD:** Colocate integration tests with their subject, suffixed `*.integration.test.ts`.
- **SHOULD:** E2E tests live at the app or feature-journey level (not beside every file), suffixed
  `*.e2e.test.ts`.
- **SHOULD:** Default to no test; add one for single-behavior functions, business rules, branches, and
  regressions you've just fixed.
- **SHOULD:** Skip controllers, repositories, DTOs, pages, layouts, and snapshots.
- **SHOULD:** Name tests `what when condition should outcome`.
- **SHOULD:** Design for testability — inject dependencies at boundaries.
- **MUST NOT:** Treat coverage % as the goal, or write weak tests to hit it.
