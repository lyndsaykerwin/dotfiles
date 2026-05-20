---
name: apple-mail-draft-reply
description: Draft a threaded reply in Apple Mail for the account configured in apple-mail-config.json. Use when the user asks to "draft a reply", "respond to", "write a reply", or "draft a response" to an email they received in Apple Mail. The draft is saved to Drafts with full threading (In-Reply-To, References, "Re:" subject), Mail's auto-quoted prior context with formatting preserved, and the account's signature. The draft is NEVER sent — the user reviews and sends manually. DO NOT use for Gmail accounts.
---

# Apple Mail: Draft Threaded Reply

Drafts a reply in Apple Mail for the account named in `apple-mail-config.json`
(the `account_name` field). Threading, auto-quoted body, signature, and
recipient are all preserved automatically by Mail.app.

## When to use this skill

Trigger when the user asks to draft/write/compose a reply to:
- An email in their Apple Mail inbox (the account configured for this workspace)
- "the email from [person]" when [person] is in the configured account
- "the most recent email" when context is Apple Mail

Phrases like:
- "draft a reply to that email from Ben about the project, saying Friday works"
- "respond to the latest email in my inbox"
- "write a reply to John saying I'll review tonight"

## When NOT to use this skill

**Do NOT use for Gmail accounts.** This skill only drives Apple Mail
(Mail.app on macOS) via AppleScript. Gmail-hosted addresses need a
Gmail-specific tool.

If the user is ambiguous about which account, ASK: "Which account — your
Apple Mail inbox (the one in `apple-mail-config.json`), or one of your
Gmail accounts?"

## How it works

The script `draft_reply.py` lives in this skill's `scripts/` directory.

It uses Mail.app's native `reply ... with opening window` AppleScript command
(which sets all threading metadata and creates a properly formatted compose
window with auto-quoted prior body), then pastes the reply text at the top
via clipboard, then saves to Drafts. The compose window stays open so the
user can review.

Required: Accessibility permission for the controlling app (one-time macOS
setup).

## Usage

### Reply to most recent INBOX message

```bash
python3 scripts/draft_reply.py "<account>" "<reply text>"
```

`<account>` is the Apple Mail account label exactly as it appears in
`apple-mail-config.json` (`account_name`), e.g. `"Exchange"` or `"Work"`.

### Reply to a specific email (by subject keyword)

```bash
python3 scripts/draft_reply.py "<account>" "<reply text>" "<subject keyword>"
```

The keyword matches the FIRST email in the INBOX whose subject contains it
(case-sensitive). Pick a unique-ish phrase from the email's subject.

### Add CC recipients

Pass `--cc` with one or more email addresses (comma-separated, or repeat
the flag). The original To recipient (set by Mail's native reply) is left
alone — CC's are added on top.

```bash
python3 scripts/draft_reply.py "<account>" "<reply text>" \
  --cc "alice@example.com,bob@example.com"
```

Or repeated:

```bash
python3 scripts/draft_reply.py "<account>" "<reply text>" "<subject keyword>" \
  --cc alice@example.com --cc bob@example.com
```

`--cc` can appear anywhere on the command line — positional args
(account / reply text / subject keyword) are parsed independently.

## Workflow

1. **Identify the target email.** If the user names the email (sender, subject
   keyword), use the 3-arg form. If they say "most recent" or don't
   specify, use the 2-arg form.
2. **Compose the reply text** based on the user's instructions. Keep the
   tone direct, plain English, no jargon — you're writing in the user's
   voice.
3. **Run the script.** Pass the account name from `apple-mail-config.json`.
4. **Tell the user where the draft is** — "Saved to your Drafts folder in
   Mail. Open Mail to review and send."

Don't ask permission for routine drafts — they're reversible. Just create
the draft and report back.

## Examples

**User:** "draft a reply to that Ben email about Thursday saying Friday works better"

```bash
python3 scripts/draft_reply.py "Exchange" "Hi Ben,

Thursday's tough — could we do Friday instead? Same time works for me.

Best,
<your name>" "Project"
```

**User:** "write a reply to the most recent email saying I got it and will respond tomorrow"

```bash
python3 scripts/draft_reply.py "Exchange" "Got it — I'll send a full response tomorrow.

<your name>"
```

**User:** "reply to the Ben email and cc Erik and Maya"

```bash
python3 scripts/draft_reply.py "Exchange" "Hi Ben,

Looping in Erik and Maya so we're all aligned.

<your name>" "Project" \
  --cc "erik@example.com,maya@example.com"
```

## Output

On success the script prints something like:
```
OK: replied to "RE: Project Discussion" from Person <person@example.com> -- draft saved
```

If the script can't find a matching email (3-arg form with bad keyword) or
the inbox is empty (2-arg form), it returns an error message starting with
`ERROR:`. Pass that back to the user verbatim.

## Edge cases

- **Reply text contains quotes (`"`) or special characters:** the script
  escapes these automatically before passing to AppleScript.
- **Multi-line reply text:** newlines are converted to `\n` for AppleScript
  but the clipboard paste preserves them visually in the compose window.
- **A compose window is already open:** the script targets the new reply
  window specifically (`set index of newComposeWindow to 1`) so it shouldn't
  affect any other open compose windows.

## What this skill does NOT do

- Send emails (the user sends manually from Drafts)
- Compose new emails (not a reply) — use the `apple-mail-draft-new` skill
- Search/read emails — use the `apple-mail-search` skill
- Anything in Gmail (different tooling)
