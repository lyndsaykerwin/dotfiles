#!/usr/bin/env python3
"""
flag_email.py

Toggle the flagged status of an INBOX message in Apple Mail. Default action
is to FLAG; use --unflag to remove the flag.

Safety: refuses if zero matches, refuses if 5+ matches (be more specific).

Usage:
    python3 flag_email.py <account> <subject_keyword> [--unflag] [--dry-run]

Examples:
    python3 flag_email.py "Exchange" "smoke test"
    python3 flag_email.py "Exchange" "smoke test" --unflag
    python3 flag_email.py "Exchange" "Project Discussion" --dry-run
"""

import argparse
import sys

from common import escape_applescript, inbox_mailbox_block, run_applescript


MAX_MATCHES = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("account", help="Apple Mail account name")
    parser.add_argument("subject_keyword", help="Subject contains KEY (case-sensitive)")
    parser.add_argument("--unflag", action="store_true", help="Remove flag instead of adding")
    parser.add_argument("--dry-run", action="store_true", help="Print matches without changing flags")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    safe_account = escape_applescript(args.account)
    safe_keyword = escape_applescript(args.subject_keyword)
    new_flag_value = "false" if args.unflag else "true"
    action_label = "Unflagged" if args.unflag else "Flagged"
    dry_label = "would unflag" if args.unflag else "would flag"
    dry = "true" if args.dry_run else "false"

    script = f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{inbox_mailbox_block("inboxMailbox", "targetAccount")}

    set matchedSubjects to {{}}
    set matchedDates to {{}}
    set matchedRefs to {{}}
    set isDryRun to {dry}

    repeat with aMessage in (every message of inboxMailbox)
        try
            if subject of aMessage contains "{safe_keyword}" then
                set end of matchedSubjects to (subject of aMessage)
                set end of matchedDates to ((date received of aMessage) as string)
                set end of matchedRefs to aMessage
            end if
        end try
    end repeat

    set matchCount to count of matchedSubjects

    if matchCount is 0 then
        return "ERROR: no messages in INBOX of \\"{safe_account}\\" with subject containing \\"{safe_keyword}\\""
    end if

    if matchCount >= {MAX_MATCHES} then
        return "ERROR: " & matchCount & " messages match — too broad (limit < {MAX_MATCHES}). Use a more specific keyword."
    end if

    set output to ""
    if isDryRun then
        set output to "DRY RUN: {dry_label} " & matchCount & " message(s):"
        repeat with i from 1 to matchCount
            set output to output & linefeed & "  - [" & (item i of matchedDates) & "] " & (item i of matchedSubjects)
        end repeat
    else
        repeat with msgRef in matchedRefs
            try
                set flagged status of msgRef to {new_flag_value}
            end try
        end repeat
        set output to "{action_label} " & matchCount & " message(s):"
        repeat with i from 1 to matchCount
            set output to output & linefeed & "  - [" & (item i of matchedDates) & "] " & (item i of matchedSubjects)
        end repeat
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
