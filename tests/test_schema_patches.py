import pytest
from complibot.db.base import Base
from complibot.db.schema_patches import apply_schema_patches
from complibot.db.session import engine
from sqlalchemy import text


@pytest.mark.asyncio
async def test_password_hash_column_added_to_legacy_users_table() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(
            lambda sync: Base.metadata.tables["tenants"].create(sync, checkfirst=True)
        )
        await conn.execute(
            text(
                """
                CREATE TABLE users (
                    id VARCHAR(32) PRIMARY KEY,
                    tenant_id VARCHAR(32) NOT NULL,
                    email VARCHAR(320) UNIQUE NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
        )
        await conn.run_sync(apply_schema_patches)
        cols = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'users' AND column_name = 'password_hash'"
            )
        )
        assert cols.scalar_one() == "password_hash"
