# Step 06 — RDS PostgreSQL 16 + pgvector

**Goal:** Managed Postgres for reviews, findings, `review_events`, embeddings.

## 6.1 Create DB subnet group

1. Search **RDS** → left **Subnet groups** → **Create DB subnet group**.
2. **Name:** `complibot-demo-db`.
3. **VPC:** `complibot-demo`.
4. **Availability Zones:** select both AZs used by your **private** subnets.
5. **Subnets:** add **only private subnet IDs** (both).
6. **Create**.

## 6.2 Create database

1. RDS → **Databases** → **Create database**.
2. **Engine:** PostgreSQL.
3. **Version:** **16.x** (latest 16 minor).
4. **Templates:** **Dev/Test** (cheaper) or **Production** if you need stricter defaults.

### Settings

| Field | Value |
|-------|--------|
| DB instance identifier | `complibot-demo` |
| Master username | `complibot` |
| Credentials | **Managed in AWS Secrets Manager** (recommended) |

### Instance configuration

| Field | Value |
|-------|--------|
| Instance class | `db.t4g.micro` or `db.t3.micro` (smallest burstable) |
| Storage | **20** GiB gp3 (adjust as needed) |
| Storage autoscaling | Optional, cap e.g. 50 GiB |

### Connectivity

| Field | Value |
|-------|--------|
| VPC | `complibot-demo` |
| Subnet group | `complibot-demo-db` |
| **Public access** | **No** |
| VPC security group | Choose existing → `complibot-rds-sg` |
| Availability | **Single-AZ** (demo cost) |

### Database authentication

- **Password authentication** (default).

### Additional configuration

- **Initial database name:** `complibot`
- **Backup retention:** 1–7 days (demo: 1 is fine)
- **Encryption:** enable
- **Deletion protection:** off for sandbox; **on** for anything you care about

3. **Create database** (10–15 minutes).

## 6.3 Enable pgvector

When status is **Available**:

### Option 1 — RDS Query Editor (if enabled for your instance)

1. RDS → database → **Query editor** (or use **psql** from a bastion—none in this design; use ECS one-off task or laptop over VPN if you add it).
2. Connect as master user.
3. Run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Option 2 — From ECS one-off task (after step 11)

Run a task with `psql` image, same VPC/security group as API, connect to endpoint.

## 6.4 Build `DATABASE_URL` for the app

1. RDS → **complibot-demo** → copy **Endpoint** (hostname).
2. Secrets Manager → secret created for RDS → retrieve password.
3. Format for SQLAlchemy async:

```
postgresql+asyncpg://complibot:PASSWORD@ENDPOINT:5432/complibot
```

Store in **Secrets Manager** secret `complibot/demo/database_url` (step 13)—never commit to Git.

## 6.5 (Later) Row-level security

PRD expects RLS policies via migrations ([14-database-migrations.md](14-database-migrations.md)).

## Verification

- RDS status **Available**.
- `CREATE EXTENSION vector` succeeds.
- Security group allows 5432 from API/worker SG only.

## Next step

→ [07-s3-bucket.md](07-s3-bucket.md)
