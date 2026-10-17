#!/usr/bin/env bash
# Nightly Postgres backup from docker-compose.prod.yml to the dedicated backup bucket.
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/complibot}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-$REPO_DIR/.env}"

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

cd "$REPO_DIR"

# No fallback to S3_BUCKET: dumps hold every tenant's data and must not land in the documents bucket.
S3_BUCKET="$(read_env_var BACKUP_S3_BUCKET)"
AWS_REGION="$(read_env_var AWS_REGION ap-south-1)"
PREFIX="$(read_env_var BACKUP_S3_PREFIX db)"

if [[ -z "$S3_BUCKET" ]]; then
  echo "BACKUP_S3_BUCKET is not set in $ENV_FILE" >&2
  exit 1
fi

umask 077
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TMP="/tmp/complibot-pg-${STAMP}.sql.gz"
trap 'rm -f "$TMP"' EXIT

docker compose -f "$COMPOSE_FILE" exec -T postgres \
  pg_dump -U complibot complibot | gzip -9 >"$TMP"

aws s3 cp "$TMP" "s3://${S3_BUCKET}/${PREFIX}/complibot-${STAMP}.sql.gz" --region "$AWS_REGION"
echo "Uploaded s3://${S3_BUCKET}/${PREFIX}/complibot-${STAMP}.sql.gz"
