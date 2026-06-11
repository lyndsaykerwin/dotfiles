# Startup Idea Discovery & Validation (Stage 1)

Use this skill when evaluating a new startup or product idea before building anything. It's a **checklist**, not a heavy process. Move fast, but don't skip steps — every checkbox must be honestly true before exiting Stage 1.

Order matters: **agents do public research first → only then do humans get interviewed**. This saves founder time and makes the conversations sharper.

---

## Core Principles (2026)

These are the assumptions baked into this checklist. If any of them stop being true, revisit the skill.

1. **AI agents do the desk work, founders do the conversations.** Scraping competitors, mining public user feedback, drafting outreach — all delegatable. Talking to 5+ real users — not.
2. **Public feedback is abundant — exhaust it before bothering humans.** Reddit, G2, Capterra, app store reviews, YouTube comments, Twitter, Glassdoor, Indeed JDs, podcast transcripts, HN threads. A user already complained on the internet. Find them.
3. **AI commoditization is the new "why now" — and the new "why not."** Every idea must answer: *what happens when the next model release makes this a feature?* If the answer is "we die," it's not a startup.
4. **Distribution > product.** Building is cheap (Cursor, v0, Lovable, Replit Agent). The hard part is reaching users. Validation must include a credible distribution plan.
5. **Willingness-to-pay needs revealed evidence, not stated intent.** "I'd pay for that" is worthless. "I already pay $X for [worse competitor]" is gold.
6. **Speed-to-conviction beats secrecy.** Your idea is being scraped right now. Validate fast, decide fast, move.

---

## Who Does What

| Role | Owns |
|------|------|
| **Founder** | Sections E (conversations) and F (synthesis) — non-delegatable |
| **Research Agent** | Section A (problem), B (public feedback mining), C (competitive), D (commoditization + distribution) |
| **User Sourcer** *(new)* | List-building: find target users on LinkedIn, Reddit, niche communities, industry Slacks |
| **Outreach Copywriter** *(new)* | Personalized cold outreach via Agentmail + LinkedIn, using each prospect's public footprint |
| **CEO** | Final Exit Gate sign-off |

**Hire if missing:** Use `paperclip-create-agent` to spin up any of the three agent roles above. The User Sourcer + Outreach Copywriter combo is what unlocks fast founder conversations — without them, sourcing eats more time than the interviews themselves.

---

## The Checklist

### A. Problem definition

- [ ] **Who specifically has this problem?** Named segment with constraints (e.g. "solo bookkeepers managing 5–15 clients on QBO"). Not "small businesses."
- [ ] **Their current workaround in their own words** — captured from public sources (forum posts, reviews, comments) or interviews. Direct quotes only.
- [ ] **The cost of not solving it** — money, time, or pain. With numbers.

> **Source for each claim:** [link] — accessed [YYYY-MM-DD]

---

### B. Public feedback mining (agents do this — save your time for real conversations)

Before talking to anyone, the Research Agent must produce a public-feedback dossier:

- [ ] **Reddit** — top 3 relevant subreddits searched; 5+ verbatim user complaints captured with links
- [ ] **Review sites** — G2 / Capterra / Trustpilot / Product Hunt comments on closest competitors; recurring complaints extracted
- [ ] **App stores** — 1-star and 3-star reviews mined for "I want this but…" patterns
- [ ] **Long-form** — YouTube tutorial comments, podcast transcripts, Substack comment sections relevant to the workflow
- [ ] **Job market signal** — Indeed/LinkedIn job postings: what tools are listed as "must have" or "experience with"? What jobs exist that didn't 2 years ago?
- [ ] **Reveal pricing signal** — what do users currently pay competitors? (BuiltWith, public pricing pages, annual reports, Reddit threads asking "what do you pay for X?")

> **Dossier saved as document key:** `public-feedback` on this issue
> **Every quote has a direct URL.** No "users say…" without a link.

**Exit check:** Could a stranger read the dossier and predict 80% of what your user interviews will surface? If yes, you've done it right.

---

### C. Competitive landscape

