# GDPR pack (Regulation (EU) 2016/679)

**Focus.** Contracts where our user is a controller engaging a processor, or is itself a processor: DPAs, MSAs with data-processing terms, privacy notices. Article 28(3) is the backbone because it lists the mandatory DPA content.

**Covered:** Art. 5(1)(e), 6, 9, 13/14, 15–22 (via 28(3)(e)), 25, 28(1)–(4), 30, 32, 33, 34, 35/36 (via 28(3)(f)), 44–46, 49.
**Not covered (MVP):** Art. 22 automated decisions, Art. 27 EU representative, Art. 37–39 DPO, national derogations, UK GDPR, and Swiss FADP. The UK IDTA/Addendum is mentioned only as a transfer red flag.

**Notes**
- Standard Contractual Clauses: Commission Implementing Decision (EU) 2021/914 (the "new SCCs"). References to the 2010 / 2004 SCC decisions are a red flag. Those clauses were repealed, and the transition period ended 27 Dec 2022.
- EU–US Data Privacy Framework: Commission Implementing Decision (EU) 2023/1795 of 10 July 2023. **In force as of 5 Oct 2026.** The General Court dismissed the annulment action in *Latombe v Commission* (T-553/23, 3 Sep 2025), and the appeal (C-703/25 P, lodged 31 Oct 2025) is pending before the Court of Justice. The pack treats DPF as a valid Art. 45 mechanism only when the importer is DPF-certified. Because the appeal is pending, the TIA control flags reliance on DPF alone, with no fallback, as `medium`.
- Art. 33(1) is the controller's 72-hour duty to the supervisory authority. A processor contract should require notice to the controller "without undue delay" (Art. 33(2)). Market practice is a fixed window (24–72h) so the controller can meet its own 72 hours. The internal pack sets the preferred window.

**Verification (checked 2026-10-05)**
- `GDPR-DPF`: status as above. Sources: CJEU press release No 106/25 on T-553/23 (curia.europa.eu); Official Journal notice of appeal C-703/25 P, OJ C/2025/6610 (eur-lex.europa.eu). The deploy checklist re-checks the case before each public demo ([deploy-to-aws](../../build/skills/deploy-to-aws/SKILL.md), step 8).
- SOC 2 crosswalk targets were checked against AICPA TSP section 100, the 2017 TSC with revised points of focus (2022):
  - `GDPR-28.3.b` maps to CC1.1 (standards of conduct, extended to outsourced providers) and C1.1. It no longer maps to CC1.4, which covers competence and background checks.
  - `GDPR-9` maps to P3.2 (explicit consent).
  - `GDPR-30` maps to P6.7, whose point of focus is to identify the types of personal information and how they are handled. It no longer maps to P8.1, which covers complaints and monitoring.
- All crosswalks are **indicative**. They are our mapping, not an official AICPA or ISO crosswalk.
