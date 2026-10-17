# Production Next.js image (build context: repo root). NEXT_PUBLIC_API_URL is a build-arg.
FROM node:22-bookworm-slim AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@9 --activate
COPY pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web apps/web
RUN pnpm install --frozen-lockfile --filter @complibot/web...
ARG NEXT_PUBLIC_API_URL
RUN case "$NEXT_PUBLIC_API_URL" in https://?*) ;; *) echo "NEXT_PUBLIC_API_URL must be https://<host>, got '$NEXT_PUBLIC_API_URL'" >&2; exit 1 ;; esac
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_TELEMETRY_DISABLED=1
# t4g.micro has 1 GB RAM (+2 GB swap); cap the build heap.
ENV NODE_OPTIONS=--max-old-space-size=512
WORKDIR /app/apps/web
RUN pnpm build

FROM node:22-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 nodejs \
    && useradd --system --uid 1001 --gid nodejs nextjs
COPY --from=builder /app/apps/web/public ./apps/web/public
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static
USER nextjs
# Host networking: bind loopback only so :3000 is reachable solely through Caddy.
ENV HOSTNAME=127.0.0.1
ENV PORT=3000
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:3000/ || exit 1
CMD ["node", "apps/web/server.js"]
