# Rule 04: Confidence bands

Implements D-01 and D-11, with thresholds per PRD Q-07 (recommended default). Values are in [runtime-config.yaml](runtime-config.yaml). The method is in [skills/confidence-calibration](../skills/confidence-calibration/SKILL.md).

Confidence is shown as a **band with a one-line reason, never a percentage**. Bands describe how sure the AI is. They do **not** route findings into separate queues, and they never accept anything.

| Band | Score (calibrated, or uncalibrated estimate) | Shown as | Behaviour |
|------|------|----|----|
| High | ≥ 0.85 | 3-segment meter `High` + reason | Normal card; needs a human decision like every finding |
| Medium | 0.70 – 0.85 *(split provisional, Q-07)* | `Medium` + reason | Normal card |
| Low | 0.55 – 0.70 *(provisional)* | `Low` + **dashed border, "Needs careful review"**, rationale expanded | **Stays inside its severity group** (a low-confidence critical sorts above every high); matched by the "Low confidence" filter; Accept enabled only after its clause has been opened (AC-AI-07) |
| (abstain) | < 0.55 | not shown as a finding | Logged for eval; the control is listed in coverage as "needs manual check" |

- Absence (`gap`) findings are capped at 0.80, so they are never High. Their reason reads "Not found in document".
- **Uncalibrated.** Until a calibrator exists for the current (packVersion, modelId), `calibrated=false` and the tooltip says "Uncalibrated estimate". Afterwards it reads "Based on [n] labelled examples, findings in this band were correct about [x]% of the time".

**System flags are separate from bands.** `systemFlags` (`critical_severity`, `absence_finding`, `verifier_disagreement`, `injection_suspected`, …) appear as their own reasons on the card, e.g. "Always reviewed: critical". They neither change the band nor set the human `escalated` status. This keeps the Low marker meaningful (PRD C-09). `verifier_disagreement` lowers the score through calibration, so it usually lands in Low.

**Nothing is final without a human.** No code path sets `accepted` without a human `decision.submit` (AC-AI-08). Every published finding starts as `status=open`, and the final report contains only human-decided findings.

**Changing thresholds** follows the eval gate: thresholds are set from calibration on the gold set (ECE / reliability curve). A change PR must include the eval diff and must not regress the gated metrics (PRD §16). Absolute calibration targets (e.g. ECE ≤ 0.05) are goals, not gates, until a baseline exists.
