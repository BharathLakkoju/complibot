# Rule 03: Severity rubric

Severity is the **impact if the gap is exploited or the obligation is breached**. It is independent of how likely that is, which is tracked as `likelihood`. Start from the control's `default_severity`, then adjust by at most one step with a stated reason. More than one step requires a reason that names a criterion from this table.

| Severity | Weight | Criteria (any) | Examples |
|----------|--------|----------------|----------|
| critical | 5 | Mandatory statutory element absent or contradicted **and** regulator/notification exposure; PHI/special-category data shared without a BAA/Art. 9 basis; breach notice window that makes the downstream statutory deadline impossible | No BAA while PHI flows; processor breach notice "within 30 days"; "may use Customer Data for any purpose" |
| high | 4 | Core protective control missing or materially weakened; unrestricted transfers; no subprocessor control | Subprocessors engaged without notice; "industry-standard security" with no annex; legacy SCCs |
| medium | 3 | Control present but incomplete or soft-worded; operational gap with compensating controls likely | Audit limited to SOC 2 report; retention "as long as necessary" without criteria; no TIA |
| low | 2 | Documentation or hygiene gap; best-practice deviation | No review cycle on policy; training frequency unstated |
| info | 1 | Observation, no gap | Stricter than required; useful context |

**Likelihood** (weights 1–5): rare, unlikely, possible, likely, almost_certain. Base it on doc type and data volume. A DPA covering bulk customer PII is `likely` for breach-related gaps. A policy that is never operationalised is `possible`.

`risk_score = severity_weight × likelihood_weight` (1–25). The UI sorts by it, and the report's top risks use it.

**Modifiers**
- Special-category data or PHI is present (pii-phi-detection): +1 step for security, breach, or transfer controls.
- Internal-pack `severity_floor`: the severity is never set below it.
- `kind=compliant`: severity is `info` (stored for coverage, not published in the MVP). Controls that do not apply are out of scope, not findings.
- `kind=partial`: at most one step below the severity a violation or gap of the same control would get.
- Reviewers may change severity through **Edit**, with a reason of at least 10 chars (D-12). The AI original is kept in the decision's `before`.
