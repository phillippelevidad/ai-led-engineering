# Stack Testing Standards (NestJS, Next.js)

Stack-specific testing rules. General TypeScript testing standards live in [concerns-typescript.md](./concerns-typescript.md).

Requirement levels follow RFC 2119.

## NestJS

- **SHOULD:** Prefer integration over unit; assert outcomes, not implementation
- **SHOULD:** At most one mock per test; max eight unit tests per service
- **SHOULD:** Thirty tests per service is a red flag

## Next.js

- **SHOULD:** Utils and helpers: exhaustive pure-function tests, max six per file
- **SHOULD:** Hooks: test only when branching behavior warrants it
