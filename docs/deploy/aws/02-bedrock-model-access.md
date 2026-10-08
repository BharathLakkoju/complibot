# Step 02 — Amazon Bedrock model access

**Goal:** Enable the models the worker uses for extraction, assessment, and embeddings (PRD Q-03).

**Region:** `us-east-1` only for this guide.

## 2.1 Open Bedrock

1. AWS Console search: **Amazon Bedrock**.
2. Click **Amazon Bedrock**.
3. Left sidebar: **Model access** (older consoles) **or** **Bedrock configurations** → **Model access** / **Enable models**.

> Console labels change; look for **Model access**, **Model catalog**, or **Get access**.

## 2.2 Request model access

1. Click **Modify model access** or **Manage model access** or **Enable specific models**.
2. Enable access for (search each name):

| Use in app | Model / profile (pin in SSM later) |
|------------|-------------------------------------|
| Fast (extract/map) | **Anthropic Claude Haiku 4.5** — inference profile `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| Reasoning (assess/remediate) | **Anthropic Claude Sonnet 5** — profile `us.anthropic.claude-sonnet-5` |
| Embeddings | **Amazon Titan Text Embeddings V2** — `amazon.titan-embed-text-v2:0` |

3. Check the box next to each → **Request model access** or **Save changes**.
4. Wait until status shows **Access granted** (can take minutes; some need one-time account form).

## 2.3 Confirm in Model catalog

1. Left sidebar: **Model catalog** (or **Foundation models**).
2. Search **Claude Haiku 4.5** → open → note **Model ID** and **Inference profiles** (use **US** geo profile, not bare ID for Haiku 4.5 on-demand).
3. Search **Titan Text Embeddings V2** → note model ID.

Write exact IDs on your scratch pad — they go into SSM in [13-ssm-secrets-env.md](13-ssm-secrets-env.md).

## 2.4 (Optional) Test invoke from console

1. **Playgrounds** → **Chat** or **Text**.
2. Select **Claude Haiku 4.5** (profile).
3. Send: `Reply with exactly: OK`
4. If you get a response, access works.

## 2.5 Service quota check

1. Search **Service Quotas**.
2. Filter service: **Amazon Bedrock**.
3. Note default **Requests per minute** for your models; request increases only if demos hit throttling.

## Worker IAM (later)

The **ECS worker task role** (step 11) needs `bedrock:InvokeModel` on **only** these model/profile ARNs — not `*`.

## Next step

→ [03-github-oidc-iam.md](03-github-oidc-iam.md)
