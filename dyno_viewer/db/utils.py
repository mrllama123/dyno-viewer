from typing import AsyncGenerator, Iterator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager


from dyno_viewer.db.models import *  # pylint: disable=unused-wildcard-import, wildcard-import
from dyno_viewer.util.path import ensure_config_dir


def start_session() -> Iterator[Session]:
    app_path = ensure_config_dir("dyno-viewer")
    engine = create_engine(
        f"sqlite:///{app_path}/db.db",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

    with engine.connect() as conn:
        current = conn.exec_driver_sql("PRAGMA journal_mode;").scalar()
        if not current or current.lower() != "wal":
            conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
            conn.exec_driver_sql("PRAGMA foreign_keys=ON;")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


# @asynccontextmanager
async def start_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create and yield an AsyncSession.
    """
    app_path = ensure_config_dir("dyno-viewer")
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{app_path}/db.db",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    async with engine.begin() as conn:
        current = (await conn.exec_driver_sql("PRAGMA journal_mode;")).scalar()
        if not current or current.lower() != "wal":
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            await conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
            await conn.exec_driver_sql("PRAGMA foreign_keys=ON;")
        await conn.run_sync(SQLModel.metadata.create_all)
    # async_session = sessionmaker(
    #     bind=engine, class_=AsyncSession, expire_on_commit=False
    # )
    async_session = AsyncSession(engine)
    try:
        yield async_session
    finally:
        await async_session.close()


def add_query_history(session: Session, params: QueryParameters) -> None:
    query_history = QueryHistory.from_query_params(params)
    last_query = session.exec(
        select(QueryHistory)
        .where(QueryHistory.filter_conditions == query_history.filter_conditions)
        .where(QueryHistory.key_condition == query_history.key_condition)
        .order_by(QueryHistory.created_at)
    ).first()
    if last_query:
        return

    session.add(query_history)
    session.commit()
    session.refresh(query_history)


async def add_query_history_async(
    session: AsyncSession, params: QueryParameters
) -> None:
    query_history = QueryHistory.from_query_params(params)
    last_query = await session.exec(
        select(QueryHistory)
        .where(QueryHistory.filter_conditions == query_history.filter_conditions)
        .where(QueryHistory.key_condition == query_history.key_condition)
        .order_by(QueryHistory.created_at)
    ).first()
    if last_query:
        return

    session.add(query_history)
    await session.commit()
    await session.refresh(query_history)
