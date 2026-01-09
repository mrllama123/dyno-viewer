from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from dyno_viewer.constants import CONFIG_DIR_NAME
from dyno_viewer.db.models import (
    Base,
    ListQueryHistoryResult,
    ListSavedQueriesResult,
    QueryHistory,
    SavedQuery,
    DbDump,
)
from dyno_viewer.models import QueryParameters
from dyno_viewer.util.path import ensure_config_dir
import json
from pathlib import Path
import shutil
from alembic import command
from alembic.config import Config as AlembicConfig
from alembic.util.exc import DatabaseNotAtHead


async def start_async_session(db_path: Path | None = None) -> AsyncSession:
    """Create and return an AsyncSession instance."""
    if not db_path:
        app_path = ensure_config_dir(CONFIG_DIR_NAME)
        db_path = app_path / "db.db"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    async with engine.begin() as conn:
        current = (await conn.exec_driver_sql("PRAGMA journal_mode;")).scalar()
        if not current or str(current).lower() != "wal":
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            await conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
            await conn.exec_driver_sql("PRAGMA foreign_keys=ON;")
        await conn.run_sync(Base.metadata.create_all)
    async_session_local = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    return async_session_local()


def get_alembic_config(
    db_path: Path | None = None, alembic_config_path: Path | None = None
) -> AlembicConfig:
    """gets the alembic config for the given database path

    :param db_path: the database path, defaults to app config
    :type db_path: Path | None, optional
    :param alembic_config_path: the alembic config file path, defaults to the default alembic.ini
    :type alembic_config_path: Path | None, optional
    :return: Alembic configuration object
    :rtype: AlembicConfig
    """
    if not db_path:
        app_path = ensure_config_dir(CONFIG_DIR_NAME)
        db_path = app_path / "db.db"
    if not alembic_config_path:
        alembic_config_path = Path(__file__).resolve().parents[1] / "alembic.ini"
    alembic_cfg = AlembicConfig(str(alembic_config_path))
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite://{db_path.resolve()}")
    alembic_cfg.attributes["configure_logger"] = False
    return alembic_cfg


def is_migration_needed(alembic_cfg: AlembicConfig) -> bool:
    try:
        command.current(alembic_cfg, check_heads=True, verbose=False)
    except DatabaseNotAtHead:
        return True
    except Exception:
        raise
    return False


def migrate_db(
    db_path: Path | None = None, alembic_config_path: Path | None = None
) -> None:
    if not db_path:
        app_path = ensure_config_dir(CONFIG_DIR_NAME)
        db_path = app_path / "db.db"
    alembic_cfg = get_alembic_config(db_path, alembic_config_path)
    if is_migration_needed(alembic_cfg):
        command.upgrade(alembic_cfg, "head")


async def has_alembic_version_table(session: AsyncSession) -> bool:
    result = await session.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version';"
    )
    table = result.scalar()
    return table is not None


async def drop_all_tables(session: AsyncSession) -> None:
    await session.execute(text("DROP TABLE IF EXISTS query_history;"))
    await session.execute(text("DROP TABLE IF EXISTS saved_query;"))
    await session.execute(text("DROP TABLE IF EXISTS alembic_version;"))
    await session.commit()


async def backup_db(
    session: AsyncSession,
    output_path: Path,
    db_path: Path,
    output_file_name: str = "db_dump.json",
) -> DbDump:
    """Backup the database contents"""
    query_history_db_items = await list_all_query_history(session)
    saved_query_db_items = await list_all_saved_queries(session)
    result = DbDump.model_validate(
        {
            "query_history": [item.to_dict() for item in query_history_db_items],
            "saved_queries": [item.to_dict() for item in saved_query_db_items],
        }
    )

    result.db_backup_path = output_path / db_path.name
    result.db_path_to_restore_to = db_path
    db_dump_file_path = output_path / output_file_name
    shutil.copy2(db_path, output_path / db_path.name)

    db_dump_file_path.write_text(result.model_dump_json(indent=4), encoding="utf-8")

    return result


async def restore_db(
    session: AsyncSession,
    dump: DbDump | None = None,
    dump_path: Path | None = None,
    revert_db: bool = False,
) -> None:
    """Restore the database contents from  a DbDump object."""
    if not dump and not dump_path:
        raise ValueError("Either dump or dump_path must be provided.")
    if not dump:
        file_content = dump_path.read_text(encoding="utf-8")
        dump = DbDump.model_validate_json(file_content)
    if revert_db:
        if not dump.db_backup_path or not dump.db_path_to_restore_to:
            raise ValueError(
                "No db_backup_path found in the dump to revert the database."
            )
        shutil.copy2(dump.db_backup_path, dump.db_path_to_restore_to)
        return

    for item in dump.query_history:
        query_history = QueryHistory(**item)
        session.add(query_history)

    for item in dump.saved_queries:
        saved_query = SavedQuery(**item)
        session.add(saved_query)

    await session.commit()


