# Non-software example

A minimal docs/research `AGENTS.md`. No stack, commands, or testing sections — the agent only needs lifecycle, conventions, and boundaries.

Based on a real pattern: a curated research folder inside a meta-repo where skills derive from standards.

---

## Example output (~25 lines)

~~~markdown
# Research

Curated source of truth for AI-native engineering. Skills derive from here — not the reverse.

## Canonical doc

`ai-engineering-principles/playbook.md` is the active standard. If agent files conflict with it, **the playbook wins**.

## Lifecycle

```
brainstorming/ → research/ → skills/
```

Accept content after review, not raw from brainstorming. When research stabilizes, extract a skill into `skills/`. Keep research human-readable; keep skills terse.

## Writing rules

- RFC 2119 levels for rules: MUST, SHOULD, MAY.
- Tag enforceable rules with **Enforced by** (tool, CI, or named reviewer).
- Prefer explicit guidance over clever abstractions.
- Document *why* here; skills carry the *how*.

## Do not

Store scratch notes here, duplicate full skill workflows, or maintain a hand-written directory map.
~~~

---

## Why this shape works

| Section | Purpose |
| ------- | ------- |
| **Identity** (title + one line) | Tells the agent this is canonical content, not scratch work |
| **Canonical doc** | Resolves conflicts — one file wins when rules disagree |
| **Lifecycle** | Non-obvious promotion path the agent would otherwise skip or invert |
| **Writing rules** | Tone and format constraints linters don't enforce |
| **Do not** | Cheapest mistake prevention — no directory maps, no skill duplication |

## Sections omitted (and why)

| Section | Why omitted |
| ------- | ----------- |
| Stack / tooling | Markdown only — nothing to guess wrong |
| Layout | Parent repo `AGENTS.md` already defines folder roles; repeating here would drift |
| Commands / workflow | No build step; promotion is a human/agent judgment call described in lifecycle |
| Hard constraints | Folded into **Do not** — keeps the file short |
| Testing / validation | No automated test suite; review gate is described in lifecycle |
| Out of scope | **Do not** covers the highest-cost mistakes for this folder size |

## When to add more sections

Add **Commands / workflow** when the folder has a non-obvious publish pipeline (e.g. `npm run build-docs`, link checker in CI).

Add **Hard constraints** separately when "do not edit" rules are numerous or security-sensitive (credentials paths, generated sites).

Add **Out of scope** when boundaries are broader than a short **Do not** list — e.g. "never refactor sibling folders", "never install packages in this directory".
