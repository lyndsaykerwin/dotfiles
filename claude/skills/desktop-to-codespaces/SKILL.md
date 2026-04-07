---
name: desktop-to-codespaces
description: Use when ending a local Desktop session and the user wants to continue work in a GitHub Codespace, or when handing off between any two Claude Code environments that don't share local state
---

# Desktop-to-Codespaces Handoff

## Overview

A Codespace session starts with ZERO local context — no memory folder, no conversation history, no MCP servers. The ONLY way it knows what to do is through files committed to the repo. This skill ensures every handoff is specific, committed, and actionable.

**Core principle:** If it's not committed and pushed, the Codespace can't see it.

## When to Use

- User says they want to continue in a Codespace
- User says "hand off" or "wrap up for today" and Codespace is the target environment
- Session is ending and work needs to continue in a different environment
- Any cross-environment handoff (Desktop → Codespace, Codespace → Desktop, Codespace → Codespace)

## The Handoff Checklist

Every handoff requires exactly 4 artifacts, produced in order. Do NOT skip steps.

### Step 1: Write the Session Handoff File

**Location:** `docs/context/session_YYYY_MM_DDx.md` (letter suffix: `a` first session of the day, `b` second, etc.)

**Before writing:** Check `docs/context/` for existing sessions with today's date to pick the correct letter suffix. Don't overwrite an existing handoff.

**Required sections — every one is mandatory:**

```markdown
---
name: session_YYYY_MM_DDx
description: One-line summary — what was done + what the next session must do
type: project
---

# Session YYYY-MM-DDx — [Short Descriptive Title]

## Why This Matters
Plain-language explanation of WHY the next session is doing this work.
Not "what" — WHY. Connect it to the user's goal.
Example: "855 records have incomplete data because plain HTTP can't
render JavaScript. Until these are re-crawled, search results will
show wrong info to users looking for marine mechanics."

## Exactly Where to Start
Numbered list. Every item names a SPECIFIC file path and what to do with it.
NO vague references like "check the scripts folder" or "see recent commits."

### 1. [First thing to do]
- **File**: `exact/path/to/file.ext`
- **What it contains**: [description]
- **What to do with it**: [specific action]

### 2. [Second thing to do]
- **File**: `exact/path/to/another-file.ext`
- ...

## Known Problems
What will go wrong if the next session doesn't know about it.
Each problem gets: what happens, why it happens, what to do about it.

## Environment
- Running in: [GitHub Codespace / Windows Desktop / etc.]
- Platform differences: [what breaks if you assume the wrong OS]
- Available tools: [MCP servers, packages, browser automation]
- NOT available: [memory folder, Windows paths, local MCP servers]

## What Success Looks Like
Numbered checklist. Every item is testable — not "it works" but
"file X exists with Y records and Z% success rate."

## Files Changed This Session
| File | What changed |
|------|-------------|
| `exact/path` | Specific description |
```

**Red flags — STOP and fix if you catch yourself writing any of these:**
- "Check the X folder for details" → Name the specific file
- "See recent commits" → Name the specific file and what changed in it
- "The script" without a path → Always `scripts/exact_name.py`
- Missing a "Why This Matters" section → The next session needs motivation, not just tasks
- Handoff references files that aren't committed → Run `git status` and add any referenced files BEFORE pushing

### Step 2: Update CLAUDE.md Current Task Pointer

Update the `## Current Task` section in the project's `CLAUDE.md` with today's date and a pointer to the new handoff file.

**Required format:**

```markdown
## Current Task (YYYY-MM-DD) — [Short description of what's next]

> **START HERE →** `docs/context/session_YYYY_MM_DDx.md`
>
> [One sentence saying what this file contains and why to read it first.]

**Summary**: [2-3 sentences in plain language. WHY we're doing this, not just WHAT.]

**Key files**:
- [Descriptive label]: `exact/path/to/file` ([what it is])
- [Descriptive label]: `exact/path/to/file` ([what it is])
```

The date in the heading MUST match today's date. The file path MUST match the handoff file you just wrote.

### Step 3: Update Memory Index (Desktop only)

If running on Desktop (with access to the memory folder), do BOTH:

1. **Copy the handoff file** to the memory folder so the MEMORY.md links resolve:
   Copy `docs/context/session_YYYY_MM_DDx.md` → `~/.claude/projects/.../memory/session_YYYY_MM_DDx.md`

2. **Update MEMORY.md** — add the new session at the top of `### Session Handoffs (newest first)`. Mark it `**LATEST**` and remove that label from the previous entry.

If running in a Codespace (no memory folder), skip this step — memory is Desktop-only.

### Step 4: Commit and Push

**This is not optional.** A Codespace can only see committed, pushed code.

```bash
git add docs/context/session_YYYY_MM_DDx.md CLAUDE.md
git commit -m "Add session handoff for [date] — [what's next]"
git push origin main
```

After pushing, verify:
```bash
git log --oneline -1  # Confirm commit exists
git status            # Confirm clean working tree
```

If there are other uncommitted files that the Codespace needs (data files, scripts, configs), add those too. The rule: **if the Codespace needs it, it must be pushed.**

## Environment Differences Quick Reference

| Thing | Desktop (Windows) | Codespace (Linux) |
|-------|-------------------|-------------------|
| Memory folder | Yes (`~/.claude/projects/.../memory/`) | No — use `docs/context/` only |
| MCP servers | Gmail, Calendar, HubSpot, Reply, Vercel, Chrome | Context7 only (unless configured in devcontainer) |
| File paths | Backslash `C:\Users\...` | Forward slash `/workspaces/...` |
| Process kill | `taskkill /F /IM chrome.exe` | `pkill -f chromium` |
| Playwright | May crash (DLL issues on Windows) | Works cleanly |
| Git push | Required for Codespace access | Required for Desktop access |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Writing handoff but not pushing to git | Codespace can't see unpushed changes — always `git push` |
| Vague file references ("check the scripts folder") | Name every file by exact path |
| Skipping "Why This Matters" | Next session needs motivation to make good decisions, not just a task list |
| Assuming MCP servers carry over | List what IS and ISN'T available in the target environment |
| Forgetting platform-specific code | Flag any Windows-only or Linux-only code in the handoff |
| Updating CLAUDE.md but with wrong date | Date in `## Current Task (YYYY-MM-DD)` must be today |
| Not marking files changed | The "Files Changed" table prevents the next session from re-investigating |
