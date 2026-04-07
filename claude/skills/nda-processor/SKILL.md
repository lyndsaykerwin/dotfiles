---
name: nda-processor
description: >
  Process NDA (Non-Disclosure Agreement) documents end-to-end: review for risks,
  fill in entity details, and save to the appropriate company prospect folder.
  Use this skill whenever the user mentions NDAs, MNDAs, non-disclosure agreements,
  confidentiality agreements, reviewing legal documents for risks, filling in
  blanks on a legal document, or preparing an NDA for signature. Also trigger
  when the user has .docx, .doc, or .pdf files that appear to be legal agreements
  and wants them reviewed or filled out, even if they don't say "NDA" explicitly.
  Trigger on phrases like "review this agreement", "what should I watch out for",
  "fill in my details", "sign this", or "process this NDA".
---

# NDA Processor

Process NDA documents (.docx, .doc, or .pdf) from review through signature-ready
output, filed into the correct prospect folder. This skill depends on the
**docx** skill for low-level unpack/edit/repack operations. If the docx skill
is not available, use the fallback approaches described below.

## Environment (read this first)

- **OS:** Windows 10
- **Python command:** always `python`, never `python3` — `python3` does not exist on this machine
- **No /tmp:** never unpack files to `/tmp` — it doesn't map to a real Windows path; always unpack into the working project directory
- **Encoding:** run `set PYTHONIOENCODING=utf-8` before calling pack.py or any script that prints unicode characters
- **LibreOffice:** installed at `C:\Program Files\LibreOffice\` — always call soffice.exe directly, never use the docx skill's soffice.py wrapper (AF_UNIX sockets don't exist on Windows)

## Hardcoded defaults

### Signing information (Great Elm Partners)

- **Name:** Lyndsay Kerwin
- **Company legal name:** Great Elm Partners LLC
- **Address:** 20 Dolphin Lane, Okatie, SC 29909
- **Title:** Founder
- **Phone:** 617 763 3301

### Prospects root folder

```
C:\Users\Courtney Stuart\Documents\Searching\Prospects\
```

Individual prospect folders live here, e.g.:

```
C:\Users\Courtney Stuart\Documents\Searching\Prospects\RioAI\
```

### Output file naming

- Filled and signed: `<NDA Name> - signed.docx`
- PDF (auto-generated after signing): `<NDA Name> - signed.pdf`

### Platform

Windows only. All instructions assume Windows. Use `python` not `python3`.
Never use `/tmp` — always unpack into the project working directory.

---

## Workflow overview

Four phases. Adapt as needed — user might only want a review, or only want
fields filled.

1. **Find & Convert** — locate the NDA file and normalize to .docx if needed
2. **Extract** — pull plain text for review
3. **Review** — apply the NDA checklist, flag risks
4. **Fill, Sign & File** — insert entity details, repack, convert to PDF, save to prospect folder

---

## Phase 1: Find & Convert

### Locating the file

Default search location is the user's Downloads folder:

```
C:\Users\Courtney Stuart\Downloads\
```

Search for NDA files:

```bash
ls "C:/Users/Courtney Stuart/Downloads/" | grep -iE "nda|mnda|nondisclosure|confidential"
```

If nothing found, ask the user for the full file path.

### Format handling

| Input format | Action |
|---|---|
| `.docx` | Use directly |
| `.doc` | Convert to .docx first using LibreOffice (see below) |
| `.pdf` | Extract text with pdfplumber for review; fields cannot be edited in a PDF — ask if user has source .docx |

### Converting .doc → .docx

Call soffice.exe directly — do NOT use the docx skill's soffice.py wrapper
(it uses AF_UNIX sockets which don't exist on Windows):

```bash
"C:/Program Files/LibreOffice/program/soffice.exe" --headless --convert-to docx --outdir "<prospect-folder>" "<file>.doc"
```

### Extracting text from PDF

```bash
pip install pdfplumber
python -c "
import pdfplumber
with pdfplumber.open('<file>.pdf') as pdf:
    text = '\n'.join(page.extract_text() for page in pdf.pages)
