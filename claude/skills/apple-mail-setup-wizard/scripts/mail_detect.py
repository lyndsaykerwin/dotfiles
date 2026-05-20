"""
mail_detect.py - AppleScript-driven detection of Apple Mail state.

What this knows how to do:
  - list_accounts()          -> [{"name": ..., "type": ..., "email": ...}, ...]
  - account_email(name)      -> "sam@example.com" or None
  - dump_sent_to_file(...)   -> Path to a temp file with the last N sent emails

Every call returns None / [] / a sensible empty answer on failure rather than
crashing — the wizard catches "no accounts found" and asks the user, rather
than dumping a Python traceback.

Sent-mail dump format (plain text, one record per email, separated by =====):

    DATE: 2026-05-15T09:42:00
    TO: someone@example.com
    SUBJECT: Re: scheduling
    BODY:
    Hi Jane,

    Thanks for the times. Tuesday 2pm works on my end - calendar invite coming
    your way shortly. Have a great weekend.

    Best,
    Sam
    =====
    DATE: ...

Claude reads this file directly during the voice-analysis pass.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from wizard_common import escape_applescript, run_applescript


_SEP_FIELD = "|~F~|"
_SEP_REC = "<<<MAIL_REC>>>"


def list_accounts() -> list[dict]:
    """Return all Apple Mail accounts as [{"name": "...", "type": "...", "email": "..."}].

    Returns [] if Mail isn't running or AppleScript fails.
    """
    script = f'''
tell application "Mail"
    set output to ""
    set accts to every account
    repeat with anAcct in accts
        set acctName to name of anAcct
        try
            set acctType to (account type of anAcct) as string
        on error
            set acctType to ""
        end try
        set firstEmail to ""
        try
            set addrs to email addresses of anAcct
            if (count of addrs) > 0 then
                set firstEmail to item 1 of addrs
            end if
        end try
        if firstEmail is missing value then set firstEmail to ""
        set output to output & acctName & "{_SEP_FIELD}" & acctType & "{_SEP_FIELD}" & firstEmail & "{_SEP_REC}"
    end repeat
    return output
end tell
'''
    raw = run_applescript(script, timeout=30)
    if raw is None:
        return []
    accounts: list[dict] = []
    for chunk in raw.split(_SEP_REC):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(_SEP_FIELD)
        if len(parts) != 3:
            continue
        name, atype, email = (p.strip() for p in parts)
        accounts.append({"name": name, "type": atype, "email": email})
    return accounts


def account_email(account_name: str) -> Optional[str]:
    """Return the first email address registered to `account_name`, or None."""
    safe = escape_applescript(account_name)
    script = f'''
tell application "Mail"
    try
        set a to account "{safe}"
        set addrs to email addresses of a
        if (count of addrs) > 0 then return item 1 of addrs
    end try
    return ""
end tell
'''
    raw = run_applescript(script, timeout=15)
    if not raw or "@" not in raw:
        return None
    return raw.strip()


def dump_sent_to_file(account_name: str, target: Path, max_emails: int = 30) -> int:
    """Read the last `max_emails` sent emails from `account_name` and write
    them to `target` as a delimited plain-text file.

    Returns the number of emails written. Returns 0 on AppleScript failure
    or if no sent mail is found.
    """
    safe = escape_applescript(account_name)
    # We do the formatting in AppleScript so the Python side just writes a blob.
    # The script grabs the LAST max_emails items (most recent), then writes
    # them oldest-first by reversing in Python afterwards.
    script = f'''
tell application "Mail"
    try
        set a to account "{safe}"
    on error
        return ""
    end try

    set sentMailbox to missing value
    set sentNames to {{"Sent", "Sent Messages", "Sent Items", "SENT"}}
    repeat with sentName in sentNames
        try
            set sentMailbox to mailbox sentName of a
            exit repeat
        end try
    end repeat
    if sentMailbox is missing value then return ""

    set allMsgs to messages of sentMailbox
    set msgCount to count of allMsgs
    if msgCount = 0 then return ""

    set want to {max_emails}
    if msgCount < want then set want to msgCount

    set output to ""
    set processed to 0
    set i to 1
    repeat while processed < want and i <= msgCount
        try
            set m to item i of allMsgs
            set isoDate to ""
            try
                set d to date sent of m
                set isoDate to (year of d as string) & "-"
                set mo to month of d as integer
                if mo < 10 then set isoDate to isoDate & "0"
                set isoDate to isoDate & mo & "-"
                set dy to day of d
                if dy < 10 then set isoDate to isoDate & "0"
                set isoDate to isoDate & dy & "T"
                set hr to hours of d
                if hr < 10 then set isoDate to isoDate & "0"
                set isoDate to isoDate & hr & ":"
                set mn to minutes of d
                if mn < 10 then set isoDate to isoDate & "0"
                set isoDate to isoDate & mn
            end try

            set recipAddr to ""
            try
                set rs to to recipients of m
                if (count of rs) > 0 then set recipAddr to address of (item 1 of rs)
            end try
            if recipAddr is missing value then set recipAddr to ""

            set subj to ""
            try
                set subj to subject of m
            end try
            if subj is missing value then set subj to ""

            set body to ""
            try
                set body to content of m
            end try
            if body is missing value then set body to ""
            -- cap body to keep the dump file readable
            try
                set bodyLen to length of body
                if bodyLen > 3000 then set body to text 1 thru 3000 of body
            end try

            set subj to my sanitize(subj)
            set recipAddr to my sanitize(recipAddr)
            set body to my sanitizeBody(body)

            set output to output & isoDate & "{_SEP_FIELD}" & recipAddr & "{_SEP_FIELD}" & subj & "{_SEP_FIELD}" & body & "{_SEP_REC}"
            set processed to processed + 1
        end try
        set i to i + 1
    end repeat
    return output
end tell

on sanitize(t)
    if t is missing value then return ""
    set t to my replaceText(t, return, " ")
    set t to my replaceText(t, linefeed, " ")
    set t to my replaceText(t, tab, " ")
    set t to my replaceText(t, "{_SEP_FIELD}", " ")
    set t to my replaceText(t, "{_SEP_REC}", " ")
    return t
end sanitize

on sanitizeBody(t)
    -- preserve newlines in body; just protect our delimiters
    if t is missing value then return ""
    set t to my replaceText(t, return, linefeed)
    set t to my replaceText(t, "{_SEP_FIELD}", " ")
    set t to my replaceText(t, "{_SEP_REC}", " ")
    return t
end sanitizeBody

on replaceText(t, findStr, replaceStr)
    set AppleScript's text item delimiters to findStr
    set parts to text items of t
    set AppleScript's text item delimiters to replaceStr
    set t to parts as string
    set AppleScript's text item delimiters to ""
    return t
end replaceText
'''
    raw = run_applescript(script, timeout=240)
    if not raw:
        return 0

    records: list[tuple[str, str, str, str]] = []
    for chunk in raw.split(_SEP_REC):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(_SEP_FIELD)
        if len(parts) != 4:
            continue
        date, to, subj, body = parts
        records.append((date.strip(), to.strip(), subj.strip(), body))

    if not records:
        return 0

    # Mail returns most-recent-first; flip to oldest-first so the dump reads
    # as a timeline.
    records.reverse()

    lines: list[str] = []
    lines.append(f"# Apple Mail sent-mail dump")
    lines.append(f"# Account: {account_name}")
    lines.append(f"# Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"# Count: {len(records)}")
    lines.append("")
    for date, to, subj, body in records:
        lines.append(f"DATE: {date}")
        lines.append(f"TO: {to}")
        lines.append(f"SUBJECT: {subj}")
        lines.append("BODY:")
        lines.append(body.rstrip())
        lines.append("=====")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(records)
