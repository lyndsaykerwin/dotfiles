# Handoff: genuine two-sheet workbook path (deferred item "#4a")

**Status:** NOT implemented. Deferred on purpose — we fixed the documentation to
match current behavior instead, and queued the code change for after a live test.
**Owner of decision:** Lyndsay. Do not start until she confirms the live test is done.

---

## The problem this solves

Today `deliver.py` runs in one of three modes (see `deliver()` in
`scripts/deliver.py`):

| Mode | Trigger | Sheets built |
|------|---------|--------------|
| `aggregating` | source workbook **+** `--source-type-col` | 3 (Corkscrew, Raw Data with Analysis, Raw Data) |
| `passthrough` | source workbook, no type col | **3** (helper is a 1:1 mirror) |
| `twotab` | no source workbook (tidy CSV only) | 2 (Corkscrew, Raw Data) |

The complaint: in `passthrough`, when the source is **already one clean row per
customer in a contiguous block**, the "Raw Data with Analysis" helper *transforms
nothing* — it's a 1:1 mirror — yet we still ship a third sheet. The Corkscrew's
`SUMPRODUCT`s could point straight at `'Raw Data'!<col>$<first>:<col>$<last>`.

**Goal:** add a genuine **two-sheet** deliverable (Corkscrew → Raw Data directly)
for the clean-contiguous-block case, so we don't ship a redundant helper.

---

## Why it's non-trivial (read before estimating)

The helper isn't pure waste — it does one real job even in pass-through mode: it
**normalizes the source's arbitrary layout into a fixed canonical grid** that the
Corkscrew formulas hard-code against. Specifically, `write_corkscrew_sheet_aggregating()`
assumes the sheet it references has:

- customer rows starting at `ANALYSIS_FIRST_CUST_ROW = 12`,
- month columns starting at `ANALYSIS_FIRST_MONTH_COL = 2` (col B),
- a `# Active` summary row at row 2 and a `# Retained` row at row 3, which the
  Corkscrew customer-count cells reach via `HLOOKUP`.

Raw Data (a verbatim source copy) has **none** of that guaranteed geometry — its
customer column, first data row, and first date column are wherever the source
put them (`source_customer_col`, `source_first_data_row`, `source_first_date_col`),
and it has **no** pre-computed active/retained summary rows.

So pointing the Corkscrew at Raw Data directly means re-deriving everything the
helper used to supply.

---

## What to implement

### 1. Parameterize the Corkscrew writer by *source* geometry
`write_corkscrew_sheet_aggregating()` currently references the helper via the
fixed constants above. Add a path (new optional arg, e.g. `raw_geometry=None`)
where, when provided, the rollforward ranges are built from Raw Data instead:

- Current/prior ranges (`rc`, `rp`): replace
  `'<helper>'!<col>$12:<col>$<last_cust_row>` with
  `'Raw Data'!<src_month_col>$<src_first_row>:<src_month_col>$<src_last_row>`,
  where `src_month_col = get_column_letter(src_first_date_idx + month_index)`.
- ARR factor handling, Beginning/New/Upsell/Downsell/Churn/Ending: unchanged
  formula shapes, just the new ranges.

### 2. Compute customer counts inline (no helper summary rows to HLOOKUP)
Replace the `HLOOKUP`-into-helper-row-2/3 cells with formulas straight against
Raw Data:

- `# Active (current)` → `=COUNTIF('Raw Data'!<curr_col>$<first>:<curr_col>$<last>,">0")`
- `# Active (prior)`   → same on the prior column
- `# Retained`         → `=SUMPRODUCT(('Raw Data'!<curr>...>0)*('Raw Data'!<prior>...>0))`
  (this is the one legitimate `SUMPRODUCT` per Rule 7 — differential across two periods)
- `# Churned` / `# New` → as today (prior−retained, current−retained)

### 3. External check (row 14) against Raw Data
The single-type external check is already `=Ending - SUM(<curr range>)*factor`.
In the two-sheet path, point its `SUM` at the Raw Data current-month column over
the customer rows. **This only stays correct if the customer block is clean** —
see the gate below — otherwise summary/excluded rows in the range corrupt the SUM.

