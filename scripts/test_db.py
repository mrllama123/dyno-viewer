import sys


sys.path.append("..")
from dyno_viewer.models import QueryParameters, KeyCondition, FilterCondition

import argparse
import asyncio
from pathlib import Path
import aiosqlite
from pydantic import BaseModel, ConfigDict
import json
from typing import Any, List, TypedDict
from dyno_viewer.db.data_store import (
    insert,
    remove,
    update,
    get,
    get_all,
    setup_connection,
)
from dyno_viewer.db.queries import add_history_query, add_saved_query
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
    connection = await setup_connection(args.db_path)
    await add_history_query(
        connection,
        QueryParameters.model_validate({
            "scan_mode": False,
            "primary_key_name": "pk",
            "sort_key_name": "sk",
            "key_condition": KeyCondition.model_validate({
                "partitionKeyValue": "partition_value",
            }),
            "filter_conditions": [],
            "next_token": None,
        }),
    )
    await connection.close()
    # async with aiosqlite.connect(args.db_path) as db:
    #     await configure_db(db)
    #     await create_data_store_table(db)
    #     await get_all(db)
        # await db.execute(
        #     "INSERT INTO data_store (key, data) VALUES (?, ?)",
        #     ("key1", '{"some_key": "some_value"}'),
        # )
        # await db.commit()
        # await update(db, "key1", {"new_key": {"nested_key": "777", "another_key": {"deep_key": 42}}})

        # await remove(db, "key1")


if __name__ == "__main__":
    asyncio.run(main())
