# Step 00 — Prerequisites

Complete this before opening the AWS console for deploy work.

## Accounts and tools

| Requirement | What to do |
|-------------|------------|
| **AWS account** | Sign in at [https://console.aws.amazon.com](https://console.aws.amazon.com). Use an account you control (not a shared prod account without approval). |
| **IAM user or SSO** | You need permission to create VPC, RDS, ECS, IAM roles, Cognito, S3, SQS, Bedrock, ACM, Route 53 (if using custom domain). **AdministratorAccess** is simplest for a solo demo; narrow later. |
| **GitHub** | Repo pushed: `BharathLakkoju/complibot` on branch `master`. |
| **Domain (optional)** | e.g. `api.yourdomain.com` for API and `app.yourdomain.com` on Vercel. You can use ALB DNS + Vercel default URL first. |
| **Local tools** | [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html), [Docker Desktop](https://www.docker.com/products/docker-desktop/), [Terraform ≥ 1.6](https://developer.hashicorp.com/terraform/install) (when you use IaC), `uv` + `pnpm` for local builds. |

## Configure AWS CLI (one machine)

1. Open **PowerShell** or **Terminal**.
2. Run:

```bash
aws configure
```

3. Enter:
   - **AWS Access Key ID** — only if not using SSO; prefer SSO/`aws sso login` for humans.
   - **AWS Secret Access Key**
   - **Default region name:** `us-east-1`
   - **Default output format:** `json`

4. Verify:

```bash
aws sts get-caller-identity
```

You should see `Account`, `Arn`, and `UserId`.

## Set console region

Almost every step assumes **N. Virginia (`us-east-1`)**:

1. Sign in to AWS Console.
2. Top-right, click the **region** dropdown.
3. Select **US East (N. Virginia) us-east-1**.

Bedrock model availability and PRD cost estimates assume this region.

## Values to copy into a scratch pad

Fill these as you complete later steps:

| Key | Your value |
|-----|------------|
| AWS Account ID | |
| Region | `us-east-1` |
| VPC ID | |
| Public subnet IDs (2) | |
| Private subnet IDs (2) | |
| RDS endpoint | |
| S3 bucket name | |
| SQS queue URL | |
| SQS DLQ URL | |
| Cognito User Pool ID | |
| Cognito App Client ID | |
| Cognito Hosted UI domain | |
| ECR repository URI | |
| ECS cluster name | `complibot-demo` |
| ALB DNS name | |
| API URL (HTTPS) | |
| Vercel production URL | |

## Application defaults for `demo`

When you configure ECS environment variables (step 13), production must differ from local `.env.example`:

| Setting | Local (dev) | AWS `demo` |
|---------|-------------|------------|
| `APP_ENV` | `local` | `demo` |
| `DATABASE_URL` | SQLite file | RDS Postgres URL |
| `INLINE_WORKER` | `true` | **`false`** |
| `LLM_PROVIDER` | `mock` | **`bedrock`** |
| Dev login | enabled | **disabled** (Cognito only) |

## Next step

→ [01-aws-account-budgets.md](01-aws-account-budgets.md)
