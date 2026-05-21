"""
common.py — shared helpers for the apple-mail toolkit scripts.

All scripts in this directory should import from here rather than copy-pasting
AppleScript escape, run, and clipboard logic. This prevents drift across the
script set as new tools are added.

Public surface:
    escape_applescript(value)        -> AppleScript-safe quoted string contents
    run_applescript(script, timeout) -> str (stdout) or raises SystemExit
    inbox_mailbox_block(var, acct)   -> AppleScript snippet (INBOX/Inbox fallback)
    drafts_mailbox_block(var, acct)  -> AppleScript snippet (Drafts mailbox)
    sent_mailbox_block(var, acct)    -> AppleScript snippet (Sent / Sent Items)
    clipboard_paste_block(text)      -> AppleScript snippet that puts `text`
                                        on clipboard, with save/restore wrappers
    require_args(min, max, usage)    -> argv[1:] or exit with usage
    strip_internal_fields(record)    -> dict with triage-internal keys removed
"""

import subprocess
import sys


# ---------- core helpers --------------------------------------------------- #


def escape_applescript(value: str) -> str:
    """Escape a Python string for safe injection into an AppleScript double-quoted literal.

    Handles backslashes, double quotes, all common newline forms, tabs, and
    Unicode line/paragraph separators. Critical: the Unicode replacements
    use explicit codepoints (\\u2028, \\u2029) — pasted glyphs in source can
    look like ASCII space and clobber regular spaces.
    """
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r\n", "\\n")
        .replace("\r", "\\n")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace(" ", "\\n")
        .replace(" ", "\\n")
    )


