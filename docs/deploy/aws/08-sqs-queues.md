# Step 08 — SQS review queue + DLQ

**Goal:** API enqueues review jobs; worker long-polls. Failed jobs go to DLQ after 3 receives.

## 8.1 Create dead-letter queue (DLQ)

1. Search **SQS** → **Create queue**.
2. **Type:** **Standard**.
3. **Name:** `complibot-review-demo-dlq`.
4. **Visibility timeout:** default (DLQ does not need long timeout).
5. **Encryption:** **Enabled** (SSE-SQS).
6. **Create queue**.
7. Copy **URL** and **ARN** → scratch pad.

## 8.2 Create main queue

1. **Create queue** → **Standard**.
2. **Name:** `complibot-review-demo`.
3. **Visibility timeout:** **900** seconds (15 min — matches `review_deadline_s` in `ai/rules/runtime-config.yaml`).
4. **Message retention:** 4 days (default) or longer for debugging.
5. **Delivery delay:** 0.
6. **Maximum message size:** 256 KB (default).
7. **Receive message wait time:** **20** seconds (long polling).
8. **Encryption:** **Enabled**.

### Dead-letter queue

1. Expand **Dead-letter queue**.
2. **Enabled:** yes.
3. **Choose queue:** `complibot-review-demo-dlq`.
4. **Maximum receives:** **3**.

5. **Create queue**.
6. Copy **Queue URL** → scratch pad (this is `SQS_QUEUE_URL` in ECS).

## 8.3 CloudWatch alarm on DLQ

1. Search **CloudWatch** → **Alarms** → **Create alarm**.
2. **Select metric** → **SQS** → **ApproximateNumberOfMessagesVisible**.
3. **QueueName:** `complibot-review-demo-dlq`.
4. **Conditions:** Greater than **0** for 1 datapoint within 5 minutes.
5. **Notification:** SNS topic or email (create topic if needed).
6. **Alarm name:** `complibot-demo-dlq-not-empty`.
7. **Create alarm**.

## 8.4 IAM

**API task role:**

- `sqs:SendMessage` on main queue ARN.

**Worker task role:**

- `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:GetQueueAttributes`, `sqs:ChangeMessageVisibility` on main queue ARN.

## 8.5 App settings

| Variable | Value |
|----------|--------|
| `SQS_QUEUE_URL` | main queue URL |
| `INLINE_WORKER` | **`false`** |

## Verification

- Main queue **Monitoring** shows 0 messages.
- Redrive policy shows DLQ + maxReceiveCount 3.
- Alarm created.

## Next step

→ [09-cognito.md](09-cognito.md)
