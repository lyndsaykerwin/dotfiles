#!/usr/bin/env python3
"""
get_email.py

Read the full content of a single email from an Apple Mail mailbox. Matches
the most recent message whose subject contains the given keyword.

Usage:
    python3 get_email.py <account> <subject_keyword> [--mailbox NAME]

Args:
    <account>          Mail account name as configured in Mail.app (e.g. "Exchange").
    <subject_keyword>  Case-insensitive substring of the subject to match.
                       The newest matching message is returned.
    --mailbox NAME     Mailbox to search. Default "Inbox" (with INBOX fallback).
                       Common values: Inbox, Drafts, Sent, "Sent Items".

Output:
    From: ...
    To: ...
    Cc: ...
    Date: ...
    Subject: ...
    Message-ID: ...

    ----------------------------------------
    <full body>

Examples:
    python3 get_email.py "Exchange" "Project Discussion"
    python3 get_email.py "Exchange" "invoice" --mailbox Sent
"""

import argparse
import sys
from typing import Optional

from common import (
    escape_applescript,
    inbox_mailbox_block,
    run_applescript,
)


USAGE = __doc__


def build_script(account: str, keyword: str, mailbox: Optional[str]) -> str:
    safe_account = escape_applescript(account)
    safe_keyword = escape_applescript(keyword)

    if mailbox is None or mailbox.lower() == "inbox":
        mailbox_block = inbox_mailbox_block("targetMailbox", "targetAccount")
    else:
        safe_mb = escape_applescript(mailbox)
        # Try the user-given name first, then case variants.
        mailbox_block = f'''
    try
        set targetMailbox to mailbox "{safe_mb}" of targetAccount
    on error
        try
            set targetMailbox to mailbox "{safe_mb.upper()}" of targetAccount
        on error
            set targetMailbox to mailbox "{safe_mb.lower()}" of targetAccount
        end try
    end try'''

    return f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{mailbox_block}

    set allMessages to (every message of targetMailbox)
    set msgCount to count of allMessages
    if msgCount is 0 then
        return "ERROR: mailbox is empty"
    end if

    set foundMessage to missing value
    set foundDate to missing value
    repeat with i from 1 to msgCount
        set aMessage to item i of allMessages
        try
            set s to subject of aMessage
            ignoring case
                if s contains "{safe_keyword}" then
                    set msgDate to date received of aMessage
                    if foundDate is missing value or msgDate > foundDate then
                        set foundDate to msgDate
                        set foundMessage to aMessage
                    end if
                end if
            end ignoring
        end try
    end repeat

    if foundMessage is missing value then
        return "ERROR: no message in mailbox with subject containing '{safe_keyword}'"
    end if

    try
        set hSubject to subject of foundMessage
    on error
        set hSubject to "(no subject)"
    end try
    try
        set hSender to sender of foundMessage
    on error
        set hSender to "(unknown sender)"
    end try
    try
        set hDate to (date received of foundMessage) as string
    on error
        set hDate to "(unknown date)"
    end try
    try
        set hMsgId to message id of foundMessage
    on error
        set hMsgId to "(no message-id)"
    end try

    -- To recipients
    set toList to {{}}
    try
        repeat with r in (to recipients of foundMessage)
            try
                set rname to name of r
            on error
                set rname to ""
            end try
            try
                set raddr to address of r
            on error
                set raddr to ""
            end try
            if rname is "" or rname is missing value then
                set end of toList to raddr
            else
                set end of toList to rname & " <" & raddr & ">"
            end if
        end repeat
    end try
    set AppleScript's text item delimiters to ", "
    set hTo to toList as text
    set AppleScript's text item delimiters to ""
    if hTo is "" then set hTo to "(none)"

    -- Cc recipients
    set ccList to {{}}
    try
        repeat with r in (cc recipients of foundMessage)
            try
                set rname to name of r
            on error
                set rname to ""
            end try
            try
                set raddr to address of r
            on error
                set raddr to ""
            end try
            if rname is "" or rname is missing value then
                set end of ccList to raddr
            else
                set end of ccList to rname & " <" & raddr & ">"
            end if
        end repeat
    end try
    set AppleScript's text item delimiters to ", "
    set hCc to ccList as text
    set AppleScript's text item delimiters to ""
    if hCc is "" then set hCc to "(none)"

    try
        set hBody to content of foundMessage
    on error
        set hBody to "(could not read body)"
    end try

    set headerBlock to "From: " & hSender & linefeed & ¬
        "To: " & hTo & linefeed & ¬
        "Cc: " & hCc & linefeed & ¬
        "Date: " & hDate & linefeed & ¬
        "Subject: " & hSubject & linefeed & ¬
        "Message-ID: " & hMsgId

    return headerBlock & linefeed & linefeed & "----------------------------------------" & linefeed & hBody
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

    if out.startswith("ERROR:"):
        print(out)
        sys.exit(1)
    print(out)


if __name__ == "__main__":
    main()
