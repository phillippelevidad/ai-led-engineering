# Engineering an AI-Native SaaS: Best Practices for Codebases Where Agents Are the Primary Developers

## TL;DR

- **The single highest-leverage decision is to optimize your entire codebase for context: small, explicit, vertically-sliced modules with machine-readable instruction files (AGENTS.md/CLAUDE.md), enforced boundaries (dependency-cruiser), and spec-first workflows.** For your NestJS modular monolith, this means doubling down on the architecture you already have — bounded-context modules with explicit `/public` APIs and adapter-enforced boundaries — while adding agent-facing documentation and deterministic guardrails from day one.
- **The biggest paradigm shift is that "cleverness" is now a liability and "explicitness" is an asset.** DRY-driven abstraction, deep inheritance, and horizontally-sliced layered structures actively hurt agents; verbose, boring, self-contained, colocated code with explicit types maximizes agent accuracy. The new bottleneck is not writing code but reviewing it, so invest disproportionately in automated guardrails (architecture fitness functions, type checks, tests, AI code review) that turn architectural intent into deterministic CI gates.
- **Treat AI-generated code as a security and stability risk that must be contained, not trusted.** Veracode's 2025 GenAI report found 45% of AI-generated code introduced an OWASP Top 10 vulnerability even as syntax correctness exceeded 95%, and the 2025 DORA report confirms AI raises throughput while degrading delivery stability. The frontier answer (Cloudflare, Anthropic) is layered AI review + mandatory enforced rules + human "break glass" + checkpoint-and-revert workflows — not autonomy without gates.

## Key Findings

1. **Context is the master constraint.** Every emerging best practice — file structure, documentation, coding style, modularity — reduces to one thing: maximizing the signal-to-noise ratio in a finite, degrading context window. Anthropic's own guidance says virtually all Claude Code best practices "boil down to" context-window management, with performance degrading well before the window is full.

2. **Vertical slices beat horizontal layers for agents.** Feature-colocated modules let an agent's tree-like, depth-first exploration stay within one narrow slice, minimizing token-hungry directory-hopping and file reads. Your DDD module-per-bounded-context structure is already the right instinct; push colocation further (tests next to code, one responsibility per file).

3. **Modular monolith is the consensus AI-native architecture** — and you've already chosen it. A single coherent codebase gives agents a complete semantic map; microservices fragment context across repos with implicit network contracts agents can't see. Keep clean internal boundaries so you can extract services later if needed.

