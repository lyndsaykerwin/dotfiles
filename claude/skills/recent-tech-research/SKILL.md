---
name: recent-tech-research
description: Restricts web searches to the most recent 30 days when researching technical, software, or AI topics. Use this skill whenever the user asks Claude to research, look up, find information about, summarize the state of, or compare anything related to AI, ML, LLMs, models, frameworks, libraries, programming languages, software tools, developer products, APIs, SDKs, cloud services, or any fast-moving technical subject — even if the user does not say "recent" or "latest." This space changes weekly (model releases, deprecations, pricing, new features, version bumps), so older results are frequently stale or misleading. Default to a 30-day recency window and surface the cutoff to the user. Do NOT use for non-technical research (history, biographies, recipes) or long-settled technical fundamentals (how TCP works, what a hash table is).
---

# Recent Tech Research

The user does technical and AI research often and finds that web search results from many months or years ago are usually outdated for this domain. This skill teaches Claude to default to a 30-day recency window for technical and AI searches without requiring the user to specify it each time.

## When this triggers

Trigger whenever the user asks for information, comparisons, recommendations, or summaries about any of the following:

- AI, ML, LLMs, foundation models, model releases, agents, evals, prompting techniques
- Software libraries, frameworks, packages, SDKs, APIs
- Programming languages and their ecosystems
- Developer tools, IDEs, CLIs, build systems
- Cloud services, infrastructure, hosting, databases
- Tech company product launches, pricing, features, deprecations
- Security vulnerabilities, CVEs, patches
- Benchmarks, leaderboards, performance comparisons in tech
- Best practices, conventions, or "how people are doing X now"

If you are unsure whether a topic counts as "fast-moving technical," err on the side of triggering — the cost of an unnecessarily fresh search is low, but the cost of confidently citing a stale result is high.

## When NOT to trigger

Do not apply the 30-day window when:

- The user explicitly asks for historical context, a retrospective, or "how this evolved over time"
- The topic is a long-settled fundamental (data structures, networking basics, mathematical concepts, established language syntax)
- The query is non-technical (news, sports, recipes, travel, biographies of historical figures)
- The user specifies their own time window ("in the last year", "since 2023", etc.) — respect their window instead

## How to apply the recency window

Use the `web_search` tool with date qualifiers in the query so the search engine returns recent results. Good ways to do this:

- Append the current month and year to the query (e.g., "Claude API rate limits May 2026")
- Add the word "today" or "this month" for fast-moving topics (e.g., "best open source LLM today")
- For very fresh topics like model releases or outages, include "this week" or the specific recent date

Today's date is available in the system context. Compute the 30-day cutoff from there and use it to frame queries — do not hardcode a year.

After getting results, **state the explicit date range you used** so the user can verify the anchor is actually today, not a stale system date. Always include the today's-date anchor pulled from system context AND the cutoff 30 days back. Format: "Searched for results from [cutoff date] to [today's date]." For example: "Searched for results from April 3 to May 3, 2026."

This is non-negotiable — saying "the last 30 days" without dates is exactly what this skill exists to prevent, because the user has no way to know whether your "today" matches their today. Always show both dates so they can confirm.

If the 30-day window returns nothing useful, expand to 90 days and tell the user you widened the window, again with explicit dates ("from February 3 to May 3, 2026"). Don't silently fall back to all-time results without flagging it, since that defeats the purpose of the skill.

## Output expectations

Lead with the freshest, most relevant findings. When citing a source, include the publication date inline if it's available — this lets the user judge freshness at a glance. If two sources conflict and one is meaningfully older, prefer the newer one and note the discrepancy.

If your search turns up something that contradicts what you'd otherwise say from memory (e.g., an API that you "know" works one way but recent docs show has changed), trust the recent search result and flag the change to the user. The whole point of this skill is that your training data is older than what the user needs.

## Example

**User:** "What's the best way to do structured outputs with Claude?"

**Without this skill:** Claude might pull from its training data or do an undated search and describe an approach that's been superseded.

**With this skill:** Claude searches with a query like "Claude structured outputs May 2026" or "Claude tool use structured output this month", reads the most recent docs and posts, and answers based on the current recommended approach — telling the user something like "Searched for results from April 3 to May 3, 2026" so they can verify the anchor is today's actual date.
