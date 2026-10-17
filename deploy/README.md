# Deploy assets

| Path | Purpose |
|------|---------|
| [`caddy/Caddyfile`](caddy/Caddyfile) | TLS reverse proxy for `docker-compose.prod.yml` (`tls` profile) |
| [`../docker-compose.prod.yml`](../docker-compose.prod.yml) | EC2 production stack (Postgres, API, worker, web, optional Caddy) |
| [`../scripts/deploy-ec2.sh`](../scripts/deploy-ec2.sh) | Pull, build, migrate, health-check on the instance |

**Runbook:** [docs/deploy/aws/ec2-single-instance.md](../docs/deploy/aws/ec2-single-instance.md) — single public URL `https://<API_DOMAIN>/`, sslip.io hostnames, `dev_login_enabled`, and rebuilding `web` when `API_DOMAIN` changes.
