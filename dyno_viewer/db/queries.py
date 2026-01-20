import hashlib
import json
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import aiosqlite

from dyno_viewer.db.data_store import insert
from dyno_viewer.db.models import (
    ListQueryHistoryResultRow,
    ListSavedQueryResultRow,
    RecordType,
)
from dyno_viewer.models import QueryParameters, SavedQuery

# exclude computed fields like boto_params
EXCLUDED_FIELDS = {"boto_params"}


async def add_query_history(
    connection: aiosqlite.Connection, params: QueryParameters
) -> None:
    """
    Add a query to the history table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :param params: Query parameters
    :type params: QueryParameters
    """
    if params.scan_mode and not params.filter_conditions:
        # Avoid storing full table scans without filters in history
        return
    key_uuid = str(
        uuid.uuid5(uuid.NAMESPACE_DNS, params.model_dump_json(exclude=EXCLUDED_FIELDS))
    )
    date = datetime.now(ZoneInfo("UTC")).isoformat()
    await insert(
        connection,
        f"{date}_{key_uuid}",
        params.model_dump(mode="json", exclude=EXCLUDED_FIELDS),
        record_type=RecordType.QueryHistory.value,
        created_at=date,
    )


async def add_saved_query_from_query_params(
    connection: aiosqlite.Connection,
    name: str,
    description: str,
    params: QueryParameters,
) -> None:
    """
    Add a query to the saved queries table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :param name: Name of the saved query
    :type name: str
    :param description: Description of the saved query
    :type description: str
    :param params: Query parameters
    :type params: QueryParameters
    """
    if params.scan_mode and not params.filter_conditions:
        # Avoid storing full table scans without filters in saved queries
        return

    saved_query = SavedQuery.model_validate(
        {
            "name": name,
            "description": description,
            **params.model_dump(),
        }
    )
    date = datetime.now(ZoneInfo("UTC")).isoformat()
    await insert(
        connection,
        str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS, saved_query.model_dump_json(exclude=EXCLUDED_FIELDS)
            )
        ),
        saved_query.model_dump(mode="json", exclude=EXCLUDED_FIELDS),
        record_type=RecordType.SavedQuery.value,
        created_at=date,
    )

async def add_saved_query(
    connection: aiosqlite.Connection, saved_query: SavedQuery
) -> None:
    """
    Add a saved query to the saved queries table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :param saved_query: Saved query object
    :type saved_query: SavedQuery
    """
    if saved_query.scan_mode and not saved_query.filter_conditions:
        # Avoid storing full table scans without filters in saved queries
        return

    key_uuid = str(
        uuid.uuid5(
            uuid.NAMESPACE_DNS,
            saved_query.model_dump_json(exclude=EXCLUDED_FIELDS),
        )
    )
    date = datetime.now(ZoneInfo("UTC")).isoformat()
    await insert(
        connection,
        key_uuid,
        saved_query.model_dump(mode="json", exclude=EXCLUDED_FIELDS),
        record_type=RecordType.SavedQuery.value,
        created_at=date,
    )

async def list_saved_queries(
    connection: aiosqlite.Connection,
    page: int = 1,
    page_size: int = 20,
    search: str = "",
) -> list[ListSavedQueryResultRow]:
    """
    List all saved queries from the data_store table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :param page: Page number for pagination
    :type page: int
    :param page_size: Number of items per page
    :type page_size: int
    :param search: Search term to filter saved queries by name
    :type search: str
    :return: List of saved queries
    :rtype: list[ListSavedQueryResultRow]
    """
    offset = (page - 1) * page_size
    saved_queries = []
    statement = "SELECT data, created_at, key FROM data_store"
    where_clauses = (
        f"WHERE json_extract(data, '$.name') LIKE '%{search}%' AND type = ?"
        if search
        else "WHERE type = ?"
    )
    order_limit_offset = "ORDER BY key LIMIT ? OFFSET ?"
    query = f"{statement} {where_clauses} {order_limit_offset}"
    async with connection.execute(
        query,
        (RecordType.SavedQuery.value, page_size, offset),
    ) as cursor:
        async for row in cursor:
            data = json.loads(row[0])
            saved_queries.append(
                ListSavedQueryResultRow(
                    data=SavedQuery.model_validate(data),
                    created_at=row[1],
                    key=row[2],
                )
            )
    return saved_queries