4. **AGENTS.md is now an open standard** (stewarded by the Agentic AI Foundation under the Linux Foundation), supported across Claude Code, Cursor, Codex, Copilot, Aider, and others. CLAUDE.md and AGENTS.md should be short (<300 lines; HumanLayer's root is <60), hierarchical (nested per-module), and treated as living code reviewed when agents err.

5. **Specs and ADRs become executable source-of-truth artifacts.** Spec-Driven Development (GitHub Spec Kit) inverts the workflow: spec → plan → tasks → implement, with the spec as the durable artifact and code as its expression. ADRs/AGENTS.md encode the "why" so agents don't regenerate or contradict prior decisions.

6. **Determinism is delegated to tooling, not the model.** Because agents are non-deterministic, the durable pattern is to convert architectural rules into deterministic checks: dependency-cruiser/tsarch for boundaries, strict TypeScript types, lint rules, and tests. Agents read the failure and self-correct.

7. **Human oversight is the new bottleneck and must be industrialized.** Frontier teams (Cloudflare, Anthropic) use multi-agent adversarial review, mandatory enforced rule sets, checkpoint/revert workflows, and explicit merge-blocking gates with human escape hatches.

8. **Git worktrees + parallel agents are the emerging dev workflow** — which you already use. The key discipline is decomposing work by feature/domain boundary so parallel agents don't collide, plus per-worktree env/db/port isolation.

## Details

### 1. Engineering Principles (first principles for agent-primary codebases)

The foundational principles, drawn from Anthropic's engineering guidance, the Stack Overflow/JetBrains/IBM practitioner writeups, and the agentic-architecture literature:

- **Explicitness over cleverness.** The Stack Overflow guidance for AI coding guidelines is blunt: "Be simple, explicit, and boring… AI loves patterns. Don't confuse the AI." Avoid idioms, implicit conventions, and magic. Prefer explicit types, descriptive unambiguous names (`user_id` not `user`), and named constants over magic values.
- **Locality of behavior / colocation.** Keep everything a feature needs in one place so an agent can reason end-to-end without stitching context across the tree.
- **Small, single-responsibility units.** Smaller files and functions mean higher recall and less noise per read. Taken to a reasonable extreme: roughly one responsibility per file, with the test file beside it.
- **Determinism via tooling.** Since the model is non-deterministic, push correctness guarantees into deterministic layers: type system, lint, architecture tests, unit tests, CI gates.
- **Idempotency and explicit state.** The "native agent architecture" movement argues for owning orchestration/state/memory as explicit, testable code rather than hidden framework abstractions — the failure is then in your code, which you can instrument and trace.
- **Testability as a first-class constraint.** Tests should be "boringly explicit" — linear setup/execute/verify, minimal logic, "prefer duplication over complex abstraction," and validate business outcomes not implementation details.
- **Avoid over-engineering.** Anthropic's own prompting docs warn that recent Claude models "tend to overengineer by creating extra files, adding unnecessary abstractions, or building in flexibility that wasn't requested," and recommend explicit instructions to keep solutions minimal. Simplicity beats complexity: simple control loops beat elaborate multi-agent systems.

### 2. Architecture Decisions

**Modular monolith is the right call and is the emerging consensus.** A modular monolith with clean domain boundaries "gives AI coding tools a coherent semantic map of the application," whereas microservices present "a fragmented codebase across multiple repositories, with implicit contracts defined by network APIs rather than in-code interfaces." Google's Service Weaver research (the HotOS'23 paper "Towards Modern Development of Cloud Applications") found that colocating logical microservices into a single binary "improves application latency by up to 15x and reduces cloud costs by up to 9x compared to a typical deployment in the cloud using microservices." Stripe and Shopify run large modular monoliths. The recommended evolution is monolith → modular monolith → extract services only on clear signal, never monolith → microservices directly.

**For AI specifically:** in a monolith, "an agent generates code that fits in one place. Clear locality." In microservices, the agent must understand service boundaries it can't see in-code and risks violating them.

**Patterns that maximize agent effectiveness:**

- **DDD bounded contexts as modules** (you have this). Each module = one business capability with its own domain/use-cases/infrastructure layers.
- **Ports-and-adapters at module boundaries.** The Synapse Studios NestJS standard is a near-perfect template for your stack: each module exposes a `/public` directory (interface + impl), and **only files in a module's `/adapters` directory may import from other modules' `/public` directories.** The consuming module defines its own local interface for what it needs. This is enforced by dependency-cruiser.
- **Event-driven for cross-module decoupling.** Use NestJS `EventEmitter2`/`@OnEvent` for loose coupling between modules (e.g., `order.placed` → inventory reservation), so agents adding a feature don't have to wire synchronous cross-module call chains.
- **Logical data isolation.** Prefix tables per module (`orders_order`, `users_user`), no cross-module DB joins, no shared foreign keys — access other modules' data through their service APIs. This keeps each module independently reasoned-about and extractable.

**Tradeoffs that matter most when AI writes the code:** favor locality and explicit contracts over network purity; favor a few duplicated lines over a shared abstraction that forces the agent to load three files; accept more upfront verbosity to gain token-efficient exploration and lower merge-conflict surface area.

### 3. Repository Structure

**Vertical/feature slicing is the key agent-era shift.** Basti Ortiz's widely-cited analysis frames a coding agent as "a deepening and narrowing search tree" — it semantically queries, keyword-searches, then reads files, dumping intermediate tokens into context at each step. Horizontally-sliced architectures (all controllers here, all services there) "violate the collocation principle by scattering snippets of features across separate directories," forcing more `ls` calls and reads of monolithic Service/Repository files that "dump more code noise than signal." Vertical slices make exploration "highly selective by construction."

**Concrete structure for Vendra (NestJS + Next.js):**

