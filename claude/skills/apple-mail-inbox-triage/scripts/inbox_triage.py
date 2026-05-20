#!/usr/bin/env python3
"""
inbox_triage.py

"What inbox emails have arrived since I last looked that need my reply?"

Read-only. Incremental — only surfaces messages received since the last
successful run (per-user state stored in ~/.claude/state/<workspace>/).
First run defaults to a 24-hour lookback.

Filters out:
  - Automated senders (noreply, no-reply, notifications, @mailer.*, @mail.*)
  - Calendar invite replies (subject starts with "Accepted:" / "Declined:" /
    "Tentative:")
  - Anything you've already replied to — matched on real email threading
    headers (Message-ID / In-Reply-To / References), NOT subject strings.
    This avoids false-negatives when you forwarded the inbound internally.
  - Sent messages whose primary recipient is at the same email domain as
    the account (i.e. internal forwards to colleagues) are not counted as
    replies.

Output (default, one per line, oldest-first):
    DATE | SENDER | SUBJECT | first 80 chars of body

Output (--json mode, one JSON object per line / JSONL):
    {"date": "...", "sender": "...", "sender_name": "...",
     "sender_email": "...", "subject": "...", "message_id": "...",
     "body": "..."}

Usage:
    python3 inbox_triage.py [--config PATH] [--limit N] [--json]

Options:
    --config PATH   Path to apple-mail-config.json. If omitted, the script
                    walks up from the current directory looking for one.
    --limit N       Cap on inbox messages to process (default 50).
    --json          Emit JSONL (one JSON record per line) with full body
                    + parsed sender fields + Message-ID. Use this when a
                    downstream step needs the full message body (e.g. to
                    draft a reply).

Config file format (apple-mail-config.json):
    {
        "workspace_id": "my-workspace",
        "account_name": "Exchange"
    }
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
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

CONFIG_FILENAME = "apple-mail-config.json"

DEFAULT_FIRST_RUN_LOOKBACK_HOURS = 24

STATE_ROOT = Path.home() / ".claude" / "state"

MESSAGE_ID_RE = re.compile(r"<[^<>\s]+>")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(add_help=True, description="Incremental inbox triage for Apple Mail.")
    p.add_argument("--config", type=str, default=None,
                   help=f"Path to {CONFIG_FILENAME}. If omitted, search up from CWD.")
    p.add_argument("--limit", type=int, default=50,
                   help="Cap on inbox messages processed (default 50).")
    p.add_argument("--json", action="store_true",
                   help="Emit JSONL with full body + Message-ID instead of one-line summary.")
    p.add_argument("--profile", type=str, default=None,
                   help="Path to a user profile .md file. Defaults to "
                        "$APPLE_MAIL_PROFILE or "
                        "~/.claude/preferences/apple-mail/profile.md. "
                        "If no profile exists, runs in fully-generic mode.")
    p.add_argument("--show-priority", action="store_true",
                   help="Show priority labels (high / standard / autopilot-ack / "
                        "noise) in the default human-readable output. Off by "
                        "default so the bare output stays skimmable. Has no "
                        "effect if no profile is loaded.")
    return p.parse_args()


def find_config(explicit: Optional[str]) -> Path:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.is_file():
            raise SystemExit(f"Config file not found: {p}")
        return p

    cur = Path.cwd().resolve()
    for candidate in [cur, *cur.parents]:
        p = candidate / CONFIG_FILENAME
        if p.is_file():
            return p

    raise SystemExit(
        f"No {CONFIG_FILENAME} found. Either run from inside your workspace "
        f"directory, or pass --config /path/to/{CONFIG_FILENAME}"
    )


def load_config(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Config file is not valid JSON ({path}): {e}")

    workspace_id = data.get("workspace_id")
    account_name = data.get("account_name")
    if not workspace_id or not isinstance(workspace_id, str):
        raise SystemExit(f"Config missing 'workspace_id' string: {path}")
    if not account_name or not isinstance(account_name, str):
        raise SystemExit(f"Config missing 'account_name' string: {path}")
    return {"workspace_id": workspace_id, "account_name": account_name}


def state_file_for(workspace_id: str) -> Path:
    return STATE_ROOT / workspace_id / "inbox-triage-last-run.json"


def read_last_run(state_path: Path) -> Optional[datetime]:
    if not state_path.is_file():
        return None
    try:
        raw = state_path.read_text(encoding="utf-8").strip()
        ts = json.loads(raw) if raw.startswith('"') else raw
    except json.JSONDecodeError:
        return None
    try:
        dt = datetime.fromisoformat(ts)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def write_last_run(state_path: Path, when: datetime) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(when.isoformat()), encoding="utf-8")


def get_account_domain(account_name: str) -> Optional[str]:
    safe = escape_applescript(account_name)
    script = f'''
tell application "Mail"
    set targetAccount to account "{safe}"
    set addrs to email addresses of targetAccount
    if (count of addrs) = 0 then
        return ""
    end if
    return item 1 of addrs
end tell
'''
    raw = run_applescript(script, timeout=30)
    if "@" not in raw:
        return None
    return raw.split("@", 1)[1].strip().lower()


def fetch_inbox_since(account: str, since: datetime, limit: int) -> list[dict]:
    """Pull INBOX messages received after `since`, with Message-ID."""
    safe_account = escape_applescript(account)
    since_local = since.astimezone()
    yr = since_local.year
    mo = since_local.month
    dy = since_local.day
    hr = since_local.hour
    mn = since_local.minute
    sc = since_local.second

    script = f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{inbox_mailbox_block("inboxMailbox", "targetAccount")}

    set cutoffDate to current date
    set year of cutoffDate to {yr}
    set month of cutoffDate to {mo}
    set day of cutoffDate to {dy}
    set hours of cutoffDate to {hr}
    set minutes of cutoffDate to {mn}
    set seconds of cutoffDate to {sc}

    set inboxMessages to (every message of inboxMailbox)
    set output to ""
    set processed to 0

    repeat with aMessage in inboxMessages
        if processed >= {limit} then exit repeat
        try
            set msgDate to date received of aMessage
            if msgDate >= cutoffDate then
                set msgSubject to subject of aMessage
                set msgSender to sender of aMessage
                set msgId to ""
                try
                    set msgId to message id of aMessage
                end try
                if msgId is missing value then set msgId to ""
                set msgBody to ""
                try
                    set fullBody to content of aMessage
                    if fullBody is missing value then set fullBody to ""
                    set bodyLen to length of fullBody
                    if bodyLen > 3000 then
                        set msgBody to text 1 thru 3000 of fullBody
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
                set msgBody to my sanitize(msgBody)
                set msgSubject to my sanitize(msgSubject)
                set msgSender to my sanitize(msgSender)
                set msgId to my sanitize(msgId)
                set output to output & isoDate & "{FIELD_SEP}" & msgSender & "{FIELD_SEP}" & msgSubject & "{FIELD_SEP}" & msgId & "{FIELD_SEP}" & msgBody & "{RECORD_SEP}"
                set processed to processed + 1
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
    return parse_records(raw, ("date", "sender", "subject", "message_id", "body"))


def fetch_sent_with_headers(account: str, since: datetime) -> list[dict]:
    """Pull sent messages since `since`, including raw header blob and primary recipient."""
    safe_account = escape_applescript(account)
    since_local = since.astimezone()
    yr = since_local.year
    mo = since_local.month
    dy = since_local.day
    hr = since_local.hour
    mn = since_local.minute
    sc = since_local.second

    script = f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{sent_mailbox_block("sentMailbox", "targetAccount")}

    set cutoffDate to current date
    set year of cutoffDate to {yr}
    set month of cutoffDate to {mo}
    set day of cutoffDate to {dy}
    set hours of cutoffDate to {hr}
    set minutes of cutoffDate to {mn}
    set seconds of cutoffDate to {sc}

    set sentMessages to (every message of sentMailbox)
    set output to ""

    repeat with aMessage in sentMessages
        try
            set msgDate to date sent of aMessage
            if msgDate >= cutoffDate then
                set recipAddr to ""
                try
                    set recips to to recipients of aMessage
                    if (count of recips) > 0 then
                        set recipAddr to address of (item 1 of recips)
                    end if
                end try
                if recipAddr is missing value then set recipAddr to ""

                set headerBlob to ""
                try
                    set headerBlob to all headers of aMessage
                end try
                if headerBlob is missing value then set headerBlob to ""

                set recipAddr to my sanitize(recipAddr)
                set headerBlob to my sanitize(headerBlob)

                set output to output & recipAddr & "{FIELD_SEP}" & headerBlob & "{RECORD_SEP}"
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
    return parse_records(raw, ("recipient", "headers"))


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


def extract_header(headers: str, name: str) -> str:
    """Pull a single header value out of the raw header blob.

    AppleScript's `all headers` returns a single string with one header per
    line (folded continuations indented). We do a forgiving line-prefix match.
    """
    if not headers:
        return ""
    prefix = name.lower() + ":"
    out_lines: list[str] = []
    capturing = False
    for line in headers.replace("\r", "\n").split("\n"):
        if capturing:
            if line.startswith((" ", "\t")):
                out_lines.append(line.strip())
                continue
            break
        if line.lower().startswith(prefix):
            out_lines.append(line[len(prefix):].strip())
            capturing = True
    return " ".join(out_lines).strip()


def extract_message_ids(value: str) -> set[str]:
    if not value:
        return set()
    return {m for m in MESSAGE_ID_RE.findall(value)}


def normalize_message_id(value: str) -> str:
    v = value.strip()
    if not v:
        return ""
    if not v.startswith("<"):
        v = "<" + v
    if not v.endswith(">"):
        v = v + ">"
    return v


def split_sender(raw: str) -> tuple[str, str]:
    """Parse 'Name <addr@x>' into (name, address). Falls back gracefully."""
    s = (raw or "").strip()
    if not s:
        return "", ""
    if "<" in s and ">" in s:
        name = s.split("<", 1)[0].strip().strip('"').strip()
        addr = s.split("<", 1)[1].rsplit(">", 1)[0].strip().lower()
        return name, addr
    if "@" in s:
        return "", s.lower()
    return s, ""


def is_automated(sender: str) -> bool:
    s = sender.lower()
    return any(p in s for p in AUTOMATED_PATTERNS)


def is_calendar_response(subject: str) -> bool:
    return subject.strip().lower().startswith(CALENDAR_PREFIXES)


def main() -> None:
    args = parse_args()

    config_path = find_config(args.config)
    config = load_config(config_path)
    workspace_id = config["workspace_id"]
    account_name = config["account_name"]

    state_path = state_file_for(workspace_id)
    last_run = read_last_run(state_path)

    now = datetime.now(timezone.utc)
    if last_run is None:
        since = now - timedelta(hours=DEFAULT_FIRST_RUN_LOOKBACK_HOURS)
        since_label = "startup (first run)"
    else:
        since = last_run
        since_label = f"{since.astimezone().date().isoformat()}"

    try:
        own_domain = get_account_domain(account_name)
    except SystemExit as e:
        print(f"ERROR resolving account domain: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        inbox = fetch_inbox_since(account_name, since, args.limit)
    except SystemExit as e:
        print(f"ERROR fetching inbox: {e}", file=sys.stderr)
        sys.exit(1)

    if not inbox:
        print(f"No new inbox emails needing reply since {since_label}.")
        write_last_run(state_path, now)
        return

    try:
        sent = fetch_sent_with_headers(account_name, since)
    except SystemExit as e:
        print(f"ERROR fetching sent: {e}", file=sys.stderr)
        sys.exit(1)

    replied_to_ids: set[str] = set()
    for s in sent:
        recip = (s.get("recipient") or "").strip().lower()
        if own_domain and recip and "@" in recip:
            recip_domain = recip.split("@", 1)[1].strip()
            if recip_domain == own_domain:
                continue
        headers = s.get("headers", "")
        in_reply_to = extract_header(headers, "In-Reply-To")
        references = extract_header(headers, "References")
        replied_to_ids |= extract_message_ids(in_reply_to)
        replied_to_ids |= extract_message_ids(references)

    # Load the user profile (personal layer) if it exists. Empty dict if not —
    # in that case the priority logic is skipped entirely and output is
    # identical to the pre-profile behavior.
    profile = load_profile(args.profile)
    priority_rules = parse_priority_rules(profile) if profile else {}
    # "Rules present" means at least one of the four lists has a usable entry.
    has_rules = bool(profile) and any(priority_rules.get(k) for k in
                                      ("high_senders", "high_keywords",
                                       "noise_senders", "autopilot_ack_patterns"))

    needs = []
    for msg in inbox:
        sender = msg["sender"]
        subject = msg["subject"]

        if is_automated(sender):
            continue
        if is_calendar_response(subject):
            continue

        msg_id = normalize_message_id(msg.get("message_id", ""))
        if msg_id and msg_id in replied_to_ids:
            continue

        try:
            inbox_date = datetime.strptime(msg["date"], "%Y-%m-%d").date()
        except ValueError:
            continue

        body = msg.get("body", "")
        body_clean = re.sub(r"[ \t]+", " ", body).strip()
        snippet = re.sub(r"\s+", " ", body_clean)[:80]

        record = {
            "date": inbox_date,
            "sender": sender,
            "subject": subject,
            "message_id": msg_id,
            "body": body_clean,
            "snippet": snippet,
        }
        if has_rules:
            record["priority"] = classify_priority(sender, subject, priority_rules)
        needs.append(record)

    if not needs:
        print(f"No new inbox emails needing reply since {since_label}.")
        write_last_run(state_path, now)
        return

    needs.sort(key=lambda r: r["date"])

    if args.json:
        # When a profile is loaded, emit a header record carrying the full
        # profile so downstream drafting agents have voice/identity context
        # without a separate file read. Each per-message record carries its
        # priority label so the same agent can sort + decide which to draft.
        if profile:
            print(json.dumps({"_profile": profile}, ensure_ascii=False))
        for r in needs:
            name, addr = split_sender(r["sender"])
            out = {
                "date": r["date"].isoformat(),
                "sender": r["sender"],
                "sender_name": name,
                "sender_email": addr,
                "subject": r["subject"],
                "message_id": r["message_id"],
                "body": r["body"],
            }
            if has_rules:
                out["priority"] = r.get("priority", "standard")
            print(json.dumps(out, ensure_ascii=False))
    else:
        for r in needs:
            prefix = ""
            label = ""
            if has_rules:
                pr = r.get("priority", "standard")
                if pr == "high":
                    prefix = "★ "  # ★ marker for the human reader
                elif pr == "noise":
                    prefix = "(noise) "
                if args.show_priority:
                    label = f" [{pr}]"
            print(f"{prefix}{r['date'].isoformat()} | {r['sender']} | "
                  f"{r['subject']} | {r['snippet']}{label}")

    write_last_run(state_path, now)


if __name__ == "__main__":
    main()
