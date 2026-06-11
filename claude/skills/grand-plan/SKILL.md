---
name: grand-plan
description: "Use at the start of any new project (or when formalizing an existing one's planning) to write the PRD in the required structure and stand up the Grand Plan system — the live PRD → spec → plan chain that keeps EVERY Paperclip task traceable to the business vision, catches drift automatically, and surfaces decisions to Lyndsay. Triggers: 'new project', 'write/structure the PRD', 'set up the plan', 'grand plan', 'project kickoff', 'why are agents doing X', 'is this drift'. Pairs with the brainstorming skill (which discovers intent) — this skill structures that intent and wires the governance around it."
---

# Grand Plan

## What this is and why it exists

A **non-technical founder** (Lyndsay) writes a vision doc, hands it to agents, and weeks later discovers the agents built a different product. This happened on SlideForge: the doc she actually read mixed the true core with heavy "sell it" machinery, a separate engineering spec quietly added a whole web-SaaS, the plan was built from the *spec* instead of the vision, and the one drift-check ran once into a document she never reads. Three weeks of work flowed toward the wrong product with no tripwire she could see.

**The Grand Plan is the fix.** It is not a document — it is the **live, linked chain of three layers**:

```
PRD  (the WHAT + WHY — Lyndsay owns, writes, edits, tracks)
 └─ Spec  (the HOW — engineering; subordinate to the PRD, must cite it)
     └─ Plan  (the checkpoints + Paperclip issues — what's actually being built)
```

**The one invariant that makes it work:**

> **No Paperclip issue may live outside the Grand Plan.** Every issue must trace up to a line in the PRD. An issue that can't be traced is one of two things — **drift** (someone wandered off-plan) or a **signal the PRD needs to change** — and either way it is raised to Lyndsay *before* code is written, never resolved silently by an agent.

This turns "watch for drift" (a vague, forgettable duty) into a single mechanical question: *does every issue trace to a PRD line?*

The worked example is SlideForge's `prd.html` (in the SlideForge repo root). Copy its visual style and section order when creating a new PRD.

---

## When to use this skill

- Starting a brand-new project → write the PRD in this structure, then stand up the Grand Plan.
- Formalizing an existing project that grew without one → reverse-engineer the PRD from what exists, then back-fill tethers to find current orphans (drift).
- Anytime someone asks "why is an agent doing X?", "is this drift?", or "what's our progress against the plan?"

The PRD *content* often comes from the `brainstorming` skill. This skill is about **structure + governance**: the required sections, the rules, and the operating system around them.

---

## Where the Grand Plan lives (the home)

- **Canonical home (what agents read):** a **pinned issue document in Paperclip**, surfaced in the **Active Plan tab** (the left-nav entry Lyndsay built). Agents must be able to read it on cloud machines too, and Paperclip is the only place that's always reachable — a Google Doc is **not** (Workspace tools are Mac-only on this setup).
- **Readable artifact (what Lyndsay reads):** an HTML doc styled like SlideForge's `prd.html`. Clean, scannable, no jargon.
- **Optional writing surface:** a Google Doc Lyndsay edits, which an agent mirrors INTO the Paperclip doc. Only add this if the Paperclip editor is too clunky for her — it's a convenience, never the source of truth.

---

## PART A — The PRD (the sections Lyndsay owns)

Lyndsay writes and owns ONLY the sections below. She never writes IDs, phase tags, or any wiring (see Part B). Keep every word plain-English — if she'd have to Google a term, define it inline. Section order:

