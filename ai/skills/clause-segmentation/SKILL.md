# Skill: clause-segmentation

**Use when** a document has been normalized and needs splitting into citable clauses. The ingestion agent uses it, and so does the assessor when it needs a sub-clause span.

## Input / output
```python
In:  normalized_text: str; page_offsets: list[int]; source_format: Literal["pdf","docx","txt"]; docx_numbering: list[NumberedPara] | None
Out: list[Clause]   # persisted as `chunk` rows (PRD §12); see agents/02 (clause_id, section_path, heading, char_start, char_end, kind, page_start, page_end)
```

## Method
1. **Structural pass (deterministic).** Detect headings and numbering with regex for patterns like `^\s*(\d+(\.\d+)*|[A-Z]\.|\([a-z]\)|\([ivx]+\)|Article \d+|Section \d+|Schedule \d+|Annex [A-Z0-9]+)`. DOCX numbering comes from `numPr` and is authoritative. Build the section tree and `section_path` (e.g. `9.2(b)`).
2. **Sentence pass.** Inside each leaf section, split into sentences with a legal-aware splitter that does not split on `e.g.`, `i.e.`, `Inc.`, `No.`, `Art.`, `U.S.`, or `§`.
3. **Group to clauses.** A clause is the smallest unit holding one obligation or definition. Keep a list lead-in ("The Processor shall:") with its items as one clause, plus child clauses per item, so citations can target either level.
4. **Classify `kind`** with heuristics: "means"/"shall mean" → definition; "WHEREAS" → recital; shall/must/will/may not → obligation; signature blocks → signature; Schedules/Annexes → schedule.
5. **Ambiguity repair (LLM, optional).** Only segments longer than 1,500 chars or shorter than 40 chars are sent to the boundary-repair prompt (agents/02). The LLM returns offsets only.
6. **Invariants.** No overlaps among clauses at the same level, `text == normalized_text[s:e]`, and `page_start` is derived from `page_offsets` with bisect.

## Edge cases
- **Tables** (e.g. a subprocessor list or TOMs annex): each row becomes a clause with `kind=schedule`, and cells are joined with ` | `.
- **Cross-page clauses**: allowed. `page_start` and `page_end` differ, and the citation shows the start page.
- **Definitions used elsewhere**: build a `defined_terms` map (term → clause_id) for the assessor's context lookup.
- **Incorporated by reference** ("the DPA at www…"): emit a clause with the warning `external_incorporation`. The assessor must not assume the referenced content.
- **Redlines / tracked changes** in DOCX: accept insertions and drop deletions, and warn. Comments are ignored, never treated as text.
- **Two-column text-layer PDFs**: use pdfplumber word positions to order columns. If the column detection score is low, add a warning. Scanned PDFs never reach this skill: they are rejected at upload (OCR is Phase 2).
