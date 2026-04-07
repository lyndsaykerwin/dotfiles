---
name: scraped-data-cleaning
description: >
  Structured workflow for cleaning, enriching, and preparing scraped business data
  (from Outscraper, Google Maps scrapers, or similar tools) for directory-style applications.
  Use this skill whenever the user has scraped or bulk-exported business/entity data they want to
  clean, deduplicate, enrich, validate, or prepare for a directory, database, or listing site.
  Also trigger when the user mentions outscraper data, Google Maps exports, business listing CSVs,
  data enrichment, or wants to crawl business websites to extract additional information.
  This skill enforces a specific workflow order — analyze first, define quality criteria,
  triage before enriching — to avoid wasting time and API calls on bad data.
---

# Scraped Data Cleaning & Enrichment

This skill guides you through a structured, efficient workflow for turning raw scraped business data into clean, enriched records ready for a directory or database. The workflow has a strict order because each phase depends on the previous one. Skipping ahead (e.g., enriching before triaging) wastes time and API calls on records that will get thrown out.

The user you're working with is a non-technical founder building directory-style products. Explain technical choices clearly, offer concrete options, and never assume they know engineering terminology.

## Workflow Overview

```
Phase 1: Analyze → Phase 2: Set Goals → Phase 3: Define Quality → Phase 4: Triage → Phase 5: Enrich → Phase 6: Track & Iterate
```

Do not skip phases. Do not start Phase 5 (Enrich) before completing Phase 4 (Triage). Each phase produces artifacts the next phase depends on.

**Exception — second-pass work:** If the user is asking you to revisit, re-check, or recover records from a dataset that has already been through this pipeline (it already has status/quality columns, the user references a prior pass), skip directly to the "Re-processing: Second Pass on Existing Data" section below. Do NOT restart from Phase 1.

---

## Test-First Data Processing

Every phase that involves writing a script (analysis, triage, enrichment) follows the same pattern. The reason for this discipline is that data processing scripts are error-prone — wrong column names, case sensitivity bugs, off-by-one errors, bad joins — and debugging after the fact wastes cycles for both you and the user. Writing the validation check first forces you to think clearly about what "correct" looks like before writing the code.

**The pattern:**

1. **Write the test first.** Before writing a processing script, write a short validation script that checks the output. What columns should the output have? What are the valid ranges or formats? What invariants should hold (e.g., no state should show >100% coverage, no duplicate IDs, all dates should be parseable)?

2. **Write the script.** Now write the actual processing code.

3. **Run and validate.** Execute the script, then immediately run the validation against the output.

4. **Self-heal on failure.** If validation fails, read the error, diagnose the issue, fix the code, and rerun. Retry up to 3 times. If it still fails after 3 attempts, stop and explain to the user what's going wrong rather than presenting broken results.

5. **Never present unvalidated results.** Do not show the user output that hasn't passed its validation checks. Broken tables, wrong counts, or mangled data erode trust and waste the user's time reviewing garbage.

**What good validation checks look like:**
- Column names and types match expectations
- Row counts are within expected ranges (not 0, not wildly inflated by bad joins)
- No nulls in required fields
- Percentages are between 0-100
- State/city names use consistent formatting
- String comparisons are case-insensitive where they should be
- Output file is valid CSV/JSON and can be re-loaded without errors

This pattern applies every time you write code in this workflow. Don't skip it even for "simple" scripts — simple scripts have simple bugs that are easy to catch with simple tests.

---

## Phase 1: Analyze & Summarize

Before touching the data, build a clear picture of what we're working with. Load the dataset and produce a summary report covering:

**Volume & Geography**
- Total number of records
- Breakdown by state, then by city within each state
- Geographic coverage gaps (states/regions with suspiciously few results)

**Data Completeness** — for each field, report the fill rate (% of records that have a non-empty value):
- Business name
- Full address (street, city, state, zip)
- Phone number
- Website URL
- Email address
- Business hours
- Reviews (count and recency — when was the most recent review?)
- Categories/tags
- Any other fields present in the dataset

**Website Health** (sample check)
- Pick a random sample of 20-30 website URLs from the data
- Check which ones return a 200 status vs. 404, timeout, or redirect to a parked domain
- Manually visit a handful of sites to verify your work
- Report the approximate % of working websites — this tells us how much enrichment is realistic

