from typing import AsyncGenerator
import aiosqlite
import pytest_asyncio
from tests.fixtures.ddb_tables import *
from tests.fixtures.moto import *
from tests.fixtures.setup import *

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dyno_viewer.constants import CONFIG_DIR_NAME
from dyno_viewer.db.data_store import setup_connection


from dyno_viewer.db.models import Base
from pathlib import Path


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
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


@pytest_asyncio.fixture
async def data_store_db_session() -> AsyncGenerator[aiosqlite.Connection, None]:
    try:
        connection = await setup_connection()
        yield connection
    finally:
        await connection.close()


@pytest.fixture
def user_config_dir_tmp_path(tmp_path: Path, mocker) -> Path:
    """Pytest fixture: create a temporary user config directory and mock the config path retrieval to use it."""
    path = tmp_path / CONFIG_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    mocker.patch("dyno_viewer.models.ensure_config_dir", return_value=path)
    return path
