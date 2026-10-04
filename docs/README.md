# Compliance Review Copilot: project index

Portfolio project by Bharath: a real-time AI copilot that reviews contracts and policies against GDPR, SOC 2, ISO/IEC 27001:2022, HIPAA and an Internal Policy pack, streams cited findings to a review team, and produces an audit-ready report.

**Start here:** [`PRD.md`](PRD.md) → [`DESIGN-SYSTEM.md`](DESIGN-SYSTEM.md) → [`ACCEPTANCE-CRITERIA.md`](ACCEPTANCE-CRITERIA.md) → [`STRUCTURE.md`](STRUCTURE.md). Decisions: [PRD §19](PRD.md#19-decisions-log). Open questions: [PRD §20](PRD.md#20-open-questions-for-bharath).

## Folder map

| Path | What it is |
|---|---|
| [`BRIEF.md`](BRIEF.md) | Original one-page brief |
| **`docs/`** | Merged product, design and acceptance specs |
| [`docs/sources/`](sources/) | Expert inputs (engineering, design, contrast checker) |
| **`apps/`** | `api`, `worker`, `web` deployable services |
| **`packages/`** | `complibot` (Python), `schemas` (YAML contracts) |
| **`ai/`** | Runtime agents, frameworks, skills, rules; `ai/build/` for coding-agent rules |
| **`data/fixtures/`** | Sample contracts for local demo |
| **`eval/`** | Gold sets and harness results |
| **`infra/terraform/`** | AWS IaC |
| [`AGENTS.md`](../AGENTS.md) | Coding-agent conventions (canonical) |

## Conventions
- Every number is a **target** or **estimate** unless stated otherwise.
- ISO/IEC 27001 and SOC 2 control text is paraphrased; only official IDs are used.
- Demo data is synthetic or public only.
- Acceptance criteria IDs: `AC-<AREA>-NN`; decisions `D-NN`; open questions `Q-NN`.
