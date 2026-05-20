#!/usr/bin/env python3
"""
draft_reply.py

Create a threaded reply DRAFT (not sent) in Apple Mail. The draft is saved
in the Drafts folder of the specified account with full threading metadata
preserved (In-Reply-To, References, "Re:" subject prefix, recipient), Mail's
auto-quoted prior context with HTML formatting intact, and the user's
signature. The reply text is inserted at the top of the body.

Requires:
    macOS with Mail.app configured for the target account
    Accessibility permission granted to the controlling app (one-time setup
    in System Settings -> Privacy & Security -> Accessibility) so System
    Events can keystroke Cmd+V into the compose window.

Usage:
    python3 draft_reply.py <account> <reply_text> [<subject_keyword>]
    python3 draft_reply.py --print-profile-context [--profile PATH]
    python3 draft_reply.py --triage-record '<json>' <account> <reply_text> \
                                                       [<subject_keyword>]

Modes:
    2 args (account, reply_text):
        Reply to the most recent message in the account's INBOX.
    3 args (account, reply_text, subject_keyword):
        Reply to the first INBOX message whose subject contains the keyword.

CC recipients:
    --cc EMAIL[,EMAIL...]
        Add one or more CC recipients to the reply. May be passed multiple
        times, and/or as a comma-separated list. Original To/From threading
        (set by Mail's native reply) is untouched — these are added on top.
        Example: --cc "alice@example.com,bob@example.com"

Profile-aware drafting (Phase 2 of the toolkit):
    --print-profile-context
        Print the user's voice / identity / banned-phrases / reply-philosophy
        sections (loaded from ~/.claude/preferences/apple-mail/profile.md
        unless --profile / $APPLE_MAIL_PROFILE override) to stdout, then
        exit. Use this BEFORE composing reply_text so the drafting agent
        can read the user's voice rules.
    --profile PATH
        Override the default profile-discovery path.
    --triage-record '<json>'
        Optional JSON object representing the inbound triage record that
        prompted this reply. Internal fields (priority, _meta, _profile) are
        stripped via strip_internal_fields() before any logging — the
        priority-never-leaks guardrail enforced in code, not docs.

Examples:
    python3 draft_reply.py "Exchange" "Friday works for me. Thanks."
    python3 draft_reply.py "Exchange" "Sounds good." "Project Discussion"
    python3 draft_reply.py --print-profile-context
"""

import argparse
import json as _json
import sys as _sys

from common import (
    clipboard_paste_block,
    clipboard_restore_block,
    escape_applescript,
    inbox_mailbox_block,
    load_profile,
    load_workspace_voice_overlay,
    require_args,
    run_applescript,
    strip_internal_fields,
)


USAGE = __doc__


# Profile section keys we care about for drafting voice. The parser normalizes
# headers to lowercase_with_underscores stripped of non-alphanumerics, so the
# header "## Voice — the load-bearing rules" becomes
# "voice_the_loadbearing_rules". We accept a short list of acceptable name
# variants per section to tolerate header drift across user profiles.
_DRAFTING_SECTION_ALIASES = {
    "identity": ("identity",),
    "voice": ("voice", "voice_the_loadbearing_rules"),
    "reply_philosophy": ("reply_philosophy",
                         "reply_philosophy_think_through_to_outcome"),
    "banned_phrases": ("banned_phrases",),
    "the_bar": ("the_bar", "the_bar_drafts_should_be_sendable_asis"),
}


def _pick_section(profile, aliases):
    """Return the first matching section body from profile, or '' if none."""
    for alias in aliases:
        if alias in profile and profile[alias]:
            return profile[alias]
    # Last-resort prefix match
    for key, value in profile.items():
        if key.startswith("_"):
            continue
        for alias in aliases:
            if key.startswith(alias):
                return value
    return ""


def format_profile_context(profile, triage_record=None, workspace_overlay=None):
    """Build a plain-text block of voice/identity/reply-philosophy rules to
    prepend to a drafting prompt. Returns '' if no profile AND no workspace
    overlay are loaded.

    Composition: personal profile (the floor — workspace-agnostic rules from
    ~/.claude/preferences/apple-mail/profile.md) followed by the workspace
    voice overlay (additive — workspace-specific rules from the file named in
    apple-mail-config.json's `voice_file` field). If the two conflict on a
    given workspace's drafts, the workspace overlay wins.

    If `triage_record` is a dict, it is first run through
    `strip_internal_fields` (priority guardrail) and then surfaced as the
    "Inbound message context" subsection.
    """
    if not profile and not workspace_overlay:
        return ""
    lines = []

    if profile:
        lines.append("=== USER PROFILE CONTEXT (voice rules — apply to draft) ===")
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

    if workspace_overlay and workspace_overlay.get("raw"):
        lines.append("=== WORKSPACE VOICE OVERLAY (additive — wins on conflict for this workspace) ===")
        lines.append(f"Source: {workspace_overlay.get('path', '')}")
        lines.append("")
        lines.append(workspace_overlay["raw"].strip())
        lines.append("")

    if triage_record is not None:
        # Guardrail: priority / _meta / _profile must never reach the draft.
        clean = strip_internal_fields(triage_record)
        lines.append("--- INBOUND MESSAGE CONTEXT (sanitized) ---")
        lines.append(_json.dumps(clean, ensure_ascii=False, indent=2))
        lines.append("")

    lines.append("=== END USER PROFILE CONTEXT ===")
    return "\n".join(lines)


