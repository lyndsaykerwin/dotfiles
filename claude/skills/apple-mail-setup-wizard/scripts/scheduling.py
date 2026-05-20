"""
scheduling.py - optionally schedule the morning inbox triage.

Two paths:

  cron:
    - Edits the user's crontab via `crontab -l` / `crontab -`.
    - The job runs python3 against the inbox-triage skill and pipes output to
      a log file under ~/.claude/state/<workspace>/inbox-triage.log
    - Detection: look for the wizard's marker line in the existing crontab.
    - Pros: runs locally, no Claude Code session needed.
    - Cons: just runs the triage and logs - no drafting, no human-readable
      morning brief in chat.

  Claude Code scheduled task (recommended):
    - Renders the full morning-triage routine prompt with workspace values
      substituted in, writes it to /tmp/<taskId>-prompt.md, and prints a
      structured instruction asking the parent Claude session to call the
      `create_scheduled_task` MCP tool. That tool both saves the prompt as
      `~/.claude/scheduled-tasks/<taskId>/SKILL.md` AND registers the cron
      schedule in the Claude Code Desktop Routines runtime. No workspace-
      level routine .md files are created - the scheduled-task SKILL.md is
      the single source of truth.
    - Pros: full agent run with drafting, runs in a real Claude Code session,
      shows up in the Desktop Routines section.
    - Cons: requires Mac online + Claude Code available at the scheduled time.

The wizard hands the user a clear trade-off and they pick.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

CRON_MARKER = "# apple-mail-skills: inbox-triage (managed by setup.py)"


def parse_clock_time(answer: str) -> Optional[tuple[int, int, bool]]:
    """Parse '9:00 AM weekdays', '9am', '14:30', etc. -> (hour, minute, weekdays_only).

    Returns None if we can't parse. The caller can re-prompt with a clearer
    example. We only need hour/minute/weekday-or-daily - this is not a full
    cron expression parser.
    """
    a = answer.strip().lower()
    weekdays_only = bool(re.search(r"weekday", a))
    # strip weekday/weekend hints to make time parsing easier
    a = re.sub(r"(weekdays?|weekends?|only|every\s+day|daily)", "", a).strip()

    # 24-hour: '14:30', '9:00'
    m = re.match(r"^(\d{1,2}):(\d{2})\s*(am|pm)?\s*$", a)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        meridian = m.group(3)
        if meridian == "pm" and hour < 12:
            hour += 12
        elif meridian == "am" and hour == 12:
            hour = 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute, weekdays_only)

    # '9am', '9 am', '9:30am'
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s*$", a)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        meridian = m.group(3)
        if meridian == "pm" and hour < 12:
            hour += 12
        elif meridian == "am" and hour == 12:
            hour = 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute, weekdays_only)

    return None


def read_crontab() -> str:
    """Return current crontab text, or '' if none / command unavailable."""
    try:
        r = subprocess.run(["crontab", "-l"], capture_output=True, timeout=10)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    if r.returncode != 0:
        return ""
    return r.stdout.decode("utf-8", errors="replace")


def has_existing_cron_entry() -> bool:
    return CRON_MARKER in read_crontab()


def install_cron_entry(
    hour: int,
    minute: int,
    weekdays_only: bool,
    workspace_id: str,
    workspace_dir: Path,
    skills_root: Path,
) -> bool:
    """Add (or replace) the wizard's cron entry. Returns True on success."""
    triage_script = skills_root / "apple-mail-inbox-triage" / "scripts" / "inbox_triage.py"
    log_path = Path.home() / ".claude" / "state" / workspace_id / "inbox-triage.log"
    config_path = workspace_dir / "apple-mail-config.json"

    dow = "1-5" if weekdays_only else "*"
    py = sys.executable or "python3"

    # log_path's parent is created lazily by inbox-triage anyway, but make sure
    log_path.parent.mkdir(parents=True, exist_ok=True)

    cron_line = (
        f"{minute} {hour} * * {dow} "
        f"{py} {triage_script} --config {config_path} "
        f">> {log_path} 2>&1"
    )

    existing = read_crontab()
    lines = existing.splitlines()
    out: list[str] = []
    skip_next = False
    for line in lines:
        if line.strip() == CRON_MARKER:
            skip_next = True
            continue
        if skip_next:
            skip_next = False
            continue
        out.append(line)
    out.append(CRON_MARKER)
    out.append(cron_line)
    new_crontab = "\n".join(out).rstrip() + "\n"

    try:
        r = subprocess.run(
            ["crontab", "-"],
            input=new_crontab.encode("utf-8"),
            capture_output=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


def render_morning_triage_prompt(workspace_id: str, workspace_dir: Path) -> str:
    """Render the morning-triage routine prompt for this workspace.

    Produces a LEAN prompt (~50 lines): paths + phases + don'ts. Voice rules,
    banned phrases, priority order, and reply philosophy are NOT inlined here
    — the `apple-mail-*` skills load `profile.md` automatically via
    `common.py:load_profile()` and apply the rules in code. Re-stating them
    in the prompt is duplication.

    Expensive operations like runtime voice mining ("read 30 sent emails to
    learn the user's phrasing") are NOT in the prompt either — the wizard
    already mined them once at setup; refresh quarterly via
    `--refresh-voice`, not daily at every routine fire.
    """
    ws = str(workspace_dir)
    config_path = f"{ws}/apple-mail-config.json"
    home = str(Path.home())
    triage_script = f"{home}/.claude/skills/apple-mail-inbox-triage/scripts/inbox_triage.py"
    awaiting_script = f"{home}/.claude/skills/apple-mail-awaiting-reply/scripts/awaiting_reply.py"

    return f"""# Morning Inbox Triage — {workspace_id}

Thin orchestration prompt. The `apple-mail-*` skills load `profile.md` (voice, priority, banned phrases, reply philosophy) automatically and apply the rules in code. **Trust the skills. Do not re-state or re-apply voice / priority / banned-phrase rules in this prompt — that's duplication.**

Each run is fresh. Requires Mail.app open and the configured account signed in.

## Constants — use these paths verbatim, do NOT explore or verify

| Variable | Path |
|---|---|
| `CONFIG` | `{config_path}` |
| `TRIAGE_SCRIPT` | `{triage_script}` |
| `AWAITING_REPLY_SCRIPT` | `{awaiting_script}` |
| `DRAFT_REPLY_SKILL` | invoke via the `apple-mail-draft-reply` skill |

No `cd`. No `ls`. No Read-to-verify. The skills handle config + profile auto-discovery.

If this workspace has its own additive voice file (e.g. `{ws}/outreach/email_style.md`), it loads via the workspace overlay mechanism — don't reference it in this prompt.

## Identity rules

- `save` drafts. Never `send`.
- Outputs go to **Mac Mail Drafts** (replies) and **chat** (briefing). No markdown briefing file.
- Never use Gmail tools. The account in `CONFIG` is the only identity.

## Phase 1 — Pull new inbox messages

```bash
python3 {triage_script} \\
  --config {config_path} \\
  --json --show-priority
```

JSONL output. Each record has `date`, `sender`, `sender_name`, `sender_email`, `subject`, `message_id`, `body`, plus `priority` (already classified by the skill from `profile.md` rules: `high` / `standard` / `autopilot-ack` / `noise`).

If "No new inbox emails needing reply since <date>." — skip Phase 2, still run Phase 3, print minimal briefing.

## Phase 2 — Draft replies, in priority order

Iterate records in this order: `high` → `standard` → `autopilot-ack`. Skip `noise`.

For each, invoke `apple-mail-draft-reply` with a 1-line reply approach (e.g., "scheduling kickoff", "diligence ack"). The skill loads `profile.md`, applies the voice + banned phrases + reply philosophy, and saves a threaded draft.

**Don't re-state voice rules to the skill.** Pass message context and approach. The skill knows the voice.

**Personal-emotional content** (family, condolences) — flag in the briefing, do NOT draft. (See profile.md's "The bar" section for the carve-out.)

## Phase 3 — Surface stalled sent threads

```bash
python3 {awaiting_script} \\
  --config {config_path}
```

Classify each (do NOT draft):
- **Worth a nudge** — >3 days quiet, substantive
- **Stale, probably forget** — >10 days quiet, low-stakes
- **Recent** — <3 days, give it time

Surface "worth a nudge" in the briefing.

## Phase 4 — Print briefing to chat

```
# Morning Inbox Briefing — YYYY-MM-DD

## New inbox — N messages since last run
### Reply Needed (N — drafted in Drafts): [sender, subject, 1-line approach]
### Autopilot Acks (N — drafted): [sender, subject]
### Internal CC / FYI (N — no draft): [sender, subject]
### Noise (N — no detail)
### Flagged for human (N): [sender, subject, why]

## Awaiting reply — worth a nudge (N): [recipient, subject, days quiet, why]

## Flags
- [Anything noise-pattern to add to profile.md filters]
- [Any draft worth a closer look]
- [Any inbound with a Message-ID already replied to — real bug]

## Ready to review.
```

## Don'ts

- Never `send`. `save` only.
- Never `cd`, `ls`, or Read-to-verify the constants.
- Never write a markdown briefing file.
- Never re-state voice / banned phrases / priority rules. Skills load and apply them.
- Never mine sent emails for voice at runtime. Voice anchors live in `profile.md`, refreshed quarterly via `--refresh-voice`.
- Never draft outbound. That's a separate workflow.
"""


def prepare_claude_scheduled_task(
    hour: int,
    minute: int,
    weekdays_only: bool,
    workspace_id: str,
    workspace_dir: Path,
) -> dict:
    """Render the morning-triage prompt, write it to a temp file, and return
    the metadata the parent Claude needs to register the scheduled task via
    the `create_scheduled_task` MCP tool.

    The returned dict has: `taskId`, `cronExpression`, `description`,
    `prompt_path` (the temp file), `prompt_preview` (first 200 chars for the
    wizard's confirmation message).

    The wizard prints a structured instruction using these values. The parent
    Claude reads the prompt file and makes ONE tool call which both writes
    the SKILL.md to `~/.claude/scheduled-tasks/<taskId>/SKILL.md` and
    registers the cron in the Routines runtime. No workspace-level mirror is
    produced.
    """
    task_id = f"{workspace_id}-morning-inbox"
    dow = "1-5" if weekdays_only else "*"
    cron_expression = f"{minute} {hour} * * {dow}"
    days_label = "weekdays" if weekdays_only else "every day"
    description = (
        f"Morning inbox triage for {workspace_id} — pulls since-last-run "
        f"Apple Mail messages, drafts in-thread replies via apple-mail-draft-reply, "
        f"surfaces stalled sent threads via apple-mail-awaiting-reply, prints a chat "
        f"briefing. Drafts only — never sends. Runs {hour:02d}:{minute:02d} {days_label}."
    )

    prompt_body = render_morning_triage_prompt(workspace_id, workspace_dir)

    # Write to a known, predictable temp path so the parent Claude can find it.
    tmp_path = Path(tempfile.gettempdir()) / f"apple-mail-routine-{task_id}.md"
    tmp_path.write_text(prompt_body, encoding="utf-8")

    return {
        "taskId": task_id,
        "cronExpression": cron_expression,
        "description": description,
        "prompt_path": str(tmp_path),
        "prompt_preview": prompt_body[:200],
    }


def format_claude_schedule_instruction(
    hour: int,
    minute: int,
    weekdays_only: bool,
    workspace_id: str,
    workspace_dir: Path,
) -> str:
    """Return the multi-line instruction the wizard prints after preparing
    the Claude Code scheduled task. The instruction is directed at the parent
    Claude session — paste-friendly but more importantly, structured enough
    that the parent Claude can pick it up and make the MCP call without
    further user input.
    """
    meta = prepare_claude_scheduled_task(
        hour=hour,
        minute=minute,
        weekdays_only=weekdays_only,
        workspace_id=workspace_id,
        workspace_dir=workspace_dir,
    )
    when = f"{hour:02d}:{minute:02d}"
    days = "weekdays" if weekdays_only else "every day"
    return (
        f"Morning triage routine prepared for workspace '{workspace_id}'.\n"
        f"\n"
        f"To register it in Claude Code Desktop Routines, the parent Claude session\n"
        f"should call the `create_scheduled_task` MCP tool with these arguments:\n"
        f"\n"
        f"  taskId         : {meta['taskId']}\n"
        f"  cronExpression : {meta['cronExpression']}    (= {when} {days})\n"
        f"  description    : {meta['description']}\n"
        f"  prompt         : <contents of {meta['prompt_path']}>\n"
        f"\n"
        f"That single tool call writes the prompt to\n"
        f"  ~/.claude/scheduled-tasks/{meta['taskId']}/SKILL.md\n"
        f"AND registers the cron schedule. The task will appear in your Desktop\n"
        f"Routines section (initially disabled — enable it there when ready).\n"
        f"\n"
        f"No workspace-level routine .md file is created. The scheduled-task\n"
        f"SKILL.md is the single source of truth for this routine."
    )
