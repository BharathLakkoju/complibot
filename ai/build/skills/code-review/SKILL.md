# Build skill: code review

**Use when** reviewing a pull request, branch, or local diff for this repository — manually, in Cursor, or via Bugbot / security review.

**Human process doc:** [`docs/CODE-REVIEW-WORKFLOW.md`](../../../docs/CODE-REVIEW-WORKFLOW.md).

## Setup

1. Identify the **base branch** (default `master`) and whether the user wants `branch changes` or `uncommitted changes` only.
2. Read the PR description and file list; note touch areas (API, worker, web, `ai/`, infra).
3. Load relevant `.cursor/rules/*.mdc` for those paths (`security-and-compliance` always applies).

## Automated checks (run or verify CI)

From repo root:

```bash
make lint && make test && make packs-validate
pnpm -C apps/web typecheck && pnpm -C apps/web lint
```

If schemas or events changed: `make schemas` and confirm generated artifacts are committed.

If pipeline, prompts, packs, or `runtime-config.yaml` changed: follow [`run-eval-harness/SKILL.md`](../run-eval-harness/SKILL.md) smoke subset before approving.

## Review pass (ordered)

1. **Security and compliance** — AuthZ on every path; 404 cross-tenant; presigned URL TTL ≤ 5 min; input limits; parse documents in workers only; no secrets in logs or client payloads.
2. **AI pipeline invariants** — No auto-accept; citations verified before publish; `wrap_document()` for untrusted text; no hard-coded model IDs; framework facts from packs/YAML only.
3. **Contracts** — WS events match `packages/schemas/events.yaml`; breaking changes include codegen + contract tests + frontend handling.
4. **Audit** — Append-only `review_decision` and related audit writes; Owner-only override and sign-off.
5. **Product ACs** — Spot-check against [`docs/ACCEPTANCE-CRITERIA.md`](../../../docs/ACCEPTANCE-CRITERIA.md) for the touched areas; cite `AC-*` IDs in findings when relevant.
6. **Tests** — New behaviour covered; integration tests for auth and tenancy; no real LLM calls in unit/integration tests (`FakeLLM` only).
7. **UI** — Disclaimer and demo notice present where required; accessibility and CSP conventions in `frontend.mdc`.

## Optional delegated reviewers

Launch **at most one** specialized subagent when the user asks or the diff is large:

- **Bugbot** — `description: "Bugbot"`, diff `branch changes`, optional `Custom Instructions` listing concerns.
- **Security review** — same shape with `description: "Security Review"`.

Do not launch both in parallel unless the user requests it. Summarize subagent output as a table: Severity | Location (file:line) | Finding.

## Output format

Return a concise report:

1. **Summary** — What changed and overall risk (low / medium / high).
2. **CI** — Commands run and pass/fail (or "not run" with reason).
3. **Findings table** — Sorted by severity (blocker → nit). Columns: Severity, Location, Finding, Suggested fix (optional).
4. **AC coverage** — List AC IDs verified or gaps needing tests.
5. **Merge recommendation** — approve / request changes / block, with one sentence why.

Never claim merge approval on behalf of a human reviewer. Never log or quote document text from fixtures in the review output.

## Definition of done cross-check

Before recommending approve, confirm items from [`ai/build/AGENTS.md`](../AGENTS.md) that apply to this diff (types, migrations, Playwright when UI changes, eval when AI changes).
