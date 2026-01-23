import json
from functools import wraps
from pathlib import Path
from typing import Any, AsyncGenerator, List, TypedDict

import aiosqlite

from dyno_viewer.db.utils import json_path_from_dict


async def setup_connection(db_path: Path | None = None) -> aiosqlite.Connection:
    """
    Set up the SQLite database connection with WAL mode and create the data_store table.

    :param db_path: Path to the SQLite database file, defaults to None (which creates in-memory DB)
    :type db_path: Path | None
    :return: Async generator yielding the database connection
    :rtype: AsyncGenerator[Connection, None]
    """
    db = await aiosqlite.connect(db_path or ":memory:")
    # Enable WAL mode for better concurrency
    cur = await db.execute("PRAGMA journal_mode;")
    row = await cur.fetchone()
    current = row[0] if row else None
    if str(current).lower() != "wal":
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA synchronous=NORMAL;")
        await db.execute("PRAGMA foreign_keys=ON;")
    await _create_data_store_table(db)
    return db


def handle_db_failures(func):
    @wraps(func)
    async def wrapper(connection: aiosqlite.Connection, *args, **kwargs):
        try:
            return await func(connection, *args, **kwargs)
        except Exception:
            await connection.rollback()
            await connection.close()
            raise

    return wrapper


@handle_db_failures
async def insert(
    connection: aiosqlite.Connection,
    key: str,
    data: dict,
    record_type: str | None = None,
):
    """
    Insert a new record into the data_store table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :param key: Key for the record
    :type key: str
    :param data: Data to be inserted
    :type data: dict
    :param record_type: Optional type of the record
    :type record_type: str | None
    """
    sql_statement = (
        "INSERT INTO data_store (key, data, type) VALUES (?, ?, ?)"
        if record_type
        else "INSERT INTO data_store (key, data) VALUES (?, ?)"
    )
    values = (
        (key, json.dumps(data), record_type) if record_type else (key, json.dumps(data))
    )
    await connection.execute(sql_statement, values)
    await connection.commit()


@handle_db_failures
async def remove(connection: aiosqlite.Connection, key: str):
    await connection.execute(
        "DELETE FROM data_store WHERE key = ?",
        (key,),
    )
    await connection.commit()


@handle_db_failures
async def update(connection: aiosqlite.Connection, key: str, data: dict):
    """
    Update an existing record in the data_store table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :param key: Key of the record to update
    :type key: str
    :param data: Data to update the record with
    :type data: dict
    """
    json_keys_for_update = json_path_from_dict(data)
    if not json_keys_for_update:
        return

    placeholders = ", ".join(["?, ?"] * len(json_keys_for_update))
    sql_statement = (
        "UPDATE data_store SET data = json_set(data, "
        + placeholders
        + ") WHERE key = ?"
    )

    params: List[Any] = []
    for path_value in json_keys_for_update:
        params.append(path_value["path"])
        params.append(path_value["value"])
    params.append(key)
    await connection.execute(sql_statement, params)
    await connection.commit()


@handle_db_failures
async def get(connection: aiosqlite.Connection, key: str) -> dict | None:
    """
    Retrieve a record from the data_store table by key.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :param key: Key of the record to retrieve
    :type key: str
    :return: Retrieved data as a dictionary or None if not found
    :rtype: dict | None
    """

    async with connection.execute(
        "SELECT data FROM data_store WHERE key = ?",
        (key,),
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None


@handle_db_failures
async def get_all(connection: aiosqlite.Connection) -> List[dict]:
    """
    Retrieve all records from the data_store table.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    :return: List of all records as dictionaries
    :rtype: List[dict]
    """
    async with connection.execute(
        "SELECT data FROM data_store",
    ) as cursor:
        return [json.loads(row[0]) async for row in cursor]


@handle_db_failures
async def _create_data_store_table(connection: aiosqlite.Connection) -> None:
    """
    Create the data_store table if it does not exist.

    :param connection: Database connection
    :type connection: aiosqlite.Connection
    """
    await connection.execute(
        """
    CREATE TABLE IF NOT EXISTS data_store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        type TEXT,
        data TEXT NOT NULL,
        CHECK (json_valid(data))
    )
    """
    )
    await connection.commit()
