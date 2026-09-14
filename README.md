# AI-Led Engineering

Cursor agent skills and research for AI-assisted software engineering.

## Skills

| Name                                                       | Description                                                                                                                                           | Install                                                                                   |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| [implement-compozy-feature](skills/implement-compozy-feature/SKILL.md) | Orchestrates an end-to-end Compozy feature build (task creation, execution, review rounds) by delegating every step to fresh isolated subagents.      | `npx skills add phillippelevidad/ai-led-engineering --skill implement-compozy-feature` |
| [implement-plan](skills/implement-plan/SKILL.md)                   | Orchestrates implementation and verification of a Cursor Plan Mode markdown file by delegating all substantive work to subagents.                   | `npx skills add phillippelevidad/ai-led-engineering --skill implement-plan`               |
| [pattern-governance](skills/pattern-governance/SKILL.md)           | Governs engineering patterns across a codebase: discovers recurring patterns, detects drift, and produces ADRs with canonical defaults for AI agents. | `npx skills add phillippelevidad/ai-led-engineering --skill pattern-governance`         |
| [pp-typescript](skills/pp-typescript/SKILL.md)                     | House TypeScript standards for naming, types, file layout, error shapes, and test placement when writing or editing .ts/.tsx code.                    | `npx skills add phillippelevidad/ai-led-engineering --skill pp-typescript`               |
| [wf-commit](skills/wf-commit/SKILL.md)                             | Writes a commit message that explains why the change exists, not what the diff shows, then commits it with `git commit -F`.                          | `npx skills add phillippelevidad/ai-led-engineering --skill wf-commit`                    |
| [wf-create-pr](skills/wf-create-pr/SKILL.md)                       | Writes a pull request title and body in a plain-English-first house format, then opens it with `gh pr create`.                                        | `npx skills add phillippelevidad/ai-led-engineering --skill wf-create-pr`                 |
| [write-agents-md](skills/write-agents-md/SKILL.md)                 | Writes or updates AGENTS.md constraint files for TypeScript projects by exploring a target folder and applying repo-specific rules.                  | `npx skills add phillippelevidad/ai-led-engineering --skill write-agents-md`             |
