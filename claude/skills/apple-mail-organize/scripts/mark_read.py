#!/usr/bin/env python3
"""
mark_read.py

Mark INBOX messages as read (default) or unread (--unread) in Apple Mail.

Safety: at least one filter (--subject, --sender, or --all-from-sender) is
required. Default --max-marks is 50, hard cap 500.

Usage:
    python3 mark_read.py <account> [filters] [--unread] [--max-marks N] [--dry-run]

Filters (at least ONE required):
    --subject KEY              Subject contains KEY
    --sender KEY               Sender contains KEY (matches subset of inbox)
    --all-from-sender SENDER   Sender contains SENDER, no other limit (alias
                               of --sender for clarity in batch operations)

Options:
    --unread                   Mark as unread instead of read
    --max-marks N              Max messages to mark (default 50, hard cap 500)
    --dry-run                  Print what would be marked, do not change

Examples:
    python3 mark_read.py "Exchange" --sender "Granola" --max-marks 10 --dry-run
    python3 mark_read.py "Exchange" --all-from-sender "newsletter@foo.com"
    python3 mark_read.py "Exchange" --subject "Daily Digest" --unread
"""

import argparse
import sys

from common import escape_applescript, inbox_mailbox_block, run_applescript


HARD_CAP = 500
DEFAULT_MAX_MARKS = 50


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("account", help="Apple Mail account name")
    parser.add_argument("--subject", default=None, help="Subject contains KEY")
    parser.add_argument("--sender", default=None, help="Sender contains KEY")
    parser.add_argument(
        "--all-from-sender",
        default=None,
        help="Sender contains SENDER (alias for --sender, semantic for batch)",
    )
    parser.add_argument("--unread", action="store_true", help="Mark as unread (default: mark read)")
    parser.add_argument(
        "--max-marks",
        type=int,
        default=DEFAULT_MAX_MARKS,
        help=f"Max messages to mark (default {DEFAULT_MAX_MARKS}, hard cap {HARD_CAP})",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print matches; do not change state")
    return parser.parse_args()


def validate(args: argparse.Namespace) -> None:
    if not (args.subject or args.sender or args.all_from_sender):
        print(
            "ERROR: at least one filter required (--subject, --sender, or --all-from-sender)."
        )
        sys.exit(1)

    if args.max_marks < 1:
        print("ERROR: --max-marks must be >= 1")
        sys.exit(1)

    if args.max_marks > HARD_CAP:
        print(
            f"ERROR: --max-marks {args.max_marks} exceeds hard cap of {HARD_CAP}. "
            f"Refusing — use a smaller batch."
        )
        sys.exit(1)


def build_filter_clauses(args: argparse.Namespace) -> str:
    clauses = []
    if args.subject:
        safe = escape_applescript(args.subject)
        clauses.append(f'(subject of aMessage contains "{safe}")')
    sender_key = args.sender or args.all_from_sender
    if sender_key:
        safe = escape_applescript(sender_key)
        clauses.append(f'(sender of aMessage contains "{safe}")')
    return " and ".join(clauses)


def main() -> None:
    args = parse_args()
    validate(args)

    safe_account = escape_applescript(args.account)
    filter_expr = build_filter_clauses(args)
    new_read_value = "false" if args.unread else "true"
    action_label = "Marked unread" if args.unread else "Marked read"
    dry_label = "would mark unread" if args.unread else "would mark read"
    dry = "true" if args.dry_run else "false"

    script = f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{inbox_mailbox_block("inboxMailbox", "targetAccount")}

    set matchedSubjects to {{}}
    set matchedDates to {{}}
    set matchedRefs to {{}}
    set markCount to 0
    set maxMarks to {args.max_marks}
    set isDryRun to {dry}

    repeat with aMessage in (every message of inboxMailbox)
        if markCount >= maxMarks then exit repeat
        try
            if {filter_expr} then
                set end of matchedSubjects to (subject of aMessage)
                set end of matchedDates to ((date received of aMessage) as string)
                set end of matchedRefs to aMessage
                set markCount to markCount + 1
            end if
        end try
    end repeat

    set output to ""
    if isDryRun then
        set output to "DRY RUN: {dry_label} " & markCount & " message(s):"
        repeat with i from 1 to (count of matchedSubjects)
            set output to output & linefeed & "  - [" & (item i of matchedDates) & "] " & (item i of matchedSubjects)
        end repeat
    else
        repeat with msgRef in matchedRefs
            try
                set read status of msgRef to {new_read_value}
            end try
        end repeat
        set output to "{action_label}: " & markCount & " message(s)"
        if markCount > 0 then
            repeat with i from 1 to (count of matchedSubjects)
                set output to output & linefeed & "  - [" & (item i of matchedDates) & "] " & (item i of matchedSubjects)
            end repeat
        end if
    end if

    return output
end tell
'''

    out = run_applescript(script, timeout=180)
    if out.startswith("ERROR:"):
        print(out)
        sys.exit(1)
    print(out)


if __name__ == "__main__":
    main()
