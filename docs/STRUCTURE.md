# Repository layout

```
complibot/
├── apps/
│   ├── api/              # API service entry (main.py); Alembic config
│   ├── worker/           # Worker service entry (main.py)
│   └── web/              # Next.js 16 frontend
├── packages/
│   ├── complibot/        # Python: complibot + complibot_worker (src layout)
│   └── schemas/          # finding + WebSocket event YAML (codegen input)
├── ai/                   # Runtime AI specs (agents, frameworks, skills, rules)
├── docs/                 # PRD, design system, acceptance criteria, sources
├── data/
│   └── fixtures/         # Sample contracts for local demo
├── database/             # Alembic migrations (when added)
├── eval/                 # Gold sets + harness results
├── infra/terraform/      # AWS IaC
├── scripts/              # Bootstrap, LocalStack, pack validation, codegen
├── tests/                # Python tests
├── AGENTS.md             # Coding-agent conventions (canonical)
├── docker-compose.yml    # Local Postgres + LocalStack
└── pyproject.toml        # Python deps + hatch wheel paths
```

**Framework packs at runtime:** `ai/frameworks/` (single source; no duplicate `frameworks/` copy).

**Product inputs:** `docs/sources/` (engineering + design inputs merged into `docs/PRD.md`).
