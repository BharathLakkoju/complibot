# Skill: retention-period-extraction

**Use when** assessing GDPR-5.1.e, GDPR-28.3.g-return-delete, SOC2-C1.2, SOC2-P4, ISO-A.8.10, HIPAA-164.316-retention, HIPAA-BAA-termination, or internal `max_retention_months` / `max_deletion_days` overrides.

## Input / output
```python
In:  clauses: list[Clause]; control_params: dict   # e.g. {"max_deletion_days": 30}
Out: list[RetentionFact(
        clause_id, quote_span: tuple[int,int],
        data_category: str | None,            # "personal data", "backups", "logs", "PHI", "documentation"
        trigger: Literal["termination","collection","last_activity","request","end_of_purpose","creation","unspecified"],
        duration: Duration | None,            # ISO 8601, e.g. "P30D", "P6Y"
        bound: Literal["max","min","exact","unbounded","criteria_only"],
        qualifiers: list[str],                # "unless required by law", "in accordance with backup rotation"
        compare: Literal["within","exceeds","no_limit","n/a"])]   # vs params
```

## Method
1. Find candidates with regex: `(?i)(retain|keep|store|delete|destroy|purge|erase|return).{0,120}`, numeric and worded durations ("thirty (30) days", "six years"), and unbounded terms (indefinitely, perpetuity, "as long as necessary").
2. Parse durations deterministically: worded and numeric forms, business days as 1.4 calendar days for comparison only (the original unit is kept), months as P{n}M.
3. Identify the trigger and the bound with a small LLM call, constrained to the enum. Feed it only the candidate sentence plus the definitions of the terms it uses.
4. **Compare to params.** `max_*`: duration > param → `exceeds`. Unbounded → `no_limit`. Criteria only (e.g. "for as long as the account is active") → `criteria_only`. The assessor treats that as `partial` unless the control accepts criteria (GDPR-5.1.e does).
5. Every fact has a quote span. Facts without spans are dropped.

## Edge cases
- **Backups**: "deleted within 30 days, except backups, which are overwritten per standard rotation". Emit two facts, and treat the backup one as `unbounded` unless a rotation period is stated.
- **Legal hold or statutory retention** ("unless required by law") is a legitimate qualifier, not a red flag.
- **Minimum vs maximum**: HIPAA's 6 years is a minimum for documentation. "Retain for at least 6 years" is compliant, and "delete after 3 years" is a gap.
- **Conflicting clauses** (MSA says 90 days, DPA says 30): emit both, set `conflict=true`, and the assessor marks the control `partial` with both quotes as evidence links.
- **Relative references** ("the period set out in Schedule 3"): resolve via section_path. If the target can't be found, `bound=criteria_only` with the warning `unresolved_reference`.
