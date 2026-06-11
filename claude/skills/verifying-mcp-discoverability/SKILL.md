---
name: verifying-mcp-discoverability
description: Use when finishing or changing ANYTHING an MCP server exposes to an LLM — tools, templates, schemas, capability listings, defaults, examples, or descriptions — before claiming done, closing the issue, or merging. Also use when an agent failed to use a feature that exists ("the model didn't see it").
---

# Verifying MCP Discoverability

## Overview

For an MCP, a feature the calling LLM can't find **does not exist**. "Done" = the code works AND a cold agent can discover and correctly use the feature through the tool surface alone.

Baseline failure this prevents: SlideForge shipped flexible layouts, blank panels, and series renaming — an external agent read the capability surface, concluded the product was rigid, and hand-built a PPTX outside the tool. 4 of its 6 "missing feature" complaints already existed in code.

## The Four Checks (all required before "done")

1. **Cold read** — Call the server's discovery/listing tool(s) with DEFAULT args, exactly as a fresh agent would. The changed capability must appear with enough information to use it without repo access. "It shows up in verbose/detail mode" fails this check.
2. **Copy audit** — Read every description, note, example, and error message the LLM sees that touches this feature. Delete steering-away language: stale "beta", "coming soon", "use X instead", constraints that no longer hold. Copy ships in the same commit as the code.
3. **Default routes** — If the server publishes defaults, recommendations, or examples, they must point at the new path — not at a legacy twin. If a rigid/old variant of the same capability still exists, delete it or mark it deprecated in the surface text, in this same change.
4. **Outsider test (the gate)** — Dispatch one subagent given ONLY the discovery-tool output (no repo, no conversation context) plus the user task the feature serves. Pass = it selects the feature and forms a valid call. Fail = not done — fix the surface, not the agent. Record the result as the issue's acceptance evidence.

**Plus, always:** if the same metadata lives in more than one place (generated catalog, hand-kept validator mirror, docs), regenerate ALL copies from the single source. Drift between copies is how features get orphaned.

## Red Flags — STOP, you're about to ship an invisible feature

| Thought | Reality |
|---|---|
| "Code works, I'll fix the docs later" | The description IS the product for an LLM caller. |
| "It's discoverable if you ask for detail" | Cold agents read defaults. Default surface or it doesn't exist. |
| "The old template still works, leave it" | A rigid twin beside a flexible one steers agents into the dead end. |
| "An agent should infer it from the schema" | Run the outsider test or it didn't happen. |
| "Removing legacy is a separate cleanup ticket" | Separate tickets never run; the agent meets the legacy first. |
