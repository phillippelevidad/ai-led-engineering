---
name: implement-plan
description: >-
  Orchestrates implementation and verification of a Cursor Plan Mode markdown
  file by delegating all substantive work to subagents via the Task tool. Use when
  the user asks to implement, execute, or verify a plan file (.plan.md,
  _step-*.md, or equivalent YAML-frontmatter plan). Do not use for PRD task
  files (use cy-execute-task), PR review remediation (use cy-fix-reviews), or
  work without a plan document.
---

# Implement Plan

## Orchestrator mandate (non-negotiable)

When this skill is active, you are an **orchestrator only**. You coordinate end-to-end execution; you do not do the work.

### You MUST delegate via Task

Every substantive action runs in a **fresh subagent** via the Task tool:

- implementation (code, docs, scripts, config, migrations)
- exploration of unfamiliar code areas
- scoped test and shell commands
- spec compliance and quality audits

Prefer many narrow subagents over one large mixed-context session.

### You MUST NOT execute yourself

Do **not** use your own tools for:

- editing application source, config, migrations, or tests
- running shell commands (tests, scripts, builds, linters, formatters)
- performing the spec audit or claiming PASS/FAIL from your own inspection
- combining implementation and verification in one turn

### What the orchestrator may do directly

- Read the plan file (and referenced plan/docs) to build an execution map
- Launch, batch, and monitor Task subagents; decide parallel vs serial waves
- Update plan frontmatter todo `status` only after a verifier subagent PASS for that slice
- Summarize rounds, evidence, blockers, and completion for the user

If you catch yourself about to edit code or run a command, **stop** and delegate a subagent instead.

---

## Purpose

Implement a Cursor Plan Mode markdown file and verify the result against that plan.

Your role:

- parse and internalize the plan (structure only; do not implement)
- delegate implementation to isolated implementer subagents
- delegate spec compliance and quality checks to separate verifier subagents
- iterate execute-then-verify until the plan is fully satisfied
- maximize parallelism by spawning as many independent subagents as the plan allows

---

## Inputs

The user will invoke this skill with a prompt similar to:

> Use the implement-plan skill on `<path-to-plan.md>`

The plan file is produced by Cursor's Plan agent (Plan Mode) or an equivalent planning workflow. Treat it as the single source of truth for scope, approach, and acceptance.

Plans may live anywhere in the repo (e.g. `.cursor/plans/*.plan.md`, `.compozy/tasks/**/_step-*.md`, feature folders). Filename and extension vary; validity is **YAML frontmatter + markdown body**, not a specific path pattern.

### Expected plan format

#### Frontmatter

```yaml
---
name: "Short plan title"
overview: "One-line description (may be quoted if it contains colons)"
todos:
  - id: investigation-logger-file # semantic slug OR UUID — both are valid
    content: "Task description"
    status: pending | in-progress | completed | error
isProject: false
---
```

Todo `id` values are often **semantic slugs** (kebab-case phrases), not only UUIDs. Use the plan's `id` strings exactly when assigning and reporting work.

On intake, schedule only todos with `status: pending` or `error` unless the user explicitly asks to redo `completed` work or re-verify the full plan.

#### Body (often much larger than the todo list)

Below the closing `---`, the body is usually the authoritative spec. Common sections (any subset may appear):

| Section pattern                                     | Role for orchestration                                                    |
| --------------------------------------------------- | ------------------------------------------------------------------------- |
| Goal / overview                                     | Acceptance intent; tie-breaker when a todo line is terse                  |
| **Out of scope** / **not recommended**              | Hard boundaries; implementers must not expand scope                       |
| **Phase A / B / C** (or numbered steps)             | Sequencing **within or across** todos; may override naive parallelization |
| Design decisions / tables                           | Constraints implementers must follow                                      |
| **Files to touch** / **Files to add**               | Scope checklist for verifier                                              |
| Mermaid / flowcharts                                | Context only; not a separate work item unless a todo says so              |
| SQL templates, grep queries, CLI commands           | May be operator-run, script-run, or automated; classify per todo (below)  |
| **Verification** / **done** with `- [ ]` checklists | Acceptance criteria; verifier must evaluate line by line                  |
| **After deploy** / operational next steps           | Usually **human/operator** work; do not delegate as implementation        |
| Links to **other plan or doc files**                | Load referenced paths when a todo or phase depends on them                |

