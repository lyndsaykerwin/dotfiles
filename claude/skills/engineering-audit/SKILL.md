---
name: engineering-audit
description: Audit a workspace, skill, agent file, routine, or set of related config files for engineering hygiene — DRY violations, context bloat, filler content, repeated expensive operations, stale facts, and broken pointers. Use when the user says "audit this", "check for duplication", "is this too much context", "DRY check", "review the architecture of [X]", "find what's repeated", or after a refactor when she wants confidence the cleanup actually cleaned up. Outputs a structured report with each finding tagged by severity + concrete fix. Does NOT auto-apply fixes — the report is for the user (or another agent) to act on.
---

# Engineering Audit

A structured pass over a set of files to find the issues that bloat context, cause drift, and waste expensive operations. Designed to catch what an experienced engineer would catch on a code review.

## When to invoke

Trigger phrases include:
- "audit this"
- "audit the [X] skill / workspace / agent"
- "DRY check on [files]"
- "is this overloading context"
- "check what's repeated across [these files]"
- "review the architecture of [X]"
- "find filler content"
- "is anything stale here"
- "spot the engineering issues in [X]"

Also use **proactively** at the end of any refactor/cleanup task — before declaring done, run a quick pass to confirm the cleanup didn't introduce new duplication or stale references.

## Scope of input

The user names a target. The skill audits:
- A **single file** (one SKILL.md, one agent .md, one config)
- A **directory** (e.g. a workspace, a skill folder)
- A **named system** (e.g. "the apple-mail toolkit" → all skills in `~/.claude/skills/apple-mail-*` + `~/.claude/preferences/apple-mail/` + any workspace `apple-mail-config.json` + any scheduled tasks)
- A **set of files** the user lists explicitly

If the scope is ambiguous, ask one clarifying question before starting. Otherwise, infer reasonably and state the inferred scope in the report.

## The 7 checks

For each finding, report: **what** (the issue), **where** (file paths + line numbers), **why it matters** (the concrete cost — drift risk, context tokens wasted, expensive op re-run, etc.), **fix** (the specific change to make).

### Check 1 — Context budget per file

For every file the audit target loads at runtime, measure line count. Compare against budget:

| File role | Budget | Rationale |
|---|---|---|
| Always-loaded (CLAUDE.md, profile/voice files, agent definitions) | < 200 lines | Burns context every invocation |
| Routine prompts (scheduled-task SKILL.md, slash commands) | < 100 lines | Should be orchestration, not editorial |
| Skill SKILL.md (auto-loaded when triggered) | < 250 lines | Discoverability vs bloat |
| On-demand reference files (templates, deal summaries, etc.) | < 500 lines | Loaded only when needed |
| Memory files | < 200 lines per file (push detail into topic sub-files) | Loaded every agent invocation |

Flag any file over budget with a target reduction (e.g., "file is 220 lines over a 100-line budget for routine prompts; aim for 50% reduction"). Don't just flag the size — say what's bloating it.

### Check 2 — DRY violations (cross-file duplication)

Search for distinctive phrases (full sentences or 3+ word phrases that are unlikely to occur by accident) appearing in 2+ files within the audit scope. For each hit, classify:

- **Pointer-style** (one file has the rule, others say "see X") → fine, leave alone
- **Restatement-style** (the rule itself is restated, even with minor wording variations) → flag

For each restatement-style hit, propose ONE canonical home and a pointer for the others. Give the canonical home a reason ("most-specific layer", "first written", "most-frequently-edited" — pick the heuristic that fits).

Heuristic: any rule that appears word-for-word or near-word-for-word in 2+ files is almost certainly a duplication. Any rule that appears in 3+ files is definitely a problem.

### Check 3 — Filler / unnecessary content

Flag content that doesn't change agent behavior. Specific patterns to look for:

- **Marketing intros.** "This document serves as the single source of truth for…" — if the doc IS the source of truth, the agent reading it doesn't need the meta-commentary. Cut.
- **Repeated emphasis.** "Critical", "non-negotiable", "load-bearing", bold everywhere. Pick once. Overuse trains the agent to ignore emphasis.
- **WHY explanations without action.** "We do X because historically Y happened" — if the explanation doesn't change what the agent does, it's just context bloat. Move to a separate notes/history file or delete.
- **Examples that don't add a new case.** If three examples illustrate the same principle, two of them are filler. Keep the best one + a note "(see X for additional cases)".
- **Conversational lead-ins.** "OK, so what should we do here…" — fine in chat, bad in a permanent prompt.
- **Redundant rule scoping.** "When drafting an email, when you're in Phase 2, when the user asks for a reply…" — the agent already knows the context. State the rule once.

