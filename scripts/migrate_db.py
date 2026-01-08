import asyncio
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from sqlalchemy import select
from dyno_viewer.util.path import get_user_config_dir
from dyno_viewer.constants import CONFIG_DIR_NAME
from dyno_viewer.db.models import QueryHistory, SavedQuery, DbDump
from dyno_viewer.db.utils import (
    has_alembic_version_table,
    list_all_query_history,
    list_all_saved_queries,
    delete_all_query_history,
    delete_all_saved_queries,
    start_async_session,
    backup_db,
    restore_db,
)
from alembic.config import Config
from alembic import command
import argparse
from sqlalchemy import MetaData
import os

from dyno_viewer.util.path import ensure_config_dir


async def db_migrate(
    migration_config_path: Path,
    db_file_path: Path,
) -> None:
    alembic_cfg = Config(str(migration_config_path.resolve()))
    print(f"Applying migration to sqlite://{db_file_path.resolve()}")
    alembic_cfg.set_main_option(
        "sqlalchemy.url",
        f"sqlite://{db_file_path.resolve()}",
    )
    command.upgrade(alembic_cfg, "head")
    print("Migration applied successfully.")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrates existing database to use Alembic for migrations."
    )
    parser.add_argument(
        "--working-dir",
        "-w",
        dest="working_dir",
        type=str,
        help="working directory to use for migration files.",
        default="./working_dir",
    )
    parser.add_argument(
        "-ac",
        "--alembic-config",
        dest="alembic_config",
        type=str,
        help="Path to alembic.ini file.",
    )
    parser.add_argument(
        "--db-path",
        "-d",
        dest="db_path",
        type=str,
        help="Path to the database file to migrate. Will use default app path if not provided",
    )
    args = parser.parse_args()
    working_dir = Path(args.working_dir).resolve()
    migration_config_path = (
        Path(args.alembic_config)
        if args.alembic_config
        else Path.cwd() / "dyno_viewer" / "alembic.ini"
    )
    db_file_path = (
        Path(args.db_path).resolve()
        if args.db_path
        else get_user_config_dir(CONFIG_DIR_NAME) / "db.db"
    )
    try:
        os.makedirs(working_dir, exist_ok=True)
        session = await start_async_session(db_file_path)
        dump = await backup_db(
            session,
            output_path=working_dir,
            db_path=db_file_path,
        )
        
    except Exception:
        raise
    finally:
        if session:
            await session.close()

    await db_migrate(migration_config_path, db_file_path)


if __name__ == "__main__":
    asyncio.run(main())