1. **Tagline** — one paragraph: what it is, for whom, the magic, in her words.
2. **The insight / the problem** — the pain, told as a concrete story of a real person's bad afternoon.
3. **Who it's for** — a named persona in a specific moment (e.g. "Maya, VP, 13 minutes before IC").
4. **What it does (in plain words)** — the handful of capabilities, each one sentence. Lead with *how you drive it*, not a feature list.
5. **The user stories — THE SPINE** — 3-5 stories. **Every task in the whole project must trace to one of these.** If a task serves none, it's out of scope or it's drift. Each story gets a Definition of Done (below).
6. **Definition of Done, per story** — see the rule below; this is the highest-leverage section.
7. **In scope now / Saved for later** — two columns. Every "later" item names the **trigger** that flips it to "now" (e.g. "when a design partner asks"). This is the plain-English version of phase-gating.
8. **Hard rules — never cross these** — the prohibitions/guardrails. Absolute lines (e.g. "the AI never invents a number"). These are the *strongest* drift-catchers because a violation is obvious. Distinct from "saved for later": a hard rule protects what the product IS; a "later" item just isn't built yet.
9. **Decisions — settled & open** — the forks agents must NOT resolve alone. Record settled ones (so the team builds to them) and keep open ones visible. The classic drift trap lives here: anything ambiguous about scope belongs here as a decision, not silently filed into "building now."

### The Definition-of-Done rule (do not get this wrong)

A Definition of Done describes **the real user action and the QUALITY of the result** — verifiable by a non-coder with their own eyes. It is **NOT** about opening a file or a passing test.

- ❌ Wrong: "You open one HTML file built from the Excel data."  *(file-mechanics, not the experience)*
- ❌ Wrong: "The retention parser's unit tests pass."  *(invisible to Lyndsay)*
- ✅ Right: "You prompt Claude with your Excel file (through the MCP connection) and get back a chart where every number is accurate to the file and the design looks professional — IC-ready, not a rough draft. Click through every cut; nothing is invented; a missing number shows a blank, never a guess."

Pattern: **[the real action the user takes] → [the result, judged on accuracy AND professionalism] → [the guardrail that proves it's trustworthy].** Always phrased as "Done when you can see…".

---

## PART B — The derived contract layer (the PM maintains; Lyndsay never types it)

The PRD prose is for humans. Agents and the drift-checker need machine-readable hooks. The **PM (Steward)** derives and maintains these *from* Lyndsay's prose — she never writes them:

1. **Stable clause IDs.** Every PRD line gets a permanent ID (`PRD-story-1`, `PRD-hardrule-no-invented-numbers`). Issues tether to the ID, so the link survives reordering and rewording. Lyndsay never invents IDs — the PM assigns them.
2. **Phase gates** are read directly from her "In scope now / Saved for later (+ trigger)" buckets. "Later until X" *is* the gate. No separate phase list.
3. **Authority is read from section placement** — no tagging needed:
   - Anything in **Decisions** or **Hard rules** = **Lyndsay's call.** Changing it needs her approval.
   - Everything else = **team discretion.**
4. **The Spec must cite PRD clause IDs.** Every spec section names the PRD clause(s) it implements. Any section that deviates from the PRD is stamped **`DEVIATION — needs CEO/Lyndsay sign-off`**. An uncited spec section is as visible as an untethered issue — this is the structural fix for "the spec quietly added the web-SaaS."

Optionally keep a read-only **"contract view"** (the IDs + tethers) next to the pretty PRD so Lyndsay can audit drift if she wants — clean doc for reading, contract view for spot-checking. Only build it if she asks.

---

## PART C — The operating system (the four owners + the machinery)

### The four owners (state this in every project; never leave it fuzzy)

| Job | **Accountable owner** | Helpers | How it happens |
|---|---|---|---|
| **Status updates as issues finish** | **PM** (owns the rendered plan) | The finishing agent owns ONLY their own issue's status | Auto-projection: agent marks their issue `done` with evidence → Paperclip wakes the checkpoint → the plan's status cell regenerates from issue state. **Nobody hand-types the plan.** |
| **Updating the plan when new things are added** | **Lyndsay** if it touches the PRD; **PM** drafts & propagates | Manager/lead if it's within existing PRD intent | New work under an existing PRD line → the creating manager tethers it. New *direction* → PM drafts the PRD change, **Lyndsay approves** (CEO holds the pen only if she's out of the loop). |
| **Drift detection** | **PM** (Steward) | An automatic code-vs-PRD check (a tripwire) | PM runs the gate + sweeps for untraceable issues; the code-check objectively flags "built something the PRD forbids." Both alarms route to the PM, who raises real ones to Lyndsay. |
| **Making sure new issues are in the Grand Plan** | **PM** (the gate is the guarantee) | The creating agent sets the tether first | Creator **sets the structured tether (`grandPlanNodeId`) at creation** — see "How to tether" below. Untethered (and not inherited) = auto-flagged drift + raised to the CEO/Lyndsay. |

