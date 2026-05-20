---
name: apple-mail-search
description: Search and read emails in Apple Mail using the account configured in apple-mail-config.json. Use when the user says things like "find that email from...", "search my inbox for...", "show me unread...", "what did X say...", or "show me the thread about...". Read-only — lists recent inbox messages, searches by subject/sender/body/date/read-status, fetches full content of a single email, or assembles all messages in a thread across INBOX + Sent + Drafts. DO NOT use for Gmail accounts.
---

# Apple Mail: Search & Read

Read-only inspection of the configured Apple Mail account (the one named in
`apple-mail-config.json`). Four scripts that together let Claude find and
read emails before doing anything else (drafting a reply, summarizing a
thread, answering a "what did X say" question).

## When to use this skill

Trigger when the user asks any of:
- "find that email from [person] about [topic]"
- "search my inbox for [keyword]"
- "show me unread emails" / "what's unread from [person]"
- "what did [person] say in their last email"
- "show me the thread about [topic]"
- "pull up the email about [topic]" / "open the [X] email"
- "what's in my inbox" / "what's the latest in my inbox"

## When NOT to use this skill

**Do NOT use for Gmail accounts.** This skill only drives Apple Mail
(Mail.app on macOS) via AppleScript. Gmail-hosted addresses need a
Gmail-specific tool.

If the user is ambiguous about which account, ASK: "Which account — your
Apple Mail inbox (the one in `apple-mail-config.json`), or one of your
Gmail accounts?"

## How it works

Four scripts in this skill's `scripts/` directory:

| Script | When to use |
|---|---|
| `list_inbox.py` | User wants a recent-inbox listing with no specific filter |
| `search_emails.py` | User wants to filter by subject / sender / body / date / unread |
| `get_email.py` | User wants the full body of one specific email |
| `get_thread.py` | User wants the whole conversation (INBOX + Sent + Drafts) |

Each uses AppleScript via `osascript` to read directly from Mail.app — no
network calls, no MCP server. Large mailboxes (a few thousand messages)
make filters like `--limit` and `--unread-only` matter for speed. Default
limit is 50.

The account name passed to each script is the `account_name` field from
`apple-mail-config.json` (case-sensitive — that's the Mail.app account
label, not an email address). Common defaults are `"Exchange"`, `"Work"`,
`"iCloud"`.

## Usage

### list_inbox.py — recent INBOX messages

```bash
python3 scripts/list_inbox.py "<account>" [--limit N] [--unread-only]
```

Default limit 50. Output: header + lines of `[unread/read] DATE | SENDER | SUBJECT` + `TOTAL: N` footer.

### search_emails.py — filtered search

```bash
python3 scripts/search_emails.py "<account>" \
    [--subject KEY] [--sender KEY] [--body KEY] \
    [--from-date YYYY-MM-DD] [--to-date YYYY-MM-DD] \
    [--unread-only] [--limit N]
```

At least one filter is required. Default limit 50. Substring matches are
case-insensitive. Output ends with `FOUND: N`.

### get_email.py — full body of one email

```bash
python3 scripts/get_email.py "<account>" "<subject keyword>" [--mailbox NAME]
```

Returns the newest matching message in the given mailbox (default `Inbox`,
with `INBOX` fallback). Output: `From / To / Cc / Date / Subject /
Message-ID` headers, separator, full body.

### get_thread.py — whole conversation

```bash
python3 scripts/get_thread.py "<account>" "<subject keyword>"
```

Strips `Re:` / `Fwd:` prefixes from the seed subject and collects every
matching message across **INBOX + Sent + Drafts**. Output: oldest first,
each message as `[mailbox] DATE | SENDER -> RECIPIENT | SUBJECT` followed
by a 300-char body excerpt.

## Workflow

1. **Pick the right script.** "Find the email from..." → `search_emails.py`
   with `--sender`. "Show me the thread about..." → `get_thread.py`. "What
   did Ben say in his project email?" → `get_email.py`. "What's new in my
   inbox?" → `list_inbox.py`.
2. **Run the script.** Pass the account name from `apple-mail-config.json`.
3. **Summarize the result for the user in plain English.** Don't dump raw
   output unless asked — say "I found 3 unread emails from Ben this
   week. Here's the gist..." Then offer to drill in.
4. **Chain naturally.** If the user said "find Ben's email about the project
   and draft a reply saying Friday works", run `search_emails.py` or
   `get_email.py` first to confirm the right thread, then call the
   `apple-mail-draft-reply` skill.

## Examples

**User:** "find that email from Ben"
```bash
python3 scripts/search_emails.py "Exchange" --sender "ben" --limit 10
```

**User:** "show me unread from this week"
```bash
python3 scripts/search_emails.py "Exchange" --unread-only --from-date 2026-04-27
```

**User:** "what did Ben say about the project"
```bash
python3 scripts/get_email.py "Exchange" "Project"
```

**User:** "show me the whole thread about the project"
```bash
python3 scripts/get_thread.py "Exchange" "Project"
```

**User:** "what's in my inbox"
```bash
python3 scripts/list_inbox.py "Exchange" --limit 20
```

## Output

- Successful runs print to stdout. Pass the relevant bits back to the user
  in plain English. Don't paraphrase headers like sender/date if they're
  asking about provenance — quote them.
- Errors start with `ERROR:` and exit code 1. Pass the error verbatim and
  ask the user how to proceed (different keyword? wrong account name?).

## Edge cases

- **Empty results on a search that should match:** the substring filter is
  case-insensitive but exact (no fuzzy matching). Try a shorter / more
  unique keyword. For sender filters, surnames usually beat full names.
- **Slow searches:** large inboxes (1000+ messages) make an unfiltered
  `list_inbox.py` with a high limit slow (can take 30-60s). Always pass
  `--limit` if you have a reasonable bound.
- **`get_thread.py` returns only one message:** thread detection works by
  normalized-subject match. If correspondents changed the subject mid-
  thread, the older messages won't be picked up — fall back to
  `search_emails.py` with `--sender` and `--from-date` to assemble it
  manually.

## What this skill does NOT do

- Send or modify or delete emails (read-only)
- Touch Gmail (different tooling)
- Search across multiple accounts (one account per invocation)
- Search attachment contents (the `apple-mail-attachments` skill covers
  attachment listing/saving)
