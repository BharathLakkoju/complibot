# Rule 01: Cite a verbatim quote and span, or abstain

**Applies to:** Assessor, Remediation Writer (no new claims about the document), Verifier, Report Composer.

1. Every finding with `kind` ∈ {violation, partial, compliant} has 1–3 `citations`. Each citation's `quote` equals `docText.slice(charStart, charEnd)` byte for byte after normalization, is ≤ 400 chars, sits inside one chunk, and carries `documentId`, `chunkId`, and `page` where known.
2. A `kind=gap` (absence) finding has no citations and **must** carry `absenceEvidence` (sections searched, queries, max similarity). Absence findings are capped at 0.80 confidence, carry the system flag `absence_finding`, and are always shown labelled "Not found in document", never as a quote.
3. If the model cannot produce a supporting span, it sets `abstain=true`. An abstention is a valid outcome: it is logged for eval, not shown as a finding, and the control appears in report coverage as `abstained`. A citation that fails verification twice is **discarded and counted** (`review.status.discardedCount`, shown in the analysis summary).
4. Paraphrases, ellipses ("…"), merged sentences, and "corrected" typos are not quotes. The verifier rejects them.
5. Legal references (article or section numbers) may only come from the control card's `ref` and the pack's `refs_whitelist`. The model never cites law from memory.
6. The UI renders every quote as a link that scrolls the document viewer to the exact span and highlights it. A quote that can't be highlighted is a bug.
