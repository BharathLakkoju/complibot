# Skill: breach-notification-timeline

**Use when** assessing GDPR-33.1, GDPR-33.2, GDPR-34, HIPAA-BAA-reporting, HIPAA-164.404, HIPAA-164.410, SOC2-CC7.3-7.4, SOC2-P6, or ISO-A.5.24-26.

## Input / output
```python
In:  clauses: list[Clause]; framework_limit: Limit; override: Limit | None
     # Limit(hours: int | None, standard: Literal["without_undue_delay","without_unreasonable_delay"] | None)
     # GDPR-33.2: Limit(None, "without_undue_delay"); GDPR-33.1: Limit(72, None); HIPAA-164.410: Limit(1440, "without_unreasonable_delay")
Out: TimelineFact(
       clause_id, quote_span,
       trigger: Literal["awareness","discovery","confirmation","determination","investigation_complete","unspecified"],
       stated: str,                     # verbatim "within five (5) business days"
       hours_min: int | None, hours_max: int | None,   # business days -> range: 5 bd = 120h..216h (weekends + 1 holiday)
       obligation_strength: Literal["shall","reasonable_efforts","may","unspecified"],
       event_scope: Literal["breach","security_incident","both","unspecified"],
       verdict: Literal["within","exceeds","ambiguous","missing"],
       verdict_reason: str)
```

## Method
1. Find candidates: clauses with `(breach|incident|unauthori[sz]ed (access|disclosure))` and `(notify|notification|inform|report)`.
2. Extract the duration (shared parser with retention-period-extraction). Convert to an hours range: hours exact, calendar days ×24, business days as a range (`n×24 + weekends` to `+ public holiday`).
3. Classify the trigger. **Awareness or discovery is required.** `confirmation`, `determination`, or `investigation_complete` can delay notice without limit, so the verdict is at best `ambiguous` and the assessor result is `partial`.
4. Classify obligation strength. `reasonable_efforts` or `may` gives `partial` at best.
5. **Verdict.** Use the effective limit, which is the stricter of framework and override. If `hours_max <= limit` → `within`. If `hours_min > limit` → `exceeds`. If they straddle → `ambiguous`. If the framework standard is only "without undue delay" and no override exists: any fixed window ≤ 72h → `within`; > 72h for a GDPR processor → `exceeds`, because it cannot support the controller's 72h duty (stated as a reasoned inference in `verdict_reason`, not a legal rule); no window at all with "without undue delay" wording → `within`.
6. If no candidate is found, return `missing`. The Orchestrator routes the control to absence mode.

## Edge cases
- **Two-stage notice** ("initial notice within 24h, full report within 10 days"): use the initial notice for the verdict, and record the second as a qualifier.
- **Incident vs breach**: HIPAA BAAs should cover both security incidents (164.314) and breaches (164.410). A clause covering only one gives `partial`.
- **Carve-out for unsuccessful attempts** (pings, port scans): standard practice, and not a red flag when explicit.
- **Law-enforcement delay** (HIPAA 164.412; GDPR allows phased notice under 33(4)): a legitimate qualifier.
- **Conflicting windows** across the MSA and DPA: the stricter applies only if the order-of-precedence clause says the DPA prevails. Find that clause and cite it, otherwise mark `ambiguous`.
