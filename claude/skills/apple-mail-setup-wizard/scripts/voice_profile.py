"""
voice_profile.py - read the Claude-produced voice profile and assemble profile.md.

The Claude-produced file is a markdown document with these sections at minimum:

    # Voice profile
    ## Voice patterns
    ...
    ## High-priority senders
    - Name <email>     -- reason
    ...
    ## Priority keywords
    - keyword     -- reason
    ...
    ## Noise senders
    - sender     -- reason
    ...
    ## Banned phrases
    - "phrase"     -- 0 uses in your sent mail
    ...
    ## Keep phrases
    - "phrase"     -- you used this 6 times, looks intentional
    ...
    ## Signature (if not already found)
    ...

We parse this into a dict so step 3/4 of the wizard can pre-fill review prompts,
then we compose the final profile.md from the user-edited version.

If the Claude-produced file doesn't exist or doesn't parse, we degrade to empty
lists and the wizard prompts the user from scratch.
"""

import re
from pathlib import Path
from typing import Optional

# Baked-in starter list of phrases the user reviews against actual sent mail.
# This is the floor — the voice-analysis pass adds context (kept vs banned)
# based on usage counts.
DEFAULT_BANNED_PHRASES = [
    "I wanted to reach out",
    "I hope this email finds you well",
    "hope this finds you well",
    "just wanted to touch base",
    "circle back",
    "happy to chat",
    "let me know if you have any questions",
    "thank you for your time",
    "please don't hesitate to reach out",
    "I trust this message finds you well",
    "as per our conversation",
    "kindly find attached",
    "moving forward",
    "going forward",
    "at your earliest convenience",
    "in today's fast-paced world",
    "leverage synergies",
    "deep dive",
    "low-hanging fruit",
    "drill down",
    "touch base",
    "ping me",
    "I appreciate your patience",
    "I just wanted to follow up",
    "I hope you're doing well",
]


def parse_voice_file(path: Path) -> dict:
    """Parse a Claude-produced voice profile markdown into a dict.

    Returns:
        {
            "voice_patterns": "free-form markdown blob",
            "high_priority_senders": ["Name <email>     -- reason", ...],
            "priority_keywords":     ["keyword     -- reason", ...],
            "noise_senders":         ["info@x.com     -- reason", ...],
            "banned_phrases":        ["phrase     -- 0 uses", ...],
            "keep_phrases":          ["phrase     -- 6 uses", ...],
            "signature":             "block of text or empty",
        }

    Missing sections come back empty. Hand-edited files are fine — we tolerate
    extra sections we don't recognize.
    """
    out = {
        "voice_patterns": "",
        "high_priority_senders": [],
        "priority_keywords": [],
        "noise_senders": [],
        "banned_phrases": [],
        "keep_phrases": [],
        "signature": "",
    }
    if not path.is_file():
        return out

    raw = path.read_text(encoding="utf-8", errors="replace")
    sections = _split_sections(raw)

    name_map = {
        "voice patterns": "voice_patterns",
        "voice": "voice_patterns",
        "high-priority senders": "high_priority_senders",
        "high priority senders": "high_priority_senders",
        "priority senders": "high_priority_senders",
        "priority keywords": "priority_keywords",
        "keywords": "priority_keywords",
        "noise senders": "noise_senders",
        "noise": "noise_senders",
        "banned phrases": "banned_phrases",
        "banned": "banned_phrases",
        "keep phrases": "keep_phrases",
        "keep": "keep_phrases",
        "signature": "signature",
    }
    for title, body in sections.items():
        key = name_map.get(title.lower().strip())
        if not key:
            continue
        if key in {"voice_patterns", "signature"}:
            out[key] = body.strip()
        else:
            out[key] = _parse_bullets(body)

    return out


def _split_sections(markdown: str) -> dict[str, str]:
    """Split markdown by `##` headers. Returns {title: body}."""
    sections: dict[str, str] = {}
    current_title: Optional[str] = None
    current_body: list[str] = []
    for line in markdown.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            if current_title is not None:
                sections[current_title] = "\n".join(current_body).strip()
            current_title = m.group(1)
            current_body = []
        else:
            if current_title is not None:
                current_body.append(line)
    if current_title is not None:
        sections[current_title] = "\n".join(current_body).strip()
    return sections


