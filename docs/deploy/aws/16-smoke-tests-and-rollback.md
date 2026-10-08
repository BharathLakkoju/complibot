# Step 16 — Smoke tests and rollback

**Goal:** Prove the stack works end-to-end; know how to roll back.

## 16.1 API health

```bash
curl -s https://api.yourdomain.com/health
```

Expected: `{"status":"ok"}`

## 16.2 Readiness (when implemented)

```bash
curl -s https://api.yourdomain.com/v1/readyz
```

Should check DB, S3, SQS (skill target).

## 16.3 WebSocket handshake

Use a WS client (e.g. `websocat`, Postman, or browser test harness):

1. Obtain valid **Cognito access token** (or dev token only in non-prod).
2. Connect: `wss://api.yourdomain.com/v1/reviews/REV_ID/ws`
3. Send first message:

```json
{
  "v": 1,
  "type": "client.hello",
  "payload": {
    "token": "BEARER_JWT",
    "lastSeq": 0,
    "clientVersion": "0.1.0"
  }
}
```

4. Expect `server.welcome` with `heartbeatMs: 15000`.

## 16.4 Review pipeline

1. Create project via REST (with auth).
2. Start demo or upload flow.
3. Confirm SQS **ApproximateNumberOfMessagesSent** increases then returns to 0.
4. Confirm **findings** appear via REST or WS `finding.created`.
5. CloudWatch log group `/ecs/complibot-worker` shows processing without stack traces.

## 16.5 Security spot checks

- [ ] `dev-login` returns 403 on `APP_ENV=demo`
- [ ] S3 bucket has no public objects
- [ ] RDS not publicly accessible
- [ ] DLQ alarm not firing
- [ ] Logs contain **no** document body text (spot-check random lines)

## 16.6 Rollback application

1. ECR → find previous image tag (git SHA).
2. ECS → task definition → **Create revision** → image tag = previous SHA.
3. **Update service** → force deployment.
4. Worker service same.

Or GitHub Actions redeploy previous commit.

## 16.7 Rollback database

**Forward-only migrations.** If a migration breaks:

1. Fix forward with new migration.
2. Restore RDS from snapshot only as last resort (data loss since snapshot).

## 16.8 Rollback Terraform

```bash
cd infra/terraform/envs/demo
terraform plan
# revert code to previous commit
terraform apply
```

## Next step

→ [17-cicd-github-actions.md](17-cicd-github-actions.md)
