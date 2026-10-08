# Step 14 — Database migrations (Alembic)

**Goal:** Schema on RDS matches `packages/complibot` models; enable pgvector and RLS via migrations.

## 14.1 Local Alembic setup (one-time)

Config already points to `database/alembic` in `apps/api/alembic.ini`.

From repo root:

```bash
$env:PYTHONPATH="packages/complibot/src;."
$env:DATABASE_URL="postgresql+asyncpg://complibot:PASSWORD@RDS_ENDPOINT:5432/complibot"
uv run alembic -c apps/api/alembic.ini revision --autogenerate -m "initial"
uv run alembic -c apps/api/alembic.ini upgrade head
```

Commit migration files under `database/alembic/versions/`.

## 14.2 First migration must include pgvector

In the first revision `upgrade()`:

```python
op.execute("CREATE EXTENSION IF NOT EXISTS vector")
```

## 14.3 Run migration on AWS (one-off ECS task)

### Console

1. ECS → **Clusters** → `complibot-demo` → **Tasks** → **Run new task**.
2. **Launch type:** Fargate.
3. **Task definition:** create `complibot-migrate` family (same image as API) with command override:

```
uv,run,alembic,-c,apps/api/alembic.ini,upgrade,head
```

4. **Networking:** public subnet, `complibot-api-sg`, public IP on.
5. **Secrets:** same `DATABASE_URL`.
6. **Run task** → wait **Stopped** → exit code 0 in logs.

### CLI

```bash
aws ecs run-task \
  --cluster complibot-demo \
  --task-definition complibot-migrate \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

## 14.4 Deploy order (every release)

1. Run migration task **upgrade head**.
2. Roll ECS **api** service.
3. Roll ECS **worker** service.

Never run incompatible API against old schema (expand/contract pattern for zero-downtime later).

## 14.5 Verify tables

Connect with Query Editor or `psql`:

```sql
\dt
SELECT * FROM alembic_version;
```

Expect tables: `tenants`, `users`, `projects`, `reviews`, `findings`, `review_events`, etc.

## Next step

→ [15-vercel-frontend.md](15-vercel-frontend.md)
