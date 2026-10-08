# Step 12 — ALB, HTTPS, ACM, and DNS

**Goal:** Public HTTPS endpoint for API + WebSocket. Idle timeout **60 s** (WS heartbeat 15 s).

## 12.1 Request ACM certificate

1. Search **Certificate Manager** → **Request certificate**.
2. **Public certificate**.
3. **Domain names:**
   - `api.yourdomain.com` (or single name you choose)
4. **Validation method:** **DNS validation**.
5. **Request**.
6. **Certificates** → your cert → **Create records in Route 53** (if domain is in Route 53) or add CNAME to your DNS provider manually.
7. Wait until **Status** is **Issued**.

## 12.2 Create Application Load Balancer

1. Search **EC2** → left **Load Balancers** → **Create load balancer**.
2. Type: **Application Load Balancer**.
3. **Name:** `complibot-demo-alb`.
4. **Scheme:** Internet-facing.
5. **IP address type:** IPv4.
6. **Network mapping:** VPC `complibot-demo`, **all public subnets**, AZs enabled.
7. **Security group:** `complibot-alb-sg`.

### Listeners

| Listener | Action |
|----------|--------|
| **HTTPS 443** | Forward to target group (create below) |
| HTTP 80 | Optional redirect to 443 |

8. **Default SSL certificate:** From ACM → select `api.yourdomain.com` cert.

### Create target group (during ALB wizard or separately)

1. **Target type:** IP (required for Fargate).
2. **Name:** `complibot-api-tg`.
3. **Protocol:** HTTP, **Port 8080**.
4. **VPC:** `complibot-demo`.
5. **Health check path:** `/health`.
6. **Healthy threshold:** 2, **Interval:** 30s, **Timeout:** 5s.

7. **Register targets:** ECS will attach IPs when you link the service—skip manual registration.

8. **Create load balancer**.

## 12.3 ALB idle timeout (critical for WebSocket)

1. **Load balancers** → `complibot-demo-alb` → **Attributes** → **Edit**.
2. **Idle timeout:** **60** seconds.
3. Save.

## 12.4 Attach ALB to ECS API service

If not done during service create:

1. ECS → service `complibot-api` → **Update service**.
2. **Load balancing** → **Application Load Balancer**.
3. **Container:** `api:8080`.
4. **Target group:** `complibot-api-tg`.
5. **Update service**.

## 12.5 Security group rules

**complibot-alb-sg inbound:**

| Type | Port | Source |
|------|------|--------|
| HTTPS | 443 | 0.0.0.0/0 |
| HTTP | 80 | 0.0.0.0/0 (if redirect) |

**complibot-api-sg inbound:**

| Type | Port | Source |
|------|------|--------|
| Custom TCP | 8080 | Security group `complibot-alb-sg` |

## 12.6 DNS record

1. Route 53 → **Hosted zones** → your domain → **Create record**.
2. **Record name:** `api`.
3. **Type:** **A** → **Alias** → Alias to ALB → select `complibot-demo-alb`.
4. **Create**.

## 12.7 WebSocket note

ALB supports WebSocket on the same listener. Clients connect to:

```
wss://api.yourdomain.com/v1/reviews/{reviewId}/ws
```

JWT goes in first message `client.hello`, not URL (PRD).

## 12.8 Test

```bash
curl https://api.yourdomain.com/health
```

Expect: `{"status":"ok"}`.

## Next step

→ [13-ssm-secrets-env.md](13-ssm-secrets-env.md)