print(text)
"
```

---

## Phase 2: Extract text

**pandoc is NOT installed on this machine.** Do not attempt pandoc for text
extraction — go straight to unpack + extract_text.py.

### Unpack the DOCX

Use the docx skill's unpack.py if available:

```bash
python "<docx-skill-path>/scripts/office/unpack.py" "<file>.docx" "<basename>_unpacked"
```

Fallback (no docx skill):

```bash
python -c "import zipfile; zipfile.ZipFile('<file>.docx').extractall('<basename>_unpacked')"
```

### Extract plain text

Run the bundled extraction script:

```bash
python "<this-skill-path>/scripts/extract_text.py" "<basename>_unpacked/word/document.xml"
```

### Windows rules (do not skip)

- Always unpack into the working project directory — never into `/tmp`
- Use `python` not `python3`
- Name unpack dirs: `<basename>_unpacked`
- Install defusedxml before first use: `pip install defusedxml`
- Set encoding before calling pack.py: `set PYTHONIOENCODING=utf-8`

---

## Phase 3: Review

Read `references/nda-checklist.md` for the full checklist. Apply every item
to the extracted text. The checklist covers:

1. **Type** — mutual vs one-way
2. **Non-solicitation** — flag if >12 months
3. **Indemnification** — flag if present, especially one-sided
4. **Governing law / jurisdiction**
5. **Confidentiality survival period**
6. **Non-compete** — flag if present at all in an NDA
7. **IP assignment / license grants** — flag if present
8. **Standard carve-outs** — verify all four are present
9. **Blanks / fields needing filling**
10. **Additional items** — return/destruction, permitted disclosures, remedies

### Red flags (highlight prominently)

- One-sided indemnification
- Non-solicitation >12 months (24 months is aggressive)
- IP assignment clauses buried in confidentiality sections
- Missing standard carve-outs (especially "independent development")
- Non-compete disguised as non-solicitation
- Unlimited or "perpetual" confidentiality for non-trade-secret info

### Framing

Frame all review output as "observations" or "items to discuss with counsel."
This is a mechanical review, not legal advice.

---

## Phase 4: Fill, Sign & File

### Confirm details before writing

Pre-fill using the hardcoded Great Elm signing information at the top of this
skill. Show the user what you plan to insert and confirm before modifying any XML.

Identify the counterparty company name from the NDA — this becomes the prospect
folder name. Ask the user to confirm spelling if uncertain.

Check for any additional blanks (project descriptions, notice addresses, etc.)
and ask the user before proceeding.

### Create the prospect folder

```python
import pathlib
prospect_folder = pathlib.Path(r"C:\Users\Courtney Stuart\Documents\Searching\Prospects") / "<Counterparty Name>"
prospect_folder.mkdir(parents=True, exist_ok=True)
```

### Edit the XML

Signature blocks follow a predictable pattern: a `<w:r>` with bold label text
("Name:", "Title:") followed by a `<w:r>` with a placeholder or blank underscores.

#### Critical rules (do not skip)

1. **XML entities, not Python Unicode.** The XML stores smart quotes as
   `&#x201C;` and `&#x201D;`, NOT as Python `\u201C`/`\u201D`. When building
   replacement strings, always use the `&#x…;` entity form. A `str.replace`
   with Python Unicode chars will silently match nothing.

2. **Never use blind `str.replace` on duplicate fields.** Mutual NDAs have
   two signature columns (Company and Recipient) with identical labels:
   `Name:`, `Title:`, `Address:`, `By:`. A plain `str.replace` hits the
   **first** occurrence, which is the Company column — putting our info
   where the counterparty is supposed to sign.

   **Always identify the correct section first** by using `w14:paraId`
   attributes on `<w:p>` elements. Steps:
   - Read the full signature block XML
   - Find the `Recipient:` label paragraph and note its `paraId`
   - The Recipient's `By:`, `Name:`, `Title:`, `Address:` fields are the
     paragraphs that follow the `Recipient:` label (in the same column)
   - Note the `paraId` for each Recipient field
   - Use `paraId`-based slicing in Python to target only those paragraphs:

   ```python
   # Target a specific paragraph by paraId
   marker = 'w14:paraId="68C9C265"'  # the Recipient Name paragraph
   idx = xml.index(marker)
   # Find the <w:t> within this paragraph and replace its content
   ```

   **Never modify Company-side fields** — those belong to the counterparty.
   Only fill fields in the Recipient section.