def run_applescript(script: str, timeout: int = 60) -> str:
    """Run an AppleScript via `osascript -` and return stdout (stripped).

    Raises SystemExit with the stderr message on non-zero return code, or on
    timeout. Use a longer timeout for scripts that iterate large mailboxes.
    """
    try:
        result = subprocess.run(
            ["osascript", "-"],
            input=script.encode("utf-8"),
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise SystemExit(f"AppleScript timed out after {timeout}s")

    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit(f"AppleScript error: {err}")
    return result.stdout.decode("utf-8", errors="replace").strip()


# ---------- mailbox-resolution snippets ------------------------------------ #


def inbox_mailbox_block(var_name: str = "inboxMailbox", account_var: str = "targetAccount") -> str:
    """AppleScript snippet that binds <var_name> to the INBOX of <account_var>.

    Falls back from "INBOX" to "Inbox" because Mail localizes/varies the
    mailbox name across account types. IMAP often uses uppercase, Exchange
    sometimes uses title case.
    """
    return f'''
    try
        set {var_name} to mailbox "INBOX" of {account_var}
    on error
        set {var_name} to mailbox "Inbox" of {account_var}
    end try'''


def drafts_mailbox_block(var_name: str = "draftsMailbox", account_var: str = "targetAccount") -> str:
    """AppleScript snippet binding <var_name> to the Drafts mailbox of <account_var>."""
    return f'''
    try
        set {var_name} to mailbox "Drafts" of {account_var}
    on error
        set {var_name} to mailbox "DRAFTS" of {account_var}
    end try'''


def sent_mailbox_block(var_name: str = "sentMailbox", account_var: str = "targetAccount") -> str:
    """AppleScript snippet binding <var_name> to the Sent mailbox of <account_var>.

    Exchange uses "Sent Items"; Gmail/IMAP typically use "Sent Messages" or "Sent".
    """
    return f'''
    set {var_name} to missing value
    set sentNames to {{"Sent", "Sent Messages", "Sent Items", "SENT"}}
    repeat with sentName in sentNames
        try
            set {var_name} to mailbox sentName of {account_var}
            exit repeat
        end try
    end repeat
    if {var_name} is missing value then
        error "Could not find Sent mailbox for account"
    end if'''


# ---------- clipboard paste -------------------------------------------------#


def clipboard_paste_block(text: str) -> str:
    """Return AppleScript snippet that:
      1. Saves current clipboard string contents to `savedClip`.
      2. Replaces clipboard with `text` (escaped).
      3. (Caller is responsible for issuing the Cmd+V via System Events.)
      4. After caller pastes, AppleScript should restore via the matching
         clipboard_restore_block().

    Requires the AppleScript prologue to include:
        use framework "Foundation"
        use framework "AppKit"
        use scripting additions
    """
    safe = escape_applescript(text)
    return f'''
set pb to current application's NSPasteboard's generalPasteboard()
set savedClip to pb's stringForType:(current application's NSPasteboardTypeString)
pb's clearContents()
set pasteNSString to (current application's NSString's stringWithString:"{safe}")
pb's setString:pasteNSString forType:(current application's NSPasteboardTypeString)'''


def clipboard_restore_block() -> str:
    """Return AppleScript snippet that restores the original clipboard.

    Must be called AFTER any paste action and after `clipboard_paste_block`.
    """
    return '''
if savedClip is not missing value then
    pb's clearContents()
    pb's setString:savedClip forType:(current application's NSPasteboardTypeString)
end if'''


# ---------- argv helpers ---------------------------------------------------- #


def require_args(min_count: int, max_count: int, usage: str) -> list:
    """Validate sys.argv length and return argv[1:] or print usage and exit."""
    n = len(sys.argv) - 1
    if n < min_count or n > max_count:
        print(usage)
        sys.exit(1)
    return sys.argv[1:]


# ---------- triage-record sanitation --------------------------------------- #


def strip_internal_fields(record):
    """Remove triage-internal fields before passing a record into any drafting context.

    Triage records carry a `priority` field and may carry `_meta`, `_profile`, or other
    underscore-prefixed keys. These are FOR THE USER'S EYES ONLY — they must never appear
    in outgoing email subjects, bodies, headers, or anywhere a recipient could see them.

    This function is the code-level enforcement of that guarantee. Every drafting skill
    must call it on triage records before threading them into a drafting prompt or
    AppleScript invocation.
    """
    if not isinstance(record, dict):
        return record
    return {
        k: v for k, v in record.items()
        if k != "priority" and not k.startswith("_")
    }


# ---------- user-profile loading ------------------------------------------- #
#
# The profile is the personal layer: ~/.claude/preferences/apple-mail/profile.md
# Skills load it on every invocation (no cache) and use it to (a) classify
# inbox messages by priority and (b) shape drafting voice. If no profile
# exists, callers must behave exactly as they did before this layer was added.

import json as _json
import os as _os
import re as _re
from pathlib import Path as _Path


_DEFAULT_PROFILE_PATH = _Path.home() / ".claude" / "preferences" / "apple-mail" / "profile.md"

# Normalize "## Voice — the load-bearing rules" → "voice_the_loadbearing_rules"
# Drops non-alphanumeric (em-dashes, quotes, hyphens), collapses whitespace
# to underscores, lowercases. Keep stable so callers can hardcode lookups.
def _normalize_header(text: str) -> str:
    s = text.strip().lower()
    # Replace whitespace runs with single space first
    s = _re.sub(r"\s+", " ", s)
    # Drop anything that isn't ascii letter, digit, or space
    s = _re.sub(r"[^a-z0-9 ]+", "", s)
    # Spaces → underscores, collapse repeats
    s = _re.sub(r" +", "_", s).strip("_")
    return s


def load_profile(profile_path=None):
    """Load the user's apple-mail profile if it exists.

    Discovery order (first hit wins):
      1. Explicit profile_path argument (e.g., from --profile CLI flag)
      2. APPLE_MAIL_PROFILE env var
      3. ~/.claude/preferences/apple-mail/profile.md

    Returns a dict with keys matching the profile's top-level ## sections,
    parsed from the markdown. Section keys are normalized to
    lowercase_with_underscores (non-alphanumeric stripped). Values are the
    section body as a string.

    Also includes:
      _title          — text of the leading `# Title` line, if any
      _preamble       — anything between the title and the first `## ` header
      _raw_headers    — {normalized_key: original_header_text} so callers can
                        recover the original header text if needed
      _path           — resolved path the profile was loaded from

    Returns an empty dict if no profile is found — callers should treat this
    as "generic mode" and behave exactly as the skill did pre-profile.

    Re-read on every call. No caching. Profile updates take effect immediately.
    """
    # 1. Resolve the path
    if profile_path:
        candidate = _Path(profile_path).expanduser()
    elif _os.environ.get("APPLE_MAIL_PROFILE"):
        candidate = _Path(_os.environ["APPLE_MAIL_PROFILE"]).expanduser()
    else:
        candidate = _DEFAULT_PROFILE_PATH

    if not candidate.is_file():
        return {}

    try:
        text = candidate.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}

    return _parse_profile_markdown(text, candidate)


