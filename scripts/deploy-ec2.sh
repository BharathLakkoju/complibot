#!/usr/bin/env bash
# Deploy or refresh CompliBot on the single-EC2 demo host.
# Run on the EC2 instance (as ec2-user) from /opt/complibot after copying .env.
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/complibot}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
COMPOSE_PROFILES="${COMPOSE_PROFILES:-tls}"
BRANCH="${BRANCH:-master}"

cd "$REPO_DIR"

if [[ ! -f .env ]]; then
  echo "Missing .env in $REPO_DIR. Copy .env.example, merge .env.bootstrap from user-data, set POSTGRES_PASSWORD and JWT secrets." >&2
  exit 1
fi

if ! grep -qE '^API_DOMAIN=.+' .env || ! grep -qE '^ACME_EMAIL=.+' .env; then
  echo "Set API_DOMAIN and ACME_EMAIL in .env before deploy (DNS A record → this host)." >&2
  exit 1
fi
api_domain="$(grep -E '^API_DOMAIN=' .env | tail -n1 | cut -d= -f2-)"

if [[ -d .git ]]; then
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
fi

# Always rebuild: web inlines NEXT_PUBLIC_API_URL at build time, so an API_DOMAIN change needs a new image.
echo "Building images (web: NEXT_PUBLIC_API_URL=https://$api_domain)..."
docker compose --profile "$COMPOSE_PROFILES" -f "$COMPOSE_FILE" build --pull

if [[ ",$COMPOSE_PROFILES," == *",tls,"* ]]; then
  echo "Restoring Caddy TLS storage from S3 (if any)..."
  bash ./scripts/restore-caddy-data-from-s3.sh || true
fi

docker compose --profile "$COMPOSE_PROFILES" -f "$COMPOSE_FILE" up -d

if compgen -G "database/alembic/versions/*.py" > /dev/null; then
  echo "Applying database migrations..."
  docker compose --profile "$COMPOSE_PROFILES" -f "$COMPOSE_FILE" exec -T api \
    alembic -c apps/api/alembic.ini upgrade head
fi

echo "Waiting for API health..."
healthy=0
for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
    curl -fsS http://127.0.0.1:8000/health
    echo
    healthy=1
    break
  fi
  sleep 2
done

if [[ "$healthy" != 1 ]]; then
  echo "API did not become healthy in time. Check: docker compose -f $COMPOSE_FILE logs api" >&2
  exit 1
fi

if [[ ",$COMPOSE_PROFILES," == *",tls,"* ]]; then
  echo "Checking https://$api_domain/ and /health (ACME can take a minute on first boot)..."
  for _ in $(seq 1 30); do
    if curl -fsS "https://$api_domain/health" >/dev/null 2>&1 \
      && curl -fsS -o /dev/null "https://$api_domain/"; then
      echo "HTTPS OK (web + API)."
      if ! bash ./scripts/backup-caddy-data-to-s3.sh; then
        echo "Warning: Caddy TLS storage backup to S3 failed (deploy still succeeded)." >&2
      fi
      echo "Deploy complete."
      exit 0
    fi
    sleep 4
  done
  echo "HTTPS check failed. Check DNS A record and: docker compose -f $COMPOSE_FILE logs caddy" >&2
  # EX_TEMPFAIL: the stack is up and Caddy keeps retrying ACME. EC2 user-data treats only this
  # code as non-fatal; 2 would collide with exit codes propagated through `set -e` (e.g. alembic).
  exit 75
fi

echo "Deploy complete."
