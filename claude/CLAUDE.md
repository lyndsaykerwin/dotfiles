## General Behavior

When you get stuck or hit a tool limitation, immediately say so and move on to the next item. Do not stall or wait for user to say 'continue'. If a batch task hits a rate limit or tool error, save progress, summarize what's done vs. remaining, and propose next steps.

When using agent teams / Task tool: Do NOT poll TaskOutput more than 5 times in a row. If agents are stalling, report status and ask me how to proceed instead of polling indefinitely.

## General Behavior

**Important** I can't write code, so I need simple step by step explanation for technical work. Act like you're a computer science professor explaining a technical concept to your grandma.

## Tools & Browser

For any browser automation tasks (navigating websites, filling forms, scraping data, testing web apps), use the agent-browser skill — NOT the Chrome extension MCP. Do not ask me to sign in or install a Chrome extension. Just use agent-browser directly.

When I ask about finding a skill, discovering a skill, or whether a skill exists for something, always use the find-skills skill to search first before suggesting anything custom.

## Skills

All skills live in the global location: `C:\Users\Courtney Stuart\.claude\skills\`

This makes them available in every project automatically. Current skills:

- **Workflow:** `brainstorming`, `writing-plans`, `executing-plans`, `finishing-a-development-branch`
- **Quality:** `verification-before-completion`, `test-driven-development`, `systematic-debugging`
- **Code review:** `requesting-code-review`, `receiving-code-review`
- **Agents:** `subagent-driven-development`, `dispatching-parallel-agents`, `using-superpowers`, `heartbeat`
- **Frontend:** `frontend-design`, `web-design-guidelines`
- **Data:** `scraped-data-cleaning`, `cost-audit`
- **Tools:** `agent-browser`, `find-skills`, `skill-creator`, `writing-skills`, `using-git-worktrees`, `desktop-to-codespaces`
- **Desktop:** `docx`, `email-writing`, `google-workspace`, `nda-processor`

When creating or updating any skill:
1. Save to `~/.claude/skills/<skill-name>/SKILL.md`
2. After saving, verify the skill appears in the auto-loaded skills list

(Skills directory IS a symlink to my dotfiles repo — edits in either location update both. Don't fight it.)

## GitHub & Git — Hand-Holding Mode

Lyndsay is a non-coder. Before any git action, say in plain English where things stand (which branch, what's staged vs committed vs pushed vs merged) and translate jargon — never assume she remembers what branch/commit/push/PR mean. Always remind her explicitly when work is committed-but-not-pushed, or pushed-but-not-merged: those don't count as "live" yet.

## Gmail MCP

A Gmail MCP server is connected for email tasks (searching, reading messages/threads, drafting, managing labels). Use the Gmail MCP tools directly for any email-related requests — do not use browser automation for Gmail.

## Verification

Tell me you read the global Claude.MD on start up.