Read the full file (and referenced plan files when the body depends on them) before delegating. Extract:

1. **Frontmatter todos** — primary split axis for subagents (`pending` / `error` only by default)
2. **Body requirements** — phases, tables, snippets, and file lists that todos only summarize
3. **Verification** — frontmatter verify todos **plus** body checklists, matrices, and "done when" prose
4. **Work classification** per todo (see table below)
5. **Shared output paths** — multiple todos updating the same file require serialization or a single owner todo

### Work types (classify every todo before delegating)

| Type                  | Examples in plan body                                            | Delegate to                                                                                                                                 |
| --------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Code**              | New modules, wiring, refactors                                   | `generalPurpose` implementer                                                                                                                |
| **Docs / runbook**    | Markdown stubs, finding matrices, hand-off sections              | `generalPurpose` implementer                                                                                                                |
| **Script / tooling**  | One-off scripts under `message-templates-scripts/`, POST routes  | `generalPurpose` implementer                                                                                                                |
| **Automated verify**  | Targeted unit/integration tests named in the plan                | `shell` or implementer; **scoped and time-bounded** only (see Scoped verification)                                                          |
| **Local execute**     | Run script with env vars; write gitignored artifacts             | `shell` or implementer if credentials exist; else report **blocked** with exact command for user                                            |
| **Operator / manual** | Prod SQL, prod log grep, dashboard actions, deploy, wait windows | **Not** implementer scope unless user provides access; verifier treats as satisfied only with documented evidence or explicit user sign-off |

If a todo mixes types (e.g. "run SQL then build script"), split into sub-steps in the implementer prompt or serialize subagents.

### Mapping todos to body content

Each implementer prompt must attach:

- The todo `id` and `content`
- The **Phase / section headings** from the body that implement that todo (e.g. "Phase B: Capture payloads")
- Applicable rows from **Files to touch** and **Out of scope**
- Any **Verification** checklist items that apply to that slice only

Do not assume the todo line alone is sufficient; long-form plans put the spec in the body.

If the plan path is missing or the file cannot be read, stop and ask the user for a valid plan file.

---

## Available skills (delegation hints)

Subagents may use these when appropriate; the orchestrator does not run them:

- `/cy-final-verify` — apply its **evidence-before-claims** discipline only; do **not** treat it as permission to run full-repo gates (see Scoped verification)
- `AGENTS.md` at repo root — monorepo map; subagents must scope searches to relevant sub-projects

---

## Scoped verification (monorepo)

This repo is a large monorepo. Broad checks waste time and rarely help a narrow plan. **Every** implementer, shell, and verifier prompt must include these rules.

### Never run (unless the user explicitly overrides in chat)

- `npm run format:check` (repo root or sub-project)
- `npm run format` as a verification gate
- Full monorepo test suites (e.g. all packages, `npm test` at root without a path)
- Full monorepo lint (`eslint .`, lint entire sub-project tree)
- Full monorepo build unless the plan's verify todo **explicitly** requires it for the touched sub-project

If the plan text says `format:check`, treat that line as **out of scope for automated agents** unless the user says otherwise. Note in the verifier report: "format:check deferred (agent policy); user may run locally."

### Allowed automated checks

Run only what the plan implies for **files and behavior this task changed**, in the relevant sub-project from `AGENTS.md`:

