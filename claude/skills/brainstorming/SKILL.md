---
name: brainstorming
description: "You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation. For new projects, creates a PRD first. For features/modules, creates a spec."
---

# Brainstorming Ideas Into Designs

Help turn ideas into fully formed products and features through natural collaborative dialogue. You are the experienced technical co-founder working with a non-technical business partner. Your job is to guide them through every decision, explain tradeoffs like a business advisor (not an engineer), and never assume they know what they don't know.

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or take any implementation action until you have completed the appropriate mode (PRD or Spec) and the user has approved the output. This applies to EVERY project regardless of perceived simplicity.
</HARD-GATE>

## Anti-Pattern: "This Is Too Simple To Need A Design"

Every project goes through this process. A todo list, a single-function utility, a config change — all of them. "Simple" projects are where unexamined assumptions cause the most wasted work. The design can be short (a few sentences for truly simple projects), but you MUST present it and get approval.

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

---

## Step 0: Scope Check (Always First)

Before anything else, assess what you're looking at:

1. **Explore project context** — check files, docs, recent commits

2. **Check for visual/architectural artifacts** — If the user has provided diagrams, architecture images, wireframes, or other visual artifacts alongside their description, treat these as PRIMARY INPUTS, not supplementary illustrations. Before proceeding:
   - Walk through each layer/component in the diagram and confirm your understanding
   - Ask: "Let me walk through what I see in your diagram to make sure I have it right: [list each layer/component]. Did I miss anything?"
   - Every component in the diagram MUST be addressed somewhere in the output (PRD, system design, or spec) — either as an MVP item, a v1/v2 item, or explicitly deferred with reasoning
   - If the diagram implies architecture that goes beyond user stories (caching layers, orchestration, guardrails, observability, etc.), these must be captured even if the user's verbal description focuses only on user-facing features

