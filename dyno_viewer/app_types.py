from typing import TypedDict


class KeySchema(TypedDict):
    primaryKey: str
    sortKey: str


class TableInfo(TypedDict):
    tableName: str = ""
    keySchema: KeySchema
    gsi: dict[str, KeySchema]
