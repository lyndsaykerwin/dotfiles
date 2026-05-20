#!/usr/bin/env python3
"""
needs_response.py

"Recent inbox emails that probably want a response from me."

Read-only. Iterates the account's INBOX for messages received in the last
N days that are unread OR flagged. Filters out:
  - Automated senders (noreply, no-reply, donotreply, notifications,
    @mailer.* / @mail.* subdomains)
  - Calendar invite replies (subject starts with "Accepted:", "Declined:",
    "Tentative:")
  - Anything the user has already replied to (matched in Sent by "Re:" subject
    sent after the inbox message arrived)

Output (one per line, oldest-first):
    DATE | SENDER | SUBJECT | first 80 chars of body

Usage:
    python3 needs_response.py <account> [--days N] [--limit N]

Options:
    --days N    Only consider inbox emails from the last N days (default 7).
    --limit N   Cap on inbox emails to process (default 50).

Examples:
    python3 needs_response.py "Exchange"
    python3 needs_response.py "Exchange" --days 14 --limit 20

Notes:
    Best-effort heuristic. Will miss some emails that genuinely need a reply
    (false negatives) and surface some that don't (false positives). Treat
    as a starting list, not gospel.
"""

import argparse
import re
import sys
from datetime import datetime

from common import (
    escape_applescript,
    inbox_mailbox_block,
    run_applescript,
    sent_mailbox_block,
)


USAGE = __doc__

FIELD_SEP = "|~|"
RECORD_SEP = "<<<REC>>>"

AUTOMATED_PATTERNS = [
    "noreply",
    "no-reply",
    "no_reply",
    "donotreply",
    "do-not-reply",
    "do_not_reply",
    "notifications",
    "notification@",
    "@mailer.",
    "@mail.",
]

CALENDAR_PREFIXES = ("accepted:", "declined:", "tentative:")


def parse_args() -> argparse.Namespace:
    if len(sys.argv) < 2:
        print(USAGE)
        sys.exit(1)
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("account")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--limit", type=int, default=50)
    try:
        return p.parse_args()
    except SystemExit:
        print(USAGE)
        sys.exit(1)


def strip_reply_prefix(subject: str) -> str:
    s = subject.strip()
    changed = True
    while changed:
        changed = False
        low = s.lower()
        for prefix in ("re:", "fwd:", "fw:", "re :", "fwd :", "fw :"):
            if low.startswith(prefix):
                s = s[len(prefix):].strip()
                changed = True
                break
    return s


def is_automated(sender: str) -> bool:
    s = sender.lower()
    return any(p in s for p in AUTOMATED_PATTERNS)


def is_calendar_response(subject: str) -> bool:
    return subject.strip().lower().startswith(CALENDAR_PREFIXES)


def fetch_inbox_unread_or_flagged(account: str, days: int, limit: int) -> list[dict]:
    """Pull recent INBOX messages that are unread OR flagged."""
    safe_account = escape_applescript(account)
    script = f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{inbox_mailbox_block("inboxMailbox", "targetAccount")}

    set cutoffDate to (current date) - ({days} * days)
    set inboxMessages to (every message of inboxMailbox)
    set output to ""
    set processed to 0

    repeat with aMessage in inboxMessages
        if processed >= {limit} then exit repeat
        try
            set msgDate to date received of aMessage
            if msgDate >= cutoffDate then
                set isUnread to read status of aMessage is false
                set isFlagged to false
                try
                    set flagIndex to flag index of aMessage
                    if flagIndex is not -1 and flagIndex is not missing value then
                        set isFlagged to true
                    end if
                end try
                if isUnread or isFlagged then
                    set msgSubject to subject of aMessage
                    set msgSender to sender of aMessage
                    set msgBody to ""
                    try
                        set fullBody to content of aMessage
                        if fullBody is missing value then set fullBody to ""
                        set bodyLen to length of fullBody
                        if bodyLen > 200 then
                            set msgBody to text 1 thru 200 of fullBody
                        else
                            set msgBody to fullBody
                        end if
                    end try
                    set isoDate to (year of msgDate as string) & "-"
                    set m to month of msgDate as integer
                    if m < 10 then set isoDate to isoDate & "0"
                    set isoDate to isoDate & m & "-"
                    set d to day of msgDate
                    if d < 10 then set isoDate to isoDate & "0"
                    set isoDate to isoDate & d
                    -- Replace newlines / tabs / pipes in body so they don't
                    -- collide with our field/record separators.
                    set msgBody to my sanitize(msgBody)
                    set msgSubject to my sanitize(msgSubject)
                    set msgSender to my sanitize(msgSender)
                    set output to output & isoDate & "{FIELD_SEP}" & msgSender & "{FIELD_SEP}" & msgSubject & "{FIELD_SEP}" & msgBody & "{RECORD_SEP}"
                    set processed to processed + 1
                end if
            end if
        end try
    end repeat
    return output
