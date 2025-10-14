import pytest_asyncio
from tests.fixtures.ddb_tables import *
from tests.fixtures.moto import *
from tests.fixtures.setup import *

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


from dyno_viewer.db.models import Base
import pytest_asyncio


@pytest_asyncio.fixture
async def db_session():
    """Pytest fixture: yield an in-memory SQLite AsyncSession with schema initialized."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()
