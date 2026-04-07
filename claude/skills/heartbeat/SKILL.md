---
name: heartbeat
description: Use this skill when processing a heartbeat poll or when Lloyd needs to do proactive background work.
---

# Heartbeat - Be Proactive

When you receive a heartbeat poll, don't just reply HEARTBEAT_OK every time. Use heartbeats productively!

## What to Check (rotate through these, 2-4 times per day)

- **Emails** - Any urgent unread messages?
- **Calendar** - Upcoming events in next 24-48h?
- **Mentions** - Twitter/social notifications?
- **Weather** - Relevant if Lyndsay might go out?

## Track Your Checks

Use `memory/heartbeat-state.json`:

```json
{
  "lastChecks": {
    "email": 1703275200,
    "calendar": 1703260800,
    "weather": null
  }
}
```

## When to Reach Out

- Important email arrived
- Calendar event coming up (<2h)
- Something interesting you found
- It's been >8h since you said anything

## When to Stay Quiet (HEARTBEAT_OK)

- Late night (23:00-08:00) unless urgent
- Lyndsay is clearly busy
- Nothing new since last check
- You just checked <30 min ago

## Heartbeat vs Cron: When to Use Each

**Use heartbeat when:**
- Multiple checks can batch together (inbox + calendar + notifications in one turn)
- You need conversational context from recent messages
- Timing can drift slightly (every ~30 min is fine, not exact)
- You want to reduce API calls by combining periodic checks

**Use cron when:**
- Exact timing matters ("9:00 AM sharp every Monday")
- Task needs isolation from main session history
- You want a different model or thinking level for the task
- One-shot reminders ("remind me in 20 minutes")
- Output should deliver directly to a channel without main session involvement

**Tip:** Batch similar periodic checks into HEARTBEAT.md instead of creating multiple cron jobs. Use cron for precise schedules and standalone tasks.

## Proactive Work (No Permission Needed)

- Read and organize memory files
- Check on projects (git status, etc.)
- Update documentation
- Commit and push your own changes

## Memory Maintenance (Every Few Days)

During a heartbeat, periodically:
1. Read through recent `memory/YYYY-MM-DD.md` files
2. Identify significant events, lessons, or insights worth keeping long-term
3. Update `MEMORY.md` with distilled learnings
4. Remove outdated info from MEMORY.md that's no longer relevant

Think of it like reviewing your journal and updating your mental model. Daily files are raw notes; MEMORY.md is curated wisdom.

The goal: Be helpful without being annoying. Check in a few times a day, do useful background work, but respect quiet time.