def main() -> None:
    # Pre-parse: handle the profile-only modes BEFORE require_args, because
    # they take fewer positional args than the standard draft path.
    raw_argv = _sys.argv[1:]

    if "--print-profile-context" in raw_argv:
        ap = argparse.ArgumentParser(add_help=False)
        ap.add_argument("--print-profile-context", action="store_true")
        ap.add_argument("--profile", default=None)
        # Strip these flags so the rest of the world ignores them
        parsed, _ = ap.parse_known_args(raw_argv)
        profile = load_profile(parsed.profile)
        workspace_overlay = load_workspace_voice_overlay()
        if not profile and not workspace_overlay:
            print("(no profile or workspace voice overlay found — drafting will use generic voice)",
                  file=_sys.stderr)
            return
        print(format_profile_context(profile, workspace_overlay=workspace_overlay))
        return

    # Parse and strip the optional --profile / --triage-record / --cc flags.
    profile_path = None
    triage_record = None
    cc_addresses = []
    positional = []
    i = 0
    while i < len(raw_argv):
        tok = raw_argv[i]
        if tok == "--profile" and i + 1 < len(raw_argv):
            profile_path = raw_argv[i + 1]
            i += 2
            continue
        if tok.startswith("--profile="):
            profile_path = tok.split("=", 1)[1]
            i += 1
            continue
        if tok == "--triage-record" and i + 1 < len(raw_argv):
            try:
                triage_record = _json.loads(raw_argv[i + 1])
            except _json.JSONDecodeError as e:
                print(f"ERROR: --triage-record is not valid JSON: {e}",
                      file=_sys.stderr)
                _sys.exit(1)
            i += 2
            continue
        if tok.startswith("--triage-record="):
            try:
                triage_record = _json.loads(tok.split("=", 1)[1])
            except _json.JSONDecodeError as e:
                print(f"ERROR: --triage-record is not valid JSON: {e}",
                      file=_sys.stderr)
                _sys.exit(1)
            i += 1
            continue
        if tok == "--cc" and i + 1 < len(raw_argv):
            cc_addresses.extend(
                a.strip() for a in raw_argv[i + 1].split(",") if a.strip()
            )
            i += 2
            continue
        if tok.startswith("--cc="):
            cc_addresses.extend(
                a.strip() for a in tok.split("=", 1)[1].split(",") if a.strip()
            )
            i += 1
            continue
        positional.append(tok)
        i += 1

    if len(positional) < 2 or len(positional) > 3:
        print(USAGE)
        _sys.exit(1)

    account = positional[0]
    reply_text = positional[1]
    subject_keyword = positional[2] if len(positional) == 3 else None

    # Load personal profile + workspace voice overlay (if configured) and
    # surface the composed voice context on stderr so the parent Claude Code
    # session can read it. (stderr keeps the AppleScript OK-line on stdout
    # intact for any caller that reads stdout.)
    profile = load_profile(profile_path)
    workspace_overlay = load_workspace_voice_overlay()
    if profile or workspace_overlay:
        ctx = format_profile_context(
            profile,
            triage_record=triage_record,
            workspace_overlay=workspace_overlay,
        )
        if ctx:
            print(ctx, file=_sys.stderr)

    safe_account = escape_applescript(account)

    # Build the optional CC block. Each address becomes a new cc recipient on
    # the reply message. Empty list -> empty string (no AppleScript emitted).
    if cc_addresses:
        cc_lines = "\n".join(
            f'    make new cc recipient at end of cc recipients of replyMessage '
            f'with properties {{address:"{escape_applescript(addr)}"}}'
            for addr in cc_addresses
        )
        cc_block = cc_lines + "\n"
    else:
        cc_block = ""

    if subject_keyword is None:
        find_message_script = f'''
    set inboxMessages to (every message of inboxMailbox)
    if (count of inboxMessages) is 0 then
        return "ERROR: INBOX is empty for account '{safe_account}'"
    end if
    set foundMessage to missing value
    set newestDate to missing value
    repeat with aMessage in inboxMessages
        try
            set msgDate to date received of aMessage
            if newestDate is missing value or msgDate > newestDate then
                set newestDate to msgDate
                set foundMessage to aMessage
            end if
        end try
    end repeat
'''
    else:
        safe_keyword = escape_applescript(subject_keyword)
        find_message_script = f'''
    set foundMessage to missing value
    repeat with aMessage in (every message of inboxMailbox)
        try
            if subject of aMessage contains "{safe_keyword}" then
                set foundMessage to aMessage
                exit repeat
            end if
        end try
    end repeat
    if foundMessage is missing value then
        return "ERROR: No message in INBOX of '{safe_account}' with subject containing '{safe_keyword}'"
    end if
'''

    script = f'''
use framework "Foundation"
use framework "AppKit"
use scripting additions

{clipboard_paste_block(reply_text)}

tell application "Mail"
    set targetAccount to account "{safe_account}"
{inbox_mailbox_block("inboxMailbox", "targetAccount")}

{find_message_script}

    set originalSubject to subject of foundMessage
    set originalSender to sender of foundMessage

    -- Native reply: sets In-Reply-To, References, "Re:" subject, auto-quoted body, signature
    set replyMessage to reply foundMessage with opening window
{cc_block}    delay 2.0

    -- Bring the new compose window to absolute front so the paste targets it
    activate
    delay 0.5
    try
        set newComposeWindow to (first window whose name contains originalSubject)
        set index of newComposeWindow to 1
    end try
    delay 0.8
end tell

-- Paste reply text at the cursor (top of body, above auto-quoted block)
tell application "System Events"
    tell process "Mail"
        set frontmost to true
        delay 0.3
        keystroke "v" using command down
        delay 0.3
        keystroke return
        keystroke return
    end tell
end tell

delay 0.5

tell application "Mail"
    save replyMessage
end tell

{clipboard_restore_block()}

return "OK: replied to \\"" & originalSubject & "\\" from " & originalSender & " -- draft saved"
'''

    print(run_applescript(script))


if __name__ == "__main__":
    main()
