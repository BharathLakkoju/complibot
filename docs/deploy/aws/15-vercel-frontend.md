# Step 15 — Deploy frontend on Vercel

**Goal:** Host `apps/web` and point it at your AWS API URL.

## 15.1 Import project

1. Go to [https://vercel.com](https://vercel.com) → sign in with GitHub.
2. **Add New…** → **Project**.
3. **Import** repository `BharathLakkoju/complibot`.
4. **Configure Project:**

| Field | Value |
|-------|--------|
| **Framework Preset** | Next.js (auto-detected) |
| **Root Directory** | Click **Edit** → set `apps/web` |
| **Build Command** | default `next build` |
| **Output Directory** | default `.next` |

## 15.2 Environment variables

**Settings** → **Environment Variables** (before or after first deploy):

| Name | Value | Environments |
|------|--------|--------------|
| `NEXT_PUBLIC_API_URL` | `https://api.yourdomain.com` | Production, Preview |

No trailing slash. Must match ALB/ACM URL from step 12.

## 15.3 Deploy

1. Click **Deploy**.
2. Wait for build success.
3. Copy **Production URL** e.g. `https://complibot-xxx.vercel.app`.

## 15.4 Update AWS CORS and Cognito

1. **ECS task definition** `complibot-api`: set `CORS_ORIGINS` to Vercel production URL (comma-separate preview URLs if needed).
2. **S3 CORS** ([07-s3-bucket.md](07-s3-bucket.md)): add Vercel URL to `AllowedOrigins`.
3. **Cognito** ([09-cognito.md](09-cognito.md)):
   - App client → **Hosted UI** → **Allowed callback URLs** → add  
     `https://YOUR_VERCEL_APP.vercel.app/api/auth/callback/cognito`  
     (exact path depends on your auth library).
   - **Sign-out URLs** → add Vercel URL.

Force new ECS deployment for API after CORS change.

## 15.5 WebSocket from browser

The app derives WS URL from `NEXT_PUBLIC_API_URL` (`apps/web/src/lib/api.ts`):

- `https://api.example.com` → `wss://api.example.com/v1/reviews/{id}/ws`

Ensure ALB supports WebSocket (default) and certificate is valid.

## 15.6 Custom domain (optional)

1. Vercel project → **Settings** → **Domains**.
2. Add `app.yourdomain.com`.
3. Follow DNS instructions (CNAME to Vercel).

## 15.7 MVP limitation

Current UI uses **`/v1/auth/dev-login`**, which must be **disabled** in `APP_ENV=demo`. Until Cognito is wired in the web app, production users cannot sign in—complete Cognito integration before sharing the Vercel URL publicly.

## Verification

- Open Vercel URL → landing page loads.
- Browser devtools **Network**: API calls go to `https://api.yourdomain.com` (not localhost).

## Next step

→ [16-smoke-tests-and-rollback.md](16-smoke-tests-and-rollback.md)
