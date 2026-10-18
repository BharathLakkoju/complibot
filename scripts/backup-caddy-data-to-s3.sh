#!/usr/bin/env bash
# Upload Caddy TLS storage (caddy_data volume) to the backup bucket after HTTPS is healthy.
# Errors are non-fatal for deploy (caller should log and continue).
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/complibot}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
COMPOSE_PROFILES="${COMPOSE_PROFILES:-tls}"
ENV_FILE="${ENV_FILE:-$REPO_DIR/.env}"
S3_KEY="${CADDY_S3_KEY:-caddy/caddy_data.tar.gz}"

read_env_var() {
  local key="$1"
  local default="${2:-}"
  if [[ ! -f "$ENV_FILE" ]]; then
    echo "$default"
    return
  fi
  local line
  line="$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 || true)"
  if [[ -z "$line" ]]; then
    echo "$default"
    return
  fi
  echo "$line" | cut -d= -f2- | sed -e 's/^["'\'']//' -e 's/["'\'']$//'
}

caddy_data_volume() {
  local project="${COMPOSE_PROJECT_NAME:-$(basename "$REPO_DIR")}"
  echo "${project}_caddy_data"
}

cd "$REPO_DIR"

if [[ ",$COMPOSE_PROFILES," != *",tls,"* ]]; then
  exit 0
fi

S3_BUCKET="$(read_env_var BACKUP_S3_BUCKET)"
AWS_REGION="$(read_env_var AWS_REGION ap-south-1)"

if [[ -z "$S3_BUCKET" ]]; then
  echo "BACKUP_S3_BUCKET is not set; skipping Caddy data backup." >&2
  exit 0
fi

VOLUME="$(caddy_data_volume)"
if ! docker volume inspect "$VOLUME" >/dev/null 2>&1; then
  echo "Volume ${VOLUME} not found; skipping Caddy data backup." >&2
  exit 0
fi

umask 077
TMP="$(mktemp /tmp/complibot-caddy-backup.XXXXXX.tar.gz)"
trap 'rm -f "$TMP"' EXIT

docker run --rm \
  -v "${VOLUME}:/data:ro" \
  -v "${TMP}:/backup/caddy_data.tar.gz" \
  alpine:3.20 \
  sh -c 'tar czf /backup/caddy_data.tar.gz -C /data .'

aws s3 cp "$TMP" "s3://${S3_BUCKET}/${S3_KEY}" --region "$AWS_REGION"
echo "Uploaded s3://${S3_BUCKET}/${S3_KEY}"
