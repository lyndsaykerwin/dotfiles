---
name: slideforge-data-survey
description: >-
  Survey a messy or huge Excel/CSV diligence model and hand SlideForge the exact
  clean column-array JSON its charts and tables need. Use this WHENEVER you have
  a real workbook (financial model, ARR/MRR detail, TAM build, returns model, KPI
  export, board pack spreadsheet) and want to turn some of its numbers into a
  SlideForge chart, table, or slide — especially when the file is large, has many
  sheets, banner/merged headers, or summary blocks, and you're tempted to give up
  and hand-build the slide yourself. Triggers: "make a chart from this xlsx",
  "build a SlideForge slide off this model", "I have a workbook, chart the
  bookings/revenue/TAM/retention", "pull these figures into a deck", or any time a
  SlideForge generate is blocked because you can't see which columns hold the
  data. Always prefer this over eyeballing a workbook or falling back to
  python-pptx / by-hand extraction.
---

# SlideForge data survey

## Why this exists

When you have a clean, tidy little table you can read the numbers yourself and
call `slideforge_generate`. The problem this skill solves is the *other* case:
a real diligence model — dozens of sheets, a banner row before the headers,
merged cells, summary/total blocks, time-series running across 80 columns. In
that situation agents tend to either (a) drown in the workbook, or (b) bail out
and build the slide by hand with python-pptx, which throws away everything
SlideForge gives you. Neither is acceptable.