# ---------- workspace voice overlay ---------------------------------------- #
#
# A workspace may declare an additive voice file via apple-mail-config.json.
# Example: AscendX's config sets `"voice_file": "outreach/email_style.md"`,
# which holds firm-specific banned words + cold outbound playbook + reply
# playbooks that layer ON TOP of the personal profile.md.
#
# Compose order: profile.md (floor — workspace-agnostic personal rules) +
# workspace voice file (additive — workspace-specific firm/team rules).
# Workspace voice never replaces profile.md; it adds.


def find_apple_mail_config(start_dir=None):
    """Walk up from start_dir (or CWD) looking for apple-mail-config.json.

    Returns the absolute path string, or None if not found before reaching
    $HOME or filesystem root.
    """
    start = _Path(start_dir) if start_dir else _Path.cwd()
    current = start.resolve()
    home = _Path.home().resolve()
    while True:
        candidate = current / "apple-mail-config.json"
        if candidate.is_file():
            return str(candidate)
        if current == home or current.parent == current:
            return None
        current = current.parent


def load_workspace_voice_overlay(config_path=None):
    """Load the workspace voice overlay file, if one is configured.

    Reads apple-mail-config.json (discovery: explicit arg → APPLE_MAIL_CONFIG
    env var → walk up from CWD). If the config has a `voice_file` field, that
    file's raw markdown content is returned for the drafting skill to layer
    onto the personal profile.

    The `voice_file` value may be absolute or relative to the config file's
    directory. The file content is returned as-is — no parsing — so workspace
    voice files can use any markdown structure.

    Returns:
      {"raw": "<markdown content>", "path": "<resolved absolute path>"}
    or {} if no overlay is configured / file is missing / read fails.

    Re-read on every call. No caching. Same discipline as load_profile().
    """
    if config_path:
        cfg = _Path(config_path).expanduser()
    elif _os.environ.get("APPLE_MAIL_CONFIG"):
        cfg = _Path(_os.environ["APPLE_MAIL_CONFIG"]).expanduser()
    else:
        discovered = find_apple_mail_config()
        if not discovered:
            return {}
        cfg = _Path(discovered)

    if not cfg.is_file():
        return {}

    try:
        config = _json.loads(cfg.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, _json.JSONDecodeError):
        return {}

    voice_rel = config.get("voice_file")
    if not voice_rel:
        return {}

    voice_path = _Path(voice_rel).expanduser()
    if not voice_path.is_absolute():
        voice_path = (cfg.parent / voice_rel).resolve()

    if not voice_path.is_file():
        return {}

    try:
        content = voice_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}

    return {"raw": content, "path": str(voice_path)}


def _parse_profile_markdown(text: str, path):
    """Plain-markdown parser. Splits on top-level `## ` headers.

    Anything before the first `## ` is _preamble (with the leading `# Title`
    extracted into _title if present).
    """
    profile = {
        "_title": "",
        "_preamble": "",
        "_raw_headers": {},
        "_path": str(path),
    }

    # Normalize line endings
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    # Walk lines, accumulating sections. A "## " at line-start (no leading
    # whitespace) is the section boundary; ### and deeper stay inside.
    sections = []  # list of (raw_header, [body_lines])
    preamble_lines = []
    current_header = None
    current_body = []

    for line in lines:
        if line.startswith("## ") and not line.startswith("### "):
            # Flush current
            if current_header is None:
                # All previous lines belong to preamble
                pass
            else:
                sections.append((current_header, current_body))
            current_header = line[3:].strip()
            current_body = []
        else:
            if current_header is None:
                preamble_lines.append(line)
            else:
                current_body.append(line)

    if current_header is not None:
        sections.append((current_header, current_body))

    # Extract `# Title` from preamble (first `# ` line)
    title = ""
    cleaned_preamble = []
    for line in preamble_lines:
        if not title and line.startswith("# ") and not line.startswith("## "):
            title = line[2:].strip()
        else:
            cleaned_preamble.append(line)

    profile["_title"] = title
    profile["_preamble"] = "\n".join(cleaned_preamble).strip()

    for raw_header, body_lines in sections:
        key = _normalize_header(raw_header)
        if not key:
            continue
        # If multiple headers normalize to the same key, append (rare but
        # tolerated — keeps data instead of dropping silently).
        body = "\n".join(body_lines).strip()
        if key in profile:
            profile[key] = profile[key] + "\n\n" + body
        else:
            profile[key] = body
        profile["_raw_headers"][key] = raw_header

    return profile


