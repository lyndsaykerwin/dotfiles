#!/usr/bin/env python3
"""
save_attachment.py

Save an attachment from a single email in an Apple Mail account to disk.
Finds the first message in the chosen mailbox whose subject contains the
supplied keyword, then writes the chosen attachment to <save-to>.

Usage:
    python3 save_attachment.py <account> <subject_keyword>
        [--mailbox NAME] [--save-to PATH] [--name FILENAME]

Args:
    <account>          Mail account name (e.g. "Exchange").
    <subject_keyword>  Case-sensitive substring of the email's subject.
    --mailbox NAME     Mailbox to search. Default Inbox.
    --save-to PATH     Directory to save into. Default ~/Desktop.
                       Must resolve to a path under the user's home directory
                       (~). The script refuses paths outside ~ to prevent a
                       crafted subject keyword from steering writes elsewhere.
    --name FILENAME    Required if the email has multiple attachments. Picks
                       the attachment whose `name` matches FILENAME exactly.
                       If omitted on a single-attachment email, that one is
                       used and the saved file keeps its original name.

Behavior:
    Refuses if 0 or 2+ messages match the keyword.
    Refuses if email has multiple attachments and --name is not given.
    NEVER overwrites an existing file. If <save-to>/<name> already exists,
    saves as <stem>_1<ext>, then _2, etc., until a free name is found.

Output:
    Saved 'NAME' to /full/path/here

Examples:
    python3 save_attachment.py "Exchange" "Q3 deck"
    python3 save_attachment.py "Exchange" "Q3 deck" --save-to /tmp
    python3 save_attachment.py "Exchange" "diligence" --name "model.xlsx"
"""

from __future__ import annotations

import argparse
import os
import sys

from common import (
    escape_applescript,
    inbox_mailbox_block,
    run_applescript,
)


USAGE = __doc__


def build_lookup_script(account: str, keyword: str, mailbox: str | None) -> str:
    """Script that locates the matching message and lists its attachment names.

    Output:
        line 1: "MATCH_COUNT: <0|1|2>"
        line 2: "SUBJECT: <subject>"          (only if MATCH_COUNT == 1)
        line 3+: "ATT|<name>"                 (one per attachment)
    """
    safe_account = escape_applescript(account)
    safe_keyword = escape_applescript(keyword)

    if mailbox is None:
        mailbox_block = inbox_mailbox_block("targetMailbox", "targetAccount")
    else:
        safe_mailbox = escape_applescript(mailbox)
        mailbox_block = (
            f'    set targetMailbox to mailbox "{safe_mailbox}" of targetAccount'
        )

    return f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{mailbox_block}

    set matchedMessages to {{}}
    repeat with aMessage in (every message of targetMailbox)
        try
            if subject of aMessage contains "{safe_keyword}" then
                set end of matchedMessages to aMessage
                if (count of matchedMessages) > 1 then exit repeat
            end if
        end try
    end repeat

    set matchCount to count of matchedMessages
    if matchCount is 0 then
        return "MATCH_COUNT: 0"
    end if
    if matchCount > 1 then
        return "MATCH_COUNT: 2"
    end if

    set foundMessage to item 1 of matchedMessages
    set theSubject to subject of foundMessage

    set outputLines to {{}}
    set end of outputLines to "MATCH_COUNT: 1"
    set end of outputLines to "SUBJECT: " & theSubject

    set atts to mail attachments of foundMessage
    repeat with anAtt in atts
        try
            set attName to name of anAtt
        on error
            set attName to "(unnamed)"
        end try
        set end of outputLines to "ATT|" & attName
    end repeat

    set AppleScript's text item delimiters to linefeed
    set joined to outputLines as text
    set AppleScript's text item delimiters to ""
    return joined
end tell
'''


def build_save_script(
    account: str,
    keyword: str,
    mailbox: str | None,
    attachment_name: str,
    full_save_path: str,
) -> str:
    """Script that re-finds the message and saves the named attachment to <full_save_path>.

    We re-find the message rather than passing a reference because AppleScript
    references don't survive between separate `osascript` invocations.

    Output: "OK" on success, or an "ERROR: ..." line.
    """
    safe_account = escape_applescript(account)
    safe_keyword = escape_applescript(keyword)
    safe_att_name = escape_applescript(attachment_name)
    safe_path = escape_applescript(full_save_path)

    if mailbox is None:
        mailbox_block = inbox_mailbox_block("targetMailbox", "targetAccount")
    else:
        safe_mailbox = escape_applescript(mailbox)
        mailbox_block = (
            f'    set targetMailbox to mailbox "{safe_mailbox}" of targetAccount'
        )

    return f'''
tell application "Mail"
    set targetAccount to account "{safe_account}"
{mailbox_block}

    set foundMessage to missing value
    repeat with aMessage in (every message of targetMailbox)
        try
            if subject of aMessage contains "{safe_keyword}" then
                set foundMessage to aMessage
                exit repeat
            end if
        end try
    end repeat
    if foundMessage is missing value then
        return "ERROR: message no longer found"
    end if

    set chosenAtt to missing value
    repeat with anAtt in (mail attachments of foundMessage)
        try
            if (name of anAtt) is "{safe_att_name}" then
                set chosenAtt to anAtt
                exit repeat
            end if
        end try
    end repeat
    if chosenAtt is missing value then
        return "ERROR: attachment named '{safe_att_name}' not found on message"
    end if

    try
        save chosenAtt in POSIX file "{safe_path}"
    on error errMsg
        return "ERROR: " & errMsg
    end try

    return "OK"