**Workers are protected:** a worker's ONLY plan-duties are (1) **set the tether (`grandPlanNodeId`) when they create an issue** (see "How to tether" — a clause mention in prose does NOT count), and (2) mark their own issue done with evidence. They never edit the Grand Plan. This keeps their context light and the plan honest.

### How to tether an issue — the BUILT mechanism (do THIS; prose is not a tether)

As of 2026-05-30 the gate is implemented in Paperclip as a **structured field on each issue: `grandPlanNodeId`** (a Grand Plan node id). Writing "PRD tether: PRD-story-1" in the description does **NOT** tether the issue — it will still be flagged as drift. Every issue you create must SET this field:

1. **Find the clause's node id.** `GET /api/companies/{companyId}/grand-plan` returns the live PRD → Spec → Plan tree. Find the node whose `title` equals the PRD clause ID you're serving (e.g. `PRD-decided-mcp-is-the-product`) and take its `id`. (Clause nodes are the `tier:"prd"` nodes directly under the root; tether to the most specific node that exists — a Plan node if one exists for that clause, otherwise the clause node itself.)
2. **Set it at creation.** Include `grandPlanNodeId: "<that node id>"` in the body of `POST /api/companies/{companyId}/issues`. The create API accepts and validates it.
3. **Sub-issues inherit automatically.** Any child issue created under an already-tethered parent inherits its clause — you only do steps 1–2 for a new **top-level** issue.

If no clause fits, leave `grandPlanNodeId` unset **on purpose** — the gate raises it to the CEO/Lyndsay as drift-or-PRD-change (it auto-raises a `grand_plan_tether` approval and wakes the CEO). **Never invent a tether to dodge the gate.**

**Adding a new PRD clause?** Don't hand-create the node — **edit the PRD document.** The PRD-change cascade detects the new/changed clause, flags affected work, and raises a `grand_plan_reconcile` approval to Lyndsay; on approval the new clause node is created automatically, and you then tether issues to it (steps 1–2).

### The Steward gate — original native-blocker design (SUPERSEDED — see "How to tether" above)

> **Superseded 2026-05-30.** The implemented gate uses the structured `grandPlanNodeId` field + an auto-raised approval + a CEO wake (above). Do **NOT** create "tether-check" blocker issues — that mechanism was never built. Kept here only for design context.

Paperclip forbids cross-agent mutation of `status`/`blockedByIssueIds` — even for the CEO. So the Steward must NOT reach into other agents' issues. Use blocker auto-resolution instead:

1. When any agent creates work issue `X`, it **self-sets** (allowed on its own new issue) `blockedByIssueIds: [tether-check-X]`, where `tether-check-X` is a small issue **assigned to the PM/Steward**.
2. The Steward only ever touches **its own** tether-check issue. It rules:
   - **Tethers cleanly** → mark `tether-check-X` `done` → Paperclip fires `issue_blockers_resolved` and **auto-unblocks `X`** for free.
   - **Looks like drift** → raise a Paperclip **approval to Lyndsay**, leave it open. Nothing builds.
   - **Legit new direction** → update the Grand Plan (PRD/spec/plan) with Lyndsay's sign-off, THEN mark done.