```
src/modules/
├── catalog/
│   ├── domain/            # entities, value objects, domain errors (no NestJS imports)
│   ├── use-cases/         # one use-case per file (create-listing.use-case.ts)
│   ├── infrastructure/    # controllers, TypeORM/Prisma repositories, DTOs
│   ├── public/            # public-service interface + impl (cross-module API)
│   ├── adapters/          # the ONLY place importing other modules' /public
│   ├── catalog.module.ts
│   └── AGENTS.md          # module-specific agent instructions
├── orders/
├── payments/
├── vendors/
└── shared/                # value objects, IdGenerator, DateService (@Global)
```

**Monorepo vs polyrepo:** For AI-native development the consensus strongly favors **monorepo** — "Monorepos provide AI with comprehensive context in one place: schema, API definitions, implementation all accessible." Keep your Next.js frontend and NestJS backend in one repo (Turborepo/pnpm workspaces) so agents see end-to-end contracts. Phoebe's engineering team went further with Bazel to make module visibility an opt-in API and fail circular dependencies at build time — "one pathway for humans and agents alike."

**File naming:** explicit, suffix-based, predictable (`*.use-case.ts`, `*.repository.ts`, `*.public-service.ts`, `*.controller.ts`, `Component.test.tsx` beside `Component.tsx`). Suffix conventions also enable tsarch/dependency-cruiser rules to enforce architecture deterministically. Do not maintain a hand-written project-map/directory-tree doc — Matthew Groff and others note these "go stale immediately"; let the agent explore the filesystem.

### 4. Documentation Strategies

**Two audiences, two doc systems.** Human docs (READMEs, prose ADRs) stay human-facing; agent docs are machine-optimized and curated.

- **AGENTS.md (open standard) and/or CLAUDE.md** at the root, with nested files per module. Claude Code walks _up_ the tree loading all ancestor CLAUDE.md files at startup, loads descendant files lazily when touching that subtree, and never loads siblings — so put repo-wide conventions at root and module-specifics in module files. Claude Code does not natively read AGENTS.md; symlink or `@AGENTS.md`-reference it to stay tool-agnostic across Cursor/Codex.
- **Keep them short and high-signal.** Research suggests frontier thinking LLMs reliably follow ~150–200 instructions; bloated files cause the agent to _ignore_ real instructions. HumanLayer's root CLAUDE.md is <60 lines; consensus is <300. Use the test "Would removing this line cause a mistake? If not, cut it."
- **Progressive disclosure / tiered docs.** Tier 1 (always loaded): build/test commands, non-negotiable conventions, boundaries. Tier 2/3 (loaded on demand via skills or `@imports`): migration workflows, API contracts, domain-specific guidance. The rule (Augment Code): info belongs in a static context file only if it is both _undiscoverable_ from the code AND _universal_ to nearly every task.
- **Three-tier permission rules** (Addy Osmani): "Always do" (run tests before commit), "Ask first" (modify DB schema, add dependencies, change CI), "Never do" (commit secrets, edit `node_modules`). "Never commit secrets" was the single most common helpful constraint in GitHub's study.
- **API contracts & domain models as machine-readable artifacts:** OpenAPI schemas, explicit TypeScript types, `llms.txt`/`llms-full.txt` for any docs sites, and a Mermaid ER diagram of the data model embedded in AGENTS.md (Tim Deschryver found this "a great way to give the agent a better understanding of the data model").
- **ADRs for the "why."** ADRs capture architecturally-significant decisions and rationale so agents "lean toward reuse rather than regeneration." Emerging variants: AgDR (Agent Decision Records) for decisions agents themselves make, and the practice of having the agent auto-create an ADR whenever an architectural change is made. A 2026 arXiv paper ("Lore") notes ADRs capture architecture-level but not implementation-level decisions — consider also encoding implementation rationale in structured commit messages.
- **The feedback loop is the most underrated practice:** when an agent makes a mistake, have it update AGENTS.md/CLAUDE.md so it doesn't repeat the error. Every code-review comment on an AI PR is a signal the agent lacked context — convert it into a rule.

### 5. Coding Conventions

Synthesizing the JetBrains, IBM, Stack Overflow, and community guidance:

