#!/usr/bin/env python3
"""
list_attachments.py

List the attachments on a single email in an Apple Mail account. Finds the
first message in the chosen mailbox whose subject contains the supplied
keyword and prints each attachment's name and size in bytes.

Usage:
    python3 list_attachments.py <account> <subject_keyword> [--mailbox NAME]

Args:
    <account>          Mail account name as configured in Mail.app (e.g. "Exchange").
    <subject_keyword>  Case-sensitive substring of the email's subject.
    --mailbox NAME     Mailbox to search inside the account. Default Inbox
                       (with INBOX/Inbox fallback).

Behavior:
    Refuses if 0 or 2+ messages match the keyword.
    If the matched email has no attachments, prints a friendly message and
    exits 0 (not an error).

Output (success, attachments present):
    Subject: <subject of matching email>
    [1] FILENAME (SIZE bytes)
    [2] FILENAME (SIZE bytes)
    ...

Output (no attachments):
    No attachments on email '<subject>'

Examples:
    python3 list_attachments.py "Exchange" "Q3 deck"
    python3 list_attachments.py "Exchange" "diligence" --mailbox "Sent"
"""

from __future__ import annotations

import argparse
import sys

from common import (
    escape_applescript,
    inbox_mailbox_block,
    run_applescript,
)


USAGE = __doc__


def build_script(account: str, keyword: str, mailbox: str | None) -> str:
    safe_account = escape_applescript(account)
    safe_keyword = escape_applescript(keyword)

    if mailbox is None:
        mailbox_block = inbox_mailbox_block("targetMailbox", "targetAccount")
    else:
        safe_mailbox = escape_applescript(mailbox)
        mailbox_block = (
            f'    set targetMailbox to mailbox "{safe_mailbox}" of targetAccount'
        )

    # Output format from AppleScript:
    #   line 1: "MATCH_COUNT: <n>"
    #   line 2: "SUBJECT: <subject>"          (only if n == 1)
    #   line 3+: "ATT|<name>|<size>"          (one per attachment, only if n == 1)
    return f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{mailbox_block}

    set matchedMessages to {{}}
    repeat with aMessage in (every message of targetMailbox)
        try
            if subject of aMessage contains "{safe_keyword}" then
                set end of matchedMessages to aMessage
                if (count of matchedMessages) > 1 then exit repeat
            end if
        end try
    end repeat

    set matchCount to count of matchedMessages
    if matchCount is 0 then
        return "MATCH_COUNT: 0"
    end if
    if matchCount > 1 then
        return "MATCH_COUNT: 2"
    end if

    set foundMessage to item 1 of matchedMessages
    set theSubject to subject of foundMessage

    set outputLines to {{}}
    set end of outputLines to "MATCH_COUNT: 1"
    set end of outputLines to "SUBJECT: " & theSubject

    set atts to mail attachments of foundMessage
    repeat with anAtt in atts
        try
            set attName to name of anAtt
        on error
            set attName to "(unnamed)"
        end try
        try
            set attSize to file size of anAtt
        on error
            set attSize to 0
        end try
        set end of outputLines to "ATT|" & attName & "|" & attSize
    end repeat

    set AppleScript's text item delimiters to linefeed
    set joined to outputLines as text
    set AppleScript's text item delimiters to ""
    return joined
end tell
'''


def main() -> None:
    if len(sys.argv) == 1:
        print(USAGE)
        sys.exit(1)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("account")
    parser.add_argument("subject_keyword")
    parser.add_argument("--mailbox", default=None)

    try:
        args = parser.parse_args()
    except SystemExit:
        print(USAGE)
        sys.exit(1)

    try:
        out = run_applescript(
            build_script(args.account, args.subject_keyword, args.mailbox),
            timeout=180,
        )
    except SystemExit as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    lines = out.splitlines()
    if not lines:
        print("ERROR: empty response from Mail")
        sys.exit(1)

    header = lines[0].strip()
    mailbox_label = args.mailbox if args.mailbox else "Inbox"

    if header == "MATCH_COUNT: 0":
        print(
            f"ERROR: No message in {mailbox_label} of '{args.account}' "
            f"with subject containing '{args.subject_keyword}'"
        )
        sys.exit(1)

    if header == "MATCH_COUNT: 2":
        print(
            f"ERROR: Multiple messages in {mailbox_label} of '{args.account}' "
            f"with subject containing '{args.subject_keyword}'. "
            f"Use a more specific keyword."
        )
        sys.exit(1)

    if header != "MATCH_COUNT: 1":
        print(f"ERROR: unexpected response header: {header!r}")
        sys.exit(1)

    # Parse: line 2 is SUBJECT, remaining are ATT|name|size rows.
    subject_line = lines[1] if len(lines) > 1 else "SUBJECT: "
    subject = subject_line[len("SUBJECT: "):] if subject_line.startswith("SUBJECT: ") else subject_line
    att_lines = lines[2:]

    if not att_lines:
        print(f"No attachments on email '{subject}'")
        sys.exit(0)

    print(f"Subject: {subject}")
    for idx, raw in enumerate(att_lines, start=1):
        # Format: ATT|<name>|<size>. Name itself can't contain '|' from Mail's
        # attachment objects in practice, but be defensive: rsplit to peel
        # size off the right.
        if not raw.startswith("ATT|"):
            continue
        body = raw[len("ATT|"):]
        # Peel size off the right
        if "|" in body:
            name, size = body.rsplit("|", 1)
        else:
            name, size = body, "?"
        print(f"[{idx}] {name} ({size} bytes)")


if __name__ == "__main__":
    main()
