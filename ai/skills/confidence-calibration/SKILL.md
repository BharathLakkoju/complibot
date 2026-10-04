# Skill: confidence-calibration

**Use when** an assessment has passed the Citation Verifier and needs `confidence {score, band, reason, calibrated}` before `finding.created`. It also runs offline in the eval harness to fit the calibrator and pick band thresholds (PRD Q-07).

## Input / output
```python
In:  signals: {model_self, retrieval_sim, quote_match, verifier_agree, red_flag_hit: bool,
               kind: violation|gap|partial|compliant, mapper_degraded: bool}
     severity: Severity; framework: str; system_flags: list[str]
Out: Confidence(score: float, band: Literal["high","medium","low"] | None,   # None => abstain (not published)
                reason: str, calibrated: bool, signals: dict)
```

## Method
1. **Feature vector.** The signals above plus a one-hot of `framework` and `kind`. There is no runtime self-consistency signal: the assessor runs once at temperature 0 (C-17), and stability is measured in eval instead.
2. **Calibrator.** Logistic regression, or isotonic regression on its output once there are ≥ 500 labelled examples. It is fit on gold-set predictions, labelled correct when the prediction matches gold (same controlRef, char IoU ≥ 0.5 or the same (doc, control) for gaps, same kind). The artifact `calibrators/{packVersion}/{modelId}.json` is versioned with the pack and model, and changing either requires a refit.
3. **Before calibration** (`calibrated=false`, tooltip "Uncalibrated estimate"): `score = 0.4·verifier_agree + 0.25·quote_match + 0.2·retrieval_sim + 0.15·model_self`. Absent signals are dropped and the weights renormalized.
4. **Caps and adjustments:** absence (`gap`) ≤ 0.80; `mapper_degraded` −0.05; repaired citation (`quote_match < 1`) −0.05.
5. **Band.** Thresholds come from `runtime-config.yaml`: High ≥ 0.85, Medium ≥ `low_below` (provisional 0.70), Low ≥ 0.55, abstain below that. The band reflects confidence only. System flags (e.g. `critical_severity`) are shown as separate reasons and never move a finding out of its severity group (D-01).
6. **Reason** (≤ 160 chars, plain language), built from the strongest signals. Examples: "Quote directly states a 30-day window", "Clause only partly matches the control", "Not found in document; searched 6 sections".
7. **Eval reporting** (targets, not gates, until a baseline exists): ECE (10 bins), reliability curve, and per-band precision with bootstrap CIs. The first run on gold v0 sets `low_below` and confirms or moves `high_min`, via an explicit PR.

## Edge cases
- **`model_self` is weakly informative.** LLM verbalized confidence is poorly calibrated, so it is never used alone and its learned weight is usually small.
- **Class imbalance.** Calibrate per kind group (violation/gap/partial) if ECE differs by more than 0.03 between groups.
- **Small gold set** (~150–250 items in v0): report the sample size per band. A band with fewer than 20 items is labelled "insufficient data", and the uncalibrated tooltip stays on.
- **Abstained** results are never shown as findings. They appear in coverage as "needs manual check".
