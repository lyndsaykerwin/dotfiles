#!/usr/bin/env python3
"""
get_thread.py

Show all messages in a conversation thread for an Apple Mail account.
Matches across INBOX, Sent, and Drafts. Threading is approximated by
stripping "Re:" / "Fwd:" prefixes from subjects and grouping by the
remaining stem.

Usage:
    python3 get_thread.py <account> <subject_keyword>

Args:
    <account>          Mail account name as configured in Mail.app (e.g. "Exchange").
    <subject_keyword>  Case-insensitive substring used to find the thread.
                       The script first finds the newest message whose subject
                       contains this keyword, normalizes its subject (strip
                       Re:/Fwd:), then collects every message in INBOX/Sent/
                       Drafts whose normalized subject matches.

Output:
    For each message in the thread (oldest first):
        [mailbox] DATE | SENDER -> RECIPIENT | SUBJECT
        <body excerpt, up to 300 chars>
        ----

Examples:
    python3 get_thread.py "Exchange" "Project Discussion"
    python3 get_thread.py "Exchange" "Q2 review"
"""

import argparse
import sys

from common import (
    drafts_mailbox_block,
    escape_applescript,
    inbox_mailbox_block,
    run_applescript,
    sent_mailbox_block,
)


USAGE = __doc__


def build_script(account: str, keyword: str) -> str:
    safe_account = escape_applescript(account)
    safe_keyword = escape_applescript(keyword)

    return f'''
on normalizeSubject(s)
    -- Strip leading Re:, Fwd:, Fw:, RE:, FWD:, FW: (any case, possibly repeated)
    -- and surrounding whitespace.
    set t to s
    set changed to true
    repeat while changed
        set changed to false
        set t to my trimWS(t)
        if (length of t) >= 3 then
            set p3 to text 1 thru 3 of t
            ignoring case
                if p3 is "re:" or p3 is "fw:" then
                    set t to text 4 thru (length of t) of t
                    set changed to true
                end if
            end ignoring
        end if
        if (not changed) and (length of t) >= 4 then
            set p4 to text 1 thru 4 of t
            ignoring case
                if p4 is "fwd:" then
                    set t to text 5 thru (length of t) of t
                    set changed to true
                end if
            end ignoring
        end if
    end repeat
    return my trimWS(t)
end normalizeSubject

on trimWS(s)
    set t to s
    repeat while (length of t) > 0 and (text 1 thru 1 of t) is in {{" ", tab}}
        set t to text 2 thru (length of t) of t
    end repeat
    repeat while (length of t) > 0 and (text -1 thru -1 of t) is in {{" ", tab}}
        set t to text 1 thru -2 of t
    end repeat
    return t
end trimWS

on excerptBody(b, n)
    if b is missing value then return "(no body)"
    set t to b as text
    -- Replace newlines with spaces for the excerpt.
    set AppleScript's text item delimiters to {{return, linefeed}}
    set parts to text items of t
    set AppleScript's text item delimiters to " "
    set t to parts as text
    set AppleScript's text item delimiters to ""
    if (length of t) > n then
        return (text 1 thru n of t) & "..."
    else
        return t
    end if
end excerptBody

on collectFrom(theMailbox, mailboxLabel, normTarget, accumulator)
    tell application "Mail"
        set msgs to (every message of theMailbox)
        repeat with i from 1 to (count of msgs)
            set aMessage to item i of msgs
            try
                set s to subject of aMessage
                set ns to my normalizeSubject(s)
                ignoring case
                    if ns is normTarget then
                        try
                            set md to date received of aMessage
                        on error
                            set md to current date
                        end try
                        try
                            set sd to sender of aMessage
                        on error
                            set sd to "(unknown)"
                        end try
                        -- Recipients (to)
                        set toList to {{}}
                        try
                            repeat with r in (to recipients of aMessage)
                                try
                                    set raddr to address of r
                                on error
                                    set raddr to ""
                                end try
                                if raddr is not "" then set end of toList to raddr
                            end repeat
                        end try
                        set AppleScript's text item delimiters to ", "
                        set toStr to toList as text
                        set AppleScript's text item delimiters to ""
                        if toStr is "" then set toStr to "(unknown)"
                        try
                            set bodyTxt to content of aMessage
                        on error
                            set bodyTxt to ""
                        end try
                        set excerpt to my excerptBody(bodyTxt, 300)
                        set end of accumulator to {{md, mailboxLabel, sd, toStr, s, excerpt}}
                    end if
                end ignoring
            end try
        end repeat
    end tell
    return accumulator
end collectFrom

tell application "Mail"
    set targetAccount to account "{safe_account}"
{inbox_mailbox_block("inboxMailbox", "targetAccount")}

    -- Find the seed message (newest in INBOX matching keyword) for normalization.
    set seedSubject to missing value
    set seedDate to missing value
    repeat with aMessage in (every message of inboxMailbox)
        try
            set s to subject of aMessage
            ignoring case
                if s contains "{safe_keyword}" then
                    set md to date received of aMessage
                    if seedDate is missing value or md > seedDate then
                        set seedDate to md
                        set seedSubject to s
                    end if
                end if
            end ignoring
        end try
    end repeat

    -- Fall back: search Sent if INBOX has no match.
    if seedSubject is missing value then
        try
{sent_mailbox_block("sentMbForSeed", "targetAccount")}
            repeat with aMessage in (every message of sentMbForSeed)
                try
                    set s to subject of aMessage
                    ignoring case
                        if s contains "{safe_keyword}" then
                            set md to date sent of aMessage
                            if seedDate is missing value or md > seedDate then
                                set seedDate to md
                                set seedSubject to s
                            end if
                        end if
                    end ignoring
                end try
            end repeat
        end try
    end if

    if seedSubject is missing value then
        return "ERROR: no message in INBOX or Sent with subject containing '{safe_keyword}'"
    end if
end tell

set normTarget to my normalizeSubject(seedSubject)

set thread to {{}}
tell application "Mail"
    set targetAccount to account "{safe_account}"
{inbox_mailbox_block("inboxMailbox2", "targetAccount")}
end tell
set thread to my collectFrom(inboxMailbox2, "INBOX", normTarget, thread)

try
    tell application "Mail"
        set targetAccount to account "{safe_account}"
{sent_mailbox_block("sentMailbox", "targetAccount")}
    end tell
    set thread to my collectFrom(sentMailbox, "Sent", normTarget, thread)
end try

try
    tell application "Mail"
        set targetAccount to account "{safe_account}"
{drafts_mailbox_block("draftsMailbox", "targetAccount")}
    end tell
    set thread to my collectFrom(draftsMailbox, "Drafts", normTarget, thread)
end try

set threadLen to count of thread
if threadLen is 0 then
    return "ERROR: thread normalization succeeded but no messages collected (subject: '" & seedSubject & "')"
end if

-- Insertion sort by date asc (oldest first).
repeat with i from 2 to threadLen
    set curItem to item i of thread
    set curDate to item 1 of curItem
    set j to i - 1
    repeat while j > 0
        set cmpItem to item j of thread
        set cmpDate to item 1 of cmpItem
        if cmpDate > curDate then
            set item (j + 1) of thread to cmpItem
            set j to j - 1
        else
            exit repeat
        end if
    end repeat
    set item (j + 1) of thread to curItem
end repeat

set outputLines to {{}}
set headerLine to "Thread '" & normTarget & "' across INBOX + Sent + Drafts (" & threadLen & " messages, oldest first)"
set end of outputLines to headerLine
repeat with i from 1 to threadLen
    set entry to item i of thread
    set d to item 1 of entry
    set lbl to item 2 of entry
    set sd to item 3 of entry
    set toStr to item 4 of entry
    set s to item 5 of entry
    set ex to item 6 of entry
    set headerStr to "[" & lbl & "] " & (d as string) & " | " & sd & " -> " & toStr & " | " & s
    set end of outputLines to headerStr
    set end of outputLines to ex
    set end of outputLines to "----"
end repeat

set AppleScript's text item delimiters to linefeed
set outText to outputLines as text
set AppleScript's text item delimiters to ""
return outText
'''


def main() -> None:
    if len(sys.argv) == 1:
        print(USAGE)
        sys.exit(1)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("account")
    parser.add_argument("subject_keyword")

    try:
        args = parser.parse_args()
    except SystemExit:
        print(USAGE)
        sys.exit(1)

    try:
        out = run_applescript(
            build_script(args.account, args.subject_keyword),
            timeout=300,
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
