#!/usr/bin/env python3
"""
move_email.py

Move messages from an account's INBOX to a target mailbox in Apple Mail.

Safety model: at least one filter (subject, sender, or date range) is REQUIRED
— running with no filter would empty the inbox. A small `--max-moves` default
prevents runaway bulk moves; hard cap of 100 per call.

Usage:
    python3 move_email.py <account> --to-mailbox NAME [filters] [options]

Required:
    <account>             Apple Mail account name (e.g. "Exchange")
    --to-mailbox NAME     Destination mailbox in the same account

Filters (at least ONE required):
    --subject KEY         Subject contains KEY (case-sensitive)
    --sender KEY          Sender (name or address) contains KEY
    --from-date YYYY-MM-DD  Only messages on/after this date
    --to-date YYYY-MM-DD    Only messages on/before this date

Options:
    --max-moves N         Max messages to move (default 5, hard cap 100)
    --dry-run             Print what would be moved, do not move

Examples:
    python3 move_email.py "Exchange" --to-mailbox "Archive" --sender "Granola" --dry-run
    python3 move_email.py "Exchange" --to-mailbox "Archive" --subject "Newsletter" --max-moves 20
"""

import argparse
import sys

from common import escape_applescript, inbox_mailbox_block, run_applescript


HARD_CAP = 100
DEFAULT_MAX_MOVES = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Move INBOX messages to a target mailbox.",
        usage=__doc__,
    )
    parser.add_argument("account", help="Apple Mail account name")
    parser.add_argument("--to-mailbox", required=True, help="Destination mailbox")
    parser.add_argument("--subject", default=None, help="Subject contains KEY")
    parser.add_argument("--sender", default=None, help="Sender contains KEY")
    parser.add_argument("--from-date", default=None, help="On/after YYYY-MM-DD")
    parser.add_argument("--to-date", default=None, help="On/before YYYY-MM-DD")
    parser.add_argument(
        "--max-moves",
        type=int,
        default=DEFAULT_MAX_MOVES,
        help=f"Max messages to move (default {DEFAULT_MAX_MOVES}, hard cap {HARD_CAP})",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print what would move; do not move")
    return parser.parse_args()


def validate(args: argparse.Namespace) -> None:
    if not (args.subject or args.sender or args.from_date or args.to_date):
        print(
            "ERROR: at least one filter required (--subject, --sender, --from-date, --to-date). "
            "Refusing to run with no filter — that would empty the inbox."
        )
        sys.exit(1)

    if args.max_moves < 1:
        print("ERROR: --max-moves must be >= 1")
        sys.exit(1)

    if args.max_moves > HARD_CAP:
        print(
            f"ERROR: --max-moves {args.max_moves} exceeds hard cap of {HARD_CAP}. "
            f"Refusing — break the operation into multiple calls."
        )
        sys.exit(1)

    for label, value in (("--from-date", args.from_date), ("--to-date", args.to_date)):
        if value is None:
            continue
        parts = value.split("-")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            print(f"ERROR: {label} must be YYYY-MM-DD; got {value!r}")
            sys.exit(1)


def applescript_date_literal(date_str: str) -> str:
    """Convert YYYY-MM-DD into an AppleScript date constructor block.

    Returns a snippet like: `(my mkDate(2025, 5, 1))` — assumes mkDate handler
    is included in the script.
    """
    y, m, d = date_str.split("-")
    return f"(my mkDate({int(y)}, {int(m)}, {int(d)}))"


def build_filter_clauses(args: argparse.Namespace) -> str:
    """Build AppleScript boolean clauses applied per-message inside the loop."""
    clauses = []
    if args.subject:
        safe = escape_applescript(args.subject)
        clauses.append(f'(subject of aMessage contains "{safe}")')
    if args.sender:
        safe = escape_applescript(args.sender)
        clauses.append(f'(sender of aMessage contains "{safe}")')
    if args.from_date:
        clauses.append(f"(date received of aMessage >= {applescript_date_literal(args.from_date)})")
    if args.to_date:
        clauses.append(f"(date received of aMessage <= {applescript_date_literal(args.to_date)})")
    return " and ".join(clauses)


def main() -> None:
    args = parse_args()
    validate(args)

    safe_account = escape_applescript(args.account)
    safe_target = escape_applescript(args.to_mailbox)
    filter_expr = build_filter_clauses(args)
    dry = "true" if args.dry_run else "false"

    script = f'''
on mkDate(y, m, d)
    set theDate to current date
    set year of theDate to y
    set month of theDate to m
    set day of theDate to d
    set time of theDate to 0
    return theDate
end mkDate

tell application "Mail"
    set targetAccount to account "{safe_account}"
{inbox_mailbox_block("inboxMailbox", "targetAccount")}

    try
        set destMailbox to mailbox "{safe_target}" of targetAccount
    on error
        return "ERROR: destination mailbox \\"{safe_target}\\" not found in account \\"{safe_account}\\""
    end try

    set inboxMessages to (every message of inboxMailbox)
    set matchedSubjects to {{}}
    set matchedDates to {{}}
    set matchedRefs to {{}}
    set moveCount to 0
    set maxMoves to {args.max_moves}
    set isDryRun to {dry}

    repeat with aMessage in inboxMessages
        if moveCount >= maxMoves then exit repeat
        try
            if {filter_expr} then
                set end of matchedSubjects to (subject of aMessage)
                set end of matchedDates to ((date received of aMessage) as string)
                set end of matchedRefs to aMessage
                set moveCount to moveCount + 1
            end if
        end try
    end repeat

    set output to ""
    if isDryRun then
        set output to "DRY RUN: would move " & moveCount & " to {safe_target}:"
        repeat with i from 1 to (count of matchedSubjects)
            set output to output & linefeed & "  - [" & (item i of matchedDates) & "] " & (item i of matchedSubjects)
        end repeat
    else
        repeat with msgRef in matchedRefs
            try
                move msgRef to destMailbox
            end try
        end repeat
        set output to "Moved " & moveCount & " messages to {safe_target}"
        if moveCount > 0 then
            repeat with i from 1 to (count of matchedSubjects)
                set output to output & linefeed & "  - [" & (item i of matchedDates) & "] " & (item i of matchedSubjects)
            end repeat
        end if
    end if

    return output
end tell
'''

    out = run_applescript(script, timeout=120)
    if out.startswith("ERROR:"):
        print(out)
        sys.exit(1)
    print(out)


if __name__ == "__main__":
    main()
