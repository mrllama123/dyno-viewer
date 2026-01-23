import sys
import uuid

sys.path.append("..")
from dyno_viewer.models import QueryParameters, KeyCondition, FilterCondition
import time
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
from dyno_viewer.db.queries import (
    add_query_history,
    add_saved_query,
    list_query_history,
    get_saved_query_by_name,
)


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
    # for _ in range(5):
    #     await add_saved_query(
    #         connection,
    #         name=f"Test Saved Query {uuid.uuid4()}",
    #         description="A test saved query",
    #         params=QueryParameters.model_validate(
    #             {
    #                 "scan_mode": False,
    #                 "primary_key_name": "pk",
    #                 "sort_key_name": "sk",
    #                 "key_condition": KeyCondition.model_validate(
    #                     {
    #                         "partitionKeyValue": "partition_value",
    #                     }
    #                 ),
    #                 "filter_conditions": [],
    #                 "next_token": None,
    #             }
    #         ),
    #     )
    #     time.sleep(0.2)
    # for _ in range(30):
    #     await add_history_query(
    #         connection,
    #         QueryParameters.model_validate({
    #             "scan_mode": False,
    #             "primary_key_name": "pk",
    #             "sort_key_name": "sk",
    #             "key_condition": KeyCondition.model_validate({
    #                 "partitionKeyValue": "partition_value",
    #             }),
    #             "filter_conditions": [],
    #             "next_token": None,
    #         }),
    #     )
    #     time.sleep(0.2)
    # page = 1
    # results = []
    # result = await list_query_history(connection, page=page, page_size=10)
    # results.extend(result)
    # print(f"Page {page}: {len(result)} results")
    # while result:
    #     result = await list_query_history(connection, page=page, page_size=10)
    #     page += 1
    #     print(f"Page {page}: {len(result)} results")
    #     if result:
    #         results.append(result)

    saved_query = await get_saved_query_by_name(
        connection,
        "Test Saved Query ced7f097-b471-465e-8e56-a2f0d7dfc2a7",
    )
    print(saved_query)

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
