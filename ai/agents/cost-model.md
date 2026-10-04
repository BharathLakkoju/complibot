# Cost model: per-review token budget vs cost targets (PRD C-19)

**Targets** (PRD §4, NFR): ≤ $0.50 per review (20 pages, 1 framework) and ≤ $1.00 (2 frameworks). These are targets, not measurements. The model below is an **estimate** and should be replaced by real token counts from the first eval run (`eval/results/*.json` records tokens and `costUsd`).

## Prices (PRD Q-03 recommended models)
The PRD lists the models but **no prices**. All prices below were verified on 2026-10-05 from the **AWS Price List API** for us-east-1: the `AmazonBedrockFoundationModels` offer (published 2026-09-30) for Anthropic models and the `AmazonBedrock` offer (published 2026-10-03) for Titan. Model IDs and profiles come from the AWS Bedrock model cards.

| Model (tier) | US geo profile (pinned) $/1M in / out | Global profile $/1M in / out | Profile ID (US geo) |
|---|---|---|---|
| Claude Haiku 4.5 (fast) | 1.10 / 5.50 | 1.00 / 5.00 | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| Claude Sonnet 5 (reasoning) | 2.20 / 11.00 | 2.00 / 10.00 (matches Anthropic's list price) | `us.anthropic.claude-sonnet-5` |
| Titan Text Embeddings V2 | 0.02 | n/a | `amazon.titan-embed-text-v2:0` (on-demand) |

The pinned endpoint is **US geo**, which keeps inference within US regions. Global profiles are about 9% cheaper but route requests worldwide. Prices and model lifecycle are re-checked at deploy ([deploy-to-aws](../build/skills/deploy-to-aws/SKILL.md), steps 3 and 8).

## Token estimate: 20 pages (≈ 13.5k tokens, ≈ 120 clauses), one 20-control framework
| Stage | Tier | Input tok | Output tok |
|---|---|---|---|
| Ingestion boundary repair (once per review) | fast | 8,000 | 1,000 |
| Embeddings (once per review) | embed | 13,500 | n/a |
| Scoping | fast | 4,000 | 1,500 |
| Mapper (6 batches × 20 clauses × 20 control cards) | fast | 36,000 | 7,000 |
| Assessor (20 controls × ~2.9k in / 450 out) | reasoning | 58,000 | 9,000 |
| Verifier entailment (~20) | fast | 12,000 | 1,600 |
| Remediation (~8 violation/gap/partial) | see variants | 17,600 | 4,800 |
| Retries / repair overhead | n/a | +15% | +15% |

## Result
| Variant | 1 framework | 2 frameworks | Tokens (1 fw) |
|---|---|---|---|
| As originally written (assessor n=3 on every control, remediation on reasoning tier) | **≈ $1.02** ✗ | **≈ $2.03** ✗ | ≈ 354k |
| Assessor n=1, remediation on reasoning tier | ≈ $0.50 (at the limit) | ≈ $0.98 | ≈ 200k |
| **Adopted, US geo prices (pinned):** assessor n=1 at temperature 0, remediation on fast tier | **≈ $0.46** ✓ | **≈ $0.90** ✓ | ≈ 200k |
| Adopted, global profiles | ≈ $0.42 | ≈ $0.82 | ≈ 200k |
| Adopted, mixed (Haiku global, Sonnet geo), the earlier basis | ≈ $0.44 | ≈ $0.87 | ≈ 200k |

**The old budget was not consistent with the targets.** `max_tokens_per_review: 1,500,000` allowed $1.50 even if every token were billed at the cheapest (Haiku input) rate, and $3.30 at Sonnet 5 input rates. That is 3–7× the $0.50 target.

**Changes made** (in [`rules/runtime-config.yaml`](../rules/runtime-config.yaml)):
- The token budget is now `30k + 240k × frameworks` (≈ 1.2× the estimate).
- A **USD guard** was added: `0.48 × frameworks`, computed live from the pinned price table. The review stops LLM work when either limit is hit, and unprocessed controls are reported in coverage (AC-AI-17).
- The assessor now runs n=1 at temperature 0. This also resolves C-17, because it matches the eval consistency setting.
- Remediation moved to the fast tier.

**Margin is thin.** At US geo prices the estimate is ≈ 8% under the $0.50 target and ≈ 4% under the guard. If the first eval run shows higher usage, the levers in order are:
1. Bedrock prompt caching for the assessor system prompt and control cards. Cache reads are priced at 10% of input in the Price List API (Sonnet 5 US geo: $0.22/1M). The minimum cache checkpoint is 1,024 tokens for Sonnet 5 and 4,096 for Haiku 4.5, per the AWS model cards.
2. Skip remediation for `low`/`info` findings.
3. Smaller mapper batches with tighter control cards.

Batch pricing (50% of on-demand in the Price List API, e.g. Haiku 4.5 US geo $0.55 / $2.75) does not fit live streaming, but the **nightly eval** can use it.
