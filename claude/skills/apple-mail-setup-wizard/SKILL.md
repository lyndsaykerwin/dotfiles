---
name: apple-mail-setup-wizard
description: Run the one-time setup wizard for the apple-mail-skills toolkit on macOS. Produces a personalized `~/.claude/preferences/apple-mail/profile.md` (voice rules, priority rules, signature, identity) and an `apple-mail-config.json` in the current workspace. Use when the user has just cloned the toolkit, says things like "set up apple-mail-skills", "run the setup wizard", "configure my email skills", "install apple-mail-skills", or when they ask why a draft "doesn't sound like me" and no profile exists yet. The wizard pauses partway through and asks YOU to read the user's last 30 sent emails and produce a voice profile - you are part of the wizard, not just the launcher. macOS + Apple Mail only.
---

# Apple Mail Skills - Setup Wizard

A hybrid wizard. Python (`setup.py` at the repo root) handles the mechanical
steps - reading Apple Mail accounts via AppleScript, auto-detecting the user's
name and signature, writing the final `profile.md` and `apple-mail-config.json`,
optionally installing a cron entry. You, Claude, handle the smart step: reading
the user's actual sent mail and producing the voice profile that makes drafts
sound like them.

## When to use this skill

Trigger phrases:

- "set up apple-mail-skills"
- "run the apple-mail setup wizard"
- "configure my email skills"
- "install apple-mail-skills"
- "the drafts don't sound like me" (and no `~/.claude/preferences/apple-mail/profile.md` exists)
- "personalize the apple-mail toolkit"
- the user has just cloned `apple-mail-skills` and asks how to get started

## When NOT to use this skill

- The user already has `~/.claude/preferences/apple-mail/profile.md` and isn't
  asking to reset it. The other apple-mail-* skills work fine against an
  existing profile - just use those.
- The user is on a non-Mac platform. Apple Mail is Mac-only; this whole
  toolkit doesn't apply.
- The user wants to schedule a routine for an already-configured workspace.
  That's `python3 setup.py --schedule-routine` - one command, not the full
  wizard.

## Refresh flags (existing profile, partial re-run)

If a profile already exists and the user wants to update part of it without
starting from scratch, pick the narrowest flag that fits:

- **"My drafts don't sound like me anymore"** / "the voice has drifted" /
  "re-mine my sent mail" / "update my voice profile":
  ```
  python3 setup.py --refresh-voice
  ```
  Re-runs ONLY the voice analysis (steps 2 -> 3 -> 4). Identity, scope, reply
  philosophy, and any custom sections in profile.md are preserved. The Voice /
  Priority rules / Banned phrases sections are rebuilt from fresh sent-mail
  analysis. Backs up the old profile to `profile.md.bak` first. Same pause-and-
  resume pattern as the full wizard - when the wizard exits with code 7, you
  do the voice analysis and re-invoke with `--resume-from-voice <file>`.

- **"I want to redo everything but keep my answers as a starting point"** /
  "re-run the wizard but don't make me re-type everything":
  ```
  python3 setup.py --refresh-profile
  ```
  Re-runs the full wizard. Every prompt is pre-filled with the answer from the
  existing profile - the user presses Enter to keep, or types to change.
  Backs up the old profile to `profile.md.bak` first.

- **"I want to schedule the morning triage routine"** / "set up a recurring
  inbox check" (when the user skipped step 6 the first time):
  ```
  python3 setup.py --schedule-routine
  ```
  Skips identity, voice, priority, scope - jumps straight to step 6
  (scheduling). Does not touch profile.md.

These three refresh flags are mutually exclusive (and incompatible with
`--resume-from-voice`). If the user asks for something that doesn't fit any
of them, fall back to the full `python3 setup.py` and explain that it will
back up the existing profile.

## How the wizard runs

The wizard has 7 steps. You will see steps 1, 2, then a PAUSE, then 3-7.

