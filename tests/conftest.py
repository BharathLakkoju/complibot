import pytest
from complibot.db.base import Base
from complibot.db.session import engine


@pytest.fixture(autouse=True)
async def _ensure_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
