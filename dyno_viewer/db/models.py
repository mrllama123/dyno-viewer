from datetime import datetime
from enum import Enum
from zoneinfo import ZoneInfo

from pydantic import BaseModel, field_validator

from dyno_viewer.models import (
    QueryHistory,
    SavedQuery,
)


class JsonPathNode(BaseModel):
    path: str
    value: str


class RecordType(Enum):
    SavedQuery = "SavedQuery"  # pylint: disable=invalid-name
    QueryHistory = "QueryHistory"  # pylint: disable=invalid-name


class ListQueryHistoryResultRow(BaseModel):
    data: QueryHistory
    created_at: datetime
    key: str

    @field_validator("created_at", mode="after")
    @classmethod
    def ensure_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=ZoneInfo("UTC"))
        return v


class ListSavedQueryResultRow(BaseModel):
    data: SavedQuery
    created_at: datetime
    key: str

    @field_validator("created_at", mode="after")
    @classmethod
    def ensure_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=ZoneInfo("UTC"))
        return v
