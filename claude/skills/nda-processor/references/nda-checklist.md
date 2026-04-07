# NDA Review Checklist

Detailed guide for reviewing Non-Disclosure Agreements. Apply every section
to the extracted NDA text. When a clause is absent, note that too — missing
provisions can be as significant as problematic ones.

## 1. Agreement Type

**What to look for:** Does the NDA protect information flowing in one direction
or both?

- **Mutual (bilateral):** Both parties disclose and receive confidential info.
  Look for symmetric language: "each party," "the disclosing party / receiving
  party."
- **One-way (unilateral):** Only one party discloses. The other is purely a
  recipient. Look for asymmetric language: "the Company" vs "the Recipient."

**Why it matters:** A one-way NDA from a counterparty means your information
gets no protection. If both sides will share sensitive info, push for mutual.

## 2. Non-Solicitation

**What to look for:** A clause preventing the recipient from hiring or
soliciting the discloser's employees.

**Key details to extract:**
- Duration (months from signing or from termination?)
- Scope: direct solicitation only, or also indirect?
- Carve-out for general recruitment (job postings not targeted at the
  company's employees)?

**Flag if:**
- Period exceeds 12 months (aggressive; 24 months is a red flag)
- No carve-out for general solicitation
- Covers employees the recipient never interacted with

## 3. Indemnification

**What to look for:** A clause requiring one or both parties to compensate
the other for losses arising from breach.

**Key details to extract:**
- Who indemnifies whom? (one-sided vs mutual)
- Scope: "any and all losses" vs limited categories
- Does it include legal fees and disbursements?
- Cap on liability?

**Flag if:**
- One-sided indemnification (recipient indemnifies company but not vice versa)
- Uncapped liability exposure
- Covers indirect/consequential damages
- Broad "indemnify and hold harmless" language

## 4. Governing Law and Jurisdiction

**What to look for:** Which country/state's law governs disputes, and where
must disputes be heard.

**Key details to extract:**
- Governing law (e.g., "laws of England and Wales," "State of Delaware")
- Dispute resolution: courts, arbitration, or mediation first?
- Exclusive vs non-exclusive jurisdiction
- Jury trial waiver?

**Flag if:**
- Governing law is in a jurisdiction unfavorable to the user's entity
- Exclusive jurisdiction in a distant or unfamiliar forum
- No dispute resolution mechanism specified

## 5. Confidentiality Survival Period

**What to look for:** How long confidentiality obligations last after
termination or expiration.

**Key details to extract:**
- Duration (years from signing, from disclosure, or from termination)
- Does it differ for trade secrets vs other confidential info?
- "Perpetual" or "indefinite" language

**Flag if:**
- Period exceeds 5 years (unusual for most commercial NDAs)
- Perpetual obligations (acceptable for trade secrets, aggressive for
  general business info)
- No stated duration (creates ambiguity)

## 6. Non-Compete Provisions

**What to look for:** Any restriction on the recipient competing with the
discloser. Sometimes disguised within non-solicitation or confidentiality
clauses.

**Key details to extract:**
- Duration and geographic scope
- Definition of "competing business"
- Whether it restricts specific individuals or the entire entity

**Flag if:**
- Any non-compete is present in what is ostensibly "just an NDA"
- Broad definition of competition
- Long duration or wide geography
- Hidden in the definitions section or non-solicitation clause

## 7. IP Assignment and License Grants

**What to look for:** Clauses that transfer intellectual property rights
or grant licenses beyond what the NDA's purpose requires.

**Key details to extract:**
- Any assignment of IP created during discussions
- License grants (exclusive vs non-exclusive)
- Scope of licensed rights
- Whether pre-existing IP is carved out

**Flag if:**
- Any IP assignment clause (this does not belong in a standard NDA)
- Broad license grants
- No carve-out for pre-existing IP
- Language covering derivative works

## 8. Standard Carve-Outs (Exceptions to Confidentiality)

Every well-drafted NDA should contain these four exceptions. Their absence
is a yellow flag.

1. **Public information:** Info that is or becomes publicly available through
   no fault of the recipient
2. **Prior possession:** Info already in recipient's possession before
   disclosure (provable)
3. **Independent development:** Info independently developed without use of
   the confidential information
4. **Third-party receipt:** Info received from a third party not under
   confidentiality obligation

**Also check for:**
- Compelled disclosure carve-out (court orders / regulatory demands)
- Whether carve-outs are narrowly worded (e.g., requiring written proof
  for prior possession, which may be impractical)

## 9. Blanks and Fields to Fill

**What to look for:** Placeholder text, underlines, brackets, or blank
spaces indicating fields the parties must complete.

Common fields:
- Party names and entity types
- Registered addresses
- Date of agreement
- Authorized signer names and titles
- Project or transaction description
- Specific "Authorized Representatives" lists

**How to identify in XML:** Look for:
- `<w:t>` elements containing only underscores (`_____`)
- `<w:t>` elements with `[brackets]` or `{braces}`
- Empty `<w:t>` elements following label runs (e.g., after "Name:")
- Red-colored or highlighted text (often used for fill-in instructions)

## 10. Additional Items

Check for these less common but potentially significant provisions:

- **Return/destruction of information:** How quickly? Certification required?
  Can the recipient retain copies for compliance purposes?
- **Permitted disclosures:** To advisors, affiliates, employees? Under what
  conditions? Must those parties sign sub-NDAs?
- **Remedies for breach:** Injunctive relief, specific performance, damages?
  Is the threshold for seeking injunctive relief lowered?
- **No warranty on information:** Does the discloser disclaim accuracy of
  the information provided? (Common in sell-side process NDAs)
- **No obligation to transact:** Does the NDA clarify that neither party is
  obligated to proceed with any deal? (Standard but worth noting if absent)
- **Amendment requirements:** Written only? By authorized officers?
- **Assignment restrictions:** Can either party assign the NDA?
- **Severability:** If one clause is invalid, does the rest survive?
- **Entire agreement:** Does it supersede prior agreements on the subject?
- **Counterparts and electronic signatures:** Are electronic signatures
  accepted? (Important for remote execution)