# ---------- priority-rule extraction --------------------------------------- #


# Bolded sub-headings under the priority section, with the list they map to.
# Heuristic match: case-insensitive substring on the heading text.
_PRIORITY_SUBSECTIONS = (
    ("high_senders", ("high priority",)),
    ("noise_senders", ("noise",)),
    ("autopilot_ack_patterns", ("autopilot", "ack")),
    # Subject keywords don't have a dedicated sub-header in Lyndsay's draft,
    # but the wizard may generate one ("Priority subject keywords:"). Match
    # loosely so future profiles work.
    ("high_keywords", ("subject keyword", "high keyword")),
)


def _find_priority_section(profile):
    """Return the body string of the priority-rules section, or "" if missing.

    Tries several normalized keys because the section header has had several
    drafts (`## Priority rules`, `## Priority rules — what to surface and how`).
    """
    candidates = [
        "priority_rules",
        "priority_rules_what_to_surface_and_how",
    ]
    for key in candidates:
        if key in profile:
            return profile[key]
    # Last-resort: any key starting with "priority"
    for key, value in profile.items():
        if key.startswith("priority") and not key.startswith("_"):
            return value
    return ""


def _extract_bullet_lines(block_text: str) -> list:
    """Return a list of bullet-line strings from a markdown block.

    Recognizes `-`, `*`, `+` bullets (with optional leading whitespace). Drops
    the bullet marker. Trims trailing punctuation that isn't part of a value.
    """
    out = []
    for line in block_text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith(("- ", "* ", "+ ")):
            out.append(stripped[2:].strip())
        elif stripped.startswith(("-\t", "*\t", "+\t")):
            out.append(stripped[2:].strip())
    return out


# Pattern for things that look like an email address or domain inside prose.
# Examples it captures: "info@example.com", "@noreply.example.com",
# "sam@example.com". Returned lowercased.
_EMAIL_OR_DOMAIN_RE = _re.compile(
    r"(?<![A-Za-z0-9_.+-])"          # left boundary (not part of an identifier)
    r"(?:"
    r"[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"   # full email
    r"|"
    r"@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"               # bare @domain or domain prefix
    r")"
)

# Pattern for backticked tokens like `info@` or `@mailer.` — these are usually
# domain/sender HINTS in prose. We strip the backticks and keep the token.
_BACKTICKED_RE = _re.compile(r"`([^`]+)`")


def _extract_senders_from_bullet(bullet: str) -> list:
    """Pull email-address-like or domain-like tokens out of a bullet's text.

    Returns a list of lowercased strings. Looks at:
      - Backticked tokens (`info@`, `@noreply.`) — strong signal.
      - Plain text matches for `addr@domain.tld` and `@domain.tld`.
      - Plain bare-domain matches inside parens (e.g., "Example Co (example.com)").
    Empty list if nothing was found.
    """
    found = []
    seen = set()

    def _add(token):
        t = token.strip().lower().strip(".,;:!?")
        if t and t not in seen:
            seen.add(t)
            found.append(t)

    for m in _BACKTICKED_RE.findall(bullet):
        _add(m)
    for m in _EMAIL_OR_DOMAIN_RE.findall(bullet):
        _add(m)
    return found