For each flagged section, propose: (a) cut entirely, (b) move to a less-loaded file (history, archive, README), or (c) condense to one line.

### Check 4 — Repeated expensive operations

Identify operations that have a known cost (AppleScript Mail queries, web fetches, repo clones, voice mining of sent emails, large file reads, AI API calls). For each one, check whether it's done at the right cadence:

| Operation cadence | Right place | Wrong place |
|---|---|---|
| One-time | Setup wizard / install script | Inside a routine that fires every morning |
| Quarterly | Refresh-flag in wizard, or a scheduled task | Inside a per-draft instruction |
| Per-message | Inside a drafting skill | Re-done by both the skill AND the routine prompt |
| At runtime | When the data genuinely changes per-invocation | When the data is stable and was stored at setup |

If an op has a stored artifact (profile.md voice anchors, config files, generated indexes), flag any instruction that re-does the op at runtime instead of reading the artifact.

### Check 5 — Stale facts

Compare descriptions / pointers / examples against the actual code or files they reference. Look for:

- Agent files describing a routine that no longer does what they say (e.g., "routine drafts 5 outbound emails" but the routine is now triage-only)
- Pointers like "see X for Y" where X doesn't actually contain Y anymore
- Listed file paths that don't exist
- Workspace layout diagrams that no longer match the directory structure
- TODOs / "this is a draft" / "we should refactor this later" markers on files that have been stable for >1 month

For each stale fact, give: the file/line, the claim, and what the truth is now. The fix is usually a 1-line edit.

### Check 6 — Working-directory assumptions

For any executable instruction (bash command in a skill, AppleScript invocation, file read), check whether it assumes a specific CWD without enforcing it. If yes, propose:
- Pass an explicit `--config /abs/path` flag, OR
- Use absolute paths throughout, OR
- Add an explicit `cd` step with the absolute path before the operation

Same applies to environment variable assumptions, $HOME assumptions, etc.

### Check 7 — Pointer correctness

For every "see X for Y" / "lives in X" / "read X first" reference in the audit scope, verify:
1. X exists at the given path
2. X actually contains Y (not just a heading — the load-bearing content)
3. X's path is current (not pointing at a renamed or archived dir)

This is the kind of thing that drifts silently — files get renamed, content gets moved, and the pointers don't update.

## Report format

Output a single structured markdown report. Sections in this order:

```
# Engineering Audit — [scope]

Audited: [date, paths]
Files inspected: [count + names]

## Findings by severity

### 🔴 Critical (would actively break something)
- [Finding] — file:line — fix

### 🟡 Important (drift risk, real waste, but works today)
- [Finding] — file:line — fix

### 🟢 Polish (nice-to-have, low impact)
- [Finding] — file:line — fix

## By check (full detail)

### Check 1 — Context budget
[Table of files + line counts vs budget, over-budget items called out]

### Check 2 — DRY violations
[Each restatement with canonical home + pointer fix]

[... checks 3-7 ...]

## Recommended action order

1. [Highest-leverage fix]
2. [Next]
3. ...

## What's good

[Briefly: what's already well-designed. Not flattery — a short, honest note on what the system does right, so the user knows what NOT to touch.]
```

## Anti-patterns — what this skill is NOT

- **Not a code formatter.** Doesn't care about indentation, line length below ~120, naming conventions. Engineering substance, not style.
- **Not a security review.** Doesn't flag secrets, auth issues, injection risks. Use a security-review skill for that.
- **Not a performance profiler.** Doesn't measure runtime cost of code paths. Measures human-attention cost and expensive-operation count.
- **Not a "rewrite everything cleaner" pass.** Reports findings; does NOT auto-apply fixes. The user or another agent applies what they want.
- **Not a vague vibe check.** Every finding must point at a specific file:line and propose a specific fix. "This feels bloated" is not a finding; "outreach.md lines 56-60 restate the sendable-as-is bar that's already in profile.md — delete and replace with a pointer" is.

## Calibration — when NOT to flag something

- **Same SHORT pointer in multiple agent files.** Each agent saying "read email_style.md first" is fine — they're each pointing at the canonical source. DRY violations are about restating the RULES, not about each consumer mentioning the source.
- **Examples that show genuinely different cases.** Don't cut examples just to reduce line count. Cut redundant examples that illustrate the same point.
- **Files that look long because they're a true reference.** A 500-line deal summary template loaded only when summarizing a deal is fine. A 500-line file loaded every conversation is not.
- **Stable historical context.** If a file has dated notes like "decision made 2026-05-18" that explain a non-obvious design choice, leave them. They're load-bearing for future maintainers.

When in doubt about whether something is filler, ask: would removing this change what any agent does? If no → flag as filler. If yes → leave it.
