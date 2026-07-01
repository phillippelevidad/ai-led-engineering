---
name: write-agents-md
description: >-
  Writes or updates AGENTS.md constraint files for any project — software repos, monorepo
  subfolders, docs, research, or other workspaces — by exploring a target folder and applying
  repo-specific rules. Use when the user asks to create, write, or update AGENTS.md, references
  a project or subfolder for agent guidance, or provides context for agent onboarding docs.
---

# Write AGENTS.md

## Inputs

The user provides:

1. **Target folder** — project root or subfolder path (relative or absolute)
2. **Additional context** — deployment model, boundaries, known pitfalls, out-of-scope areas, or anything not obvious from the folder

If either is missing, ask before writing.

## Workflow

```
Task Progress:
- [ ] Step 1: Confirm target path and output location
- [ ] Step 2: Classify the project and explore (read-only)
- [ ] Step 3: Check for parent or sibling AGENTS.md files
- [ ] Step 4: Draft AGENTS.md
- [ ] Step 5: Validate against rules below
- [ ] Step 6: Write file and report line count
```

### Step 1: Confirm target path

- Output file: `<target-folder>/AGENTS.md`
- If the target is a monorepo subfolder, write a **scoped** AGENTS.md for that subfolder only. Do not duplicate the root monorepo map unless the user asked for the root file.
- If content would exceed ~150 lines, split: keep the root file as a map + cross-cutting rules; put subfolder-specific rules in scoped `AGENTS.md` files.

### Step 2: Classify the project and explore (read-only)

First infer what kind of workspace this is (application, library, docs/research, content, infra, mixed). Read only what the agent cannot infer from defaults. Prioritize:

| Signal | Extract |
| ------ | ------- |
| Manifest / build files | Package manager, scripts, language/runtime version, module layout |
| Tool configs | Compiler, linter, formatter, or test runner settings the agent would guess wrong about |
| Directory layout | Only non-standard paths (unusual test location, domain vs lib split, content vs templates split, etc.) |
| Existing docs | README, `.agents/docs/*-stack.md`, style guides, contribution docs with runtime or workflow facts |
| Sub-project skills | `.agents/skills/*` when present for the same area |
| CI / env / publishing | Side-effect requirements (DB, credentials, approval gates, deploy targets) |

For ecosystem-specific files to read, see [references/exploration-signals.md](references/exploration-signals.md).

For **non-software** workspaces (docs, research, design, ops runbooks), prioritize README, templates, folder roles, tone/style guides, and approval or publishing workflow over build manifests. See [references/non-software-example.md](references/non-software-example.md) for a minimal example.

Do **not** copy config verbatim into AGENTS.md. Distill into imperative constraints the agent would otherwise get wrong.

### Step 3: Check existing AGENTS.md files

- Read parent `AGENTS.md` (e.g. repo root) to avoid duplicating monorepo-wide rules.
- Read sibling sub-project files for consistent tone and section naming.
- Reference upstream rules ("follow root AGENTS.md for formatting") instead of repeating them.

### Step 4: Draft structure

Use this section order. **Omit sections with nothing non-obvious to say** — many non-software projects need only identity, conventions, hard constraints, and out of scope (see [references/non-software-example.md](references/non-software-example.md)).

```markdown
# [Project name]

[One-sentence identity: what it is, what it does, and its audience, runtime, or output target.]

## Stack / tooling

[Only non-obvious choices: language/runtime version, test runner, CMS, ORM, build tool, non-default tooling. Omit for pure content workspaces.]

## Layout

[Only paths that contradict default assumptions for this project type.]

## Commands / workflow

[Exact commands or steps: dev, test, build, lint, publish, review. Note side effects: Docker, DB, credentials, approval gates. Omit if no repeatable workflow.]

## Conventions

[Imperative rules only: "Use X", "Never Y". Architectural boundaries, error handling, tone, naming, what goes where.]

## Hard constraints

[Files/dirs that must not be modified. Dependencies or tools that must not be added silently. Non-negotiable invariants.]

## Testing / validation

[Framework, file location, mocking approach, minimum expectations. Omit when not applicable.]

## Out of scope

[What the agent must not touch or do unprompted.]
```

### Step 5: Validate

Before writing, check every line against the rules in the next section. Remove anything the agent can read from config files, anything vague, and anything duplicated from parent AGENTS.md.

### Step 6: Write and report

- Write `<target-folder>/AGENTS.md`
- Report final line count. If over 150 lines, recommend splitting into scoped files.
- Do not commit unless the user asks.

---

## Rules for Good `AGENTS.md`

### Length

**80–150 lines.** Over 200 and the important rules dilute into noise. If you're hitting that ceiling, add scoped `AGENTS.md` files in subdirectories instead of growing the root one.

---

### What to Include

**1. Project identity** — One sentence: what it is, what it does, and who or what it serves (runtime, audience, output format). Enough for the agent to pick the right idioms.

**2. Stack / tooling** — Only choices where version or tool is non-obvious or where the agent would otherwise guess wrong. Not a dump of manifests or lockfiles. Key things: language/runtime version, test runner, data layer, CMS, build tool, any non-default tooling. Skip for workspaces with no toolchain.

**3. Non-obvious layout** — Only what contradicts the agent's default assumptions for this project type. Standard `src/components` in a React app? Skip it. Tests in an unusual location? Document it. For content repos: which folders are canonical vs scratch.

**4. Commands / workflow** — Exact commands or steps for dev, test, build, lint, publish, review. Use the actual package manager or task runner. Note which require side effects (Docker, DB, credentials, human approval). Skip when there is no repeatable workflow.

**5. Conventions** — Only rules where the agent would otherwise make a wrong choice. Imperative statements only: "Use X", "Never Y". Not suggestions, not prose. Focus on things automated tools can't enforce: architectural boundaries, error handling patterns, tone, naming, what goes where.

**6. Hard constraints** — Separate section. Files or directories that must not be modified. Dependencies or tools that must not be added silently. Non-negotiable invariants.

**7. Testing / validation** — Framework, file location convention, mocking approach, minimum expectations. For non-software: spell-check gates, link checks, review requirements. Omit when not applicable.

**8. Out of scope** — Explicit list of what the agent must not touch or do unprompted. This is the most underused section and prevents the most expensive mistakes.

---

### What NOT to Include

- Anything the agent can read directly from config files (manifests, lockfiles, linter configs, compiler settings)
- Git/PR workflow
- Vague quality statements ("write clean code", "be careful with X")
- Business/domain logic — that belongs in task prompts
- Justifications for why rules exist — directives only
- Changelog or history
- ASCII architecture diagrams
- Duplicate information that will drift out of sync with the real source

---

### The Core Principle

An `AGENTS.md` is not documentation for a careful human reader. It's constraints for a system that will find the path of least resistance through your workspace. Your job is to make the correct path also the easiest one.

---

## Additional resources

- [references/exploration-signals.md](references/exploration-signals.md) — manifest and config files to read by ecosystem (JS/TS, Python, Rust/Go, infra, non-software). Read during Step 2.
- [references/non-software-example.md](references/non-software-example.md) — minimal docs/research example with section-by-section rationale. Read when the target folder has no toolchain.
