---
name: slideforge-new-chart
description: Add a new chart OR table type to the SlideForge library from a screenshot + a name. Use when Lyndsay says "add a new chart", "add a table", or shows a screenshot of a chart/table she wants in the library. Always ends with a four-layout visual sign-off — never claim done before she's approved all four screenshots.
---

# slideforge-new-chart

## When to use

- User asks to add a new chart or table type
- User shows a chart screenshot and wants it in the SlideForge library
- User says things like "I need a stock chart in there" or "we need a TAM table"

Do NOT use for: editing an existing chart, theming, layout fixes.

## Acceptance criteria — every new chart/table MUST end with

1. ✓ Recipe file committed at `library/charts/<id>.json` or `library/tables/<id>.json`
2. ✓ `aliases` populated with finance/jargon names Lyndsay confirms by name (NEVER guess; ASK)
3. ✓ `npm run build:catalog` run successfully
4. ✓ `npm run chart-qa -- --id <id>` run; four PNGs generated
5. ✓ Lyndsay's explicit sign-off on all four renders
6. ✓ Committed to a branch (per CLAUDE.md "commit early and often" rule)

Do not claim the chart is shipped until all six are checked.

## Workflow

### 1. Examine the screenshot
Identify the chart family. For charts, families currently in code: see `apps/api/src/lib/chart-scaffolds/`. For tables: same folder, `--type table`. If the family is unfamiliar, treat it as new and go to step 2. Otherwise, skip to step 3.

### 2. Build the family scaffold (only for NEW families)
The trigger that tells you this step is needed: running `new-chart.mjs` in step 4 exits with code 2 and points you at `apps/api/src/lib/chart-scaffolds/README.md`. That's the expected error — go build the scaffold now.

- Open `apps/api/src/lib/chart-scaffolds/README.md` and follow the "How to add one" steps.
- Create `<family>.scaffold.ts` capturing: family-level appetite (minSlot, preferredSlot, legend/label/column pressure), the ECharts chart type + base options (for charts) or column-default shape (for tables), all with `${tokens.X}` placeholders.
- Register it in `index.ts`.
- Touch NOTHING about colors, slot positions, or legend placement.
- Commit the scaffold as its own commit before moving on.

### 3. Ask Lyndsay for the firm aliases
Phrase: "What does the firm call this chart? Any nicknames I should add to `aliases`?" Wait for her answer. Do NOT invent names. Do NOT use LLM-generated terms like "hero" unless she confirms them.

### 4. Run `new-chart`
Run via Bash on her behalf:
```
node apps/api/scripts/new-chart.mjs \
  --family <family> \
  --id <id> \
  --type <chart|table> \
  --name "<name>" \
  --description "<one-line>" \
  --category <category> \
  --aliases "<comma,separated,list>"
```

### 5. Fill the variable bits
Open the new recipe file and fill any blanks the scaffold left (data-field names, supported_cases, table columns, etc.).

### 6. Build the catalog
Run: `cd apps/api && npm run build:catalog`

### 7. Run the QA harness
Run: `node apps/api/scripts/chart-qa.mjs --id <id>` (or, equivalently, `npm run chart-qa -- --id <id>` from `apps/api`). That's the full CLI surface for the typical case — no other args needed; the harness drives the deck-client `/qa` route (which accepts a base64-encoded DeckSpec via URL hash, added in Task 10) across all four archetypes and dumps PNGs.

### 8. Present the four screenshots inline
Use Read tool on each PNG and embed in your reply. Group them with clear labels: "Full-page", "Quadrant", "Vertical 2-up", "Side-by-side 2-up". Ask her to sign off OR list specific layout fixes.

### 9. If she requests fixes
Most fixes are appetite tweaks (chart needs more room → bump `minSlot.w` or `preferredSlot.w` in the recipe). Some are scaffold-level (every chart in this family is too cramped → bump the scaffold). Decide which level the fix belongs at; explain briefly; apply; re-run the harness; re-present.

### 10. Sign-off and commit
Once Lyndsay says all four look good, commit:
```
git add library/<charts|tables>/<id>.json apps/api/src/lib/chart-scaffolds/<family>.scaffold.ts apps/api/src/lib/chart-scaffolds/index.ts
git commit -m "feat(library): add <id> (<name>) to the <chart|table> library

Aliases: <list>. Visually QA'd in 4 archetypes by Lyndsay <date>."
```

## What this skill must NOT do

- ❌ Run terminal commands without using the Bash tool on Lyndsay's behalf (she does not use the terminal)
- ❌ Guess or LLM-generate aliases
- ❌ Skip any of the four QA renders
- ❌ Mark the chart shipped before her explicit sign-off
- ❌ Touch colors, palettes, theme tokens, or legend positions in the recipe
- ❌ Bypass the scaffold step ("just write the JSON directly") — even for one-offs

## Common pitfalls

- **Chart paints blank in QA screenshot.** See `slideforge-deck-client-webdriver-blank-chart` memory: the harness already overrides `navigator.webdriver`. If it still happens, the chart's `data-rendered="true"` signal may not be firing.
- **Catalog doesn't see the new recipe.** Did you run `npm run build:catalog`? Restart the MCP server too (stdio MCP loads at session start per `mcp-stdio-restart-required-for-code-changes` memory).
- **Scaffold doesn't exist for the family.** That's the expected error — `new-chart.mjs` exits with code 2 and points you at `apps/api/src/lib/chart-scaffolds/README.md`. Go build the scaffold (step 2). Don't work around it by writing the JSON by hand.
