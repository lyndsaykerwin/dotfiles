"""
wizard_common.py - shared helpers for the apple-mail-skills setup wizard.

Keeps setup.py focused on flow control. Anything mechanical (AppleScript escape,
subprocess wrappers, HTML-to-text, prompt helpers, file paths) lives here.

This is the ONLY module in skills/apple-mail-setup-wizard/scripts/ that other
helpers should import from. setup.py imports from this module + the small
sibling modules in this same folder.
"""

import json
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional


# ---------- paths ---------------------------------------------------------- #

PROFILE_DIR = Path.home() / ".claude" / "preferences" / "apple-mail"
PROFILE_PATH = PROFILE_DIR / "profile.md"
PROFILE_BACKUP_PATH = PROFILE_DIR / "profile.md.bak"

CONFIG_FILENAME = "apple-mail-config.json"


# ---------- subprocess wrappers ------------------------------------------- #


def run_capture(cmd: list[str], timeout: int = 10) -> Optional[str]:
    """Run a command and return stripped stdout, or None on any failure.

    Used for soft auto-detection (git config user.name, id -F, etc.) where
    "didn't work" should not be loud — the wizard just moves on to the next
    fallback.
    """
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except (FileNotFoundError, subprocess.TimeoutExpired, PermissionError):
        return None
    if r.returncode != 0:
        return None
    out = r.stdout.decode("utf-8", errors="replace").strip()
    return out or None


# ---------- AppleScript -------------------------------------------------- #


def escape_applescript(value: str) -> str:
    """Escape a Python string for safe injection into AppleScript double-quoted literal."""
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


