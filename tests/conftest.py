from typing import AsyncGenerator
import pytest_asyncio
from tests.fixtures.ddb_tables import *
from tests.fixtures.moto import *
from tests.fixtures.setup import *

from dyno_viewer.constants import CONFIG_DIR_NAME
import pytest


from pathlib import Path


from dyno_viewer.db.manager import DatabaseManager


@pytest_asyncio.fixture
async def db_manager() -> AsyncGenerator[DatabaseManager, None]:
    """Fixture for DatabaseManager"""
    try:
        manager = DatabaseManager()
        await manager.setup()
        yield manager
    finally:
        await manager.close()


@pytest.fixture
def user_config_dir_tmp_path(tmp_path: Path, mocker) -> Path:
    """Pytest fixture: create a temporary user config directory and mock the config path retrieval to use it."""
    path = tmp_path / CONFIG_DIR_NAME
    path.mkdir(parents=True, exist_ok=True)
    mocker.patch("dyno_viewer.models.ensure_config_dir", return_value=path)
    return path
