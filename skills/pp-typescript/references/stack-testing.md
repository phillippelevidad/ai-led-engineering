# Stack testing limits (NestJS, Next.js)

Stack-specific guardrails on top of the general testing rules in `SKILL.md` — ceilings that stop suites
becoming a maintenance tax. RFC 2119 levels apply.

## NestJS

- **SHOULD:** Prefer integration tests over unit tests; assert outcomes, not implementation details.
- **SHOULD:** At most one mock per test; at most eight unit tests per service.
- **SHOULD:** Thirty tests on a single service is a red flag — the service is probably doing too much.

## Next.js

- **SHOULD:** Utils and helpers — exhaustive pure-function tests, max six per file.
- **SHOULD:** Hooks — test only when branching behavior actually warrants it.