**Duplicates**
- Check for likely duplicates (same name + same city, same phone number, same address)
- Report how many suspected duplicates exist

Present this summary to the user in a clear table format before moving on. This is the foundation for everything that follows.

### Data Processing Library

Before writing any code, explain the tradeoff between pandas and polars (or any other library that fits):
- **Pandas**: More tutorials and examples online, easier to debug, great for datasets under ~500K rows. Most people's data will be fine with pandas.
- **Polars**: Faster for large datasets (500K+ rows), uses less memory, but error messages are less beginner-friendly.

Recommend one based on the dataset size and explain why. Let the user decide. If the dataset is under 100K rows, default to pandas unless there's a specific reason not to.

---

## Phase 2: Set Enrichment Goals

Based on the Phase 1 analysis, work with the user to set concrete, measurable goals. This phase is about connecting the data work to the user experience they want to build.

### Ask About the User Experience Goal

Ask the user: **"What kind of directory experience do you want to build? What filters or search options do you want users to have?"**

Common directory filters include:
- Location (city, state, zip radius)
- Services offered
- Certifications or specializations
- Ratings/reviews
- Price range
- Hours of operation
- Languages spoken

For each filter the user wants, check the Phase 1 analysis:
- Do we already have this data for most records? → Great, just clean it
- Can we reasonably extract this from business websites? → Plan for enrichment
- Is this data unlikely to exist on most websites? → Flag it early

**The "scant results" test**: For any proposed filter, estimate how many records would show results. If a filter would return < 10% of records in a given area, warn the user: "If we add a filter for [X] but only 8% of listings have that data, users will see very thin results when they use it. That creates a bad experience — it looks like the directory is empty. Should we drop this filter, or try a different approach?"

### Set Measurable Targets

Write down specific goals like:
- "Enrich [X] records with services-offered data"
- "Achieve [X]% fill rate for the website field"
- "Verify and correct addresses for [X]% of records"
- "Extract business hours from websites for [X] records"

These become your success criteria. Revisit them at the end.

---

## Phase 3: Define Quality Criteria

Work with the user to define what makes a record "good" (worth enriching) vs. "bad" (skip it). This is industry-specific and there's no universal answer.

### Walk Through Quality Dimensions

For each dimension, ask the user what their threshold is:

**Identity**: Does the record clearly represent a real, distinct business?
- Has a real business name (not "Business Owner" or "N/A")
- Has a verifiable address or at least a city/state
- Is not a duplicate of another record

**Reachability**: Can a user actually contact or find this business?
- Has a working phone number OR working website OR physical address
- Is not permanently closed

**Relevance**: Does this business belong in the directory?
- Is in the right industry/category
- Is in the right geographic area
- Is not a tangentially-related business (e.g., a boat dealership in a marine mechanics directory)

**Freshness**: Is this business still active?
- Has recent reviews (within last 2 years) OR a working website
- Is not flagged as "permanently closed" or "temporarily closed"

### Create a Scoring Rubric

Based on the user's answers, create a simple scoring system:
- **Good**: Meets all critical criteria → proceed to enrichment
- **Needs Review**: Missing 1-2 non-critical fields but otherwise solid → flag for manual check
- **Bad**: Fails critical criteria (no name, permanently closed, wrong industry, duplicate) → skip enrichment

Add a `quality_status` column to the dataset: `good`, `needs_review`, or `bad`.
Add a `quality_notes` column to capture why a record was flagged.

Document the rubric in the project's `docs/` folder so it can be referenced later.

---

## Phase 4: Triage

Apply the quality rubric from Phase 3 to every record in the dataset. This happens BEFORE enrichment to avoid wasting crawling time and API calls on bad data.

### Automated Triage

Follow the test-first pattern: write a validation script first that checks the triage output (e.g., every record has a `quality_status`, no record is tagged both `good` and `bad`, the counts of good + bad + needs_review equal the total records). Then write and run the triage script:
- Tag duplicates as `bad`
- Tag records missing critical identity fields as `bad`
- Tag records marked "permanently closed" as `bad`
- Tag records that pass all criteria as `good`
- Tag edge cases as `needs_review`

