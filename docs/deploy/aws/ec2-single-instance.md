# Single EC2 demo deploy (< $10/month)

This path runs **API + worker + Next.js + Postgres (pgvector)** on one **ARM** EC2 instance with real **S3** and **SQS**. **Caddy** terminates **HTTPS** on :443 and routes API paths to the API container and everything else to Next.js — **one public origin** (no Vercel, no cross-origin CORS for the UI). No ALB, RDS, ECS, Cognito, or Bedrock in this budget profile.

## Public URL

After deploy, open **`https://<API_DOMAIN>/`** (same value as Terraform `api_domain` and `API_DOMAIN` in `.env`). REST and WebSocket use that origin (`NEXT_PUBLIC_API_URL` is set at **Docker image build** time to `https://<API_DOMAIN>`).

**Changing `API_DOMAIN`** requires rebuilding the `web` service (`docker compose ... build web` or re-run `./scripts/deploy-ec2.sh`) so the browser bundle picks up the new API base URL.

### Hostname without a custom domain (sslip.io)

If you do not have a DNS name yet, use **[sslip.io](https://sslip.io/)**: set `api_domain` / `API_DOMAIN` to `<dashed-eip>.sslip.io`, where Elastic IP `a.b.c.d` becomes `a-b-c-d.sslip.io` (e.g. `203.0.113.50` → `203-0-113-50.sslip.io`). No DNS record is needed; sslip.io resolves the name to that IP. Let's Encrypt still needs ports 80/443 reachable (`api_cidr` default `0.0.0.0/0`). The EIP is only known after the first `terraform apply`, so set `api_domain` then and apply again. Cloud-init runs user-data once per instance, so the second apply does not rewrite `.env`: edit `API_DOMAIN`, `CORS_ORIGINS`, and `JWT_ISSUER` in `/opt/complibot/.env` by hand, then run `./scripts/deploy-ec2.sh`.

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
3. A DNS name for the site (custom domain or `x-x-x-x.sslip.io`) with traffic to the Elastic IP after `terraform apply`.
4. Docker on your laptop (to verify `docker build` before push).

## 1. Provision AWS (Terraform)

```bash
cd infra/terraform/envs/demo
cp terraform.tfvars.example terraform.tfvars
# Edit ssh_cidr, api_domain, acme_email, cors_allowed_origins, dev_login_enabled, optional ssh_key_name.
```

`https://<api_domain>` is always included in API CORS (`CORS_ORIGINS`) and S3 presigned PUT CORS. Use `cors_allowed_origins` only for extra origins (e.g. a Vercel preview).

For a **public demo** where anyone can sign in with any email (passwordless dev login, synthetic data only, mock LLM), set:

```hcl
dev_login_enabled = true
```

Default is `false` (nobody can sign in until you enable dev login or add Cognito elsewhere).

```bash
terraform init
terraform plan
terraform apply
```

Note outputs: `public_ip`, `api_base_url`, `s3_bucket`, `backup_s3_bucket`, `sqs_queue_url`.

Point **`api_domain`** at `public_ip` (A record or sslip.io). Caddy starts on first boot and retries
certificate issuance until the name resolves to the instance. The Caddyfile allows both Let's Encrypt
and ZeroSSL as ACME issuers (Let's Encrypt first). After HTTPS succeeds, deploy saves
`s3://<backup_s3_bucket>/caddy/caddy_data.tar.gz` and restores it before Caddy starts on the next
instance replacement, so certificates survive `terraform apply -replace=aws_instance.app`.

**Do not commit `terraform.tfvars`** if it contains sensitive CIDRs.

## 2. Configure the instance

SSH (if key pair set):

```bash
ssh -i ~/.ssh/your-key.pem ec2-user@$(terraform output -raw public_ip)
```

User-data installs Docker, the Compose v2 plugin (pinned GitHub release; Amazon Linux 2023 has no
`docker-compose-plugin` package), `cronie`, and a 2 GB swap file (`t4g.micro` has 1 GB RAM). It writes
`.env.bootstrap` with every Terraform-derived value plus a random `POSTGRES_PASSWORD` and
`DEV_AUTH_SECRET`, copies it to `.env` (mode 600) if `.env` does not exist yet, and runs
`./scripts/deploy-ec2.sh` as `ec2-user`. No manual step is needed on first boot.

If the deploy fails (build, `up`, migrations, API health), cloud-init reports an error. If only the final
HTTPS check times out (DNS or Let's Encrypt still pending), cloud-init succeeds: the stack is up and Caddy
keeps retrying certificate issuance on its own.

```bash
cloud-init status --long
sudo tail -n 50 /var/log/cloud-init-output.log
tail -n 100 /var/log/complibot-deploy.log
```

On reboot, Docker starts at boot and the containers come back (`restart: unless-stopped`); `.env` is never
rewritten.

Review `.env` (see root `.env.example` **Production (EC2)** section):

- `POSTGRES_PASSWORD` — generated; if you change it use URL-safe characters (it is embedded in `DATABASE_URL`).
- `API_DOMAIN` / `ACME_EMAIL` — same as Terraform `api_domain` / `acme_email`.
- `S3_BUCKET`, `BACKUP_S3_BUCKET`, `SQS_QUEUE_URL`, `AWS_REGION` — from Terraform outputs.
- `AWS_ENDPOINT_URL` — empty (real AWS).
- `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` — **leave empty** on EC2 (instance role).
- `INLINE_WORKER=false`
- `APP_ENV=demo`
- `DEV_LOGIN_ENABLED` — from Terraform `dev_login_enabled` in `.env.bootstrap`. When `false`, users sign in with **email + password** via `/v1/auth/register` and `/v1/auth/login` (recommended once real accounts are in use). When `true`, passwordless dev login is also available for quick demos — use only synthetic data and set `DEV_LOGIN_ENABLED=false` (or stop the instance) between public demos. Auth attempts are rate-limited to 20/min per client IP.
- `DEV_AUTH_SECRET` — generated; must be ≥ 32 characters (the API refuses to start otherwise). It signs
  every JWT, so rotating it logs everyone out.
- `JWT_ISSUER` / `JWT_AUDIENCE` — generated from `api_domain`.
- `CORS_ORIGINS` — `https://<API_DOMAIN>` plus any Terraform `cors_allowed_origins`.

## 3. Deploy application

User-data runs the first deploy. `deploy-ec2.sh` enables the `tls` compose profile for Caddy and builds
**api**, **worker**, and **web** (web embeds `NEXT_PUBLIC_API_URL=https://<API_DOMAIN>`). It exits `75`
when the stack is healthy but `https://<API_DOMAIN>` is not reachable yet. Updates later:

```bash
cd /opt/complibot && ./scripts/deploy-ec2.sh
```

If you change only `API_DOMAIN`, rebuild web explicitly:

```bash
docker compose --profile tls -f docker-compose.prod.yml build web
docker compose --profile tls -f docker-compose.prod.yml up -d
```

## 4. Database backups (cron)

`cronie` is installed and `crond` enabled by user-data. The instance role can put and get objects under
`db/` and `caddy/` in the backup bucket but cannot delete them; old dumps expire through the bucket lifecycle (90 days, noncurrent
versions after 30).

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
curl -fsS -o /dev/null -w '%{http_code}\n' "$(terraform output -raw api_base_url)/"
```

Expect `ok` JSON from `/health` and `200` from `/`.

Use [16-smoke-tests-and-rollback.md](16-smoke-tests-and-rollback.md) where applicable.

## 6. Tear down

```bash
cd infra/terraform/envs/demo
terraform destroy
```

Empty the S3 buckets first if `terraform destroy` fails on bucket versioning.

## Caddy routing (compose `tls` profile)

On `{$API_DOMAIN}`:

| Path | Backend |
|------|---------|
| `/v1`, `/v1/*` (REST + WebSocket `/v1/reviews/{id}/ws`), `/health`, `/docs`, `/docs/*`, `/redoc`, `/openapi.json` | `127.0.0.1:8000` (API), `request_body` max 1MB |
| Everything else (`/`, app routes, `/_next/*`) | `127.0.0.1:3000` (Next.js) |

Uploads use S3 presigned PUT; large bodies are not proxied through Caddy. Only 22/80/443 are open in the
security group; the API (`:8000`), Next.js (`:3000`), Postgres, and the Caddy admin API bind `127.0.0.1` only.

## Blockers for production-grade deploy

- **Bedrock / real LLM** — not in this stack; worker uses `LLM_PROVIDER=mock` until a separate Bedrock-enabled worker profile is added.
- **Cognito** — API uses dev JWT when `DEV_LOGIN_ENABLED=true`; default Terraform keeps it **off**.
- **SSH** — `ssh_cidr` must be a narrow CIDR (Terraform rejects `0.0.0.0/0`).
- **`api_cidr`** — keep `0.0.0.0/0`; Let's Encrypt validates from undisclosed IPs, so narrowing 80/443
  breaks certificate issuance and renewal.
- **Remote Terraform state** — optional S3 backend is commented in `versions.tf`; enable for team use.

## Local verification (no AWS)

`docker-compose.prod.yml` uses **host networking** so services talk on `127.0.0.1`. `API_DOMAIN` is required
(compose refuses to build `web` without it). Without the `tls` profile (no Caddy):

```bash
cp .env.example .env
export POSTGRES_PASSWORD='choose-a-strong-local-password'
grep -q '^POSTGRES_PASSWORD=' .env && sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/" .env \
  || echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}" >> .env
echo "API_DOMAIN=localhost" >> .env
echo "ACME_EMAIL=local@example.com" >> .env
docker compose -f docker-compose.prod.yml config
docker compose -f docker-compose.prod.yml up -d --build
curl -fsS http://127.0.0.1:8000/health
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3000/
```

With Caddy (`tls` profile), Caddy uses an internal certificate for `localhost`:

```bash
docker compose --profile tls -f docker-compose.prod.yml up -d --build
curl -kfsS https://localhost/health
curl -kfsS -o /dev/null -w '%{http_code}\n' https://localhost/
```

Verify the web bundle contains the configured API origin:

```bash
docker compose -f docker-compose.prod.yml exec web grep -rlF 'https://localhost' apps/web/.next/static
```

**Bridge networking note:** On some nested/containerized dev VMs, Docker bridge traffic between containers can time out while host-published ports work. Host networking matches the single-EC2 production shape and avoids that class of issue.
