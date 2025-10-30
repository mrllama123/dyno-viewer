from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from dyno_viewer.db.models import (
    Base,
    ListQueryHistoryResult,
    ListSavedQueriesResult,
    QueryHistory,
    SavedQuery,
)
from dyno_viewer.models import QueryParameters
from dyno_viewer.util.path import ensure_config_dir


async def start_async_session() -> AsyncSession:
    """Create and return an AsyncSession instance."""
    app_path = ensure_config_dir("dyno-viewer")
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{app_path}/db.db",
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


async def delete_all_query_history(session: AsyncSession) -> None:
    stmt = delete(QueryHistory)
    await session.execute(stmt)
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


async def delete_saved_query(session: AsyncSession, query_id: int) -> None:
    stmt = select(SavedQuery).where(SavedQuery.id == query_id)
    result = await session.execute(stmt)
    saved_query = result.scalars().first()
    if saved_query:
        await session.delete(saved_query)
        await session.commit()


async def delete_all_saved_queries(session: AsyncSession) -> None:
    stmt = delete(SavedQuery)
    await session.execute(stmt)
    await session.commit()
