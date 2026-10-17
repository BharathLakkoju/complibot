"""Idempotent DDL for live databases where create_all does not alter existing tables."""

from sqlalchemy import text
from sqlalchemy.engine import Connection


def apply_schema_patches(sync_conn: Connection) -> None:
    dialect = sync_conn.dialect.name
    if dialect == "postgresql":
        sync_conn.execute(
            text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)")
        )
        return
    if dialect == "sqlite":
        rows = sync_conn.execute(text("PRAGMA table_info(users)")).fetchall()
        if not rows:
            return
        if any(row[1] == "password_hash" for row in rows):
            return
        sync_conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)"))
