from typing import TypedDict


class KeySchema(TypedDict):
    primaryKey: str
    sortKey: str


class TableInfo(TypedDict):
    keySchema: KeySchema
    gsi: dict[str, KeySchema]
