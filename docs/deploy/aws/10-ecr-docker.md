# Step 10 — Dockerfile and Amazon ECR

**Goal:** Build one image used by **api** and **worker** services (different commands).

## 10.1 Add Dockerfile to repo (if not present)

Create `Dockerfile` at repository root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./
COPY packages/ packages/
COPY apps/api apps/api
COPY apps/worker apps/worker
COPY ai/frameworks ai/frameworks
COPY ai/rules ai/rules

RUN pip install uv && uv sync --frozen --no-dev

ENV PYTHONPATH=/app/packages/complibot/src
ENV APP_ENV=demo

EXPOSE 8080
# Default CMD overridden per ECS service
CMD ["uv", "run", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Commit and push to GitHub.

## 10.2 Create ECR repository

1. Search **Elastic Container Registry** → **Repositories** → **Create repository**.
2. **Visibility:** Private.
3. **Repository name:** `complibot`.
4. **Scan on push:** **Enable**.
5. **Encryption:** AES-256.
6. **Create repository**.

7. Note **URI:** `ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/complibot`

## 10.3 Authenticate Docker to ECR

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

## 10.4 Build and push (local)

From repo root:

```bash
export GIT_SHA=$(git rev-parse --short HEAD)
docker build -t complibot:$GIT_SHA .
docker tag complibot:$GIT_SHA ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/complibot:$GIT_SHA
docker tag complibot:$GIT_SHA ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/complibot:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/complibot:$GIT_SHA
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/complibot:latest
```

## 10.5 Verify in console

1. ECR → **complibot** → **Images**.
2. You should see tags `latest` and git SHA.
3. **Scan** status should complete (no critical vulns ideal).

## 10.6 Image size tips

- Multi-stage build later to strip build deps.
- Do not copy `node_modules`, `.venv`, or `.data` into image (use `.dockerignore`).

Example `.dockerignore`:

```
.venv
node_modules
apps/web
.git
.data
*.db
```

## Next step

→ [11-ecs-fargate-api-worker.md](11-ecs-fargate-api-worker.md)
