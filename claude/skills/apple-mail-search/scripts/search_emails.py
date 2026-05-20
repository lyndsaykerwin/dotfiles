#!/usr/bin/env python3
"""
search_emails.py

Search INBOX of an Apple Mail account by one or more criteria. Sorted by date
received, newest first.

Usage:
    python3 search_emails.py <account> [--subject KEY] [--sender KEY]
                                       [--body KEY] [--from-date YYYY-MM-DD]
                                       [--to-date YYYY-MM-DD]
                                       [--unread-only] [--limit N]

Args:
    <account>           Mail account name as configured in Mail.app (e.g. "Exchange").
    --subject KEY       Substring to match (case-insensitive) in the subject.
    --sender KEY        Substring to match (case-insensitive) in the sender.
    --body KEY          Substring to match (case-insensitive) in the body content.
    --from-date YYYY-MM-DD  Only include messages received on/after this date.
    --to-date YYYY-MM-DD    Only include messages received on/before this date.
    --unread-only       Only include messages whose read status is false.
    --limit N           Max emails to return. Default 50.

At least one filter is required (subject, sender, body, from-date, to-date,
or unread-only). Otherwise use list_inbox.py.

Output:
    Header line, then one line per message:
        [unread/read] DATE | SENDER | SUBJECT
    then a "FOUND: N" footer.

Examples:
    python3 search_emails.py "Exchange" --sender "newsletter"
    python3 search_emails.py "Exchange" --subject "Project Discussion" --limit 10
    python3 search_emails.py "Exchange" --from-date 2026-04-01 --unread-only
"""

import argparse
import sys
from datetime import datetime
from typing import List, Optional

from common import (
    escape_applescript,
    inbox_mailbox_block,
    run_applescript,
)


USAGE = __doc__


def parse_date(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: invalid date '{s}', expected YYYY-MM-DD")
        sys.exit(1)


def applescript_date_literal(dt: datetime, end_of_day: bool = False) -> str:
    """Build an AppleScript `date "..."` literal for a Python datetime.

    AppleScript's `date "YYYY-MM-DD HH:MM:SS"` form is parsed by the system
    locale, so we instead build a date object via `current date` and set its
    fields explicitly to avoid locale surprises.
    """
    if end_of_day:
        h, m, s = 23, 59, 59
    else:
        h, m, s = 0, 0, 0
    return (
        f'(my buildDate({dt.year}, {dt.month}, {dt.day}, {h}, {m}, {s}))'
    )


def build_script(
    account: str,
    subject_key: Optional[str],
    sender_key: Optional[str],
    body_key: Optional[str],
    from_date: Optional[datetime],
    to_date: Optional[datetime],
    unread_only: bool,
    limit: int,
) -> str:
    safe_account = escape_applescript(account)

    # Build per-message AppleScript filter clauses. We do filtering inside the
    # repeat loop (rather than `whose ...`) so we can combine multiple criteria
    # without a giant whose-clause and so we can do case-insensitive compares
    # via `considering case` blocks.
    filters: List[str] = []

    if subject_key is not None:
        safe = escape_applescript(subject_key)
        filters.append(
            f'''
            try
                set s to subject of aMessage
                ignoring case
                    if s does not contain "{safe}" then set keepIt to false
                end ignoring
            on error
                set keepIt to false
            end try'''
        )

    if sender_key is not None:
        safe = escape_applescript(sender_key)
        filters.append(
            f'''
            try
                set sd to sender of aMessage
                ignoring case
                    if sd does not contain "{safe}" then set keepIt to false
                end ignoring
            on error
                set keepIt to false
            end try'''
        )

    if body_key is not None:
        safe = escape_applescript(body_key)
        filters.append(
            f'''
            try
                set bd to content of aMessage
                ignoring case
                    if bd does not contain "{safe}" then set keepIt to false
                end ignoring
            on error
                set keepIt to false
            end try'''
        )

    if from_date is not None:
        from_lit = applescript_date_literal(from_date, end_of_day=False)
        filters.append(
            f'''
            try
                if (date received of aMessage) < {from_lit} then set keepIt to false
            on error
                set keepIt to false
            end try'''
        )

    if to_date is not None:
        to_lit = applescript_date_literal(to_date, end_of_day=True)
        filters.append(
            f'''
            try
                if (date received of aMessage) > {to_lit} then set keepIt to false
            on error
                set keepIt to false
            end try'''
        )

    if unread_only:
        filters.append(
            '''
            try
                if (read status of aMessage) is true then set keepIt to false
            on error
                set keepIt to false
            end try'''
        )

    filter_block = "\n".join(filters)

    return f'''
on buildDate(y, m, d, hh, mm, ss)
    set theDate to current date
    set year of theDate to y
    set month of theDate to m
    set day of theDate to d
    set hours of theDate to hh
    set minutes of theDate to mm
    set seconds of theDate to ss
    return theDate
end buildDate

tell application "Mail"
    set targetAccount to account "{safe_account}"
{inbox_mailbox_block("inboxMailbox", "targetAccount")}

    set allMessages to (every message of inboxMailbox)
    set msgCount to count of allMessages
    if msgCount is 0 then
        return "FOUND: 0"
    end if

    set maxItems to {limit}

    set msgList to {{}}
    repeat with i from 1 to msgCount
        set aMessage to item i of allMessages
        set keepIt to true
{filter_block}
        if keepIt then
            try
                set msgDate to date received of aMessage
                set end of msgList to {{msgDate, aMessage}}
            end try
        end if
    end repeat

    set listLen to count of msgList
    if listLen is 0 then
        return "Search of INBOX of " & "{safe_account}" & ": no matches" & linefeed & "FOUND: 0"
    end if

    -- Insertion sort by date desc (newest first).
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
    set headerLine to "Search of INBOX of " & "{safe_account}" & " (showing " & takeN & " of " & listLen & " matching)"
    set bodyText to outputLines as text
    set AppleScript's text item delimiters to ""
    return headerLine & linefeed & bodyText & linefeed & "FOUND: " & takeN
end tell
'''


def main() -> None:
    if len(sys.argv) == 1:
        print(USAGE)
        sys.exit(1)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("account")
    parser.add_argument("--subject")
    parser.add_argument("--sender")
    parser.add_argument("--body")
    parser.add_argument("--from-date", dest="from_date")
    parser.add_argument("--to-date", dest="to_date")
    parser.add_argument("--unread-only", action="store_true")
    parser.add_argument("--limit", type=int, default=50)

    try:
        args = parser.parse_args()
    except SystemExit:
        print(USAGE)
        sys.exit(1)

    if args.limit < 1:
        print("ERROR: --limit must be >= 1")
        sys.exit(1)

    if not any(
        [
            args.subject,
            args.sender,
            args.body,
            args.from_date,
            args.to_date,
            args.unread_only,
        ]
    ):
        print(
            "ERROR: at least one filter required "
            "(--subject, --sender, --body, --from-date, --to-date, or --unread-only). "
            "Use list_inbox.py for an unfiltered listing."
        )
        sys.exit(1)

    from_dt = parse_date(args.from_date) if args.from_date else None
    to_dt = parse_date(args.to_date) if args.to_date else None

    try:
        out = run_applescript(
            build_script(
                account=args.account,
                subject_key=args.subject,
                sender_key=args.sender,
                body_key=args.body,
                from_date=from_dt,
                to_date=to_dt,
                unread_only=args.unread_only,
                limit=args.limit,
            ),
            timeout=300,
        )
    except SystemExit as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    print(out)


if __name__ == "__main__":
    main()
