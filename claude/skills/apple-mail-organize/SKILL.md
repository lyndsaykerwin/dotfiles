---
name: apple-mail-organize
description: Organize emails in Apple Mail using the account configured in apple-mail-config.json — move messages between folders, flag/unflag for follow-up, mark read/unread. Use when the user asks to "archive that newsletter", "flag this for follow-up", "mark all from X as read", "move emails from Y to Z folder", "clean up my inbox", or any other organizing/triage action against their configured inbox. DO NOT use for Gmail accounts. Bulk operations have small default caps and support --dry-run for safety.
---

# Apple Mail: Organize (move, flag, mark read/unread)

Three small scripts for keeping the configured Apple Mail inbox tidy. The
account name comes from `apple-mail-config.json` (the `account_name`
field). Each script is single-purpose and has its own safety guardrails.

## When to use this skill

Trigger when the user asks to organize messages in their configured Apple
Mail inbox:
- "archive that summary email"
- "flag the email from Ben for follow-up"
- "mark everything from Project X as read"
- "move all the newsletters into the Newsletters folder"
- "unflag the smoke test email"
- "move emails from before April 1 to Archive"

## When NOT to use this skill

**Do NOT use for Gmail accounts.** This skill only drives Apple Mail
(Mail.app on macOS) via AppleScript. Gmail-hosted addresses need a
Gmail-specific tool.

If the user is ambiguous about which account, ASK: "Which account — your
Apple Mail inbox (the one in `apple-mail-config.json`), or one of your
Gmail accounts?"

## Scripts

All three live in this skill's `scripts/` directory.

### `move_email.py` — move messages out of INBOX

```bash
python3 scripts/move_email.py "<account>" --to-mailbox NAME [filters] [options]
```

**Required:**
- `--to-mailbox NAME` — destination mailbox in the same account.
- At least one filter — `--subject KEY`, `--sender KEY`, `--from-date YYYY-MM-DD`, `--to-date YYYY-MM-DD`. Without a filter the script REFUSES (would otherwise empty the inbox).

**Options:**
- `--max-moves N` — default 5, hard cap 100.
- `--dry-run` — print matches without moving.

**Examples:**
```bash
# Dry-run first to preview
python3 scripts/move_email.py "Exchange" --to-mailbox "Archive" --sender "newsletter" --dry-run

# Real move, up to 20
python3 scripts/move_email.py "Exchange" --to-mailbox "Archive" --sender "newsletter" --max-moves 20
```

### `flag_email.py` — flag/unflag a single message

```bash
python3 scripts/flag_email.py "<account>" "<subject keyword>" [--unflag] [--dry-run]
```

- Default action: flag. With `--unflag`: remove the flag.
- Refuses if 0 matches.
- Refuses if 5+ matches — keyword too broad, ask the user for a more specific phrase.

**Examples:**
```bash
python3 scripts/flag_email.py "Exchange" "Project Discussion"
python3 scripts/flag_email.py "Exchange" "Project Discussion" --unflag
```

### `mark_read.py` — mark messages read/unread

```bash
python3 scripts/mark_read.py "<account>" [filters] [--unread] [--max-marks N] [--dry-run]
```

**Required:** at least one of `--subject KEY`, `--sender KEY`, or `--all-from-sender SENDER`.

**Options:**
- `--unread` — mark unread instead of read.
- `--max-marks N` — default 50, hard cap 500.
- `--dry-run` — print matches without changing state.

**Examples:**
```bash
# Preview
python3 scripts/mark_read.py "Exchange" --sender "newsletter" --max-marks 10 --dry-run

# Real
python3 scripts/mark_read.py "Exchange" --all-from-sender "newsletter@foo.com"
```

## Safety

This skill mutates Mail state, so the scripts are designed to fail safe:

- **Bulk operations require `--max-moves` / `--max-marks`.** Defaults are
  small (5 for moves, 50 for marks). Hard caps are 100 / 500 respectively —
  the scripts REFUSE to go above and tell you to break the operation up.
- **`--dry-run` is encouraged for any first-time bulk operation.** Run
  dry-run first, eyeball the list with the user, then re-run without it.
- **No-filter calls are refused.** A `move_email.py` invocation with no
  `--subject`/`--sender`/`--from-date`/`--to-date` would empty the inbox —
  the script exits with an error before doing anything.
- **Ambiguous flag operations are refused.** `flag_email.py` requires a
  unique-ish keyword: 0 matches errors, 5+ matches errors. This forces
  precision when toggling individual message flags.
- **Move-to-trash is NOT chained with empty-trash.** If the user wants
  emails permanently gone, that's a separate explicit request.

## Workflow

1. **Identify the operation type.** Move? Flag? Mark read?
2. **For bulk ops, dry-run first.** Show the user the list. If they're
   happy, re-run without `--dry-run`.
3. **Run the appropriate script.** Pass the account name from
   `apple-mail-config.json`.
4. **Report back.** Include the count and a few example subjects so the
   user can verify the right messages were touched.

## Output

Successful runs print one of:
- `Moved N messages to MAILBOX` (with bulleted list of subject + date)
- `DRY RUN: would move N to MAILBOX:` (with bulleted list)
- `Flagged 1 message(s):` / `Unflagged 1 message(s):`
- `Marked read: N message(s)` / `Marked unread: N message(s)`

Errors start with `ERROR:` and the script exits non-zero. Pass error
messages back to the user verbatim.

## What this skill does NOT do

- Send or draft emails — use `apple-mail-draft-reply` or `apple-mail-draft-new`.
- Search/list emails — use the `apple-mail-search` skill.
- Empty trash, delete forever, or any irreversible destructive action.
- Touch any account other than the one named in argv.
- Work on Gmail accounts (different tooling).