def _parse_bullets(body: str) -> list[str]:
    """Pull bullet lines out of a section body. Strips '-' / '*' / numbering."""
    items: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = re.match(r"^(?:[-*]|\d+\.)\s+(.*)$", stripped)
        if m:
            items.append(m.group(1).strip())
        elif items and (stripped.startswith("  ") or line.startswith("  ")):
            # continuation of previous bullet
            items[-1] = items[-1] + " " + stripped
    return items


def compose_profile_markdown(profile_data: dict) -> str:
    """Build the final profile.md content from collected data.

    profile_data shape (all keys optional; missing -> placeholder text):
        identity:           {"name": ..., "email_account_label": ..., "signature": ...}
        voice_patterns:     "markdown blob from Claude"
        high_priority:      ["Name <email>", ...]      (display strings, sources stripped)
        priority_keywords:  ["keyword", ...]
        noise_senders:      ["info@x.com", ...]
        banned_phrases:     ["phrase", ...]
        keep_phrases:       ["phrase", ...]            (informational)
        scope_in:           bool                       (did user confirm scope?)
        cold_outbound_out:  bool                       (always True for V1)
    """
    identity = profile_data.get("identity", {})
    name = identity.get("name", "(your name)")
    account_label = identity.get("email_account_label", "Exchange")
    signature = identity.get("signature", "").strip() or "(set this in Apple Mail > Settings > Signatures, or paste your block here)"

    voice_blob = profile_data.get("voice_patterns", "").strip()
    high_priority = profile_data.get("high_priority", [])
    keywords = profile_data.get("priority_keywords", [])
    noise = profile_data.get("noise_senders", [])
    banned = profile_data.get("banned_phrases", [])
    keep = profile_data.get("keep_phrases", [])

    lines: list[str] = []
    lines.append(f"# {name} - Email Preferences Profile")
    lines.append("")
    lines.append("This file is the personal layer for the `apple-mail-*` toolkit. "
                 "Any apple-mail-* skill (or a downstream drafting agent) reads this file "
                 "and applies the rules below. Edit anything here by hand - the skills "
                 "re-read this file on every invocation.")
    lines.append("")
    lines.append("## Identity")
    lines.append("")
    lines.append(f"- **Name in sign-offs:** {name}")
    lines.append(f"- **Apple Mail account label:** {account_label}")
    lines.append(f"- **Email signature:**")
    lines.append("")
    for sigline in signature.splitlines() or [signature]:
        lines.append(f"  {sigline}")
    lines.append("")

    lines.append("## Voice")
    lines.append("")
    if voice_blob:
        lines.append(voice_blob)
    else:
        lines.append("(no voice analysis run yet - re-run `setup.py` with voice analysis enabled, "
                     "or fill in this section by hand.)")
    lines.append("")

    lines.append("## Priority rules - what to surface first")
    lines.append("")
    lines.append("These rules drive the `apple-mail-inbox-triage` skill's priority labels. "
                 "Labels are **internal only** - the user reads them in the morning triage "
                 "summary; they never appear in outgoing email.")
    lines.append("")
    lines.append("### High-priority senders")
    lines.append("")
    if high_priority:
        for s in high_priority:
            lines.append(f"- {s}")
    else:
        lines.append("- (none yet - edit this list to add high-priority contacts)")
    lines.append("")
    lines.append("### Priority subject keywords")
    lines.append("")
    if keywords:
        for k in keywords:
            lines.append(f"- {k}")
    else:
        lines.append("- (none yet)")
    lines.append("")
    lines.append("### Noise senders - never surface")
    lines.append("")
    if noise:
        for n in noise:
            lines.append(f"- {n}")
    else:
        lines.append("- (none yet)")
    lines.append("")

    lines.append("## Banned phrases")
    lines.append("")
    lines.append("Drafting agents must not produce these phrases. They are LLM-filler that "
                 "the user has confirmed is not part of their voice.")
    lines.append("")
    if banned:
        for b in banned:
            lines.append(f"- {b}")
    else:
        lines.append("- (none yet)")
    lines.append("")
    if keep:
        lines.append("### Phrases the user does use (do NOT ban)")
        lines.append("")
        lines.append("For reference - these phrases appeared in the user's actual sent mail. "
                     "They look intentional, so drafting agents may use them.")
        lines.append("")
        for k in keep:
            lines.append(f"- {k}")
        lines.append("")

    lines.append("## Scope")
    lines.append("")
    lines.append("**IN scope for this profile:** inbox triage, reply drafting, "
                 "follow-up drafting, awaiting-reply surfacing, internal team emails, "
                 "FYIs and scheduling.")
    lines.append("")
    lines.append("**OUT of scope:** cold outbound (fresh first-touch emails to brand-new "
                 "prospects). Handled by a separate workflow.")
    lines.append("")

    lines.append("## Reply philosophy - 'think through to outcome'")
    lines.append("")
    lines.append("- When the user gives directional instructions ('intro X to Y', 'reply with "
                 "thanks', 'look back at prior emails'), think through what the next logical "
                 "step actually is to push the thread to its outcome. Don't execute literally.")
    lines.append("- What's the NEXT STEP that moves the thread forward?")
    lines.append("- Consolidate redundant responses. Two emails to the same person same day "
                 "saying similar things = one email covering both.")
    lines.append("- Don't send people back their own data. If they originated a fact, don't "
                 "include it as 'context' back to them.")
    lines.append("- Match the goal of the package. Internal-context emails go to the internal "
                 "team. External-scheduling emails go to the external party. Don't conflate.")
    lines.append("- Look at MULTIPLE prior emails for voice anchoring, not one.")
    lines.append("- Push back if a literal reading produces a bad result. Surface the corrected "
                 "shape in chat before drafting.")
    lines.append("")

    return "\n".join(lines) + "\n"


