---
name: apple-mail-inbox-triage
description: Incrementally triage Apple Mail's inbox to surface new emails that need a reply — only messages received since the last successful run. Read-only. Workspace-aware via apple-mail-config.json. macOS + Apple Mail only — not for Gmail accounts.
---

# Apple Mail: Inbox Triage (incremental)

A read-only script that answers one question: **"what's arrived in my inbox
since I last looked that needs my reply?"**

It is **incremental** — every run remembers when it last ran and only
surfaces messages newer than that. The default first-run window is
24 hours; after that, the window is "since the previous run."

It is **heuristic**, but the matching is real: "did I already reply" is
checked against actual email threading headers (Message-ID /
In-Reply-To / References), not stripped subject strings — so internal
forwards (e.g. forwarding the inbound to a colleague) no longer cause
the original to be hidden from triage.

## When to use this skill

Trigger on phrases like:

- "what's new in my inbox"
- "anything I need to reply to since this morning"
- "what came in overnight that needs my response"
- "show me unread inbox stuff I haven't replied to"
- "what's waiting on me"

## When NOT to use this skill

**Do NOT use for Gmail accounts.** This skill only knows how to drive
Apple Mail (Mail.app on macOS) via AppleScript. If the inbox in question
is a Google account (gmail.com, or a Google Workspace domain that the
user reads via the Gmail web app), it needs a Gmail-specific tool.

If it's ambiguous which account the user means, ASK before running.

This skill is **not** for:
- "Who am I waiting on" (use a different skill — that's a sent-side question)
- Older flagged-but-unread emails (out of scope — this is strictly
  "what's new since last run")

## Requirements

1. **macOS with Apple Mail** open and signed in to the account in question.
2. **A workspace config file** named `apple-mail-config.json` somewhere
   from the current working directory upward. Format:

   ```json
   {
     "workspace_id": "my-workspace",
     "account_name": "Exchange"
   }
   ```

   - `workspace_id` — a short identifier used for the per-user state path
     (folder name under `~/.claude/state/`). Anything filesystem-safe.
   - `account_name` — the Apple Mail account label exactly as it appears
     in Mail's settings (e.g. `"Exchange"`, `"Work"`, `"iCloud"`).

   If no config is found and `--config` isn't passed, the script errors out
   with a clear message. You can either `cd` into the workspace before
   running, or pass `--config /path/to/apple-mail-config.json`.

## Usage

```bash
python3 scripts/inbox_triage.py
```

With options:

```bash
python3 scripts/inbox_triage.py \
    --config /path/to/apple-mail-config.json \
    --limit 30
```

Output (one line per email, oldest-first):

```
2026-05-17 | Liam <liam@example.com> | Quick intro | Hey, we briefly met at the Acme summit and...
```

If there's nothing new and unanswered:

```
No new inbox emails needing reply since 2026-05-17.
```

On the very first run (no state file yet):

```
No new inbox emails needing reply since startup (first run).
```

## How the "already replied" check works

For each candidate inbox message we get its `Message-ID`. For each sent
message in the same time window we read the `In-Reply-To` and `References`
headers. If any sent message points at this inbox message's Message-ID, the
inbox message is treated as already replied to and dropped from the list.

Sent messages whose primary recipient is at the **same email domain** as
the configured account (i.e. internal forwards to colleagues / aliases on
your own domain) are skipped during this check — forwarding the inbound
internally does not count as a reply.

## State

The "when did I last successfully run" timestamp lives at:

```
~/.claude/state/<workspace_id>/inbox-triage-last-run.json
```

- The folder is auto-created on first run.
- The file contains a single ISO 8601 timestamp string.
- It is updated only after a successful run (no crash, no AppleScript error).
- It is **per-user** (in the user's home directory) and **not in the repo**.

To force a longer one-off window, delete or edit the state file before running.

## Heuristic accuracy

This is a best-effort heuristic, not magic. Expect:

- **False positives** — emails on the list that don't actually need a reply.
  Examples: threads that wrapped up via Slack/phone, FYI emails that were
  fine to ignore, autoresponders that don't match the filter list.
- **False negatives** — real follow-ups the script misses. Examples: a new
  email about an old topic from a sender the script didn't recognize as
  needing attention, automated senders not in the filter list.

The thread-header matching kills the most common false-negative from the
old subject-string approach (internal forwards looking like replies), but
it can't fix every edge case. Treat the output as a **starting list, not
gospel**.

## What this skill does NOT do

- Mutate Mail state (no flagging, no marking read/unread, no moving, no archiving)
- Send any email
- Work on Gmail accounts (different tooling)
- Surface older flagged or unread emails outside the incremental window
- Answer "who am I waiting on" — that's a sent-side question, different skill
- Read or modify anything outside the configured Apple Mail account

## Workflow

1. Make sure the user is in a workspace with `apple-mail-config.json`
   (or pass `--config` explicitly).
2. Run the script.
3. Show the user the output verbatim (or summarized if it's long).
4. Remind them these are heuristics — they can ask to draft a reply to any
   item via the `apple-mail-draft-reply` skill.
5. Don't ask permission to run — it's read-only.
