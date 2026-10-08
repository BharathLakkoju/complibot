# Step 04 — Terraform remote state (bootstrap)

**Goal:** S3 bucket + locking for Terraform state before you apply `infra/terraform/` modules.

**Skip this step** only if you deploy 100% via console and never use Terraform (not recommended long term).

## 4.1 Create state S3 bucket (console)

1. Search **S3** → **Create bucket**.
2. **Bucket name:** `complibot-tfstate-demo-us-east-1` (must be globally unique; add suffix if taken).
3. **AWS Region:** `us-east-1`.
4. **Block all public access:** leave **ON**.
5. **Bucket Versioning:** **Enable**.
6. **Default encryption:** **SSE-S3**.
7. **Create bucket**.

## 4.2 (Recommended) Bucket policy — TLS only

1. Open bucket → **Permissions** → **Bucket policy** → **Edit**.
2. Example (replace bucket name and account):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::complibot-tfstate-demo-us-east-1",
        "arn:aws:s3:::complibot-tfstate-demo-us-east-1/*"
      ],
      "Condition": {
        "Bool": { "aws:SecureTransport": "false" }
      }
    }
  ]
}
```

## 4.3 Terraform backend block (in repo)

When modules exist, `infra/terraform/envs/demo/backend.tf` should look like:

```hcl
terraform {
  backend "s3" {
    bucket       = "complibot-tfstate-demo-us-east-1"
    key          = "demo/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
    encrypt      = true
  }
}
```

Terraform 1.10+ supports S3 native locking via `use_lockfile`.

## 4.4 First init (from your laptop)

```bash
cd D:\workFiles\complibot\infra\terraform\envs\demo
terraform init
terraform plan
```

Today the stub only outputs `status`; after you add modules, `plan` will show real resources.

## 4.5 IAM for GitHub role

Grant the deploy role:

- `s3:GetObject`, `s3:PutObject`, `s3:ListBucket` on the state bucket
- Permissions for resources Terraform manages

## Next step

→ [05-network-vpc.md](05-network-vpc.md)