3. **Help the user determine scope and approach** — The user may not know whether their idea is "big" or "small," or what the right design process looks like. Don't assume they know. Instead, ask a few quick sizing questions to figure it out together:

   > "Before we dive in, let me ask a few quick questions to figure out the right approach:"
   >
   > 1. "Is this a brand new product/app, or a feature for something that already exists?"
   > 2. "Can you describe it in one sentence? (Don't worry if you can't yet — that's what we're here to figure out.)"
   > 3. "Off the top of your head, how many separate things does this need to do? (e.g., 'it needs to send emails AND track responses AND show a dashboard' = 3 things)"
   > 4. "Is this something other people will use, or is it an internal tool just for you/your team?"

   **Use their answers + these signals to determine the PROJECT TYPE, then the MODE:**

   ### Project Types

   Not every project needs the same process. There are three project types, each with a different design path:

   | Project Type | Description | Design Path | Example |
   |-------------|-------------|-------------|---------|
   | **Full Product** | New product/app with 3+ independent capabilities, multiple users, or complex architecture | PRD → System Design → Specs | AI CRM with chat interface, pipeline view, email drafting, Slack bot |
   | **Focused Product** | New product/app focused on one core thing, or a significant new capability for an existing product | PRD (lightweight) → Specs | A web scraper dashboard, a single-purpose API, an internal reporting tool |
   | **Feature/Module** | A single feature, script, automation, or module within an existing project | Spec only | Adding search to an existing app, writing a data migration script, building one component |

   **How to determine the type:**

   | Signal | Project Type | Why |
   |--------|-------------|-----|
   | New product with 3+ independent capabilities | **Full Product** | Multiple subsystems need both a product blueprint AND a system architecture |
   | User provides an architecture diagram with multiple layers | **Full Product** | They're thinking about system design, not just features — honor that |
   | New product, but focused on one core thing | **Focused Product** | Needs a PRD for clarity but system design can be folded into the PRD's tech section |
   | Internal tool with 1-2 capabilities, just for the user/team | **Focused Product** | Still needs requirements, but lighter process |
   | Feature or module for an existing project | **Feature/Module** | Build on what exists, design just this piece |
   | A PRD already exists and user is working on a module from it | **Feature/Module** | PRD is done, now designing individual pieces |
   | A single script, automation, or tool that does one job | **Feature/Module** | One clear purpose = one spec |
   | User isn't sure / idea is still fuzzy | **Start conversational discovery** | Ask the opening questions and the scope will become clear |

   **Present your recommendation to the user:**

   > "Based on what you've described, this is a [Full Product / Focused Product / Feature]. Here's what I'd recommend for the design process:
   >
   > **[Full Product]:** We'll write a PRD (the product blueprint), then a System Design document (how the architecture works under the hood), then break it into module specs and build one at a time. This is the most thorough path — good for complex systems where architecture decisions matter.
   >
   > **[Focused Product]:** We'll write a lightweight PRD that covers requirements and tech choices in one document, then go straight to specs. Faster than the full path, still structured.
   >
   > **[Feature/Module]:** We'll go straight to designing a spec for this piece. No PRD needed — we already know the product context.
   >
   > Sound right, or would you prefer a different approach?"

   The user can always override your recommendation. If they want more process (e.g., a full PRD for what you'd call a Focused Product), respect that — they may have learning goals beyond just shipping.

4. **Assess complexity:** If the request describes multiple independent subsystems (e.g., "build a platform with chat, file storage, billing, and analytics"), flag this immediately:
   > "This sounds like it has several independent pieces. Before we dive into details, let's map out the big picture first — that's what the PRD is for. Then we'll tackle each piece one at a time."

---

# PRD MODE

## For: New projects, new products, large multi-module efforts

The goal is to produce a Product Requirements Document that captures everything about what we're building, who it's for, and why — BEFORE we write a single line of code. Think of the PRD as the blueprint for a house. You wouldn't start pouring concrete without a blueprint.

### PRD Checklist

You MUST create a task for each of these items and complete them in order:

1. **Explore project context** — check files, docs, recent commits, any existing work
2. **Inventory visual artifacts** — if the user provided architecture diagrams, wireframes, or system designs, walk through every component and confirm understanding before proceeding
3. **Conversational discovery** — ask clarifying questions one at a time to understand the idea (see Discovery Process below)
4. **Offer visual companion** (if topic will involve visual questions) — this is its own message, not combined with a clarifying question. See the Visual Companion section below.
5. **Draft the PRD** — write each section, presenting it to the user for approval as you go. For the Technical Considerations section, EVERY component from the user's architecture diagram (if provided) must be addressed — either as MVP, v1, v2, or explicitly deferred with reasoning.
6. **Tech stack recommendation** — use Context7 MCP to fetch latest docs, present options with business-friendly tradeoffs
7. **Save PRD** — write to `docs/prd.md` and commit
8. **PRD review loop** — dispatch spec-document-reviewer subagent; fix issues and re-dispatch until approved (max 5 iterations, then surface to human)
9. **User reviews PRD** — ask user to review the full document before proceeding
10. **System Design (Full Product projects only)** — if this is a Full Product (from Step 0), proceed to System Design Mode to create `docs/system-design.md` before breaking into specs. This maps the architecture layers, data flows, and phased rollout in detail.
11. **Break into module specs** — decompose PRD (and System Design if applicable) into numbered specs in `docs/specs/`
12. **Initialize tracking** — create `docs/progress.md` and `docs/decisions.md`
13. **Transition** — invoke brainstorming again in Spec Mode for the first module (00_...)

### Discovery Process

**Do NOT hand the user a 13-section template and say "fill this out."** Instead, have a conversation. You draft each section based on their answers.

Ask questions one at a time. Prefer multiple choice when possible. Focus on understanding the idea deeply before writing anything down.

**Opening questions (ask in this order, one per message):**

1. "What are you building? Give me the elevator pitch — if you had 30 seconds to explain this to someone, what would you say?"
2. "Who is this for? Describe the person who would use this. What's their day like? What frustrates them?"
3. "What's the #1 problem this solves for them? What are they doing today without your product?"
4. "What does success look like? If this works perfectly, what changes for your users?"
5. "What's the simplest version that would be useful? If you could only ship 3 features, which 3?"

**Follow-up questions (ask as needed based on their answers):**

- "You mentioned [X]. Can you give me an example of how that would actually work from the user's perspective?"
- "What happens if [edge case]? For example, what if someone has no data yet, or enters something unexpected?"
- "Is there anything you've seen in another product that's close to what you want? What did they get right? What did they get wrong?"
- "What should this absolutely NOT do? Sometimes knowing what's out of scope is as important as knowing what's in scope."

**When you have enough context** (usually 5-10 questions), say:
> "I think I have a good picture of what you're building. Let me draft the requirements document section by section. I'll show you each part so you can tell me if I'm on track."

### The 13-Section PRD Framework

Draft each section based on the discovery conversation. Present each section to the user for approval before moving on. Scale each section to its complexity — a few sentences if straightforward, a full paragraph if nuanced.

**Section 1: Overview**
- Product name, one-line description, target launch date
- Should be scannable in 5 seconds

**Section 2: Problem Statement**
- What problem, who has it, why now
- Be specific — "people waste time on X" is vague. "Remote teams spend 5+ hours/week on manual task triage" is specific.
- Help the user articulate this. Ask: "Can you estimate how much time/money/frustration this problem costs?"

**Section 3: Target Users**
- 2-3 personas with: role, behaviors, pain points, current tools, willingness to pay
- Claude drafts these from the user's descriptions, user approves
- Ask: "If I described your ideal customer, would you tell me if I'm getting it right?"

**Section 4: Goals & Success Metrics**
- Measurable KPIs with Month 1 and Month 6 targets
- Claude suggests metrics based on the product type, user approves
- Explain each metric: "WAU means Weekly Active Users — how many people use your product in a given week. This tells us if people are coming back, not just signing up and disappearing."

**Section 5: User Stories**
- 8-12 stories in "As a [user], I want [action], so that [benefit]" format
- Each must be testable — you can write acceptance criteria proving it works
- Claude drafts these from the discovery conversation, user reviews

**Section 6: Functional Requirements (CRITICAL)**
- Prioritized feature list using three tiers:
  - **P0 (Must-have for MVP)** — ship or die. The product is useless without these.
  - **P1 (Should-have for v1)** — needed for a credible first version, but MVP can launch without them.
  - **P2 (Nice-to-have for v1.x)** — delighters that can wait. Don't even think about these until P0 and P1 are done.
- Explain to user: "Without these tiers, we'll try to build everything at once and finish nothing. P0 is what we build first. Everything else waits."

**Section 7: Non-Functional Requirements**
- Performance, security, scalability, accessibility
- Claude suggests sensible defaults for the product type
- Explain in business terms:
  - Performance: "Pages should load in under 2 seconds. After that, people leave."
  - Security: "User data encrypted, passwords hashed. Think of it like putting your customers' data in a safe vs. leaving it on the counter."
  - Accessibility: "Can someone using a screen reader use your product? This isn't just nice — it's legally required in many cases."

**Section 8: Technical Considerations**
- Recommended stack, APIs, database, hosting
- **This section requires real back-and-forth.** For each technology choice, explain:

| What to Cover | Example |
|---------------|---------|
| **What it is** | "Supabase is a database + authentication service. Think of it as the filing cabinet and security guard for your app, bundled together." |
| **Why this one** | "It has a generous free tier (up to 50,000 monthly active users for free), built-in auth so we don't have to build login from scratch, and it uses standard SQL so we're not locked into their proprietary system." |
| **What it costs** | "Free for development and small apps. $25/month once you hit the Pro tier. The paid API for [X] costs approximately $0.002 per call — at your expected volume that's about $15/month." |
| **Maintenance burden** | "This is widely used (100k+ projects). If a future developer takes over, they'll likely know it already. Compare this to [obscure alternative] where finding help would be harder." |
| **Alternatives considered** | "We could also use Firebase (Google's version) — it's similarly priced but uses a non-standard query language that makes switching harder later." |
| **Codespace vs. local** | "This runs fine in a GitHub Codespace, which gives you a more powerful machine than your local Windows setup and avoids 'it works on my machine' headaches." |

- **Use Context7 MCP** to fetch latest documentation for every recommended library. Don't guess at current pricing or features.
- Ask the user after presenting options: "Do any of these feel like the wrong call? Any budget constraints I should know about?"

**Section 9: UI/UX Requirements**
- Key screens, user flows, design system
- Describe the visual system in words (Claude works better with words than images)
- Offer the visual companion for mockup questions
- Ask: "Are there any apps or websites whose look-and-feel you like? That helps me understand your taste."

**Section 10: Out of Scope**
- Explicitly state what this version does NOT include
- This prevents scope creep — Claude will happily build features you never asked for if you don't tell it to stop
- Ask: "Is there anything people might expect this to do that you explicitly don't want to build yet?"

**Section 11: Timeline & Milestones**
- Break delivery into phases with rough estimates
- This becomes the basis for numbered module specs
- Each phase should produce something testable and demoable

**Section 12: Risks & Mitigations**
- What could go wrong and contingency plans
- Claude proactively raises risks the user wouldn't think of:
  - "What if the API you depend on changes its pricing?"
  - "What if 1000 people sign up on day one — can the free tier handle that?"
  - "What happens to user data if you decide to shut this down?"

**Section 13: Open Questions**
- Unresolved decisions listed honestly
- It's OK to not have all the answers. Better to flag them now than discover them mid-build.
- "These are decisions we don't need to make today, but we'll need to make before we launch. I'll flag them when they become relevant."

**Section 14: Change Log** (initialized empty)
```markdown
## Change Log
| Date | Change | Level | Why | Specs Affected |
|------|--------|-------|-----|----------------|
```
- This stays at the bottom of the PRD and gets updated whenever a module pivot or product pivot happens (see Change Management section)

### After the PRD

**Save the PRD:**
- Write to `docs/prd.md`
- Commit to git

**PRD Review Loop:**
1. Dispatch spec-document-reviewer subagent (see spec-document-reviewer-prompt.md) — provide the PRD path
2. If Issues Found: fix, re-dispatch, repeat until Approved (max 5 iterations)
3. If loop exceeds 5 iterations, surface to human for guidance

**User Review Gate:**
> "PRD written and committed to `docs/prd.md`. Please review it and let me know if you want to make any changes before we break it into module specs."

Wait for the user's response. If they request changes, make them and re-run the review loop.

**Break Into Module Specs:**
Using the Timeline & Milestones (Section 11) and Functional Requirements (Section 6), create numbered module specs:

- `docs/specs/00_<first-module>.md` — typically foundation (database, auth, project setup)
- `docs/specs/01_<second-module>.md` — core feature #1
- `docs/specs/02_<third-module>.md` — core feature #2
- etc.

Each module spec is a brief outline (not a full design yet) containing:
- What this module covers (which user stories, which P0/P1 features)
- Dependencies on other modules
- Rough scope

**Initialize Tracking Files:**

Create `docs/progress.md`:
```markdown
# Project Progress

## Spec Status
| # | Spec | Status | Started | Completed | Notes |
|---|------|--------|---------|-----------|-------|
| 00 | <module-name> | pending | | | |
| 01 | <module-name> | pending | | | |

## Session Log
| Date | What was done | Spec(s) touched |
|------|---------------|-----------------|
```

Create `docs/decisions.md`:
```markdown
# Decision Log
| Date | Decision | Options Considered | Why This Option | Decided By |
|------|----------|-------------------|-----------------|------------|
```

Log all tech stack decisions from Section 8 into `docs/decisions.md` immediately.

**Transition — depends on project type:**

For **Full Product** projects (determined in Step 0):
> "PRD is complete. Since this is a complex system with multiple architectural layers, the next step is a System Design document that maps out how all the pieces fit together under the hood. Then we'll break it into module specs and build one at a time."

Proceed to **System Design Mode** below.

For **Focused Product** projects:
> "PRD is complete. I've broken it into [N] module specs. Let's start with module 00: [name]. I'm going to switch to design mode for this specific module."

Skip System Design Mode and re-invoke brainstorming — it will enter Spec Mode since a PRD now exists.

---

# SYSTEM DESIGN MODE

## For: Full Product projects where the architecture has multiple layers, agents, caches, databases, or other infrastructure beyond the user-facing features

The PRD captures WHAT we're building and WHY. The System Design document captures HOW the system works under the hood. This is the document that a new engineer (or a new Claude session) would read to understand the architecture — how data flows, what each layer does, where the boundaries are.

**When to use this mode:**
- The project was classified as a "Full Product" in Step 0
- The user provided an architecture diagram
- The PRD's tech section touches 3+ infrastructure concerns (database, caching, orchestration, agents, etc.)
- The user explicitly asks for a system design document

**When to skip this mode:**
- Focused Products — fold architecture decisions into the PRD's tech section
- Feature/Module work — the system design already exists (or isn't needed)

### System Design Checklist

1. **Read the PRD** — the system design must serve the PRD's requirements, not exist in the abstract
2. **Inventory all architectural layers** — from user input to data storage. If the user provided a diagram, EVERY layer must be addressed.
3. **For each layer, document:**
   - What it does (in plain language)
   - What technology/tool is chosen and why
   - What ships in MVP vs. v1 vs. v2 (with reasoning for deferral)
   - How it connects to adjacent layers (data flow)
   - What could go wrong and how we handle it
4. **Create a roadmap table** — one row per layer, columns for MVP/v1/v2 showing what ships when
5. **Document cross-cutting concerns:**
   - Observability/logging — how do we know what the system is doing?
   - Error handling — what happens when a layer fails?
   - Security — authentication, authorization, data protection
   - Cost — what's free, what costs money, at what scale?
6. **Present to user** — section by section, get approval
7. **Write to `docs/system-design.md`**
8. **User reviews** — ask for approval before proceeding to specs

### System Design Document Structure

```markdown
# [Project Name] — System Design

## Overview
One paragraph: what this system does and the key architectural principles.

## Architecture Layers
For each layer:
### Layer N: [Name]
- **Purpose:** What it does in plain language
- **Technology:** What we're using and why
- **MVP scope:** What ships first
- **V1/V2 scope:** What comes later and why
- **Connections:** What it talks to and how
- **Failure modes:** What can go wrong and how we handle it

## Roadmap Table
| Layer | MVP | V1 | V2 |
|-------|-----|----|----|

## Cross-Cutting Concerns
### Observability
### Error Handling
### Security
### Cost Projections

## Open Questions
```

### After the System Design

**Break Into Module Specs:**
Using the System Design layers and PRD's Functional Requirements, create numbered module specs:

- `docs/specs/00_<first-module>.md` — typically foundation (database, schema, project setup)
- `docs/specs/01_<second-module>.md` — core feature #1
- etc.

Each module spec is a brief outline (not a full design yet) containing:
- What this module covers (which user stories, which architectural layers)
- Dependencies on other modules
- Rough scope

**Transition to first module:**
> "System design is complete. I've broken the project into [N] module specs. Let's start with module 00: [name]. I'm going to switch to design mode for this specific module."

Then re-invoke brainstorming — it will enter Spec Mode.

---

# SPEC MODE

## For: Individual modules, features, small projects, work within existing projects

This is the detailed design for a single piece of work. If a PRD exists, this designs one module from it. If no PRD exists (small project/feature), this designs the whole thing.

### Spec Checklist

You MUST create a task for each of these items and complete them in order:

1. **Explore project context** — check files, docs, recent commits
2. **Offer visual companion** (if topic will involve visual questions) — this is its own message, not combined with a clarifying question. See the Visual Companion section below.
3. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
4. **Propose 2-3 approaches** — with trade-offs and your recommendation
5. **Present design** — in sections scaled to their complexity, get user approval after each section
6. **Write spec doc** — save to `docs/specs/YYYY-MM-DD-<topic>-design.md` (or update the numbered module spec if working from a PRD) and commit
7. **Spec review loop** — dispatch spec-document-reviewer subagent with precisely crafted review context (never your session history); fix issues and re-dispatch until approved (max 5 iterations, then surface to human)
8. **User reviews written spec** — ask user to review the spec file before proceeding
9. **Transition to implementation** — invoke writing-plans skill to create implementation plan

### Process Flow

```dot
digraph brainstorming {
    "Explore project context" [shape=box];
    "Visual questions ahead?" [shape=diamond];
    "Offer Visual Companion\n(own message, no other content)" [shape=box];
    "Ask clarifying questions" [shape=box];
    "Propose 2-3 approaches" [shape=box];
    "Present design sections" [shape=box];
    "User approves design?" [shape=diamond];
    "Write spec doc" [shape=box];
    "Spec review loop" [shape=box];
    "Spec review passed?" [shape=diamond];
    "User reviews spec?" [shape=diamond];
    "Invoke writing-plans skill" [shape=doublecircle];

    "Explore project context" -> "Visual questions ahead?";
    "Visual questions ahead?" -> "Offer Visual Companion\n(own message, no other content)" [label="yes"];
    "Visual questions ahead?" -> "Ask clarifying questions" [label="no"];
    "Offer Visual Companion\n(own message, no other content)" -> "Ask clarifying questions";
    "Ask clarifying questions" -> "Propose 2-3 approaches";
    "Propose 2-3 approaches" -> "Present design sections";
    "Present design sections" -> "User approves design?";
    "User approves design?" -> "Present design sections" [label="no, revise"];
    "User approves design?" -> "Write spec doc" [label="yes"];
    "Write spec doc" -> "Spec review loop";
    "Spec review loop" -> "Spec review passed?";
    "Spec review passed?" -> "Spec review loop" [label="issues found,\nfix and re-dispatch"];
    "Spec review passed?" -> "User reviews spec?" [label="approved"];
    "User reviews spec?" -> "Write spec doc" [label="changes requested"];
    "User reviews spec?" -> "Invoke writing-plans skill" [label="approved"];
}
```

**The terminal state is invoking writing-plans.** Do NOT invoke frontend-design, mcp-builder, or any other implementation skill. The ONLY skill you invoke after brainstorming is writing-plans.

### The Process

**Understanding the idea:**

- Check out the current project state first (files, docs, recent commits)
- If working from a PRD, read the relevant module spec and the PRD for context
- Ask questions one at a time to refine the design
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message — if a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**

- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why
- For every technical tradeoff, explain it in business terms:
  - Cost: "Option A is free. Option B costs ~$20/month but handles 10x the traffic."
  - Complexity: "Option A is simpler — a future developer could understand it in an afternoon. Option B is more powerful but would take a week to understand."
  - Risk: "Option A is the safe bet. Option B is faster but if it breaks, debugging is harder."

**Presenting the design:**

- Once you believe you understand what you're building, present the design
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

**Confirmation before writing:**

Once all sections are approved, present a summary:
> "Here's what I'm going to write into the spec: [brief summary]. Does this capture everything, or did I miss something?"

Only after this confirmation, write the spec document.

**Design for isolation and clarity:**

- Break the system into smaller units that each have one clear purpose, communicate through well-defined interfaces, and can be understood and tested independently
- For each unit, you should be able to answer: what does it do, how do you use it, and what does it depend on?
- Can someone understand what a unit does without reading its internals? Can you change the internals without breaking consumers? If not, the boundaries need work.
- Smaller, well-bounded units are also easier for you to work with — you reason better about code you can hold in context at once, and your edits are more reliable when files are focused. When a file grows large, that's often a signal that it's doing too much.

**Working in existing codebases:**

- Explore the current structure before proposing changes. Follow existing patterns.
- Where existing code has problems that affect the work (e.g., a file that's grown too large, unclear boundaries, tangled responsibilities), include targeted improvements as part of the design — the way a good developer improves code they're working in.
- Don't propose unrelated refactoring. Stay focused on what serves the current goal.

### After the Design

**Documentation:**

- Write the validated design (spec) to `docs/specs/YYYY-MM-DD-<topic>-design.md`
  - If working from a PRD module spec, update the numbered file (e.g., `docs/specs/00_database-schema.md`) with the full design
  - (User preferences for spec location override this default)
- Use elements-of-style:writing-clearly-and-concisely skill if available
- Commit the design document to git

**Spec Review Loop:**
After writing the spec document:

1. Dispatch spec-document-reviewer subagent (see spec-document-reviewer-prompt.md)
2. If Issues Found: fix, re-dispatch, repeat until Approved
3. If loop exceeds 5 iterations, surface to human for guidance

**User Review Gate:**
After the spec review loop passes, ask the user to review the written spec before proceeding:

> "Spec written and committed to `<path>`. Please review it and let me know if you want to make any changes before we start writing out the implementation plan."

Wait for the user's response. If they request changes, make them and re-run the spec review loop. Only proceed once the user approves.

**Implementation:**

- Invoke the writing-plans skill to create a detailed implementation plan
- Do NOT invoke any other skill. writing-plans is the next step.

---

# CHANGE MANAGEMENT

## When Things Change Mid-Project

Changes will happen. You'll discover something while building Module 02 that changes how Module 04 should work. A user will give you feedback that reshapes the product. You'll realize a feature isn't needed. This is normal — the PRD is a living document, not a contract carved in stone.

**Trigger this protocol when the user says things like:**
- "Actually, let's change..."
- "I want to pivot / rethink / drop / add..."
- "This module taught me that we should..."
- "Can we switch from X to Y?"
- "I don't think we need [feature] anymore"
- Or when YOU notice during implementation that the current plan conflicts with reality

### Three Levels of Change

Walk the user through identifying which level this is:

| Level | Signal | Example | What to Update |
|-------|--------|---------|----------------|
| **Tweak** (Spec-only) | Changes how one module works, but doesn't affect anything else | "Use a dropdown instead of radio buttons" | Update that module's spec only |
| **Module pivot** (Spec + PRD) | Changes a module's approach in a way that other modules might reference | "Auth should use magic links, not passwords" | Update the spec AND the relevant PRD sections. Check if other specs reference the old approach. |
| **Product pivot** (PRD-first, then ripple) | Adds, removes, or fundamentally changes a capability | "Drop the billing module" or "We need real-time chat" | Update the PRD first. Then update progress.md. Then check ALL remaining specs for ripple effects. |

> "It sounds like this is a [tweak / module pivot / product pivot]. Here's what I think we need to update: [list]. Does that sound right?"

### The Change Protocol

**For tweaks:**
1. Update the affected spec
2. Note the change in `docs/decisions.md` with reasoning
3. Continue building

**For module pivots:**
1. Update the affected spec
2. Update the relevant PRD sections (Functional Requirements, Technical Considerations, or whatever changed)
3. Search all other specs for references to the old approach — flag any that need updating
4. Note the change in `docs/decisions.md`
5. Update `docs/progress.md` if timelines or dependencies changed
6. Present a summary: "Here's what changed and what it affects: [list]. Ready to continue?"

**For product pivots:**
1. **Update the PRD first** — this is the source of truth. Changes flow downward from the PRD, never upward from specs.
2. Add an entry to the **Change Log** at the bottom of the PRD (see below)
3. Update `docs/progress.md`:
   - Mark cancelled specs as `cancelled` with a reason
   - Add new specs if capabilities were added
   - Update dependencies if the build order changed
4. For **specs not yet built**: update them to reflect the new reality
5. For **specs already completed**: add a note about what changed and whether rework is needed. Flag rework items in progress.md.
6. Update `docs/decisions.md`
7. Present a full impact summary: "Here's everything that changed: [PRD sections, specs affected, rework needed]. Want to review any of these before we continue?"

### PRD Change Log

Add this section to the bottom of every PRD (the project-kickoff process initializes it):

```markdown
## Change Log
| Date | Change | Level | Why | Specs Affected |
|------|--------|-------|-----|----------------|
```

Every module pivot or product pivot gets logged here. This creates a history of how the product evolved — invaluable for understanding why things are the way they are.

### Key Principle: PRD Is Always Current

The PRD should always reflect **what we're building NOW**, not what we originally planned. If someone reads the PRD cold (like a new Claude session), they should get an accurate picture of the current product — not a historical one. The Change Log at the bottom provides the history.

---

## Shared: Key Principles

- **One question at a time** — Don't overwhelm with multiple questions
- **Multiple choice preferred** — Easier to answer than open-ended when possible
- **YAGNI ruthlessly** — Remove unnecessary features from all designs
- **Explore alternatives** — Always propose 2-3 approaches before settling
- **Incremental validation** — Present design, get approval before moving on
- **Be flexible** — Go back and clarify when something doesn't make sense
- **Explain like a business advisor** — Cost, risk, maintenance burden, not just technical merits
- **Use Context7** — For any library/framework recommendation, fetch latest docs first. Don't guess at pricing or features.

## Shared: Visual Companion

A browser-based companion for showing mockups, diagrams, and visual options during brainstorming. Available as a tool — not a mode. Accepting the companion means it's available for questions that benefit from visual treatment; it does NOT mean every question goes through the browser.

**Offering the companion:** When you anticipate that upcoming questions will involve visual content (mockups, layouts, diagrams), offer it once for consent:
> "Some of what we're working on might be easier to explain if I can show it to you in a web browser. I can put together mockups, diagrams, comparisons, and other visuals as we go. This feature is still new and can be token-intensive. Want to try it? (Requires opening a local URL)"

**This offer MUST be its own message.** Do not combine it with clarifying questions, context summaries, or any other content. The message should contain ONLY the offer above and nothing else. Wait for the user's response before continuing. If they decline, proceed with text-only brainstorming.

**Per-question decision:** Even after the user accepts, decide FOR EACH QUESTION whether to use the browser or the terminal. The test: **would the user understand this better by seeing it than reading it?**

- **Use the browser** for content that IS visual — mockups, wireframes, layout comparisons, architecture diagrams, side-by-side visual designs
- **Use the terminal** for content that is text — requirements questions, conceptual choices, tradeoff lists, A/B/C/D text options, scope decisions

A question about a UI topic is not automatically a visual question. "What does personality mean in this context?" is a conceptual question — use the terminal. "Which wizard layout works better?" is a visual question — use the browser.

If they agree to the companion, read the detailed guide before proceeding:
`skills/brainstorming/visual-companion.md`