async def list_query_history(
    connection: aiosqlite.Connection, page: int = 1, page_size: int = 20
) -> list[ListQueryHistoryResultRow]:
    """
    List all query history from the data_store table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :param page: Page number for pagination
    :type page: int
    :param page_size: Number of items per page
    :type page_size: int
    :return: List of query history
    :rtype: list[QueryParameters]
    """
    offset = (page - 1) * page_size
    query_history = []
    async with connection.execute(
        "SELECT data, created_at, key FROM data_store WHERE type = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (RecordType.QueryHistory.value, page_size, offset),
    ) as cursor:
        async for row in cursor:
            data = json.loads(row[0])
            query_history.append(
                ListQueryHistoryResultRow(
                    data=QueryParameters.model_validate(data),
                    created_at=row[1],
                    key=row[2],
                )
            )
    return query_history


async def get_query_history(
    connection: aiosqlite.Connection, key: str
) -> QueryParameters | None:
    """
    Retrieve a query history entry by key from the data_store table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :param key: Key of the query history entry
    :type key: str
    :return: Retrieved query parameters or None if not found
    :rtype: QueryParameters | None
    """
    async with connection.execute(
        "SELECT data FROM data_store WHERE type = ? AND key = ?",
        (RecordType.QueryHistory.value, key),
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            data = json.loads(row[0])
            return QueryParameters.model_validate(data)
    return None


async def get_last_query_ran(
    connection: aiosqlite.Connection,
) -> QueryParameters | None:
    """
    Retrieve the most recent query history from the data_store table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :return: Most recent query history or None if not found
    :rtype: QueryParameters | None
    """
    async with connection.execute(
        "SELECT data FROM data_store WHERE type = ? ORDER BY created_at DESC LIMIT 1",
        (RecordType.QueryHistory.value,),
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            data = json.loads(row[0])
            return QueryParameters.model_validate(data)
    return None


async def get_saved_query_by_name(
    connection: aiosqlite.Connection, name: str
) -> SavedQuery | None:
    """
    Retrieve a saved query by name from the data_store table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :param name: Name of the saved query
    :type name: str
    :return: Retrieved saved query or None if not found
    :rtype: SavedQuery | None
    """
    async with connection.execute(
        "SELECT data FROM data_store WHERE type = ? AND json_extract(data, '$.name') = ?",
        (RecordType.SavedQuery.value, name),
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            data = json.loads(row[0])
            return SavedQuery.model_validate(data)
    return None


async def get_saved_query(
    connection: aiosqlite.Connection, key: str
) -> SavedQuery | None:
    """
    Retrieve a saved query by key from the data_store table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :param key: Key of the saved query
    :type key: str
    :return: Retrieved saved query or None if not found
    :rtype: SavedQuery | None
    """
    async with connection.execute(
        "SELECT data FROM data_store WHERE type = ? AND key = ?",
        (RecordType.SavedQuery.value, key),
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            data = json.loads(row[0])
            return SavedQuery.model_validate(data)
    return None


async def remove_all_query_history(connection: aiosqlite.Connection) -> None:
    """
    Delete all query history from the data_store table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    """
    await connection.execute(
        "DELETE FROM data_store WHERE type = ?",
        (RecordType.QueryHistory.value,),
    )
    await connection.commit()


async def delete_all_saved_queries(connection: aiosqlite.Connection) -> None:
    """
    Delete all saved queries from the data_store table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    """
    await connection.execute(
        "DELETE FROM data_store WHERE type = ?",
        (RecordType.SavedQuery.value,),
    )
    await connection.commit()
