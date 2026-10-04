# `complibot` Python package

Shared backend code for the API and worker services.

| Module | Role |
|--------|------|
| `complibot` | Config, DB, auth, REST routers, WebSocket hub, domain services |
| `complibot_worker` | SQS consumer and review pipeline stages |

Entrypoints (thin wrappers):

- `apps/api/main.py` → FastAPI `app`
- `apps/worker/main.py` → worker process
