# Step 18 — Cost controls and scale-to-zero

**Goal:** Stay near **$75/month** demo budget (PRD Q-04).

## 18.1 ECS scheduled scaling

### Option A — Application Auto Scaling (simple)

1. ECS → service `complibot-api` → **Service auto scaling**.
2. Create policy: min **0**, max **1** desired count (demo).
3. Use scheduled actions:
   - **Scale to 0** cron: `0 22 * * *` (10 PM UTC) weekdays
   - **Scale to 1** cron: `0 14 * * *` before demos

Repeat for `complibot-worker`.

### Option B — EventBridge Scheduler

1. Search **EventBridge** → **Schedules** → **Create schedule**.
2. **Schedule pattern:** cron expression.
3. **Target:** AWS SDK call `ecs:UpdateService` with `desiredCount: 0`.
4. IAM role for scheduler to call ECS.

## 18.2 RDS stop/start (optional)

1. RDS → `complibot-demo` → **Actions** → **Stop temporarily** when not demoing for days.
2. **Start** before demos (5–10 min startup).

Automate with Lambda + EventBridge if desired.

## 18.3 NAT reminder

This architecture **does not use NAT Gateway** (~$32+/month saved). Do not add NAT unless you move Fargate to private subnets only.

## 18.4 Bedrock cost guard

`ai/rules/runtime-config.yaml` defines per-review token and USD guards. Ensure worker respects them so runaway reviews do not blow the budget.

## 18.5 Review monthly

1. **Cost Explorer** → filter by tag `project=complibot`.
2. Compare to Budgets alarm thresholds.
3. **Trusted Advisor** / **Compute Optimizer** recommendations.

## 18.6 Tear down sandbox

Delete in order to avoid orphans:

1. ECS services → cluster
2. ALB + target groups
3. RDS (disable deletion protection first)
4. S3 buckets (empty first)
5. SQS queues
6. Cognito pool
7. ECR images
8. CloudWatch log groups
9. VPC (subnets, SGs, endpoints)

## Done

You completed the AWS deploy runbook. Keep [README.md](README.md) as the index and update step docs when Terraform modules land in `infra/terraform/modules/`.