def strip_source(item: str) -> str:
    """Strip the trailing '-- reason' source annotation from a bullet line.

    Voice-pass output: 'Sam Rivera <sam@example.com>     -- replied within 1hr x 8 times'
    Final-profile: 'Sam Rivera <sam@example.com>'
    """
    for sep in ["     --", "    --", "   --", "  --", " --", "\t--"]:
        if sep in item:
            return item.split(sep, 1)[0].rstrip()
    return item


# ---------- existing-profile parser (for refresh flows) ------------------ #


# Section titles (## level) that --refresh-voice replaces. Everything else in
# the existing profile is preserved verbatim. Match is case-insensitive on the
# title text only (the header marker '##' is stripped before comparison).
_VOICE_REFRESH_SECTIONS = {
    "voice",
    "priority rules - what to surface first",
    "priority rules — what to surface first",  # em-dash variant
    "banned phrases",
}


def _ordered_split_sections(markdown: str) -> list[tuple[Optional[str], str]]:
    """Like _split_sections but preserves order and keeps the pre-header preamble.

    Returns a list of (title, body) tuples. The first tuple has title=None
    and holds any text before the first `##` header (typically the H1 title
    and intro paragraph). Each subsequent tuple is a `## Section` and its body
    (NOT including the header line itself; the body keeps its trailing/leading
    whitespace trimmed).
    """
    out: list[tuple[Optional[str], str]] = []
    current_title: Optional[str] = None
    current_body: list[str] = []
    for line in markdown.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            out.append((current_title, "\n".join(current_body).rstrip()))
            current_title = m.group(1)
            current_body = []
        else:
            current_body.append(line)
    out.append((current_title, "\n".join(current_body).rstrip()))
    return out


