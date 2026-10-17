#!/usr/bin/env bash
# Nightly Postgres backup from docker-compose.prod.yml to S3 (uses instance IAM role).
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/complibot}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"

cd "$REPO_DIR"
set -a
# shellcheck disable=SC1091
source .env
set +a

if [[ -z "${S3_BUCKET:-}" ]]; then
  echo "S3_BUCKET is not set in .env" >&2
  exit 1
fi

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TMP="/tmp/complibot-pg-${STAMP}.sql.gz"
PREFIX="${BACKUP_S3_PREFIX:-backups/db}"

docker compose -f "$COMPOSE_FILE" exec -T postgres \
  pg_dump -U complibot complibot | gzip -9 >"$TMP"

aws s3 cp "$TMP" "s3://${S3_BUCKET}/${PREFIX}/complibot-${STAMP}.sql.gz" --region "${AWS_REGION:-ap-south-1}"
rm -f "$TMP"
echo "Uploaded s3://${S3_BUCKET}/${PREFIX}/complibot-${STAMP}.sql.gz"
