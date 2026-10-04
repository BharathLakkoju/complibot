# Framework rule packs

One directory per framework: `pack.yaml` (machine-readable, loaded by the Orchestrator, Mapper, and Assessor) plus a `README.md` (scope and caveats). Packs are versioned (semver), and each review pins the version it used.

| Pack | Code | Controls in `pack.yaml` | MVP maturity | Scope |
|------|------|------|------|-------|
| [gdpr](gdpr/) | `GDPR` | 20 | **Full**, evaluated on gold v0 | Processor contracts (DPAs), transfers, breach, retention, rights |
| [soc2](soc2/) | `SOC2` | 19 | **Full**, evaluated on gold v0 | Trust Services Criteria: Security (CC), Availability, Processing Integrity, Confidentiality, Privacy |
| [iso27001](iso27001/) | `ISO27001` | 22 entries (~30 Annex A controls) | `Preview · Limited control coverage` | ISO/IEC 27001:2022 Annex A, all four themes |
| [hipaa](hipaa/) | `HIPAA` | 20 | `Preview · Limited control coverage` | Privacy, Security, and Breach Notification Rules + BAA content |
| [internal-policy](internal-policy/) | `INTERNAL` | 5 (sample/template) | `Preview` (sample pack + validated YAML upload, D-07) | How a company defines and parameterizes its own controls |

Engineering sized the Preview packs at 5–8 controls. These packs are larger, but **only GDPR and SOC 2 are evaluated and claimed in depth in the MVP**. Preview packs show "not yet measured" on the metrics page until gold v1 covers them (PRD §5, C-20). Counts are checked by `make packs-validate` against this table.

## Control entry schema
```yaml
- id: GDPR-33.2                 # unique within the pack; stable forever (deprecate, never reuse)
  ref: "Art. 33(2)"             # official citation; must be in refs whitelist (rules/02)
  title: Processor notifies controller of breaches
  requirement: >                # plain-language paraphrase. Never verbatim ISO/AICPA text.
  satisfied_by:                 # elements the assessor checks one by one; ids used by remediation covers_elements
    - { id: e1, text: "..." }
  red_flags:
    - { id: rf1, kind: regex, pattern: "(?i)...", note: "..." }   # deterministic, run by mapper
    - { id: rf2, kind: semantic, text: "..." }                    # given to the LLM as a hint
  default_severity: high        # critical | high | medium | low | info
  doc_types: [dpa, msa]         # where the control is expected
  mandatory_for: [dpa]          # absence => kind=gap only for these doc types; else out of scope (coverage)
  applies_when: "processor processes personal data on behalf of controller"
  params: { max_notification_hours: null }   # overridable by the internal pack
  skills: [breach-notification-timeline]
  mappings:                     # indicative crosswalk, not equivalence
    iso27001: [A.5.24, A.5.26]
    soc2: [CC7.4]
    hipaa: ["164.410"]
  keywords: [breach, incident, notify]
  verify: confirmed             # confirmed | unverified (citation or mapping still needs a human check against the primary source)
```

## Authoring rules
1. **Copyright.** ISO/IEC 27001 and the AICPA TSC are copyrighted. Use control **numbers and short titles** only, and write requirements in your own words. GDPR (EU law) and HIPAA (US federal regulation, 45 CFR) may be cited by article or section.
2. **Accuracy.** Only cite numbers you are sure of. Anything uncertain gets `verify: unverified` and is listed, with what is still to be checked, in the pack README's Verification section. CI fails if an `unverified` control is loaded with `env=prod` and `strict_citations=true`. As of 2026-10-05, every control in the GDPR, SOC 2, ISO 27001 and HIPAA packs is `confirmed`, and each pack README records its primary sources. Internal Policy controls cite the organisation's own policy and have no `verify` field.
3. **Mappings are indicative.** The crosswalk helps reviewers pivot between frameworks. A finding never states that satisfying one framework satisfies another.
4. **Red-flag regexes** must have a positive and a negative example in `eval/fixtures/red_flags/<pack>.yaml`. CI runs them.
5. A new pack follows `build/skills/add-framework-pack/SKILL.md`.
6. **Internal Policy uploads** (D-07) are validated against this schema. Errors are reported with line numbers (AC-ING-04), and a valid upload is stored as a tenant-scoped pack with a version.
