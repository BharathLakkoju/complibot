# AWS deployment guide — CompliBot (demo environment)

This folder is a **click-by-click** runbook for deploying the Compliance Review Copilot backend on **AWS** and the frontend on **Vercel** (PRD default). It matches [`ai/build/skills/deploy-to-aws/SKILL.md`](../../../ai/build/skills/deploy-to-aws/SKILL.md) and [`ai/build/.cursor/rules/aws-iac.mdc`](../../../ai/build/.cursor/rules/aws-iac.mdc).

| | |
|---|---|
| **Environment name** | `demo` |
| **Recommended region** | `us-east-1` (N. Virginia) |
| **GitHub repo** | `https://github.com/BharathLakkoju/complibot` |
| **Cost target** | ~$75/month (demo; use budgets + scale-to-zero) |

## What you are deploying

| Piece | Platform | Doc step |
|-------|----------|----------|
| Next.js UI (`apps/web`) | **Vercel** | [15-vercel-frontend.md](15-vercel-frontend.md) |
| FastAPI + WebSocket (`apps/api`) | **ECS Fargate** + **ALB** | [11-ecs-fargate-api-worker.md](11-ecs-fargate-api-worker.md), [12-alb-acm-dns.md](12-alb-acm-dns.md) |
| Pipeline worker (`apps/worker`) | **ECS Fargate** | [11-ecs-fargate-api-worker.md](11-ecs-fargate-api-worker.md) |
| Postgres + pgvector | **RDS** | [06-rds-postgres.md](06-rds-postgres.md) |
| Documents / reports | **S3** | [07-s3-bucket.md](07-s3-bucket.md) |
| Review jobs | **SQS** + DLQ | [08-sqs-queues.md](08-sqs-queues.md) |
| Login (JWT) | **Cognito** | [09-cognito.md](09-cognito.md) |
| LLM / embeddings | **Bedrock** | [02-bedrock-model-access.md](02-bedrock-model-access.md) |
| Container images | **ECR** | [10-ecr-docker.md](10-ecr-docker.md) |
| Config / DB secrets | **SSM** + **Secrets Manager** | [13-ssm-secrets-env.md](13-ssm-secrets-env.md) |
| CI deploy | **GitHub Actions** + **OIDC** | [03-github-oidc-iam.md](03-github-oidc-iam.md), [17-cicd-github-actions.md](17-cicd-github-actions.md) |

## Order of operations (do not skip)

1. [00-prerequisites.md](00-prerequisites.md)
2. [01-aws-account-budgets.md](01-aws-account-budgets.md)
3. [02-bedrock-model-access.md](02-bedrock-model-access.md)
4. [03-github-oidc-iam.md](03-github-oidc-iam.md)
5. [04-terraform-state-bootstrap.md](04-terraform-state-bootstrap.md) — optional if you use console-only first; required for Terraform/IaC
6. [05-network-vpc.md](05-network-vpc.md)
7. [06-rds-postgres.md](06-rds-postgres.md)
8. [07-s3-bucket.md](07-s3-bucket.md)
9. [08-sqs-queues.md](08-sqs-queues.md)
10. [09-cognito.md](09-cognito.md)
11. [10-ecr-docker.md](10-ecr-docker.md)
12. [11-ecs-fargate-api-worker.md](11-ecs-fargate-api-worker.md)
13. [12-alb-acm-dns.md](12-alb-acm-dns.md)
14. [13-ssm-secrets-env.md](13-ssm-secrets-env.md)
15. [14-database-migrations.md](14-database-migrations.md)
16. [15-vercel-frontend.md](15-vercel-frontend.md)
17. [16-smoke-tests-and-rollback.md](16-smoke-tests-and-rollback.md)
18. [17-cicd-github-actions.md](17-cicd-github-actions.md)
19. [18-cost-scale-down.md](18-cost-scale-down.md)

## Repo gaps (read before you deploy)

The application code is deployable as containers, but **you must add or complete** these in the repo before production matches the PRD:

- **Dockerfile** at repo root (see [10-ecr-docker.md](10-ecr-docker.md))
- **Terraform modules** under `infra/terraform/modules/` (today only a stub in `infra/terraform/envs/demo/`)
- **Cognito JWT** validation in the API (today: `dev-login` only for local)
- **Bedrock pipeline** (today: mock worker for demo)
- **Alembic migrations** under `database/alembic/`

Use this runbook for infrastructure; track app wiring in GitHub issues or follow-up PRs.

## Naming convention (use everywhere)

| Resource | Example name |
|----------|----------------|
| Project tag | `complibot` |
| Environment tag | `demo` |
| S3 state bucket | `complibot-tfstate-demo-us-east-1` |
| App data bucket | `complibot-demo-documents-<account-id>` |
| ECR repo | `complibot` |
| ECS cluster | `complibot-demo` |
| RDS identifier | `complibot-demo` |
| Cognito pool name | `complibot-demo` |
| SQS queue | `complibot-review-demo` |
| SQS DLQ | `complibot-review-demo-dlq` |

Replace `<account-id>` with your 12-digit AWS account ID (top-right menu in console → account).
