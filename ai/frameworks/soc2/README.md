# SOC 2 pack (AICPA Trust Services Criteria, 2017, with revised points of focus 2022)

**Copyright.** The TSC text is © AICPA. This pack uses **criterion IDs only** (e.g. `CC6.1`), and every requirement is written in our own words. Do not paste the criteria or points of focus.

**How SOC 2 shows up in documents.** SOC 2 is an attestation of a service organisation's controls, not a contract standard. Documents trigger it in two ways:
1. **Vendor contracts and DPAs**, where the vendor commits to controls (encryption, access, IR) or to providing a SOC 2 Type II report.
2. **Internal security policies** that the auditor will test against the criteria.

**Categories covered.** Security (Common Criteria CC1–CC9) is mandatory in every SOC 2. Availability (A1), Processing Integrity (PI1), Confidentiality (C1), and Privacy (P1–P8) are opt-in. Each review picks categories via `params.categories`.

**Verification (checked 2026-10-05)**
Every criterion ID in this pack and in the other packs' SOC 2 crosswalks was checked against AICPA TSP section 100: *2017 Trust Services Criteria (With Revised Points of Focus – 2022)*. The copy checked is © 2024 AICPA, linked from aicpa-cima.com. The 2022 revision changed only the points of focus. **Criterion numbering did not change.** The IDs used here:
- `SOC2-PI1` → PI1.2 (system inputs), PI1.3 (system processing), and PI1.4 (making output available or delivering it). PI1.1 (processing specifications) and PI1.5 (storing inputs and outputs) are not used.
- `SOC2-P4` → P4.2 (retention) and P4.3 (secure disposal).
- `SOC2-P6` → P6.1 (disclosure to third parties for identified purposes), P6.5 (vendors commit to notify the entity of unauthorised disclosures), and P6.6 (breach and incident notification to data subjects and regulators).
- Personnel mappings: CC1.1 covers standards of conduct, including confidentiality expectations for staff and outsourced providers. CC1.4 covers competence and background checks, so CC1.4 is used only for screening (ISO A.6.1).

Cross-framework mappings are **indicative**: they are our judgment, not an official AICPA crosswalk.
