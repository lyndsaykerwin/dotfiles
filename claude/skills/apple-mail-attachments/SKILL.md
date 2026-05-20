---
name: apple-mail-attachments
description: List or save attachments from Apple Mail emails using the account configured in apple-mail-config.json. DO NOT use for Gmail accounts.
---

# Apple Mail: List & Save Attachments

Two read-only-ish operations on the configured Apple Mail account (the one
named in `apple-mail-config.json`):

1. List the attachments on a single email (filenames + sizes).
2. Save one of those attachments to disk (default `~/Desktop`).

Both operations are non-destructive — they don't move, mark, or modify the
email itself.

## When to use this skill

Trigger when the user says something like:
- "save the attachment from that email about X"
- "what's attached to that email"
- "download the attachment in the email from Y"
- "grab the deck off the latest Z email"
- "pull the file off that email and put it on my desktop"

The skill is for emails that live in the user's configured Apple Mail
account. If they're ambiguous about which account, ASK: "Which account —
your Apple Mail inbox (the one in `apple-mail-config.json`), or one of
your Gmail accounts?"

## When NOT to use this skill

**Do NOT use for Gmail attachments.** This skill only drives Apple Mail
(Mail.app on macOS) via AppleScript. Gmail-hosted addresses need a
Gmail-specific tool.

## How it works

Two scripts in this skill's `scripts/` directory:

- `list_attachments.py` — prints attachment names and sizes for one email.
- `save_attachment.py` — saves one attachment to a directory.

Both find the target email by **subject keyword** (case-sensitive substring).
The keyword must match exactly **one** message in the chosen mailbox — if
zero match, the script errors out; if 2+ match, it asks for a more specific
keyword. This is a guardrail against grabbing the wrong email's attachment.

## Usage

### List attachments

```bash
python3 scripts/list_attachments.py "<account>" "<subject keyword>"
```

Optional: `--mailbox NAME` to search a folder other than Inbox (e.g.
`--mailbox "Sent Items"`).

Output:
```
Subject: <full subject of matched email>
[1] FILENAME (SIZE bytes)
[2] FILENAME (SIZE bytes)
...
```

If the matched email has no attachments, prints `No attachments on email '...'`
and exits successfully (this is information, not an error).

### Save an attachment

```bash
python3 scripts/save_attachment.py "<account>" "<subject keyword>"
```

Default save destination: `~/Desktop`. Default attachment: the (only) one on
the email.

Optional flags:
- `--save-to PATH` — directory to save into. Must be under `~` (or `/tmp`
  for testing). Anything else is refused, so a misspelled keyword can't
  steer the write somewhere unexpected.
- `--name FILENAME` — required when the email has 2+ attachments. Pick the
  one whose `name` matches FILENAME exactly. Run `list_attachments.py`
  first to see the available names.
- `--mailbox NAME` — same as on `list_attachments.py`.

Output:
```
Saved 'NAME' to /full/path/to/NAME
```

The script **never overwrites an existing file**. If `<save-to>/<name>`
already exists, it adds a suffix: `<stem>_1<ext>`, then `_2`, etc. The
output line shows the actual final path.

## Workflow

1. **Pick a unique-ish subject keyword.** Large inboxes (1000+ messages)
   often have repeat subjects from threaded conversations. If the user
   says "the email from Ben about X", use a keyword that's specific to
   that one message, not the whole thread (otherwise the script will
   refuse with "Multiple messages...").
2. **List first if you don't know what's there.** `list_attachments.py`
   gives you the filenames so you know what `--name` to pass.
3. **Save with appropriate `--save-to`.** Default `~/Desktop` is right for
   normal "save this file" requests. Use `/tmp` only for transient/test
   work. Use `~/Documents/...` for things being filed.
4. **Tell the user where the file landed** — paste back the script's
   `Saved '...' to ...` line. They often want to open it next.

## Examples

**User:** "save the attachment from that calendar invite from Nathan to my desktop"

```bash
# Step 1: confirm what's attached (optional but useful)
python3 scripts/list_attachments.py "Exchange" "Accepted: Nathan"

# Step 2: save it (defaults to ~/Desktop)
python3 scripts/save_attachment.py "Exchange" "Accepted: Nathan"
```

**User:** "what's attached to the Project Domain IM email"

```bash
python3 scripts/list_attachments.py "Exchange" "Project Domain IM"
```

**User:** "download the model.xlsx from that diligence email and put it in my Documents"

```bash
python3 scripts/save_attachment.py "Exchange" "diligence" --name "model.xlsx" --save-to ~/Documents
```

## Edge cases

- **Multiple matching emails:** keyword too broad. Ask the user for more of
  the subject (e.g. add the sender's name to the keyword).
- **Email has 2+ attachments and you didn't pass `--name`:** the script
  refuses and tells you. Run `list_attachments.py` first, then re-run
  `save_attachment.py` with `--name`.
- **Filename collision in target directory:** automatic `_1`, `_2`, ...
  suffix. The user sees the exact final path in the output.
- **Path outside `~`:** refused. To save anywhere else (e.g. an external
  drive), save to `~/Desktop` first and move it manually.

## Output

On success, both scripts print to stdout and exit 0. Errors print
`ERROR: <message>` and exit 1 — pass that line back to the user verbatim.

## What this skill does NOT do

- Open or preview attachments — it only saves files to disk.
- Modify the email (no marking read, no archiving). Use `apple-mail-organize`
  for that.
- Send attachments. Use `apple-mail-draft-new` to compose an
  email with attachments.
- Anything in Gmail (different tooling).
