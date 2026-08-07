---
name: implement-compozy-feature
description: >-
  Orchestrates an end-to-end Compozy feature build (task creation, per-task
  execution, review rounds, and review-fix rounds) by delegating every step to
  fresh isolated subagents via the Task tool. Use when the user asks to build,
  implement, or run a Compozy feature from a `.compozy/tasks/<feature>/` folder
  containing a PRD/TechSpec, or invokes the compozy-feature-builder workflow. Do
  not use for a single Cursor plan file (use implement-plan), a standalone PRD
  task (use cy-execute-task), or isolated review remediation (use cy-fix-reviews).
---

# Implement Compozy Feature

## Orchestrator mandate (non-negotiable)

When this skill is active, you are an **orchestrator only**. You coordinate the
full Compozy pipeline; you never do the work yourself.

### You MUST delegate via Task

Every substantive action runs in a **fresh subagent** via the Task tool:

- recon (Phase 0b)
- task creation (`/cy-create-tasks`)
- task execution (`/cy-execute-task`, **one subagent per task file**)
- review rounds (`/cy-review-round`, **one subagent per round**)
- review-fix rounds (`/cy-fix-reviews`, **one subagent per fix round**)
- any exploration of unfamiliar code areas

Treat each Task invocation as **single-use and disposable**.

### You MUST NOT execute yourself

Do **not** use your own tools for:

- creating, editing, or executing task files
- editing application source, config, migrations, or tests
- running shell commands (tests, scripts, builds, linters, formatters)
- producing review findings or claiming a feature is done from your own inspection
- combining creation, execution, review, or fixing in one turn

### What the orchestrator may do directly

- List the feature folder and read PRD/TechSpec/ADR/task files to build an execution map (structure only)
- Read and append to `_context.md` (see Phase 0b) — this is orchestration state, not project work
- Launch and monitor Task subagents; decide parallel vs serial waves
- Track which task files, review rounds, and fix rounds have run
- Summarize rounds, evidence, blockers, and completion for the user

If you catch yourself about to write a task, edit code, or run a command,
**stop** and delegate a subagent instead.

---

## Inputs

The user will invoke this skill with a prompt similar to:

> Use implement-compozy-feature to build `<feature-folder>`

where `<feature-folder>` is a `.compozy/tasks/<name>/` directory containing some
subset of:

- `_prd.md` and/or `_techspec.md`
- `adrs/` decision records
- `_tasks.md` master tracking file
- `task_*.md` task files (may not exist yet)

The installed `cy-*` skills already know how to interpret these files. Pass the
feature folder (and, for execution, exactly one task file path) into the
subagent prompts; do not re-implement their logic.

If the feature folder is missing or contains no `_prd.md` or `_techspec.md`,
stop and ask the user to create at least one first.

---

## Delegated skills (orchestrator never runs them itself)

| Skill                                              | Purpose                                | Isolation rule                          |
| -------------------------------------------------- | -------------------------------------- | --------------------------------------- |
| `/cy-create-tasks <feature-folder>`                | Decompose PRD/TechSpec into task files | One subagent, runs once per feature     |
| `/cy-execute-task <feature-folder>/<task-file>.md` | Implement exactly one task             | **One fresh subagent per task file**    |
| `/cy-review-round <feature-folder>`                | Produce a review round with findings   | **One fresh subagent per review round** |
| `/cy-fix-reviews <feature-folder>`                 | Remediate findings from a review round | **One fresh subagent per fix round**    |

Subagents may also use `cy-final-verify` (evidence-before-claims discipline) and
must follow `AGENTS.md` / `CLAUDE.md` where present.

**The `cy-*` skills are vendored and may be replaced by upstream updates. Never
edit them.** Where a `cy-*` instruction is wrong for the current project, the
Standard Preamble overrides it — the orchestrator's prompt is later and more
specific, so it wins. See "Known `cy-*` overrides" below.

