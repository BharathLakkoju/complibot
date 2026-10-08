# Step 11 — ECS Fargate (API + worker)

**Goal:** Two services on one cluster: **api** (behind ALB) and **worker** (SQS only).

## 11.1 Create ECS cluster

1. Search **Elastic Container Service** → **Clusters** → **Create cluster**.
2. **Cluster name:** `complibot-demo`.
3. **Infrastructure:** **AWS Fargate (serverless)**.
4. **Create**.

## 11.2 Create task execution role (if not exists)

ECS usually offers **ecsTaskExecutionRole** — use it or create:

1. IAM → **Roles** → **Create role** → **Elastic Container Service** → **Elastic Container Service Task**.
2. Attach **AmazonECSTaskExecutionRolePolicy**.
3. Name: `complibot-ecs-execution-role`.

This role pulls images from ECR and reads Secrets Manager for env injection.

## 11.3 Create API task role

1. IAM → **Roles** → **Create role** → **Elastic Container Service Task**.
2. Name: `complibot-api-task-role`.
3. Attach **custom policy** (example — tighten ARNs):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::YOUR_BUCKET/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::YOUR_BUCKET"
    },
    {
      "Effect": "Allow",
      "Action": ["sqs:SendMessage"],
      "Resource": "arn:aws:sqs:us-east-1:ACCOUNT:complibot-review-demo"
    }
  ]
}
```

No Bedrock on API.

## 11.4 Create worker task role

Name: `complibot-worker-task-role`. Add SQS receive/delete + Bedrock:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:ChangeMessageVisibility"
      ],
      "Resource": "arn:aws:sqs:us-east-1:ACCOUNT:complibot-review-demo"
    },
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/*",
        "arn:aws:bedrock:us-east-1:ACCOUNT:inference-profile/*"
      ]
    }
  ]
}
```

Narrow Bedrock ARNs to your pinned models when possible.

## 11.5 Register task definition — API

1. ECS → **Task definitions** → **Create new task definition** → **Create new task definition with JSON** (or form).

**Form path:**

| Field | Value |
|-------|--------|
| Task definition family | `complibot-api` |
| Launch type | Fargate |
| OS/Arch | Linux / X86_64 |
| CPU | 0.5 vCPU (512) |
| Memory | 1 GB (1024) |
| Task role | `complibot-api-task-role` |
| Task execution role | `complibot-ecs-execution-role` |

**Container — `api`:**

| Field | Value |
|-------|--------|
| Name | `api` |
| Image URI | `ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/complibot:latest` |
| Port | **8080** TCP |
| Command override | leave empty (image CMD) or `uv,run,uvicorn,apps.api.main:app,--host,0.0.0.0,--port,8080` |
| Log configuration | awslogs → create group `/ecs/complibot-api` |
| Environment | see [13-ssm-secrets-env.md](13-ssm-secrets-env.md) |
| Secrets | `DATABASE_URL` from Secrets Manager |

**Health check (container):**

- Command: `CMD-SHELL,curl -f http://localhost:8080/health || exit 1`
- Or use ALB health check only.

**Create**.

## 11.6 Register task definition — worker

Family: `complibot-worker`. No port mappings.

| Field | Value |
|-------|--------|
| CPU / Memory | 1 vCPU / 2 GB (pipeline may need more) |
| Task role | `complibot-worker-task-role` |
| Command override | `python,apps/worker/main.py` or `uv,run,python,apps/worker/main.py` |
| Log group | `/ecs/complibot-worker` |

## 11.7 Create service — API (ALB attached in step 12)

1. Cluster `complibot-demo` → **Create service**.
2. **Compute:** Launch type **Fargate**.
3. **Task definition:** `complibot-api` latest revision.
4. **Service name:** `complibot-api`.
5. **Desired tasks:** **1** (demo).
6. **Networking:**
   - VPC: `complibot-demo`
   - Subnets: **public** (both)
   - Security group: `complibot-api-sg`
   - **Public IP:** **ON**
7. **Load balancing:** configure in [12-alb-acm-dns.md](12-alb-acm-dns.md) — can create service with ALB in one wizard.
8. **Create service**.

## 11.8 Create service — worker

1. **Create service** on same cluster.
2. Task definition: `complibot-worker`.
3. Service name: `complibot-worker`.
4. Desired tasks: **1**.
5. **No load balancer**.
6. Same public subnets + **new SG** `complibot-worker-sg` with **no inbound rules**.
7. Add **outbound** all (default).
8. Update **RDS SG** to allow 5432 from `complibot-worker-sg`.
9. **Create service**.

## 11.9 Verify tasks running

1. Cluster → **Services** → each service → **Tasks** tab.
2. **Last status** should be **RUNNING**.
3. If **STOPPED**, click task → **Stopped reason** and **Logs** (CloudWatch).

Common fixes:

- Wrong image URI / no ECR pull permission
- Missing `DATABASE_URL` secret
- Cannot reach RDS (SG or wrong subnet)

## Next step

→ [12-alb-acm-dns.md](12-alb-acm-dns.md)