end tell

on sanitize(t)
    if t is missing value then return ""
    set t to my replaceText(t, return, " ")
    set t to my replaceText(t, linefeed, " ")
    set t to my replaceText(t, tab, " ")
    set t to my replaceText(t, "{FIELD_SEP}", " ")
    set t to my replaceText(t, "{RECORD_SEP}", " ")
    return t
end sanitize

on replaceText(t, findStr, replaceStr)
    set AppleScript's text item delimiters to findStr
    set parts to text items of t
    set AppleScript's text item delimiters to replaceStr
    set t to parts as string
    set AppleScript's text item delimiters to ""
    return t
end replaceText
'''
    raw = run_applescript(script, timeout=180)
    return parse_records(raw, ("date", "sender", "subject", "body"))


def fetch_sent_subjects(account: str, days: int) -> list[dict]:
    """Pull recent sent messages: date + (stripped) subject. Used to detect
    'I already replied' on an inbox message.
    """
    safe_account = escape_applescript(account)
    # Look back days*2 to safely cover replies sent shortly after a recent
    # incoming message lands at the boundary of the inbox window.
    script = f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{sent_mailbox_block("sentMailbox", "targetAccount")}

    set cutoffDate to (current date) - ({days * 2} * days)
    set sentMessages to (every message of sentMailbox)
    set output to ""

    repeat with aMessage in sentMessages
        try
            set msgDate to date sent of aMessage
            if msgDate >= cutoffDate then
                set msgSubject to subject of aMessage
                set isoDate to (year of msgDate as string) & "-"
                set m to month of msgDate as integer
                if m < 10 then set isoDate to isoDate & "0"
                set isoDate to isoDate & m & "-"
                set d to day of msgDate
                if d < 10 then set isoDate to isoDate & "0"
                set isoDate to isoDate & d
                set output to output & isoDate & "{FIELD_SEP}" & msgSubject & "{RECORD_SEP}"
            end if
        end try
    end repeat
    return output
end tell
'''
    raw = run_applescript(script, timeout=120)
    return parse_records(raw, ("date", "subject"))


def parse_records(raw: str, fields: tuple) -> list[dict]:
    if not raw:
        return []
    records = []
    for chunk in raw.split(RECORD_SEP):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(FIELD_SEP)
        if len(parts) != len(fields):
            continue
        records.append(dict(zip(fields, [p.strip() for p in parts])))
    return records


def main() -> None:
    args = parse_args()

    try:
        inbox = fetch_inbox_unread_or_flagged(args.account, args.days, args.limit)
    except SystemExit as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not inbox:
        print(f"Inbox-zero on the last {args.days} days.")
        return

    try:
        sent = fetch_sent_subjects(args.account, args.days)
    except SystemExit as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Index sent: { stripped_subject_lower -> [datetime.date] }
    sent_by_subject: dict[str, list[datetime]] = {}
    for s in sent:
        key = strip_reply_prefix(s["subject"]).lower()
        if not key:
            continue
        try:
            d = datetime.strptime(s["date"], "%Y-%m-%d").date()
        except ValueError:
            continue
        sent_by_subject.setdefault(key, []).append(d)

    needs = []
    for msg in inbox:
        sender = msg["sender"]
        subject = msg["subject"]

        if is_automated(sender):
            continue
        if is_calendar_response(subject):
            continue

        # Already replied?
        try:
            inbox_date = datetime.strptime(msg["date"], "%Y-%m-%d").date()
        except ValueError:
            continue
        key = strip_reply_prefix(subject).lower()
        replied = False
        for sent_date in sent_by_subject.get(key, []):
            if sent_date >= inbox_date:
                replied = True
                break
        if replied:
            continue

        body = msg.get("body", "")
        # Collapse whitespace runs and trim to 80 chars.
        body = re.sub(r"\s+", " ", body).strip()
        snippet = body[:80]

        needs.append((inbox_date, sender, subject, snippet))

    if not needs:
        print(f"Inbox-zero on the last {args.days} days.")
        return

    needs.sort(key=lambda r: r[0])
    for date, sender, subject, snippet in needs:
        print(f"{date.isoformat()} | {sender} | {subject} | {snippet}")


if __name__ == "__main__":
    main()
