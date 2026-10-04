# Skill: pii-phi-detection

**Use when** (a) tagging clauses at ingestion, (b) redacting anything bound for logs, traces or LLM-eval exports, (c) scoping (no PHI anywhere, so HIPAA controls are likely out of scope), and (d) GDPR-9 and HIPAA-164.514-deid assessments.

## Input / output
```python
In:  text: str; mode: Literal["tag","redact"]; locale_hints: list[str] = ["en-US","en-GB","en-IN"]
Out: Detection(entities: list[Entity(type, char_start, char_end, score, source)], redacted_text: str | None,
               has_phi: bool, has_special_category: bool)
```
Entity types: `PERSON, EMAIL, PHONE, ADDRESS, IP, NATIONAL_ID (SSN, NINO, Aadhaar, PAN), FINANCIAL (IBAN, card), DOB, MRN, HEALTH_PLAN_ID, DIAGNOSIS, MEDICATION, BIOMETRIC, GENETIC`.

## Method
1. **Pattern layer.** Regex with checksums: Luhn for cards, Verhoeff for Aadhaar, the IBAN mod-97 check, and SSN area rules. This is high precision.
2. **NER layer.** Microsoft Presidio with spaCy `en_core_web_lg`, run in-process so no text leaves the VPC. Optionally call Amazon Comprehend Medical `DetectPHI` for PHI types. It is off in the MVP demo, which uses synthetic data only, and must be enabled explicitly by config. Enable it only when the account has signed an AWS BAA. Comprehend Medical is listed on AWS's HIPAA Eligible Services Reference (aws.amazon.com/compliance/hipaa-eligible-services-reference, last updated 3 Sep 2026, checked 2026-10-05). The deploy checklist re-checks this before enabling it.
3. **Context gating.** Contract boilerplate names parties and signatories. Those count as `PERSON` with `context=party`, are not sensitive, and do not set `has_phi`. Set `has_phi` only when a health entity co-occurs with an identifier in the same clause, or the document is a sample record or data export.
4. **Redact mode.** Replace with typed tokens `<EMAIL_1>` that stay stable within a document. Store the mapping only in memory for the request; never persist it.

## Edge cases
- **Example data in DPAs** (e.g. "such as name, email address") are category names, not PII. Don't flag them; the category list feeds GDPR-28.3-scope instead.
- **Health terms in policy prose** ("health information", "diagnosis") with no individual attached mean `has_special_category_topic=true`, not `has_phi`.
- **Indian identifiers.** Aadhaar (12 digits, Verhoeff) and PAN (`[A-Z]{5}[0-9]{4}[A-Z]`) are needed for India-based reviewers' test data.
- **False positives** on clause numbers that look like phone numbers or dates: require a context window and score ≥ 0.6.
- **Never** send unredacted text to OpenRouter in dev. The dev fallback always uses redact mode.
