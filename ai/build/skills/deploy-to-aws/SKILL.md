# Build skill: deploy to AWS (API and workers)

**Use when** deploying the backend or setting up the AWS account for the first time. Scope: **one environment (`demo`), one region** (PRD §6, Q-03 default `us-east-1`). The **frontend is not deployed here.** `apps/web` deploys to **Vercel** (PRD Q-02, recommended default) through Vercel's Git integration, with `NEXT_PUBLIC_API_URL` pointing at the ALB or custom domain. If Bharath picks the all-AWS option (Amplify or S3 + CloudFront), add a separate frontend runbook.

## One-time setup (day 1)
1. **Guardrails first.** Create an AWS Budgets alarm at 50/80/100% of $75/month, and request Bedrock model access for the Q-03 models in the region.
2. **Bootstrap state.** `infra/bootstrap` creates the state bucket (versioned, encrypted) and the GitHub OIDC provider plus a `deploy-demo` role trusted only for `repo:<org>/<repo>:ref:refs/heads/main`.
3. **Pin models.** Put the inference-profile IDs in SSM `/cc/demo/bedrock/{fast,reasoning,embed}`. Defaults were verified on 2026-10-05 against the AWS Bedrock model cards and the AWS Price List API (us-east-1); they use **US geo** profiles, which keep inference in US regions:

   | Tier | SSM value | Input / output, USD per 1M tokens |
   |---|---|---|
   | fast | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | 1.10 / 5.50 (global profile: 1.00 / 5.00) |
   | reasoning | `us.anthropic.claude-sonnet-5` | 2.20 / 11.00 (global profile: 2.00 / 10.00) |
   | embed | `amazon.titan-embed-text-v2:0` | 0.02 |

   Haiku 4.5 on `bedrock-runtime` requires a geo or global profile; the bare model ID is not accepted for on-demand use. If the pinned endpoint or prices differ, update `price_table` in `ai/rules/runtime-config.yaml` in the same PR.
4. **Apply the stack.** Run `make tf-apply`. It creates VPC (no NAT), ALB, ECS Fargate `api` + `worker`, RDS Postgres 16 single-AZ + pgvector, S3 (SSE-S3), SQS + DLQ, Cognito, and the CloudWatch dashboard (AC-INF-01).
5. **First user.** Run `scripts/create_user.sh <email>`, which sends a Cognito invite. Project roles (`owner`/`reviewer`/`viewer`) are assigned in the app via membership, not Cognito groups.
6. **Database.** The first migration runs `CREATE EXTENSION IF NOT EXISTS vector;` and enables RLS policies.
7. **Vercel.** Add the Vercel domain to the Cognito app client callback URLs and to the S3 CORS and API CORS allowlists.
8. **Pre-demo re-checks** (before day 1 and before each public demo). Record the date and result in the PR or release notes:
   - **Models.** Each pinned model shows `Model lifecycle: Active` on its AWS Bedrock model card, and model access is granted in the account. On 2026-10-05, Claude Haiku 4.5 showed "EOL no sooner than Oct 16, 2026" and Claude Sonnet 5 showed "EOL no sooner than June 30, 2027". If a model is marked Legacy, re-pin the fast tier to the Q-03 alternative (Amazon Nova 2 Lite) or to the successor Anthropic lists for it, then re-run the eval.
   - **Prices.** Read the `AmazonBedrockFoundationModels` and `AmazonBedrock` offer files from the AWS Price List API for the region. If prices changed, update `price_table`, re-run `ai/agents/cost-model.md`, and confirm the USD guard still fits the targets.
   - **Content facts.** Check that the EU–US DPF is still in force (CJEU case C-703/25 P) and that no HIPAA Security Rule final rule has appeared (RIN 0945-AA22). If either changed, update the GDPR or HIPAA pack and bump its version.
   - **Comprehend Medical** (only if the optional PHI layer is enabled): confirm it is still on AWS's HIPAA Eligible Services Reference and that the account has an AWS BAA.

## Every deploy (GitHub Actions on merge to `main`)
1. Run tests, lint, `pip-audit`, `checkov`, and the cross-tenant suite. The eval smoke gate already ran on the PR, so it is not repeated here.
2. Build the `api` and `worker` images (same codebase, different entrypoints), push to ECR with immutable git-SHA tags, and scan them.
3. `terraform plan` is posted on the PR, and apply runs on merge (single env).
4. Migrations run as a one-off ECS task (`alembic upgrade head`) **before** the service update, using expand/contract so the previous image keeps working.
5. ECS rolling deploy with the circuit breaker and rollback. Workers stop polling on SIGTERM and finish in-flight tasks within `stopTimeout` (120 s).
6. Smoke test: `GET /v1/healthz` and `/v1/readyz` (DB, SQS, S3); WS `client.hello` → `server.welcome` on a synthetic review; one FakeLLM review end to end.

## Cost controls
- Scheduled scale-to-zero for `api` and `worker` outside demo windows (PRD Q-04 default), with optional RDS stop/start on a schedule.
- No NAT gateway; single-AZ RDS on the smallest burstable class.
- The per-review USD guard in `runtime-config.yaml` aborts runaway reviews.

## Rollback
- **App**: redeploy the previous image tag (`make deploy TAG=<prev_sha>`).
- **Migration**: forward fix only.
- **Prompt or pack regression**: revert the pinned version in config. Existing report versions are unaffected.

## After deploy
- Check the CloudWatch dashboard: time to first finding, tokens and cost per review, WS connections, SQS age of oldest message, DLQ depth (alarm > 0), and Bedrock throttles.
- Confirm that no logs contain document text (AC-SEC-03 spot check).