```
Step 1: Identity                    (Python auto-detects, asks on failure)
Step 2: Voice analysis              (Python dumps sent mail to /tmp, then exits)
                                    --- PAUSE: Claude reads the dump and writes a voice file ---
Step 3: Priority rules              (Python re-runs, pre-fills from voice file)
Step 4: Banned phrases              (Python pre-fills from voice file)
Step 5: Scope confirmation
Step 6: Routine scheduling          (cron or Claude Code scheduled task)
Step 7: Write profile.md + config.json
```

## Your job during the pause

When the user runs `python3 setup.py` and chooses `yes` for voice analysis,
the Python side will:

1. Dump the last 30 sent emails to `/tmp/apple-mail-wizard-sent-XXXX.txt`.
2. Print a "PAUSE - voice analysis handoff to Claude" banner.
3. Exit with sentinel code 7.

At that point, you take over. Do this:

### 1. Read the sent-mail dump

The file is delimited plain text with one record per email:

```
DATE: 2026-05-15T09:42:00
TO: someone@example.com
SUBJECT: Re: scheduling
BODY:
(the actual email body)
=====
DATE: ...
```

Use the `Read` tool against the path printed in the PAUSE banner.

### 2. Produce a voice profile

Write a markdown file with these `##` sections. The output path is also
printed in the PAUSE banner (something like
`/tmp/apple-mail-wizard-voice-XXXX.md`). Use the `Write` tool.

```markdown
# Voice profile

## Voice patterns

A free-form markdown blob describing how the user writes. Include:
- Greeting style ("Hi X", "Hey X", just "X,", no greeting)
- Sign-off line (e.g. "Best, <your name>" vs "Thanks, <your name>" vs no sign-off)
- Sentence length tendency
- Em-dash frequency
- `&` vs `and` usage
- Contraction frequency
- Sentence case vs title case
- 3-5 verbatim sentences pulled from real sent mail as voice anchors
  (these are the gold - drafting agents will echo their cadence)

## High-priority senders

One bullet per sender, with the SOURCE shown after a double-space `--`:

- Sam Rivera <sam@example.com>            -- replied to within 1hr x 8 times last 30 days
- Alex Chen <alex@example.com>            -- 12 emails sent last 90 days

Mine: top 10 most-emailed recipients in the dump, plus anyone the user
replied to within <1 hour multiple times. Show the reasoning so the user
can spot misfires fast.

## Priority keywords

Subject-line patterns from threads where the user replied fastest:

- intro     -- appears in 14 threads, avg reply time 22min
- scheduling     -- 8 threads, all replied same day

## Noise senders

Senders to never surface in triage. These are senders the user has NEVER
responded to AND who match patterns like `info@`, `noreply@`, `marketing@`,
`team@`, or who they archive consistently:

- info@example.com             -- 17 emails received, 0 replies

(In the sent-mail dump you only see outbound; for noise senders, surface
patterns the user has CLEARLY never written back to. If you're not sure,
omit - it's better for the user to add later than for the wizard to silence
something they care about.)

## Banned phrases

Cross-check this baked-in starter list against the sent-mail dump:

- "I wanted to reach out"
- "I hope this email finds you well"
- "hope this finds you well"
- "just wanted to touch base"
- "circle back"
- "happy to chat"
- "let me know if you have any questions"
- "thank you for your time"
- "please don't hesitate to reach out"
- "I trust this message finds you well"
- "as per our conversation"
- "kindly find attached"
- "moving forward" / "going forward"
- "at your earliest convenience"
- "leverage synergies" / "deep dive" / "low-hanging fruit" / "drill down" / "touch base"
- "ping me"
- "I appreciate your patience"
- "I just wanted to follow up"
- "I hope you're doing well"

For each one:
  - If it appears 0 times in the dump, list under `## Banned phrases` with
    annotation `-- 0 uses in your sent mail`.
  - If it appears in the dump, list under `## Keep phrases` with annotation
    `-- you used this N times, looks intentional` (do NOT ban these).

Add any phrases you find the user using suspiciously often (>5x in 30
emails) under `## Keep phrases` with a `?` annotation - the user reviews.

## Keep phrases

(populated as described above)

## Signature

