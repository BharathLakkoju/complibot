# Internal Policy pack (template)

Shows how a company encodes **its own** contracting and security standards as reviewable controls. It is usually stricter than the law (e.g. "vendors must notify us of incidents within 48h", "EU customer data stays in the EU").

**Three mechanisms**
1. **New controls.** Company-specific rules with `INT-` IDs (e.g. liability cap carve-outs, approved hosting regions, no AI training on our data).
2. **`overrides`.** These tighten parameters of controls in other packs without forking them. For example, setting `GDPR-33.2.params.max_notification_hours: 48` makes the breach-timeline skill flag 72h as `partial`, even though 72h passes GDPR on its face.
3. **`preferences`.** Fallback language and parameters the Remediation Writer uses for suggested clauses.

**Authoring**
- Copy `pack.yaml` to `internal-policy/<org-slug>/pack.yaml`, change `pack.id` and `owner`, and edit the controls.
- `approved_by` and `effective_date` are required. The report prints them so auditors can trace the standard to an approved policy.
- Uploads via the UI (`POST /frameworks/internal`) go through the same JSON-Schema validation and red-flag regex tests as the shipped packs.