Batch to control cost: one tether-check per *checkpoint* (covering its new children); auto-pass issues whose tether points at an already-approved node — only genuinely new nodes need a ruling.

### Auto-update — event-driven, never a clock (budget + heartbeats-off safe)

Two flows, both fired by real events (which work even when scheduled heartbeats are off; a daily cron would drain a tiny budget):

- **Bottom-up (issues → plan):** issue → `done` → checkpoint wake (`issue_children_completed` / status change) → regenerate just that row from issue state, using the plan doc's revision system (`baseRevisionId` optimistic concurrency). Only volatile cells (status, what's-left) rewrite; the plain-English what/why prose is written once and frozen.
- **Top-down (PRD/spec morphs → re-validate):** a PRD document revision bump wakes the Steward to re-check every tether pointing at the changed clause and flag anything now-orphaned or now-contradicted. This is what makes "the Grand Plan is allowed to change" safe instead of scary.

The heavier code-vs-PRD diff runs on a Paperclip routine with an **`api`/`webhook` trigger** wired to commits/deploys (fires on real change, not a clock), plus on-demand when Lyndsay opens the Active Plan tab. Reserve a true cron only as a weekly backstop if budget allows. Be honest with Lyndsay: continuous real-time drift detection doesn't fit a $2/month budget — event-driven + on-open is genuinely automatic for everything that matters.

### Context management (preserve the full plan for the right readers; don't drown workers)

| Audience | Loads | Mechanism |
|---|---|---|
| Lyndsay | the rendered PRD/Active Plan (full, human-readable) | Active Plan tab |
| Managers / Steward | full PRD + spec + plan, once per session, prompt-cached | `GET /issues/:id/documents` + caching of the stable docs |
| Workers | ONLY their issue + the one-line tether + their checkpoint's DoD & Out-of-Scope | `GET /issues/:id/heartbeat-context` (ancestor **summaries**, not full bodies) |

The **tether is the firewall**: one line ("serves PRD-story-1") carries enough *why* down to a worker without the *weight* of the whole plan. Keep PRD/spec stable (cache well) and the plan's prose frozen so only volatile status churns.

---

## PART D — Setup checklist for a new project

1. **Write the PRD** (Part A sections) as an HTML doc styled like SlideForge `prd.html`. Plain English; DoD per story using the rule above; Hard rules section; Decisions section.
2. **Publish it as the canonical Paperclip doc** and pin it to the Active Plan tab.
3. **Derive the contract layer** (Part B): assign clause IDs, read phase gates from now/later, authority from section placement. Require the spec to cite clause IDs.
4. **Declare the four owners** (Part C) in the project's kickoff issue — PM is Steward; name who plays each role.
5. **The Steward gate is built-in** — the `grandPlanNodeId` soft-gate (raises an approval + wakes the CEO on any untethered issue). Make sure every agent **sets `grandPlanNodeId` at issue creation** — see "How to tether an issue".
6. **Wire auto-update**: event-driven row refresh + PRD-change re-validation; code-vs-PRD diff on commit/deploy + on-open.
7. **Back-fill (existing projects):** tether every current issue. Each one that won't tether is surfaced as drift-or-PRD-change and raised to Lyndsay.

---

## Hard constraints / gotchas

- **Never cross-mutate another agent's status/blockers** (403, even as CEO). Use the native-blocker mechanism above.
- **Budget is tiny ($2/mo on SlideForge) and scheduled heartbeats may be off.** Drive everything off *events*, not clocks. Batch Steward rulings.
- **Cloud agents can't read Google Docs.** Canonical Grand Plan lives in Paperclip, full stop.
- **Don't let workers load the full plan.** Tether + `heartbeat-context` only. The plan is a projection of issue state — never hand-edit status into it.
- **Surface, don't decide.** When an issue can't be tethered, raise it to Lyndsay as drift-or-change. Do not silently file it under a vague theme — that "laundering" (e.g. labeling consumer-signup as "licensing") is exactly how the original drift slipped through.