---

## Subagent roles and model assignment

| Role              | `subagent_type`   | Model     | Responsibility                                |
| ----------------- | ----------------- | --------- | --------------------------------------------- |
| **Recon**         | `Explore`         | `sonnet`  | Phase 0b discovery; writes `_context.md`      |
| **Task creator**  | `general-purpose` | `opus`    | Run `/cy-create-tasks`; generate task files   |
| **Task executor** | `general-purpose` | see below | Run `/cy-execute-task` for **one** task file  |
| **Reviewer**      | `general-purpose` | see below | Run `/cy-review-round`; produce findings only |
| **Fixer**         | `general-purpose` | `sonnet`  | Run `/cy-fix-reviews`; remediate one round    |

**Model rules:**

- **Task creator → `opus`.** A task file is itself a specification. A bad
  decomposition poisons every downstream executor, so this is the
  highest-leverage judgment call in the run.
- **Task executor → `sonnet` by default, `opus` when the task file declares
  high complexity** (or the task involves an architectural choice, a spec
  contradiction, or a security-sensitive surface). Well-scoped implementation is
  execution work; genuine design calls are not.
- **Reviewer → `opus` for rounds 1-2, `sonnet` from round 3 onward** or as soon
  as a round returns fewer than ~6 findings. Early rounds find the real defects
  and need reasoning; later rounds are confirmation.
- **Fixer → `sonnet`.** The fixer is handed a diagnosis; that is execution.
- **Recon → `sonnet`.** Mechanical discovery. `haiku` is acceptable for a small,
  single-sub-project codebase.

Only `sonnet`, `opus`, `haiku`, and `fable` are valid model values. **Version
strings such as `claude-opus-4-8` are rejected** — pass the family name only.

Never combine two phases (create / execute / review / fix) in one subagent.

---

## Core workflow

Follow this strictly. Do not skip or merge phases.

### Phase 0a — Intake (orchestrator only)

List the feature folder and read PRD/TechSpec/ADRs to build an execution map:

- whether task files already exist (skip Phase 1 if a complete set exists and the user did not ask to regenerate)
- the ordered list of task files and their declared dependencies
- which tasks can run in **parallel** (no dependency, no shared output file)
- which sub-projects the feature will touch

Do not edit anything in this phase.

### Phase 0b — Recon (one subagent, runs once, before any other phase)

The purpose is to discover **once** what every later subagent would otherwise
rediscover independently. Delegate **one fresh subagent** (`Explore`, `sonnet`)
to investigate the sub-projects identified in Phase 0a and write
`<feature-folder>/_context.md`.

Recon MUST discover and record, for each sub-project the feature will touch:

1. **Verification commands, read from the project's own manifests** (e.g.
   `package.json` scripts, `Makefile` targets, `pyproject.toml`, `go.mod`).
   Record the exact check-only commands for: typecheck, lint, format check, unit
   tests, and single-file test invocation. **Never assume a command exists —
   confirm it is defined.** Record which commands are check-only and which
   mutate files.
2. **Test runner gotchas**: required env vars (e.g. `TZ`), typical runtime,
   whether type errors are suppressed in the test runner, known-slow suites.
3. **Repo hygiene facts**: whether the feature folder itself is gitignored, which
   paths are excluded from formatters, pre-existing check failures that agents
   must report rather than fix.
4. **Commit protocol**: hook behavior, staging conventions, branch rules.
5. **Applicable convention skills or docs** (`AGENTS.md`, `CLAUDE.md`,
   project pattern skills) and the specific rules that bind this feature.

`_context.md` is orchestration state, not deliverable work. It lives in the
feature folder. If that folder is gitignored, the file is machine-local and will
not survive to another checkout — record that fact in the file itself so a
resumed run knows to re-run recon.

Recon is **read-only**: it discovers and writes `_context.md`, nothing else. It
does not run mutating commands and does not commit.