The fix is a disciplined hand-off: figure out **exactly which fields the target
chart needs**, **survey the workbook** to find where those numbers live, **confirm
with the user once**, then hand `slideforge_generate` a clean payload. You do the
messy extraction (you're good at it); the product stays in charge of the slide.

## The loop

```
1. Pin the target template   → get its required data fields (the shopping list)
2. Survey the workbook       → scripts/survey.py  (two-pass, handles huge files)
3. Map columns → fields      → you, reading the profile + samples
4. Confirm once              → ONE AskUserQuestion with the sheet/cols/sample rows
5. Assemble the payload      → slide.data[data_key] + a source_footer provenance line
6. Generate                  → slideforge_generate
```

Do them in order. Step 4 is not optional — the survey produces *hypotheses*, and
a confidently-wrong chart in a diligence deck is worse than a slow one.

---

## Step 1 — Pin the target template and read its required fields

The shopping list is **the chart/table's own schema**, never a hardcoded set of
columns. Find it via `slideforge_list_capabilities`:

- If you already know the template id (e.g. `revenue_history_bars`,
  `arr_waterfall`, `tam_analysis`), pass `filter.chart_template_id=<id>` (or the
  table equivalent) to get just that schema.
- If you don't, call `slideforge_list_capabilities` with
  `include:['chart_templates']` (add `'table_templates'`) and pick the template
  whose shape matches the user's intent.

Read the template's `data_schema`. That JSON Schema tells you the **field names**
and **types** the payload must contain. Those field names are your shopping list.

## Step 2 — Survey the workbook

```bash
python3 scripts/survey.py "<path-to-file.xlsx>"          # JSON (default — use this)
python3 scripts/survey.py "<path-to-file.xlsx>" --text   # human-readable, for your own eyes
```

It accepts `.xlsx`, `.xlsm`, and `.csv`. It reads in streaming/read-only mode, so
a multi-megabyte, many-sheet model surveys in well under a second without loading
the whole grid into memory.

What it returns (per the top 1–2 sheets it judges most data-like):

- `header_row` — the detected header row (banner/title rows above it are skipped).
- `columns[]` — for every column: `col_letter`, `header_label`, `dtype`
  (`number` / `text` / `date` / `bool`), `n_nonempty`, up to 5 `samples`,
  `numeric_range` (min/max), and `has_negative`.
- `role_hints` — `category_columns` (good x-axis / row labels — text or period
  labels like FY24, Q1'25, Jan-25) and `numeric_columns` (series values).
- `sample_rows` — the first few full data rows, so you can eyeball real records.
- `skipped_sheets` — sheets the two-pass scorer set aside (with the reason), and
  `near_tie` if a runner-up sheet scored close and you should look at both.

If the sheet you actually want was skipped, just re-run pointing at it — open the
file and call the profiler on the named sheet, or tell the user which sheet you
expected and ask. Don't force a mapping onto the wrong sheet.

## Step 3 — Map columns onto the chart's fields

Read the `samples` and `numeric_range` to decide which column feeds which field.
Common shapes (confirm the exact field names against the schema from Step 1):

- **Category/x-axis field** (`years`, `periods`, `quarters`, `categories`,
  `labels`) ← a `category_columns` entry, OR the `header_label`s of a row of
  date/period columns when the model runs time across columns (transposed). When
  the model is transposed (metrics down rows, dates across), you read values
  *along a row* and the period labels *from the header* — survey reports both.
- **Numeric series fields** (`revenue`, `gross_profit`, `grr`, `nrr`, `values`,
  `base`/`deltas`) ← `numeric_columns`. Match by `header_label` and by sanity-
  checking `numeric_range` (e.g. a % series sits ~0–130; a $M series is bigger).
- **Series labels** — if the template supports `series_names`, set them from the
  source column headers so the legend reads "Revenue ($M)", not "Series 1".

**Negatives are ordinary numbers.** Churn, contraction, net-cash drawdowns — pass
them straight through with their sign. `has_negative` is just a flag so you notice
them, not a problem to fix.

**Units & the 1-decimal $ rule.** SlideForge expects clean display numbers. If the
model stores raw dollars (e.g. `1582660.46`) and the chart is in `$M`, convert
(÷1,000,000) and round to one decimal before putting it in the payload. Don't ship
14-digit floats. Keep percentages as the chart expects (the schema or template
description says whether it wants `94` or `0.94`).

## Step 4 — Confirm once, with samples

Before you trust the mapping, show the user what you found in **one**
`AskUserQuestion`. Give them enough to catch a wrong-sheet / wrong-column mistake:

- the workbook + sheet you read,
- the columns you picked for each chart field, with a couple of sample values,
- and let them confirm or correct.

Keep it to a single question with clear options (e.g. "Use Sheet 'Summary',
Revenue=col B, Gross Profit=col C?" vs. "Let me pick different columns"). This is
the cheap insurance that makes the hand-off trustworthy.

## Step 5 — Assemble the payload + provenance

Build the object SlideForge expects under `slide.data[<data_key>]`, where
`data_key` is the chart slot's `data_key` (defaults to its `slot_id`). Shapes
vary **per template** — always match the Step 1 schema. Reference shapes:

**Grouped/stacked bars** (`revenue_history_bars`):
```json
{ "years": ["FY21","FY22","FY23","FY24","FY25"],
  "revenue": [38,54,73,94,118],
  "gross_profit": [28,41,56,73,93],
  "series_names": ["Revenue ($M)","Gross Profit ($M)"] }
```

**Retention / line** (`retention_line_hero`):
```json
{ "periods": ["FY22","FY23","FY24","FY25"],
  "grr": [90,92,93,94], "nrr": [110,115,119,122], "logo": [86,88,89,90] }
```

**Pie / donut** (`revenue_mix_donut`) — give `labels`+`values`; the client builds
the slices:
```json
{ "labels": ["Recurring","Re-occurring","Non-recurring"], "values": [82,11,7] }
```

**Waterfall** (`arr_waterfall`):
```json
{ "categories": ["Starting ARR","New","Expansion","Churn","Contraction","Ending ARR"],
  "base":   [0,42,51,53,51.5,0],
  "deltas": [42,9,4,3,1.5,50.5],
  "kinds":  ["total","gain","gain","loss","loss","total"],
  "value_labels": ["$42M","+$9M","+$4M","-$3M","-$1.5M","$50.5M"] }
```

**Table** (`tam_analysis` and other table templates) — a `rows` array of objects
keyed by the template's column `key`s:
```json
{ "rows": [
    { "segment": "State Workforce & Labor", "entities": 54, "acv_k": 750, "pct_addressable": 0.65, "tam_m": 26.3 },
    { "segment": "Non-profits & Education", "entities": 8200, "acv_k": 40, "pct_addressable": 0.30, "tam_m": 98.4 } ] }
```

**Provenance — always set `source_footer`.** Build a one-line string that says
where the numbers came from, so the slide is self-documenting and auditable:

```
Source: <workbook filename> · sheet '<sheet name>' · <row/col description> · as of <date if known>
```
e.g. `Source: Launchpad - Financial model.xlsx · sheet 'Summary' · ARR & GDR rows, FY21–FY26 · as of Apr 2026`.

Leave `takeaway` unset (it renders the editable `[Insert key takeaway]`
placeholder) unless the user gave you a specific caption — don't invent a
takeaway from the data.

## Step 6 — Generate

Call `slideforge_generate` with the slide spec: the `chart_slots[]` (each with
`slot_id`, `chart_template_id`/`table_template_id`, and `data_key`), the assembled
`data` object keyed by those `data_key`s, your `source_footer`, and `mode='deck'`
(you have real data). Then `slideforge_inspect` to confirm the slide rendered with
a real `template_id` and positions before you call it done.

---

## Worked example (transposed financial model → bars)

A "Summary" sheet has metric names down column A and one column per period across
the top (`2021-12-31`, `2022-12-31`, …), values in raw dollars.

1. Target = `revenue_history_bars`; schema wants `years`, `revenue`,
   `gross_profit`.
2. `survey.py` reports header row 3, category col A (metric names), numeric cols
   B…G with date `header_label`s; you spot the "Revenue" and "Gross profit" rows
   in the `samples`.
3. Map: `years` = the period `header_label`s (B…G), `revenue` = the Revenue row's
   values across B…G (÷1e6, 1-dp), `gross_profit` = the Gross profit row likewise.
4. Confirm: "Revenue from row 'Total revenue', Gross profit from row 'Gross
   profit', periods FY21–FY26 — right?"
5. Payload as the bars shape above; `source_footer` cites sheet 'Summary'.
6. Generate → inspect.

## Quick checks

- `python3 scripts/survey.py --self-test` — verifies the engine end-to-end
  (banner-row skipping, type detection, two-pass sheet selection, negatives).
- If the file is a `.csv`, the same command works; if it's neither xlsx nor csv,
  convert first.
