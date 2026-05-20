---
name: apple-mail-draft-new
description: Compose a NEW (non-reply) email DRAFT in Apple Mail using the account configured in apple-mail-config.json. Use when the user asks to draft, write, or compose a fresh email to someone — NOT a reply to an existing email (use apple-mail-draft-reply for replies). DO NOT use for Gmail accounts. Saves draft to Drafts folder; does NOT send.
---

# Apple Mail: Compose New Email Draft

Composes a brand-new outgoing email DRAFT (no original message, no threading)
in Apple Mail using the account named in `apple-mail-config.json` (the
`account_name` field). The draft is saved to that account's Drafts folder
and the compose window is left open so the user can review/edit before
sending manually.

## When to use this skill

Trigger when the user asks to compose / draft / write a **fresh** email — one
that is NOT a reply to an existing message — in their configured Apple
Mail account.

Phrases like:
- "draft an email to Sarah about the founder call"
- "compose a new email to ben@example.com"
- "write Mark an email saying I'll be in town next week"
- "send (draft) a fresh email to the team about Friday"
- "start a new email to John, subject 'Quick question', body ..."

## When NOT to use this skill

- **Replies.** If the user is responding to an email they received, use
  `apple-mail-draft-reply` instead — that skill preserves threading
  metadata (In-Reply-To, References, "Re:" subject, auto-quoted body).
- **Gmail accounts.** This skill only drives Apple Mail (Mail.app on
  macOS) via AppleScript. Gmail-hosted addresses need a Gmail-specific
  tool.
- **Sending.** This skill creates a DRAFT only. It NEVER sends. The user
  opens Mail and clicks send manually.

If the user is ambiguous about which account, ASK: "Which account — your
Apple Mail inbox (the one in `apple-mail-config.json`), or one of your
Gmail accounts?"

## How it works

The script `compose_new.py` lives in this skill's `scripts/` directory.

It uses Mail.app's `make new outgoing message` AppleScript command to create
a fresh compose window with the subject and From address pre-filled, adds
To/Cc/Bcc recipients via `make new ... recipient`, then explicitly focuses
the message body's text area (an AXWebArea) and pastes the body via the
clipboard (Cmd+V from System Events) — same proven clipboard pattern as
`draft_reply.py`. Finally it saves the message, which lands it in the
Drafts folder of the configured account. The compose window stays open
for review.

Required: Accessibility permission for the controlling app (one-time macOS
setup).

## Usage

### Required arguments

```bash
python3 scripts/compose_new.py \
    "<account>" "<to_addr>" "<subject>" "<body>"
```

- `<account>` — Mail account name (the `account_name` from
  `apple-mail-config.json`, e.g. `"Exchange"`).
- `<to_addr>` — single recipient email address.
- `<subject>` — subject line.
- `<body>` — plain-text body. Use `\n` for line breaks (preserved through clipboard).

### Optional flags

```bash
--cc "addr1@example.com,addr2@example.com"
--bcc "addr@example.com"
```

Both accept comma-separated lists of addresses.

## Workflow

1. **Identify recipient(s) and subject.** If the user names them directly,
   use them. If they're vague ("email Sarah"), ask for the address.
2. **Compose the body** based on the user's instructions. Keep the tone
   direct, plain English, no jargon — you're writing in the user's voice.
3. **Run the script** with the configured account name.
4. **Tell the user where the draft is** — "Saved to your Drafts folder in
   Mail. The compose window is open if you want to tweak it."

Don't ask permission for routine drafts — they're reversible. Just create
the draft and report back.

## Examples

**User:** "draft an email to ben@example.com, subject 'Project follow-up', saying I'll have feedback by Friday"

```bash
python3 scripts/compose_new.py \
    "Exchange" \
    "ben@example.com" \
    "Project follow-up" \
    "Hi Ben,

I'll have feedback for you by Friday.

<your name>"
```

**User:** "compose a new email to sarah@example.com about the founder dinner, cc john@example.com"

```bash
python3 scripts/compose_new.py \
    "Exchange" \
    "sarah@example.com" \
    "Founder dinner — date options" \
    "Hi Sarah,

A few date options for the founder dinner — let me know what works.

<your name>" \
    --cc "john@example.com"
```

## Output

On success the script prints something like:
```
OK: draft composed to ben@example.com -- subject "Project follow-up" -- saved to Drafts
```

If the named account doesn't exist or has no email addresses configured,
the script returns an error message starting with `ERROR:`. Pass that back
to the user verbatim.

## Edge cases

- **Body contains quotes (`"`) or special characters:** the script escapes
  these automatically before passing to AppleScript.
- **Multi-line bodies:** newlines are converted to `\n` for AppleScript
  but the clipboard paste preserves them visually in the compose window.
- **Multiple Cc or Bcc recipients:** pass them comma-separated in a single
  flag value, e.g. `--cc "a@x.com,b@y.com"`.
- **Other compose windows already open:** the script targets the new
  window specifically (by `first window of newMessage`, falling back to
  matching the subject) so it shouldn't affect any other open compose
  windows.

## What this skill does NOT do

- Send emails (the user sends manually from Drafts)
- Reply to existing messages — use `apple-mail-draft-reply` for that
- Search/read emails — use `apple-mail-search`
- Anything in Gmail (different tooling)