async def get_last_query_history(session: AsyncSession) -> QueryHistory | None:
    stmt = select(QueryHistory).order_by(QueryHistory.created_at.desc()).limit(1)
    result = await session.execute(stmt)
    return result.scalars().first()


async def add_query_history(session: AsyncSession, params: QueryParameters) -> None:
    query_history = QueryHistory.from_query_params(params)
    stmt = (
        select(QueryHistory)
        .where(QueryHistory.filter_conditions == query_history.filter_conditions)
        .where(QueryHistory.key_condition == query_history.key_condition)
        .order_by(QueryHistory.created_at)
        .limit(1)
    )
    result = await session.execute(stmt)
    last_query = result.scalars().first()
    if last_query:
        return

    session.add(query_history)
    await session.commit()
    await session.refresh(query_history)


async def delete_query_history(session: AsyncSession, history_id: int) -> None:
    stmt = select(QueryHistory).where(QueryHistory.id == history_id)
    result = await session.execute(stmt)
    query_history = result.scalars().first()
    if query_history:
        await session.delete(query_history)
        await session.commit()


async def delete_all_query_history(
    session: AsyncSession, delete_table: bool = False
) -> None:
    stmt = delete(QueryHistory)
    await session.execute(stmt)
    await session.commit()
    if delete_table:
        await session.execute(text("DROP TABLE IF EXISTS query_history;"))
        await session.commit()


async def get_total_pages(session: AsyncSession, page_size: int) -> int:
    total = await session.scalar(
        select(func.count()).select_from(QueryHistory)  # pylint: disable=not-callable
    )
    return (total + page_size - 1) // page_size


# async def get_saved_query_by_name(
#     session: AsyncSession, name: str
# ) -> SavedQuery | None:
#     stmt = select(SavedQuery).where(SavedQuery.name == name)
#     result = await session.execute(stmt)
#     return result.scalars().first()


async def add_saved_query(
    session: AsyncSession, params: QueryParameters, name: str, description: str = ""
) -> None:
    saved_query = SavedQuery.from_query_params(params, name, description)
    session.add(saved_query)
    await session.commit()
    await session.refresh(saved_query)


async def get_saved_query(session: AsyncSession, query_id: int) -> SavedQuery | None:
    stmt = select(SavedQuery).where(SavedQuery.id == query_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_query_history(
    session: AsyncSession, history_id: int
) -> QueryHistory | None:
    stmt = select(QueryHistory).where(QueryHistory.id == history_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def list_query_history(
    session: AsyncSession, page: int = 1, page_size: int = 20
) -> ListQueryHistoryResult:
    offset = (page - 1) * page_size
    stmt = (
        select(QueryHistory)
        .order_by(QueryHistory.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    items = result.scalars().all()

    total = await session.scalar(
        select(func.count()).select_from(QueryHistory)  # pylint: disable=not-callable
    )
    total_pages = (total + page_size - 1) // page_size
    return ListQueryHistoryResult(total=total, total_pages=total_pages, items=items)


async def list_all_query_history(session: AsyncSession) -> list[QueryHistory]:
    stmt = select(QueryHistory)
    result = await session.execute(stmt)
    return result.scalars().all()


async def list_saved_queries(
    session: AsyncSession, page: int = 1, page_size: int = 20, search: str = ""
) -> ListSavedQueriesResult:
    offset = (page - 1) * page_size
    stmt = (
        select(SavedQuery)
        .order_by(SavedQuery.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    if search:
        stmt = stmt.where(SavedQuery.name.ilike(f"%{search}%"))
    result = await session.execute(stmt)
    items = result.scalars().all()

    total = await session.scalar(
        select(func.count()).select_from(SavedQuery)  # pylint: disable=not-callable
    )
    total_pages = (total + page_size - 1) // page_size
    return ListSavedQueriesResult(total=total, total_pages=total_pages, items=items)


async def list_all_saved_queries(session: AsyncSession) -> list[SavedQuery]:
    stmt = select(SavedQuery)
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_saved_query(session: AsyncSession, query_id: int) -> None:
    stmt = select(SavedQuery).where(SavedQuery.id == query_id)
    result = await session.execute(stmt)
    saved_query = result.scalars().first()
    if saved_query:
        await session.delete(saved_query)
        await session.commit()


async def delete_all_saved_queries(
    session: AsyncSession, delete_table: bool = False
) -> None:
    stmt = delete(SavedQuery)
    await session.execute(stmt)
    await session.commit()
    if delete_table:
        await session.execute(text("DROP TABLE IF EXISTS saved_query;"))
        await session.commit()
