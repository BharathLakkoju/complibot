# Build skill: run the eval harness

**Use when** you change a prompt, model, pack, skill, threshold, or verifier logic, or before a release tag or demo. Spec: PRD §16, AC-EVAL-01…08.

## Dataset
- **Gold v0**: `eval/gold/v0/`. About 12–15 docs (DPAs, MSAs, privacy and security policies), ~150–250 labelled items (target) across GDPR + SOC 2, and ~3 injection fixtures, each with a clean twin.
- **Label fields**: `docId, charStart, charEnd, controlRef, verdict (violation|gap|partial|compliant), severity, notes, labeler, labelVersion`. Gaps have no span and are keyed by (doc, control).
- **Sources**: synthetic docs with seeded defects, public documents with **verified licences** (e.g. CUAD v1, CC BY 4.0, attribution in `eval/gold/vN/SOURCES.md`), and hand-written edge cases. Synthetic items are tagged, and results are reported separately for synthetic and real. The set is public (PRD Q-05, recommended default). Never customer data.
- Released versions are immutable. Changes create v(n+1).

## Run
```bash
eval run --gold v0 --frameworks GDPR,SOC2 --prompt-version X       # full suite (manual / nightly / before release tag)
eval run --gold v0 --subset smoke --frameworks GDPR,SOC2           # CI smoke subset (~4 docs, <= $2 target)
eval run ... --consistency 3                                        # 3 runs at temperature 0 (same as runtime)
eval calibrate --gold v0                                            # fit calibrator; propose band thresholds (Q-07)
```
- Output: `eval/results/<git-sha>.json` plus a Markdown report diffed against the stored baseline on `main`.
- Responses are cached by (model, prompt hash, input hash), so reruns on unchanged prompts are free (AC-EVAL-07).
- The nightly full suite may use Bedrock batch pricing.

## Metrics
- **Matching**: same `controlRef` and char IoU ≥ 0.5; gaps match on (doc, control).
- Precision / recall / F1 (overall, per control, per severity, per framework, synthetic vs real).
- Severity accuracy (exact, ±1, confusion matrix).
- Citation existence (must be 100%).
- Citation support (LLM judge with a fixed rubric; report its agreement with ~50 human pairs).
- Hallucination rate.
- Consistency (Jaccard, severity agreement, confidence std-dev).
- Calibration (ECE, reliability curve).
- Injection robustness.
- Cost (tokens, `costUsd` from the pinned price table) and latency.
- Report bootstrap 95% CIs. Per-control metrics with < 5 gold items show "insufficient data".

## CI gate (regressions only until a baseline exists)
Runs on PRs that change `apps/worker/prompts/`, `apps/worker/pipeline/`, or `frameworks/`. The PR fails if any of these hold:
- citation existence < 100%
- schema violations > 0
- F1 or citation support drops > 3 pts vs the baseline
- hallucination rate rises > 2 pts
- any injection fixture regresses

There are **no absolute quality gates** (e.g. a recall or ECE target) until gold v0 has a published baseline. Absolute numbers are tracked as targets. Before the first baseline exists, only the citation-existence, schema, and injection checks can fail the build.

## Baselines and publication
- The baseline changes only through an explicit PR that commits the new results file.
- The README metrics page shows real numbers with sample sizes once measured, and "not yet measured" until then. ISO 27001, HIPAA, and Internal stay "not yet measured" until gold v1.
- `citation existence < 100%` is always a bug in the verifier or normalization, never something to tolerate.
