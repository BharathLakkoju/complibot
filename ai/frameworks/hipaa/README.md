# HIPAA pack (45 CFR Parts 160 and 164)

> **MVP maturity: `Preview · Limited control coverage`** (PRD §5). Not evaluated or claimed in depth until gold set v1. The metrics page shows "not yet measured".

**Covered**
- **Privacy Rule** (Part 164 Subpart E): minimum necessary 164.502(b) / 164.514(d), BA disclosures 164.502(e), BAA content 164.504(e), de-identification 164.514(a)–(b), individual rights 164.524 / 164.526 / 164.528, documentation retention 164.530(j).
- **Security Rule** (Subpart C): administrative 164.308, physical 164.310, technical 164.312, BA contracts 164.314(a), documentation 164.316.
- **Breach Notification Rule** (Subpart D): 164.402 definitions, 164.404 individuals, 164.406 media, 164.408 Secretary, 164.410 BA to covered entity.

**BAA focus.** A Business Associate Agreement is the most common HIPAA document users will upload. Controls tagged `baa_element: true` make up the BAA checklist. When `doc_type=baa`, every one of them is `mandatory_for`.

**Addressable ≠ optional.** Under the current Security Rule (eCFR, current to 1 Oct 2026), encryption (164.312(a)(2)(iv), 164.312(e)(2)(ii)) is *addressable*. The entity must implement it or document why an equivalent alternative is reasonable. The assessor treats "no encryption and no documented alternative" as a gap.

**Key numbers**
- Breach notice to individuals: without unreasonable delay and no later than **60 calendar days** after discovery (164.404(b)).
- BA notice to the covered entity: same outer limit of **60 days** (164.410(b)). Market practice is much shorter (e.g. 5–10 business days), and the internal pack can set the preferred window.
- Media notice when > 500 residents of a State or jurisdiction are affected (164.406). Secretary notice: contemporaneous for ≥ 500 individuals, annual log for < 500 (within 60 days of calendar year end) (164.408).
- Documentation retention: **6 years** from creation or last effective date (164.316(b)(2)(i); 164.530(j)(2)).

**BAA elements in 164.504(e)(2)(ii) (checked in the eCFR, current to 2026-10-01)**

| Letter | Requirement | Control |
|---|---|---|
| (A) | No use or disclosure beyond the contract or as required by law | `HIPAA-BAA-permitted-uses` (with (e)(2)(i)) |
| (B) | Appropriate safeguards; Subpart C for ePHI | `HIPAA-BAA-safeguards` (with 164.314(a)(2)(i)(A)) |
| (C) | Report non-permitted use or disclosure, including breaches of unsecured PHI per 164.410 | `HIPAA-BAA-reporting` (with 164.314(a)(2)(i)(C)) |
| (D) | Subcontractors agree to the same restrictions (per 164.502(e)(1)(ii)) | `HIPAA-BAA-subcontractors` (with 164.314(a)(2)(i)(B)) |
| (E), (F), (G) | Access (164.524), amendment (164.526), accounting of disclosures (164.528) | `HIPAA-BAA-individual-rights` |
| (H) | When the BA carries out a covered entity's Privacy Rule obligation, it complies with the requirements that apply to that obligation | Not a separate control; relevant only when the BA performs CE obligations |
| (I) | Internal practices, books and records available to the Secretary | `HIPAA-BAA-books-records` |
| (J) | Return or destroy PHI at termination, or extend protections if infeasible | `HIPAA-BAA-termination` (with (e)(2)(iii), the CE's right to terminate) |

**Security Rule NPRM (status 2026-10-05).** HHS proposed the Security Rule changes on 6 Jan 2025 (90 FR 898, RIN 0945-AA22). The proposal would make encryption and other specifications required. **No final rule has been published.** The eCFR text of 164.312 still marks encryption as Addressable. The 2026 Unified Agenda lists the rule as a Long-Term Action with final action projected for 07/2027. `HIPAA-164.312-enc` therefore keeps the current, addressable wording. Sources: ecfr.gov (45 CFR 164.312, 164.314, 164.504); federalregister.gov 2024-30983; reginfo.gov RIN 0945-AA22. The deploy checklist re-checks this before each public demo ([deploy-to-aws](../../build/skills/deploy-to-aws/SKILL.md), step 8).

**Out of scope:** 42 CFR Part 2 (SUD records) and state laws (e.g. CMIA).