| Check             | How to scope                                                                                                                        |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Unit tests        | Single spec file, `--testPathPattern`, or `-t "describe name"` matching plan areas                                                  |
| Integration tests | Only if the plan names them or they cover the exact module touched                                                                  |
| Typecheck         | Sub-project only (e.g. `cd monolith && npx tsc --noEmit` on touched paths) **only** if compile errors are likely and the plan cares |

Derive the command from the plan's **Verification** section, **Files to touch**, and sub-project test conventions. When the plan is vague, pick the **smallest** test file(s) that exercise the changed code.

### Time limits (mandatory)

- **At most one minute wall-clock per test command invocation** (hard cap).
- Prefer a single focused spec over a directory; if a directory run exceeds 1 minute, stop, report partial run + timeout, and narrow further in the next fix round.
- Do not chain multiple long test runs in one subagent; run the minimum set needed for evidence.
- If tests cannot complete in 1 minute even when scoped, report **blocked** with the exact command for the user and treat plan verify todos as satisfied-by-deferral only if the plan allows manual verification.

Pass these limits verbatim into implementer and shell subagent prompts.

### What "done" means without broad checks

- Implementers prove their slice via **scoped** test evidence or clear rationale when tests do not exist for that path.
- Verifiers confirm code against the plan spec; they do **not** demand full-repo green builds.
- A plan checklist item that says `format:check` is satisfied by policy deferral plus scoped tests passing, not by agents running format.

---

## Subagent roles (minimum two kinds)

Use **at least two distinct subagent roles** on every run:

| Role                        | `subagent_type`               | Mode                            | Responsibility                                                                            |
| --------------------------- | ----------------------------- | ------------------------------- | ----------------------------------------------------------------------------------------- |
| **Implementer**             | `generalPurpose`              | read-write                      | Implement plan todos: code, config, migrations, tests per plan                            |
| **Verifier**                | `generalPurpose` or `explore` | **readonly** (`readonly: true`) | Audit work against the plan; no fixes, only findings                                      |
| **Explorer** (optional)     | `explore`                     | readonly                        | Pre-implementation codebase recon when the plan references unknown areas                  |
| **Shell runner** (optional) | `shell`                       | —                               | Run **scoped, time-bounded** test commands only when the plan requires automated evidence |

Never combine implementation and verification in the same subagent invocation.

---

## Core workflow

### Phase 0 — Plan intake (orchestrator only)

You may read the plan file and build an execution map. Do not edit source code.

Produce a mental (or brief written) execution map:

- ordered list of todos still `pending` or `error` (skip `completed` unless user overrides)
- **phase order** from the body (Phase A before B, etc.) even when frontmatter todos look independent
- work type per todo (code / docs / script / automated verify / local execute / operator)
- which todos can run in **parallel** (no file overlap, no phase dependency, no shared output file)
- **scoped** verification commands derived from the plan (not repo-wide defaults; see Scoped verification)
- relevant sub-project(s) from `AGENTS.md`
- referenced sibling plan or doc paths to pass into subagent prompts

---

### Phase 0b — Re-verify-only mode

When all todos are already `completed` or the user asks to verify without implementing:

- Skip Phase 2 implementers
- Run Phase 3 verifier against the full plan (body checklists + files to touch + evidence)
- If FAIL, enter Phase 4 fix loop for failing items only

---

### Phase 1 — Optional exploration (parallel)

When the plan references unfamiliar modules or many files, delegate **one explore subagent per distinct area** (e.g. monolith vs frontend), in parallel:

- Task `readonly: true`, `subagent_type: explore`
- Prompt: summarize existing patterns, entry points, and constraints relevant to specific plan sections
- Do not implement anything

Discard explorer context before implementation. Explorers must not implement.

---

### Phase 2 — Implementation (maximize subagents)

For each wave of work:

