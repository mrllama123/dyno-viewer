import asyncio
from pathlib import Path

from dyno_viewer.util.path import get_user_config_dir
from dyno_viewer.constants import CONFIG_DIR_NAME
from dyno_viewer.db.utils import (
    start_async_session,
    migrate_db,
    backup_db,
    drop_all_tables
)
import argparse
import os


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
        await drop_all_tables(session)
    except Exception:
        raise
    finally:
        if session:
            await session.close()
    # db_file_path.unlink(missing_ok=True)
    migrate_db(
        db_path=db_file_path,
    )


if __name__ == "__main__":
    asyncio.run(main())
