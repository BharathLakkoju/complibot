import asyncio

import pytest
from complibot.db.base import Base
from complibot.db.schema_patches import apply_schema_patches
from complibot.db.session import engine


@pytest.fixture(autouse=True)
async def _ensure_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(apply_schema_patches)
    await engine.dispose()
    yield
    from complibot.services.queue import _inline_tasks

    pending = list(_inline_tasks)
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)
    await engine.dispose()

