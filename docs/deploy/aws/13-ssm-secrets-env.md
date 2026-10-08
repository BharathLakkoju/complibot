# Step 13 — Secrets Manager, SSM, and ECS environment

**Goal:** Centralize secrets; wire ECS task definitions.

## 13.1 Database URL secret

1. **Secrets Manager** → **Store a new secret**.
2. **Other type of secret**.
3. Key/value: `DATABASE_URL` = `postgresql+asyncpg://complibot:PASSWORD@RDS_ENDPOINT:5432/complibot`
4. **Secret name:** `complibot/demo/database_url`.
5. **Disable automatic rotation** for demo (enable later).
6. **Store**.

Note the **ARN**.

## 13.2 Bedrock model IDs (SSM Parameter Store)

1. Search **Systems Manager** → **Parameter Store** → **Create parameter**.

Create three **String** parameters:

| Name | Value |
|------|--------|
| `/cc/demo/bedrock/fast` | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| `/cc/demo/bedrock/reasoning` | `us.anthropic.claude-sonnet-5` |
| `/cc/demo/bedrock/embed` | `amazon.titan-embed-text-v2:0` |

**Type:** Standard. **Data type:** text.

Grant **worker task role** `ssm:GetParameters` on `/cc/demo/bedrock/*`.

## 13.3 API container environment (console)

ECS → **Task definitions** → `complibot-api` → **Create new revision**.

**Environment variables** (plain text):

| Key | Value |
|-----|--------|
| `APP_ENV` | `demo` |
| `AWS_REGION` | `us-east-1` |
| `S3_BUCKET` | your bucket name |
| `SQS_QUEUE_URL` | main queue URL |
| `INLINE_WORKER` | `false` |
| `CORS_ORIGINS` | `https://YOUR_VERCEL_APP.vercel.app` |
| `JWT_ISSUER` | `https://cognito-idp.us-east-1.amazonaws.com/USER_POOL_ID` |
| `JWT_AUDIENCE` | Cognito app client ID |
| `frameworks_path` | `ai/frameworks` |
| `LLM_PROVIDER` | `bedrock` (API may ignore; worker uses) |
| `token_streaming_enabled` | `true` |

**Do not set:** `AWS_ENDPOINT_URL`, `DEV_AUTH_SECRET` for production demo.

**Secrets** (from Secrets Manager):

| Key | Secret ARN | JSON key |
|-----|------------|----------|
| `DATABASE_URL` | `complibot/demo/database_url` ARN | `DATABASE_URL` |

If secret is plain string, map entire secret to env var per ECS UI.

## 13.4 Worker container environment

Same as API except:

- No `CORS_ORIGINS` required.
- `LLM_PROVIDER` = `bedrock` **required**.
- Worker reads Bedrock IDs from SSM (when app code supports it) or set env vars `BEDROCK_MODEL_FAST`, etc.

## 13.5 Update running services

1. ECS → `complibot-api` → **Update service** → **Force new deployment** → check latest task definition revision.
2. Repeat for `complibot-worker`.

## 13.6 Cognito JWKS (API code)

API must validate JWT using Cognito JWKS URL:

`https://cognito-idp.us-east-1.amazonaws.com/USER_POOL_ID/.well-known/jwks.json`

Implement in `packages/complibot/src/complibot/auth/jwt.py` before public launch.

## Verification

- New tasks start with env in **Configuration** tab.
- API logs show DB connection success (no password in logs).
- Worker logs show SQS polling URL.

## Next step

→ [14-database-migrations.md](14-database-migrations.md)
