#!/usr/bin/env python3
"""
list_inbox.py

List recent INBOX emails for an Apple Mail account, sorted by date received
(newest first).

Usage:
    python3 list_inbox.py <account> [--limit N] [--unread-only]

Args:
    <account>      Mail account name as configured in Mail.app (e.g. "Exchange").
    --limit N      Max emails to return. Default 50.
    --unread-only  If set, only include messages whose read status is false.

Output:
    Header line, then one line per message:
        [unread/read] DATE | SENDER | SUBJECT
    followed by a "TOTAL: N" footer.

Examples:
    python3 list_inbox.py "Exchange"
    python3 list_inbox.py "Exchange" --limit 10
    python3 list_inbox.py "Exchange" --unread-only --limit 25
"""

import argparse
import sys

from common import (
    escape_applescript,
    inbox_mailbox_block,
    run_applescript,
)


USAGE = __doc__


def build_script(account: str, limit: int, unread_only: bool) -> str:
    safe_account = escape_applescript(account)
    unread_filter = "true" if unread_only else "false"

    return f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{inbox_mailbox_block("inboxMailbox", "targetAccount")}

    set allMessages to (every message of inboxMailbox)
    set msgCount to count of allMessages
    if msgCount is 0 then
        return "TOTAL: 0"
    end if

    -- Collect into a list of records-like tuples (date, message ref)
    -- We then sort by date desc and trim to limit.
    set unreadOnly to {unread_filter}
    set maxItems to {limit}

    set msgList to {{}}
    repeat with i from 1 to msgCount
        set aMessage to item i of allMessages
        try
            set msgRead to read status of aMessage
            if (not unreadOnly) or (msgRead is false) then
                set msgDate to date received of aMessage
                set end of msgList to {{msgDate, aMessage}}
            end if
        end try
    end repeat

    set listLen to count of msgList
    if listLen is 0 then
        return "TOTAL: 0"
    end if

    -- Insertion sort by date desc (newest first). Fine for low thousands.
    repeat with i from 2 to listLen
        set curItem to item i of msgList
        set curDate to item 1 of curItem
        set j to i - 1
        repeat while j > 0
            set cmpItem to item j of msgList
            set cmpDate to item 1 of cmpItem
            if cmpDate < curDate then
                set item (j + 1) of msgList to cmpItem
                set j to j - 1
            else
                exit repeat
            end if
        end repeat
        set item (j + 1) of msgList to curItem
    end repeat

    if listLen < maxItems then
        set takeN to listLen
    else
        set takeN to maxItems
    end if

    set outputLines to {{}}
    repeat with i from 1 to takeN
        set entry to item i of msgList
        set theMessage to item 2 of entry
        set theDate to item 1 of entry
        try
            set theSubject to subject of theMessage
        on error
            set theSubject to "(no subject)"
        end try
        try
            set theSender to sender of theMessage
        on error
            set theSender to "(unknown sender)"
        end try
        try
            set isRead to read status of theMessage
        on error
            set isRead to true
        end try
        if isRead then
            set readMark to "[read]   "
        else
            set readMark to "[unread] "
        end if
        set dateStr to (theDate as string)
        set lineStr to readMark & dateStr & " | " & theSender & " | " & theSubject
        set end of outputLines to lineStr
    end repeat

    set AppleScript's text item delimiters to linefeed
    set headerLine to "INBOX of " & "{safe_account}" & " (showing " & takeN & " of " & listLen & " matching)"
    set bodyText to outputLines as text
    set AppleScript's text item delimiters to ""
    return headerLine & linefeed & bodyText & linefeed & "TOTAL: " & takeN
end tell
'''


def main() -> None:
    if len(sys.argv) == 1:
        print(USAGE)
        sys.exit(1)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("account")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--unread-only", action="store_true")

    try:
        args = parser.parse_args()
    except SystemExit:
        print(USAGE)
        sys.exit(1)

    if args.limit < 1:
        print("ERROR: --limit must be >= 1")
        sys.exit(1)

    try:
        out = run_applescript(
            build_script(args.account, args.limit, args.unread_only),
            timeout=180,
        )
    except SystemExit as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    print(out)


if __name__ == "__main__":
    main()
