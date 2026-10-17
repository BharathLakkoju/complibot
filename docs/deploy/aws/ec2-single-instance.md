# Single EC2 demo deploy (< $10/month)

This path runs **API + worker + Postgres (pgvector)** on one **ARM** EC2 instance with real **S3** and **SQS**. The Next.js UI stays on **Vercel**. **Caddy** terminates **HTTPS** on :443 (Let's Encrypt) so the browser can call the API and WebSocket from your HTTPS Vercel app. No ALB, RDS, ECS, Cognito, or Bedrock in this budget profile.

## Monthly cost estimate (ap-south-1, always-on)

| Line item | Assumption | ~USD/month |
|-----------|------------|------------|
| EC2 `t4g.micro` | 730 h × ~$0.0084/h | **6.10** |
| EBS gp3 20 GB | ~$0.08/GB-month | **1.60** |
| Elastic IP | Attached to running instance | **0.00** |
| S3 | < 5 GB demo documents + backups | **0.50** |
| SQS | < 1M requests | **0.00** |
| Data transfer | Light demo traffic | **0.50** |
| **Total** | | **~8.70** |

Use **`t4g.micro`** (not `t4g.small`) to stay under **$10** with headroom. `t4g.small` is ~2× compute cost and typically pushes the stack over $10 before traffic.

Set an AWS Budget at **$10** with alerts at 80% and 100%.

## Prerequisites

1. AWS CLI configured for the owner account (apply is **not** run in CI for this demo).
2. Terraform ≥ 1.6.
3. A DNS name for the API (e.g. `api.demo.example.com`) with an **A record** to the Elastic IP after `terraform apply`.
4. Docker on your laptop (to verify `docker build` before push).
5. Vercel `NEXT_PUBLIC_API_URL` → `https://<api_domain>` (from Terraform output `api_base_url`).

## 1. Provision AWS (Terraform)

```bash
cd infra/terraform/envs/demo
cp terraform.tfvars.example terraform.tfvars
# Edit ssh_cidr, api_domain, acme_email, cors_allowed_origins, optional ssh_key_name.

terraform init
terraform plan
terraform apply
```

Note outputs: `public_ip`, `api_base_url`, `s3_bucket`, `backup_s3_bucket`, `sqs_queue_url`.

Point **`api_domain`** DNS at `public_ip` before starting Caddy on the host.

**Do not commit `terraform.tfvars`** if it contains sensitive CIDRs.

## 2. Configure the instance

SSH (if key pair set):

```bash
ssh -i ~/.ssh/your-key.pem ec2-user@$(terraform output -raw public_ip)
```

On the instance:

```bash
sudo chown -R ec2-user:ec2-user /opt/complibot
cd /opt/complibot
cp .env.bootstrap .env   # from user-data; edit secrets
```

Merge production values into `.env` (see root `.env.example` **Production (EC2)** section):

- `POSTGRES_PASSWORD` — strong password (matches compose interpolation).
- `API_DOMAIN` / `ACME_EMAIL` — same as Terraform `api_domain` / `acme_email`.
- `S3_BUCKET`, `BACKUP_S3_BUCKET`, `SQS_QUEUE_URL`, `AWS_REGION` — from Terraform outputs.
- `AWS_ENDPOINT_URL` — empty (real AWS).
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — **leave empty** on EC2 (instance role).
- `INLINE_WORKER=false`
- `APP_ENV=demo`
- `DEV_LOGIN_ENABLED=false` unless you explicitly want open dev-login (not recommended on the public internet).
- `DEV_AUTH_SECRET` — at least 32 random characters if dev-login is enabled.
- `JWT_ISSUER` / `JWT_AUDIENCE` — demo values documented in `.env.example`.
- `CORS_ORIGINS` — your Vercel URL (must match Terraform `cors_allowed_origins` for presigned PUT).

## 3. Deploy application

On the EC2 host (`deploy-ec2.sh` enables the `tls` compose profile for Caddy):

```bash
./scripts/deploy-ec2.sh
```

Updates later:

```bash
cd /opt/complibot && ./scripts/deploy-ec2.sh
```

## 4. Database backups (cron)

```bash
sudo crontab -u ec2-user -e
```

Add:

```cron
0 3 * * * /opt/complibot/scripts/backup-db-to-s3.sh >> /var/log/complibot-backup.log 2>&1
```

Backups land in `s3://<backup_s3_bucket>/db/` (separate from application documents).

## 5. Smoke tests

From your laptop (after DNS propagates and Caddy has issued a certificate):

```bash
curl -fsS "$(terraform output -raw api_base_url)/health"
```

Use [16-smoke-tests-and-rollback.md](16-smoke-tests-and-rollback.md) where applicable. Enable `DEV_LOGIN_ENABLED=true` only for controlled demo auth (prefer Cognito for anything beyond a lab).

## 6. Tear down

```bash
cd infra/terraform/envs/demo
terraform destroy
```

Empty the S3 buckets first if `terraform destroy` fails on bucket versioning.

## Blockers for production-grade deploy

- **Bedrock / real LLM** — not in this stack; worker uses `LLM_PROVIDER=mock` until a separate Bedrock-enabled worker profile is added.
- **Cognito** — API uses dev JWT when `DEV_LOGIN_ENABLED=true`; default demo bootstrap keeps it **off**.
- **SSH** — restrict `ssh_cidr` in tfvars before apply.
- **Remote Terraform state** — optional S3 backend is commented in `versions.tf`; enable for team use.

## Local verification (no AWS, no TLS)

`docker-compose.prod.yml` uses **host networking** so API/worker talk to Postgres on `127.0.0.1:5432`. Skip the `tls` profile locally (no Caddy); API is on `127.0.0.1:8000` only.

```bash
cp .env.example .env
export POSTGRES_PASSWORD='choose-a-strong-local-password'
grep -q '^POSTGRES_PASSWORD=' .env && sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/" .env \
  || echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> .env
docker compose -f docker-compose.prod.yml config
docker compose -f docker-compose.prod.yml up -d --build
curl -fsS http://127.0.0.1:8000/health
```

**Bridge networking note:** On some nested/containerized dev VMs, Docker bridge traffic between containers can time out while host-published ports work. Host networking matches the single-EC2 production shape and avoids that class of issue.
