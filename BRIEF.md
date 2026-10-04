# Real-time AI Compliance Review Copilot — project brief

Owner: Bharath. Purpose: a portfolio "finishing blow" project for interviews (Deloitte and similar) showing Python, AI, FastAPI, WebSockets and AWS.

## Concept
Teams upload contracts / policy documents. AI agents check them against selectable frameworks: GDPR, SOC 2, ISO/IEC 27001, HIPAA, and a custom Internal Policy pack. Findings stream live to all reviewers (with the exact clause cited, severity, confidence). Reviewers accept/reject/comment on findings together in real time (presence, live decisions). Output: an audit-ready report (PDF/JSON) with evidence trail.

## Skills to showcase
- Python + AI: RAG over documents (chunking, embeddings, pgvector), agent pipeline (clause extraction -> control mapping -> risk scoring -> remediation suggestion), citations + confidence, an evaluation harness with a labeled set and accuracy metrics. LLM via Amazon Bedrock (OpenRouter fallback for local dev).
- FastAPI: typed REST API (uploads, projects, frameworks, findings, reports), auth, background jobs.
- WebSockets: token streaming of findings, presence, collaborative decisions, reconnect/resume with event replay.
- AWS: S3 (docs), ECS Fargate (API + workers), RDS Postgres + pgvector, SQS (processing queue), Cognito (auth), CloudWatch (logs/metrics), IaC with Terraform or CDK, CI/CD.
- Target: focused MVP in 2-3 weeks. Bharath's usual frontend stack: Next.js 16, React 19, TypeScript, Tailwind 4.

## Deliverables being produced (in /workspace/compliance-copilot/)
PRD, design system, acceptance criteria, and AI agent/skill/rule definitions for the five frameworks.
Teammate inputs go in /workspace/compliance-copilot/input/.
