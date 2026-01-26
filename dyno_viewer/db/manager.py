import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional
from zoneinfo import ZoneInfo

import aiosqlite

from dyno_viewer.db.models import (
    ListQueryHistoryResultRow,
    ListSavedQueryResultRow,
    RecordType,
)
from dyno_viewer.db.utils import json_path_from_dict
from dyno_viewer.models import QueryParameters, SavedQuery


class DatabaseManager:
    """
    Database manager class that encapsulates all database operations and manages
    the async connection lifecycle.

    This class provides a unified interface for all database operations, managing
    a single async SQLite connection that is created on initialization and closed
    when the manager is closed.

    :param db_path: Path to the SQLite database file, defaults to None (in-memory DB)
    :type db_path: Path | None
    """

    EXCLUDED_FIELDS = {"boto_params"}

    def __init__(self, db_path: Path | None = None):
        """
        Initialize the DatabaseManager.

        :param db_path: Path to the SQLite database file, defaults to None (in-memory DB)
        :type db_path: Path | None
        """
        self._db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        self._is_closed = True

    async def setup(self) -> None:
        """
        Set up the database connection with WAL mode and create the data_store table.

        :return: None
        :rtype: None
        """
        if not self._is_closed:
            return

        self._connection = await self._setup_connection()
        self._is_closed = False

    async def close(self) -> None:
        """
        Close the database connection.

        :return: None
        :rtype: None
        """
        if self._is_closed:
            return

        if self._connection:
            await self._connection.close()
            self._connection = None
        self._is_closed = True

    @property
    def connection(self) -> aiosqlite.Connection:
        return self._ensure_connection()

    async def _setup_connection(self) -> aiosqlite.Connection:
        """
        Set up the SQLite database connection with WAL mode and create the data_store table.

        :return: Database connection
        :rtype: aiosqlite.Connection
        """
        db = await aiosqlite.connect(self._db_path or ":memory:")
        # Enable WAL mode for better concurrency
        cur = await db.execute("PRAGMA journal_mode;")
        row = await cur.fetchone()
        current = row[0] if row else None
        if str(current).lower() != "wal":
            await db.execute("PRAGMA journal_mode = WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")
            await db.execute("PRAGMA foreign_keys=ON;")
        await self._create_data_store_table(db)
        return db

    async def _create_data_store_table(self, connection: aiosqlite.Connection) -> None:
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
            record_type TEXT,
            data TEXT NOT NULL,
            CHECK (json_valid(data))
        )
        """
        )
        await connection.commit()

    def _ensure_connection(self) -> aiosqlite.Connection:
        """
        Ensure the connection is open and return it.

        :return: Database connection
        :rtype: aiosqlite.Connection
        :raises: RuntimeError if connection is closed
        """
        if self._is_closed or not self._connection:
            raise RuntimeError("Database connection is closed")
        return self._connection

    async def insert(
        self,
        key: str,
        data: dict,
        record_type: str | None = None,
        created_at: str | None = None,
    ) -> None:
        """
        Insert a new record into the data_store table.

        :param key: Key for the record
        :type key: str
        :param data: Data to be inserted
        :type data: dict
        :param record_type: Optional type of the record
        :type record_type: str | None
        :param created_at: Optional creation timestamp
        :type created_at: str | None
        """
        connection = self._ensure_connection()
        sql_statement = "INSERT INTO data_store"

        cols = ["key", "data"]
        placeholders = ["?", "?"]
        if record_type:
            cols.append("record_type")
            placeholders.append("?")
        if created_at:
            cols.append("created_at")
            placeholders.append("?")
        sql_statement += f" ({', '.join(cols)}) VALUES ({', '.join(placeholders)})"
        values = (key, json.dumps(data))
        if record_type:
            values += (record_type,)
        if created_at:
            values += (created_at,)

        await connection.execute(sql_statement, (values))
        await connection.commit()

    async def remove(self, key: str) -> None:
        """
        Delete a record from the data_store table by key.

        :param key: Key of the record to delete
        :type key: str
        """
        connection = self._ensure_connection()
        await connection.execute(
            "DELETE FROM data_store WHERE key = ?",
            (key,),
        )
        await connection.commit()

    async def update(self, key: str, data: dict) -> None:
        """
        Update an existing record in the data_store table.

        :param key: Key of the record to update
        :type key: str
        :param data: Data to update the record with
        :type data: dict
        """
        connection = self._ensure_connection()
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

    async def get(self, key: str) -> dict | None:
        """
        Retrieve a record from the data_store table by key.

        :param key: Key of the record to retrieve
        :type key: str
        :return: Retrieved data as a dictionary or None if not found
        :rtype: dict | None
        """
        connection = self._ensure_connection()
        async with connection.execute(
            "SELECT data FROM data_store WHERE key = ?",
            (key,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    async def get_all(self) -> List[dict]:
        """
        Retrieve all records from the data_store table.

        :return: List of all records as dictionaries
        :rtype: List[dict]
        """
        connection = self._ensure_connection()
        async with connection.execute(
            "SELECT data FROM data_store",
        ) as cursor:
            return [json.loads(row[0]) async for row in cursor]

    async def add_query_history(self, params: QueryParameters) -> None:
        """
        Add a query to the history table.

        :param params: Query parameters
        :type params: QueryParameters
        """
        key_uuid = str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS, params.model_dump_json(exclude=self.EXCLUDED_FIELDS)
            )
        )
        date = datetime.now(ZoneInfo("UTC")).isoformat()
        await self.insert(
            f"{date}_{key_uuid}",
            params.model_dump(mode="json", exclude=self.EXCLUDED_FIELDS),
            record_type=RecordType.QueryHistory.value,
            created_at=date,
        )

    async def add_saved_query_from_query_params(
        self, name: str, description: str, params: QueryParameters
    ) -> None:
        """
        Add a query to the saved queries table.

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
        await self.insert(
            str(
                uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    saved_query.model_dump_json(exclude=self.EXCLUDED_FIELDS),
                )
            ),
            saved_query.model_dump(mode="json", exclude=self.EXCLUDED_FIELDS),
            record_type=RecordType.SavedQuery.value,
            created_at=date,
        )

    async def add_saved_query(self, saved_query: SavedQuery) -> None:
        """
        Add a saved query to the saved queries table.

        :param saved_query: Saved query object
        :type saved_query: SavedQuery
        """
        if saved_query.scan_mode and not saved_query.filter_conditions:
            # Avoid storing full table scans without filters in saved queries
            return

        key_uuid = str(
            uuid.uuid5(
                uuid.NAMESPACE_DNS,
                saved_query.model_dump_json(exclude=self.EXCLUDED_FIELDS),
            )
        )
        date = datetime.now(ZoneInfo("UTC")).isoformat()
        await self.insert(
            key_uuid,
            saved_query.model_dump(mode="json", exclude=self.EXCLUDED_FIELDS),
            record_type=RecordType.SavedQuery.value,
            created_at=date,
        )

    async def list_saved_queries(
        self, page: int = 1, page_size: int = 20, search: str = ""
    ) -> list[ListSavedQueryResultRow]:
        """
        List all saved queries from the data_store table.

        :param page: Page number for pagination
        :type page: int
        :param page_size: Number of items per page
        :type page_size: int
        :param search: Search term to filter saved queries by name
        :type search: str
        :return: List of saved queries
        :rtype: list[ListSavedQueryResultRow]
        """
        connection = self._ensure_connection()
        offset = (page - 1) * page_size
        saved_queries = []
        statement = "SELECT data, created_at, key FROM data_store"
        where_clauses = (
            f"WHERE json_extract(data, '$.name') LIKE '%{search}%' AND record_type = ?"
            if search
            else "WHERE record_type = ?"
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
        self, page: int = 1, page_size: int = 20
    ) -> list[ListQueryHistoryResultRow]:
        """
        List all query history from the data_store table.

        :param page: Page number for pagination
        :type page: int
        :param page_size: Number of items per page
        :type page_size: int
        :return: List of query history
        :rtype: list[ListQueryHistoryResultRow]
        """
        connection = self._ensure_connection()
        offset = (page - 1) * page_size
        query_history = []
        async with connection.execute(
            "SELECT data, created_at, key FROM data_store WHERE record_type = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
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

    async def get_query_history(self, key: str) -> QueryParameters | None:
        """
        Retrieve a query history entry by key from the data_store table.

        :param key: Key of the query history entry
        :type key: str
        :return: Retrieved query parameters or None if not found
        :rtype: QueryParameters | None
        """
        connection = self._ensure_connection()
        async with connection.execute(
            "SELECT data FROM data_store WHERE record_type = ? AND key = ?",
            (RecordType.QueryHistory.value, key),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                data = json.loads(row[0])
                return QueryParameters.model_validate(data)
        return None

    async def get_last_query_ran(self) -> QueryParameters | None:
        """
        Retrieve the most recent query history from the data_store table.

        :return: Most recent query history or None if not found
        :rtype: QueryParameters | None
        """
        connection = self._ensure_connection()
        async with connection.execute(
            "SELECT data FROM data_store WHERE record_type = ? ORDER BY created_at DESC LIMIT 1",
            (RecordType.QueryHistory.value,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                data = json.loads(row[0])
                return QueryParameters.model_validate(data)
        return None

    async def get_saved_query_by_name(self, name: str) -> SavedQuery | None:
        """
        Retrieve a saved query by name from the data_store table.

        :param name: Name of the saved query
        :type name: str
        :return: Retrieved saved query or None if not found
        :rtype: SavedQuery | None
        """
        connection = self._ensure_connection()
        async with connection.execute(
            "SELECT data FROM data_store WHERE record_type = ? AND json_extract(data, '$.name') = ?",
            (RecordType.SavedQuery.value, name),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                data = json.loads(row[0])
                return SavedQuery.model_validate(data)
        return None

    async def get_saved_query(self, key: str) -> SavedQuery | None:
        """
        Retrieve a saved query by key from the data_store table.

        :param key: Key of the saved query
        :type key: str
        :return: Retrieved saved query or None if not found
        :rtype: SavedQuery | None
        """
        connection = self._ensure_connection()
        async with connection.execute(
            "SELECT data FROM data_store WHERE record_type = ? AND key = ?",
            (RecordType.SavedQuery.value, key),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                data = json.loads(row[0])
                return SavedQuery.model_validate(data)
        return None

    async def remove_all_query_history(self) -> None:
        """
        Delete all query history from the data_store table.
        """
        connection = self._ensure_connection()
        await connection.execute(
            "DELETE FROM data_store WHERE record_type = ?",
            (RecordType.QueryHistory.value,),
        )
        await connection.commit()

    async def delete_all_saved_queries(self) -> None:
        """
        Delete all saved queries from the data_store table.
        """
        connection = self._ensure_connection()
        await connection.execute(
            "DELETE FROM data_store WHERE record_type = ?",
            (RecordType.SavedQuery.value,),
        )
        await connection.commit()
