# Skill: subprocessor-analysis

**Use when** assessing GDPR-28.2-subprocessors, SOC2-CC9.2, ISO-A.5.19-20, ISO-A.5.21-22, HIPAA-BAA-subcontractors, or SOC2-P6. It also feeds cross-border-transfer.

## Input / output
```python
In:  clauses: list[Clause]; params: {min_notice_days: int | None}
Out: SubprocessorAnalysis(
       authorisation: Literal["specific","general","none","unclear"], authorisation_span: Span | None,
       notice_days: int | None, notice_method: Literal["email","website","portal","unspecified"] | None,
       objection_right: bool, objection_remedy: Literal["alternative","termination_with_refund","termination_no_refund","none"] | None,
       flow_down: Literal["equivalent","substantially_similar","confidentiality_only","none"],
       liability_retained: bool,
       listed: list[SubprocessorFact(name, purpose, country_iso2, clause_id, span)],
       list_location: Literal["inline","annex","url","none"],
       findings_hints: list[str])     # e.g. "notice 10d < required 30d"
```

## Method
1. Find the sub-processing clauses (keywords plus the mapper candidates for the controls listed above).
2. Extract each attribute with a constrained LLM call. Every attribute needs a supporting span, otherwise `unclear` / `None`.
3. **Parse the list.** Annex tables come from clause-segmentation schedule rows. For a URL list, record the URL and **do not fetch it** (no network egress from workers to untrusted URLs). The finding notes that the list was not verified.
4. **Compare**: notice_days against `min_notice_days`; flow_down must be `equivalent` (GDPR 28(4) needs the same obligations; HIPAA needs the same restrictions); liability_retained must be true.
5. Hand `listed[].country_iso2` to cross-border-transfer.

## Edge cases
- "Substantially similar" or "no less protective" flow-down: acceptable for GDPR in practice. Mark it compliant with confidence capped at 0.8.
- **Notice by website update with no subscription mechanism**: `partial`, because the controller can't realistically object.
- **Objection remedy = termination without refund**: `partial` and a medium-severity red flag.
- **Affiliates** as a blanket category: needs a list or named entities.
- **Emergency replacement** clauses (notice after the fact for continuity reasons): legitimate when narrow and time-boxed.
