#!/usr/bin/env python3
"""
awaiting_reply.py

"Emails I sent that haven't gotten a reply back yet."

Read-only. Iterates the configured account's Sent mailbox for messages sent
in the last N days, then for each one checks the INBOX for any inbound
message from the primary recipient AFTER the sent date. If none is found,
the sent message is flagged as "awaiting reply."

Same-domain recipients are excluded (internal forwards / FYI to colleagues
should not show up here). The configured account's own email-address domain
is detected via AppleScript at runtime.

Output (one per line, oldest-first / most overdue first):
    DATE_SENT | RECIPIENT | SUBJECT | (sent N days ago)

Usage:
    python3 awaiting_reply.py [--config PATH] [--days N] [--limit N]

Options:
    --config PATH  Path to apple-mail-config.json. If omitted, walks up from
                   CWD looking for the file.
    --days N       Only consider sent emails from the last N days (default 14).
    --limit N      Cap on sent emails to process (default 50). Bounds the
                   N x M scan against the inbox.

Config file shape:
    {
      "workspace_id": "my-workspace",
      "account_name": "Exchange"
    }

Notes:
    Best-effort heuristic. False positives (you don't actually need a reply)
    and false negatives (a reply came via another channel) are possible.
    Treat output as a starting list, not a definitive answer.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from common import (
    classify_priority,
    escape_applescript,
    inbox_mailbox_block,
    load_profile,
    parse_priority_rules,
    run_applescript,
    sent_mailbox_block,
)


USAGE = __doc__

FIELD_SEP = "|~|"
RECORD_SEP = "<<<REC>>>"

CONFIG_FILENAME = "apple-mail-config.json"

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
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--config", type=str, default=None)
    p.add_argument("--days", type=int, default=14)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--profile", type=str, default=None,
                   help="Path to user profile .md file.")
    p.add_argument("--show-priority", action="store_true",
                   help="Show priority labels in output (requires loaded profile).")
    p.add_argument("-h", "--help", action="store_true")
    try:
        args = p.parse_args()
    except SystemExit:
        print(USAGE)
        sys.exit(1)
    if args.help:
        print(USAGE)
        sys.exit(0)
    return args


def find_config(explicit_path: Optional[str]) -> Path:
    """Locate apple-mail-config.json.

    Order:
      1. --config <path> if provided.
      2. Walk up from CWD looking for the file.
      3. Error with guidance.
    """
    if explicit_path:
        p = Path(explicit_path).expanduser().resolve()
        if not p.is_file():
            print(f"ERROR: --config path does not exist: {p}")
            sys.exit(1)
        return p

    cwd = Path.cwd().resolve()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / CONFIG_FILENAME
        if candidate.is_file():
            return candidate

    print(
        f"ERROR: No {CONFIG_FILENAME} found. Either run from inside your "
        "workspace directory, or pass --config /path/to/config.json"
    )
    sys.exit(1)


def load_config(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: {path} is not valid JSON: {e}")
        sys.exit(1)

    account = data.get("account_name")
    if not account or not isinstance(account, str):
        print(f"ERROR: {path} must contain a string 'account_name' field.")
        sys.exit(1)
    return data


def strip_reply_prefix(subject: str) -> str:
    """Strip leading Re:/Fwd: (and variants) iteratively. Case-insensitive."""
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


def extract_email_address(recipient: str) -> str:
    """Pull the email out of a 'Name <addr@x>' style string. Returns the
    address lowercased; falls back to the whole string if no angle brackets.
    """
    if not recipient:
        return ""
    if "<" in recipient and ">" in recipient:
        start = recipient.index("<") + 1
        end = recipient.index(">", start)
        return recipient[start:end].strip().lower()
    return recipient.strip().lower()


def domain_of(email_addr: str) -> str:
    """Return the lowercased domain portion of an email address, or ''."""
    if not email_addr or "@" not in email_addr:
        return ""
    return email_addr.rsplit("@", 1)[1].strip().lower()


def is_automated(recipient: str) -> bool:
    s = recipient.lower()
    return any(p in s for p in AUTOMATED_PATTERNS)


def is_calendar_response(subject: str) -> bool:
    return subject.strip().lower().startswith(CALENDAR_PREFIXES)


def fetch_own_domain(account: str) -> str:
    """Ask Mail for the first email address on this account; return its domain."""
    safe_account = escape_applescript(account)
    script = f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
    set addrs to email addresses of targetAccount
    if addrs is missing value then return ""
    if (count of addrs) = 0 then return ""
    return item 1 of addrs
end tell
'''
    raw = run_applescript(script, timeout=30)
    return domain_of(raw.strip())


def fetch_sent_messages(account: str, days: int, limit: int) -> list[dict]:
    """Pull recent sent messages: date, primary recipient, subject."""
    safe_account = escape_applescript(account)
    script = f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{sent_mailbox_block("sentMailbox", "targetAccount")}

    set cutoffDate to (current date) - ({days} * days)
    set sentMessages to (every message of sentMailbox)
    set output to ""
    set processed to 0

    repeat with aMessage in sentMessages
        if processed >= {limit} then exit repeat
        try
            set msgDate to date sent of aMessage
            if msgDate >= cutoffDate then
                set msgSubject to subject of aMessage
                set toList to to recipients of aMessage
                set primaryRecipient to ""
                if (count of toList) > 0 then
                    set firstRecip to item 1 of toList
                    try
                        set recipName to name of firstRecip
                    on error
                        set recipName to ""
                    end try
                    try
                        set recipAddr to address of firstRecip
                    on error
                        set recipAddr to ""
                    end try
                    if recipName is missing value then set recipName to ""
                    if recipAddr is missing value then set recipAddr to ""
                    set primaryRecipient to recipName & " <" & recipAddr & ">"
                end if
                set isoDate to (year of msgDate as string) & "-"
                set m to month of msgDate as integer
                if m < 10 then set isoDate to isoDate & "0"
                set isoDate to isoDate & m & "-"
                set d to day of msgDate
                if d < 10 then set isoDate to isoDate & "0"
                set isoDate to isoDate & d
                set output to output & isoDate & "{FIELD_SEP}" & primaryRecipient & "{FIELD_SEP}" & msgSubject & "{RECORD_SEP}"
                set processed to processed + 1
            end if
        end try
    end repeat
    return output
end tell
'''
    raw = run_applescript(script, timeout=120)
    return parse_records(raw, ("date", "recipient", "subject"))


def fetch_inbox_messages(account: str, days: int) -> list[dict]:
    """Pull recent inbox messages with sender + date, for matching against
    sent messages. Pulled once and reused so we don't re-iterate per sent.
    """
    safe_account = escape_applescript(account)
    script = f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{inbox_mailbox_block("inboxMailbox", "targetAccount")}

    set cutoffDate to (current date) - ({days * 2} * days)
    set inboxMessages to (every message of inboxMailbox)
    set output to ""

    repeat with aMessage in inboxMessages
        try
            set msgDate to date received of aMessage
            if msgDate >= cutoffDate then
                set msgSender to sender of aMessage
                set isoDate to (year of msgDate as string) & "-"
                set m to month of msgDate as integer
                if m < 10 then set isoDate to isoDate & "0"
                set isoDate to isoDate & m & "-"
                set d to day of msgDate
                if d < 10 then set isoDate to isoDate & "0"
                set isoDate to isoDate & d
                set output to output & isoDate & "{FIELD_SEP}" & msgSender & "{RECORD_SEP}"
            end if
        end try
    end repeat
    return output
end tell
'''
    raw = run_applescript(script, timeout=120)
    return parse_records(raw, ("date", "sender"))


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

    config_path = find_config(args.config)
    config = load_config(config_path)
    account = config["account_name"]

    try:
        own_domain = fetch_own_domain(account)
    except SystemExit as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    try:
        sent = fetch_sent_messages(account, args.days, args.limit)
    except SystemExit as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not sent:
        print(f"No emails awaiting reply in last {args.days} days.")
        return

    try:
        inbox = fetch_inbox_messages(account, args.days)
    except SystemExit as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    inbox_by_sender: dict[str, list[str]] = {}
    for msg in inbox:
        addr = extract_email_address(msg["sender"])
        if not addr:
            continue
        inbox_by_sender.setdefault(addr, []).append(msg["date"])

    today = datetime.now().date()
    awaiting: list[tuple] = []

    # Load profile + parse priority rules. Empty dict if no profile —
    # behavior then matches pre-profile exactly.
    profile = load_profile(args.profile)
    priority_rules = parse_priority_rules(profile) if profile else {}
    has_rules = bool(profile) and any(priority_rules.get(k) for k in
                                      ("high_senders", "high_keywords",
                                       "noise_senders", "autopilot_ack_patterns"))

    for s in sent:
        recip_addr = extract_email_address(s["recipient"])
        if not recip_addr:
            continue

        if own_domain and domain_of(recip_addr) == own_domain:
            continue
        if is_automated(recip_addr):
            continue
        if is_calendar_response(s["subject"]):
            continue

        try:
            sent_date = datetime.strptime(s["date"], "%Y-%m-%d").date()
        except ValueError:
            continue

        got_reply = False
        for reply_date_str in inbox_by_sender.get(recip_addr, []):
            try:
                reply_date = datetime.strptime(reply_date_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            if reply_date >= sent_date:
                got_reply = True
                break

        if not got_reply:
            days_ago = (today - sent_date).days
            # Classify the recipient as if it were an inbound sender —
            # same priority rule set applies (high-priority person → high-
            # priority follow-up).
            pr = (classify_priority(s["recipient"], s["subject"], priority_rules)
                  if has_rules else None)
            awaiting.append((sent_date, s["recipient"], s["subject"], days_ago, pr))

    if not awaiting:
        print(f"No emails awaiting reply in last {args.days} days.")
        return

    awaiting.sort(key=lambda r: r[0])
    for date, recipient, subject, days_ago, pr in awaiting:
        suffix = f"(sent {days_ago} day{'s' if days_ago != 1 else ''} ago)"
        prefix = ""
        label = ""
        if has_rules:
            if pr == "high":
                prefix = "★ "
            elif pr == "noise":
                prefix = "(noise) "
            if args.show_priority:
                label = f" [{pr}]"
        print(f"{prefix}{date.isoformat()} | {recipient} | {subject} | {suffix}{label}")


if __name__ == "__main__":
    main()
