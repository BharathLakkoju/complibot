# Build-time agent instructions

The canonical repo guide for coding agents is **[`AGENTS.md`](../../AGENTS.md)** at the repository root (commands, layout, architecture).

This file keeps the **extended definition of done** and pointers to `.cursor/rules` and build skills in `ai/build/skills/`.

## Definition of done (full)
- [ ] Types are generated from schemas, and mypy and tsc pass with no new `Any` or `any`.
- [ ] Unit and integration tests cover the new behaviour. Reference matching `AC-*` IDs from `docs/ACCEPTANCE-CRITERIA.md` in test names where applicable.
- [ ] Prompt, pipeline, or pack changes pass the eval **regression** gate when CI is enabled.
- [ ] New WS events: update `ai/agents/schemas/events.yaml`, run `make schemas`, contract test, frontend reducer, replay test.
- [ ] Logs contain no document text. Auth + tenant checks on new endpoints.
- [ ] Alembic migrations reversible when schema changes land in `database/alembic/`.
- [ ] UI changes: Playwright + axe (0 contrast violations, both themes).
- [ ] Legal disclaimer and demo-data notice still render where required.

## Cursor rules
Copy or sync from `ai/build/.cursor/` to the repo root `.cursor/` when scaffolding. Rules reference `packages/complibot/` and `apps/web/`.
