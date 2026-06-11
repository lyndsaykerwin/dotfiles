---
name: nda-processor
description: >
  Process NDA (Non-Disclosure Agreement) documents end-to-end on Lyndsay's Mac:
  pull from Gmail, review for search-fund-relevant risks, fill in Great Elm
  Partners details, sign with a script-style signature, save to the right deal
  folder, and draft a threaded reply to the sender with the signed PDF attached.
  Use this skill whenever Lyndsay mentions NDAs, MNDAs, non-disclosure agreements,
  confidentiality agreements, reviewing legal documents for risks, filling in
  blanks on a legal document, or preparing an NDA for signature. Also trigger
  when she has .docx, .doc, or .pdf files that appear to be legal agreements
  and wants them reviewed or filled out, even if she doesn't say "NDA" explicitly.
  Trigger on phrases like "review this agreement", "what should I watch out
  for", "fill in my details", "sign this", or "process this NDA".
---

# NDA Processor (Mac)

End-to-end NDA workflow for Lyndsay on her Mac. Pulls the file from Gmail,
runs a search-fund-aware lawyer review, pauses for her sign-off, then either
redlines or signs and drafts the reply to the broker — all without her having
to touch a file manually.

## Environment (verify before starting)

- **OS:** macOS (Apple Silicon)
- **Python:** always `python3`, never `python`
- **LibreOffice:** `/Users/lyndsay/Applications/LibreOffice.app/Contents/MacOS/soffice`
  - Used for `.doc → .docx` conversion AND `.docx → .pdf` final export
  - Install command if missing: download latest .dmg from documentfoundation.org
    and copy `LibreOffice.app` into `~/Applications/` (no admin password needed)
- **pandoc:** installed at `~/.local/bin/pandoc` (used for plain-text extraction)
- **Working directory:** the deal folder (see "Folder convention" below).
  Never use `/tmp` for outputs — final files go in the deal folder.

## Hardcoded defaults

### Signing block (Great Elm Partners)
- **Name:** Lyndsay Kerwin
- **Title:** Founder
- **Company legal name:** Great Elm Partners LLC
- **Address:** 214 Duffield St, Brooklyn, NY 11201
- **Phone:** omit unless Lyndsay says otherwise
- **Signature font:** **Snell Roundhand** (built into macOS, classic copperplate
  style for signatures). Set the Lyndsay-name run to size 40 (`<w:sz w:val="40"/>`).
  Do not mimic the counterparty's font choice — pick our own.

### Folder convention
- **Parent:** `/Users/lyndsay/Documents/Claude_Work/great-elm-deal-evaluation-system/Deals/`
  (NOTE: lowercase, hyphenated. There is also an old `Great Elm deal evaluation system`
  parallel folder in some legacy paths — never write there. Always confirm you're in
  the lowercase-hyphenated parent.)
- **Per-deal subfolder:** `<Project Codename>/` (e.g. `Project Loyalty/`, `Launchpad/`,
  `Zendata/`). Codename comes from the broker's prior email if they used one;
  otherwise pick something descriptive of the space ("Project Loyalty" for a
  loyalty/rewards SaaS, etc.) and confirm with Lyndsay before creating the folder.

### Output file naming (per deal folder)
- `<Project Codename> NDA - signed.docx` (filled, editable copy)
- `<Project Codename> NDA - signed.pdf` (final to attach to reply)
- If redlining instead: `<Project Codename> NDA - redlined.docx` (with comments)
- Keep the original counterparty file (`.doc` or `.docx`) untouched in the folder
- Keep `NDA_extracted.txt` (plain text used for review) for traceability

---

## Workflow overview

Eight phases. The pause after Phase 5 (lawyer review) is mandatory — never
insert comments or fill the doc until Lyndsay greenlights the findings.

1. **Read the email** that contains the NDA → understand the deal context, find
   any project codename
2. **Pull the attachment** from Gmail via the local MCP
3. **Convert** `.doc → .docx` if needed; extract plain text
4. **Lawyer review** with a search-fund lens (use `references/nda-checklist.md`)
5. **PAUSE — present findings to Lyndsay, get explicit sign-off** on which
   path: sign-as-is, light redline, or full redline
