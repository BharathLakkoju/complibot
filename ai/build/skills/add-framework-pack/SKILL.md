# Build skill: add a new framework pack

**Use when** adding a framework (e.g. PCI DSS, DORA, India DPDP Act) or a new version of an existing one.

## Steps
1. **Scope.** List 12–20 controls that contracts and policies actually trigger. Write down the authoritative source and edition, plus its licence: is verbatim text allowed? ISO, AICPA, and PCI SSC texts are not, so use numbers, short titles, and paraphrases.
2. **Scaffold.** Run `make pack-new ID=<id>`, which copies `ai/frameworks/_template/` to `ai/frameworks/<id>/{pack.yaml,README.md}`. Set `pack.version: 0.1.0`.
3. **Author controls** per the schema in `ai/frameworks/README.md`. Each needs `satisfied_by` elements (atomic, checkable), `red_flags` (regex and semantic), `default_severity` per `ai/rules/03`, `doc_types` / `mandatory_for`, `mappings`, and `verify`. Anything you are not sure of gets `verify: unverified` and goes in the README's Verification section with the source still to check.
4. **Wire skills.** Reference existing skills in `skills:`. If a control needs a new deterministic extractor, add it under `apps/worker/skills/` with a SKILL.md in `ai/skills/`.
5. **Regex fixtures.** Add `eval/fixtures/red_flags/<id>.yaml` with ≥ 1 positive and ≥ 1 negative example per regex red flag.
6. **Register.** Add the `code` (e.g. `PCIDSS`) to the `framework` enum in `ai/agents/schemas/finding.schema.yaml`, run `make schemas`, and set `pack.maturity: preview`. The picker then shows `Preview · Limited control coverage` (AC-UPL-09) until the pack is evaluated in depth.
7. **Crosswalk.** Add reverse mappings in the existing packs where relevant (keep mappings symmetric). `make packs-validate` warns on asymmetry.
8. **Eval.** Add ≥ 3 labelled documents (synthetic or public) to the next gold version (`eval/gold/vN/`) and run `eval run --gold vN --frameworks <CODE>`. Until the pack has a baseline, the metrics page shows "not yet measured".
9. **Validate**: `make packs-validate` (schema, unique IDs, regexes compile, fixtures pass, refs in whitelist, no `unverified` controls when `STRICT=1`).

## Done when
- Pack loads in `make up`, appears in the UI, and produces findings on the eval docs.
- The eval regression gate passes (citation existence 100%, 0 schema violations), and metrics are reported with sample sizes and CIs.
- README lists coverage, exclusions, and a Verification section citing the primary sources (with any `unverified` items). A human SME has signed off on citations (name in the PR).
