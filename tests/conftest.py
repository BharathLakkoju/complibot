import pytest
from complibot.db.base import Base
from complibot.db.session import engine


@pytest.fixture(autouse=True)
async def _ensure_schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    # asyncpg connections are bound to the loop that opened them; each test (and each
    # TestClient portal) runs its own loop, so never hand a pooled connection across.
    await engine.dispose()
    yield
    await engine.dispose()
