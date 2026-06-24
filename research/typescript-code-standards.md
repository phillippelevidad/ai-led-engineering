# TypeScript Code Standards

Focused standards for TypeScript. Pragmatic Programmer mindset: craft, clarity, contracts, and continuous small improvement.

Requirement levels follow RFC 2119: **MUST** / **MUST NOT** are non-negotiable; **SHOULD** / **SHOULD NOT** are strong defaults requiring a documented reason to violate; **MAY** is discretionary.

## General rules

- **MUST:** Handle every async rejection; never fire-and-forget promises
- **MUST:** Automate checks: typecheck, lint, tests on every change
- **SHOULD:** One responsibility per function; extract when intent blurs
- **SHOULD:** Prefer flat code; guard early, avoid nesting
- **SHOULD:** Keep modules orthogonal; minimize cross-import coupling

## Naming

- **MUST:** Constants: SCREAMING_SNAKE at module scope; name all literals
- **MUST:** Descriptive, unambiguous names; `userId`, not `id` or `u`; no abbreviations
- **SHOULD:** Variables and functions: camelCase; nouns, verbs, is/has/can booleans
- **SHOULD:** Classes and object interfaces: PascalCase nouns, no prefix
- **SHOULD:** Contract interfaces: I prefix for behavior ports (IDatabase, ILogger)
- **SHOULD:** Union types: PascalCase; suffix Result, Error, or State
- **SHOULD:** Name for domain meaning; code explains what, comments why

## Type constructs

- **MUST:** Enable strict mode; fix type errors; no implicit `any`
- **MUST:** Explicit return types on all exported functions
- **MUST:** Use unknown and narrow; never cast without reason
- **MUST:** Export one canonical shape; avoid duplicate definitions
- **MUST:** One consistent error shape or class across the codebase
- **SHOULD:** Use interface for objects and classes; type for unions
- **SHOULD:** Prefer const object, as const, and satisfies over enums
- **SHOULD:** Encode contracts in types; validate boundaries, assert invariants
- **SHOULD:** Discriminated unions for states, results, and canonical errors
- **SHOULD:** Branded types for opaque ids, not plain strings
- **SHOULD:** Good enough types now; tighten when behavior stabilizes
- **SHOULD:** Default to const; use let only when reassignment is necessary

## File layout

Order for top-down reading, not compiler define-before-use.

- **MUST:** Named exports only; no default export surprises
- **SHOULD:** Classes: public methods first; private last in call order
- **SHOULD:** Modules: primary export first; helpers below in call order
- **SHOULD:** Single export: exported first, then unexported helpers below
- **SHOULD NOT:** Put helpers above the orchestrator or entry point

```ts
// ✅ entry first
export function someCheck(...) {
  const parsed = parseData(...);
}

function parseData(...) { ... }

// ❌ helper first — bottom-up, hard to read
function parseData(...) { ... }
export function someCheck(...) { ... }
```

## Testing

- **MUST:** Behavioral authorization tests for endpoints touching payments, vendor data, or PII
- **MUST:** Colocate unit tests with source (`thing.ts` + `thing.test.ts`)
- **SHOULD:** Colocate integration tests with their subject; suffix `*.integration.test.ts`
- **SHOULD:** E2E tests live at app or feature journey level, not beside every source file; suffix `*.e2e.test.ts`
- **SHOULD:** Default no test; one-behavior fns, rules, branches, bugs
- **SHOULD:** Skip controllers, repos, DTOs, pages, layouts, snapshots
- Stack-specific (NestJS, Next.js): [concerns-stack-testing.md](./concerns-stack-testing.md)
- **SHOULD:** Test names: what when condition should outcome format
- **SHOULD:** Design for testability; inject dependencies at boundaries
- **MUST NOT:** Treat coverage % as the goal; skip weak tests
