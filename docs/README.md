# Compliance Review Copilot: project index

Portfolio project by Bharath: a real-time AI copilot that reviews contracts and policies against GDPR, SOC 2, ISO/IEC 27001:2022, HIPAA and an Internal Policy pack, streams cited findings to a review team, and produces an audit-ready report. Status: specification only (2026-10-05 IST). Nothing is built or measured yet.

**Start here:** [`PRD.md`](PRD.md) → [`DESIGN-SYSTEM.md`](DESIGN-SYSTEM.md) → [`ACCEPTANCE-CRITERIA.md`](ACCEPTANCE-CRITERIA.md). Decisions awaiting Bharath's confirmation: [PRD §19](PRD.md#19-decisions-log). Open questions: [PRD §20](PRD.md#20-open-questions-for-bharath). Conflicts with `ai/` (all resolved): [PRD §21](PRD.md#21-known-conflicts-with-ai-resolved-2026-10-05).

## Folder map (`/workspace/compliance-copilot/`)

| Path | What it is |
|---|---|
| [`BRIEF.md`](../BRIEF.md) | Original one-page brief |
| **`docs/`** | **Merged product, design and acceptance specs (this folder)** |
| [`docs/PRD.md`](PRD.md) | Problem, personas, goals, metrics (targets), scope (MVP / Phase 2 / stretch), user stories, FRs, AI behaviour, realtime, architecture, data model, WS contract, NFRs, security, eval plan, risks + success estimate, milestones, decisions log, open questions, `ai/` conflicts |
| [`docs/DESIGN-SYSTEM.md`](DESIGN-SYSTEM.md) | Principles, tokens and Tailwind 4 `@theme`, typography, severity colours and WCAG AA contrast results, spacing, motion, components with states, key screens and flows, accessibility |
| [`docs/ACCEPTANCE-CRITERIA.md`](ACCEPTANCE-CRITERIA.md) | Given/When/Then criteria by feature, with ID, priority, verification method and traceability to the engineering and design inputs |
| **`input/`** | **Expert inputs (read-only sources)** |
| [`input/engineering.md`](../input/engineering.md) | Head of Engineering: success estimate, risks, architecture, types, WS schema, scope, stack, acceptance criteria, eval harness |
| [`input/design.md`](../input/design.md) | Design Head: principles, tokens, components, screens, UX acceptance criteria, open questions |
| [`input/design-contrast.py`](../input/design-contrast.py) · [`input/design-contrast.json`](../input/design-contrast.json) | Contrast checker and its computed output (136 / 136 pairs pass) |
| **`ai/`** | **Runtime AI and build-time agent definitions (separate effort, written from the brief before the inputs; see PRD §21)** |
| [`ai/README.md`](../ai/README.md) | Overview of the runtime vs build layers |
| [`ai/agents/`](../ai/agents/README.md) | 7 pipeline agents: 01 Orchestrator, 02 Ingestion & Clause Extractor, 03 Framework Mapper, 04 Gap & Risk Assessor, 05 Remediation Writer, 06 Citation Verifier, 07 Report Composer |
| [`ai/agents/schemas/`](../ai/agents/schemas/) | `finding.schema.yaml` (shared Finding JSON Schema) and `events.yaml` (WebSocket event contract v1) |
| [`ai/frameworks/`](../ai/frameworks/README.md) | Framework packs (`pack.yaml` + README): `gdpr`, `soc2`, `iso27001`, `hipaa`, `internal-policy` (template) |
| [`ai/rules/`](../ai/rules/) | Global invariants: 01 cite-or-abstain, 02 no legal advice, 03 severity rubric, 04 confidence thresholds, 05 PII handling, 06 prompt-injection defence, 07 schema validation; `runtime-config.yaml` (thresholds 0.85 / 0.55, budgets, model tiers) |
| [`ai/skills/`](../ai/skills/) | Runtime skills: breach-notification-timeline, clause-segmentation, confidence-calibration, cross-border-transfer, pii-phi-detection, retention-period-extraction, subprocessor-analysis |
| [`ai/build/`](../ai/build/AGENTS.md) | Coding-agent instructions: `AGENTS.md`, `.cursor/rules/*.mdc` (ai-pipeline, aws-iac, frontend, python-fastapi, security-and-compliance, testing, websocket-contract), build skills (add-framework-pack, add-websocket-event, deploy-to-aws, run-eval-harness) |

## Conventions
- Every number is a **target** or **estimate** unless stated otherwise; success probabilities are judgment, not data.
- ISO/IEC 27001 and SOC 2 control text is paraphrased; only official IDs are used. GDPR and HIPAA may be quoted.
- Demo data is synthetic or public only.
- Acceptance criteria IDs: `AC-<AREA>-NN`; decisions `D-NN`; open questions `Q-NN`; `ai/` conflicts `C-NN`.
