# Database migrations

Alembic configuration: [`alembic.ini`](../apps/api/alembic.ini) (paths reference this folder).

```bash
uv run alembic -c apps/api/alembic.ini upgrade head
```

Local dev also auto-creates tables on API startup when using SQLite.
