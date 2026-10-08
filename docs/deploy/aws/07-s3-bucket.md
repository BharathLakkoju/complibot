# Step 07 — S3 bucket (documents and reports)

**Goal:** Private bucket for uploads (presigned PUT) and report PDF/JSON. SSE-S3, tenant-prefixed keys.

## 7.1 Create bucket

1. **S3** → **Create bucket**.
2. **Bucket name:** `complibot-demo-documents-YOUR_ACCOUNT_ID` (unique).
3. **Region:** `us-east-1`.
4. **Block all public access:** **ON** (all four checkboxes).
5. **Bucket versioning:** **Enable** (audit trail).
6. **Default encryption:** **SSE-S3**.
7. **Create bucket**.

## 7.2 CORS (for browser uploads from Vercel)

1. Bucket → **Permissions** → **Cross-origin resource sharing (CORS)** → **Edit**.
2. Paste (replace origin after Vercel deploy):

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["PUT", "GET", "HEAD"],
    "AllowedOrigins": [
      "https://YOUR_VERCEL_APP.vercel.app",
      "http://localhost:3000"
    ],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

3. **Save changes**.

Update `AllowedOrigins` in [15-vercel-frontend.md](15-vercel-frontend.md) when you know production URL.

## 7.3 Lifecycle (optional cost control)

1. **Management** → **Create lifecycle rule**.
2. Name: `expire-old-uploads-demo`.
3. Scope: whole bucket or prefix `*/tmp/`.
4. **Expire current versions** after e.g. **90** days (demo policy).

## 7.4 IAM expectations (ECS task roles)

**API role** needs on this bucket:

- `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject` on `arn:aws:s3:::BUCKET/*`
- `s3:ListBucket` on bucket ARN

Prefix pattern in app: `{tenant_id}/...` (see PRD).

**Worker role:** read/write same prefixes for pipeline artifacts.

## 7.5 App environment variable

| Variable | Value |
|----------|--------|
| `S3_BUCKET` | bucket name |
| `AWS_REGION` | `us-east-1` |

In ECS, do **not** set `AWS_ENDPOINT_URL` (LocalStack only).

## Verification

- Bucket shows **Objects** tab empty.
- CORS saved.
- Public access block: **On**.

## Next step

→ [08-sqs-queues.md](08-sqs-queues.md)
