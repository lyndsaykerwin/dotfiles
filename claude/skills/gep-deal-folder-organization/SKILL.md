---
name: gep-deal-folder-organization
description: Maintain clean, consistent folder organization for Great Elm Partners deal evaluations. Use this skill whenever (1) creating a new file inside a Deals/ folder under the great-elm-deal-evaluation-system repo, (2) processing or copying files from a data room delivery (Datasite, Intralinks, IDrive, ShareFile, raw email attachments, etc.) into a deal folder, (3) creating a new version of an existing versioned deliverable (e.g., Foo_v2.xlsx when Foo_v1.xlsx exists, or Foo.md when an older Foo.md exists), or (4) the user asks to organize, restructure, archive, or clean up a deal folder. Triggers on phrases like "save this analysis", "create a new version", "data room download", "organize the deal folder", "archive the prior", "clean up Launchpad", or any save/create/move operation targeting `Deals/[Company]/`. Encodes the canonical folder structure, the archive-on-version-bump rule, and the data-room intake convention.
---

# GEP Deal Folder Organization

How files are organized inside `Deals/[Company]/` in Lyndsay's Great Elm Partners deal evaluation system. Apply automatically — Lyndsay shouldn't have to ask twice for the same structure.

## Canonical folder structure

Every deal under `Deals/` follows the same shape:

```
Deals/[Company]/
├── From Company/              ← Everything the seller / banker provides
│   ├── Pre-IOI/              ← Materials received before the IOI was sent
│   └── Post-IOI/             ← Data room delivered after the IOI was sent
│       ├── [Datasite_<id>/]  ← Preserve the seller's folder structure verbatim
│       └── [other VDR sections/]
├── IOI/                       ← The Indication of Interest letter we sent
├── Great Elm Analysis/        ← Anything WE produced — analyses, models, workbooks
│   ├── [Analysis Type 1]/    ← One folder per analysis type
│   │   ├── [Active version(s)]
│   │   └── Archive/          ← Prior versions
│   ├── [Analysis Type 2]/
│   │   ├── [Active version(s)]
│   │   └── Archive/
│   └── [loose top-level files: e.g., annotated seller models]
├── Notes & Research/          ← Banker call notes, market research, voice memos
├── Summary Deal Analyses/     ← Opportunity Summary (the canonical Stage 1 .md + .docx)
└── Archive/                   ← Old materials that don't fit elsewhere (use sparingly)
```

**Distinguishing principles:**
- **"From Company" vs "Great Elm Analysis"** = anything the seller sent vs anything we built. If you can't tell, ask before placing.
- **Pre-IOI vs Post-IOI** = simple time split, IOI date is the boundary. Helps reconstruct "what did we know when?"
- **Analysis-type subfolders** under Great Elm Analysis. Examples: `Retention Analysis/`, `ARR Bridge/`, `Sales Pipeline Win-Loss/`, `Cohort Analysis/`. **Do not** dump loose versioned files at the Great Elm Analysis root if there are 2+ versions of the same artifact — give it its own folder.

## The archive-on-version-bump rule (mandatory)

When writing a new version of a versioned deliverable, **move the prior version into `Archive/` in the same set of operations.** No exceptions.

**Trigger:** about to write `Foo_v(N+1).xlsx` (or `.md` / `.docx`) when `Foo_vN.<ext>` exists in the same folder.

**Action:**
1. If `Archive/` doesn't exist in that folder, create it (`mkdir -p`).
2. Move ALL paired files of the prior version to `Archive/`:
   - If a deliverable has both an `.xlsx` and `.md` summary (e.g., `Launchpad_Retention_v7.xlsx` + `Launchpad_Retention_Summary_v7.md`), move both.
   - If the project's house style produces `.md` + `.docx` (per the project CLAUDE.md), move both.
3. Then write the new version into the active folder.

**Never delete prior versions** — `mv` to Archive, don't `rm`. Lyndsay has been bitten by accidental loss of intermediate work; archive is recoverable, delete isn't.

**Pair detection — match by version-stripped basename:**
- `Foo_v7.xlsx` → look for `Foo_v7.*` (any extension)
- `Foo_v7_summary.md` → look for `Foo_v7*`
- When in doubt, ask before archiving — better one extra question than an orphaned summary file.

## When to create a new analysis-type subfolder

If the user introduces a new analysis (retention, cohort, pricing, salesforce, NPS, etc.) and the work will produce 2+ files (xlsx + md summary, or any pair), create a subfolder under `Great Elm Analysis/` named after the analysis type. Use Title Case with spaces: `Retention Analysis/`, not `retention_analysis/`.

If the work is a one-off single file with no versioning expected (e.g., a one-off back-of-envelope sanity check), leave it loose at the Great Elm Analysis root. Promote to its own folder when the second version appears.

## Data-room intake rule

When the user reports a new data room delivery (or an updated one), follow this sequence:

1. **Find the files.** Look in `~/Downloads/` for folders matching the VDR platform name (`Datasite_<timestamp>`, `Intralinks_<id>`, `IDrive_<id>`) or topical names from the seller (e.g., "Capitalization and legal", "Customers", "Financials"). Datasite exports often come as multiple sibling folders, not one bundle.
2. **Copy, don't move.** `cp -R` into `Deals/[Company]/From Company/Pre-IOI/` or `.../Post-IOI/` depending on timing. Preserve the seller's folder structure exactly — don't flatten, rename, or "clean up."
3. **Verify file counts match before deleting originals.** `find <source> -type f | wc -l` should equal `find <dest> -type f | wc -l`. Only then offer to delete the Downloads copies.
4. **Don't edit the dataroom files.** Per project CLAUDE.md: "Never touch raw data. Dataroom files and source workbooks are read-only." Any analysis we run uses these files as immutable inputs.
5. **Catalog what arrived, by category, in chat.** Use the seller's own folder structure as the outline. Flag what's new vs. what we already had, and what's missing relative to a normal data room.

If the seller delivers files via Gmail attachment instead of a VDR, save them under `From Company/[Pre|Post]-IOI/` in a folder named for the email date and sender, e.g., `From Company/Post-IOI/2026-05-28 from banker (Smith)/`.

## When to invoke this skill (be aggressive)

Run this skill — don't ask, just apply the structure — when any of the following happen:

- About to write a new file to `Deals/[Company]/[anywhere]/`. Check the proposed path against the canonical structure first; if it doesn't fit, adjust.
- About to `mv` or `cp` files from `~/Downloads/` into a Deal folder.
- About to overwrite or create vN+1 of a file. The archive step is non-optional.
- User says "save this", "create the analysis file", "where should this go", "data room came in", "new version", "archive the old one", "clean up the folder", "reorganize".

## When to ASK instead of apply silently

- A new analysis type whose folder name isn't obvious (e.g., user runs "customer cohort decomposition" — name it `Cohort Analysis/` or `Customer Cohort/`?). Pick a reasonable default, mention it, and proceed unless corrected.
- Ambiguous artifacts that could be either "From Company" or "Great Elm Analysis" (e.g., the banker's DD-request workbook with our handwritten answers in it). Ask before placing.
- The first time a new structure decision is made for a deal that didn't follow the canonical layout — surface the deviation, propose the canonical structure, let the user accept before moving anything.

## Related project conventions

- Project CLAUDE.md "File naming and versioning" section: "Never overwrite. If `Company_Opportunity_Summary_v1.md` exists, the next version is `v2.md`, then `v3.md`." This skill extends that rule with the explicit `Archive/` step.
- Project CLAUDE.md "Final deliverables are saved in two formats: `.md` and `.docx`" — pair these when archiving.
