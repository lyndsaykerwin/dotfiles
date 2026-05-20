#!/usr/bin/env python3
"""
compose_new.py

Compose a FRESH (non-reply) outgoing email DRAFT in Apple Mail. The draft is
saved in the Drafts folder of the specified account and the compose window is
left open so the user can review/edit before sending manually. This script
NEVER sends — it only creates a draft.

Requires:
    macOS with Mail.app configured for the target account
    Accessibility permission granted to the controlling app (one-time setup
    in System Settings -> Privacy & Security -> Accessibility) so System
    Events can keystroke Cmd+V into the compose window.

Usage:
    python3 compose_new.py <account> <to_addr> <subject> <body> [--cc CC] [--bcc BCC]

Notes:
    - <to_addr> is a single email address (string).
    - <subject> is the email subject line.
    - <body> is the plain-text body. Newlines (`\\n`) are preserved through
      the clipboard paste.
    - --cc and --bcc each accept a comma-separated list of email addresses.
    - The "from" address is automatically set to the first email of the named
      account.
    - Use this for a brand-new outgoing email. For replies to an existing
      message, use draft_reply.py instead (it preserves threading).

Examples:
    python3 compose_new.py "Exchange" "ben@example.com" "Quick question" \\
        "Hi Ben,\\n\\nDo you have time Thursday for a quick call?\\n\\nThanks"

    python3 compose_new.py "Exchange" "sarah@example.com" "Intro" \\
        "Hi Sarah, ..." --cc "john@example.com,jane@example.com"
"""

from __future__ import annotations

import argparse
import json as _json
import sys as _sys

from common import (
    clipboard_paste_block,
    clipboard_restore_block,
    escape_applescript,
    load_profile,
    run_applescript,
    strip_internal_fields,
)


# Same drafting-section aliases used by draft_reply — kept duplicated so each
# skill is self-contained (matches the common.py duplication trade-off).
_DRAFTING_SECTION_ALIASES = {
    "identity": ("identity",),
    "voice": ("voice", "voice_the_loadbearing_rules"),
    "reply_philosophy": ("reply_philosophy",
                         "reply_philosophy_think_through_to_outcome"),
    "banned_phrases": ("banned_phrases",),
    "the_bar": ("the_bar", "the_bar_drafts_should_be_sendable_asis"),
}


def _pick_section(profile, aliases):
    for alias in aliases:
        if alias in profile and profile[alias]:
            return profile[alias]
    for key, value in profile.items():
        if key.startswith("_"):
            continue
        for alias in aliases:
            if key.startswith(alias):
                return value
    return ""


def format_profile_context(profile, triage_record=None):
    """Plain-text voice/identity/reply-philosophy block for the drafting prompt.

    Returns '' if no profile is loaded. If triage_record is provided it is
    stripped via strip_internal_fields() first (priority guardrail).
    """
    if not profile:
        return ""
    lines = ["=== USER PROFILE CONTEXT (voice rules — apply to draft) ==="]
    title = profile.get("_title")
    if title:
        lines.append(f"Profile: {title}")
    lines.append("")
    for label, aliases in _DRAFTING_SECTION_ALIASES.items():
        body = _pick_section(profile, aliases)
        if not body:
            continue
        lines.append(f"--- {label.upper()} ---")
        lines.append(body.strip())
        lines.append("")
    if triage_record is not None:
        clean = strip_internal_fields(triage_record)
        lines.append("--- INBOUND MESSAGE CONTEXT (sanitized) ---")
        lines.append(_json.dumps(clean, ensure_ascii=False, indent=2))
        lines.append("")
    lines.append("=== END USER PROFILE CONTEXT ===")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compose a fresh outgoing email DRAFT in Apple Mail.",
        usage=(
            "python3 compose_new.py <account> <to_addr> <subject> <body> "
            "[--cc CC] [--bcc BCC] [--profile PATH] [--triage-record JSON]\n"
            "       python3 compose_new.py --print-profile-context "
            "[--profile PATH]"
        ),
    )
    # All positional args are nargs="?" so --print-profile-context can be used
    # alone. The validation happens in main().
    parser.add_argument("account", nargs="?", help="Mail account name, e.g. 'Exchange'")
    parser.add_argument("to_addr", nargs="?", help="To recipient (single email address)")
    parser.add_argument("subject", nargs="?", help="Subject line")
    parser.add_argument("body", nargs="?", help="Plain-text body (\\n for newlines)")
    parser.add_argument(
        "--cc",
        default=None,
        help="Cc addresses, comma-separated (optional)",
    )
    parser.add_argument(
        "--bcc",
        default=None,
        help="Bcc addresses, comma-separated (optional)",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Path to the user profile .md file. Defaults to "
             "$APPLE_MAIL_PROFILE or "
             "~/.claude/preferences/apple-mail/profile.md. "
             "If no profile exists, runs in fully-generic mode.",
    )
    parser.add_argument(
        "--print-profile-context",
        action="store_true",
        help="Print the user's voice/identity/banned-phrases/reply-philosophy "
             "sections from the loaded profile to stdout, then exit. Use "
             "BEFORE composing the body so the drafting agent can read the "
             "user's voice rules.",
    )
    parser.add_argument(
        "--triage-record",
        default=None,
        help="Optional JSON object representing the inbound triage record "
             "that prompted this draft. Internal fields (priority, _meta, "
             "_profile) are stripped via strip_internal_fields() before any "
             "logging — the priority-never-leaks guardrail.",
    )
    return parser.parse_args()


