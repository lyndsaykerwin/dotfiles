---
name: cost-audit
description: Use this skill when Lyndsay asks to check spending, run a cost audit, review token usage, or asks "how much am I spending" or "where is my money going."
---

# Cost Audit Skill

When Lyndsay asks for a cost audit, run the following analysis and present results in plain English. No session IDs, no file paths, no jargon.

## Step 1: Gather Data

Run these commands to collect spending data:

### Daily spend (last 7 days)
```bash
for f in ~/.openclaw/agents/*/sessions/*.jsonl; do
  date=$(head -1 "$f" | jq -r '.timestamp' | cut -dT -f1)
  cost=$(jq -s '[.[] | .message.usage.cost.total // 0] | add' "$f")
  echo "$date $cost"
done | awk '{a[$1]+=$2} END {for(d in a) print d, "$"a[d]}' | sort -r | head -7
```

### Spend by model
```bash
for f in ~/.openclaw/agents/*/sessions/*.jsonl; do
  jq -r 'select(.message.usage != null) | .message.model // "unknown"' "$f"
done | sort | uniq -c | sort -rn
```

### Most expensive sessions (top 5)
```bash
for f in ~/.openclaw/agents/*/sessions/*.jsonl; do
  cost=$(jq -s '[.[] | .message.usage.cost.total // 0] | add' "$f")
  echo "$cost $f"
done | sort -rn | head -5
```

### Tool call frequency
```bash
for f in ~/.openclaw/agents/*/sessions/*.jsonl; do
  jq -r '.message.content[]? | select(.type == "toolCall") | .name' "$f"
done | sort | uniq -c | sort -rn | head -10
```

### Current context size
```bash
wc -c ~/.openclaw/workspace/SOUL.md ~/.openclaw/workspace/USER.md ~/.openclaw/workspace/IDENTITY.md ~/.openclaw/workspace/AGENTS.md 2>/dev/null
```

## Step 2: For Each Expensive Session, Read What Happened

For the top 5 most expensive sessions, read the actual user messages:
```bash
jq -r 'select(.message.role == "user") | .message.content[]? | select(.type == "text") | .text' <session-file>.jsonl | head -20
```

Summarize what Lyndsay was actually doing in that session (e.g., "drafting an email to Erik about taxes" not "session 2282bd65").

## Step 3: Present the Report

Use this format:

### Spending Summary (Last 7 Days)
- **Total spent:** $X.XX
- **Daily average:** $X.XX
- **Budget status:** X% of $1.50/day limit

### Where the Money Went
- Break down by what Lyndsay was doing (email work, setup, troubleshooting, etc.)
- Note what percentage went to Sonnet vs Haiku
- Flag any heartbeat or cron costs hitting the paid API

### Waste Flags
- Any sessions with input tokens over 50K (context bloat)
- Any sessions with more than 20 tool calls (runaway loops)
- Any cache write costs over $0.10 (cache miss on a big conversation)
- Any Sonnet usage on simple tasks (file reads, shell commands)

### Recommendations
- Top 3 specific actions to reduce costs, in order of impact
- Compare current daily average to the $1.50 budget target

## Step 4: Budget Check

If today's spend is over $1.13 (75% of $1.50 daily budget), warn Lyndsay immediately.
