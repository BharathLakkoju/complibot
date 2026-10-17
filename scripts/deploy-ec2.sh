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

if [[ -d .git ]]; then
  git fetch origin "$BRANCH"
  git checkout "$BRANCH"
  git pull --ff-only origin "$BRANCH"
fi

docker compose --profile "$COMPOSE_PROFILES" -f "$COMPOSE_FILE" build --pull
docker compose --profile "$COMPOSE_PROFILES" -f "$COMPOSE_FILE" up -d

if compgen -G "database/alembic/versions/*.py" > /dev/null; then
  echo "Applying database migrations..."
  docker compose --profile "$COMPOSE_PROFILES" -f "$COMPOSE_FILE" exec -T api \
    uv run alembic -c apps/api/alembic.ini upgrade head
fi

echo "Waiting for API health..."
for _ in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null 2>&1; then
    curl -fsS http://127.0.0.1:8000/health
    echo
    echo "Deploy complete."
    exit 0
  fi
  sleep 2
done

echo "API did not become healthy in time. Check: docker compose -f $COMPOSE_FILE logs api" >&2
exit 1