def merge_voice_refresh(
    existing_profile_md: str,
    fresh_voice_sections_md: str,
) -> str:
    """Splice fresh voice/priority/banned sections into an existing profile.

    Preserves identity, scope, reply philosophy, and any user-added sections
    we don't recognize. Replaces the three sections listed in
    _VOICE_REFRESH_SECTIONS with the freshly-composed equivalents.

    Args:
        existing_profile_md:    the current profile.md text.
        fresh_voice_sections_md: a markdown blob containing ONLY the three
            replacement sections, in the order Voice -> Priority -> Banned.
            (Produced by compose_voice_sections_only().)

    Returns the merged profile.md text (with a trailing newline).
    """
    parts = _ordered_split_sections(existing_profile_md)
    fresh_parts = _ordered_split_sections(fresh_voice_sections_md)
    # fresh_parts[0] is the preamble (should be empty); skip it.
    fresh_by_title: dict[str, str] = {}
    fresh_order: list[str] = []
    for title, body in fresh_parts[1:]:
        if title is None:
            continue
        key = title.lower().strip()
        fresh_by_title[key] = body
        fresh_order.append(key)

    # Walk the existing profile; replace recognized sections in place; drop the
    # original bodies but keep their position. Track which fresh sections we've
    # spent so we can append any leftovers at the end (e.g. if the existing
    # profile was missing one of the three).
    used_fresh: set[str] = set()
    chunks: list[str] = []  # each chunk is one section worth of text
    if parts and parts[0][0] is None and parts[0][1]:
        chunks.append(parts[0][1].rstrip() + "\n")
    for title, body in parts:
        if title is None:
            continue
        key = title.lower().strip()
        if key in _VOICE_REFRESH_SECTIONS and key in fresh_by_title:
            # fresh_by_title[key] already has trailing newline structure; trim
            # and re-emit cleanly.
            section = f"## {title}\n\n{fresh_by_title[key].strip()}\n"
            used_fresh.add(key)
        elif body:
            section = f"## {title}\n\n{body.strip()}\n"
        else:
            section = f"## {title}\n"
        chunks.append(section)

    # Append any fresh sections that weren't present in the existing profile,
    # in the order they appear in fresh_voice_sections_md.
    for key in fresh_order:
        if key in used_fresh:
            continue
        original_title = next(t for t, _ in fresh_parts[1:] if t and t.lower().strip() == key)
        chunks.append(f"## {original_title}\n\n{fresh_by_title[key].strip()}\n")

    # Join with a blank line between sections (so the raw markdown is also nice
    # to read, not just the rendered output).
    text = "\n\n".join(chunk.rstrip() for chunk in chunks) + "\n"
    # Collapse runs of 3+ newlines to 2 (one blank line).
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.rstrip() + "\n"


def compose_voice_sections_only(profile_data: dict) -> str:
    """Build ONLY the Voice / Priority / Banned-phrases sections.

    Used by --refresh-voice to produce a markdown blob suitable for
    merge_voice_refresh(). Mirrors the section text in compose_profile_markdown
    so the merged profile is indistinguishable from a freshly-composed one.
    """
    voice_blob = (profile_data.get("voice_patterns") or "").strip()
    high_priority = profile_data.get("high_priority", [])
    keywords = profile_data.get("priority_keywords", [])
    noise = profile_data.get("noise_senders", [])
    banned = profile_data.get("banned_phrases", [])
    keep = profile_data.get("keep_phrases", [])

    lines: list[str] = []
    lines.append("## Voice")
    lines.append("")
    if voice_blob:
        lines.append(voice_blob)
    else:
        lines.append("(no voice analysis run yet - re-run `setup.py` with voice analysis enabled, "
                     "or fill in this section by hand.)")
    lines.append("")

    lines.append("## Priority rules - what to surface first")
    lines.append("")
    lines.append("These rules drive the `apple-mail-inbox-triage` skill's priority labels. "
                 "Labels are **internal only** - the user reads them in the morning triage "
                 "summary; they never appear in outgoing email.")
    lines.append("")
    lines.append("### High-priority senders")
    lines.append("")
    if high_priority:
        for s in high_priority:
            lines.append(f"- {s}")
    else:
        lines.append("- (none yet - edit this list to add high-priority contacts)")
    lines.append("")
    lines.append("### Priority subject keywords")
    lines.append("")
    if keywords:
        for k in keywords:
            lines.append(f"- {k}")
    else:
        lines.append("- (none yet)")
    lines.append("")
    lines.append("### Noise senders - never surface")
    lines.append("")
    if noise:
        for n in noise:
            lines.append(f"- {n}")
    else:
        lines.append("- (none yet)")
    lines.append("")

    lines.append("## Banned phrases")
    lines.append("")
    lines.append("Drafting agents must not produce these phrases. They are LLM-filler that "
                 "the user has confirmed is not part of their voice.")
    lines.append("")
    if banned:
        for b in banned:
            lines.append(f"- {b}")
    else:
        lines.append("- (none yet)")
    lines.append("")
    if keep:
        lines.append("### Phrases the user does use (do NOT ban)")
        lines.append("")
        lines.append("For reference - these phrases appeared in the user's actual sent mail. "
                     "They look intentional, so drafting agents may use them.")
        lines.append("")
        for k in keep:
            lines.append(f"- {k}")
        lines.append("")

    return "\n".join(lines) + "\n"