end tell
'''


def parse_lookup_output(out: str) -> tuple[str, str, list[str]]:
    """Return (match_status, subject, attachment_names).

    match_status is one of "0", "1", "2".
    """
    lines = out.splitlines()
    if not lines:
        return ("", "", [])

    header = lines[0].strip()
    if header == "MATCH_COUNT: 0":
        return ("0", "", [])
    if header == "MATCH_COUNT: 2":
        return ("2", "", [])
    if header != "MATCH_COUNT: 1":
        return ("", "", [])

    subject_line = lines[1] if len(lines) > 1 else "SUBJECT: "
    subject = (
        subject_line[len("SUBJECT: "):]
        if subject_line.startswith("SUBJECT: ")
        else subject_line
    )

    names: list[str] = []
    for raw in lines[2:]:
        if raw.startswith("ATT|"):
            names.append(raw[len("ATT|"):])
    return ("1", subject, names)


def resolve_unique_path(directory: str, filename: str) -> str:
    """Pick a path inside `directory` that doesn't collide with anything on disk.

    If <directory>/<filename> is free, returns it. Otherwise tries
    <stem>_1<ext>, <stem>_2<ext>, etc., up to _999 to avoid pathological loops.
    """
    candidate = os.path.join(directory, filename)
    if not os.path.exists(candidate):
        return candidate

    stem, ext = os.path.splitext(filename)
    for i in range(1, 1000):
        alt = os.path.join(directory, f"{stem}_{i}{ext}")
        if not os.path.exists(alt):
            return alt
    raise SystemExit(
        f"too many existing files with prefix '{stem}_' in {directory}"
    )


def main() -> None:
    if len(sys.argv) == 1:
        print(USAGE)
        sys.exit(1)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("account")
    parser.add_argument("subject_keyword")
    parser.add_argument("--mailbox", default=None)
    parser.add_argument("--save-to", default="~/Desktop")
    parser.add_argument("--name", default=None)

    try:
        args = parser.parse_args()
    except SystemExit:
        print(USAGE)
        sys.exit(1)

    # Resolve and validate save-to path: must live under the user's home dir.
    home = os.path.realpath(os.path.expanduser("~"))
    save_to_expanded = os.path.expanduser(args.save_to)
    save_to_abs = os.path.realpath(os.path.abspath(save_to_expanded))

    # /tmp is allowed for testing (caller may symlink, but on macOS /tmp is
    # /private/tmp — explicitly permitted).
    tmp_real = os.path.realpath("/tmp")
    is_under_home = (
        save_to_abs == home or save_to_abs.startswith(home + os.sep)
    )
    is_under_tmp = (
        save_to_abs == tmp_real or save_to_abs.startswith(tmp_real + os.sep)
    )
    if not (is_under_home or is_under_tmp):
        print(
            f"ERROR: --save-to must resolve to a path under your home directory "
            f"({home}) or /tmp; got '{save_to_abs}'"
        )
        sys.exit(1)

    if not os.path.isdir(save_to_abs):
        print(f"ERROR: --save-to directory does not exist: {save_to_abs}")
        sys.exit(1)

    # Look up the email and its attachments.
    try:
        lookup_out = run_applescript(
            build_lookup_script(args.account, args.subject_keyword, args.mailbox),
            timeout=180,
        )
    except SystemExit as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    status, subject, att_names = parse_lookup_output(lookup_out)
    mailbox_label = args.mailbox if args.mailbox else "Inbox"

    if status == "0":
        print(
            f"ERROR: No message in {mailbox_label} of '{args.account}' "
            f"with subject containing '{args.subject_keyword}'"
        )
        sys.exit(1)
    if status == "2":
        print(
            f"ERROR: Multiple messages in {mailbox_label} of '{args.account}' "
            f"with subject containing '{args.subject_keyword}'. "
            f"Use a more specific keyword."
        )
        sys.exit(1)
    if status != "1":
        print(f"ERROR: unexpected response from Mail: {lookup_out!r}")
        sys.exit(1)

    if not att_names:
        print(f"ERROR: Email '{subject}' has no attachments")
        sys.exit(1)

    # Pick which attachment.
    if args.name is None:
        if len(att_names) > 1:
            print(
                f"ERROR: Email has {len(att_names)} attachments; specify "
                f"--name to choose. Run list_attachments.py first."
            )
            sys.exit(1)
        chosen_name = att_names[0]
    else:
        if args.name not in att_names:
            print(
                f"ERROR: No attachment named '{args.name}' on email '{subject}'. "
                f"Available: {', '.join(att_names)}"
            )
            sys.exit(1)
        chosen_name = args.name

    # Resolve a non-colliding path. Attachment is saved using its original
    # filename; if that filename is in use, suffix with _1, _2, ...
    final_path = resolve_unique_path(save_to_abs, chosen_name)

    # Final defensive check: never overwrite. resolve_unique_path guarantees
    # this, but check again right before handing the path to AppleScript.
    if os.path.exists(final_path):
        print(f"ERROR: refusing to overwrite existing file at {final_path}")
        sys.exit(1)

    try:
        save_out = run_applescript(
            build_save_script(
                args.account,
                args.subject_keyword,
                args.mailbox,
                chosen_name,
                final_path,
            ),
            timeout=180,
        )
    except SystemExit as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    if save_out.startswith("ERROR:"):
        print(save_out)
        sys.exit(1)
    if save_out.strip() != "OK":
        print(f"ERROR: unexpected save response: {save_out!r}")
        sys.exit(1)

    if not os.path.exists(final_path):
        print(
            f"ERROR: Mail reported success but file is not on disk at {final_path}"
        )
        sys.exit(1)

    print(f"Saved '{chosen_name}' to {final_path}")


if __name__ == "__main__":
    main()