3. **Preamble blank.** The preamble typically has a blank
   (`____________________________`) before `(&#x201C;Recipient&#x201D;)`.
   Replace the underscores with "Great Elm Partners LLC" using the XML entity
   form of the smart quotes in the search string.

4. **Preserve formatting.** Only change text content inside `<w:t>` elements.
   Never alter `<w:rPr>` or `<w:pPr>`.

5. **Verify after editing.** After all replacements, grep the XML to confirm:
   - Company-side fields (`Name:`, `Title:`) are still blank
   - Recipient-side fields have the correct Great Elm info
   - Preamble blank is filled

6. **Confirm before writing.** Always show the user what you plan to insert and
   get confirmation before modifying the XML.

### Repack

**Always use the zipfile approach below.** The docx skill's `pack.py` fails on
this machine because a pip-installed `validators` package shadows the local
`validators` module, causing an unresolvable `ImportError`. Do not attempt
`pack.py` — go straight to zipfile:

```python
import zipfile, pathlib
def repack(src_dir, out_path):
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in pathlib.Path(src_dir).rglob('*'):
            if f.is_file():
                zf.write(f, f.relative_to(src_dir))
repack("<basename>_unpacked", "<NDA Name> - signed.docx")
```

### Convert to PDF (always done after signing)

```bash
"C:/Program Files/LibreOffice/program/soffice.exe" --headless --convert-to pdf --outdir "." "<NDA Name> - signed.docx"
```

If LibreOffice is not installed, tell the user and ask them to open the .docx
in Word and use File → Save As → PDF.

### Move files to prospect folder

```python
import shutil, pathlib
prospect_folder = pathlib.Path(r"C:\Users\Courtney Stuart\Documents\Searching\Prospects") / "<Counterparty Name>"
base = "<NDA Name> - signed"
for fname in [f"{base}.docx", f"{base}.pdf"]:
    src = pathlib.Path(fname)
    if src.exists():
        shutil.move(str(src), str(prospect_folder / fname))
```

Confirm to the user where files landed:

```
C:\Users\Courtney Stuart\Documents\Searching\Prospects\<Counterparty Name>\<NDA Name> - signed.docx
C:\Users\Courtney Stuart\Documents\Searching\Prospects\<Counterparty Name>\<NDA Name> - signed.pdf
```

---

## Known environment issues

| Issue | Root cause | Permanent workaround |
|---|---|---|
| `pack.py` crashes with `ImportError: cannot import name 'DOCXSchemaValidator' from 'validators'` | pip-installed `validators` package shadows the docx skill's local `validators` module | **Never use pack.py.** Always repack with Python zipfile (see Phase 4). |
| `pandoc` not found (exit code 127) | pandoc is not installed | **Never attempt pandoc.** Use unpack.py + `scripts/extract_text.py` for text extraction. |
| `/tmp` path fails in Python | Windows doesn't have `/tmp`; bash may map it to a temp dir that Python can't resolve | **Always unpack into the project working directory**, never `/tmp`. |
| Smart quote replacement silently fails | XML uses `&#x201C;` entities but Python `str.replace` used `\u201C` Unicode literals — they don't match | **Always use XML entity form** (`&#x201C;`, `&#x201D;`, `&#x2019;`) in replacement strings, never Python Unicode escapes. |
| Our info placed in Company signature block | `str.replace` on `Name:` hit the first occurrence (Company column) instead of the Recipient column | **Never blind-replace duplicate labels.** Always use `w14:paraId` targeting to edit only Recipient-section paragraphs. Verify Company fields remain blank after editing. |
