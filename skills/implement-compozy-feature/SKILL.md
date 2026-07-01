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
must follow `AGENTS.md` (monorepo map). The orchestrator does not run these.

---

## Subagent roles

| Role                    | `subagent_type`  | Mode       | Responsibility                                 |
| ----------------------- | ---------------- | ---------- | ---------------------------------------------- |
| **Task creator**        | `generalPurpose` | read-write | Run `/cy-create-tasks`; generate task files    |
| **Task executor**       | `generalPurpose` | read-write | Run `/cy-execute-task` for **one** task file   |
| **Reviewer**            | `generalPurpose` | read-write | Run `/cy-review-round`; produce findings only  |
| **Fixer**               | `generalPurpose` | read-write | Run `/cy-fix-reviews`; remediate one round     |
| **Explorer** (optional) | `explore`        | readonly   | Pre-work codebase recon for an unfamiliar area |

Never combine two phases (create / execute / review / fix) in one subagent.

---

## Core workflow

Follow this strictly. Do not skip or merge phases.

### Phase 0 — Intake (orchestrator only)

List the feature folder and read PRD/TechSpec/ADRs to build an execution map:

- whether task files already exist (skip Phase 1 if a complete set exists and the user did not ask to regenerate)
- the ordered list of task files and their declared dependencies
- which tasks can run in **parallel** (no dependency, no shared output file)
- relevant sub-project(s) from `AGENTS.md`

Do not edit anything in this phase.

### Phase 1 — Task creation (one subagent, runs once)

If task files do not yet exist, delegate **one fresh subagent**:

- `subagent_type: generalPurpose`
- Prompt: run `/cy-create-tasks <feature-folder>`; read specs, generate task files, prepare implementation work
- The subagent owns all reading and decomposition; the orchestrator does not

When it completes, **discard its context entirely** and return to orchestration.
Phase 1 runs **once per feature**.

### Phase 2 — Task execution (one subagent per task, no exceptions)

For each task file produced in Phase 1 (e.g. `task_01.md`, `task_02.md`),
delegate **exactly one new isolated subagent**:

- `subagent_type: generalPurpose`
- Prompt: run `/cy-execute-task <feature-folder>/<task-file>.md`
- Pass the feature folder for PRD context **and exactly one task file path**

**Strict one-task-per-subagent rule:**

- Each task file gets its own dedicated subagent invocation.
- A single subagent must NEVER execute two or more tasks, even sequentially.
- Do not batch tasks into one prompt; do not resume or reuse a prior task subagent for the next task.
- After a subagent completes one task, discard that context before starting the next.

**Parallelization:** launch independent tasks (no dependency, disjoint files) in
parallel using a single message with multiple Task calls. Serialize tasks that
declare dependencies, share an output file, or are ordered by the TechSpec.
Phase 2 with N tasks means **N fresh subagent invocations**.

Each executor is solely responsible for its one task: implementing per spec,
running scoped validation, and updating task tracking. It must not share context
with the task creator, other executors, reviewers, or fixers.

When all tasks are executed, discard each context and return to orchestration.

### Phase 3 — Review round (one fresh subagent per round)

After all task execution completes, delegate **one new isolated subagent**:

- `subagent_type: generalPurpose`
- Prompt: run `/cy-review-round <feature-folder>`; analyze implementation state, identify issues, produce a review round directory with findings

The reviewer must not share context with creation, execution, fix, or previous
review subagents. Always isolate review runs. Each review round is a brand-new
subagent.

### Phase 4 — Fix round (one fresh subagent per round)

If Phase 3 produced blocking findings, delegate **one new isolated subagent**:

- `subagent_type: generalPurpose`
- Prompt: run `/cy-fix-reviews <feature-folder>`; address the review findings, update the implementation, resolve discovered issues

When fixes complete, **discard that context** and start a **completely fresh
review subagent** (back to Phase 3). Never reuse a fix subagent for review, and
never reuse a fix subagent across fix rounds.

---

## Iteration rules

Phases 1 and 2 run **once** per feature. Then repeat:

```
loop:
  review   (1 fresh subagent — Phase 3)
  if blocking findings:
    fix    (1 fresh subagent — Phase 4)
    goto review
  until review reports no remaining issues
```

Hard rules:

- **Never** reuse a subagent session across create / execute / review / fix phases.
- **Never** reuse a subagent across task files, review rounds, or fix rounds.
- **Never** let a reviewer fix issues, or a fixer self-review.
- **Never** skip a fresh review round after fixes.
- Cap iteration at **10** review rounds; if still failing, stop and report remaining findings to the user.

---

## Scoped test execution (pass into every subagent prompt)

This is a large monorepo. Every executor, reviewer, and fixer prompt must carry
these limits:

- **Keep tests focused.** Run only tests that exercise the code changed in the current task/fix. Do not expand to unrelated modules.
- **1-minute cap per test command.** Use `timeout 60` (or `--testTimeout=60000` for Jest) per invocation. If a run exceeds the cap, stop and narrow scope instead of extending.
- **No broad runs.** Do not run the full repo suite, root `npm test`, repo-wide lint, `format:check`, or full builds unless the task spec or `cy-final-verify` explicitly requires that breadth.
- **Narrow to specific files.** Prefer `jest path/to/changed.test.ts` in the relevant sub-project over package-wide invocations.
- **Scope per `AGENTS.md`.** Subagents must not search the entire monorepo blindly.

---

## Critical constraints

### Context isolation is mandatory

Every phase executes in a fresh isolated subagent. In Phase 2 this means one
subagent per task file. Never allow review contamination, cross-task context
accumulation, cross-phase context accumulation, or long-running mixed-context
sessions. Do not pass a subagent's chain-of-thought into the next subagent; pass
only objective artifacts (paths changed, task ids, review round numbers).

### Preserve workflow discipline

Do not skip phases. Do not merge phases. Do not allow review and implementation
in the same subagent. Do not allow multiple task executions in one subagent.
Strict separation is required.

### Commits

Do not create git commits unless the user explicitly requests it (or the feature
folder's auto-commit mode dictates it via the `cy-*` skill). Pass the user's
stated commit preference into subagent prompts.

---

## Completion criteria

The workflow is complete only when:

- A review round reports no remaining blocking issues
- All review rounds converge successfully
- Every task has been executed by its own subagent

At completion, summarize for the user:

- feature name and folder path
- number of tasks executed (one subagent each)
- number of review and fix rounds
- resolved issue categories and scoped verification evidence
- any minor non-blocking notes deferred

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
- parallel task executors when tasks are independent
- isolation, repeatability, determinism, narrow context windows, strict phase boundaries

Avoid:

- the orchestrator implementing, reviewing, or fixing instead of delegating
- giant mixed-context sessions or batching multiple tasks into one subagent
- reusing a subagent across phases or rounds
- speculative changes outside review scope
- repo-wide `format:check`, full test suites, or multi-minute verification runs

A clean, isolated workflow beats a clever one.