- **Explicit static types everywhere.** TypeScript strict mode; explicit return types; no implicit `any`. Types are deterministic guardrails the agent and compiler both enforce.
- **Descriptive, standard-pattern names.** Verbs for functions, nouns for variables/classes; no abbreviations; no magic numbers/strings.
- **Verbosity over brevity; duplication over premature abstraction.** This is the single biggest convention reversal: DRY applied too early "creates brittle abstractions." Faros AI notes thoughtful context design — not aggressive DRY — is the better duplication-prevention mechanism (give the agent the right map and it reuses rather than regenerates). Reserve abstraction for genuine, stable, single-source-of-truth knowledge.
- **Named exports, not default exports; repository pattern for data access; a single custom error class/shape.**
- **Comments explain "why," not "what."** Especially in tests, comment the business reason, not the mechanics.
- **Tests: boringly explicit, minimal logic, self-contained, business-outcome assertions.** Tightly-scoped unit tests per function/file keep agents honest and keep test-file reads cheap.
- **Provide canonical examples.** Include in your conventions one full example of code that follows all guidelines, plus correct/incorrect pairs — "AIs love a good template."

### 6. Human Oversight Patterns

This is where Vendra most needs to be deliberate, because the data is sobering and the bottleneck has moved from writing to reviewing.

**The risk data (cite explicitly in your own internal standards):**

