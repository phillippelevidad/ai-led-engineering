# Skills (authored)

Agent skills we write live here. Installed skills live in `.agents/skills/`.

## When to add

When `research/` has stable guidance agents should invoke — not for drafts or one-offs.

## Structure

`skills/<name>/SKILL.md` (required), plus optional `references/` and `scripts/`. See `pattern-governance/` as reference.

## SKILL.md rules

- Frontmatter: `name`, `description` (drives auto-invocation).
- State scope, deliverables, and out-of-scope boundaries.
- Use ALWAYS / NEVER / PREFERRED / FORBIDDEN.
- One job per skill.

## Workflow

1. Derive from promoted `research/`, not `brainstorming/`.
2. Author under `skills/<name>/`.
3. Update root `README.md` skills table.

## Do not

Edit `.agents/skills/` for authored work, open-ended code review, or duplicate long research — link instead.