### Report Results

After triage, report:
- How many records are `good` (these get enriched)
- How many are `bad` (these get skipped)
- How many are `needs_review` (these need a quick look from the user)

Show some examples from each bucket so the user can sanity-check the rubric. If the triage is catching too many good records or letting too many bad ones through, adjust the rubric and re-run.

### Add Tracking Columns

Add these columns to the dataset for tracking progress through enrichment:
- `reviewed`: boolean — has this record been processed by the enrichment pipeline?
- `enrichment_status`: `pending`, `enriched`, `failed`, `skipped`
- `enrichment_notes`: free text for capturing issues
- `last_updated`: timestamp of most recent modification

---

## Phase 5: Enrich

Only enrich records tagged as `good` in Phase 4. Never enrich records tagged `bad`.

### Validate Before You Scale

The test-first pattern is especially important here because enrichment scripts are the most complex and expensive part of the workflow. Before running enrichment at scale, write validation checks for the enrichment output: does each enriched record have the expected fields? Are the extracted values plausible (e.g., phone numbers look like phone numbers, not random strings)? Does the enriched dataset still have the same number of `good` records as the triage output (no records mysteriously dropped or duplicated)?

### Confirm Crawling Approach Before Starting

Before crawling any websites, do a test run on 5-10 sample sites to figure out:

1. **Where is the valuable information?** Is it on the homepage, an "About" page, a "Services" page? Different industries put key info in different places.
2. **What's the site structure like?** Are these mostly simple small-business sites, or complex multi-page sites? Do they use JavaScript rendering?
3. **What can we actually extract?** Try pulling the enrichment fields we defined in Phase 2. How often does the data actually appear?

Share the test results with the user before scaling up. If most sites don't have the info we're looking for, revisit the enrichment goals rather than crawling hundreds of sites for nothing.

### Crawl4AI Setup

