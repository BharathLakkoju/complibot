# Step 05 — VPC and networking (no NAT gateway)

**Goal:** VPC with **public subnets** (Fargate + ALB) and **private subnets** (RDS). **No NAT gateway** (cost saving per PRD).

## Option A — VPC wizard (fastest for demo)

1. Search **VPC** → **Create VPC**.
2. Choose **VPC and more** (wizard).
3. Settings:

| Field | Value |
|-------|--------|
| Name tag | `complibot-demo` |
| IPv4 CIDR | `10.0.0.0/16` |
| **Number of Availability Zones** | **2** |
| **Number of public subnets** | **2** |
| **Number of private subnets** | **2** |
| **NAT gateways** | **None** (0) |
| VPC endpoints | S3 Gateway only if offered (optional) |

4. Click **Create VPC**.
5. Note on scratch pad:
   - **VPC ID**
   - **Public subnet IDs** (2)
   - **Private subnet IDs** (2)

## Option B — Terraform `network` module (when implemented)

Apply module from repo per `aws-iac.mdc`: public subnets route to IGW; private subnets have no default route to internet.

## 5.1 S3 gateway endpoint (recommended, free)

1. **VPC** → **Endpoints** → **Create endpoint**.
2. **Service category:** AWS services.
3. **Service:** type `s3` → select **com.amazonaws.us-east-1.s3** (Gateway).
4. **VPC:** `complibot-demo`.
5. **Route tables:** select **private** route tables associated with RDS subnets (and any private RT).
6. **Policy:** Full access (default) or restrict to your bucket ARN later.
7. **Create endpoint**.

## 5.2 Security groups (create empty shells; rules in later steps)

### SG: `complibot-alb`

1. **VPC** → **Security groups** → **Create security group**.
2. Name: `complibot-alb-sg`, VPC: `complibot-demo`.
3. **Inbound:** (add in step 12) HTTPS 443 from `0.0.0.0/0`.
4. **Outbound:** All traffic (default).
5. Create.

### SG: `complibot-api`

1. Create SG: `complibot-api-sg`.
2. **Inbound:** (step 12) TCP **8080** from `complibot-alb-sg` only.
3. Outbound: All.

### SG: `complibot-rds`

1. Create SG: `complibot-rds-sg`.
2. **Inbound:** TCP **5432** from `complibot-api-sg` (add worker SG later too).
3. Outbound: default.

Write all SG IDs on scratch pad.

## 5.3 Fargate networking note

ECS tasks for **api** and **worker** use **public subnets** with **Auto-assign public IP: ENABLED** so they can reach Bedrock and ECR without NAT. Their security groups must **not** allow inbound from the internet—only from ALB (api) or nothing (worker).

## Verification

- VPC has 2 public + 2 private subnets across 2 AZs.
- No NAT gateway in **NAT gateways** list.
- Three security groups created.

## Next step

→ [06-rds-postgres.md](06-rds-postgres.md)