6. **Either**: (a) fill + sign + save PDF, OR (b) insert Word comments at the
   problematic clauses with suggested rewrites; save .docx with comments
7. **Draft the threaded reply** in Lyndsay's voice with the file attached
8. **Tell Lyndsay where to find/send the draft** — and the critical warning:
   never open it in Mail.app

---

## Phase 1: Read the email

Use `mcp__google-workspace-local__gmail_read_message` (NOT `gmail_search` —
search returns snippets only, not full body). You need the full body of the
NDA email AND the prior email in the thread (which usually has the deal
context and possibly a project codename).

If you only have the message id Lyndsay paid attention to, also walk back the
thread: `mcp__google-workspace-local__gmail_read_thread <thread_id>`.

Pull out:
- Counterparty broker name (e.g. Apex Capital Advisors)
- Sector/space (e.g. "loyalty/rewards SaaS for wealth management")
- Any codename or company name the broker revealed
- Headline financials if mentioned (revenue, EBITDA, ARR) — useful for the folder README later

Propose a project codename to Lyndsay. If she approves (or doesn't object),
proceed.

## Phase 2: Pull the attachment

```
mcp__google-workspace-local__gmail_list_attachments(message_id=<NDA email id>)
```

This returns one entry per attachment with `filename`, `mime_type`, `size_bytes`,
and `attachment_id`. Skip any inline images (sender signature logos, typically
~10 KB PNG). The NDA itself is usually a `.doc` or `.docx`, ~50-200 KB.

Then:

```
mcp__google-workspace-local__gmail_download_attachment(
    message_id=<NDA email id>,
    attachment_id=<from list>,
    filename=<exact filename from list>,
    save_dir="/Users/lyndsay/Documents/Claude_Work/great-elm-deal-evaluation-system/Deals/<Project Codename>"
)
```

Create the folder first with `mkdir -p` if it doesn't exist.

## Phase 3: Convert + extract text

If the file is a legacy `.doc` (not `.docx`), convert via LibreOffice:

```bash
~/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to docx \
  "<filename>.doc" --outdir "<deal folder>"
```

Then extract plain text via pandoc (cleanest text output for LLM review):

```bash
pandoc -f docx -t plain "<filename>.docx" -o NDA_extracted.txt
```

Read the resulting `NDA_extracted.txt` — that's what feeds the review.

If the file arrives as a PDF instead of `.doc`/`.docx`:
- Use `pdfplumber` for text extraction only
- For redlining/filling, convert PDF → docx via LibreOffice
  (`--convert-to docx`) but warn Lyndsay that PDF→Word conversion isn't pixel
  perfect — better to ask the counterparty for a Word version

## Phase 4: Lawyer review (search-fund lens)

Apply every item in `references/nda-checklist.md` to the extracted text.
Then specifically flag for search-fund context:

🔴 **Hard flags** (always raise):
- Non-compete provisions (any kind)
- Non-solicitation longer than 12 months
- One-sided indemnification (we indemnify them, they don't indemnify us)
- IP assignment language buried in confidentiality clauses
- Missing **independent development** carve-out (critical — without it, looking
  at any other deal in the same space is risky)
- Perpetual / unlimited confidentiality on non-trade-secret info
- Phantom references to clauses that don't exist (e.g. survival clause says
  "non-solicitation provisions survive" but no non-solicit clause is in the doc)

🟡 **Soft flags** (mention but usually OK):
- Confidentiality survival > 2 years (search-fund norm is 1–2 years)
- Governing law in a non-US jurisdiction (Canadian brokers often use Ontario)
- Long return/destruction window (>30 days)

🟢 **Good things to confirm are present** (no action needed):
- Mutual structure (not one-way against us)
- All four standard carve-outs (public domain, prior knowledge, third-party,
  independent development)
- "Sources of capital" or similar language permitting disclosure to investors
- Retention exception (one copy for record-keeping/legal compliance)

## Phase 5: PAUSE for sign-off — DO NOT skip

Present findings to Lyndsay in three buckets (red / yellow / green) with
plain-English explanations and the trade-off for each red flag. Then offer
three paths:

- **(A) Sign as-is** — accept the flagged risks, fastest path
- **(B) Light redline** — flag only the highest-priority items
- **(C) Full redline** — push back on everything

WAIT for her explicit choice before doing anything to the document. **Never
insert comments or fill blanks before she's chosen a path.**

## Phase 6a: Fill + Sign (chosen path: A)

Unzip the `.docx` (it's just a zip file):

```python
import zipfile
with zipfile.ZipFile('<filename>.docx') as z:
    z.extractall('_unpacked')
```

Edit `_unpacked/word/document.xml` to:

1. **Fill date placeholders.** Today's date in the format the doc expects
   (often "Xth day of Month, YYYY" — e.g. "4th day of May, 2026")
2. **Fill `{Insert company name}` or similar placeholders** with
   `Great Elm Partners LLC`. Watch out: placeholders may be split across
   multiple `<w:r>` runs (e.g. `<w:t>{</w:t>` followed by another run with
   `<w:t>Insert company name}</w:t>` and a `w:highlight w:val="yellow"` —
   handle both pieces).
3. **Replace the recipient signature line.** Find the company-side
   `By:___________________________` run and replace with two runs that mimic
   how the broker did their signature, but in our font:
   ```xml
   <w:r><w:rPr><w:rFonts w:cs="Arial" w:ascii="Arial" w:hAnsi="Arial"/></w:rPr><w:t xml:space="preserve">By:  </w:t></w:r>
   <w:r><w:rPr><w:rFonts w:cs="Arial" w:ascii="Snell Roundhand" w:hAnsi="Snell Roundhand"/><w:sz w:val="40"/><w:szCs w:val="40"/></w:rPr><w:t>Lyndsay Kerwin</w:t></w:r>
   ```
   **Critical:** target the COMPANY (recipient) side, not the broker side.
   Mutual NDAs have two columns with identical labels; identify the recipient
   column by reading XML context, not by blind string replacement.

After every replacement, run a sanity check:
- `Great Elm Partners LLC` count == expected (usually 2: preamble + sig block)
- No leftover `{Insert` or `Insert company name`
- No leftover `By:___`
- `Lyndsay Kerwin` present exactly once

Repack via Python `zipfile` (do NOT use the docx skill's `pack.py` — known
to fail on validators import):

```python
import zipfile, pathlib
with zipfile.ZipFile('<Project Codename> NDA - signed.docx', 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in pathlib.Path('_unpacked').rglob('*'):
        if f.is_file():
            zf.write(f, f.relative_to('_unpacked'))
```

Convert to PDF:

```bash
~/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf \
  "<Project Codename> NDA - signed.docx" --outdir "<deal folder>"
```

Verify the PDF (`file <name>.pdf` should report `PDF document, version 1.7`)
and use `pdfplumber` to confirm the filled text shows up correctly. If
Lyndsay opens it in Preview and gets a "file can't be opened" error, it's
usually a transient Preview cache thing — ask her to try again or close
and reopen Preview.

## Phase 6b: Redline with comments (chosen path: B or C)

If Lyndsay chose redline, insert Microsoft Word comments at the problematic
clauses, with suggested replacement text written into the comment body.
Save as `<Project Codename> NDA - redlined.docx` and skip the PDF export
(she'll send the .docx for the broker to accept/reject in Word).

True tracked-changes (strikethrough + insert) is harder to script reliably;
comments-with-suggested-rewrite is the simpler-and-clear-enough first version.
If Lyndsay specifically asks for tracked changes, do them via raw `<w:ins>`
and `<w:del>` XML manipulation — but only when asked, not by default.

## Phase 7: Draft the reply

Use `mcp__google-workspace-local__gmail_create_draft` with:
- `reply_to_message_id` set to the NDA email's message id (this threads the
  reply into the existing conversation AND auto-quotes the prior message —
  matches Gmail web's reply behavior)
- `attachments` set to a single-element list with the absolute path to the
  PDF (or redlined .docx)
- Body in Lyndsay's voice — short, warm, em-dash style, "Hi <Name>," opener,
  "Best, Lyndsay" sign-off. Default template:

  ```
  Hi <First Name>,

  Thanks — NDA is signed and attached. Look forward to the CIM whenever
  it's convenient on your end.

  Best,
  Lyndsay
  ```

  ~25 words. Adjust slightly based on tone of broker's prior message; pull
  one or two of her past replies to similar broker emails (`gmail_search`
  for `from:lyndsay@greatelmpartners.com NDA OR signed OR CIM`) if uncertain.

After creating the draft, **immediately verify the attachment is on it**:

```
mcp__google-workspace-local__gmail_list_attachments(message_id=<draft message id>)
```

Confirm the file size matches the local PDF byte count.

## Phase 8: Hand off to Lyndsay — and the Mail.app warning

Tell Lyndsay:
1. Where the files landed (full path to deal folder)
2. The draft is ready in Gmail Drafts, threaded into the broker's chain
3. **CRITICAL WARNING:** "Don't open the draft in Mail.app — that destroys
   the attachment." Mail.app's behavior of opening API-created drafts for
   editing deletes the server-side draft and creates a local copy without
   the attachment. If she sends from Mail.app after that, the attachment
   won't go.
4. Her two safe send options:
   - **(a)** Send via Gmail web at mail.google.com (she can verify the
     attachment is shown before clicking Send), OR
   - **(b)** Ask Claude to send via API: `gmail_send_draft <draft_id>` —
     fires immediately, Mail.app never touches it. Requires explicit
     "send it" confirmation from Lyndsay first.

---

## Known limitations and gaps in current tooling

1. **No `gmail_delete_draft` in the MCP.** If you create multiple drafts
   during iteration (e.g. a font swap), the old ones persist. Tell Lyndsay
   to delete them manually in Gmail Drafts → "Discard draft" on the obsolete
   ones.
2. **Mail.app-destroys-draft bug.** See Phase 8. This isn't fixable from
   our side — it's how Apple Mail handles IMAP drafts that have attachments
   added via the Gmail API. The only workaround is to never open the draft
   in Mail.app for editing.
3. **No `gmail_update_draft`.** Cannot edit body or attachments of an
   existing draft. To change anything, create a new draft and tell Lyndsay
   to discard the old.

---

## Things that have caused real bugs (don't repeat)

| Bug | Root cause | Permanent fix |
|---|---|---|
| Wrote NDA into a duplicated parallel `Great Elm deal evaluation system/` folder instead of the real `great-elm-deal-evaluation-system/` (lowercase, hyphenated) project | Created folder by guessing path instead of checking the existing project structure | Always `ls ~/Documents/Claude_Work/` first to find the correct lowercase-hyphenated parent before creating any deal folder |
| Mail.app destroyed the draft when Lyndsay opened it for editing — attachment vanished | Mail.app's IMAP handling of Gmail-API-created drafts: opening for edit deletes server draft, creates local copy without attachment | Never tell Lyndsay to send from Mail.app. Send via API or via Gmail web |
| Used the broker's signature font (Freestyle Script) for our signature too | Mimicked the counterparty when I should have made our own choice | Always Snell Roundhand for our signature |
| Only 1 of 2 `{Insert company name}` placeholders replaced | Second placeholder split across multiple `<w:r>` runs with the `{` and the rest in different runs (one with yellow highlight) | After bulk replace, grep for any remaining `Insert company name` and `{Insert` and handle the split-run case explicitly |
| Tried to install LibreOffice via `brew install --cask` | Homebrew not installed on this Mac | Direct .dmg download to `~/Applications/` (no admin password needed) |
| Skill referenced a "read full message" Gmail tool that didn't exist | Old version of MCP only had search/draft/send | Confirmed `gmail_read_message`, `gmail_read_thread`, `gmail_list_attachments`, `gmail_download_attachment` now exist in `/Users/lyndsay/Documents/Claude_Work/mcp_google_agent/server.py` |

---

## Reference files in this skill folder

- `references/nda-checklist.md` — full review checklist, applied in Phase 4
- `scripts/extract_text.py` — alternative XML-based text extractor (only
  needed if pandoc is unavailable; pandoc is the default)
- `evals/` — evaluation cases (don't run during normal workflow)
