from datetime import datetime
from enum import Enum
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator

from dyno_viewer.models import QueryHistory, SavedQuery, Session, SessionGroup


class JsonPathNode(BaseModel):
    path: str
    value: str


class RecordType(Enum):
    SavedQuery = "SavedQuery"  # pylint: disable=invalid-name
    QueryHistory = "QueryHistory"  # pylint: disable=invalid-name
    SessionGroup = "SessionGroup"  # pylint: disable=invalid-name
    Session = "Session"  # pylint: disable=invalid-name


class BaseDataStoreRow(BaseModel):
    # needed to allow pydantic models
    model_config = ConfigDict(arbitrary_types_allowed=True)
    data: BaseModel
    created_at: datetime
    key: str

    @field_validator("created_at", mode="after")
    @classmethod
    def ensure_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=ZoneInfo("UTC"))
        return v


class ListQueryHistoryResultRow(BaseDataStoreRow):
    data: QueryHistory


class ListSavedQueryResultRow(BaseDataStoreRow):
    data: SavedQuery


class ListSessionGroupResultRow(BaseDataStoreRow):
    data: SessionGroup


class ListSessionResultRow(BaseDataStoreRow):
    data: Session


class BatchInsertRecord(BaseModel):
    key: str
    record_type: str | None = None
    created_at: str = Field(
        default_factory=lambda: datetime.now(ZoneInfo("UTC")).isoformat()
    )
    data: dict
