# AI-Led Engineering

Meta-repo for AI-native engineering standards, research, and Cursor agent skills.

## Content pipeline

`brainstorming/` → `research/` → `skills/` — draft, then canonical, then executable. Promote upstream only when stable.

## Folder roles

| Path              | Purpose                              |
| ----------------- | ------------------------------------ |
| `brainstorming/`  | Scratch notes — not source of truth  |
| `research/`       | Curated standards — basis for skills |
| `skills/`         | Skills we author                     |
| `.agents/skills/` | Installed skills — do not edit       |
| `.claude/skills/` | Synced from `.agents/` — never edit  |

## Before changing anything

1. Read the nearest `AGENTS.md`.
2. For standards, read `research/ai-engineering-principles/playbook.md`.
3. Match tone: explicit, enforceable, agent-oriented.

Run `npm run sync-claude-skills` after installing into `.agents/skills/`.

## Other rules

- **Never** treat brainstorming as canonical, author under `.agents/skills/`, or add directory maps.
