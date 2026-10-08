# Step 01 — AWS Budgets and billing alerts

**Goal:** Get email (or SNS) alerts before the demo environment exceeds the **~$75/month** target (PRD).

**Time:** ~15 minutes.

## 1.1 Open AWS Budgets

1. Sign in to [AWS Console](https://console.aws.amazon.com).
2. Confirm region is **us-east-1** (budgets are global but set them while you are in the habit of using this region).
3. Top search bar: type **Budgets**.
4. Click **Budgets** (service under **Billing and Cost Management**).

Or: **Account menu (top right)** → **Billing and Cost Management** → left sidebar **Budgets**.

## 1.2 Create a monthly cost budget

1. Click **Create budget**.
2. Budget type: select **Customize (advanced)** → **Next**.
3. Template: choose **Monthly cost budget** → **Next**.

### Budget setup

| Field | Value |
|-------|--------|
| **Budget name** | `complibot-demo-monthly` |
| **Period** | Monthly |
| **Budget effective dates** | Start: first day of current month (default) |
| **Budgeted amount** | **Fixed** → **75** USD |

4. Click **Next**.

### Alerts (create three thresholds)

For each alert, click **Add an alert threshold**:

| Alert # | Threshold | Type | Email |
|---------|-----------|------|--------|
| 1 | **50** | **Actual** | your email |
| 2 | **80** | **Actual** | same email |
| 3 | **100** | **Actual** | same email |

- **Threshold:** enter the percentage.
- **Alert threshold type:** **Actual** (not forecasted) for hard stops; you may add one **Forecasted** at 100% if you want early warning.

5. **Email recipients:** enter the address that should receive alerts. Confirm the subscription email AWS sends.
6. Click **Next** → review → **Create budget**.

## 1.3 (Optional) Billing preferences

1. **Billing and Cost Management** → **Billing preferences**.
2. Enable **Receive Free Tier usage alerts** if you are on a new account.
3. Enable **Receive billing alerts** if available.

## 1.4 (Optional) Cost anomaly detection

1. Search **Cost Anomaly Detection**.
2. **Create monitor** → **AWS services** → name `complibot-demo`.
3. **Create subscription** → email yourself → threshold e.g. **$10** absolute impact.

## Verification

- **Budgets** list shows `complibot-demo-monthly` with $75 limit.
- You received AWS email to confirm budget notifications.

## Next step

→ [02-bedrock-model-access.md](02-bedrock-model-access.md)
