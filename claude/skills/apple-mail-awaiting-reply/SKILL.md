---
name: apple-mail-awaiting-reply
description: Answer "who am I waiting on" against the user's Apple Mail (macOS) account configured in apple-mail-config.json. Read-only — surfaces emails the user sent in the last N days that haven't gotten a response yet. Reads a small per-workspace config file for the Mail account name. macOS + Apple Mail only — not for Gmail accounts.
---

# Apple Mail: Awaiting Reply

A read-only macOS Apple Mail script that answers a single question:

> What emails have I sent in the last N days that haven't gotten a response?

This is a fresh snapshot, not an incremental view. It does not track state
between runs. The window is governed by `--days` (default 14).

## When to use this skill

Trigger on phrases like:
- "who am I waiting on"
- "what emails am I waiting on a reply for"
- "what sent emails haven't been responded to"
- "show me what I sent that nobody replied to"
- "follow-ups I might owe a nudge to"

## When NOT to use this skill

**Do NOT use for Gmail accounts.** This skill only drives Apple Mail
(Mail.app on macOS) via AppleScript. Anything at `@gmail.com` or a
Gmail-hosted custom domain needs a Gmail-specific tool.

If the account is ambiguous, ASK: "Which account — your Apple Mail
inbox (the one in `apple-mail-config.json`), or one of your Gmail accounts?"

This skill also does NOT triage the inbox ("what's waiting on me"). For
that, see the `apple-mail-inbox-triage` skill.

## Requirements

- **macOS with Apple Mail.app.** Uses AppleScript via `osascript`. Will not
  work on Linux, Windows, or remote cloud sandboxes.
- **A configured Mail account** matching the `account_name` in the config.
- **A `apple-mail-config.json` file** somewhere in the workspace tree (see
  Config below).

## Config

The script reads `apple-mail-config.json`:

```json
{
  "workspace_id": "my-workspace",
  "account_name": "Exchange"
}
```

Only `account_name` is used by this skill — it must exactly match the
account name shown in `Mail.app → Settings → Accounts`. The `workspace_id`
field is parsed for forward-compatibility with stateful siblings (e.g.
`apple-mail-inbox-triage`) but unused here.

**Discovery order:**
1. `--config <path>` if passed on the command line.
2. Walk up from the current working directory looking for
   `apple-mail-config.json`.
3. Error: "No apple-mail-config.json found. Either run from inside your
   workspace directory, or pass --config /path/to/config.json"

## Usage

```bash
python3 scripts/awaiting_reply.py \
    [--config PATH] [--days N] [--limit N]
```

Defaults: `--days 14`, `--limit 50`.

Output (one per line, oldest-first / most overdue first):

```
2026-04-20 | Person <person@example.com> | Project follow-up | (sent 14 days ago)
```

If the user is caught up: `No emails awaiting reply in last <N> days.`

## What it filters out

- **Same-domain recipients.** Internal forwards / FYI emails to colleagues
  on the same domain as the configured account are skipped. (Detected via
  AppleScript: `email addresses of account "<account_name>"` — take the
  domain of the first address.)
- **Automated recipients.** `noreply@…`, `notifications@…`, `@mailer.*`,
  `@mail.*` and similar patterns are skipped — there's no point waiting on
  a reply from a robot.
- **Calendar-invite responses.** Subjects starting with `Accepted:`,
  `Declined:`, `Tentative:` are skipped.

## Heuristic accuracy

This is a **best-effort heuristic**, not magic. Expect:

- **False positives** — sent emails flagged as "awaiting reply" that
  genuinely don't need a response. Examples: threads that wrapped up via
  Slack/phone, FYI emails that were themselves the closing word.
- **False negatives** — real follow-ups the script misses. Examples: a
  reply that arrived from a different address than the one originally
  written to, sent emails older than the `--days` window.

Match is by **email address only**, not thread headers — this answers the
simpler question "did this person ever write back" rather than "did they
reply to this specific thread." That's the right trade-off for the
who-am-I-waiting-on view; thread-header matching is reserved for the
inbox-triage sibling.

Treat the output as a **starting list, not gospel**. If something on the
list doesn't actually need attention, that's expected. If the list seems
incomplete, run with a larger `--days` window.

## Bounds

The script is bounded — it never iterates the entire mailbox. If a run
feels slow, lower `--limit` or `--days`.

## What this skill does NOT do

- Mutate Mail state (no flagging, marking read/unread, moving, archiving)
- Send any email
- Work on Gmail accounts (different tooling)
- Track state between runs (this is a fresh snapshot; the inbox-triage
  sibling is the stateful one)
- Top-senders / frequency analytics

## Workflow

1. Run the script.
2. Show the user the output verbatim (or summarized if it's long).
3. Remind them these are heuristics — they can ask to draft a reply to any
   of them via the `apple-mail-draft-reply` skill.
4. Don't ask permission to run — it's read-only.
