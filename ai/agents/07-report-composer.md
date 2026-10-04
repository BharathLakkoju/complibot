# Agent 7: Report Composer

**Purpose.** Produces **one report per project** (D-06), combining the selected frameworks into per-framework sections, in canonical JSON plus a PDF rendering (Jinja2 HTML → WeasyPrint). Reports are **versioned**. MVP sign-off is an **attestation that locks the version** (D-02). Any later change creates v(n+1) and marks the prior version `superseded`. The LLM writes only the executive summary. Every number and table comes from the database.

## Input
```python
class ReportTask(BaseModel):
    project_id: str
    tenant_id: str
    mode: Literal["final","draft"] = "final"   # draft = DRAFT-watermarked export (PRD Q-10 recommended default)
    requested_by: str
```

## Output
```python
class ReportVersion(BaseModel):
    report_id: str                            # one per project
    version: int                              # v1, v2, ...
    status: Literal["draft","signed","superseded"]
    generated_at: datetime
    disclaimer: str                           # rules/02 text, verbatim
    scope: ReportScope                        # documents (name, pages), frameworks + pack versions (+ Preview label), models, prompt versions
    executive_summary: constr(max_length=2500)
    sections: list[FrameworkSection]          # one per selected framework:
        # summary (severity x decision), findings (accepted/edited, by severity -> control),
        # open escalations (status=escalated, assignee, reason), coverage (assessed / abstained / out of scope / unprocessed)
    appendix_rejected: list[Finding]          # rejected findings with decider + reason
    evidence_trail: EvidenceTrail             # audit digest (decisions, overrides, sign-off), model IDs, prompt + pack versions
    blocking: list[str]                       # finding ids with status=open (non-empty => sign-off disabled)
    signoff: Signoff | None                   # {signer_id, attested_at, statement}; Owner only
```

## Inclusion rules (final report)
| Finding status | Final report | Draft export |
|---|---|---|
| `accepted`, `edited` | Findings section (edited shows "Accepted · edited" and the diff to the AI original) | yes |
| `escalated` | "Open escalations" (human-decided routing: assignee + reason) | yes |
| `rejected` | Appendix with reason | yes |
| `open` (undecided) | **Excluded.** Listed only as a blocking count with links (AC-RPT-03) | yes, marked "Undecided" under a DRAFT watermark |

Sign-off is blocked while any finding is `open`. Escalations are human decisions, so they do not block sign-off, but the completeness check shows them as a warning ("1 escalation open"). A framework with no published findings shows "No issues found for <framework> in this document" with coverage stats and **[Confirm no findings]**, which is recorded in the audit log (AC-RPT-07).

## System prompt (executive summary)
```
Write an executive summary (<= 300 words) of a compliance document review for a non-specialist reader.
Use ONLY the statistics and finding titles in <report_data>, which contains human-decided findings only.
Do not introduce new findings, numbers, or legal conclusions. Lead with the top three risks by riskScore among
accepted or edited findings, naming the control and document section, then mention open escalations.
Never say the organisation "is compliant" or "is non-compliant"; say what the reviewed text does or does not address.
Return only via emit_summary.
```

## Tools
`db.report_data(project_id)`, `templates.render_html`, `weasyprint.render_pdf`, `s3.put` (private bucket, SSE-S3, tenant-prefixed key), `audit.append`.

## Guardrails
- **Number check.** Every number in the summary must appear in the stats. If not, regenerate once, then fall back to a templated summary.
- **Draft marking.** Unsigned versions carry a `DRAFT` watermark and `status: provisional` in the JSON. File names include the version and date (AC-RPT-06).
- **Sign-off (Owner only, AC-AUTH-06 / AC-RPT-04).** Requires zero `open` findings and a ticked attestation. It records signer, time, and statement in the report and the audit log, and locks the version. Any decision change after that creates v(n+1) and marks vn `superseded`; vn stays viewable (AC-RPT-05).
- **Immutable versions.** A generated version's JSON and PDF objects are never overwritten. A rerun creates a new version.
- The disclaimer is on the cover and in every page footer. Preview packs (ISO 27001, HIPAA, Internal) are labelled `Preview · Limited control coverage`.
- **Stretch** (FR-25, AC-RPT-09; not in the MVP): SHA-256 document hash, KMS-signed PDF, S3 Object Lock, and a tamper-evident hash chain over `review_events`.

## Failure behaviour
If PDF rendering fails, the JSON is still delivered and the UI offers a PDF retry (AC-RPT-08). If summary generation fails, the templated summary is used.

## Events emitted
None on the review socket. Report generation is a REST resource (`POST /v1/projects/{id}/reports` → `202`, then `GET` the version status). Sign-off and "Confirm no findings" are appended to the project audit log.
