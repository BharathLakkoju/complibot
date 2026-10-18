#!/usr/bin/env bash
# Restore Caddy TLS storage (caddy_data volume) from the backup bucket before Caddy starts.
# Missing or corrupt archives are logged and ignored so deploy can continue with fresh storage.
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
  echo "Skipping Caddy data restore (tls profile not enabled)."
  exit 0
fi

S3_BUCKET="$(read_env_var BACKUP_S3_BUCKET)"
AWS_REGION="$(read_env_var AWS_REGION ap-south-1)"

if [[ -z "$S3_BUCKET" ]]; then
  echo "BACKUP_S3_BUCKET is not set; skipping Caddy data restore." >&2
  exit 0
fi

VOLUME="$(caddy_data_volume)"
docker volume create "$VOLUME" >/dev/null

TMP="$(mktemp /tmp/complibot-caddy-restore.XXXXXX.tar.gz)"
trap 'rm -f "$TMP"' EXIT

if ! aws s3 cp "s3://${S3_BUCKET}/${S3_KEY}" "$TMP" --region "$AWS_REGION" 2>&1; then
  echo "No Caddy data archive at s3://${S3_BUCKET}/${S3_KEY}; starting with empty storage."
  exit 0
fi

if ! docker run --rm \
  -v "${VOLUME}:/data" \
  -v "${TMP}:/backup/caddy_data.tar.gz:ro" \
  alpine:3.20 \
  sh -c 'tar xzf /backup/caddy_data.tar.gz -C /data'; then
  echo "Caddy data restore failed (corrupt archive?); continuing with existing volume contents." >&2
  exit 0
fi

echo "Restored Caddy storage into volume ${VOLUME} from s3://${S3_BUCKET}/${S3_KEY}"