Use Crawl4AI's async crawler for speed. Key components:

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.extraction_strategy import LLMExtractionStrategy
```

**BrowserConfig**: Set headless=True, configure reasonable timeouts. Use a realistic user agent.

**CrawlerRunConfig**: Configure based on the test run findings:
- If data is on the homepage → crawl just the root URL
- If data is on inner pages → use link discovery to find /about, /services, etc.
- Set `cache_mode=CacheMode.ENABLED` to avoid re-crawling on retries

**PruningContentFilter**: Strip navigation, footers, ads, and boilerplate. This reduces noise and token usage for LLM extraction.

**LLMExtractionStrategy + LLMConfig**: Use an LLM to extract structured data from the crawled content. Define a clear schema matching the enrichment fields from Phase 2. Choose the model based on the complexity of extraction needed — don't default to the cheapest model if it produces garbage results. A slightly more expensive model that extracts data correctly on the first pass is cheaper overall than a cheap model that needs retries and manual review.

**Concurrency**: Use Crawl4AI's async features to crawl multiple sites concurrently. Start with 5-10 concurrent requests and adjust based on success rates. If many sites are timing out, reduce concurrency.

### API Efficiency

Be smart about API usage:
- Cache aggressively — if a crawl succeeds, save the raw content so we don't need to re-crawl
- Batch LLM extraction calls where possible
- Don't retry failed crawls more than twice — mark them as `failed` and move on
- The cheapest option is not always the most efficient. If a $0.01/call model gives 40% accuracy and a $0.03/call model gives 90% accuracy, the expensive model is cheaper per successful extraction

### Progress Tracking

Save progress after every batch. Update the tracking columns (`reviewed`, `enrichment_status`, `last_updated`) as each record is processed so you can pick up exactly where you left off if the process is interrupted.

**Check metrics every 50 records:**
- Crawl success rate (% of URLs that returned content)
- Extraction success rate (% of crawled pages where we found the target data)
- Per-field fill rates (are we actually getting the data we wanted?)
- Error patterns (are certain types of sites consistently failing?)

If the success rate drops below 50%, stop and reassess the approach. Share the metrics with the user and discuss whether to:
- Adjust the crawling strategy (different pages, different selectors)
- Adjust the extraction prompt
- Accept a lower fill rate for that field
- Drop that enrichment field entirely

---

## Phase 6: Final Report & Handoff

After enrichment is complete, produce a final summary:

**Before vs. After**
- Record count: started with X, kept Y good records, enriched Z
- Per-field fill rates: before enrichment vs. after
- Quality distribution: good / needs_review / bad counts

**Goal Achievement**
- For each goal set in Phase 2, report whether it was met
- If goals weren't met, explain why and what could be done differently

**Data Export**
- Export the clean, enriched dataset in the format needed for the directory (CSV, JSON, database import, etc.)
- Include a data dictionary explaining what each column contains
- Flag any records in `needs_review` that the user should look at manually

**Lessons Learned**
- What worked well in the enrichment process
- What didn't work (fields that were hard to extract, sites that were hard to crawl)
- Recommendations for the next batch of data

---

## Re-processing: Second Pass on Existing Data

Sometimes the user has already run through the full pipeline and wants to revisit a specific subset of records — typically because the first pass was too aggressive in filtering, used the wrong strategy for a particular check, or new information changes what counts as "good." This is NOT a fresh start. Do not restart from Phase 1.

### How to Recognize a Second-Pass Request

The user will say things like:
- "Revisit the records that were tagged dead/bad/unknown"
- "The first pass missed X records because..."
- "Go back and re-check the ones that failed"
- "I think there are good records hiding in the rejected pile"

### What to Do

1. **Understand the scope.** Ask: What subset of records? What was wrong with the first-pass logic? What should the new criteria be? If the user has already explained this (as in their prompt), don't re-ask — just confirm your understanding.

2. **Analyze just the target subset.** Load the existing dataset and filter to the subset the user specified. Report basic stats on that subset (count, what fields are populated, what the current status tags say). This is a mini Phase 1 scoped to the subset, not the full dataset.

3. **Define the revised criteria.** Work with the user to define what "recoverable" means for this subset. For example: "A record tagged `dead` is recoverable if the root domain returns a 200 even though the specific Google Maps URL was dead, OR if the business has recent reviews suggesting it's still operating."

4. **Write the re-check script using test-first pattern.** The test-first discipline from above still applies:
   - Write validation checks first (e.g., no record should flip from `dead` to `good` without a documented reason, re-checked count + remaining dead count should equal original dead count)
   - Write the re-check script
   - Run and validate
   - Self-heal up to 3 times on failure

5. **Report recovery results.** Show the user: how many records were re-checked, how many were recovered (with examples), how many remain dead (with examples of why), and what changed.

6. **Merge back into the main dataset.** Update the status columns on recovered records and save. Don't create a separate file unless the user asks for one.

### Key Difference from Fresh Processing

In a second pass, the user already knows their data. They don't need you to explain what pandas is or walk through quality dimensions from scratch. Be direct: confirm the subset, confirm the new criteria, run the re-check, report results. Skip the parts of the workflow that don't apply.

---

## Key Principles

**Workflow order is non-negotiable for fresh data.** Analyze → Goals → Quality Definition → Triage → Enrich. Every shortcut costs more time in the long run. But for second-pass re-processing of already-triaged data, skip to the relevant phase — see "Re-processing" above.

**Triage before enrichment, always.** Enriching a bad record is pure waste — crawling time, API calls, and human attention spent on data that gets thrown away.

**Track everything.** The `reviewed` and `enrichment_status` columns let you pick up exactly where you left off. Sessions get interrupted. Rate limits happen. Progress should never be lost.

**Check metrics regularly.** Every 50 records, pause and look at success rates. A failing approach doesn't get better at record 200 — it just wastes 150 more records worth of API calls.

**User experience drives decisions.** Every enrichment field should serve a directory filter or search feature. If the data can't support a good user experience for a particular filter, drop it rather than shipping thin results.

**Explain technical choices.** The user is not an engineer. When choosing between libraries, crawling strategies, or API tradeoffs, explain the options in plain language and let them decide.

**Test before you trust.** Every script gets a validation check written before the script itself. Run the validation after execution. If it fails, fix and retry up to 3 times. Never present unvalidated output — broken tables and wrong counts waste the user's time and erode trust.