- **Veracode's 2025 GenAI Code Security Report** (testing 100+ LLMs across 80+ coding tasks) found that "across all models and all tasks, only 55% of generation tasks result in secure code… in 45% of cases, the model introduces a known security flaw" — while syntax correctness exceeded 95%, meaning the security/syntax gap is _widening_. The failure was worst in Java (72% failure rate) and for Cross-Site Scripting (failed in 86% of relevant samples). A separate January 2025 study found 38% of AI-generated code contained at least one flaw, and GitHub found Copilot suggestions vulnerable in ~30% of security-sensitive scenarios.
- **Escape.tech's "State of Security of Vibe Coded Apps"** analyzed over 5,600 publicly available applications and identified more than 2,000 vulnerabilities, 400+ exposed secrets, and 175 instances of exposed PII (including medical records, IBANs, phone numbers, and emails) — all in live production systems.
- AI-specific vulnerability classes: hallucinated/nonexistent dependencies (~1 in 5 GPT-series samples referenced packages that didn't exist), missing authorization checks, and prompt-injection of the agent itself.
- **Iterative degradation:** the June 2025 arXiv study "Security Degradation in Iterative AI Code Generation" (400 samples, 40 rounds, 4 prompting strategies) found "a 37.6% increase in critical vulnerabilities after just five iterations."
- **The 2025 DORA report** (State of AI-assisted Software Development, ~5,000 respondents) states: "AI adoption does continue to have a negative relationship with software delivery stability. This confirms our central theory — AI accelerates software development, but that acceleration can expose weaknesses downstream. Without robust control systems… an increase in change volume leads to instability."
- **METR's July 2025 randomized controlled trial** (Becker, Rush, Barnes, Rein; arXiv 2507.09089; 16 experienced developers, 246 tasks in repos averaging 22k+ stars) found that "allowing AI actually increases completion time by 19%" — even though developers forecast being 24% faster beforehand and still estimated they were 20% faster afterward. A caution against assuming raw speedups and against skipping review on mature codebases.

**The frontier oversight playbook:**

- **Layered, multi-agent code review in CI.** Cloudflare's "Orchestrating AI Code Review at scale" (blog.cloudflare.com/ai-code-review, April 2026): "we launch up to seven specialised reviewers covering security, performance, code quality, documentation, release management, and compliance with our internal Engineering Codex," coordinated by a top-tier model (Claude Opus 4.7 / GPT-5.4) that deduplicates findings and posts a single structured review. In the first 30 days (Mar 10–Apr 9, 2026) it ran 131,246 review runs across 48,095 merge requests in 5,169 repositories, with a median review time of 3m 39s and 2.7 reviews per MR. Risk tiers scale review intensity (trivial ≤10 lines → 2 agents; full >100 lines or security-sensitive files → 7+). Explicit merge gates: any critical/production-safety item → request changes and **block merge**; bias explicitly toward approval; humans can comment "break glass" to force approval (needed in only 0.6% of MRs).
- **Mandatory, enforced rule sets.** Cloudflare's internal "Engineering Codex" is enforced via AI code review on the entire codebase without exception — "Rules without enforcement are suggestions." Their outage post-mortems led to deterministic rules like banning Rust `.unwrap()` outside tests.
- **Adversarial / fresh-context review.** Anthropic's Boris Cherny spawns review subagents, then _more_ subagents tasked with poking holes in the first set's findings. A fresh context window (or a different model) reviewing is less biased toward code it just wrote. Tell reviewers to flag only gaps affecting correctness or stated requirements to avoid over-engineering.
- **Checkpoint-and-revert over correct-in-place.** Anthropic teams start from a clean git state, commit frequently, and revert rather than fight a bad trajectory ("starting over often has a higher success rate than trying to fix mistakes"). Use `/clear` and `/rewind` to avoid polluting context with failed attempts.
- **Test coverage as a gate, but coverage-of-behavior not just %.** Have agents write tests (Anthropic's Inference team cut R&D time ~80% via agent-generated edge-case unit tests); gate merges on tests passing via "stop hooks" that make the model keep fixing until green. Add behavioral end-to-end tests for auth/authorization paths, since those are exactly what agents skip.
- **Static analysis as deterministic backstop.** SonarQube/Semgrep-style SAST and secret scanning on every PR; "static code analysis is deterministic" and independently verifies non-deterministic AI output.
- **Provenance & accountability.** "In the end, every engineer is responsible for their own checked-in code, whether they wrote it by hand or had Cursor generate it" (Cursor). Keep human accountability for merged code non-negotiable.

### 7. Obsolete vs Emerging Patterns

**Becoming liabilities:**

- **Heavy DRY/abstraction-first design** — premature abstractions force multi-file context loads and obscure behavior.
- **Horizontally-sliced layered repos** (group-by-technical-layer) — scatter feature logic and pessimize agent exploration.
- **Deep inheritance / framework magic / implicit conventions** — invisible behavior the agent can't see and will get wrong.
- **Microservices-by-default** — fragment context; a 2026 industry write-up cites ~42% of orgs consolidating microservices back into larger units (treat as directional).
- **Hand-maintained directory-map docs** — go stale immediately.
- **Thick framework abstractions for orchestration/state** — replaced by explicit, owned, testable code ("native agent architecture").

**Emerging/replacing:**

- **Vertical/feature slices + colocation.**
- **Explicit verbose code + explicit types.**
- **Spec-Driven Development** (spec/plan/tasks/implement as artifacts; spec as source of truth).
- **Architecture fitness functions** (dependency-cruiser, tsarch, ArchUnit-style) as CI gates — Ford/Parsons/Kua's concept now central to agent governance.
- **Context-as-code** (AGENTS.md, CLAUDE.md, skills, llms.txt) versioned with the repo.
- **Just-in-time context retrieval** over pre-loading everything (Anthropic): agents keep lightweight identifiers (file paths, queries) and load on demand.

### 8. Context Management at the Repository Level

- **Design for the "40% rule."** Practitioners observe output quality degrades past ~40% context utilization (some cite a "dumb zone" around 40%, "context rot" around 300–400k tokens on million-token models). Structure code so a feature fits in a small context budget — this is the deepest justification for vertical slices and small files.
- **Repository-level memory hierarchy** (Google ADK framing, echoed across the field): working context (the prompt) → session (durable log) → memory (long-lived searchable knowledge, e.g., AGENTS.md, ADRs, skills) → artifacts (files addressed by name). Persist durable knowledge as version-controlled, curated, high-signal files — not raw logs or secrets.
- **Compaction & note-taking.** Use `/clear` between unrelated tasks, `/compact` to summarize within a task, and structured "scratchpad"/plan files (PLAN.md) that survive context resets. Tool-result clearing is the safest lightweight compaction.
- **Persistent cross-session memory is still an open problem.** Cursor/Windsurf rebuild context per session via semantic index; tools like ContextPool/Mem0/Zep and Claude Code's `memory`/skills are early solutions. The pragmatic repo-level answer today: encode durable decisions in ADRs + AGENTS.md + tightly-scoped specs so each new session re-grounds cheaply.
- **Just-in-time loading** beats stuffing everything into context "just in case" — extra context is "often counterproductive."

### 9. AI-Native Organizations (what frontier teams do differently)

- **Anthropic** dogfoods Claude Code to build Claude Code; uses auto-accept loops for edge tasks (Vim mode was ~70% autonomous), synchronous detailed prompting for core business logic, frequent checkpointing, CLAUDE.md files as the primary context mechanism (replacing data catalogs), and subagent-based adversarial review.
- **Cursor/Anysphere** ships a single TypeScript+Rust monolith with conservative feature flagging every 2–4 weeks ("speed through simplicity, not microservices"), reached ~$500M ARR in ~2 years (later reportedly $1B+), is used by >50% of the largest Fortune 500 tech companies, and built Background Agents so each senior engineer orchestrates fleets of agents on separate branches. They use BugBot for AI review and added memory in Cursor 1.0.
- **Vercel** runs an "Iterate to Greatness" culture — engineers open PRs from day two (one intern merged 80+ PRs), formalized the **Design Engineer** role (eliminating design↔frontend handoff), and ships Agent Skills + v0 + a Vercel MCP server so agents can inspect deployments/logs.
- **Linear** is cited for a "no-A/B-testing," taste-driven quality philosophy and tight Cursor/Vercel/QA.tech integration (Linear ticket → Cursor build → Vercel preview → automated QA bot approves PR in 5–8 min).
- **Cloudflare** built CI-native multi-agent review ("Code Orange: Fail Small") with an enforced Engineering Codex.
- **Cross-cutting cultural traits:** revenue-per-engineer as the defining metric; "taste" and "discipline" (specs before prompts, tests before shipping, reviews before merging, ADRs before architecture changes) as the scarce skills; small teams + heavy tooling leverage.

### 10. Tooling

- **Cursor** (AI-native IDE, codebase-aware multi-file edits, Background Agents, BugBot review) and **Claude Code** (agentic CLI, subagents, skills, hooks, worktree isolation, MCP) — you already use both; they are the current frontier pairing.
- **Git worktrees** for parallel isolated agent sessions (you use these). Claude Code's `--worktree` flag and desktop app auto-create worktrees; `.worktreeinclude` copies gitignored env files into each. Discipline: decompose by feature/domain boundary; isolate db/port per worktree; avoid parallel dependency changes (lockfile conflicts); each worktree needs its own `node_modules`.
- **Architecture enforcement:** dependency-cruiser (your stack — enforce the `/public`+adapters pattern and ban cross-module imports/cycles in CI), tsarch (naming/access conventions as unit tests), wired into agent feedback loops via stop hooks.
- **Spec/workflow:** GitHub Spec Kit (`/specify`, `/plan`, `/tasks`, `/implement`, `/analyze`), MADR-format ADRs.
- **Review/quality:** SonarQube (with MCP server for Cursor/Claude), Semgrep, secret scanners; CI-posted AI review agents.
- **MCP servers** (Vercel, GitHub, Sentry, Linear, Postgres) to give agents typed, bounded tools — Anthropic's tool-design guidance: namespace tools by domain, prefer search over list-all, return high-signal context, cap tool responses (Claude Code caps at 25,000 tokens), and design the Agent-Computer Interface (ACI) with as much care as a human UI.
- Other notable agents: Codex, Aider, Windsurf, Gemini CLI, Codeium — all increasingly AGENTS.md-compatible, supporting a tool-agnostic context layer.

## Recommendations

**Stage 0 — Lock in foundations now (day-one, compounding):**

1. **Adopt the Synapse-style NestJS module template**: `domain/` (no NestJS imports), `use-cases/` (one per file), `infrastructure/`, `public/` (interface+impl), `adapters/` (only place importing other modules). This is the single most stack-specific, high-leverage move for Vendra.
2. **Install dependency-cruiser in CI** with the six boundary rules (no-NestJS-in-domain, no-NestJS-in-use-cases, domain-isolation, no-cross-module-imports, no-shared-imports-outside-adapters, adapters-only-use-public-services) plus no-circular-deps. This makes your architecture a deterministic gate agents self-correct against.
3. **Write a tight root AGENTS.md (<100 lines)** + per-module AGENTS.md, symlinked to CLAUDE.md. Include: stack/versions, build/test/lint commands, the module-boundary rule, three-tier permissions (always/ask/never), error-handling shape, and a Mermaid ER diagram. Keep `CLAUDE.local.md` gitignored for personal prefs.
4. **Turn on TypeScript strict mode and named-exports-only**, and write one canonical "golden" example module that follows every convention.

**Stage 1 — Workflow & oversight (first weeks):** 5. **Adopt Spec-Driven Development** (Spec Kit or a lightweight spec→plan→tasks template) for any feature beyond trivial. Review the spec/plan, not just the diff. 6. **Build the CI gate stack**: typecheck → lint → dependency-cruiser → unit tests (stop-hook enforced) → SAST/secret scan → AI review agent posting a structured PR comment. Block merge on any critical/security finding; keep a human "break glass." 7. **Standardize the agent loop**: clean git state → spec → implement with frequent commits → checkpoint → fresh-context (or cross-model) adversarial review → human approval. Revert rather than fight bad trajectories. 8. **Mandate behavioral auth/authorization tests** for every endpoint that touches vendor data, payments, or PII — these are exactly the checks agents skip and where the vibe-coding breaches happened.

**Stage 2 — Scale (as agent share grows):** 9. **Adopt the auto-update-the-docs feedback loop**: every recurring review comment becomes an AGENTS.md rule or a dependency-cruiser/tsarch check. 10. **Introduce ADRs/AgDRs** (MADR format in `/docs/adr`) and have agents draft them on architectural changes. 11. **Parallelize via worktrees by domain boundary** with per-worktree db/port isolation; consider a kanban/orchestrator tool as throughput grows.

**Benchmarks/thresholds that should change your approach:**

- If agent PRs routinely exceed ~40% context to plan, your modules are too big — slice further.
- If dependency-cruiser violations or review comments cluster on the same rule, that rule belongs in AGENTS.md and as a deterministic check.
- If delivery stability (change-fail rate, incidents per PR) rises as AI share grows — the DORA-predicted failure mode — tighten gates and slow merge cadence before adding more autonomy.
- If a module is touched by features in >1 bounded context repeatedly, your boundaries are wrong; re-draw them.
- Only consider extracting a microservice when a module has a clear independent-scaling or team-autonomy signal — not before.

## Caveats

- **"% of code written by AI" figures are directional, not precise.** There is no standardized measurement method, and executives hedge heavily (Nadella's "maybe 20%, 30%"; Pichai's "more than 25%"→"more than 30%"). A widely-circulated "75% of Google's new code is AI-generated" claim could not be confirmed against a primary Google source and conflicts with the documented 25→30% trajectory — treat as unverified.
- **Some sources are vendor/marketing content** (Augment Code, Faros AI, GitClear, OX Security, Escape.tech, Cursor-integration vendors) with potential interpretive bias; their specific figures are cited as directional and corroborated where possible with primary or peer-style sources (Anthropic, Cloudflare, Veracode, METR, the 2025 DORA report, GitHub, and the Service Weaver HotOS'23 paper).
- **Several cited industry statistics come from single studies or blog posts** (e.g., the "~42% consolidating microservices," the GitClear duplication trends, the "40% rule") and represent emerging rather than settled consensus.
- **Predictions are flagged as such** (Kevin Scott's "95% by 2030," Zuckerberg's "half of development within a year") and have not occurred.
- **This is a fast-moving field (data through ~mid-2026).** Model capabilities, context-window sizes, and tool features change rapidly; persistent cross-session memory in particular remains an unsolved, actively-evolving area. Treat the specific tool recommendations as a current snapshot and the architectural principles as the durable layer.
- **The frontier-team practices (Anthropic, Cloudflare, Cursor) reflect very large, well-resourced engineering orgs;** a smaller SaaS like Vendra should adopt the principles and the cheapest high-leverage gates first (types, dependency-cruiser, AGENTS.md, AI review in CI) rather than replicating seven-agent review fleets from day one.