### Phase 0c — Compose the Standard Preamble (orchestrator only)

Read `_context.md` and compose the Standard Preamble **once** (see the section
below). Reuse it verbatim in every subsequent subagent prompt, appending only
the task-specific body. Do not re-derive it per subagent.

### Phase 1 — Task creation (one subagent, runs once)

If task files do not yet exist, delegate **one fresh subagent** (`opus`):

- Prompt: Standard Preamble + run `/cy-create-tasks <feature-folder>`
- The subagent owns all reading and decomposition; the orchestrator does not
- Require it to report, per task: declared dependencies, output paths, and
  whether the task is high complexity (this drives executor model selection)

When it completes, **discard its context entirely**. Phase 1 runs **once per
feature**.

### Phase 2 — Task execution (one subagent per task, no exceptions)

For each task file, delegate **exactly one new isolated subagent**:

- Prompt: Standard Preamble + run `/cy-execute-task <feature-folder>/<task-file>.md`
- Pass the feature folder for PRD context **and exactly one task file path**
- Select the model per the task's declared complexity (see Model rules)

**Strict one-task-per-subagent rule:**

- Each task file gets its own dedicated subagent invocation.
- A single subagent must NEVER execute two or more tasks, even sequentially.
- Do not batch tasks into one prompt; do not resume or reuse a prior task subagent for the next task.
- After a subagent completes one task, discard that context before starting the next.

**Parallelization is the default, not the exception.** Launch every task whose
dependencies are satisfied in a single message with multiple Task calls.
Serialize only tasks that declare a dependency, write to the same file, or are
explicitly ordered by the TechSpec.

Concurrent agents share one git index. The Standard Preamble's path-only staging
rule is what makes parallel commits safe — **do not respond to a staging
collision by serializing the whole run.** Fix the staging discipline instead.
Do not reach for worktree isolation unless agents genuinely mutate the same
files; in dependency-heavy projects the per-worktree install cost typically
exceeds the parallelism gained.

After each wave, append any cross-cutting discovery the agents reported to
`_context.md` (see "Living context" below).

### Phase 3 — Review round (one fresh subagent per round)

After all task execution completes, delegate **one new isolated subagent**:

- Prompt: Standard Preamble + run `/cy-review-round <feature-folder>`
- Model per the Model rules (opus early, sonnet once converging)
- Pass forward, as objective artifacts only: the commit shas of prior phases,
  the list of accepted deviations, and known operational items — so the reviewer
  does not re-raise settled decisions as new findings

From round 3 onward, frame the round as a **convergence check** and state
explicitly that "no remaining blocking issues" is a valid, expected outcome.
Require honest severity: "blocking" is reserved for defects that break a user,
lose data, cost money, or expose a security hole.

The reviewer must not share context with creation, execution, fix, or previous
review subagents.

### Phase 4 — Fix round (one fresh subagent per round)

If Phase 3 produced blocking findings, delegate **one new isolated subagent**:

- Prompt: Standard Preamble + run `/cy-fix-reviews <feature-folder>`
- Model: `sonnet`

**Fixers MUST self-verify before committing.** Fix rounds are the single largest
source of new defects: a large remediation sweep routinely introduces the
regressions the next review then finds. Every fixer prompt MUST require:

- re-running the specific tests covering every file it touched, not only the
  ones tied to the issue it was fixing
- a self-diff against the issue list before committing, confirming each change
  maps to a finding and that no change introduces behavior outside the round's scope
- explicitly reporting any finding it deferred, and why

When fixes complete, **discard that context** and start a **completely fresh
review subagent** (back to Phase 3). Never reuse a fix subagent for review, and
never reuse a fix subagent across fix rounds.

---

## The Standard Preamble

Compose this once in Phase 0c from `_context.md`, then paste it verbatim into
**every** subagent prompt. It exists so no subagent has to rediscover what a
previous one already learned.

