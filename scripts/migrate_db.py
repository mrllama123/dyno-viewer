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
    migrate_db,
    backup_db,
    restore_db,
)
from alembic.config import Config
from alembic import command
import argparse
from sqlalchemy import MetaData
import os

from dyno_viewer.util.path import ensure_config_dir


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="tests database migration scripts for dyno viewer"
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
        "--db-path",
        "-d",
        dest="db_path",
        type=str,
        help="Path to the database file to migrate. Will use default app path if not provided",
    )
    args = parser.parse_args()
    working_dir = Path(args.working_dir).resolve()

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

    migrate_db(
        db_path=db_file_path,
    )


if __name__ == "__main__":
    asyncio.run(main())
