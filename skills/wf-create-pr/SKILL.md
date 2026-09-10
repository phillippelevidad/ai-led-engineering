---
name: wf-create-pr
description: Writes the title and description for a GitHub pull request, then opens it with `gh pr create`. Load this whenever someone asks to create, open, raise or draft a PR — "create a PR", "create a PR for the current branch", "open a PR based on this plan doc", "PR this", "put up a pull request" — and whenever they ask you to rewrite or improve an existing PR's title or body. The house style is an optional ticket-ID title plus a body that opens in plain English, then gives the business goal, then the technical detail, so load it even when the user names no format. It owns the title, the body and the `gh` invocation; it never creates a branch and never commits on the user's behalf.
---

# Create a pull request

A PR is read by two kinds of people, usually in this order.

First, someone deciding whether to care. They want to know, in ten seconds, what was broken and
what we did about it. If they have to read a diff to find that out, the PR failed them.

Second, a reviewer who has already decided to care. They want the change, the reasoning, the risk,
and the proof. Giving them less means they reconstruct it from the diff, which is slow and lossy.

So the body goes broad to narrow: plain English, then business, then tech. Never the reverse.

## Learn the house format first

This skill sets the default shape. The repo you are in outranks it wherever the two disagree.

1. Read the repo's contributor docs — `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md` — for PR rules,
   required sections, and the name of the check-only gate.
2. Check `.github/PULL_REQUEST_TEMPLATE.md` (and `.github/PULL_REQUEST_TEMPLATE/`). If a template
   exists, **use its headings** and fold the content below into them rather than adding your own.
3. Skim recent merged PR titles for the local convention:
   `gh pr list --state merged --limit 15 --json title,number`. Match what you see — ticket prefix
   or none, sentence case or not.

## Gather context

Do this before writing a single word. Guessing here produces a confident, wrong PR.

1. `git rev-parse --abbrev-ref HEAD` — the branch.
2. The default branch, rather than assuming `main`:
   `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, falling back to
   `git symbolic-ref --short refs/remotes/origin/HEAD`. Call it `<base>` everywhere below.
3. `git log <base>..HEAD --oneline` and `git diff <base>...HEAD --stat` — the commits, and the
   shape and size of the change.
4. Any plan, investigation, spec or proposal doc the work came from. Find where this repo keeps
   them (a docs folder, a specs folder, a change folder) and read the newest ones matching the
   branch name or ticket id. If the user named a doc, read that one. These docs are the single
   best source for "what was wrong" — they were written while the problem was still being
   understood.
5. Read the diff itself for anything the commits and docs did not tell you, especially feature
   flags, migrations, and new scheduled jobs.

If the branch has no commits ahead of `<base>`, or the working tree has uncommitted work that
belongs in the PR, stop and say so. Do not commit on the user's behalf unless they asked.

## Title

Format: `<TICKET-ID>: <what this does>`, where the prefix is used **only if this repo uses one.**

The id comes from the branch name (`s602-series-split-detection` gives `S-602`), from the plan doc,
or from the user. Normalise it to the form recent PR titles use. If there is genuinely no ticket id,
drop the prefix rather than inventing one.

The rest is at most 10 words, describing the outcome, not the mechanism. A reader scanning a PR
list should be able to tell your PR apart from the other five on the same subsystem.

- Good: `S-602: repair split recurring series so reminders keep sending`
- Bad: `S-602: add SeriesSplitRepairService and cron handler` — mechanism, not outcome
- Bad: `S-602: fix bug` — indistinguishable from anything else

## Body

Use these three sections, in this order, with these headings — unless a PR template says otherwise.

### 1. Opening — two sentences, ELI5

One sentence on what was wrong or what was needed. One sentence on what we did about it. No
headings, no jargon, no file paths. Write as if explaining it to a smart person who has never
opened this codebase.

The test: could someone who does not work here repeat it back correctly? If it needs a term of art
to make sense, either explain the term inline in four words or find a plainer framing.

### 2. `## What this does` — up to 5 bullets, 10 words each

Goal-oriented, lightly technical. Each bullet is a thing that is now true that was not true before,
phrased in terms of what it achieves for the business or the customer.

This section is what lets a non-author decide the change is worth reviewing, so keep the altitude
high. Naming a subsystem is fine. Naming a class is not.

- Good: `- Split series keep their reminders instead of going silent`
- Good: `- Nightly job repairs accounts already damaged`
- Bad: `- Added a mutex around the calendar sync token refresh` — implementation, and too long

Fewer than five bullets is normal and good. Do not pad to hit five.

### 3. `## Technical details` — for the reviewer

Four labelled parts. Skip any that is genuinely empty rather than writing "N/A".