def parse_priority_rules(profile):
    """Extract structured priority rules from a loaded profile.

    Looks for the section keyed roughly as 'priority_rules' (try a few variants)
    and parses its bullet content into:
      {
        "high_senders": [list of strings — email addresses or domains],
        "high_keywords": [list of strings — subject patterns],
        "noise_senders": [list of strings — email addresses or domains],
        "autopilot_ack_patterns": [list of strings — descriptors],
      }

    The current profile schema groups bullets under bolded sub-headings like
    `**High priority — surface first, draft fast:**`. Parse heuristically by
    splitting the section into sub-blocks at those bold headers, then
    extracting bullets under each.

    Returns a dict with empty lists if the section is missing or malformed —
    skills should treat empty lists as "no rules, default everything to standard".
    """
    empty = {
        "high_senders": [],
        "high_keywords": [],
        "noise_senders": [],
        "autopilot_ack_patterns": [],
    }
    if not isinstance(profile, dict) or not profile:
        return empty

    section_text = _find_priority_section(profile)
    if not section_text:
        return empty

    # Split into sub-blocks at lines that look like `**Heading:**`.
    bold_header_re = _re.compile(r"^\s*\*\*([^*]+?)\*\*\s*:?\s*$")
    sub_blocks = []  # list of (heading_lower, [block_lines])
    current_heading = ""
    current_lines = []
    for line in section_text.split("\n"):
        m = bold_header_re.match(line)
        if m:
            if current_lines or current_heading:
                sub_blocks.append((current_heading.lower(), current_lines))
            current_heading = m.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines or current_heading:
        sub_blocks.append((current_heading.lower(), current_lines))

    result = dict(empty)  # fresh lists

    for heading, body_lines in sub_blocks:
        if not heading:
            continue
        body_text = "\n".join(body_lines)
        bullets = _extract_bullet_lines(body_text)
        if not bullets:
            continue

        # Match heading to a target list
        target_key = None
        for key, needles in _PRIORITY_SUBSECTIONS:
            if any(n in heading for n in needles):
                target_key = key
                break
        if target_key is None:
            continue

        if target_key in ("high_senders", "noise_senders"):
            # Pull email/domain tokens out of each bullet. If a bullet has no
            # parseable token, store the raw descriptor — drafting agents can
            # still read it; the classifier just won't strictly match it.
            for bullet in bullets:
                senders = _extract_senders_from_bullet(bullet)
                if senders:
                    for s in senders:
                        if s not in result[target_key]:
                            result[target_key].append(s)
                else:
                    # Keep descriptor verbatim so it's not lost
                    if bullet not in result[target_key]:
                        result[target_key].append(bullet)
        else:
            # high_keywords + autopilot_ack_patterns: store bullets verbatim
            for bullet in bullets:
                if bullet not in result[target_key]:
                    result[target_key].append(bullet)

    return result


def classify_priority(sender_raw: str, subject_raw: str, rules: dict) -> str:
    """Classify a single message against parsed priority rules.

    Returns one of: 'high', 'standard', 'autopilot-ack', 'noise'.

    Matching rules:
      - sender match against `high_senders` (case-insensitive substring on the
        sender's email/domain) → 'high'
      - subject contains any token from `high_keywords` (case-insensitive) → 'high'
      - sender match against `noise_senders` → 'noise'
      - default → 'standard'

    autopilot-ack is not auto-assigned by sender/subject; it's reserved for
    a downstream pass that inspects body content.
    """
    if not rules:
        return "standard"

    sender_l = (sender_raw or "").lower()
    subject_l = (subject_raw or "").lower()

    # Extract the sender's email/domain explicitly for cleaner matching
    sender_email = sender_l
    if "<" in sender_l and ">" in sender_l:
        try:
            sender_email = sender_l.split("<", 1)[1].rsplit(">", 1)[0].strip()
        except Exception:
            sender_email = sender_l

    def _sender_hit(needles):
        for n in needles:
            if not isinstance(n, str):
                continue
            nl = n.lower().strip()
            if not nl:
                continue
            # Tokens like "@mailer." or "info@" — substring match against the
            # whole sender field handles both "info@x.com" and "@mailer.x.com".
            if nl in sender_l or nl in sender_email:
                return True
        return False

    if _sender_hit(rules.get("high_senders") or []):
        return "high"

    for kw in rules.get("high_keywords") or []:
        if not isinstance(kw, str):
            continue
        kwl = kw.lower().strip()
        if kwl and kwl in subject_l:
            return "high"

    if _sender_hit(rules.get("noise_senders") or []):
        return "noise"

    return "standard"