It MUST carry:

**1. Fan-out and wait discipline (highest-value rule in this skill)**

> Do not fan out into many parallel subagents. Do the work yourself, or use at
> most 2 helpers. Do not arm polling loops, monitors, or wait-loops to track
> helpers — return directly when your work is done.

Unbounded sub-delegation is the dominant catastrophic failure mode: it exhausts
session limits mid-round and leaves orphaned monitors that fire duplicate
completion notifications long after the agent finished, burning orchestrator
turns. Carry this rule in every prompt, without exception.

**2. Verification commands and scope** — the exact check-only commands recon
found, plus:

- Run only tests exercising code changed in this task/fix.
- Prefer single-file invocations over package-wide ones.
- Do not run repo-wide suites, repo-wide lint, format checks, or full builds
  unless this feature's spec explicitly requires that breadth.
- Report pre-existing failures; never silently fix unrelated ones.

**3. Timeouts** — a per-command cap calibrated from recon's observed runtimes,
not a fixed number. A cap so tight that agents routinely breach and retry costs
more than it saves. If a run exceeds the cap, narrow scope rather than extending.

**4. Staging and commit rules**

> Stage ONLY the files you changed, explicitly by path. Never `git add -A` or
> `git add .`. Never skip hooks. Never amend. Never create a branch.

**5. Repo hygiene facts from `_context.md`** — gitignored paths (so agents stop
reporting the same uncommittable tracking files), formatter exclusions, known
pre-existing check failures.

**6. Accepted deviations and settled decisions to date** — so later agents
neither re-litigate them nor undo them.

**7. Cross-cutting discoveries from earlier phases** (see below).

### Known `cy-*` overrides

State these explicitly in the preamble whenever they apply:

- **Verification breadth.** `cy-final-verify` mandates running "the full
  pipeline, not a subset" before commit. In a monorepo this means **the touched
  sub-project's full gate**, not the repository root's. Say so, or every agent
  that commits will burn tool calls deciding between two contradictory rules.
- **Hardcoded example commands.** `cy-*` skills cite commands from their origin
  project (e.g. `make lint`, `make verify`) that may not exist here. The
  preamble's discovered commands supersede them.
- **Language-specific templates.** Issue templates may default to another
  language's file extensions. State the project's actual languages.

### Living context

`_context.md` is append-only working memory for the run. Between phases, the
orchestrator appends any discovery that a later agent would otherwise repeat:

- a convention correction (e.g. a pattern skill overriding the task text)
- a spec claim proven false during implementation
- a tooling bug or trap one agent lost time to
- a decision the user made mid-run

Append the fact and its consequence, not the agent's reasoning. Keep it terse
and factual. This file is the antidote to N agents independently paying the same
discovery cost.

---

## Iteration rules

Phases 0a-0c and 1-2 run **once** per feature. Then repeat:

```
loop:
  review   (1 fresh subagent — Phase 3)
  if blocking findings:
    fix    (1 fresh subagent — Phase 4)
    goto review
  until review reports no remaining blocking issues
```

Hard rules:

- **Never** reuse a subagent session across create / execute / review / fix phases.
- **Never** reuse a subagent across task files, review rounds, or fix rounds.
- **Never** let a reviewer fix issues, or a fixer self-review its own round's findings.
- **Never** skip a fresh review round after fixes.
- Cap iteration at **10** review rounds; if still failing, stop and report remaining findings to the user.

**Batching guidance:** when a round returns many findings, prefer having the
fixer address blocking findings first and sweep non-blocking ones in a later
round. Large mixed sweeps are the pattern that seeds the next round's
regressions. This is a default, not a prohibition — a round of small, obviously
independent fixes may safely be handled in one pass.

---

## Human decision gates

Some findings are product calls, not engineering calls: analytics instrumentation
requiring approval, behavior contradicting a stated requirement, changes
affecting live user data.

