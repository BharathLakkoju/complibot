"""Idempotent DDL for live databases where create_all does not alter existing tables."""

from sqlalchemy import text
from sqlalchemy.engine import Connection


def apply_schema_patches(sync_conn: Connection) -> None:
    sync_conn.execute(
        text(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)"
        )
    )