### 4. Gate: only take this path when the source is provably clean
Add the two-sheet path **only** when ALL of these hold (otherwise fall back to the
current 3-sheet pass-through):

- mode would be `passthrough` (source workbook, no type filter, one row/customer), AND
- the customer block is **contiguous** and covers the whole data range with **no
  excluded/summary rows inside it**, AND
- a **single** in-scope revenue type.

`survey.py` already reports the signals you need for this decision:
`customer_row_range.contiguous`, `customer_row_range.section_rows_excluded`, and
`section_rows_in_customer_col` (added in the #4/#5 work). Use them.

**Recommendation: make it an explicit opt-in**, not auto-detection. Add a flag
like `--two-sheet` (or `--no-helper`) that the agent passes only after survey
confirms a clean contiguous block. Auto-detecting "clean" risks silently shipping
a wrong two-sheet file; an explicit flag keeps the decision visible. Document in
SKILL.md that the agent sets it based on survey's `customer_row_range`.

---

## Edge cases to cover
- Source customer rows NOT contiguous (gaps, interspersed section rows) → must NOT
  take the two-sheet path; fall back to 3-sheet (the helper handles the mess).
- Excluded customers (present in Raw Data, dropped from analysis) → 3-sheet path,
  because the helper's "Excluded?" flag is what keeps them out.
- Raw Data month columns not starting at a known offset, or non-monthly spacing →
  rely on `source_first_date_col` + `get_source_months()`; verify the month count
  matches the corkscrew's expectation.
- ARR vs MRR factor: unchanged (`$B$3`).

---

## Tests to add (deliver.py has no self-test today — add a smoke harness)
1. **Clean source → 2 sheets, external check present, recalcs to 0.** Build a
   small source workbook with one contiguous row per customer, run with the new
   flag, assert: sheet names == `['Corkscrew', 'Raw Data']`; B14 external-check
   formula references `'Raw Data'!...`; (if LibreOffice available) recalc and
   assert B14 == 0 and Ending matches `compute.py`'s ending for that period.
2. **Messy source (interspersed section rows) + flag → falls back to 3 sheets**
   (the gate refuses the two-sheet path).
3. **Parity:** the two-sheet and three-sheet outputs produce identical Ending /
   GRR / NRR / Logo for the same clean source (cross-check with `compute.py`).

Run the existing self-tests too — they must stay green:
`python3 scripts/survey.py --self-test` and `python3 scripts/compute.py --self-test`.

---

## Docs to update when done
- **SKILL.md → "When the helper sheet appears"** — today it says a workbook source
  always yields 3 sheets and notes "a genuine two-sheet workbook path would be a
  future code change." Update that to describe the new flag and the clean-block
  condition.
- **SKILL.md → Bundled Scripts (`deliver.py`)** — document the `--two-sheet` flag.
- **README.md** — adjust the sheet-count description if it asserts 3.
- **reference/formulas-and-layout.md** — note that the rollforward ranges and the
  customer-count cells reference Raw Data directly in the two-sheet path.

---

## Effort / risk
- **Effort:** medium. The formula shapes already exist; the work is threading
  source geometry through `write_corkscrew_sheet_aggregating()` (or forking a
  `..._raw_direct` variant) and writing the gate + tests.
- **Risk:** medium. The failure mode is a silently-wrong two-sheet file if the
  "clean block" gate is too loose — which is exactly why the gate should be strict
  and the path opt-in. Keep the 3-sheet pass-through as the default fallback.

## Pointers (as of this handoff)
- `scripts/deliver.py` → `deliver()` (mode selection ~the `if mode == "aggregating"`
  block), `write_corkscrew_sheet_aggregating()` (rollforward + counts + external
  check), `write_analysis_passthrough_sheet()` (the helper this path would skip),
  layout constants `ANALYSIS_FIRST_CUST_ROW`, `ANALYSIS_FIRST_MONTH_COL`,
  `ROW_CHECK`.
- `scripts/survey.py` → `inspect_sheet()` output keys `customer_row_range`,
  `section_rows_in_customer_col` (the gate inputs).
