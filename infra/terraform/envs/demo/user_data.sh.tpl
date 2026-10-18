#!/bin/bash
set -euo pipefail

# Amazon Linux 2023: there is no docker-compose-plugin package and no cron by default.
dnf update -y
dnf install -y docker git awscli-2 cronie openssl
systemctl enable --now docker crond
usermod -aG docker ec2-user

COMPOSE_VERSION="v2.29.7"
case "$(uname -m)" in
  aarch64) COMPOSE_ARCH=aarch64 ;;
  x86_64) COMPOSE_ARCH=x86_64 ;;
  *) echo "unsupported arch $(uname -m)" >&2; exit 1 ;;
esac
COMPOSE_URL="https://github.com/docker/compose/releases/download/$${COMPOSE_VERSION}/docker-compose-linux-$${COMPOSE_ARCH}"
mkdir -p /usr/local/lib/docker/cli-plugins
curl -fsSL -o /tmp/docker-compose "$COMPOSE_URL"
curl -fsSL -o /tmp/docker-compose.sha256 "$COMPOSE_URL.sha256"
(cd /tmp && sed 's# .*# docker-compose#; s#\*##' docker-compose.sha256 | sha256sum -c -)
install -m 0755 /tmp/docker-compose /usr/local/lib/docker/cli-plugins/docker-compose
docker compose version

# 1 GB RAM on t4g.micro: swap keeps `docker compose build` and Postgres from OOM-killing each other.
if [ ! -f /swapfile ]; then
  dd if=/dev/zero of=/swapfile bs=1M count=2048
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

mkdir -p /opt/complibot
if [ ! -d /opt/complibot/.git ]; then
  git clone "${repository_url}" /opt/complibot
fi

if [ ! -f /opt/complibot/.env.bootstrap ]; then
  umask 077
  cat >/opt/complibot/.env.bootstrap <<EOF
APP_ENV=demo
AWS_REGION=${aws_region}
S3_BUCKET=${s3_bucket}
BACKUP_S3_BUCKET=${backup_bucket}
SQS_QUEUE_URL=${sqs_queue_url}
AWS_ENDPOINT_URL=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
INLINE_WORKER=false
LLM_PROVIDER=${llm_provider}
OPENROUTER_MODEL=${openrouter_model}
DEV_LOGIN_ENABLED=${dev_login_enabled}
API_DOMAIN=${api_domain}
ACME_EMAIL=${acme_email}
CORS_ORIGINS=${cors_origins}
JWT_ISSUER=https://${api_domain}/auth
JWT_AUDIENCE=complibot-demo
POSTGRES_PASSWORD=$(openssl rand -hex 24)
DEV_AUTH_SECRET=$(openssl rand -hex 32)
EOF
fi

chown -R ec2-user:ec2-user /opt/complibot

if [ ! -f /opt/complibot/.env ]; then
  install -m 0600 -o ec2-user -g ec2-user /opt/complibot/.env.bootstrap /opt/complibot/.env
fi

touch /var/log/complibot-deploy.log
chown ec2-user:ec2-user /var/log/complibot-deploy.log

# Best-effort: load OPENROUTER_API_KEY from Secrets Manager when not already set in .env.
_openrouter_secret_arn="${openrouter_secret_arn}"
_complibot_env="/opt/complibot/.env"
if [ -n "$_openrouter_secret_arn" ] && [ -f "$_complibot_env" ]; then
  if ! grep -qE '^OPENROUTER_API_KEY=.+$' "$_complibot_env"; then
    _aws_region=$(grep -E '^AWS_REGION=' "$_complibot_env" | head -1 | cut -d= -f2-)
    set +e
    _openrouter_key=$(aws secretsmanager get-secret-value \
      --secret-id "$_openrouter_secret_arn" \
      --region "$_aws_region" \
      --query SecretString \
      --output text 2>/dev/null)
    _openrouter_fetch_rc=$?
    set -e
    if [ "$_openrouter_fetch_rc" -ne 0 ] || [ -z "$_openrouter_key" ]; then
      echo "openrouter: could not load OPENROUTER_API_KEY from Secrets Manager (continuing)" \
        >>/var/log/complibot-deploy.log
    else
      _env_tmp=$(mktemp)
      grep -v '^OPENROUTER_API_KEY=' "$_complibot_env" >"$_env_tmp" || true
      printf 'OPENROUTER_API_KEY=%s\n' "$_openrouter_key" >>"$_env_tmp"
      install -m 0600 -o ec2-user -g ec2-user "$_env_tmp" "$_complibot_env"
      rm -f "$_env_tmp"
      unset _openrouter_key
    fi
  fi
fi
unset _openrouter_secret_arn _complibot_env _aws_region _env_tmp _openrouter_fetch_rc || true

# runuser calls initgroups(), so the docker group added above applies without a re-login.
deploy_rc=0
runuser -u ec2-user -- bash -lc 'cd /opt/complibot && exec ./scripts/deploy-ec2.sh' \
  >>/var/log/complibot-deploy.log 2>&1 || deploy_rc=$?
case "$deploy_rc" in
  0) ;;
  # 75 = stack up, HTTPS not reachable yet; Caddy keeps retrying ACME, so cloud-init should not fail.
  75) echo "complibot deploy: API healthy, HTTPS not ready yet (see /var/log/complibot-deploy.log)" >&2 ;;
  *)
    echo "complibot deploy failed (exit $deploy_rc); last log lines:" >&2
    tail -n 40 /var/log/complibot-deploy.log >&2 || true
    exit "$deploy_rc"
    ;;
esac