The repeating block at the bottom of the user's emails. Strip out per-email
content; what's left is the signature. Typically 1-4 lines: name, role,
email, website.
```

### 3. Resume the wizard

After you've written the voice file, re-invoke setup.py with the resume
flag. The exact command is printed in the PAUSE banner:

```bash
python3 /path/to/apple-mail-skills/setup.py \
    --resume-from-voice /tmp/apple-mail-wizard-voice-XXXX.md
```

Use the `Bash` tool to run it. The wizard will pick up the in-progress
state (saved alongside the sent-mail dump under
`/tmp/apple-mail-wizard-state-XXXX.json`), load your voice profile, and
walk the user through steps 3-7 with everything pre-filled.

## Workflow

1. Run `python3 setup.py` from the user's workspace directory.
2. Talk the user through any prompts they need to type (most prompts have
   detected defaults - Enter accepts).
3. When the wizard hits the voice-analysis pause, exit cleanly. Your job
   begins:
   a. Read the sent-mail dump.
   b. Write the voice file at the path the wizard printed.
   c. Re-invoke `setup.py --resume-from-voice <voice file>`.
4. Continue talking the user through steps 3-7.
5. **If step 6 produced a Claude Code scheduled task** (the user picked
   "claude-task" — the recommended option), register it before reporting
   done. The wizard will have printed something like:

   ```
   Morning triage routine prepared for workspace '<workspace_id>'.

   To register it in Claude Code Desktop Routines, the parent Claude session
   should call the `create_scheduled_task` MCP tool with these arguments:

     taskId         : <workspace_id>-morning-inbox
     cronExpression : 0 9 * * 1-5    (= 09:00 weekdays)
     description    : Morning inbox triage for <workspace_id> — ...
     prompt         : <contents of /tmp/apple-mail-routine-<workspace_id>-morning-inbox.md>
   ```

   Read the prompt file the wizard wrote, then call
   `create_scheduled_task` with those exact arguments. ONE tool call writes
   the SKILL.md to `~/.claude/scheduled-tasks/<taskId>/SKILL.md` AND
   registers the cron in the Desktop Routines runtime. The task starts
   **disabled** — tell the user to enable it in the Routines section when
   ready.

   **Do not** create a workspace-level routine .md file. The scheduled-task
   SKILL.md is the single source of truth for the routine. If the user's
   workspace conventions reference an `outreach/routines/` directory or
   similar, leave at most a short pointer file there directing readers to
   `~/.claude/scheduled-tasks/<taskId>/SKILL.md`.

6. When the wizard finishes, report the file paths it wrote.

## Common edge cases

- **macOS scripting permission dialog.** First time the wizard reads from
  Mail, macOS pops up a "Terminal wants to control Mail.app" dialog. If the
  user clicks Don't Allow, the AppleScript fails silently and the wizard
  reports "Couldn't read sent mail." Tell them: System Settings > Privacy
  & Security > Automation > Terminal > Mail > toggle on, then re-run.
- **No Apple Mail accounts.** Mail.app isn't running or hasn't been signed
  in to. The wizard asks the user for the account label by hand; the user
  can finish setup and the file-based skills will still work once they sign
  in.
- **Existing profile.** The wizard backs up `profile.md` to `profile.md.bak`
  automatically before overwriting. No silent overwrites.
- **The user wants to skip voice analysis.** Totally fine - they can run
  `python3 setup.py` again later to redo with voice on, or hand-edit
  `~/.claude/preferences/apple-mail/profile.md` directly.

## What this skill does NOT do

- Send any email.
- Read inbox (only sent mail, only during the opt-in voice-analysis step).
- Work on Gmail accounts (Gmail goes through a different MCP entirely).
- Create workspace-level routine .md files. The morning triage routine
  lives in exactly one place: `~/.claude/scheduled-tasks/<taskId>/SKILL.md`.
  Editing the prompt means editing that file (or calling
  `update_scheduled_task`). Workspace-level routine mirrors get stale and
  drift from the scheduled task — don't make them.
- Modify any Apple Mail data (read-only against Mail; write-only against
  the user's own `~/.claude/preferences/` and the current workspace).