def parse_existing_profile(path: Path) -> dict:
    """Read a previously-written profile.md back into the dict shape that
    compose_profile_markdown / step_* functions expect.

    Used by --refresh-profile to pre-fill prompts with the user's existing
    answers. Best-effort: missing or unparseable sections return empty
    strings / empty lists, and the wizard will just ask the user fresh for
    those.

    Returns a dict with keys:
        identity:           {"name", "email_account_label", "signature"}
        voice_patterns:     str
        high_priority:      list[str]
        priority_keywords:  list[str]
        noise_senders:      list[str]
        banned_phrases:     list[str]
        keep_phrases:       list[str]
    """
    out = {
        "identity": {"name": "", "email_account_label": "", "signature": ""},
        "voice_patterns": "",
        "high_priority": [],
        "priority_keywords": [],
        "noise_senders": [],
        "banned_phrases": [],
        "keep_phrases": [],
    }
    if not path.is_file():
        return out

    raw = path.read_text(encoding="utf-8", errors="replace")

    # Identity is encoded in the H1 title + an Identity section with bullet
    # fields. The H1 is "# {name} - Email Preferences Profile".
    m = re.search(r"^#\s+(.+?)\s*-\s*Email Preferences Profile\s*$", raw, re.MULTILINE)
    if m:
        out["identity"]["name"] = m.group(1).strip()

    # Split top-level sections.
    sections = _split_sections(raw)

    # Identity section: look for the bullet lines.
    identity_body = sections.get("Identity", "") or sections.get("identity", "")
    if identity_body:
        nm = re.search(r"\*\*Name in sign-offs:\*\*\s*(.+)$", identity_body, re.MULTILINE)
        if nm:
            out["identity"]["name"] = nm.group(1).strip()
        lm = re.search(r"\*\*Apple Mail account label:\*\*\s*(.+)$", identity_body, re.MULTILINE)
        if lm:
            out["identity"]["email_account_label"] = lm.group(1).strip()
        # Signature: text after "**Email signature:**" line, indented by 2 spaces
        sig_match = re.search(
            r"\*\*Email signature:\*\*\s*\n(.*?)(?=\n##|\Z)",
            identity_body + "\n##",  # sentinel so the lookahead succeeds at EOF
            re.DOTALL,
        )
        if sig_match:
            sig_block = sig_match.group(1)
            sig_lines = []
            for line in sig_block.splitlines():
                if line.startswith("  "):
                    sig_lines.append(line[2:])
                elif line.strip() == "":
                    sig_lines.append("")
            sig = "\n".join(sig_lines).strip()
            # Skip the placeholder text written when no signature was detected
            if sig and "(set this in Apple Mail" not in sig:
                out["identity"]["signature"] = sig

    # Voice section: free-form blob.
    voice_body = sections.get("Voice", "")
    if voice_body and "(no voice analysis run yet" not in voice_body:
        out["voice_patterns"] = voice_body.strip()

    # Priority section contains ### subsections we have to dig out by hand.
    prio_body = (
        sections.get("Priority rules - what to surface first", "")
        or sections.get("Priority rules — what to surface first", "")
    )
    if prio_body:
        for sub_title, key in (
            ("High-priority senders", "high_priority"),
            ("Priority subject keywords", "priority_keywords"),
            ("Noise senders - never surface", "noise_senders"),
            ("Noise senders — never surface", "noise_senders"),
        ):
            m2 = re.search(
                rf"^###\s+{re.escape(sub_title)}\s*$\n+(.*?)(?=^###\s|\Z)",
                prio_body,
                re.MULTILINE | re.DOTALL,
            )
            if m2:
                items = _parse_bullets(m2.group(1))
                # filter placeholder "(none yet ...)" entries
                items = [i for i in items if not i.startswith("(none yet")]
                if items:
                    out[key] = items

    # Banned phrases section.
    banned_body = sections.get("Banned phrases", "")
    if banned_body:
        # Split off the "### Phrases the user does use" subsection if present.
        keep_match = re.search(
            r"^###\s+Phrases the user does use.*?$\n+(.*?)(?=^##|\Z)",
            banned_body,
            re.MULTILINE | re.DOTALL,
        )
        keep_text = ""
        banned_text = banned_body
        if keep_match:
            keep_text = keep_match.group(1)
            banned_text = banned_body[: keep_match.start()]
        banned_items = [i for i in _parse_bullets(banned_text) if not i.startswith("(none yet")]
        keep_items = [i for i in _parse_bullets(keep_text) if not i.startswith("(none yet")]
        out["banned_phrases"] = banned_items
        out["keep_phrases"] = keep_items

    return out