def run_applescript(script: str, timeout: int = 60) -> Optional[str]:
    """Run AppleScript via osascript. Returns stdout on success, None on failure.

    Soft failure (returns None) rather than SystemExit, because the wizard
    needs to recover gracefully — most of the AppleScript calls here are
    "try to detect this; if it doesn't work, ask the user".
    """
    try:
        r = subprocess.run(
            ["osascript", "-"],
            input=script.encode("utf-8"),
            capture_output=True,
            timeout=timeout,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", errors="replace").strip()


def applescript_available() -> bool:
    return shutil.which("osascript") is not None


# ---------- mail signature parsing ---------------------------------------- #


class _SignatureHTMLParser(HTMLParser):
    """Tiny HTML-to-text converter.

    Apple Mail signature files are HTML fragments (sometimes a full document
    with embedded MIME headers). We pull out visible text, treat <br> and
    <p>/<div> close as newlines, and skip <style>/<script>.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in {"style", "script", "head"}:
            self._skip_depth += 1
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"style", "script", "head"} and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self.parts.append(data)


def html_to_text(html: str) -> str:
    p = _SignatureHTMLParser()
    try:
        p.feed(html)
    except Exception:
        return html
    text = "".join(p.parts)
    # Apple Mail signature files often start with MIME-like headers
    # (Content-Type, Mime-Version, Message-Id, etc.). Strip those if present.
    lines = text.split("\n")
    cleaned: list[str] = []
    in_header_block = True
    for line in lines:
        stripped = line.strip()
        if in_header_block:
            if not stripped:
                in_header_block = False
                continue
            if re.match(r"^[A-Za-z\-]+:\s", stripped):
                continue
            in_header_block = False
        cleaned.append(line)
    # collapse runs of >2 blank lines
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(cleaned)).strip()
    return out


def find_signature_files() -> list[Path]:
    """Return all .mailsignature files found in the two standard locations.

    macOS has moved Mail's data directory around over the years. We check
    both — the classic location and the sandboxed Containers location.
    """
    candidates: list[Path] = []
    roots = [
        Path.home() / "Library" / "Mail",
        Path.home() / "Library" / "Containers" / "com.apple.mail" / "Data" / "Library" / "Mail",
    ]
    for root in roots:
        if not root.exists():
            continue
        for path in root.glob("V*/MailData/Signatures/*.mailsignature"):
            candidates.append(path)
    return candidates


def read_signature_from_files() -> Optional[str]:
    """Read the largest mailsignature file (proxy for "the one with real content")."""
    files = find_signature_files()
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_size, reverse=True)
    for f in files:
        try:
            raw = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        text = html_to_text(raw)
        if text:
            return text
    return None


# ---------- prompt helpers ------------------------------------------------ #


def _is_tty() -> bool:
    return sys.stdin.isatty()


def prompt(question: str, default: Optional[str] = None) -> str:
    """Ask a question. Returns the user's answer (or default if they pressed Enter).

    Non-TTY: returns the default (or empty string). This keeps the wizard
    runnable from scripted/test contexts without hanging on stdin.
    """
    if not _is_tty():
        return default or ""
    hint = f" [{default}]" if default else ""
    try:
        answer = input(f"{question}{hint}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit("Setup cancelled.")
    return answer or (default or "")


def prompt_required(question: str) -> str:
    """Loop until the user types a non-empty answer. No default Enter-accept."""
    while True:
        ans = prompt(question)
        if ans:
            return ans
        print("  (an answer is required — please type something.)")


def prompt_choice(question: str, choices: list[str], default: Optional[str] = None) -> str:
    """Constrain answer to one of `choices`. Case-insensitive match on prefix."""
    label = "/".join(choices)
    while True:
        ans = prompt(f"{question} ({label})", default=default)
        if not ans:
            continue
        low = ans.lower()
        for c in choices:
            if c.lower() == low or c.lower().startswith(low):
                return c
        print(f"  please answer one of: {label}")


def prompt_yn(question: str, default: Optional[str] = None) -> bool:
    """Yes/no prompt. Returns True for yes."""
    ans = prompt_choice(question, ["y", "n"], default=default)
    return ans == "y"


def apply_edits(items: list[str], edits: str) -> list[str]:
    """Apply +foo / -foo style edits to a list.

    Splitting:
      - commas split top-level edits
      - each token is whitespace-stripped
      - prefix '+' means add, '-' means remove (case-insensitive removal)
      - bare token (no prefix) is treated as +add

    Removal matches case-insensitively; addition preserves the user's casing.
    """
    if not edits.strip():
        return list(items)
    result = list(items)
    lower_result = [x.lower() for x in result]
    for raw in edits.split(","):
        tok = raw.strip()
        if not tok:
            continue
        op = "+"
        if tok[0] in "+-":
            op = tok[0]
            tok = tok[1:].strip()
        if not tok:
            continue
        if op == "-":
            try:
                idx = lower_result.index(tok.lower())
                result.pop(idx)
                lower_result.pop(idx)
            except ValueError:
                pass
        else:
            if tok.lower() not in lower_result:
                result.append(tok)
                lower_result.append(tok.lower())
    return result


# ---------- printing ------------------------------------------------------ #


def banner(text: str) -> None:
    """Print a section header that stands out."""
    line = "=" * max(len(text) + 4, 60)
    print()
    print(line)
    print(f"  {text}")
    print(line)


def info(text: str) -> None:
    print(text)


def step(num: int, text: str) -> None:
    print()
    print(f"--- Step {num}: {text} ---")


def warn(text: str) -> None:
    print(f"  ! {text}")


def good(text: str) -> None:
    print(f"  > {text}")


# ---------- config writing ------------------------------------------------ #


def write_config_json(target_dir: Path, workspace_id: str, account_name: str) -> Path:
    target = target_dir / CONFIG_FILENAME
    payload = {
        "workspace_id": workspace_id,
        "account_name": account_name,
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def backup_existing_profile() -> Optional[Path]:
    """If a profile already exists, copy it to profile.md.bak. Returns the backup path."""
    if not PROFILE_PATH.exists():
        return None
    PROFILE_BACKUP_PATH.write_text(
        PROFILE_PATH.read_text(encoding="utf-8"), encoding="utf-8"
    )
    return PROFILE_BACKUP_PATH


def ensure_profile_dir() -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