- [ ] **Top 5 competitors listed** with: what they're good at, what they fail at *for this specific user*, pricing, and a link
- [ ] **The closest competitor** identified — and the single sentence: "Unlike [X], we [differentiator] for [segment]."
- [ ] **AI-native competitors checked** — search "[problem] + AI", "[problem] + GPT", "[problem] + agent" on Twitter, Product Hunt, and HN from the last 90 days. Someone is already building this.

> Every competitor row has a direct URL.

---

### D. Why now + AI stress test (the new "why now")

- [ ] **What changed in the last 12 months that makes this newly solvable?** With a datable, linkable event or trend.
- [ ] **AI commoditization test:** what happens to this product if foundation models get 10x better in the next 18 months? (Acceptable answers: "we have proprietary data," "we have unique distribution," "we own the workflow integration." Unacceptable: "users will still prefer our UI.")
- [ ] **Distribution test:** how will you reach the first 100 paying users without burning money? Name the channel and why you can win it.

---

### E. User conversations (founder only — agents source, founder talks)

**Goal:** 5+ conversations with named, real humans in the target segment.

**Pre-work (agents handle):**
- [ ] User Sourcer builds a list of 30+ prospects from LinkedIn / communities / Reddit
- [ ] Outreach Copywriter drafts 30+ personalized messages using each prospect's public footprint
- [ ] Founder reviews/edits/sends via Agentmail or LinkedIn

**Mom Test rules (founder applies during conversations):**
- Talk about their life, not your idea
- No demos in the first 15 minutes
- "Cool!" or "I'd use that!" = you failed (politeness, not signal)
- Described workaround or specific manual headache = you passed

**Conversation log:**

| # | Name | Role | Date | Workaround they described (their words) | Revealed willingness to pay |
|---|------|------|------|----------------------------------------|----------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Willingness-to-pay bar:** "I'd pay" = 0 points. "I already pay $X for [worse tool]" or "I'd sign a paid pilot today" = real signal.

- [ ] 5 named humans interviewed
- [ ] 3+ described a real workaround in their own words
- [ ] 1+ said something I did not expect
- [ ] 1+ showed revealed willingness to pay (current spend on alternative, or paid pilot commitment)

---

### F. Synthesis

- [ ] **One surprise that changed my thinking** — specific, datable, attributable to a conversation or source
- [ ] **Top 3 risky assumptions** that, if wrong, kill the idea. For each: how I'd know it's wrong, and how I'd test it cheaply
- [ ] **Wedge** — the smallest valuable thing to build first

---

## EXIT GATE — All must be TRUE

- [ ] Section A: target user is named with constraints; cost-of-not-solving has numbers
- [ ] Section B: public-feedback dossier saved with linked quotes — exhausted before interviews started
- [ ] Section C: 5 competitors + AI-native competitor scan completed
- [ ] Section D: "why now" has a datable event AND the AI commoditization test has a credible answer AND distribution channel is named
- [ ] Section E: 5 named real humans, 3+ workarounds in their words, 1+ surprise, 1+ revealed willingness to pay
- [ ] Section F: surprise, 3 risky assumptions with tests, wedge identified
- [ ] **Every claim in A–D has a direct URL citation**
- [ ] CEO has reviewed and signed off

If any box is unchecked: the gate is closed. Identify the gap, assign a child issue, do not proceed to Stage 2.

---

## Hires needed to run this fast

If you don't have these agents, hire them before starting:

1. **Research Agent** — desk research, competitive analysis, public feedback mining. Owns Sections A–D.
2. **User Sourcer** — finds 30+ target users on LinkedIn, Reddit, niche communities, Slack groups. Outputs a prospect list.
3. **Outreach Copywriter** — drafts personalized cold messages per prospect using their public footprint. Sends via Agentmail (never Lyndsay's gmail).

Without 2 and 3, sourcing eats more founder time than the interviews. With them, founder spends time only on the conversations themselves.

Use `paperclip-create-agent` to hire any of the three.

---

*Skill version: 2.0 — Updated 2026-05-10 with public-feedback-first ordering, AI commoditization test, distribution test, revealed willingness-to-pay bar, and User Sourcer + Outreach Copywriter roles.*