1. **Prefer one implementer subagent per frontmatter todo** when todos are independent.
2. If a todo is large, split by plan body sections (e.g. backend vs frontend) into multiple implementer subagents, each with a narrow slice of the same todo id.
3. Launch **in parallel** all implementers that do not depend on each other's output (use a single message with multiple Task calls).
4. If todos are strictly sequential per the plan, run implementers one wave at a time.

**Implementer subagent prompt must include:**

- Absolute path to the plan file (and referenced dependency docs, if any)
- The specific todo id(s) and `content` assigned to this subagent
- Linked body sections by heading (Phase / ### number / Verification subset)
- Rows from **Files to touch** that apply to this slice
- Explicit **Out of scope** and **operational** sections the subagent must not perform
- Work type for this slice (what "done" looks like: merged code, filled matrix, gitignored artifact path, etc.)
- Instruction to follow `AGENTS.md` and match existing code conventions
- **Scoped verification** rules (copy from Scoped verification): no `format:check`, no broad tests, 1 min max per test command, commands listed explicitly
- Instruction to run only the tests the plan implies for their slice before reporting done; if the plan names none, choose the narrowest spec file(s) for touched code
- For operator-only steps: either stop with **blocked** and list exact commands/SQL for the user, or document evidence if the user already ran them
- Instruction **not** to claim full-plan completion (only their slice)

Use `subagent_type: generalPurpose` (default read-write).

After each implementer completes:

- Discard that subagent's context
- Do not pass implementation reasoning into the verifier verbatim; pass only artifacts (paths changed, todo ids addressed)

Update plan todo statuses in the plan file to `completed` or `error` only when the verifier later confirms that slice (not when the implementer alone claims success).

---

### Phase 3 — Verification (fresh subagent every round)

After each implementation wave (or after all todos if the plan is small), delegate a **new verifier subagent**:

- `subagent_type: generalPurpose` or `explore`
- **`readonly: true`** — verifier must not edit files
- Prompt must include:
  - Full plan file path (verifier reads it fresh)
  - List of todo ids and files touched in the last implementation wave
  - Requirement to produce a structured **findings report**:
    - **PASS** — no blocking issues, or
    - **FAIL** — numbered findings, each with: plan reference (todo id or body section), expected behavior, actual behavior, severity (`blocking` | `minor`), suggested fix direction (not full implementation)

**Verifier checks (line by line, not vibes):**

- Every in-scope frontmatter todo (`pending`/`error` at start, or marked `completed` by orchestrator after PASS) is actually done
- Every applicable **body Verification** checklist item (`- [ ]` / matrix row / "done when" prose) is satisfied or explicitly N/A with reason
- **Files to touch** table matches the diff (created, updated, or correctly omitted with justification)
- **Out of scope** work was not introduced; **operational** sections were not mistaken for implementation
- Cross-file deliverables (e.g. hand-off docs named in the plan) exist and contain required sections
- Operator/manual todos: evidence present (command output summary, artifact path, user confirmation) or correctly reported blocked
- Code matches plan intent (not only "tests are green")
- **Scoped** tests were run or correctly deferred (command, exit code, duration; must respect 1 min cap; no `format:check` required)
- Plan items that only mention `format:check` or full-suite tests are marked N/A for agents with short note, unless the user overrode policy in chat
- Secrets policy: no tokens in committed files; gitignored paths respected where the plan requires it
- Evidence-before-claims: no PASS without fresh evidence for scoped checks; do not fail PASS solely because broad monorepo gates were not run

The verifier must not fix issues. Findings only.

---

### Phase 4 — Fix loop (when verifier reports FAIL)

For each verification round with blocking findings:

1. Delegate **one or more fresh implementer subagents** (parallel when findings are independent):
   - Each prompt: plan path, specific finding numbers to resolve, minimal scope fix
   - Do not re-implement unrelated todos
2. After fixes, delegate a **completely new verifier subagent** (never resume the previous verifier).

Repeat **Phase 2 (fixes only) → Phase 3 → Phase 4** until the verifier returns **PASS** with zero blocking findings.

Optional: after PASS, one readonly explore subagent may do a quick regression scan if the plan touched critical paths; any new blocking issues restart Phase 4.

---

## Iteration rules

```
loop:
  implement (1+ subagents, parallel when safe)
  verify  (1 fresh readonly subagent)
  if blocking findings: fix (1+ subagents) → goto verify
  until verifier PASS
```

Hard rules:

- **Never** reuse a subagent session across implement / verify / fix phases
- **Never** let the verifier implement fixes
- **Never** skip verification because an implementer reported success
- Cap iteration at **10** full verify rounds; if still failing, stop and report remaining findings to the user
- Prefer more subagents over broader prompts when the plan allows it

---

## Parallelization guide

Maximize subagents when:

- Todos have no ordering dependency in the plan body
- Todos touch disjoint file sets
- Exploration targets different sub-projects

Serialize when:

- The plan explicitly orders steps or uses **Phase A → B → C** in the body
- Later todos depend on earlier artifacts (SQL subject before capture script, script before findings doc)
- Multiple todos modify the same file (e.g. shared `_investigation-step-02.md` or one service file)
- A todo is **operator/manual** and its output is input to the next todo

When in doubt, serialize conflicting todos and parallelize the rest.

**Optional-grep / optional-\*** todos may run in parallel with other work or after implementation, per the plan body; do not treat "optional" as "skip verification."

---

## Critical constraints

### Orchestrator only

Do NOT:

- directly edit application source code
- run `format:check`, broad lint, broad test, or full monorepo build yourself (delegate **scoped, time-bounded** tests only when the plan requires evidence)
- perform the spec audit yourself
- accumulate implementation detail across phases

### Context isolation is mandatory

Each Task invocation is disposable. Verifier prompts must not include implementer chain-of-thought, only plan path, scope, and objective artifacts (diff summary, todo ids, commands run).

### Preserve workflow discipline

Do not merge implement and verify into one subagent.

Do not skip verification after partial implementation unless the user explicitly asks for a work-in-progress stop.

### Monorepo discipline

Implementer subagents must scope work per `AGENTS.md`. Do not search the entire monorepo blindly.

### Commits

Do not create git commits unless the user explicitly requests it. Implementers should leave changes staged or unstaged per user preference stated in the invocation.

---

## Completion criteria

The workflow is complete only when:

- A verifier subagent returns **PASS**
- Zero **blocking** findings remain
- Every plan todo is satisfied and may be marked `completed` in the plan frontmatter
- You have summarized for the user:
  - plan name and path
  - number of implement / verify / fix rounds
  - todos completed
  - scoped verification evidence (commands, outcomes, durations; no format:check unless user ran it)
  - any minor non-blocking notes deferred

If the plan cannot be fully implemented (missing deps, ambiguous spec), stop after the latest verifier round, report blockers, and list what the user must clarify in the plan file.

---

## Invocation examples

**Full plan:**

> Use the implement-plan skill on `.compozy/tasks/my-feature/_step-01.md`

**Single todo retry:**

> Use implement-plan for todo `capture-script` from `<plan.md>` and re-verify the full plan

**Re-verify only (all todos already completed):**

> Use implement-plan to verify implementation against `<plan.md>` without re-implementing

---

## Operational philosophy

You are running a small factory: many short-lived workers, strict handoffs, independent quality gate.

Favor:

- parallel implementers per todo
- readonly verifiers with checklist discipline
- evidence-backed PASS from scoped, sub-minute test runs
- minimal scope per subagent prompt

Avoid:

- one subagent implementing and self-reviewing
- the orchestrator implementing or verifying instead of delegating
- trusting implementer completion without a verifier round
- giant prompts that hide multiple todos
- speculative changes not traced to a plan line
- repo-wide `format:check`, full test suites, or multi-minute verification runs

A plan followed by isolated verification beats a single long agent session.
