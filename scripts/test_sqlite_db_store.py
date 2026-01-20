import argparse
import asyncio
from pathlib import Path
import aiosqlite
from pydantic import BaseModel, ConfigDict
import json
from typing import Any, List


async def configure_db(connection: aiosqlite.Connection) -> None:
    cur = await connection.execute("PRAGMA journal_mode;")
    row = await cur.fetchone()
    current = row[0] if row else None
    if str(current).lower() != "wal":
        await connection.execute("PRAGMA journal_mode = WAL;")
        await connection.execute("PRAGMA synchronous=NORMAL;")
        await connection.execute("PRAGMA foreign_keys=ON;")


async def insert(connection: aiosqlite.Connection, key: str, data: dict | str):
    if isinstance(data, dict):
        data = json.dumps(data)
    await connection.execute(
        "INSERT INTO data_store (key, json(data)) VALUES (?, ?)",
        (key, data),
    )
    await connection.commit()


async def remove(connection: aiosqlite.Connection, key: str):
    await connection.execute(
        "DELETE FROM data_store WHERE key = ?",
        (key,),
    )
    await connection.commit()

async def update(connection: aiosqlite.Connection, key: str, data: dict | str):
    pass
    # await connection.execute(
    #     "UPDATE data_store SET data = ? WHERE key = ?",
    #     (data, key),
    # )
    # await connection.commit()


async def create_data_store_table(connection: aiosqlite.Connection) -> None:
    await connection.execute(
        """
    CREATE TABLE IF NOT EXISTS data_store (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL UNIQUE,
        data TEXT NOT NULL,
        CHECK (json_valid(data))
    )
    """
    )
    await connection.commit()


def format_dict_keys_as_json_paths(data: dict[str, Any]) -> List[str]:
    """
    Return all keys in a dict as JSONPath-like strings starting with "$".

    Examples:
    - {"a": 1} -> ["$.a"]
    - {"a": {"b": 2}, "c": 3} -> ["$.a", "$.a.b", "$.c"]

    Only nested dicts are traversed as requested; other types are treated as leaf values.
    """

    def walk(obj: dict[str, Any], prefix: str) -> List[str]:
        paths: List[str] = []
        for key, value in obj.items():
            current = f"{prefix}.{key}"
            if isinstance(value, dict):
                paths.extend(walk(value, current))
            paths.append(current)
        return paths

    if not isinstance(data, dict):
        return []
    return walk(data, "$")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test local storage",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path("db.db"),
        help="Path to the SQLite database file",
    )
    args = parser.parse_args()
    async with aiosqlite.connect(args.db_path) as db:
        await configure_db(db)
        await create_data_store_table(db)
        await db.execute(
            "INSERT INTO data_store (key, data) VALUES (?, ?)",
            ("key1", '{"some_key": "some_value"}'),
        )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