def split_addresses(value: str | None) -> list[str]:
    """Split a comma-separated address string into a clean list."""
    if not value:
        return []
    return [a.strip() for a in value.split(",") if a.strip()]


def recipient_block(kind: str, addresses: list[str]) -> str:
    """Build AppleScript that adds recipients of a given kind to the message.

    kind: "to", "cc", or "bcc" (matches AppleScript's recipient class names).
    """
    if not addresses:
        return ""
    lines = []
    for addr in addresses:
        safe_addr = escape_applescript(addr)
        lines.append(
            f'        make new {kind} recipient at end of {kind} recipients '
            f'of newMessage with properties {{address:"{safe_addr}"}}'
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()

    # Handle --print-profile-context: print profile then exit.
    if args.print_profile_context:
        profile = load_profile(args.profile)
        if not profile:
            print("(no profile found — drafting will use generic voice)",
                  file=_sys.stderr)
            return
        print(format_profile_context(profile))
        return

    # Otherwise the four positional args are required.
    missing = [n for n, v in (
        ("account", args.account),
        ("to_addr", args.to_addr),
        ("subject", args.subject),
        ("body", args.body),
    ) if v is None]
    if missing:
        print(f"ERROR: missing required argument(s): {', '.join(missing)}",
              file=_sys.stderr)
        print(__doc__)
        _sys.exit(1)

    # Optional triage record — strip internal fields immediately.
    triage_record = None
    if args.triage_record:
        try:
            triage_record = _json.loads(args.triage_record)
        except _json.JSONDecodeError as e:
            print(f"ERROR: --triage-record is not valid JSON: {e}",
                  file=_sys.stderr)
            _sys.exit(1)

    # Load profile (empty dict if none) and surface its voice context on
    # stderr so the parent Claude Code session can read it. stdout stays
    # reserved for the AppleScript OK-line.
    profile = load_profile(args.profile)
    if profile:
        ctx = format_profile_context(profile, triage_record=triage_record)
        if ctx:
            print(ctx, file=_sys.stderr)

    account = args.account
    to_addr = args.to_addr
    subject = args.subject
    body = args.body.replace("\\n", "\n")  # allow literal \n on the CLI
    cc_list = split_addresses(args.cc)
    bcc_list = split_addresses(args.bcc)

    safe_account = escape_applescript(account)
    safe_subject = escape_applescript(subject)
    safe_to = escape_applescript(to_addr)

    to_block = (
        f'        make new to recipient at end of to recipients '
        f'of newMessage with properties {{address:"{safe_to}"}}'
    )
    cc_block = recipient_block("cc", cc_list)
    bcc_block = recipient_block("bcc", bcc_list)

    # Resolve the "from" address as the first email of the named account so
    # the compose window opens with the correct sender pre-selected.
    sender_block = f'''
    set acctEmails to email addresses of targetAccount
    if (count of acctEmails) is 0 then
        return "ERROR: account '{safe_account}' has no email addresses configured"
    end if
    set fromAddr to item 1 of acctEmails'''

    script = f'''
use framework "Foundation"
use framework "AppKit"
use scripting additions

{clipboard_paste_block(body)}

tell application "Mail"
    set targetAccount to account "{safe_account}"
{sender_block}

    set newMessage to make new outgoing message with properties {{subject:"{safe_subject}", visible:true, sender:fromAddr}}

{to_block}
{cc_block}
{bcc_block}

    delay 0.8
    activate
    delay 0.3
    try
        set composeWindow to first window of newMessage
        set index of composeWindow to 1
    on error
        try
            set composeWindow to (first window whose name contains "{safe_subject}")
            set index of composeWindow to 1
        end try
    end try
    delay 0.6
end tell

-- Paste the body via clipboard. We first focus the body's AXWebArea
-- explicitly because in a fresh compose window the keyboard focus is in
-- the To field — pasting straight away clobbers the recipient. The body
-- is an AXWebArea ("message body") inside the compose window's nested
-- group/group/scroll-area; setting its `focused` property is the most
-- reliable way to land the paste in the right place regardless of how
-- many header fields (From / To / Cc / Bcc / Subject) are visible.
tell application "System Events"
    tell process "Mail"
        set frontmost to true
        delay 0.3
        try
            set composeWin to (first window whose name contains "{safe_subject}")
            set bodyArea to UI element 1 of scroll area 1 of group 1 of group 1 of composeWin
            set focused of bodyArea to true
            delay 0.2
        on error
            -- Fall through; paste may go to a header field, but we tried.
        end try
        keystroke "v" using command down
        delay 0.3
    end tell
end tell

delay 0.5

tell application "Mail"
    save newMessage
end tell

{clipboard_restore_block()}

return "OK: draft composed to " & "{safe_to}" & " -- subject \\"" & "{safe_subject}" & "\\" -- saved to Drafts"
'''

    print(run_applescript(script))


if __name__ == "__main__":
    main()
