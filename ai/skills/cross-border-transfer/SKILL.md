# Skill: cross-border-transfer

**Use when** assessing GDPR-44-transfers, GDPR-DPF, ISO-A.5.14, ISO-A.5.23, or INT-RES-01.

## Input / output
```python
In:  clauses: list[Clause]; subprocessors: list[SubprocessorFact] | None   # from subprocessor-analysis
     exporter_region: Literal["EEA","UK","CH","US","IN","other"]; approved_regions: list[str] | None
Out: TransferAnalysis(
       locations: list[Location(country_iso2, kind: storage|processing|support_access|subprocessor, clause_id, span)],
       mechanisms: list[Mechanism(type: adequacy|scc_2021|scc_legacy|bcr|dpf|uk_idta|uk_addendum|derogation_49|none|unclear,
                                  module: Literal["C2C","C2P","P2P","P2C"] | None, clause_id, span)],
       tia_commitment: bool, onward_transfer_restricted: bool,
       unmatched_locations: list[str],   # third-country locations with no mechanism
       verdict: Literal["covered","partially_covered","uncovered","no_transfer","unknown"])
```

## Method
1. **Locations.** Gazetteer of country names, ISO codes, and AWS/GCP/Azure region codes mapped to countries (e.g. `eu-west-1` → IE, `ap-south-1` → IN). Include support-access phrases ("follow-the-sun support", "personnel located in").
2. **Classify each location** against the exporter's region. For EEA exporters, check the adequacy list (config `adequacy_countries.yaml`, which carries a `last_reviewed` date). That file is the single place to maintain; no hard-coding in prompts.
3. **Detect mechanisms.** Regex for `2021/914`, "Standard Contractual Clauses", "Module (One|Two|Three|Four)", "Binding Corporate Rules", "Data Privacy Framework", "International Data Transfer (Agreement|Addendum)". Detect legacy decisions `2010/87/EU`, `2001/497/EC`, `2004/915/EC` and "Privacy Shield" as red flags.
4. **Module check**: the DPA role should match the module (controller→processor = Module 2, processor→sub-processor = Module 3).
5. **Join** locations and subprocessor countries with mechanisms. Anything left over goes to `unmatched_locations`.
6. Verdict: all covered with a TIA → `covered`. Mechanism present but no TIA or a module mismatch → `partially_covered`. Third country with no mechanism → `uncovered`.

## Edge cases
- **"Data may be accessed from any country where we or our subprocessors operate"**: locations unknown, so `unknown` plus red flag rf3. Do not assume.
- **Remote access is a transfer** under the EDPB view, so support access from India or the US counts even if storage is in the EU.
- **DPF**: valid only if the US recipient is self-certified. Recommend a fallback mechanism. DPF status is a config flag reviewed at release.
- **UK and Swiss exporters**: the UK IDTA or UK Addendum to the EU SCCs, and Swiss FADP adaptations. MVP only detects them and marks them `unclear` for human review.
- **Intra-group transfers** still need a mechanism (BCRs or SCCs). "Affiliates" with no list is a red flag.