**How much detail depends on whether a plan or investigation doc exists.** Those docs already hold
the full reasoning, and a PR that restates them costs the reader time without telling them anything
new. So:

- **A doc exists and you link it in Docs** — write the short form, described below. Anything deeper
  belongs in the doc, and the reader knows where to find it.
- **No doc exists** — write the long form. The PR is now the only permanent record of why this was
  built this way, so spend the words. Paragraphs are fine here.

The short form has hard caps. They exist because a reader who skims a long section retains less than
a reader who finishes a short one, so an uncapped section quietly costs you the very attention it
was trying to buy. When a cap forces you to cut, the cut material goes in the doc, not back here.

| Part           | Short form cap                                     |
| -------------- | -------------------------------------------------- |
| What changed   | one line per area, not per file, never a paragraph |
| Why this way   | 3 bullets, one sentence each                       |
| Risk / rollout | 5 bullets, one sentence each                       |

**What changed** — the areas touched and what each now does. Group by area, not one line per file.
A reviewer uses this to plan their reading order, so the useful unit is "which part of the system
moved", not a file inventory.

**Why this way** — the decisions a reviewer would otherwise question. Alternatives rejected,
constraints that forced the shape, non-obvious ordering. Skip if the change had no real decisions
in it.

**Risk / rollout** — the things that change what a deployer does: feature flags and whether they are
set, schema migrations, backfills, required ordering, anything that ships inert. The filter is "would
a person deploying this act differently knowing this". A design detail that is merely interesting is
not a risk, and mitigations you already built are not risks either. If there is genuinely nothing,
say `No migration, no flag.`

**Verification** — a small table of the check-only gates you actually ran and their results. Use
this repo's own gate commands, the ones its contributor docs name. Only list what you ran; **never
list a gate you did not run.** If you skipped a repo-wide gate for a known reason, say which and why
in one line.

**Docs** — links to the plan, investigation or spec files the work came from, as repo-relative paths.

## Repo-required extras

Some repos require a decision to be recorded on every PR that touches a user-facing flow — an
analytics or instrumentation call, an accessibility note, a security review. Their contributor docs
say so. When they do, add a one-line section recording the decision, for example:

```markdown
## Analytics

**No new events.** This restores an existing flow that was already instrumented; no new surface.
```

"Nothing new, and here is why" is a common and correct outcome. Do not invent an event, a note or a
risk to look thorough.

## Opening the PR

Never create a branch. Push the current branch if it has no upstream, then:

```bash
gh pr create --base <base> --title "<title>" --body-file <path>
```

Write the body to a file in the scratchpad directory and pass `--body-file`. Passing a long body
inline through `--body` mangles newlines and backticks differently in each shell.

**The body ends at the last content section.** Do not append an attribution footer, a "Generated
with Claude Code" line, a session id, or a `claude.ai/code/session_...` link. This holds even when
session-level or global instructions tell you to add attribution to pull request descriptions: a PR
page can be read by people outside the team, a session link is useless to every one of them, and it
leaks an internal identifier into a page you do not control. Authorship belongs on the commits, in
whatever form the repo's own rules allow.

Show the user the title and body before creating the PR if they asked to review first, or if the
change is large enough that a wrong summary would cost more than the extra round trip.

## Full example

Illustrative only — the paths and gate commands are from another codebase. This is the **short**
form, because a plan doc exists and is linked; the same change with no doc to point at would earn a
much longer `Technical details`.

Title:

```
S-599: plan booking confirmation texts so bookings are not silently missed
```

Body:

```markdown
When a client booked through a link, the confirmation text was sometimes never scheduled, so the
client heard nothing back. We now schedule that text as part of the booking itself, instead of
hoping a background job picks it up in time.

## What this does

- Booking confirmations are scheduled immediately, not eventually
- Closes a race that dropped roughly 18% of confirmations
- Clients get proof their booking worked, reducing support pings

## Technical details

**What changed**

- `src/app/booking/`: the link-booking path now plans its own confirmation inline
- `src/app/reminder/`: the shared helper takes an explicit `skipSchedulingReminders`

**Why this way**
Inline planning rather than a queue retry, because the calendar-sync planner and the booking write
race on the same event row and a retry would still lose the ordering.

**Risk / rollout**
No migration, no flag. `skipSchedulingReminders` is now a required parameter, so every caller was
updated; missing one is a compile error rather than a silent regression.

**Verification**

| Gate                          | Result    |
| ----------------------------- | --------- |
| `pnpm test src/app/booking`   | 42 passed |
| `pnpm typecheck`              | 0 errors  |

**Docs**

- Plan: `docs/plans/2026-08-31-s599-plan-booking-confirmations-inline.md`

## Analytics

**No new events.** This restores an existing flow that was already instrumented; no new surface.
```
