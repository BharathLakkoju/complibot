# Step 09 — Amazon Cognito (user pool + app client)

**Goal:** Users sign in on the frontend; API validates JWT (RS256 via JWKS). **Project roles** (`owner`/`reviewer`/`viewer`) stay in the app database—not Cognito groups.

## 9.1 Create user pool

1. Search **Cognito** → **User pools** → **Create user pool**.

### Step 1 — Application type

- **Application type:** **Single-page application (SPA)** (Vercel + Next.js).

### Step 2 — Configure sign-in

| Option | Value |
|--------|--------|
| Sign-in options | **Email** |
| User name requirements | Email as username |

### Step 3 — Security

| Option | Value |
|--------|--------|
| Password policy | Default or stricter |
| MFA | **No MFA** for demo (enable for prod) |
| Self-registration | **Enable** for demo invite-only later you can disable |

### Step 4 — Sign-up experience

- Required attributes: **email**, **name** (optional but useful).

### Step 5 — Message delivery

- **Send email with Cognito** (demo) or SES (production).

### Step 6 — Integrate your app

- **User pool name:** `complibot-demo`.
- **App client name:** `complibot-web`.
- **Client secret:** **Don't generate** (public SPA client).

### Hosted UI domain

- **Cognito domain:** choose prefix e.g. `complibot-demo-YOURNAME` (must be unique).
- Full domain: `complibot-demo-YOURNAME.auth.us-east-1.amazoncognito.com`

### Callback URLs (temporary — update after Vercel)

Add:

```
http://localhost:3000/api/auth/callback/cognito
https://YOUR_VERCEL_APP.vercel.app/api/auth/callback/cognito
```

> **Note:** The current MVP uses `dev-login` only. You must implement Cognito callback routes in `apps/web` and JWT validation in the API before production. Until then, use this pool for manual testing with Hosted UI + Postman.

### Sign-out URLs

```
http://localhost:3000
https://YOUR_VERCEL_APP.vercel.app
```

### OAuth flows

- **Authorization code grant** (with PKCE for SPA).
- Scopes: **openid**, **email**, **profile**.

7. **Create user pool**.

## 9.2 Record identifiers

**User pool** → **User pool overview**:

| Item | Copy to scratch pad |
|------|---------------------|
| User pool ID | e.g. `us-east-1_xxxxx` |
| ARN | |

**App integration** → **App clients** → `complibot-web`:

| Item | Value |
|------|--------|
| Client ID | |

**Domain** tab: hosted UI domain URL.

## 9.3 Create first user (console)

1. **Users** → **Create user**.
2. **Invite email** or set password.
3. **Email:** your test address.
4. **Mark email verified:** yes (demo).
5. **Create**.

## 9.4 API configuration (when implemented)

| ECS env | Value |
|---------|--------|
| `JWT_ISSUER` | `https://cognito-idp.us-east-1.amazonaws.com/USER_POOL_ID` |
| `JWT_AUDIENCE` | App client ID |

Disable or block `/v1/auth/dev-login` when `APP_ENV=demo`.

## 9.5 Web configuration (when implemented)

Use **Amplify Auth**, **NextAuth**, or **oidc-client-ts** with:

- Authority: issuer URL
- Client ID: app client ID
- Redirect URI: must match callback URL exactly

## Verification

- Hosted UI opens: `https://YOUR_DOMAIN.auth.us-east-1.amazoncognito.com/login?client_id=...`
- Test user can sign in.

## Next step

→ [10-ecr-docker.md](10-ecr-docker.md)
