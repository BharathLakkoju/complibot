# Compliance Review Copilot (CompliBot)

Real-time AI compliance review for contracts and policies: verified citations, collaborative decisions, audit-ready reports.

**Docs:** [`docs/PRD.md`](docs/PRD.md) · [`docs/DESIGN-SYSTEM.md`](docs/DESIGN-SYSTEM.md) · [`docs/ACCEPTANCE-CRITERIA.md`](docs/ACCEPTANCE-CRITERIA.md) · [`docs/STRUCTURE.md`](docs/STRUCTURE.md) · [`AGENTS.md`](AGENTS.md)

## Quick start (local)

```bash
cp .env.example .env
make bootstrap
make up
make migrate   # optional; API also creates tables on startup in local dev
make api       # terminal 1
make worker    # terminal 2
make web       # terminal 3
```

Open [http://localhost:3000](http://localhost:3000) and click **Try with a sample contract**.

| Service | URL |
|---------|-----|
| Web | http://localhost:3000 |
| API | http://localhost:8000 |
| Health | http://localhost:8000/health |

## Architecture (MVP)

- **apps/web** — Next.js 16, React 19, Tailwind 4
- **apps/api** · **apps/worker** — thin service entrypoints
- **packages/complibot** — shared Python (API, DB, WebSocket, worker pipeline)
- **packages/schemas** — wire-format YAML for codegen
- **ai/frameworks** — GDPR, SOC 2, ISO 27001, HIPAA, Internal Policy packs (runtime source)
- **ai/** — Agent specs, skills, rules
- **data/fixtures** — synthetic sample contracts
- **eval/** · **infra/terraform/** — harness and AWS skeleton

## Commands

See [`AGENTS.md`](AGENTS.md) for the full command table (`make schemas`, `make packs-validate`, `eval run`, etc.).

## Deploy to AWS

Full click-by-click runbook (18 steps): [`docs/deploy/aws/README.md`](docs/deploy/aws/README.md).

## Demo data policy

Use **synthetic or public sample contracts only**. Do not upload real confidential data in demo environments.

## Status

This repository ships a **working local vertical slice**: dev auth, projects, sample contract review, WebSocket finding stream, decisions, and verified citation spans. AWS deploy, full agent pipeline, PDF reports, and eval CI gates follow the milestone plan in the PRD.