**Surface these to the user as early as they are known.** Where a project
mandates propose-then-stop for a category of change, that phase will block; a
decision the user could have made in Phase 0 avoids an entire extra subagent
later. When a subagent reports a decision gate, put it to the user before the
next phase rather than deferring to the end.

Do not manufacture gates. Most rounds have none.

---

## Critical constraints

### Context isolation is mandatory

Every phase executes in a fresh isolated subagent. In Phase 2 this means one
subagent per task file. Never allow review contamination, cross-task context
accumulation, cross-phase context accumulation, or long-running mixed-context
sessions. Do not pass a subagent's chain-of-thought into the next subagent; pass
only objective artifacts (paths changed, task ids, review round numbers,
`_context.md` facts).

### Preserve workflow discipline

Do not skip phases. Do not merge phases. Do not allow review and implementation
in the same subagent. Do not allow multiple task executions in one subagent.
Strict separation is required.

### Commits

Subagents MUST commit their work at natural completion boundaries unless the
user explicitly forbids commits. Pass any user commit preference into every
subagent prompt; when the user is silent, treat commits as required.

Required boundaries:

- A task executor MUST commit after a task is fully implemented and scoped
  verification has passed.
- A fixer MUST commit after a fix round has remediated findings and scoped
  verification has passed.
- A task creator SHOULD commit after generating or regenerating task files when
  those files are new or materially changed.

Commit rules:

- Each commit MUST cover only the work from that subagent's phase (one task, one
  fix round, or one task-creation pass).
- Subagents MUST stage explicitly by path, write a concise why-focused message,
  never skip hooks, and never amend unless the project's amend rules are met.
- The orchestrator MUST NOT commit; only the subagent that produced the changes
  MAY create the commit.
- If a subagent cannot commit (hook failure, secrets in the diff, empty tree, or
  the target path is gitignored), it MUST report the blocker and MUST NOT claim
  the phase complete until the commit succeeds or the user overrides.

---

## Completion criteria

The workflow is complete only when:

- A review round reports no remaining blocking issues
- All review rounds converge successfully
- Every task has been executed by its own subagent

At completion, summarize for the user:

- feature name and folder path
- number of tasks executed (one subagent each)
- number of review and fix rounds, and the finding trend across them
- resolved issue categories and scoped verification evidence
- any minor non-blocking notes deferred
- **any operational or human action still required before the work can ship**

If the feature cannot be fully implemented (missing deps, ambiguous spec, or 10
review rounds without convergence), stop after the latest review round, report
blockers, and list what the user must clarify.

---

## Invocation examples

**Full feature build:**

> Use implement-compozy-feature to build `.compozy/tasks/event-phone-resolution-pipeline/`

**Resume after tasks already created:**

> Use implement-compozy-feature on `.compozy/tasks/my-feature/`; tasks already exist, start execution

**Review-only loop:**

> Use implement-compozy-feature to run review and fix rounds on `.compozy/tasks/my-feature/` until it passes

---

## Operational philosophy

You are coordinating a disciplined engineering pipeline, not improvising. You run
a small factory of short-lived, single-use workers with strict handoffs.

Favor:

- one disposable subagent per task, per review round, and per fix round
- parallel task executors whenever dependencies allow
- discovering a fact once and carrying it forward, rather than N agents rediscovering it
- matching model capability to the nature of the work, not to its importance
- isolation, repeatability, determinism, narrow context windows, strict phase boundaries

Avoid:

- the orchestrator implementing, reviewing, or fixing instead of delegating
- unbounded sub-delegation, polling loops, or monitors inside subagents
- giant mixed-context sessions or batching multiple tasks into one subagent
- serializing work that path-scoped staging already makes safe
- reusing a subagent across phases or rounds
- speculative changes outside review scope
- repo-wide format checks, full test suites, or multi-minute verification runs

A clean, isolated workflow beats a clever one.
